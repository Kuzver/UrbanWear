from django.contrib import admin
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from .models import Product

def generate_pdf_catalog(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="catalog.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(20 * mm, height - 20 * mm, "Каталог товаров")

    y = height - 40 * mm
    p.setFont("Helvetica", 12)
    for product in queryset:
        p.drawString(20 * mm, y, f"{product.name} - {product.price} руб.")
        y -= 10 * mm
        if y < 20 * mm:
            p.showPage()
            y = height - 20 * mm
            p.setFont("Helvetica", 12)

    p.save()
    return response

generate_pdf_catalog.short_description = "Создать PDF-каталог"

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price')
    actions = [generate_pdf_catalog]

# Если Product уже зарегистрирован в админке, сначала удалите старую регистрацию:
# admin.site.unregister(Product)
admin.site.register(Product, ProductAdmin)