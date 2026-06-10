from decimal import Decimal

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .filters import ProductFilter

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
    ordering_fields = ["price", "name", "created_at", "stock", "discount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Возвращает оптимизированный QuerySet товаров.

        Здесь специально оставлена только базовая выборка.
        Фильтрация по цене, категории, бренду, размеру, скидке и наличию
        вынесена в ProductFilter из файла shop/filters.py.
        """
        return (
            Product.objects
            .select_related("category", "brand")
            .prefetch_related(
                "images",
                "variants__size",
                "recommended_products",
                "reviews",
            )
            .exclude(price=0)
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
    def get_cart(self, request):
        return request.session.get('cart', {})

    def save_cart(self, request, cart):
        request.session['cart'] = cart
        request.session.modified = True

    def build_cart_data(self, request):
        cart = self.get_cart(request)
        products = Product.objects.select_related('category', 'brand').filter(id__in=cart.keys())

        items = []
        subtotal = Decimal('0')
        discount_total = Decimal('0')

        for product in products:
            quantity = int(cart.get(str(product.id), 1))
            old_price = product.price * quantity
            unit_price = product.get_discounted_price()
            line_total = unit_price * quantity

            subtotal += old_price
            discount_total += old_price - line_total

            items.append({
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': line_total,
            })

        delivery = Decimal('0')
        total = subtotal - discount_total + delivery

        return {
            'items': items,
            'subtotal': subtotal,
            'discount_total': discount_total,
            'delivery': delivery,
            'total': total,
        }

    def cart_response(self, request, status_code=status.HTTP_200_OK):
        serializer = CartSerializer(self.build_cart_data(request), context={'request': request})
        return Response(serializer.data, status=status_code)


class CartView(CartMixin, APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return self.cart_response(request)

    def delete(self, request):
        self.save_cart(request, {})
        return self.cart_response(request)


class CartAddView(CartMixin, APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        cart = self.get_cart(request)
        product_id_str = str(product.id)
        cart[product_id_str] = int(cart.get(product_id_str, 0)) + 1
        self.save_cart(request, cart)
        return self.cart_response(request, status.HTTP_201_CREATED)


class CartUpdateView(CartMixin, APIView):
    permission_classes = (permissions.AllowAny,)

    def patch(self, request, product_id):
        cart = self.get_cart(request)
        product_id_str = str(product_id)

        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({'quantity': 'Количество должно быть целым числом.'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity > 0:
            cart[product_id_str] = quantity
        else:
            cart.pop(product_id_str, None)

        self.save_cart(request, cart)
        return self.cart_response(request)


class CartRemoveView(CartMixin, APIView):
    permission_classes = (permissions.AllowAny,)

    def delete(self, request, product_id):
        cart = self.get_cart(request)
        cart.pop(str(product_id), None)
        self.save_cart(request, cart)
        return self.cart_response(request)