from decimal import Decimal

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
from django.http import Http404, HttpResponseRedirect, HttpResponse
from .forms import ProductImageUploadForm
from .models import ProductImage
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Avg, Max, Min, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProductForm, ProductImageUploadForm, ReviewForm
from .models import Brand, Category, Order, Product, ProductImage

def export_order_pdf_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="order_{order.id}.pdf"'
    response.write(f'PDF для заказа {order.id}')
    return response

def home(request):
    products = Product.objects.select_related('category', 'brand').exclude(price=0).order_by('-created_at')

    hero_product = products.filter(main_image__isnull=False).exclude(main_image='').first()
    products_with_images = products.filter(main_image__isnull=False).exclude(main_image='')[:12]

    return render(request, 'shop/home.html', {
        'products': products_with_images,
        'hero_product': hero_product,
    })

def export_order_pdf_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="order_{order.id}.pdf"'

    response.write(f"PDF для заказа {order.id}")
    return response


def _gender_filter(products, value):
    women_words = ['жен', 'woman', 'women', 'female', 'девуш', 'дам']
    men_words = ['муж', 'man', 'men', 'male', 'парн']

    words = women_words if value == 'women' else men_words
    query = Q()

    for word in words:
        query |= Q(category__name__icontains=word)
        query |= Q(category__slug__icontains=word)
        query |= Q(name__icontains=word)
        query |= Q(description__icontains=word)

    return products.filter(query)

def product_list(request):
    products = Product.objects.select_related('category', 'brand').prefetch_related('variants__size').exclude(price=0)

    category = request.GET.get('category', '').strip()
    q = request.GET.get('q', '').strip()
    brand = request.GET.get('brand', '').strip()
    size = request.GET.get('size', '').strip()
    color = request.GET.get('color', '').strip()
    discount = request.GET.get('discount', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    sort = request.GET.get('sort', 'popular').strip()

    if category in {'women', 'men'}:
        products = _gender_filter(products, category)
    elif category == 'looks':
        products = products.filter(Q(category__name__icontains='образ') | Q(name__icontains='образ'))
    elif category == 'shoes':
        products = products.filter(Q(category__name__icontains='обув') | Q(name__icontains='обув') | Q(name__icontains='shoe'))
    elif category == 'accessories':
        products = products.filter(Q(category__name__icontains='аксесс') | Q(name__icontains='аксесс') | Q(name__icontains='шап') | Q(name__icontains='кеп'))
    elif category:
        products = products.filter(Q(category__slug=category) | Q(category__name__icontains=category))

    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(sku__icontains=q))

    if brand:
        products = products.filter(Q(brand__slug=brand) | Q(brand__name__icontains=brand))

    if size:
        products = products.filter(variants__size__name__iexact=size, variants__stock__gt=0)

    # В модели нет отдельного поля color, поэтому фильтр ищет цвет по названию/описанию.
    if color:
        color_words = {
            'white': ['бел', 'white'],
            'beige': ['беж', 'beige'],
            'black': ['черн', 'black'],
            'orange': ['оранж', 'orange', 'персик'],
        }

        color_query = Q()
        for word in color_words.get(color, [color]):
            color_query |= Q(name__icontains=word)
            color_query |= Q(description__icontains=word)
            color_query |= Q(category__name__icontains=word)

        products = products.filter(color_query)

    if discount:
        products = products.filter(discount__gt=0)

    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price.replace(',', '.')))
        except Exception:
            messages.warning(request, 'Минимальная цена указана неверно.')

    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price.replace(',', '.')))
        except Exception:
            messages.warning(request, 'Максимальная цена указана неверно.')

    if sort == 'price_asc':
        products = products.order_by('price', 'name')
    elif sort == 'price_desc':
        products = products.order_by('-price', 'name')
    elif sort == 'new':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-created_at', 'name')

    products = products.distinct()

    paginator = Paginator(products, 9)
    page = request.GET.get('page')

    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    query_params = request.GET.copy()
    query_params.pop('page', None)

    category_labels = {
        'women': 'ЖЕНЩИНАМ',
        'men': 'МУЖЧИНАМ',
        'looks': 'ОБРАЗЫ',
        'shoes': 'ОБУВЬ',
        'accessories': 'АКСЕССУАРЫ',
    }

    return render(request, 'shop/product_list.html', {
        'products': products_page,
        'brands': Brand.objects.all(),
        'current_category': category,
        'current_category_label': category_labels.get(category, 'КАТАЛОГ'),
        'current_brand': brand,
        'current_size': size,
        'current_color': color,
        'current_sort': sort,
        'query_params': query_params.urlencode(),
    })
def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно.')
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    profile_products = (
        Product.objects
        .filter(main_image__isnull=False)
        .exclude(main_image='')
        .order_by('-created_at')[:3]
    )

    return render(request, 'shop/profile.html', {
        'profile_products': profile_products,
    })

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
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related('images', 'variants', 'reviews'),
        slug=slug
    )

    viewed_products = request.session.get('viewed_products', [])
    if product.id not in viewed_products:
        viewed_products.append(product.id)
        request.session['viewed_products'] = viewed_products
        request.session.modified = True

    request.session['last_viewed_product'] = product.name

    return render(request, 'shop/product_detail.html', {
        'product': product,
    })

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

def cart(request):
    cart = request.session.get('cart', {})
    products = Product.objects.filter(id__in=cart.keys())
    items = []
    subtotal = 0

    for product in products:
        quantity = cart[str(product.id)]
        line_total = product.get_discounted_price() * quantity
        subtotal += line_total

        items.append({
            'product': product,
            'quantity': quantity,
            'line_total': line_total,
        })

    delivery = 0
    total = subtotal + delivery

    return render(request, 'shop/cart.html', {
        'items': items,
        'subtotal': subtotal,
        'delivery': delivery,
        'total': total,
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})
    product_id_str = str(product.id)

    if product_id_str in cart:
        cart[product_id_str] += 1
    else:
        cart[product_id_str] = 1

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        del cart[product_id_str]

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


def update_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)

    quantity = int(request.POST.get('quantity', 1))

    if quantity > 0:
        cart[product_id_str] = quantity
    else:
        cart.pop(product_id_str, None)

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})
    product_id_str = str(product.id)

    cart[product_id_str] = int(cart.get(product_id_str, 0)) + 1

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


def cart_remove(request, product_id):
    cart = request.session.get('cart', {})

    cart.pop(str(product_id), None)

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


def cart_update(request, product_id):
    cart = request.session.get('cart', {})

    quantity = request.POST.get('quantity', '1')

    try:
        quantity = int(quantity)
    except ValueError:
        quantity = 1

    product_id_str = str(product_id)

    if quantity > 0:
        cart[product_id_str] = quantity
    else:
        cart.pop(product_id_str, None)

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


def cart_detail(request):
    cart = request.session.get('cart', {})

    products = Product.objects.filter(id__in=cart.keys()).select_related('category', 'brand')

    items = []
    subtotal = Decimal('0')
    discount_total = Decimal('0')

    for product in products:
        quantity = int(cart.get(str(product.id), 1))

        old_price = product.price * quantity
        unit_price = product.get_discounted_price()
        line_total = unit_price * quantity

        subtotal += old_price
        discount_total += old_price - line_total

        items.append({
            'product': product,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total,
        })

    delivery = Decimal('0')
    total = subtotal - discount_total + delivery

    return render(request, 'shop/cart.html', {
        'items': items,
        'subtotal': subtotal,
        'discount_total': discount_total,
        'delivery': delivery,
        'total': total,
    })