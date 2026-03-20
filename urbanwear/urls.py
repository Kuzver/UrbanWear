from django.contrib import admin
from django.template.context_processors import static
from django.urls import path, include
from django.conf import settings
from shop import views   # абсолютный импорт (без точек)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),                     # маршруты из shop/urls.py
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),  # если своя регистрация
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)