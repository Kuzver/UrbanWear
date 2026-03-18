from django import template
from django.utils import timezone
from ..models import Product  # или from ..models import Product

register = template.Library()

@register.simple_tag
def current_time(format_string='%d.%m.%Y %H:%M'):
    return timezone.now().strftime(format_string)

@register.simple_tag(takes_context=True)
def cart_total_items(context):
    # Заглушка – позже замените на реальную логику корзины
    return 0

@register.simple_tag
def popular_products(limit=5):
    # Пока возвращаем пустой QuerySet, чтобы избежать других ошибок
    return Product.objects.none()