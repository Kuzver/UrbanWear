from django.contrib import admin
from django.urls import path, include  # добавили include
from django.conf import settings
from django.urls import include, path

from urbanwear.shop import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),  # если своя регистрация
    path('__debug__/', include(debug_toolbar.urls)),    # все запросы к корню будут идти в shop.urls
]
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]