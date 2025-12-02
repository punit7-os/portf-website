# shop/cart.py
from decimal import Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Product

# session key
CART_SESSION_ID = getattr(settings, "CART_SESSION_ID", "cart")

class Cart:
    """
    Simple session-based cart.
    - The session stores only JSON-serializable primitives:
      { product_id (str) : { "quantity": int, "price": str } }
      price is stored as string (e.g. "163.00") to avoid Decimal in session.
    - When iterating, we yield dicts containing product object, price (Decimal),
      quantity (int), total_price (Decimal).
    """
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_ID)
        if not cart:
            cart = self.session[CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):
        """
        Add product to cart or update quantity.
        product: Product instance
        quantity: int
        update_quantity: if True sets quantity, otherwise increments
        """
        pid = str(product.id)
        price_str = format(product.price, 'f')  # convert Decimal to string without exponent
        if pid not in self.cart:
            self.cart[pid] = {"quantity": 0, "price": price_str}

        if update_quantity:
            self.cart[pid]["quantity"] = int(quantity)
        else:
            self.cart[pid]["quantity"] = int(self.cart[pid]["quantity"]) + int(quantity)

        # persist
        self.session.modified = True

    def remove(self, product):
        """
        Remove a product from the cart.
        product: Product instance or id
        """
        pid = str(product.id) if hasattr(product, 'id') else str(product)
        if pid in self.cart:
            del self.cart[pid]
            self.session.modified = True

    def clear(self):
        """ Remove cart from session """
        if CART_SESSION_ID in self.session:
            del self.session[CART_SESSION_ID]
            self.session.modified = True

    def __iter__(self):
        """
        Iterate over cart items and attach product objects.
        Yields dicts with keys: product, price (Decimal), quantity (int), total_price (Decimal)
        """
        product_ids = list(self.cart.keys())
        products = Product.objects.filter(id__in=product_ids)
        # map by id for quick access
        prod_map = {str(p.id): p for p in products}

        for pid, item in self.cart.items():
            product = prod_map.get(pid)
            price = Decimal(str(item["price"]))
            quantity = int(item["quantity"])
            total_price = price * quantity
            yield {
                "product": product,
                "price": price,
                "quantity": quantity,
                "total_price": total_price
            }

    def __len__(self):
        """Return total quantity of items in cart"""
        return sum(int(item["quantity"]) for item in self.cart.values())

    def get_total_price(self):
        total = Decimal("0.00")
        for item in self.__iter__():
            total += item["total_price"]
        return total
