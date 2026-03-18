from django import template
from django.utils import timezone

register = template.Library()

@register.simple_tag
def current_time(format_string='%d.%m.%Y %H:%M'):
    return timezone.now().strftime(format_string)

@register.simple_tag(takes_context=True)
def cart_total_items(context):
    cart = context.get('cart')
    # Здесь должна быть логика получения количества товаров в корзине.
    # Для примера вернём 0, пока корзина не реализована.
    return cart.total_items if cart else 0

from ..models import Product
from django.db.models import Count

@register.simple_tag
def popular_products(limit=5):
    return Product.objects.annotate(
        order_count=Count('reviews')  # для примера используем количество отзывов
    ).order_by('-order_count')[:limit]