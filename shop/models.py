from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, blank=True)  # blank=True разрешает пустое значение в формах
    instruction = models.FileField(
        upload_to='product_instructions/',
        blank=True,
        null=True,
        verbose_name='Инструкция (PDF)'
    )
    video_url = models.URLField(
        blank=True,
        verbose_name='Ссылка на видеообзор'
    )
    documentation = models.FileField(
        upload_to='product_docs/',
        blank=True,
        null=True,
        verbose_name='Документация'
    )
    video_url = models.URLField(
        blank=True,
        verbose_name='Ссылка на видео'
    )
    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        # Генерируем slug только если его нет
        if not self.slug:
            self.slug = slugify(self.name)
            # Простая проверка на уникальность, чтобы избежать дубликатов
            original_slug = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at', 'name']

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтверждён'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    products = models.ManyToManyField(
        Product,
        through='OrderItem',
        through_fields=('order', 'product'),
        # Явно указываем: 'order' в OrderItem -> наша модель, 'product' в OrderItem -> целевая модель
    )

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Добавляем ещё одну связь с пользователем, которая создаст неоднозначность
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_order_items'
    )

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

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

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'product')  # чтобы один товар можно было добавить в избранное только один раз


class Review(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username}"