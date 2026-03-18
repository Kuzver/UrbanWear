from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"

    class Meta:
        ordering = ['-created_at', 'name']

from django.utils import timezone

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтверждён'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'   # позволяет обращаться product.images.all()
    )
    image = models.ImageField(upload_to='products/')


class ProductManager(models.Manager):
    def cheap_products(self):
        return self.exclude(price__gt=5000)

    def sorted_by_price_desc(self):
        return self.order_by('-price')
