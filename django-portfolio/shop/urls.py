from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Product pages
    path('', views.product_list, name='product_list'),
    path('search/', views.search_products, name='search_products'),
    path('c/<slug:slug>/', views.product_list, name='product_list_by_category'),
    path('<slug:slug>/', views.product_detail, name='product_detail'),

    # Cart pages
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),

    # Checkout
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),

    # # Pasteables
    


]
