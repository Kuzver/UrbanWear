from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Brand,
    Category,
    Order,
    OrderItem,
    Product,
    ProductImage,
    ProductVariant,
    PromoCode,
    Review,
    Size,
    Wishlist,
)


class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        read_only_fields = fields


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'products_count')


class BrandSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Brand
        fields = ('id', 'name', 'slug', 'logo', 'products_count')


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ('id', 'name')


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'product', 'image', 'sort_order')


class ProductVariantSerializer(serializers.ModelSerializer):
    size = SizeSerializer(read_only=True)
    size_id = serializers.PrimaryKeyRelatedField(
        queryset=Size.objects.all(),
        source='size',
        write_only=True,
        required=False,
    )

    def validate_stock(self, value):
        """
        Проверяет остаток товара по конкретному размеру.

        Остаток не может быть отрицательным.
        """
        if value < 0:
            raise serializers.ValidationError(
                "Остаток по размеру не может быть отрицательным."
            )
        return value

    class Meta:
        model = ProductVariant
        fields = ('id', 'product', 'size', 'size_id', 'stock')


class ProductListSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField()
    avg_rating = serializers.FloatField(read_only=True)
    sold_count = serializers.IntegerField(read_only=True)
    wishlist_count = serializers.IntegerField(read_only=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "category",
            "brand",
            "price",
            "discount",
            "discounted_price",
            "stock",
            "main_image",
            "created_at",
            "updated_at",
            "avg_rating",
            "sold_count",
            "wishlist_count",
            "is_favorite",
        ]

    def get_discounted_price(self, obj):
        return obj.get_discounted_price()

    def get_is_favorite(self, obj):
        """
        Проверяет, находится ли товар в избранном у текущего пользователя.
        """
        favorite_products = self.context.get("favorite_products", set())
        return obj.id in favorite_products


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField()
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
    )
    brand = BrandSerializer(read_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        source='brand',
        write_only=True,
        required=False,
        allow_null=True,
    )
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    recommended_products = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.all(),
        required=False,
    )
    discounted_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        source='get_discounted_price',
    )
    reviews_count = serializers.IntegerField(source='reviews.count', read_only=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'category',
            'category_id',
            'brand',
            'brand_id',
            'name',
            'recommended_products',
            'slug',
            'sku',
            'price',
            'discount',
            'discounted_price',
            'stock',
            'description',
            'instruction',
            'video_url',
            'documentation',
            'main_image',
            'images',
            'variants',
            'reviews_count',
            'created_at',
            'updated_at',
            "is_favorite",
        )
        read_only_fields = ('created_at', 'updated_at', 'slug')

    def validate(self, attrs):
        """
        Проверяет бизнес-правила для товара.

        Реализованные проверки:
        - цена товара не может быть нулевой или отрицательной;
        - скидка должна быть в диапазоне от 0 до 100 процентов;
        - общий остаток товара не может быть отрицательным;
        - артикул не может быть пустым.
        """
        price = attrs.get("price", getattr(self.instance, "price", None))
        discount = attrs.get("discount", getattr(self.instance, "discount", 0))
        stock = attrs.get("stock", getattr(self.instance, "stock", 0))
        sku = attrs.get("sku", getattr(self.instance, "sku", ""))

        errors = {}

        if price is not None and price <= 0:
            errors["price"] = "Цена товара должна быть больше 0."

        if discount is not None and (discount < 0 or discount > 100):
            errors["discount"] = "Скидка должна быть в диапазоне от 0 до 100 процентов."

        if stock is not None and stock < 0:
            errors["stock"] = "Остаток товара не может быть отрицательным."

        if sku is not None and not str(sku).strip():
            errors["sku"] = "Артикул товара не может быть пустым."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def get_is_favorite(self, obj):
        """
        Проверяет, находится ли товар в избранном у текущего пользователя.
        """
        favorite_products = self.context.get("favorite_products", set())
        return obj.id in favorite_products

    def validate_discount(self, value):
        if value > 100:
            raise serializers.ValidationError('Скидка не может быть больше 100 %.')
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Цена должна быть больше нуля.')
        return value


class ReviewSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'product', 'user', 'user_id', 'rating', 'comment', 'created_at')
        read_only_fields = ('user', 'user_id', 'created_at')

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Оценка должна быть от 1 до 5.')
        return value

    def validate_rating(self, value):
        """
        Проверяет оценку отзыва.

        Оценка должна быть от 1 до 5.
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Оценка должна быть в диапазоне от 1 до 5."
            )
        return value

    def validate(self, attrs):
        """
        Проверяет бизнес-правила добавления отзыва.

        Один пользователь не может оставить несколько отзывов
        на один и тот же товар.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        product = attrs.get("product")

        if self.instance is None and user and user.is_authenticated and product:
            review_exists = Review.objects.filter(
                user=user,
                product=product,
            ).exists()

            if review_exists:
                raise serializers.ValidationError(
                    "Вы уже оставляли отзыв на этот товар."
                )

        return attrs

class WishlistSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    product_detail = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = Wishlist
        fields = ('id', 'user', 'product', 'product_detail', 'created_at')
        read_only_fields = ('user', 'created_at')


class OrderItemSerializer(serializers.ModelSerializer):
    product_detail = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product', 'product_detail', 'quantity', 'price', 'confirmed_by')
        read_only_fields = ('order', 'confirmed_by')

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError('Количество должно быть не меньше 1.')
        return value

    def validate_quantity(self, value):
        """
        Проверяет количество товара в позиции заказа.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Количество товара должно быть больше 0."
            )
        return value

    def validate(self, attrs):
        """
        Проверяет наличие товара на складе.

        Нельзя заказать больше товара, чем есть в наличии.
        """
        product = attrs.get("product", getattr(self.instance, "product", None))
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))

        if product and quantity and quantity > product.stock:
            raise serializers.ValidationError(
                {
                    "quantity": (
                        f"Недостаточно товара на складе. "
                        f"Доступно: {product.stock}."
                    )
                }
            )

        return attrs


class OrderSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'status',
            'delivery_address',
            'city',
            'postal_code',
            'contact_phone',
            'total_amount',
            'items',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('user', 'total_amount', 'created_at', 'updated_at')

    def validate_total_amount(self, value):
        """
        Проверяет сумму заказа.

        Сумма заказа должна быть положительной и не должна превышать
        установленный лимит.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Сумма заказа должна быть больше 0."
            )

        if value > 100000:
            raise serializers.ValidationError(
                "Сумма заказа не может быть больше 100 000 рублей."
            )

        return value

    def validate_address(self, value):
        """
        Проверяет адрес доставки.

        Адрес должен содержать минимум 10 символов.
        Для учебного проекта этого достаточно, чтобы показать
        базовую валидацию формата адреса.
        """
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Адрес доставки должен содержать не менее 10 символов."
            )

        return value


class PromoCodeSerializer(serializers.ModelSerializer):
    active = serializers.BooleanField(source='is_valid', read_only=True)

    class Meta:
        model = PromoCode
        fields = (
            'id',
            'code',
            'discount_type',
            'discount_value',
            'start_date',
            'end_date',
            'max_uses',
            'used_count',
            'active',
        )
        read_only_fields = ('used_count', 'active')


class CartItemSerializer(serializers.Serializer):
    product = ProductListSerializer(read_only=True)
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    delivery = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
