
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.cache import cache_page

from .models import Product, Order, ProductImage
from django.shortcuts import get_object_or_404, render
from django.shortcuts import render
from .models import Product
from .forms import ProductImageUploadForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from .forms import ProductForm, ReviewForm
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from .forms import ProductImageUploadForm
from .models import ProductImage
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Avg, Max, Min

def home(request):
    latest_products = Product.objects.order_by('-created_at')[:5]
    # Количество товаров в категории "Hoodies"
    hoodies_count = Product.objects.filter(category__name='Hoodies').count()
    # Есть ли дорогие товары (>10000)
    expensive_exists = Product.objects.filter(price__gt=10000).exists()

    stats = Product.objects.aggregate(
        avg_price=Avg('price'),
        max_price=Max('price'),
        min_price=Min('price')
    )

    return render(request, 'shop/home.html', {
        'latest_products': latest_products,
        'hoodies_count': hoodies_count,
        'expensive_exists': expensive_exists,
    })

@cache_page(60 * 15)  # 15 минут
def product_list(request):
    products = Product.objects.all().exclude(price=0)

    paginator = Paginator(products, 6)  # 6 товаров на страницу
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    return render(request, 'shop/product_list.html', {
        'products': products
    })

def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related('images', 'variants', 'reviews'),
        slug=slug
    )
    avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'avg_rating': avg_rating
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('product_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@staff_member_required
def product_create(request):
    """Создание нового товара"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)  # Создаём объект, но не сохраняем в БД
            # Модифицируем объект перед сохранением
            product.name = f"(NEW) {product.name}"
            product.save()  # Теперь сохраняем
            messages.success(request, f'Товар "{product.name}" успешно создан.')
            return HttpResponseRedirect(product.get_absolute_url())
    else:
        form = ProductForm()
    return render(request, 'shop/product_form.html', {'form': form, 'title': 'Создание товара'})

@staff_member_required
def product_update(request, slug):
    product = get_object_or_404(Product, slug=slug)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=True)
            messages.success(request, f'Товар "{product.name}" успешно обновлён.')
            return redirect('product_detail', slug=product.slug)
    else:
        form = ProductForm(instance=product)

    return render(request, 'shop/product_form.html', {
        'form': form,
        'title': 'Редактирование товара',
        'product': product
    })

@staff_member_required
def product_delete(request, slug):
    """Удаление товара"""
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Товар удалён.')
        return redirect('product_list')
    return redirect('product_list')

def order_detail(request, order_id):
    # Оптимизация: загружаем связанного пользователя (ForeignKey) через JOIN
    # и все позиции заказа, а для каждой позиции — связанный товар (отдельным запросом)
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related('items__product'),
        id=order_id
    )
    return render(request, 'shop/order_detail.html', {'order': order})

def product_search(request):
    query = request.GET.get('q')
    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(name__contains=query)
        )

    return render(request, 'shop/product_list.html', {'products': products})

@login_required
def add_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data.get('text')
            rating = form.cleaned_data.get('rating')

            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.text = text
            review.rating = rating
            review.save()

            messages.success(request, 'Спасибо за ваш отзыв!')
            return redirect('product_detail', slug=product.slug)
    else:
        form = ReviewForm()
    return render(request, 'shop/add_review.html', {'form': form, 'product': product})

@staff_member_required
def add_product_images(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    if request.method == 'POST':
        # request.FILES содержит загруженные файлы
        for image_file in request.FILES.getlist('images'):
            ProductImage.objects.create(product=product, image=image_file)
        messages.success(request, 'Изображения добавлены')
        return redirect('product_detail', slug=product.slug)
    return render(request, 'shop/add_images.html', {'product': product})

def product_names(request):
    # values_list с flat=True даст список названий
    names = Product.objects.values_list('name', flat=True)
    # или values – список словарей
    data = Product.objects.values('name', 'price')
    # Для примера передадим оба в шаблон
    return render(request, 'shop/product_names.html', {'names': names, 'data': data})

@staff_member_required
def increase_prices(request):
    if request.method == 'POST':
        # Повышаем цену всех товаров на 10%
        updated = Product.objects.update(price=F('price') * 1.1)
        messages.success(request, f'Цены обновлены у {updated} товаров.')
        return redirect('product_list')
    return render(request, 'shop/increase_prices_confirm.html')

def product_detail(request, slug):
    try:
        product = Product.objects.get(slug=slug)
    except Product.DoesNotExist:
        raise Http404("Товар не найден")
    return render(request, 'shop/product_detail.html', {'product': product})

@staff_member_required
def upload_product_images(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        form = ProductImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            for image_file in request.FILES.getlist('images'):
                ProductImage.objects.create(product=product, image=image_file)
            messages.success(request, 'Изображения загружены')
            return redirect('product_detail', slug=product.slug)
    else:
        form = ProductImageUploadForm()
    return render(request, 'shop/upload_images.html', {'form': form, 'product': product})

def get_cached_data():
    data = cache.get('my_key')
    if not data:
        data = increase_prices()
        cache.set('my_key', data, 60*5)
    return data

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect('cart_detail')

def cart_detail(request):
    cart = request.session.get('cart', {})
    products = Product.objects.filter(id__in=cart.keys())
    items = []
    for product in products:
        items.append({
            'product': product,
            'quantity': cart[str(product.id)],
        })
    return render(request, 'shop/cart.html', {'items': items})