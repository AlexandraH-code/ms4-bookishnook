from django.contrib import admin
from .models import NewsletterSubscriber


# Register your models here.
@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "confirmed", "unsubscribed", "created_at", "confirmed_at")
    list_filter = ("confirmed", "unsubscribed", "created_at")
    search_fields = ("email",)
    ordering = ("-created_at",)
    readonly_fields = ("confirm_token", "unsubscribe_token", "created_at", "confirm_sent_at", "confirmed_at")

    fieldsets = (
        (None, {
            "fields": ("email", "confirmed", "unsubscribed")
        }),
        ("Tokens", {
            "fields": ("confirm_token", "unsubscribe_token"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "confirm_sent_at", "confirmed_at"),
            "classes": ("collapse",),
        }),
    )
