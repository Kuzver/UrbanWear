# OAuth2-авторизация в UrbanWear

## 1. Назначение

В проекте UrbanWear реализована подготовка к OAuth2-авторизации через Google.

Для этого используется библиотека django-allauth.

OAuth2 позволяет пользователю входить на сайт через внешний аккаунт, например Google.

## 2. Подключенные приложения

В INSTALLED_APPS добавлены:

django.contrib.sites
allauth
allauth.account
allauth.socialaccount
allauth.socialaccount.providers.google

## 3. Middleware

В MIDDLEWARE добавлен:

allauth.account.middleware.AccountMiddleware

## 4. Backend авторизации

В settings.py добавлены backend-классы:

django.contrib.auth.backends.ModelBackend
allauth.account.auth_backends.AuthenticationBackend

## 5. Маршруты

В urbanwear/urls.py подключены маршруты django-allauth:

/accounts/

Страница входа:

/accounts/login/

## 6. Настройка Google OAuth2

Для полноценной работы OAuth2 необходимо:

1. Открыть Google Cloud Console.
2. Создать проект.
3. Настроить OAuth Consent Screen.
4. Создать OAuth Client ID.
5. Получить Client ID и Client Secret.
6. Войти в Django Admin.
7. Открыть раздел Social Applications.
8. Создать приложение Google.
9. Указать Client ID и Client Secret.
10. Привязать приложение к текущему сайту.

## 7. Redirect URI

Для локального запуска можно использовать redirect URI:

http://127.0.0.1:8000/accounts/google/login/callback/

Если проект размещён на сервере, вместо 127.0.0.1 указывается домен проекта.

## 8. SITE_ID

В settings.py указано:

SITE_ID = 1

Это нужно для связи OAuth2-приложения с текущим сайтом Django.

## 9. Проверка

Запустить сервер:

python manage.py runserver

Открыть:

http://127.0.0.1:8000/accounts/login/

Если Social Application настроен в админке, на странице входа будет доступна авторизация через Google.
