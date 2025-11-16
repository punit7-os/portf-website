from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from .models import Category, Product, Order
from .cart import Cart

# Auth imports
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm

import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse


CART_KEY = "cart"

# --- Utility Cart Functions ---
def _get_cart(session):
    return session.get(CART_KEY, {})

def _save_cart(session, cart):
    session[CART_KEY] = cart
    session.modified = True


# 🏠 PRODUCT LIST
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


# 📦 PRODUCT DETAIL
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)

    # get related products
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id)[:4]

    # if no related products, get random products instead
    all_products = None
    if not related_products.exists():
        all_products = Product.objects.filter(is_active=True).exclude(id=product.id)[:4]

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'all_products': all_products,
    })


# ➕ ADD TO CART
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
    return redirect("shop:cart_detail")


# ❌ REMOVE FROM CART
def cart_remove(request, product_id):
    cart = Cart(request)
    try:
        product = Product.objects.get(id=product_id)
        cart.remove(product)
    except Product.DoesNotExist:
        pass
    return redirect("shop:cart_detail")


# 🛒 VIEW CART
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


# 💳 CHECKOUT
def checkout(request):
    """
    If ?buy=<product_id> is present, clear cart, add only that product, then render checkout.
    Otherwise use current cart.
    """
    buy_id = request.GET.get('buy')
    cart = Cart(request)

    if buy_id:
        try:
            product = Product.objects.get(id=int(buy_id), is_active=True)
        except (Product.DoesNotExist, ValueError):
            return redirect('shop:product_list')
        # Single product checkout mode
        cart.clear()
        cart.add(product=product, quantity=1)

    if len(cart) == 0:
        return redirect("shop:product_list")

    # If POST -> place order
    if request.method == "POST":
        # Prefer posted email, but if user is logged in and has an email, use that
        posted_email = request.POST.get("email", "").strip()
        if posted_email:
            email = posted_email
        elif request.user.is_authenticated and request.user.email:
            email = request.user.email
        else:
            # no email provided and user not logged in -> re-render with error
            suggestions = Product.objects.filter(is_active=True).order_by('?')[:4]
            error = "Please provide an email address to receive the receipt."
            items = []
            total = Decimal("0.00")
            for item in cart:
                items.append(item)
                total += item["total_price"]
            return render(request, "shop/checkout.html", {
                "cart": cart,
                "cart_items": items,
                "total": total,
                "suggestions": suggestions,
                "error": error
            })

        total = sum(item["price"] * item["quantity"] for item in cart)
        Order.objects.create(email=email, total_amount=total)
        cart.clear()
        return redirect("shop:checkout_success")

    # GET -> render checkout
    items = []
    total = Decimal("0.00")
    for item in cart:
        items.append(item)
        total += item["total_price"]

    suggestions = Product.objects.filter(is_active=True).order_by('?')[:4]
    return render(request, "shop/checkout.html", {
        "cart": cart,
        "cart_items": items,
        "total": total,
        "suggestions": suggestions
    })

def initiate_payment(request):
    """
    Called when user clicks "Pay" on checkout (POST).
    Creates a local Order object AND Razorpay Order, returns needed info to JS.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")

    cart = Cart(request)
    if len(cart) == 0:
        return JsonResponse({"error": "Cart is empty"}, status=400)

    # decide email
    posted_email = request.POST.get("email", "").strip()
    if posted_email:
        email = posted_email
    elif request.user.is_authenticated and request.user.email:
        email = request.user.email
    else:
        return JsonResponse({"error": "Email required"}, status=400)

    # compute amount in paise (Razorpay expects amount in smallest currency unit)
    total = sum(item["price"] * item["quantity"] for item in cart)
    amount_paise = int(total * 100)  # Decimal -> paise (int)

    # create local Order
    order = Order.objects.create(email=email, total_amount=total)

    # create razorpay order
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    DATA = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"order_{order.id}",
        "notes": {"order_id": str(order.id)}
    }
    razorpay_order = client.order.create(data=DATA)

    # save razorpay order id
    order.razorpay_order_id = razorpay_order.get('id')
    order.save()

    # return data to frontend
    return JsonResponse({
        "razorpay_order_id": order.razorpay_order_id,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "amount": amount_paise,
        "order_id": order.id,
        "currency": "INR",
    })


@csrf_exempt
def payment_handler(request):
    """
    This endpoint handles the verification after payment is completed (POST from frontend)
    and also can be used as webhook endpoint (recommended to verify signature).
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")

    data = request.POST

    # Expected fields from Razorpay checkout success
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_signature = data.get('razorpay_signature')
    order_id = data.get('order_id')  # our DB order id (passed via checkout)

    # Validate presence
    if not (razorpay_payment_id and razorpay_order_id and razorpay_signature and order_id):
        return HttpResponseBadRequest("Missing parameters")

    # verify signature using razorpay util
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }
    try:
        client.utility.verify_payment_signature(params_dict)
    except razorpay.errors.SignatureVerificationError:
        # mark order failed
        try:
            order = Order.objects.get(id=int(order_id))
            order.status = 'failed'
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.save()
        except Order.DoesNotExist:
            pass
        return HttpResponseBadRequest("Signature verification failed")

    # signature ok -> mark paid, clear cart
    try:
        order = Order.objects.get(id=int(order_id))
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature
        order.status = 'paid'
        order.save()
    except Order.DoesNotExist:
        pass

    # clear cart
    cart = Cart(request)
    cart.clear()

    # respond OK
    return JsonResponse({"status": "paid", "order_id": order_id})


# ✅ CHECKOUT SUCCESS
def checkout_success(request):
    suggestions = Product.objects.filter(is_active=True).order_by('?')[:4]
    return render(request, "shop/checkout_success.html", {"suggestions": suggestions})


# 🔍 SEARCH (FULL & AJAX)
def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query) if query else Product.objects.all()
    return render(request, 'shop/product_list_partial.html', {'products': products})

def ajax_search(request):
    q = request.GET.get('q', '')
    results = []
    if q:
        products = Product.objects.filter(name__icontains=q)[:10]
        results = [{"name": p.name, "slug": p.slug, "price": float(p.price)} for p in products]
    return JsonResponse({"results": results})


# ⚡ BUY NOW (Redirect to checkout)
def buy_now(request, product_id):
    """
    When user clicks Buy Now, redirect directly to checkout with the product preloaded.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    return redirect(f"{reverse('shop:checkout')}?buy={product.id}")


# --- AUTH: Signup with email validation ---
def signup(request):
    """
    Signup using CustomUserCreationForm which includes an email field and validates uniqueness.
    On successful signup the user is authenticated and logged in.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Save user but ensure we attach the email to the user instance
            user = form.save(commit=False)
            user.email = form.cleaned_data.get('email')
            user.save()
            # authenticate & login
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            if user:
                login(request, user)
                return redirect('shop:product_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


def logout_view(request):
    # logs out and redirects
    logout(request)
    return redirect('shop:product_list')