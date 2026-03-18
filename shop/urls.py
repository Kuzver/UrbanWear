from django.urls import path
from . import views
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
]