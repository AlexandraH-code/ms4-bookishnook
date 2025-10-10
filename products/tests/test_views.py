from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product

class ProductViewsTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Books", slug="books")
        self.p = Product.objects.create(category=self.cat, name="Novel", slug="novel", price=199)

    def test_product_list(self):
        res = self.client.get(reverse("products:list"))
        self.assertContains(res, "Novel")

    def test_product_detail(self):
        res = self.client.get(reverse("products:detail", args=[self.p.slug]))
        self.assertContains(res, "Novel")

    def test_filter_by_category(self):
        url = self.cat.get_absolute_url()  # /products/category/books/
        res = self.client.get(url)
        self.assertContains(res, "Novel")
