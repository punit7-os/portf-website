from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from .models import Category, Product, Order
from .cart import Cart

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

    if request.method == "POST":
        email = request.POST.get("email", "")
        total = sum(item["price"] * item["quantity"] for item in cart)
        Order.objects.create(email=email, total_amount=total)
        cart.clear()
        return redirect("shop:checkout_success")

    items = []
    total = Decimal("0.00")
    for item in cart:
        items.append(item)
        total += item["total_price"]

    suggestions = Product.objects.filter(is_active=True).order_by('?')[:4]
    return render(request, "shop/checkout.html", {"cart": cart, "cart_items": items, "total": total, "suggestions": suggestions})


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
