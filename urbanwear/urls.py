from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static  # правильный импорт

from shop import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)