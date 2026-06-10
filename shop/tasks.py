"""
Фоновые задачи приложения shop.

Здесь реализованы Celery-задачи для интернет-магазина UrbanWear.
"""

from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from .models import Product


@shared_task
def send_weekly_stock_report() -> str:
    """
    Отправляет еженедельный отчёт по товарам с низким остатком.

    В учебном проекте задача демонстрирует:
    - использование Celery;
    - работу с периодическими задачами;
    - отправку писем через SMTP;
    - возможность проверки писем через MailHog.
    """
    low_stock_products = (
        Product.objects
        .select_related("category", "brand")
        .filter(stock__lte=5)
        .order_by("stock", "name")
    )

    if not low_stock_products.exists():
        message = "Товаров с низким остатком нет."
    else:
        rows = []

        for product in low_stock_products:
            rows.append(
                (
                    f"{product.name} | "
                    f"SKU: {product.sku} | "
                    f"Категория: {product.category.name if product.category else '—'} | "
                    f"Бренд: {product.brand.name if product.brand else '—'} | "
                    f"Остаток: {product.stock}"
                )
            )

        message = "Товары с низким остатком:\n\n" + "\n".join(rows)

    send_mail(
        subject="UrbanWear: еженедельный отчёт по остаткам",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["admin@urbanwear.local"],
        fail_silently=False,
    )

    return message