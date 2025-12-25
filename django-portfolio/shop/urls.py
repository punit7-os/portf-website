# shop/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'shop'

urlpatterns = [

    path("wishlist/", views.wishlist_page, name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", views.toggle_wishlist, name="toggle_wishlist"),
    # Home / Products
    path('', views.product_list, name='product_list'),
    path('search/', views.search_products, name='search_products'),
    path('c/<slug:slug>/', views.product_list, name='product_list_by_category'),
    path('ajax/search/', views.ajax_search, name='ajax_search'),

    # Cart
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),

    # Checkout & Payments
    path('checkout/', views.checkout, name='checkout'),
    path('payment/initiate/', views.initiate_payment, name='payment_initiate'),
    path('payment/handler/', views.payment_handler, name='payment_handler'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),

    # Buy Now
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),

    # Authentication
    path('signup/', views.signup, name='signup'),
    # path('login/', auth_views.LoginView.as_view(
    #     template_name='registration/login.html'
    # ), name='login'),
    path('login/', views.login_view, name='login'),

    path('logout/', views.logout_view, name='logout'),

    # Profile & Orders
    path('profile/', views.profile, name='profile'),
    path('orders/', views.my_orders, name='my_orders'),

    path('payment/clear-buy-now/', views.clear_buy_now_session, name='clear_buy_now'),


    # ✅ ORDER DETAIL (FIX FOR YOUR ERROR)
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),

    # ✅ CANCEL ORDER (USED IN TEMPLATE)
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),

    # Product Feedback
    path('feedback/<int:product_id>/', views.product_feedback, name='product_feedback'),
    path('feedback/rss/<int:product_id>/', views.product_reviews_rss, name='product_reviews_rss'),

    path("profile/address/add/", views.add_address, name="add_address"),
    path("profile/address/delete/<int:address_id>/", views.delete_address, name="delete_address"),

    # Product Detail (KEEP LAST)
    path('<slug:slug>/', views.product_detail, name='product_detail'),
    # urls.py (ADD BELOW profile path)

]
