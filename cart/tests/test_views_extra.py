# from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from products.models import Category, Product
from products.templatetags.price_filters import currency

"""
Extra coverage for cart views: empty state, redirects, totals and flash messages.
"""


class CartViewExtraTests(TestCase):
    """
    Covers ancillary cart behaviors beyond the basic add/update/remove.
    """

    def setUp(self):
        """
        Create a category and one product for cart operations.
        """

        cat = Category.objects.create(name="TestCat", slug="testcat")
        self.p = Product.objects.create(category=cat, name="P1", price=99, stock=5, slug="p1")

    def test_view_cart_empty(self):
        """
        Empty cart page shows the 'Your cart is empty.' message.
        """

        res = self.client.get(reverse("cart:view"))
        self.assertContains(res, "Your cart is empty.")

    def test_add_to_cart_non_post_redirects(self):
        """
        GET to add endpoint should redirect and not modify the cart.
        """

        url = reverse("cart:add", args=[self.p.id])
        res = self.client.get(url)
        self.assertRedirects(res, reverse("cart:view"))
        self.assertEqual(self.client.session.get("cart", {}), {})

    def test_update_cart_to_zero_removes_item(self):
        """
        Updating qty to zero removes the item and redirects back to cart.
        """

        self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 2})
        res = self.client.post(reverse("cart:update", args=[self.p.id]), {"qty": 0})
        self.assertRedirects(res, reverse("cart:view"))
        self.assertNotIn(str(self.p.id), self.client.session.get("cart", {}))

    def test_view_cart_totals_and_render(self):
        """
        Cart page renders item name and total using the same currency formatting as templates.
        """

        self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 1})
        self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 2})
        res = self.client.get(reverse("cart:view"))

        expected_total = self.p.price * 3
        expected_str = currency(expected_total)

        self.assertContains(res, self.p.name)
        self.assertContains(res, expected_str)

    def test_messages_on_add_and_remove(self):
        """
        Flash messages appear after add and remove operations.
        """

        res = self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 1}, follow=True)
        messages = [m.message for m in get_messages(res.wsgi_request)]
        self.assertTrue(any("Added" in m for m in messages))

        res = self.client.post(reverse("cart:remove", args=[self.p.id]), follow=True)
        messages = [m.message for m in get_messages(res.wsgi_request)]
        self.assertTrue(any("Item removed" in m for m in messages))
