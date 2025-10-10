from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product


class CartViewTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="TestCat", slug="testcat")
        self.p = Product.objects.create(category=cat, name="P1", price=100, stock=5, slug="p1")

    def test_add_to_cart(self):
        res = self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 2})
        self.assertRedirects(res, self.p.get_absolute_url())
        self.assertEqual(self.client.session["cart"][str(self.p.id)], 2)

    def test_update_cart(self):
        self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 1})
        res = self.client.post(reverse("cart:update", args=[self.p.id]), {"qty": 3})
        self.assertRedirects(res, reverse("cart:view"))
        self.assertEqual(self.client.session["cart"][str(self.p.id)], 3)

    def test_remove_from_cart(self):
        self.client.post(reverse("cart:add", args=[self.p.id]), {"qty": 1})
        res = self.client.get(reverse("cart:remove", args=[self.p.id]))
        self.assertRedirects(res, reverse("cart:view"))
        self.assertNotIn(str(self.p.id), self.client.session["cart"])
