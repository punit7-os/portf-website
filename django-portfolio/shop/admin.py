from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Category, Product, Order

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
