from django.contrib import admin
from .models import Order, OrderItem


# Register your models here.
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "email", "grand_total", "created")
    list_filter = ("status", "created")
    inlines = [OrderItemInline]
