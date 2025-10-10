from django.conf import settings
from django.db import models

"""
Profile and Address models for storing user-specific data and saved addresses.
"""

# Create your models here.
User = settings.AUTH_USER_MODEL


class Profile(models.Model):
    """
    Lightweight user profile linked one-to-one with the Django user.

    Fields:
        user (User): The owning user (1:1).
        full_name (str): Optional display/real name.
        phone (str): Optional phone number.
        newsletter_opt_in (bool): Whether the user opted in to the newsletter.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    newsletter_opt_in = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile({self.user})"


ADDRESS_TYPES = (
    ("shipping","Shipping"),
    ("billing","Billing"),
)


class Address(models.Model):
    """
    A saved address for a user, either shipping or billing.

    Fields:
        user (User): The address owner.
        kind (str): Either "shipping" or "billing".
        full_name (str): Optional contact name for the address.
        phone (str): Optional contact phone.
        line1, line2 (str): Street address lines.
        postal_code (str): Postal or ZIP code.
        city (str): City.
        country (str): ISO 3166-1 alpha-2 code (e.g., "SE").
        is_default (bool): If true, marks this as the default for its kind.

    Constraints:
        Only one default per (user, kind) is enforced in `save()`.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    kind = models.CharField(max_length=20, choices=ADDRESS_TYPES)
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=2, default="SE")  # ISO 2
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["kind", "-is_default", "id"]

    def __str__(self):
        return f"{self.get_kind_display()} • {self.line1}, {self.city}"

    def save(self, *args, **kwargs):
        """
        Save the address and ensure at most one default per (user, kind).

        If this instance is marked as default, all other addresses of the same
        kind for the same user will have `is_default` cleared.
        """

        super().save(*args, **kwargs)
        # Make sure there is only one default per type
        if self.is_default:
            Address.objects.filter(user=self.user, kind=self.kind).exclude(id=self.id).update(is_default=False)
