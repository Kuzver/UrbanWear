# shop/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from . import models
from .models import (
    Category, Brand, Product, ProductImage, Size, ProductVariant,
    Order, OrderItem, Wishlist, Review, PromoCode
)


# ---------- Category ----------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_display_links = ['name']


# ---------- Brand ----------
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'logo_preview']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['logo_preview']
    list_display_links = ['name']

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" />', obj.logo.url)
        return '-'
    logo_preview.short_description = 'Логотип'


# ---------- Product ----------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'sort_order')
    verbose_name = 'Изображение'
    verbose_name_plural = 'Изображения'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('size', 'stock')
    verbose_name = 'Размер'
    verbose_name_plural = 'Размеры'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'price', 'discounted_price', 'stock', 'category', 'brand', 'created_at']
    list_filter = ['category', 'brand', 'created_at']
    search_fields = ['name', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    list_display_links = ['name']
    list_editable = ['price', 'stock']
    readonly_fields = ['created_at', 'updated_at', 'discounted_price']
    date_hierarchy = 'created_at'
    raw_id_fields = ['category', 'brand']
    filter_horizontal = ['recommended_products']
    inlines = [ProductImageInline, ProductVariantInline]
    fieldsets = (
        ('Основное', {
            'fields': ('category', 'brand', 'name', 'slug', 'sku', 'description', 'instruction', 'documentation', 'video_url', 'main_image')
        }),
        ('Цены и наличие', {
            'fields': ('price', 'discount', 'discounted_price', 'stock')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Цена со скидкой')
    def discounted_price(self, obj):
        if obj.discount:
            return f"{obj.get_discounted_price():.2f} руб."
        return '-'


# ---------- Order ----------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'price')
    readonly_fields = ('price',)
    can_delete = False
    verbose_name = 'Товар'
    verbose_name_plural = 'Товары'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'total_amount']
    date_hierarchy = 'created_at'
    list_display_links = ['id']
    raw_id_fields = ['user']
    inlines = [OrderItemInline]
    fieldsets = (
        ('Информация о заказе', {
            'fields': ('user', 'status', 'total_amount', 'created_at', 'updated_at')
        }),
        ('Данные доставки', {
            'fields': ('delivery_address', 'city', 'postal_code', 'contact_phone')
        }),
    )
    actions = ['mark_as_shipped', 'mark_as_delivered']

    @admin.action(description='Отметить как отправленные')
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')

    @admin.action(description='Отметить как доставленные')
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')


# ---------- Size ----------
@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


# ---------- Wishlist ----------
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    raw_id_fields = ['user', 'product']
    readonly_fields = ['created_at']


# ---------- Review ----------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'user__username', 'comment']
    readonly_fields = ['created_at']
    raw_id_fields = ['product', 'user']


# ---------- PromoCode ----------
@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'start_date', 'end_date', 'max_uses', 'used_count']
    list_filter = ['discount_type', 'start_date', 'end_date']
    search_fields = ['code']
    readonly_fields = ['used_count']
    fieldsets = (
        ('Код', {'fields': ('code',)}),
        ('Скидка', {'fields': ('discount_type', 'discount_value')}),
        ('Срок действия', {'fields': ('start_date', 'end_date')}),
        ('Ограничения', {'fields': ('max_uses', 'used_count')}),
    )