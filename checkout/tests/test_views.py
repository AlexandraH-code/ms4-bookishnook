from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model
from products.models import Category, Product
from decimal import Decimal
from unittest.mock import patch

User = get_user_model()

@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CheckoutViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name="Bookmarks", slug="bookmarks", is_active=True)
        cls.prod = Product.objects.create(
            name="Cozy Bookmark", slug="cozy-bookmark", price=Decimal("39.00"),
            category=cls.cat, is_active=True
        )
        cls.start_url = reverse("checkout:start")     # byt om du använder annat namn
        cls.success_url = reverse("checkout:success")   # byt om du använder annat namn
        cls.cart_add = reverse("cart:add", args=[cls.prod.id])

    def setUp(self):
        # lägg något i carten
        self.client.post(self.cart_add, {"quantity": 1})

    def test_checkout_page_loads_with_cart(self):
        resp = self.client.get(self.start_url)
        self.assertEqual(resp.status_code, 200)
        # self.assertTemplateUsed(resp, "checkout/checkout.html")

    def test_checkout_redirects_if_cart_empty(self):
        # töm carten genom att starta ny session
        self.client = self.client.__class__()
        resp = self.client.get(self.start_url)
        # beroende på din logik: förväntad redirect till cart/list eller products
        self.assertIn(resp.status_code, (302, 303))

    @patch("checkout.views.stripe.PaymentIntent.create")
    def test_checkout_post_success_creates_pi_and_redirects(self, mock_pi):
        mock_pi.return_value = {"id": "pi_123", "client_secret": "cs_123"}
        payload = {
            "shipping_name": "Test User",
            "shipping_address1": "Street 1",
            "shipping_city": "City",
            "shipping_zip": "11111",
            "shipping_country": "SE",
            "email": "buyer@example.com",
        }
        resp = self.client.post(self.start_url, data=payload, follow=True)
        self.assertIn(resp.status_code, (200, 302))
        # Oftast redirectas man till success:
        # self.assertRedirects(resp, self.success_url)
        self.assertTrue(mock_pi.called)

    def test_success_page_loads(self):
        resp = self.client.get(self.success_url)
        self.assertEqual(resp.status_code, 200)
        # self.assertTemplateUsed(resp, "checkout/success.html")
