from django.test import TestCase
from products.models import Category, Product
from backoffice.forms import ProductForm  # your form is located in backoffice.forms

class ProductFormSlugUniqueTests(TestCase):
    """Ensure the form makes the slug unique (p1, p1-2, p1-3, ...)."""

    def setUp(self):
        self.c = Category.objects.create(name="Cat", slug="cat")

    def test_slug_deduplication(self):
        # Create first product
        p1 = Product.objects.create(category=self.c, name="Nice Name", price=10)
        self.assertTrue(p1.slug)  # auto-slugify vid save

        # Try creating others with the same name via the form
        form = ProductForm(data={
            "category": self.c.id,
            "name": "Nice Name",
            "slug": "",  # let clean_slug create for us
            "description": "",
            "price": "12.00",
            "is_active": "1",
        })
        self.assertTrue(form.is_valid(), form.errors)
        p2 = form.save()
        self.assertNotEqual(p1.slug, p2.slug)
        self.assertTrue(p2.slug.startswith(p1.slug))    # e.g. nice-name-2
