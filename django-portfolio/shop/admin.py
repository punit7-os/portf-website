from django.contrib import admin 
from .models import Category, Product, Order, Feedback

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name","category","price","is_active")
    list_filter = ("category","is_active")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id","email","total_amount","created_at")
    readonly_fields = ("created_at",)

# Feedback admin
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "rating", "short_reviewer", "approved", "created_at")
    list_filter = ("approved", "rating", "created_at")
    search_fields = ("reviewer_name", "reviewer_email", "message", "product__name")
    readonly_fields = ("created_at",)
    actions = ["approve_reviews", "reject_reviews"]

    def short_reviewer(self, obj):
        if obj.user:
            return obj.user.get_username()
        return obj.reviewer_name or "(anonymous)"
    short_reviewer.short_description = "Reviewer"

    def approve_reviews(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f"{updated} review(s) approved.")
    approve_reviews.short_description = "Approve selected reviews"

    def reject_reviews(self, request, queryset):
        updated = queryset.update(approved=False)
        self.message_user(request, f"{updated} review(s) rejected/unapproved.")
    reject_reviews.short_description = "Reject / mark selected reviews unapproved"
