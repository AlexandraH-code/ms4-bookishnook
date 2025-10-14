from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product
"""Cart: updating quantity to zero removes the item."""


class CartZeroQtyTests(TestCase):
    """
    Ensure qty=0 updates remove items from the session cart.
    """

    def setUp(self):
        """
        Create a category and a product used across tests.
        """

        c = Category.objects.create(name="C", slug="c")
        self.p = Product.objects.create(category=c, name="X", slug="x", price=10, stock=5)

    def test_update_to_zero_removes(self):
        """
        Posting qty=0 to update endpoint removes the product and redirects.
        """

        self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 2})
        res = self.client.post(reverse("cart:update", args=[self.p.id]), {"qty": 0})
        self.assertEqual(res.status_code, 302)
        self.assertNotIn(str(self.p.id), self.client.session.get("cart", {}))
