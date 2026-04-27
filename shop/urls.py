from django.urls import path
from . import views
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # ← ГЛАВНАЯ должна быть первой

    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),

    path('create/', views.product_create, name='product_create'),
    path('<slug:slug>/update/', views.product_update, name='product_update'),
    path('<slug:slug>/delete/', views.product_delete, name='product_delete'),

    path('increase-prices/', views.increase_prices, name='increase_prices'),
    path('product/<slug:slug>/upload-images/', views.upload_product_images, name='upload_images'),

    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/', views.cart_detail, name='cart'),

    path('search/', views.product_search, name='product_search'),
    path('orders/<int:order_id>/pdf/', views.export_order_pdf_view, name='order_pdf'),
]