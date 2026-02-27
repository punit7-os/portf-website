from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Avg, Count

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True)  # simple for local demo
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def average_rating(self):
        """
        Returns average rating (float) for approved reviews or 0.0
        """
        agg = self.feedbacks.filter(approved=True).aggregate(avg=Avg('rating'))
        return float(agg['avg'] or 0.0)

    def review_count(self):
        return self.feedbacks.filter(approved=True).count()

class Order(models.Model):
    STATUS_CHOICES = (
        ('created', 'Created'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    )

    email = models.EmailField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    # Razorpay fields
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')

    def __str__(self):
        return f"Order #{self.id} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name if self.product else 'Item'} × {self.quantity}"


# models.py

# models.py

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # ✅ NEW: signup source
    signup_provider = models.CharField(
        max_length=20,
        choices=(("manual", "Manual"), ("google", "Google")),
        default="manual"
    )

    def __str__(self):
        return f"{self.user.username} profile"



# ---------- Feedback model ----------
class Feedback(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    message = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    reviewer_name = models.CharField(max_length=120, blank=True)   # for anonymous name
    reviewer_email = models.EmailField(blank=True)                 # for anonymous email
    approved = models.BooleanField(default=False, db_index=True)   # moderation flag
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Product Feedback"
        verbose_name_plural = "Product Feedbacks"
        indexes = [
            models.Index(fields=['product', 'approved', 'created_at'])
        ]

    def __str__(self):
        who = self.reviewer_name or (self.user.get_full_name() if self.user else "Anonymous")
        return f"{self.product.name} — {self.rating} ★ by {who}"

    def short_message(self, length=150):
        return (self.message[:length] + '...') if self.message and len(self.message) > length else (self.message or '')
# models.py (ADD BELOW Profile model)

class Address(models.Model):
    profile = models.ForeignKey(
        Profile,
        related_name="addresses",
        on_delete=models.CASCADE
    )
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Address for {self.profile.user.username}"

# shop/models.py

from django.conf import settings

class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlisted_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user} - {self.product}"
