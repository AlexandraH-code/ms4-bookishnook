from django.test import TestCase
from decimal import Decimal
from products.models import Category, Product

# Byt denna import till din faktiska formklass
# from backoffice.forms import ProductForm
from django import forms


# Minimal “stand-in” om du vill köra testet utan färdig form:
# Ta bort denna klass när du har en riktig ProductForm att importera.
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "slug", "price", "category", "is_active"]

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price


class ProductFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cat = Category.objects.create(name="Bookmarks", slug="bookmarks", is_active=True)
        Product.objects.create(
            name="Existing", slug="existing", price=Decimal("49.00"),
            category=cls.cat, is_active=True
        )

    def test_valid_payload(self):
        form = ProductForm(data={
            "name": "New Product",
            "slug": "new-product",
            "price": "79.00",
            "category": self.cat.id,
            "is_active": True,
        })
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_price_must_be_positive(self):
        form = ProductForm(data={
            "name": "Bad Price",
            "slug": "bad-price",
            "price": "0.00",
            "category": self.cat.id,
            "is_active": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_slug_must_be_unique(self):
        form = ProductForm(data={
            "name": "Duplicate",
            "slug": "existing",  # redan i setUpTestData
            "price": "59.00",
            "category": self.cat.id,
            "is_active": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("slug", form.errors)
