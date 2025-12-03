# shop/context_processors.py
from .cart import Cart

def cart_counts(request):
    """
    Provides:
      - cart_unique_items: number of unique product IDs in session cart
      - cart_total_qty: total quantity across all items
    """
    try:
        cart = Cart(request)
        unique = len(cart.cart) if hasattr(cart, 'cart') else 0
        total_qty = len(cart)
    except Exception:
        unique = 0
        total_qty = 0

    return {
        "cart_unique_items": unique,
        "cart_total_qty": total_qty,
    }
