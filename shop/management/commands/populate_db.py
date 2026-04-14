from decimal import Decimal
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from shop.models import (
    Brand,
    Category,
    Order,
    OrderItem,
    Product,
    ProductVariant,
    PromoCode,
    Review,
    Size,
    Wishlist,
)

fake = Faker("ru_RU")


class Command(BaseCommand):
    help = "Заполняет базу данных тестовыми данными для UrbanWear"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Начинаю заполнение базы..."))

        categories = self.create_categories()
        brands = self.create_brands()
        sizes = self.create_sizes()
        users = self.create_users(10)
        products = self.create_products(30, categories, brands)

        self.create_variants(products, sizes)
        self.create_reviews(products, users, 50)
        self.create_wishlist(products, users, 20)
        self.create_promocodes(5)
        self.create_orders(users, products, 12)

        self.stdout.write(self.style.SUCCESS("База успешно заполнена."))

    def make_unique_slug(self, model, name: str) -> str:
        base_slug = slugify(name) or fake.unique.slug()
        slug = base_slug
        counter = 1

        while model.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def create_categories(self):
        names = [
            "Худи",
            "Футболки",
            "Обувь",
            "Джинсы",
            "Куртки",
            "Свитшоты",
            "Брюки",
            "Аксессуары",
        ]

        result = []
        for name in names:
            category, _ = Category.objects.get_or_create(
                name=name,
                defaults={"slug": self.make_unique_slug(Category, name)},
            )
            result.append(category)
        return result

    def create_brands(self):
        names = [
            "Urban Core",
            "Street Motion",
            "North Black",
            "Mono Layer",
            "Peak Wear",
            "Daily Form",
        ]

        result = []
        for name in names:
            brand, _ = Brand.objects.get_or_create(
                name=name,
                defaults={"slug": self.make_unique_slug(Brand, name)},
            )
            result.append(brand)
        return result

    def create_sizes(self):
        result = []
        for name in ["XS", "S", "M", "L", "XL"]:
            size, _ = Size.objects.get_or_create(name=name)
            result.append(size)
        return result

    def create_users(self, count: int):
        result = []

        for _ in range(count):
            username = fake.unique.user_name()
            email = fake.unique.email()

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                },
            )

            if created:
                user.set_password("testpass123")
                user.save()

            result.append(user)

        return result

    def create_products(self, count: int, categories, brands):
        result = []

        for _ in range(count):
            category = random.choice(categories)
            brand = random.choice(brands)

            name = f"{category.name} {fake.word().capitalize()} {random.randint(100, 999)}"

            product = Product.objects.create(
                category=category,
                brand=brand,
                name=name,
                sku=fake.unique.bothify(text="UW-#####"),
                price=Decimal(random.randint(1500, 15000)),
                discount=random.choice([0, 0, 5, 10, 15, 20]),
                stock=random.randint(1, 50),
                description=fake.text(max_nb_chars=250),
                video_url=fake.url(),
            )

            result.append(product)

        for product in result:
            recommendations = random.sample(result, k=min(3, len(result)))
            product.recommended_products.set(
                [p for p in recommendations if p.id != product.id]
            )

        return result

    def create_variants(self, products, sizes):
        for product in products:
            selected_sizes = random.sample(
                sizes,
                k=random.randint(2, min(5, len(sizes))),
            )

            for size in selected_sizes:
                ProductVariant.objects.get_or_create(
                    product=product,
                    size=size,
                    defaults={"stock": random.randint(1, 20)},
                )

    def create_reviews(self, products, users, count: int):
        for _ in range(count):
            Review.objects.create(
                product=random.choice(products),
                user=random.choice(users),
                rating=random.randint(1, 5),
                comment=fake.sentence(nb_words=12),
            )

    def create_wishlist(self, products, users, count: int):
        used_pairs = set()

        for _ in range(count):
            user = random.choice(users)
            product = random.choice(products)
            pair = (user.id, product.id)

            if pair in used_pairs:
                continue

            Wishlist.objects.get_or_create(user=user, product=product)
            used_pairs.add(pair)

    def create_promocodes(self, count: int):
        for _ in range(count):
            PromoCode.objects.get_or_create(
                code=fake.unique.bothify(text="SALE-####"),
                defaults={
                    "discount_type": random.choice(["percentage", "fixed"]),
                    "discount_value": Decimal(random.randint(5, 30)),
                    "start_date": timezone.now(),
                    "max_uses": random.randint(5, 30),
                    "used_count": random.randint(0, 3),
                },
            )

    def create_orders(self, users, products, count: int):
        for _ in range(count):
            user = random.choice(users)

            order = Order.objects.create(
                user=user,
                status=random.choice(["new", "confirmed", "shipped", "delivered"]),
                delivery_address=fake.street_address(),
                city=fake.city(),
                postal_code=fake.postcode(),
                contact_phone=fake.phone_number()[:20],
                total_amount=Decimal("0.00"),
            )

            selected_products = random.sample(products, k=random.randint(1, 4))
            total = Decimal("0.00")

            for product in selected_products:
                quantity = random.randint(1, 3)
                price = product.price

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price,
                    confirmed_by=user,
                )

                total += Decimal(quantity) * price

            order.total_amount = total
            order.save(update_fields=["total_amount"])