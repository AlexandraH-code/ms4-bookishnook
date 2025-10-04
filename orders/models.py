from django.db import models
from django.conf import settings
from products.models import Product


# Create your models here.
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    confirmation_sent_at = models.DateTimeField(blank=True, null=True)
    
    # Customer data (from Stripe)
    full_name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    # Delivery address
    address_line1 = models.CharField(max_length=200, blank=True, null=True)
    address_line2 = models.CharField(max_length=200, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=2, blank=True, null=True)
    
    # Billing address
    billing_name = models.CharField(max_length=200, blank=True, null=True)
    billing_line1 = models.CharField(max_length=200, blank=True, null=True)
    billing_line2 = models.CharField(max_length=200, blank=True, null=True)
    billing_postal = models.CharField(max_length=20, blank=True, null=True)
    billing_city = models.CharField(max_length=100, blank=True, null=True)
    billing_country = models.CharField(max_length=2, blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} x {self.qty}"


class ProcessedStripeEvent(models.Model):
    event_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)