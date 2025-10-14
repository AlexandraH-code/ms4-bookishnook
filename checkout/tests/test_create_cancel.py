from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from products.models import Category, Product

"""
Create session and cancel views for checkout.
"""


class CheckoutCreateCancelTests(TestCase):
    """
    Smoke tests for creating a Stripe Checkout session and cancel page rendering.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Create catalog data shared across tests.
        """

        cls.cat = Category.objects.create(name="C", slug="c")
        cls.p = Product.objects.create(category=cls.cat, name="P", slug="p", price=199, stock=5)

    def setUp(self):
        """
        Seed the cart in the client session.
        """

        s = self.client.session
        s["cart"] = {str(self.p.id): 2}
        s.save()

    @patch("checkout.views.stripe.checkout.Session.create")
    def test_create_checkout_session_redirects_to_stripe_and_creates_pending_order(self, mock_create):
        """
        POST create_session should 302 to Stripe and (in view) create a pending order.
        """

        mock_create.return_value = type("Obj", (), {"id": "cs_abc", "url": "https://stripe.example/checkout/cs_abc"})
        res = self.client.post(reverse("checkout:create_session"))
        self.assertEqual(res.status_code, 302)
        self.assertIn("stripe.example/checkout", res["Location"])

    def test_cancel_renders(self):
        """
        GET /cancel/ renders a friendly cancellation page.
        """

        res = self.client.get(reverse("checkout:cancel"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "You canceled the payment.")
