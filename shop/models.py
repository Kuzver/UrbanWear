# shop/models.py
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='название')
    slug = models.SlugField(unique=True, verbose_name='slug')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name='название')
    slug = models.SlugField(unique=True, verbose_name='slug')
    logo = models.ImageField(upload_to='brands/', blank=True, verbose_name='логотип')

    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренды'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductManager(models.Manager):
    def cheap_products(self):
        return self.exclude(price__gt=5000)

    def sorted_by_price_desc(self):
        return self.order_by('-price')


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='категория')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products', blank=True, null=True, verbose_name='бренд')
    name = models.CharField(max_length=200, verbose_name='название')
    slug = models.SlugField(unique=True, blank=True, verbose_name='slug')  # убрал дубль
    sku = models.CharField(max_length=50, unique=True, verbose_name='артикул')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='цена')
    discount = models.PositiveIntegerField(default=0, help_text='Скидка в процентах', verbose_name='скидка')
    stock = models.PositiveIntegerField(default=0, verbose_name='общий остаток')
    description = models.TextField(blank=True, verbose_name='описание')
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
    main_image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name='Главное изображение'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='дата обновления')

    objects = ProductManager()

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at', 'name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def get_discounted_price(self):
        if self.discount:
            return self.price * (100 - self.discount) / 100
        return self.price


class Size(models.Model):
    name = models.CharField(max_length=10, unique=True, verbose_name='размер')

    class Meta:
        verbose_name = 'Размер'
        verbose_name_plural = 'Размеры'
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name='товар')
    size = models.ForeignKey(Size, on_delete=models.CASCADE, related_name='variants', verbose_name='размер')
    stock = models.PositiveIntegerField(default=0, verbose_name='остаток')

    class Meta:
        verbose_name = 'Вариация товара'
        verbose_name_plural = 'Вариации товаров'
        unique_together = ('product', 'size')

    def __str__(self):
        return f"{self.product.name} – {self.size.name}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтверждён'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='пользователь', null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='статус')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='дата обновления')
    delivery_address = models.TextField(verbose_name='адрес доставки', null=True)
    city = models.CharField(max_length=100, verbose_name='город', null=True)
    postal_code = models.CharField(max_length=20, verbose_name='индекс', null=True)
    contact_phone = models.CharField(max_length=20, verbose_name='телефон', null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='итоговая сумма', null=True)

    products = models.ManyToManyField(
        Product,
        through='OrderItem',
        through_fields=('order', 'product'),
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} – {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='заказ')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='товар')
    quantity = models.PositiveIntegerField(default=1, verbose_name='количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='цена на момент заказа')
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_order_items',
        verbose_name='подтвердил'
    )

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказов'

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='товар'
    )
    image = models.ImageField(upload_to='products/', verbose_name='изображение')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='порядок')

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['sort_order']

    def __str__(self):
        return f"Изображение для {self.product.name}"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist', verbose_name='пользователь')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by', verbose_name='товар')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='дата добавления')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные товары'
        unique_together = ('user', 'product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} – {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='товар')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='пользователь')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='оценка')
    comment = models.TextField(verbose_name='комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='дата создания')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} – {self.product.name} – {self.rating}"


class PromoCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Процент'),
        ('fixed', 'Фиксированная сумма'),
    ]
    code = models.CharField(max_length=50, unique=True, verbose_name='код')
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, verbose_name='тип скидки')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='значение')
    start_date = models.DateTimeField(default=timezone.now, verbose_name='дата начала')
    end_date = models.DateTimeField(blank=True, null=True, verbose_name='дата окончания')
    max_uses = models.PositiveIntegerField(default=1, verbose_name='макс. использований')
    used_count = models.PositiveIntegerField(default=0, verbose_name='использовано')

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['-start_date']

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return (self.start_date <= now and
                (self.end_date is None or self.end_date > now) and
                self.used_count < self.max_uses)