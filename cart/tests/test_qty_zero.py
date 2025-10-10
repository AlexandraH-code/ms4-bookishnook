from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product


class CartZeroQtyTests(TestCase):
    """
    Updating to 0 will remove the item from the cart.
    """

    def setUp(self):
        c = Category.objects.create(name="C", slug="c")
        self.p = Product.objects.create(category=c, name="X", slug="x", price=10, stock=5)

    def test_update_to_zero_removes(self):
        # Add first
        self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 2})
        # Set qty=0 → to be removed
        res = self.client.post(reverse("cart:update", args=[self.p.id]), {"qty": 0})
        self.assertEqual(res.status_code, 302)  # redirect till cart:view
        self.assertNotIn(str(self.p.id), self.client.session.get("cart", {}))
