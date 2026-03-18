from django.db.models import Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Product
from django.shortcuts import get_object_or_404, render
def product_list(request):
    product_list = Product.objects.all()
    paginator = Paginator(product_list, 10)  # 10 товаров на странице
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    return render(request, 'shop/product_list.html', {'page_obj': products})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'avg_rating': avg_rating
    })

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

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