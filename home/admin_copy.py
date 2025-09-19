import csv
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import admin, messages
from .models import NewsletterSubscriber
from .utils import send_newsletter_confirmation


# Register your models here.
@admin.action(description="Export selected to CSV")
def export_subscribers_csv(modeladmin, request, queryset):
    # Gör filnamn med tidsstämpel
    ts = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"newsletter_subscribers_{ts}.csv"

    # Excel-vänligt: UTF-8 med BOM
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")  # BOM för Excel

    writer = csv.writer(response)
    # Header
    writer.writerow([
        "email",
        "confirmed",
        "unsubscribed",
        "created_at",
        "confirm_sent_at",
        "confirmed_at",
    ])
    # Rader
    for s in queryset.iterator():
        writer.writerow([
            s.email,
            "yes" if s.confirmed else "no",
            "yes" if s.unsubscribed else "no",
            s.created_at.isoformat() if s.created_at else "",
            s.confirm_sent_at.isoformat() if s.confirm_sent_at else "",
            s.confirmed_at.isoformat() if s.confirmed_at else "",
        ])

    return response


@admin.action(description="Export ALL confirmed to CSV")
def export_all_confirmed_csv(modeladmin, request, queryset):
    confirmed_qs = NewsletterSubscriber.objects.filter(confirmed=True, unsubscribed=False)
    return export_subscribers_csv(modeladmin, request, confirmed_qs)


@admin.action(description="Resend confirmation email")
def resend_confirmation(modeladmin, request, queryset):
    count = 0
    for sub in queryset:
        if not sub.confirmed and not sub.unsubscribed:
            try:
                # Skicka mailet igen
                send_newsletter_confirmation(sub, request)
                count += 1
            except Exception as e:
                messages.error(request, f"Failed for {sub.email}: {e}")
    if count:
        messages.success(request, f"Sent {count} confirmation email(s).")
    else:
        messages.warning(request, "No unconfirmed subscribers selected.")


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
    actions = [export_subscribers_csv, export_all_confirmed_csv, resend_confirmation]

