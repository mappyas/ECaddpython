from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_in_stock', 'created_at')
    list_filter = ('created_at', 'stock')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
