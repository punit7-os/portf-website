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

from .models import Category, Product, Order, Profile, Feedback
from .cart import Cart
from .forms import CustomUserCreationForm, ProfileForm

# Auth imports
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required

import razorpay
from django.conf import settings


def is_ajax_request(request):
    """
    Safe AJAX detection. Some clients set X-Requested-With header.
    """
    return (request.headers.get('x-requested-with') == 'XMLHttpRequest') or \
           (request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest')


# -------------------------
# PRODUCT LIST
# -------------------------
def product_list(request, slug=None):
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True).order_by('-created_at')
    current_category = None

    if slug:
        current_category = get_object_or_404(Category, slug=slug)
        products = products.filter(category=current_category)

    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    return render(request, "shop/product_list.html", {
        "categories": categories,
        "products": products,
        "current_category": current_category,
        "query": query or ""
    })


# -------------------------
# PRODUCT DETAIL (updated)
# -------------------------
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # Related products (full queryset provided to template; template does client-side paging)
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id)

    # fallback "all products" if none in same category
    all_products = None
    if not related_products.exists():
        all_products = Product.objects.filter(is_active=True).exclude(id=product.id)[:8]

    # Reviews: only approved ones for public display
    reviews_qs = product.feedbacks.filter(approved=True).order_by('-created_at')
    page = request.GET.get('rpage', 1)
    paginator = Paginator(reviews_qs, 5)  # 5 reviews per page
    try:
        reviews_page = paginator.page(page)
    except PageNotAnInteger:
        reviews_page = paginator.page(1)
    except EmptyPage:
        reviews_page = paginator.page(paginator.num_pages)

    # If AJAX request specifically asked for a reviews page, return only the reviews partial.
    # This makes "See more reviews" faster (JS expects HTML fragment).
    if is_ajax_request(request) and request.GET.get('rpage'):
        rendered = render_to_string('shop/reviews_list.html', {
            'reviews_page': reviews_page,
            'product': product,
            'avg_rating': product.average_rating(),
            'review_count': product.review_count(),
            'reviews_paginator': paginator,
        }, request=request)
        return HttpResponse(rendered)

    avg_rating = float(product.average_rating() or 0.0)
    review_count = product.review_count()

    # compute display name once in the view to avoid template expression issues
    if request.user.is_authenticated:
        display_name = request.user.get_full_name() or request.user.get_username()
    else:
        display_name = ''

    # Provide user_feedback if exists (may be pending or approved)
    user_feedback = None
    if request.user.is_authenticated:
        user_feedback = product.feedbacks.filter(user=request.user).first()

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'all_products': all_products,
        'reviews_page': reviews_page,
        'avg_rating': avg_rating,
        'review_count': review_count,
        'reviews_paginator': paginator,
        'display_name': display_name,
        'user_feedback': user_feedback,
    })


# -------------------------
# ADD TO CART (AJAX SAFE)
# -------------------------
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = Cart(request)
    qty = 1
    try:
        if request.method == "POST":
            qty = int(request.POST.get("qty", 1))
    except Exception:
        qty = 1

    cart.add(product=product, quantity=qty, update_quantity=False)

    try:
        unique_count = len(cart.cart) if hasattr(cart, 'cart') else 0
    except Exception:
        unique_count = 0
    try:
        total_qty = len(cart)
    except Exception:
        total_qty = 0

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

    cart_total = float(cart.get_total_price())
    try:
        cart_unique_count = len(cart.cart) if hasattr(cart, 'cart') else 0
    except:
        cart_unique_count = 0
    try:
        total_qty = len(cart)
    except:
        total_qty = 0

    return JsonResponse({
        "success": True,
        "row_total": row_total,
        "cart_total": cart_total,
        "cart_count": cart_unique_count,
        "total_qty": total_qty,
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

    return render(request, "shop/cart_detail.html", {"items": items, "total": total})


# -------------------------
# CHECKOUT + PAYMENT
# -------------------------
def checkout(request):
    buy_id = request.GET.get('buy')
    buy_qty = request.GET.get('qty')

    cart = Cart(request)

    try:
        buy_qty = int(buy_qty) if buy_qty else 1
    except:
        buy_qty = 1

    if buy_id:
        try:
            product = Product.objects.get(id=int(buy_id))
        except:
            return redirect("shop:product_list")
        cart.clear()
        cart.add(product=product, quantity=buy_qty)

    if len(cart) == 0:
        return redirect("shop:product_list")

    if request.method == "POST":
        posted_email = request.POST.get("email", "").strip()
        if posted_email:
            email = posted_email
        elif request.user.is_authenticated and request.user.email:
            email = request.user.email
        else:
            suggestions = Product.objects.filter(is_active=True).order_by('?')[:4]
            error = "Please provide an email address to receive the receipt."
            items = list(cart)
            total = cart.get_total_price()
            return render(request, "shop/checkout.html", {
                "cart": items,
                "total": total,
                "suggestions": suggestions,
                "error": error
            })

        total = cart.get_total_price()
        Order.objects.create(email=email, total_amount=total)
        cart.clear()
        return redirect("shop:checkout_success")

    items = list(cart)
    total = cart.get_total_price()
    suggestions = Product.objects.filter(is_active=True).order_by('?')[:4]
    return render(request, "shop/checkout.html", {
        "cart": items,
        "total": total,
        "suggestions": suggestions
    })


def initiate_payment(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid")

    cart = Cart(request)
    if len(cart) == 0:
        return JsonResponse({"error": "Cart empty"}, status=400)

    email = request.POST.get("email","").strip()
    if not email:
        if request.user.is_authenticated:
            email = request.user.email

    if not email:
        return JsonResponse({"error":"Email required"}, status=400)

    total = cart.get_total_price()
    paise = int(total * 100)

    order = Order.objects.create(email=email, total_amount=total)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    data = {
        "amount": paise,
        "currency":"INR",
        "receipt": f"order_{order.id}",
        "notes": {"order_id": str(order.id)}
    }

    rzp_order = client.order.create(data=data)
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
def payment_handler(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid")

    order_id = request.POST.get("order_id")
    payment_id = request.POST.get("razorpay_payment_id")
    signature = request.POST.get("razorpay_signature")
    razorpay_order_id = request.POST.get("razorpay_order_id")

    if not all([order_id, payment_id, signature, razorpay_order_id]):
        return HttpResponseBadRequest("Missing params")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature
        })
    except:
        Order.objects.filter(id=order_id).update(status="failed")
        return HttpResponseBadRequest("Signature failed")

    Order.objects.filter(id=order_id).update(
        status="paid",
        razorpay_payment_id=payment_id,
        razorpay_signature=signature
    )

    Cart(request).clear()
    return JsonResponse({"status":"paid"})


def checkout_success(request):
    return render(request, "shop/checkout_success.html")


# -------------------------
# SEARCH ROUTES
# -------------------------
def search_products(request):
    query = request.GET.get('q','')
    products = Product.objects.filter(name__icontains=query)
    return render(request, "shop/product_list_partial.html", {"products":products})


def ajax_search(request):
    q = request.GET.get('q','')
    products = Product.objects.filter(name__icontains=q)[:10]
    data = [{"name":p.name, "slug":p.slug, "price":float(p.price)} for p in products]
    return JsonResponse({"results":data})


# -------------------------
# BUY NOW
# -------------------------
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    qty = int(request.POST.get("qty",1))
    cart = Cart(request)
    cart.add(product, qty)
    return redirect("shop:checkout")


# -------------------------
# AUTH / PROFILE
# -------------------------
def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect("shop:product_list")
    else:
        form = CustomUserCreationForm()

    return render(request, "registration/signup.html", {"form":form})


@login_required
def profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("shop:profile")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "shop/profile.html", {"form":form})


@login_required
def my_orders(request):
    orders = Order.objects.filter(email=request.user.email).order_by("-created_at")
    return render(request, "shop/my_orders.html", {"orders":orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.email != request.user.email:
        return redirect("shop:my_orders")
    return render(request, "shop/order_detail.html", {"order":order})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.email != request.user.email:
        return redirect("shop:my_orders")
    if order.status not in ["paid","cancelled"]:
        order.status = "cancelled"
        order.save()
    return redirect("shop:my_orders")


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

    # Support both JSON body and form-encoded
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

    # Default values
    approved = False
    fb = None

    # If user is authenticated, try to update existing feedback instead of creating duplicate
    if request.user.is_authenticated:
        existing = Feedback.objects.filter(product=product, user=request.user).first()
        # If an explicit feedback_id/update is provided, respect and verify ownership
        if feedback_id:
            try:
                fid = int(feedback_id)
                candidate = Feedback.objects.filter(id=fid).first()
                if candidate and candidate.user == request.user and candidate.product_id == product.id:
                    fb = candidate
            except Exception:
                fb = fb  # no-op

        if not fb and existing:
            fb = existing

        if fb:
            # update fields
            fb.rating = rating
            fb.message = message
            fb.reviewer_name = request.user.get_full_name() or request.user.get_username()
            fb.reviewer_email = request.user.email or ''
            # auto-approve authenticated user's reviews by default
            fb.approved = True
            fb.save()
            approved = fb.approved
        else:
            # create new for authenticated user (auto-approve)
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
        # anonymous creation (moderation required)
        fb = Feedback.objects.create(
            product=product,
            rating=rating,
            message=message,
            reviewer_name=reviewer_name,
            reviewer_email=reviewer_email,
            approved=False
        )
        approved = False

    # Prepare public reviews (only approved ones), first page
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

    message = "Review submitted."
    if not approved:
        message = "Thanks — your review is submitted and will appear once approved."

    return JsonResponse({
        "success": True,
        "approved": bool(approved),
        "message": message,
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
