from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'shop'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('search/', views.search_products, name='search_products'),
    path('c/<slug:slug>/', views.product_list, name='product_list_by_category'),
    path('ajax/search/', views.ajax_search, name='ajax_search'),

    # Cart
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),

    # Checkout & Payments
    path('checkout/', views.checkout, name='checkout'),
    path('payment/initiate/', views.initiate_payment, name='payment_initiate'),
    path('payment/handler/', views.payment_handler, name='payment_handler'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),

    # Buy Now
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),

    # Authentication
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profile & Orders — IMPORTANT: point to the proper views
    path('profile/', views.profile, name='profile'),
    path('orders/', views.my_orders, name='my_orders'),

    # Product Detail (keep last)
    path('<slug:slug>/', views.product_detail, name='product_detail'),

    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    # add this import at top if not present:
    # from . import views

    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),



]
