from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product

"""
Rendering basics for checkout start page.
"""


class CheckoutViewsExtraTests(TestCase):
    """
    Smoke tests for start page content and totals section.
    """

    def setUp(self):
        """
        Start page renders product and heading.
        """

        cat = Category.objects.create(name="TestCat", slug="testcat")
        self.p = Product.objects.create(category=cat, name="Lamp", price=150, stock=2, slug="lamp")
        session = self.client.session
        session["cart"] = {str(self.p.id): 1}
        session.save()

    def test_checkout_start_loads(self):
        """
        Start page renders product and heading.
        """

        res = self.client.get(reverse("checkout:start"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Checkout")
        self.assertContains(res, self.p.name)

    def test_checkout_totals_displayed(self):
        """
        Start page shows subtotal/tax/total labels.
        """

        res = self.client.get(reverse("checkout:start"))
        content = res.content.decode()
        self.assertIn("Subtotal", content)
        self.assertIn("Tax", content)
        self.assertIn("Total", content)
