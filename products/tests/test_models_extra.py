from django.test import TestCase
from products.models import Category, Product

"""
Model niceties: auto slug + absolute URL uses slug.
"""


class ProductModelExtraTests(TestCase):
    """
    Sanity checks for slug generation and get_absolute_url.
    """

    def test_product_slug_auto_set_and_url(self):
        cat = Category.objects.create(name="Cat", slug="cat")
        p = Product.objects.create(category=cat, name="Nice Lamp", price=10)
        self.assertTrue(p.slug)  # auto-set
        self.assertIn(p.slug, p.get_absolute_url())