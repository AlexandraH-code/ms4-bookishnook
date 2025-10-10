# from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from products.models import Category, Product
from products.templatetags.price_filters import currency


class CartViewExtraTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="TestCat", slug="testcat")
        self.p = Product.objects.create(category=cat, name="P1", price=99, stock=5, slug="p1")

    def test_view_cart_empty(self):
        """Empty shopping cart should display the text 'Your cart is empty.'"""
        res = self.client.get(reverse("cart:view"))
        self.assertContains(res, "Your cart is empty.")

    def test_add_to_cart_non_post_redirects(self):
        """GET mot add ska bara redirecta och inte ändra vagnen."""
        url = reverse("cart:add", args=[self.p.id])
        res = self.client.get(url)
        self.assertRedirects(res, reverse("cart:view"))
        self.assertEqual(self.client.session.get("cart", {}), {})

    def test_update_cart_to_zero_removes_item(self):
        """qty=0 ska ta bort varan från vagnen."""
        # insert first
        self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 2})
        # update to 0
        res = self.client.post(reverse("cart:update", args=[self.p.id]), {"qty": 0})
        self.assertRedirects(res, reverse("cart:view"))
        self.assertNotIn(str(self.p.id), self.client.session.get("cart", {}))

    def test_view_cart_totals_and_render(self):
        """Display name + total cost (sum of subtotals)."""
        # add two different rows (same product twice for simplicity)
        self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 1})
        self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 2})
        res = self.client.get(reverse("cart:view"))

        expected_total = self.p.price * 3  # 297.00
        expected_str = currency(expected_total)  # same formatting (period/comma + SEK) as in the template

        self.assertContains(res, self.p.name)
        self.assertContains(res, expected_str)

    def test_messages_on_add_and_remove(self):
        """Check that flash messages are set on add/remove."""
        # add
        res = self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 1}, follow=True)
        messages = [m.message for m in get_messages(res.wsgi_request)]
        self.assertTrue(any("Added" in m for m in messages))

        # remove (your view removes with GET or POST; we use POST as in the template)
        res = self.client.post(reverse("cart:remove", args=[self.p.id]), follow=True)
        messages = [m.message for m in get_messages(res.wsgi_request)]
        self.assertTrue(any("Item removed" in m for m in messages))
