# shop/views.py
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.html import escape
from django.utils import timezone
from .models import OrderItem


from .models import Category, Product, Order, Profile, Feedback, Address
from .cart import Cart
from .forms import CustomUserCreationForm, ProfileForm

# Auth imports
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.core.mail import send_mail
from django.conf import settings

import razorpay
import random
import time




def is_ajax_request(request):
    """
    Safe AJAX detection. Some clients set X-Requested-With header.
    """
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"
    )


# -------------------------
# PRODUCT LIST
# -------------------------
def product_list(request, slug=None):
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True).order_by("-created_at")
    current_category = None

    if slug:
        current_category = get_object_or_404(Category, slug=slug)
        products = products.filter(category=current_category)

    query = request.GET.get("q")
    if query:
        products = products.filter(name__icontains=query)

    return render(request, "shop/product_list.html", {
        "categories": categories,
        "products": products,
        "current_category": current_category,
        "query": query or ""
    })


# -------------------------
# PRODUCT DETAIL
# -------------------------
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id)

    all_products = None
    if not related_products.exists():
        all_products = Product.objects.filter(is_active=True).exclude(id=product.id)[:8]

    reviews_qs = product.feedbacks.filter(approved=True).order_by("-created_at")
    page = request.GET.get("rpage", 1)
    paginator = Paginator(reviews_qs, 5)

    try:
        reviews_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        reviews_page = paginator.page(1)

    if is_ajax_request(request) and request.GET.get("rpage"):
        rendered = render_to_string(
            "shop/reviews_list.html",
            {
                "reviews_page": reviews_page,
                "product": product,
                "avg_rating": product.average_rating(),
                "review_count": product.review_count(),
                "reviews_paginator": paginator,
            },
            request=request,
        )
        return HttpResponse(rendered)

    display_name = (
        request.user.get_full_name() or request.user.get_username()
        if request.user.is_authenticated else ""
    )

    user_feedback = (
        product.feedbacks.filter(user=request.user).first()
        if request.user.is_authenticated else None
    )

    return render(request, "shop/product_detail.html", {
        "product": product,
        "related_products": related_products,
        "all_products": all_products,
        "reviews_page": reviews_page,
        "avg_rating": float(product.average_rating() or 0),
        "review_count": product.review_count(),
        "reviews_paginator": paginator,
        "display_name": display_name,
        "user_feedback": user_feedback,
    })


# -------------------------
# ADD TO CART (LOGIN REQUIRED + TOAST + REDIRECT BACK)
# -------------------------
def cart_add(request, product_id):
    if not request.user.is_authenticated:
        messages.warning(request, "Please login to continue")
        login_url = f"{reverse('shop:login')}?next={request.path}"

        if is_ajax_request(request):
            return JsonResponse({
                "login_required": True,
                "redirect_url": login_url,
                "message": "Please login to continue"
            }, status=401)

        return redirect(login_url)

    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = Cart(request)

    qty = 1
    try:
        qty = int(request.POST.get("qty", 1))
    except:
        qty = 1

    cart.add(product=product, quantity=qty, update_quantity=False)

    unique_count = len(cart.cart) if hasattr(cart, "cart") else 0
    total_qty = len(cart)

    if is_ajax_request(request):
        return JsonResponse({
            "success": True,
            "cart_count": unique_count,
            "total_qty": total_qty,
        })

    return redirect("shop:cart_detail")


# -------------------------
# UPDATE CART QTY
# -------------------------
def cart_update(request, product_id):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid")

    cart = Cart(request)

    try:
        qty = int(request.POST.get("qty", 1))
    except:
        qty = 1

    if qty <= 0:
        try:
            product = Product.objects.get(id=product_id)
            cart.remove(product)
        except:
            pass
    else:
        product = get_object_or_404(Product, id=product_id)
        cart.add(product=product, quantity=qty, update_quantity=True)

    row_total = 0.0
    for item in cart:
        if item["product"].id == product_id:
            row_total = float(item["total_price"])
            break

    return JsonResponse({
        "success": True,
        "row_total": row_total,
        "cart_total": float(cart.get_total_price()),
        "cart_count": len(cart.cart),
        "total_qty": len(cart),
    })


# -------------------------
# REMOVE FROM CART
# -------------------------
def cart_remove(request, product_id):
    cart = Cart(request)
    try:
        product = Product.objects.get(id=product_id)
        cart.remove(product)
    except:
        pass
    return redirect("shop:cart_detail")


# -------------------------
# CART DETAIL
# -------------------------
def cart_detail(request):
    cart = Cart(request)
    items = []
    total = Decimal("0.00")

    for item in cart:
        items.append({
            "id": item["product"].id,
            "product": item["product"],
            "name": item["product"].name,
            "price": item["price"],
            "quantity": item["quantity"],
            "line_total": item["total_price"],
        })
        total += item["total_price"]

    return render(request, "shop/cart_detail.html", {
        "items": items,
        "total": total
    })


# -------------------------
# BUY NOW (LOGIN REQUIRED + TOAST + REDIRECT BACK)
# -------------------------
# -------------------------

#BUY NOW (LOGIN REQUIRED → REDIRECT TO CHECKOUT)
def buy_now(request, product_id):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('shop:login')}?next={request.path}")

    product = get_object_or_404(Product, id=product_id, is_active=True)

    try:
        qty = int(request.POST.get("qty", 1))
    except:
        qty = 1


    cart = Cart(request)

    # ✅ Remove ONLY this product from cart (if already present)
    product_key = str(product.id)
    if product_key in cart.cart:
        del cart.cart[product_key]
        cart.session.modified = True

    # ✅ Store buy-now intent (isolated checkout)
    request.session["buy_now_product_id"] = product.id
    request.session["buy_now_qty"] = qty
    request.session.modified = True

    # ✅ Go to isolated checkout
    return redirect(f"{reverse('shop:checkout')}?buy={product.id}&qty={qty}")

# -------------------------
# BUY NOW (STRICT ISOLATED FLOW)
# -------------------------
# @login_required
# def buy_now(request, product_id):
#     product = get_object_or_404(Product, id=product_id, is_active=True)

#     try:
#         qty = int(request.POST.get("qty", 1))
#     except:
#         qty = 1

#     cart = Cart(request)
#     cart.clear()                       # ✅ ALWAYS clear old cart
#     cart.add(product=product, quantity=qty, update_quantity=True)

#     request.session.modified = True
#     return redirect("shop:checkout")




# -------------------------
# CHECKOUT + PAYMENT
# -------------------------
def checkout(request):
    buy_id = request.GET.get("buy")
    buy_qty = request.GET.get("qty")

    try:
        buy_qty = int(buy_qty) if buy_qty else 1
    except:
        buy_qty = 1

    cart = Cart(request)

    # ================================
    # ✅ BUY NOW MODE (READ-ONLY CART)
    # ================================
    if buy_id:
        try:
            product = Product.objects.get(id=int(buy_id), is_active=True)
        except Product.DoesNotExist:
            return redirect("shop:product_list")

    # ✅ CRITICAL FIX:
    # Ensure buy-now session is ALWAYS set (home page Buy Now was missing this)
    request.session["buy_now_product_id"] = product.id
    request.session["buy_now_qty"] = buy_qty
    request.session.modified = True

    # 🚫 DO NOT touch cart

    buy_now_items = [{
        "product": product,
        "price": product.price,
        "quantity": buy_qty,
        "total_price": product.price * buy_qty,
    }]

    total = product.price * buy_qty

    return render(request, "shop/checkout.html", {
        "cart": buy_now_items,
        "total": total,
        "suggestions": Product.objects.filter(is_active=True)
            .exclude(id=product.id)
            .order_by("?")[:4],
    })

    # ================================
    # ✅ NORMAL CART CHECKOUT
    # ================================
    if len(cart) == 0:
        return redirect("shop:product_list")

    return render(request, "shop/checkout.html", {
        "cart": list(cart),
        "total": cart.get_total_price(),
        "suggestions": Product.objects.filter(is_active=True).order_by("?")[:4],
    })


def initiate_payment(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid")

    email = request.POST.get("email", "").strip()
    if not email and request.user.is_authenticated:
        email = request.user.email

    if not email:
        return JsonResponse({"error": "Email required"}, status=400)

    cart = Cart(request)

    # ================================
    # ✅ BUY NOW PAYMENT MODE
    # ================================
    buy_id = request.session.get("buy_now_product_id")
    buy_qty = request.session.get("buy_now_qty", 1)

    if buy_id:
        try:
            product = Product.objects.get(id=int(buy_id), is_active=True)
        except Product.DoesNotExist:
            return JsonResponse({"error": "Invalid product"}, status=400)

        total = product.price * int(buy_qty)

        # Create order
        order = Order.objects.create(
            email=email,
            total_amount=total
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.price,
            quantity=int(buy_qty)
        )

    # ================================
    # ✅ NORMAL CART PAYMENT MODE
    # ================================
    else:
        if len(cart) == 0:
            return JsonResponse({"error": "Cart empty"}, status=400)

        total = cart.get_total_price()

        order = Order.objects.create(
            email=email,
            total_amount=total
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item["product"],
                price=item["price"],
                quantity=item["quantity"]
            )

    paise = int(total * 100)

    # ================================
    # RAZORPAY ORDER
    # ================================
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    rzp_order = client.order.create({
        "amount": paise,
        "currency": "INR",
        "receipt": f"order_{order.id}",
        "notes": {"order_id": str(order.id)}
    })

    order.razorpay_order_id = rzp_order["id"]
    order.save()

    return JsonResponse({
        "razorpay_order_id": rzp_order["id"],
        "order_id": order.id,
        "amount": paise,
        "currency": "INR",
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    })

@csrf_exempt
@csrf_exempt
def payment_handler(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid")

    order_id = request.POST.get("order_id")
    payment_id = request.POST.get("razorpay_payment_id")
    signature = request.POST.get("razorpay_signature")
    razorpay_order_id = request.POST.get("razorpay_order_id")

    if not all([order_id, payment_id, signature, razorpay_order_id]):
        return HttpResponseBadRequest("Missing params")

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })
    except:
        Order.objects.filter(id=order_id).update(status="failed")
        return HttpResponseBadRequest("Signature failed")

    # ✅ Mark order paid
    Order.objects.filter(id=order_id).update(
        status="paid",
        razorpay_payment_id=payment_id,
        razorpay_signature=signature
    )

    # ✅ CLEAR CART ONLY FOR NORMAL CART CHECKOUT
    if not request.session.get("buy_now_product_id"):
        Cart(request).clear()

    return JsonResponse({"status": "paid"})

from django.views.decorators.http import require_POST

@require_POST
def clear_buy_now_session(request):
    """
    Called when Razorpay popup is dismissed.
    Clears ONLY buy-now intent, not the cart.
    """
    request.session.pop("buy_now_product_id", None)
    request.session.pop("buy_now_qty", None)
    request.session.modified = True
    return JsonResponse({"cleared": True})


# -------------------------
# CHECKOUT SUCCESS
# -------------------------
def checkout_success(request):
    # ✅ Clear ONLY buy-now session (cart must remain untouched)
    request.session.pop("buy_now_product_id", None)
    request.session.pop("buy_now_qty", None)
    request.session.modified = True

    return render(request, "shop/checkout_success.html")



# -------------------------
# SEARCH
# -------------------------
def search_products(request):
    query = request.GET.get("q", "")
    products = Product.objects.filter(name__icontains=query)
    return render(request, "shop/product_list_partial.html", {"products": products})


def ajax_search(request):
    q = request.GET.get("q", "")
    products = Product.objects.filter(name__icontains=q)[:10]
    return JsonResponse({
        "results": [{"name": p.name, "slug": p.slug, "price": float(p.price)} for p in products]
    })


# -------------------------
# AUTH / PROFILE / ORDERS / FEEDBACK
# -------------------------
def signup(request):
    """
    Two-step signup:
      1) User submits username,email,password,password2,phone -> server validates -> generate OTP -> send to email -> show OTP form.
      2) User submits OTP -> server verifies -> create user+profile -> authenticate & login -> redirect to product_list.
    OTP is stored in session with an expiry (5 minutes).
    """
    OTP_SESSION_KEY = "signup_otp_data"

    if request.method == "POST":

        # 🔁 RESEND OTP (AJAX)
        if request.POST.get("resend_otp") == "1":
            otp_data = request.session.get(OTP_SESSION_KEY)
            if not otp_data:
                return JsonResponse({"success": False}, status=400)

            otp = random.randint(100000, 999999)
            otp_data["otp"] = str(otp)
            otp_data["expires_at"] = time.time() + (5 * 60)
            request.session[OTP_SESSION_KEY] = otp_data
            request.session.modified = True

            subject = "Your signup OTP for My Shoppings"
            message = f"Hi {otp_data['username']},\n\nYour new OTP is: {otp}"
            from_email = settings.DEFAULT_FROM_EMAIL
            send_mail(subject, message, from_email, [otp_data["email"]])

            return JsonResponse({"success": True})

        # If OTP field present -> verify branch
        if request.POST.get("otp_verify") == "1":
            otp_provided = request.POST.get("otp", "").strip()
            otp_data = request.session.get(OTP_SESSION_KEY)
            if not otp_data:
                return render(request, "registration/signup.html", {
                    "form": CustomUserCreationForm(),
                    "otp_error": "Session expired. Please fill the signup form again."
                })
            if time.time() > otp_data.get("expires_at", 0):
                del request.session[OTP_SESSION_KEY]
                return render(request, "registration/signup.html", {
                    "form": CustomUserCreationForm(),
                    "otp_error": "OTP expired. Please submit signup form again to receive a new OTP."
                })
            if otp_provided != str(otp_data.get("otp")):
                return render(request, "registration/signup.html", {
                    "form": CustomUserCreationForm(initial={
                        "username": otp_data.get("username"),
                        "email": otp_data.get("email"),
                        "phone": otp_data.get("phone"),
                    }),
                    "show_otp": True,
                    "otp_error": "Invalid OTP. Please check your email and try again."
                })

            # OTP correct => create user
            username = otp_data.get("username")
            email = otp_data.get("email")
            password = otp_data.get("password")
            phone = otp_data.get("phone")

            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exists():
                del request.session[OTP_SESSION_KEY]
                return render(request, "registration/signup.html", {
                    "form": CustomUserCreationForm(),
                    "otp_error": "Username already taken. Please choose another."
                })
            if User.objects.filter(email__iexact=email).exists():
                del request.session[OTP_SESSION_KEY]
                return render(request, "registration/signup.html", {
                    "form": CustomUserCreationForm(),
                    "otp_error": "Email already registered. Try logging in instead."
                })

            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user, phone=phone, signup_provider="manual")
        


            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
            try:
                del request.session[OTP_SESSION_KEY]
            except KeyError:
                pass
            return redirect("shop:product_list")

        # Initial signup form submission
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password1")
            phone = form.cleaned_data.get("phone")

            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exists():
                form.add_error("username", "This username is already taken.")
                return render(request, "registration/signup.html", {"form": form})
            if User.objects.filter(email__iexact=email).exists():
                form.add_error("email", "An account with this email already exists.")
                return render(request, "registration/signup.html", {"form": form})

            otp = random.randint(100000, 999999)
            expires_at = time.time() + (5 * 60)

            request.session[OTP_SESSION_KEY] = {
                "username": username,
                "email": email,
                "password": password,
                "phone": phone,
                "otp": str(otp),
                "expires_at": expires_at
            }
            request.session.modified = True

            subject = "Your signup OTP for My Shoppings"
            message = f"Hi {username},\n\nYour OTP to complete signup is: {otp}\nThis OTP expires in 5 minutes.\n\nIf you did not request this, ignore this email."
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER if hasattr(settings, "EMAIL_HOST_USER") else None)
            recipient_list = [email]

            try:
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            except Exception as e:
                try:
                    del request.session[OTP_SESSION_KEY]
                except:
                    pass
                form.add_error(None, f"Failed to send OTP email: {e}. Check your email settings.")
                return render(request, "registration/signup.html", {"form": form})

            return render(request, "registration/signup.html", {
                "form": CustomUserCreationForm(initial={
                    "username": username,
                    "email": email,
                    "phone": phone
                }),
                "show_otp": True,
                "otp_sent_to": email
            })
        else:
            return render(request, "registration/signup.html", {"form": form})
    else:
        form = CustomUserCreationForm()
        return render(request, "registration/signup.html", {"form": form})


@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"signup_provider": "google"}  # Google fallback
    )

    if request.method == "POST":
        profile.phone = request.POST.get("phone", "").strip()
        profile.address = request.POST.get("address", "").strip()
        profile.save()
        return redirect("shop:profile")

    return render(request, "shop/profile.html", {
    "profile": profile,
    "address_limit_reached": profile.addresses.count() >= 3
})



@login_required
def my_orders(request):
    orders = Order.objects.filter(email=request.user.email).order_by("-created_at")
    return render(request, "shop/my_orders.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.email != request.user.email:
        return redirect("shop:my_orders")
    return render(request, "shop/order_detail.html", {"order": order})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.email != request.user.email:
        return redirect("shop:my_orders")
    if order.status not in ["paid", "cancelled"]:
        order.status = "cancelled"
        order.save()
    return redirect("shop:my_orders")

from django.contrib.auth.models import User

def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier", "").strip()
        password = request.POST.get("password", "")
        next_url = request.POST.get("next") or reverse("shop:product_list")

        user = None

        # 🔹 If email entered → get username
        if "@" in identifier:
            try:
                user_obj = User.objects.get(email__iexact=identifier)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            # 🔹 Username login
            user = authenticate(username=identifier, password=password)

        if user:
            login(request, user)
            return redirect(next_url)

        return render(request, "registration/login.html", {
            "error": "Invalid email/username or password",
            "next": next_url
        })

    return render(request, "registration/login.html", {
        "next": request.GET.get("next", "")
    })


def logout_view(request):
    logout(request)
    return redirect("shop:product_list")


# -------------------------
# PRODUCT FEEDBACK POST (AJAX)
# -------------------------
@require_POST
def product_feedback(request, product_id):
    """
    Accepts JSON (application/json) or form POST.
    Payload expected:
      { rating: int(1-5), message: str, reviewer_name: str (optional), reviewer_email: str (optional),
        update: bool (optional), feedback_id: int (optional) }

    Behavior:
      - If authenticated user already has a feedback for this product, it will be updated (no duplicate).
      - If payload contains 'update' + 'feedback_id' and the feedback belongs to the user, it will be updated.
      - Anonymous submissions create a new Feedback (approved=False).
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)

    try:
        if request.content_type and 'application/json' in request.content_type:
            import json
            payload = json.loads(request.body.decode('utf-8') or '{}')
            rating = int(payload.get('rating', 0))
            message = (payload.get('message') or '').strip()
            reviewer_name = (payload.get('reviewer_name') or '').strip()
            reviewer_email = (payload.get('reviewer_email') or '').strip()
            update_flag = bool(payload.get('update', False))
            feedback_id = payload.get('feedback_id') or None
        else:
            rating = int(request.POST.get('rating', 0))
            message = (request.POST.get('message') or '').strip()
            reviewer_name = (request.POST.get('reviewer_name') or '').strip()
            reviewer_email = (request.POST.get('reviewer_email') or '').strip()
            update_flag = bool(request.POST.get('update', False))
            feedback_id = request.POST.get('feedback_id', None)
    except Exception:
        return HttpResponseBadRequest("Invalid payload")

    if rating < 1 or rating > 5:
        return JsonResponse({"success": False, "error": "Invalid rating"}, status=400)

    approved = False
    fb = None

    if request.user.is_authenticated:
        existing = Feedback.objects.filter(product=product, user=request.user).first()
        if feedback_id:
            try:
                fid = int(feedback_id)
                candidate = Feedback.objects.filter(id=fid).first()
                if candidate and candidate.user == request.user and candidate.product_id == product.id:
                    fb = candidate
            except Exception:
                pass

        if not fb and existing:
            fb = existing

        if fb:
            fb.rating = rating
            fb.message = message
            fb.reviewer_name = request.user.get_full_name() or request.user.get_username()
            fb.reviewer_email = request.user.email or ''
            fb.approved = True
            fb.save()
            approved = fb.approved
        else:
            fb = Feedback.objects.create(
                product=product,
                rating=rating,
                message=message,
                user=request.user,
                reviewer_name=request.user.get_full_name() or request.user.get_username(),
                reviewer_email=(request.user.email or ''),
                approved=True
            )
            approved = True
    else:
        fb = Feedback.objects.create(
            product=product,
            rating=rating,
            message=message,
            reviewer_name=reviewer_name,
            reviewer_email=reviewer_email,
            approved=False
        )
        approved = False

    reviews_qs = product.feedbacks.filter(approved=True).order_by('-created_at')
    paginator = Paginator(reviews_qs, 5)
    try:
        reviews_page = paginator.page(1)
    except:
        reviews_page = []

    rendered = render_to_string('shop/reviews_list.html', {
        'reviews_page': reviews_page,
        'product': product,
        'avg_rating': product.average_rating(),
        'review_count': product.review_count(),
        'reviews_paginator': paginator,
    }, request=request)

    message_text = "Review submitted."
    if not approved:
        message_text = "Thanks — your review is submitted and will appear once approved."

    return JsonResponse({
        "success": True,
        "approved": bool(approved),
        "message": message_text,
        "html": rendered,
        "avg_rating": product.average_rating(),
        "review_count": product.review_count(),
        "feedback_id": fb.id if fb else None
    })


# -------------------------
# RSS feed for product reviews
# -------------------------
def product_reviews_rss(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    reviews = product.feedbacks.filter(approved=True).order_by('-created_at')[:50]

    feed_items = []
    for r in reviews:
        title = f"{r.rating} stars — {escape(r.reviewer_name or (r.user.get_username() if r.user else 'Anonymous'))}"
        link = request.build_absolute_uri(product.get_absolute_url() if hasattr(product, 'get_absolute_url') else reverse('shop:product_detail', args=[product.slug]))
        description = escape(r.short_message(500) or '')
        pubdate = r.created_at.strftime('%a, %d %b %Y %H:%M:%S +0000')
        feed_items.append({
            'title': title,
            'link': link,
            'description': description,
            'pubdate': pubdate,
            'guid': f"feedback-{r.id}"
        })

    rss = render_to_string('shop/reviews_rss.xml', {
        'product': product,
        'items': feed_items,
        'build_time': timezone.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    })
    return HttpResponse(rss, content_type='application/rss+xml')

@login_required
def add_address(request):
    profile = request.user.profile

    if request.method == "POST":
        if profile.addresses.count() >= 3:
            return redirect("shop:profile")

        address_text = request.POST.get("address", "").strip()
        if address_text:
            Address.objects.create(
                profile=profile,
                address=address_text
            )

    return redirect("shop:profile")

@login_required
def delete_address(request, address_id):
    profile = request.user.profile
    try:
        addr = profile.addresses.get(id=address_id)
        addr.delete()
    except:
        pass

    return redirect("shop:profile")

