"""
Фильтры API для приложения shop.

Файл используется Django Filter для фильтрации товаров через REST API.
Например:
    /api/products/?category=hoodie
    /api/products/?brand=nike
    /api/products/?size=M
    /api/products/?min_price=1000&max_price=5000
    /api/products/?discount=1
    /api/products/?in_stock=1
"""

from __future__ import annotations

import django_filters
from django.db.models import QuerySet, Q

from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Фильтрация товаров UrbanWear для REST API.

    Поддерживает фильтрацию по:
    - строке поиска;
    - категории;
    - бренду;
    - размеру;
    - минимальной и максимальной цене;
    - наличию скидки;
    - наличию товара на складе.
    """

    q = django_filters.CharFilter(method="filter_search", label="Поиск")
    category = django_filters.CharFilter(
        field_name="category__slug",
        lookup_expr="iexact",
        label="Категория",
    )
    brand = django_filters.CharFilter(
        field_name="brand__slug",
        lookup_expr="iexact",
        label="Бренд",
    )
    size = django_filters.CharFilter(method="filter_size", label="Размер")
    min_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
        label="Минимальная цена",
    )
    max_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
        label="Максимальная цена",
    )
    discount = django_filters.BooleanFilter(
        method="filter_discount",
        label="Товары со скидкой",
    )
    in_stock = django_filters.BooleanFilter(
        method="filter_in_stock",
        label="Товары в наличии",
    )

    class Meta:
        model = Product
        fields = [
            "q",
            "category",
            "brand",
            "size",
            "min_price",
            "max_price",
            "discount",
            "in_stock",
        ]

    def filter_search(
        self,
        queryset: QuerySet[Product],
        name: str,
        value: str,
    ) -> QuerySet[Product]:
        """
        Поиск товара по названию, описанию и артикулу.

        Args:
            queryset: Исходный набор товаров.
            name: Название фильтра.
            value: Строка поиска.

        Returns:
            Отфильтрованный QuerySet товаров.
        """
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(sku__icontains=value)
        )

    def filter_size(
        self,
        queryset: QuerySet[Product],
        name: str,
        value: str,
    ) -> QuerySet[Product]:
        """
        Фильтрация товаров по размеру через модель ProductVariant.

        Args:
            queryset: Исходный набор товаров.
            name: Название фильтра.
            value: Размер товара, например S, M, L, XL.

        Returns:
            QuerySet товаров, у которых есть указанный размер.
        """
        if not value:
            return queryset

        return queryset.filter(
            variants__size__name__iexact=value,
            variants__stock__gt=0,
        ).distinct()

    def filter_discount(
        self,
        queryset: QuerySet[Product],
        name: str,
        value: bool,
    ) -> QuerySet[Product]:
        """
        Фильтрация товаров по наличию скидки.

        Args:
            queryset: Исходный набор товаров.
            name: Название фильтра.
            value: True — только товары со скидкой.

        Returns:
            Отфильтрованный QuerySet.
        """
        if value:
            return queryset.filter(discount__gt=0)

        return queryset

    def filter_in_stock(
        self,
        queryset: QuerySet[Product],
        name: str,
        value: bool,
    ) -> QuerySet[Product]:
        """
        Фильтрация товаров по наличию на складе.

        Args:
            queryset: Исходный набор товаров.
            name: Название фильтра.
            value: True — только товары с положительным остатком.

        Returns:
            Отфильтрованный QuerySet.
        """
        if value:
            return queryset.filter(stock__gt=0)

        return queryset