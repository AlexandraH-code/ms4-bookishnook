from django.contrib import admin
from .models import Profile, Address


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "phone", "newsletter_opt_in")
    search_fields = ("user__email", "full_name", "phone")

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "full_name", "city", "country", "is_default")
    list_filter = ("kind", "country", "is_default")
    search_fields = ("user__email", "full_name", "city")
