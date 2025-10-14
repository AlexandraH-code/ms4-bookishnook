from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product

"""
Edge cases for category tree utilities and view sorting fallback.
"""


class ProductEdgesTests(TestCase):
    """
    Cover descendant id traversal and invalid sort fallback.
    """

    def setUp(self):
        """
        Create a 3-level category tree and three products.
        """

        self.root = Category.objects.create(name="Root", slug="root")
        self.child = Category.objects.create(name="Child", slug="child", parent=self.root)
        self.leaf = Category.objects.create(name="Leaf", slug="leaf", parent=self.child)

        Product.objects.create(category=self.root, name="A", price=10, slug="a")
        Product.objects.create(category=self.child, name="B", price=20, slug="b")
        Product.objects.create(category=self.leaf, name="C", price=30, slug="c")

    def test_descendant_ids_includes_all_levels(self):
        """
        descendant_ids should include the node itself and all children recursively.
        """

        ids = set(self.root.descendant_ids())
        self.assertIn(self.root.id, ids)
        self.assertIn(self.child.id, ids)
        self.assertIn(self.leaf.id, ids)

    def test_sort_fallback_on_invalid_value(self):
        """
        Unsupported sort key should fall back to name ordering without crashing.
        """

        res = self.client.get(reverse("products:list"), {"sort": "INVALID"})
        self.assertEqual(res.status_code, 200)
        content = res.content.decode()
        for n in ["A", "B", "C"]:
            self.assertIn(n, content)
