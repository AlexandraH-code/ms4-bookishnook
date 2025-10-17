from django.db import models
# from django.conf import settings
from products.models import Product

"""
Order domain models.

Includes:
- Order: a customer order with monetary totals, status, and shipping/billing info.
- OrderItem: line items belonging to an order.
- ProcessedStripeEvent: idempotency helper to ensure each Stripe webhook event
  is processed at most once.
"""


class Order(models.Model):
    """
    Represents a single customer order.

    Fields:
        created (DateTime): When the order record was created.
        updated (DateTime): When the order was last updated.
        total (Decimal): Sum of item subtotals before tax and shipping.
        shipping (Decimal): Shipping cost applied to this order.
        tax_amount (Decimal): Tax applied to this order.
        grand_total (Decimal): Total + shipping + tax.
        status (Char): Order status (pending/paid/cancelled).
        stripe_session_id (Char): Stripe Checkout Session id associated with the order.
        confirmation_sent_at (DateTime): Timestamp when a confirmation email was sent.

        full_name (Char): Customer full name.
        email (Email): Customer email address.
        phone (Char): Customer phone number.

        # Shipping address (delivery)
        address_line1 (Char)
        address_line2 (Char)
        postal_code (Char)
        city (Char)
        country (Char, ISO 3166-1 alpha-2)

        # Billing address (invoice)
        billing_name (Char)
        billing_line1 (Char)
        billing_line2 (Char)
        billing_postal (Char)
        billing_city (Char)
        billing_country (Char, ISO 3166-1 alpha-2)
    """

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
        """
        Human-readable representation used in admin/console.
        """

        return f"Order #{self.id} ({self.status})"


class OrderItem(models.Model):
    """
    A single line item in an order.

    Fields:
        order (FK Order): Parent order.
        product (FK Product): Product snapshot reference.
        name (Char): Product name at time of purchase.
        unit_price (Decimal): Price per unit at time of purchase.
        qty (PositiveInteger): Quantity purchased.
        subtotal (Decimal): unit_price * qty.
    """

    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        """
        Readable summary of the purchased quantity and title.
        """

        return f"{self.name} x {self.qty}"


class ProcessedStripeEvent(models.Model):
    """
    Tracks processed Stripe webhook event IDs to enforce idempotency.

    Fields:
        event_id (Char, unique): The Stripe event id.
        created_at (DateTime): When this event was recorded as processed.
    """

    event_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
