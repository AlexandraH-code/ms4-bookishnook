from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product


class CheckoutViewsExtraTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="TestCat", slug="testcat")
        self.p = Product.objects.create(category=cat, name="Lamp", price=150, stock=2, slug="lamp")
        # add to cart
        session = self.client.session
        session["cart"] = {str(self.p.id): 1}
        session.save()

    def test_checkout_start_loads(self):
        res = self.client.get(reverse("checkout:start"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Checkout")
        self.assertContains(res, self.p.name)

    def test_checkout_totals_displayed(self):
        res = self.client.get(reverse("checkout:start"))
        content = res.content.decode()
        self.assertIn("Subtotal", content)
        self.assertIn("Tax", content)
        self.assertIn("Total", content)
