# REST API UrbanWear

В проект добавлен API-слой на Django REST Framework. Основные HTML-страницы сохранены, но ключевые сущности интернет-магазина теперь доступны через RESTful endpoints.

## Основные маршруты

| Метод | URL | Назначение |
|---|---|---|
| GET | `/api/products/` | Список товаров с пагинацией, поиском и фильтрами |
| POST | `/api/products/` | Создание товара сотрудником |
| GET | `/api/products/<slug>/` | Детальная карточка товара |
| PUT/PATCH | `/api/products/<slug>/` | Изменение товара сотрудником |
| DELETE | `/api/products/<slug>/` | Удаление товара сотрудником |
| GET | `/api/categories/` | Список категорий |
| GET | `/api/brands/` | Список брендов |
| GET | `/api/sizes/` | Список размеров |
| GET/POST | `/api/reviews/` | Получение и добавление отзывов |
| GET/POST | `/api/orders/` | Работа с заказами пользователя |
| GET/POST | `/api/wishlist/` | Работа с избранным пользователя |
| GET | `/api/promo-codes/` | Список промокодов |
| GET | `/api/cart/` | Получение корзины из сессии |
| POST | `/api/cart/add/<product_id>/` | Добавление товара в корзину |
| PATCH | `/api/cart/update/<product_id>/` | Изменение количества товара |
| DELETE | `/api/cart/remove/<product_id>/` | Удаление товара из корзины |
| DELETE | `/api/cart/` | Очистка корзины |

## Примеры фильтрации товаров

```text
/api/products/?q=hoodie
/api/products/?category=shoes
/api/products/?brand=nike
/api/products/?size=M
/api/products/?min_price=1000&max_price=5000
/api/products/?discount=1
/api/products/?ordering=price
/api/products/?ordering=-created_at
