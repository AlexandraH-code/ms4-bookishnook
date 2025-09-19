from django.conf import settings
from django.db import models

# Create your models here.
User = settings.AUTH_USER_MODEL


class Profile(models.Model):
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
        super().save(*args, **kwargs)
        # Se till att bara en default per typ
        if self.is_default:
            Address.objects.filter(user=self.user, kind=self.kind).exclude(id=self.id).update(is_default=False)
