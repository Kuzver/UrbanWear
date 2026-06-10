"""
Главная маршрутизация проекта UrbanWear.

Здесь подключаются:
- административная панель Django;
- пользовательские маршруты приложения shop;
- маршруты Django REST Framework;
- авторизация через django-allauth;
- Django Silk для профилирования;
- Debug Toolbar в режиме DEBUG;
- раздача media-файлов при локальной разработке.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),

    path("api-auth/", include("rest_framework.urls")),
    path("accounts/", include("allauth.urls")),
    path("silk/", include("silk.urls", namespace="silk")),

    path("", include("shop.urls")),
]


if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )