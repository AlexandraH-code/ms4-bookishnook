from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product


class CheckoutStartTotalsTests(TestCase):
    def setUp(self):
        c = Category.objects.create(name="Cat", slug="cat")
        self.p = Product.objects.create(category=c, name="P", price=Decimal("200.00"), stock=10, slug="p")

    def test_totals_shipping_and_tax(self):
        # add 2 pcs to cart => total=400 -> free shipping according to your rule (>=500? adjust qty to 3 if you have limit 500)
        # free shipping total < 500
        session = self.client.session
        session["cart"] = {str(self.p.id): 3}  # 3*200=600 -> free shipping
        session.save()
        res = self.client.get(reverse("checkout:start"))
        self.assertEqual(res.status_code, 200)
        ctx = res.context
        self.assertEqual(ctx["total"], Decimal("600.00"))
        self.assertEqual(ctx["shipping"], Decimal("0.00"))
        self.assertEqual(ctx["tax_amount"], Decimal("150.00"))  # 25% på 600
        self.assertEqual(ctx["grand_total"], Decimal("750.00"))
