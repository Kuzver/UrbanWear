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
        fields = [
            'category',
            'brand',
            'name',
            'slug',
            'sku',
            'price',
            'discount',
            'stock',
            'description',
            'main_image',
            'instruction',
            'video_url',
            'documentation',
            'recommended_products',
        ]

        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

        labels = {
            'name': 'Название товара',
            'price': 'Цена, руб.',
            'main_image': 'Главное изображение товара',
        }

        help_texts = {
            'slug': 'Если не заполнить, slug сгенерируется автоматически.',
            'main_image': 'Это фото будет показано в каталоге, корзине и карточке товара.',
        }


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            'widget',
            MultipleFileInput(attrs={
                'multiple': True,
                'accept': 'image/*',
            })
        )
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            return []

        files = data if isinstance(data, (list, tuple)) else [data]

        return [
            super(MultipleFileField, self).clean(file, initial)
            for file in files
        ]


class ProductImageUploadForm(forms.Form):
    images = MultipleFileField(
        label='Выберите изображения',
        required=False,
        help_text='Можно выбрать несколько фото сразу.',
    )