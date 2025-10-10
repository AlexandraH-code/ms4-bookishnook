from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product


class ProductEdgesTests(TestCase):
    def setUp(self):
        self.root = Category.objects.create(name="Root", slug="root")
        self.child = Category.objects.create(name="Child", slug="child", parent=self.root)
        self.leaf = Category.objects.create(name="Leaf", slug="leaf", parent=self.child)

        Product.objects.create(category=self.root, name="A", price=10, slug="a")
        Product.objects.create(category=self.child, name="B", price=20, slug="b")
        Product.objects.create(category=self.leaf, name="C", price=30, slug="c")

    def test_descendant_ids_includes_all_levels(self):
        ids = set(self.root.descendant_ids())
        self.assertIn(self.root.id, ids)
        self.assertIn(self.child.id, ids)
        self.assertIn(self.leaf.id, ids)

    def test_sort_fallback_on_invalid_value(self):
        # sort parameter that is not whitelisted should fall back to name
        res = self.client.get(reverse("products:list"), {"sort": "INVALID"})
        self.assertEqual(res.status_code, 200)
        # simple sanity: all three products are rendered
        content = res.content.decode()
        for n in ["A", "B", "C"]:
            self.assertIn(n, content)
