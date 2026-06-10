from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api_views, views

router = DefaultRouter()
router.register(r'categories', api_views.CategoryViewSet, basename='api-category')
router.register(r'brands', api_views.BrandViewSet, basename='api-brand')
router.register(r'sizes', api_views.SizeViewSet, basename='api-size')
router.register(r'products', api_views.ProductViewSet, basename='api-product')
router.register(r'product-images', api_views.ProductImageViewSet, basename='api-product-image')
router.register(r'product-variants', api_views.ProductVariantViewSet, basename='api-product-variant')
router.register(r'reviews', api_views.ReviewViewSet, basename='api-review')
router.register(r'wishlist', api_views.WishlistViewSet, basename='api-wishlist')
router.register(r'orders', api_views.OrderViewSet, basename='api-order')
router.register(r'promo-codes', api_views.PromoCodeViewSet, basename='api-promo-code')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/cart/', api_views.CartView.as_view(), name='api-cart'),
    path('api/cart/add/<int:product_id>/', api_views.CartAddView.as_view(), name='api-cart-add'),
    path('api/cart/update/<int:product_id>/', api_views.CartUpdateView.as_view(), name='api-cart-update'),
    path('api/cart/remove/<int:product_id>/', api_views.CartRemoveView.as_view(), name='api-cart-remove'),

    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('product/<slug:product_slug>/add_review/', views.add_review, name='add_review'),

    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),

    path('create/', views.product_create, name='product_create'),
    path('<slug:slug>/update/', views.product_update, name='product_update'),
    path('<slug:slug>/delete/', views.product_delete, name='product_delete'),

    path('increase-prices/', views.increase_prices, name='increase_prices'),
    path('product/<slug:slug>/upload-images/', views.upload_product_images, name='upload_images'),

    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),

    path('search/', views.product_search, name='product_search'),
    path('orders/<int:order_id>/pdf/', views.export_order_pdf_view, name='order_pdf'),
]
