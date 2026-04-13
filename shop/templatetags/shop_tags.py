from django import template
from django.utils import timezone
from ..models import Product  # или from ..models import Product

register = template.Library()

@register.simple_tag
def current_time(format_string='%d.%m.%Y %H:%M'):
    return timezone.now().strftime(format_string)

@register.simple_tag(takes_context=True)
def cart_total_items(context):
    request = context.get('request')
    if not request:
        return 0

    cart = request.session.get('cart', {})
    if isinstance(cart, dict):
        return sum(item.get('quantity', 0) for item in cart.values())

    return 0

@register.simple_tag
def popular_products(limit=5):
    return Product.objects.order_by('-created_at')[:limit]

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return ''


@register.filter
def ru_yesno(value):
    return 'Да' if value else 'Нет'