from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_featured", "featured_order", "is_active")
    list_filter = ("is_featured", "is_active",)
    search_fields = ("name", "slug",)
    ordering = ("parent__id", "featured_order", "name")
    list_editable = ("is_featured", "featured_order")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
