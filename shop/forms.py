from django import forms
from .models import Product, ProductImage
from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Ваш отзыв..----.'}),
        }
        labels = {
            'rating': 'Оценка',
            'comment': 'Комментарий',
        }
        help_texts = {
            'rating': 'Поставьте оценку от 1 до 5 ----',
        }
        error_messages = {
            'rating': {
                'required': 'Пожалуйста, поставьте оценку',
                'min_value': 'Оценка не может быть меньше 1',
                'max_value': 'Оценка не может быть больше 5',
            },
        }
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'slug', 'sku', 'price', 'stock', 'description']
        exclude = []  # можно исключить поля, но мы уже перечислили все
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'name': 'Название товара',
            'price': 'Цена (р ------уб)',
        }
        help_texts = {
            'slug': 'Уникальный идентификатор ----------- для URL. Если не заполнить, сгенерируется автоматически.',
        }
        error_messages = {
            'price': {
                'min_value': 'Цена не может быть отрицательной',
            },
            'sku': {
                'unique': 'Товар с таким артикулом уже существует',
            },
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']

class ProductImageUploadForm(forms.Form):
    images = forms.FileField(
        label='Выберите изображение',
        required=False
    )