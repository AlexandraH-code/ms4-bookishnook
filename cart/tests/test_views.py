from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product
from decimal import Decimal


class CartFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name="Bookmarks", slug="bookmarks", is_active=True)
        cls.prod = Product.objects.create(
            name="Tab Bookmark", slug="tab-bookmark", price=Decimal("29.00"),
            category=cls.cat, is_active=True
        )
        cls.add_url = reverse("cart:add", args=[cls.prod.id])
        cls.view_url = reverse("cart:view")
        cls.remove_url = reverse("cart:remove", args=[cls.prod.id])
        # ev. update_url = reverse("cart:update", args=[cls.prod.id])

    def test_add_and_view_cart(self):
        resp = self.client.post(self.add_url, {"quantity": 2}, follow=True)
        self.assertEqual(resp.status_code, 200)
        resp2 = self.client.get(self.view_url)
        self.assertContains(resp2, "Tab Bookmark")

    def test_remove_from_cart(self):
        self.client.post(self.add_url, {"quantity": 1})
        resp = self.client.post(self.remove_url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Tab Bookmark")
