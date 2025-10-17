import csv
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import admin, messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html
from .models import NewsletterSubscriber
from .utils import send_newsletter_confirmation


@admin.action(description="Export selected to CSV")
def export_subscribers_csv(modeladmin, request, queryset):
    ts = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"newsletter_subscribers_{ts}.csv"

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")  # BOM for Excel

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
    list_display = ("email", "confirmed", "unsubscribed", "created_at", "confirmed_at", "confirm_now_button")
    list_filter = ("confirmed", "unsubscribed", "created_at")
    search_fields = ("email",)
    ordering = ("-created_at",)
    readonly_fields = ("confirm_token", "unsubscribe_token", "created_at", "confirm_sent_at", "confirmed_at", "confirm_now_button")

    fieldsets = (
        (None, {
            "fields": ("email", "confirmed", "unsubscribed", "confirm_now_button")
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

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:pk>/confirm-now/",
                self.admin_site.admin_view(self.confirm_now_view),
                name="home_newslettersubscriber_confirm_now",
            ),
        ]
        return custom + urls

    def confirm_now_view(self, request, pk: int):
        sub = get_object_or_404(NewsletterSubscriber, pk=pk)
        if sub.unsubscribed:
            self.message_user(request, f"{sub.email} is unsubscribed. Set unsubscribed = False first.", level=messages.WARNING)
            return redirect("admin:home_newslettersubscriber_change", pk)

        if not sub.confirmed:
            sub.confirmed = True
            sub.confirmed_at = timezone.now()
            sub.save(update_fields=["confirmed", "confirmed_at"])
            self.message_user(request, f"{sub.email} marked as confirmed.", level=messages.SUCCESS)
        else:
            self.message_user(request, f"{sub.email} is already confirmed.", level=messages.INFO)

        return redirect("admin:home_newslettersubscriber_change", pk)

    @admin.display(description="Confirm now")
    def confirm_now_button(self, obj):
        if obj.unsubscribed:
            return format_html('<span style="color:#dc3545;">Unsubscribed</span>')
        if obj.confirmed:
            return format_html('<span style="color:#28a745;">Confirmed</span>')
        url = reverse("admin:home_newslettersubscriber_confirm_now", args=[obj.pk])
        return format_html('<a class="button" href="{}">Confirm now</a>', url)

    class Media:
        css = {"all": ("admin/css/widgets.css",)}
