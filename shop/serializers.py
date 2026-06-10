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

    class Meta:
        model = ProductVariant
        fields = ('id', 'product', 'size', 'size_id', 'stock')


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    avg_rating = serializers.FloatField(read_only=True)
    sold_count = serializers.IntegerField(read_only=True)
    wishlist_count = serializers.IntegerField(read_only=True)
    discounted_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        source='get_discounted_price',
    )

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'slug',
            'sku',
            'category',
            'brand',
            'price',
            'discount',
            'discounted_price',
            'stock',
            'main_image',
            'created_at',
            'updated_at',
            "avg_rating",
            "sold_count",
            "wishlist_count",
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
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
        )
        read_only_fields = ('created_at', 'updated_at', 'slug')

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
