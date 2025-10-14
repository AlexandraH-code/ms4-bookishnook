from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product

"""
Totals calculation on checkout start.
"""


class CheckoutStartTotalsTests(TestCase):
    """
    Validate subtotal, tax, shipping, grand total on the start page.
    """

    def setUp(self):
        """
        Create a product with a neat price to make math assertions explicit.
        """

        c = Category.objects.create(name="Cat", slug="cat")
        self.p = Product.objects.create(category=c, name="P", price=Decimal("200.00"), stock=10, slug="p")

    def test_totals_shipping_and_tax(self):
        """
        3×200 = 600 → free shipping; VAT 25% → 150; grand total 750.
        """

        session = self.client.session
        session["cart"] = {str(self.p.id): 3}
        session.save()
        res = self.client.get(reverse("checkout:start"))
        self.assertEqual(res.status_code, 200)
        ctx = res.context
        self.assertEqual(ctx["total"], Decimal("600.00"))
        self.assertEqual(ctx["shipping"], Decimal("0.00"))
        self.assertEqual(ctx["tax_amount"], Decimal("150.00"))
        self.assertEqual(ctx["grand_total"], Decimal("750.00"))
