from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory

from .models import Brand, Category, Order, OrderItem, Product, Review, Wishlist
from .serializers import OrderSerializer, ProductDetailSerializer, ReviewSerializer


class UrbanWearAPITests(TestCase):
    """
    Тесты основных функций интернет-магазина UrbanWear.

    Проверяются:
    - бизнес-валидация;
    - расчёт скидки;
    - работа API товаров;
    - фильтрация;
    - аннотации;
    - избранное через context;
    - корзина;
    - отзывы;
    - заказы.
    """

    def setUp(self):
        """
        Создаёт базовые тестовые данные.
        """
        self.client = APIClient()
        self.factory = APIRequestFactory()

        self.user = User.objects.create_user(
            username="buyer",
            email="buyer@example.com",
            password="password123",
        )

        self.admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password123",
        )

        self.category = Category.objects.create(
            name="Худи",
            slug="hoodie",
        )

        self.brand = Brand.objects.create(
            name="Urban Core",
            slug="urban-core",
        )

        self.product = Product.objects.create(
            category=self.category,
            brand=self.brand,
            name="Test Hoodie",
            slug="test-hoodie",
            sku="UW-TEST-001",
            price=Decimal("1000.00"),
            discount=10,
            stock=5,
            description="Тестовое худи UrbanWear",
        )

    def test_discounted_price_calculation(self):
        """
        Проверяет корректный расчёт цены со скидкой.
        """
        self.assertEqual(
            self.product.get_discounted_price(),
            Decimal("900.00"),
        )

    def test_product_list_api_returns_products(self):
        """
        Проверяет, что API списка товаров возвращает товары.
        """
        url = reverse("api-product-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Test Hoodie")

    def test_product_filter_by_category(self):
        """
        Проверяет фильтрацию товаров по категории через API.
        """
        url = reverse("api-product-list")
        response = self.client.get(url, {"category": "hoodie"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_product_filter_by_price_range(self):
        """
        Проверяет фильтрацию товаров по диапазону цены.
        """
        url = reverse("api-product-list")
        response = self.client.get(
            url,
            {
                "min_price": "900",
                "max_price": "1100",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_product_annotations_are_returned(self):
        """
        Проверяет аннотированные поля товара:
        средний рейтинг, продажи и количество добавлений в избранное.
        """
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment="Отличный товар",
        )

        Wishlist.objects.create(
            user=self.user,
            product=self.product,
        )

        order = Order.objects.create(
            user=self.user,
            delivery_address="Москва, улица Тестовая, дом 1",
            city="Москва",
            postal_code="123456",
            contact_phone="+79990000000",
            total_amount=Decimal("2700.00"),
        )

        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=3,
            price=Decimal("900.00"),
        )

        url = reverse("api-product-list")
        response = self.client.get(url)

        product_data = response.data["results"][0]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(product_data["avg_rating"], 5.0)
        self.assertEqual(product_data["sold_count"], 3)
        self.assertEqual(product_data["wishlist_count"], 1)

    def test_is_favorite_field_for_authenticated_user(self):
        """
        Проверяет поле is_favorite, которое передаётся через context сериализатора.
        """
        Wishlist.objects.create(
            user=self.user,
            product=self.product,
        )

        self.client.force_authenticate(user=self.user)

        url = reverse("api-product-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["results"][0]["is_favorite"])

    def test_add_product_to_cart(self):
        """
        Проверяет добавление товара в корзину через API.
        """
        url = reverse("api-cart-add", args=[self.product.id])
        response = self.client.post(
            url,
            {"quantity": 2},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 2)

    def test_cannot_add_more_than_stock_to_cart(self):
        """
        Проверяет запрет добавления товара сверх складского остатка.
        """
        url = reverse("api-cart-add", args=[self.product.id])
        response = self.client.post(
            url,
            {"quantity": 99},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)

    def test_review_rating_validation(self):
        """
        Проверяет, что отзыв не может иметь рейтинг больше 5.
        """
        serializer = ReviewSerializer(
            data={
                "product": self.product.id,
                "rating": 6,
                "comment": "Некорректная оценка",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("rating", serializer.errors)

    def test_duplicate_review_validation(self):
        """
        Проверяет запрет повторного отзыва на один товар от одного пользователя.
        """
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            comment="Первый отзыв",
        )

        request = self.factory.post("/")
        request.user = self.user

        serializer = ReviewSerializer(
            data={
                "product": self.product.id,
                "rating": 4,
                "comment": "Повторный отзыв",
            },
            context={"request": request},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_product_price_validation(self):
        """
        Проверяет, что товар нельзя создать с нулевой ценой.
        """
        serializer = ProductDetailSerializer(
            data={
                "category_id": self.category.id,
                "brand_id": self.brand.id,
                "name": "Invalid Product",
                "sku": "UW-BAD-001",
                "price": "0.00",
                "discount": 0,
                "stock": 10,
                "description": "Некорректный товар",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)

    def test_order_delivery_address_validation(self):
        """
        Проверяет валидацию адреса доставки.
        """
        serializer = OrderSerializer(
            data={
                "delivery_address": "дом",
                "city": "Москва",
                "postal_code": "123456",
                "contact_phone": "+79990000000",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("delivery_address", serializer.errors)

    def test_order_total_amount_validation_method(self):
        """
        Проверяет валидацию итоговой суммы заказа.
        """
        serializer = OrderSerializer()

        with self.assertRaises(Exception):
            serializer.validate_total_amount(Decimal("-100.00"))
