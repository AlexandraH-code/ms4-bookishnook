from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "name", "unit_price", "qty", "subtotal")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "status", "grand_total", "created", "confirmation_sent_at")
    list_filter = ("status", "created")
    search_fields = ("id", "email", "full_name")

    fieldsets = (
        ("Order", {
            "fields": ("status", "stripe_session_id", "created", "updated")
        }),
        ("Customer", {
            "fields": ("email", "full_name", "phone"),
        }),
        ("Shipping address", {
            "fields": (
                "address_line1", "address_line2", "postal_code", "city", "country",
            ),
        }),
        ("Billing address", {
            "fields": (
                "billing_name", "billing_line1", "billing_line2",
                "billing_postal", "billing_city", "billing_country",
            ),
        }),
        ("Totals", {
            "fields": ("total", "tax_amount", "shipping", "grand_total"),
        }),
    )
    readonly_fields = ("created", "updated")

    inlines = [OrderItemInline]

