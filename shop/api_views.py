from decimal import Decimal

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .filters import ProductFilter
from django.db.models import Avg, Count, Sum, Value, IntegerField, FloatField
from django.db.models.functions import Coalesce
from .models import Brand, Category, Order, Product, PromoCode, Review, Size, Wishlist
from decimal import Decimal
from typing import Any

from django.shortcuts import get_object_or_404
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import (
    Brand,
    Category,
    Order,
    Product,
    ProductImage,
    ProductVariant,
    PromoCode,
    Review,
    Size,
    Wishlist,
)
from .serializers import (
    BrandSerializer,
    CartSerializer,
    CategorySerializer,
    OrderSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
    ProductListSerializer,
    ProductVariantSerializer,
    PromoCodeSerializer,
    ReviewSerializer,
    SizeSerializer,
    WishlistSerializer,
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Чтение открыто всем, изменение доступно только сотруднику."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsOwnerOrStaff(permissions.BasePermission):
    """Пользователь работает со своими объектами, администратор — со всеми."""

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        owner = getattr(obj, 'user', None)
        return bool(owner == request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = 'slug'


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = 'slug'


class SizeViewSet(viewsets.ModelViewSet):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    permission_classes = (IsAdminOrReadOnly,)


class ProductViewSet(viewsets.ModelViewSet):
    """
    API для товаров интернет-магазина UrbanWear.

    Реализует:
    - получение списка товаров;
    - получение детальной карточки товара по slug;
    - создание, изменение и удаление товара сотрудником;
    - фильтрацию через Django Filter;
    - поиск через DRF SearchFilter;
    - сортировку через DRF OrderingFilter;
    - получение отзывов конкретного товара.
    """

    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = "slug"
    filterset_class = ProductFilter
    search_fields = ["name", "description", "sku", "category__name", "brand__name"]
    ordering_fields = [
        "price",
        "name",
        "created_at",
        "stock",
        "discount",
        "avg_rating",
        "sold_count",
        "wishlist_count",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Возвращает оптимизированный QuerySet товаров.

        В QuerySet добавлены аннотированные поля:
        - avg_rating: средний рейтинг товара;
        - sold_count: количество проданных единиц товара;
        - wishlist_count: сколько раз товар добавили в избранное.

        Важно:
        в текущих моделях проекта обратная связь OrderItem -> Product называется orderitem,
        а обратная связь Wishlist -> Product называется wishlisted_by.
        """
        return (
            Product.objects
            .select_related("category", "brand")
            .prefetch_related(
                "images",
                "variants__size",
                "recommended_products",
                "reviews",
                "wishlisted_by",
            )
            .exclude(price=0)
            .annotate(
                avg_rating=Coalesce(
                    Avg("reviews__rating"),
                    Value(0.0),
                    output_field=FloatField(),
                ),
                sold_count=Coalesce(
                    Sum("orderitem__quantity"),
                    Value(0),
                    output_field=IntegerField(),
                ),
                wishlist_count=Count("wishlisted_by", distinct=True),
            )
            .distinct()
        )

    def get_serializer_class(self):
        """
        Для списка товаров используется краткий сериализатор,
        для детальной карточки — расширенный сериализатор.
        """
        if self.action == "list":
            return ProductListSerializer
        return ProductDetailSerializer

    def get_serializer_context(self):
        """
        Передает в сериализатор список товаров, добавленных в избранное
        текущим пользователем.

        Это нужно для поля is_favorite в ProductListSerializer
        и ProductDetailSerializer.
        """
        context = super().get_serializer_context()
        user = self.request.user

        if user.is_authenticated:
            favorite_products = set(
                Wishlist.objects
                .filter(user=user)
                .values_list("product_id", flat=True)
            )
        else:
            favorite_products = set()

        context["favorite_products"] = favorite_products
        return context

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def reviews(self, request, slug=None):
        """
        Возвращает отзывы по конкретному товару.
        """
        product = self.get_object()
        reviews = product.reviews.select_related("user").all()
        serializer = ReviewSerializer(
            reviews,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.select_related('product').all()
    serializer_class = ProductImageSerializer
    permission_classes = (IsAdminOrReadOnly,)


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.select_related('product', 'size').all()
    serializer_class = ProductVariantSerializer
    permission_classes = (IsAdminOrReadOnly,)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrStaff)

    def get_queryset(self):
        reviews = Review.objects.select_related('product', 'user')
        product_slug = self.request.query_params.get('product', '').strip()
        if product_slug:
            reviews = reviews.filter(product__slug=product_slug)
        return reviews

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrStaff)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Wishlist.objects.select_related('user', 'product').all()
        return Wishlist.objects.select_related('user', 'product').filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrStaff)

    def get_queryset(self):
        orders = Order.objects.select_related('user').prefetch_related('items__product')
        if self.request.user.is_staff:
            return orders
        return orders.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PromoCodeViewSet(viewsets.ModelViewSet):
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer
    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = 'code'


class CartMixin:
    """
    Общая логика работы с корзиной в сессии Django.

    Корзина хранится в request.session в виде словаря:
        {
            "product_id": quantity
        }
    """

    MAX_ITEM_QUANTITY = 99

    def get_cart(self, request: Request) -> dict[str, int]:
        """
        Возвращает корзину из пользовательской сессии.
        """
        return request.session.get("cart", {})

    def save_cart(self, request: Request, cart: dict[str, int]) -> None:
        """
        Сохраняет корзину в пользовательскую сессию.
        """
        request.session["cart"] = cart
        request.session.modified = True

    def validate_quantity(self, quantity: int) -> None:
        """
        Проверяет корректность количества товара.

        Количество не может быть отрицательным.
        Также установлен технический лимит, чтобы пользователь
        не мог добавить нереалистично большое количество товара.
        """
        if quantity < 0:
            raise ValueError("Количество товара не может быть отрицательным.")

        if quantity > self.MAX_ITEM_QUANTITY:
            raise ValueError(
                f"Нельзя добавить больше {self.MAX_ITEM_QUANTITY} единиц одного товара."
            )

    def validate_product_available(self, product: Product, quantity: int) -> None:
        """
        Проверяет доступность товара для добавления в корзину.

        Проверки:
        - товар должен иметь положительную цену;
        - товар должен быть в наличии;
        - запрошенное количество не должно превышать складской остаток.
        """
        if product.price <= 0:
            raise ValueError("Товар с некорректной ценой нельзя добавить в корзину.")

        if product.stock <= 0:
            raise ValueError("Товара нет в наличии.")

        if quantity > product.stock:
            raise ValueError(
                f"Недостаточно товара на складе. Доступно: {product.stock}."
            )

    def build_cart_data(self, request: Request) -> dict[str, Any]:
        """
        Формирует структуру корзины с товарами, количеством и итоговыми суммами.
        """
        cart = self.get_cart(request)
        products = (
            Product.objects
            .select_related("category", "brand")
            .filter(id__in=cart.keys())
        )

        items = []
        subtotal = Decimal("0")
        discount_total = Decimal("0")

        for product in products:
            quantity = int(cart.get(str(product.id), 1))

            old_price = product.price * quantity
            unit_price = product.get_discounted_price()
            line_total = unit_price * quantity

            subtotal += old_price
            discount_total += old_price - line_total

            items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_total": line_total,
                }
            )

        delivery = Decimal("0")
        total = subtotal - discount_total + delivery

        return {
            "items": items,
            "subtotal": subtotal,
            "discount_total": discount_total,
            "delivery": delivery,
            "total": total,
        }

    def cart_response(
        self,
        request: Request,
        status_code: int = status.HTTP_200_OK,
    ) -> Response:
        """
        Возвращает сериализованный ответ корзины.
        """
        serializer = CartSerializer(
            self.build_cart_data(request),
            context={"request": request},
        )
        return Response(serializer.data, status=status_code)


class CartView(CartMixin, APIView):
    """
    API для просмотра и очистки корзины.
    """

    permission_classes = (permissions.AllowAny,)

    def get(self, request: Request) -> Response:
        """
        Возвращает текущую корзину.
        """
        return self.cart_response(request)

    def delete(self, request: Request) -> Response:
        """
        Полностью очищает корзину.
        """
        self.save_cart(request, {})
        return self.cart_response(request)


class CartAddView(CartMixin, APIView):
    """
    API для добавления товара в корзину.
    """

    permission_classes = (permissions.AllowAny,)

    def post(self, request: Request, product_id: int) -> Response:
        """
        Добавляет товар в корзину.

        Поддерживает два варианта:
        - если quantity не передан, добавляет 1 товар;
        - если quantity передан, добавляет указанное количество.
        """
        product = get_object_or_404(Product, id=product_id)
        cart = self.get_cart(request)
        product_id_str = str(product.id)

        try:
            quantity_to_add = int(request.data.get("quantity", 1))
        except (TypeError, ValueError):
            return Response(
                {"quantity": "Количество должно быть целым числом."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity_to_add <= 0:
            return Response(
                {"quantity": "Количество для добавления должно быть больше 0."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_quantity = int(cart.get(product_id_str, 0))
        new_quantity = current_quantity + quantity_to_add

        try:
            self.validate_quantity(new_quantity)
            self.validate_product_available(product, new_quantity)
        except ValueError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart[product_id_str] = new_quantity
        self.save_cart(request, cart)

        return self.cart_response(request, status.HTTP_201_CREATED)


class CartUpdateView(CartMixin, APIView):
    """
    API для изменения количества товара в корзине.
    """

    permission_classes = (permissions.AllowAny,)

    def patch(self, request: Request, product_id: int) -> Response:
        """
        Обновляет количество товара в корзине.

        Если quantity = 0, товар удаляется из корзины.
        """
        product = get_object_or_404(Product, id=product_id)
        cart = self.get_cart(request)
        product_id_str = str(product.id)

        try:
            quantity = int(request.data.get("quantity", 1))
        except (TypeError, ValueError):
            return Response(
                {"quantity": "Количество должно быть целым числом."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            self.validate_quantity(quantity)

            if quantity > 0:
                self.validate_product_available(product, quantity)
        except ValueError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity > 0:
            cart[product_id_str] = quantity
        else:
            cart.pop(product_id_str, None)

        self.save_cart(request, cart)

        return self.cart_response(request)


class CartRemoveView(CartMixin, APIView):
    """
    API для удаления товара из корзины.
    """

    permission_classes = (permissions.AllowAny,)

    def delete(self, request: Request, product_id: int) -> Response:
        """
        Удаляет товар из корзины.
        """
        cart = self.get_cart(request)
        cart.pop(str(product_id), None)
        self.save_cart(request, cart)

        return self.cart_response(request)