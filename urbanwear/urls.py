from django.contrib import admin
from django.urls import path, include  # добавили include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),     # все запросы к корню будут идти в shop.urls
]
