from django.core.management.base import BaseCommand
from faker import Faker
import random
from shop.models import Product, Category, Brand
from django.utils.text import slugify

fake = Faker('ru_RU')


class Command(BaseCommand):
    help = 'Заполняет базу тестовыми данными'

    def handle(self, *args, **kwargs):
        self.create_categories()
        self.create_brands()
        self.create_products(20)

    def create_categories(self):
        categories = ['Худи', 'Футболки', 'Обувь', 'Джинсы']

        for name in categories:
            Category.objects.get_or_create(
                name=name,
                slug=fake.unique.slug()
            )

    def create_brands(self):
        for _ in range(5):
            name = fake.company()
            base_slug = slugify(name)
            slug = base_slug
            counter = 1

            while Brand.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            Brand.objects.create(
                name=name,
                slug=slug
            )

    def create_products(self, count):
        categories = Category.objects.all()
        brands = Brand.objects.all()

        for _ in range(count):
            Product.objects.create(
                name=fake.word(),
                sku=fake.unique.ean(length=8),
                price=random.randint(1000, 10000),
                category=random.choice(categories),
                brand=random.choice(brands),
                description=fake.text()
            )