from django.test import TestCase
from products.models import Category, Product
from backoffice.forms import ProductForm

"""
Form-level slug de-duplication for products created via backoffice form.
"""


class ProductFormSlugUniqueTests(TestCase):
    """
    When creating multiple products with the same name, slugs should be uniquified.
    """

    def setUp(self):
        """
        Root category for the products.
        """

        self.c = Category.objects.create(name="Cat", slug="cat")

    def test_slug_deduplication(self):
        """
        Second product with same name should get a unique slug (e.g., '-2').
        """

        p1 = Product.objects.create(category=self.c, name="Nice Name", price=10)
        self.assertTrue(p1.slug)

        form = ProductForm(data={
            "category": self.c.id,
            "name": "Nice Name",
            "slug": "",
            "description": "",
            "price": "12.00",
            "is_active": "1",
        })
        self.assertTrue(form.is_valid(), form.errors)
        p2 = form.save()
        self.assertNotEqual(p1.slug, p2.slug)
        self.assertTrue(p2.slug.startswith(p1.slug))
