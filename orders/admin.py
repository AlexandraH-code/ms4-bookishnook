from django.contrib import admin
from .models import Order, OrderItem


# Register your models here.
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "email", "full_name", "grand_total", "created")
    list_filter = ("status", "created")
    readonly_fields = ("created", "updated", "stripe_session_id")
    fieldsets = (
        ("Status & totals", {"fields": ("status", "total", "tax_amount", "shipping", "grand_total")}),
        ("Stripe", {"fields": ("stripe_session_id",)}),
        ("Customer", {"fields": ("full_name", "email", "phone")}),
        ("Shipping address", {"fields": ("address_line1","address_line2","postal_code","city","country")}),
        ("Meta", {"fields": ("created","updated")}),
    )
    inlines = [OrderItemInline]
