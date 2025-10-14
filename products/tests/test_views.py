from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product

"""
Core product views: list, detail, and category filter.
"""


class ProductViewsTests(TestCase):
    """
    Essential rendering checks for product pages.
    """

    def setUp(self):
        """
        One category and one product.
        """

        self.cat = Category.objects.create(name="Books", slug="books")
        self.p = Product.objects.create(category=self.cat, name="Novel", slug="novel", price=199)

    def test_product_list(self):
        """
        List page should include the product's name.
        """

        res = self.client.get(reverse("products:list"))
        self.assertContains(res, "Novel")

    def test_product_detail(self):
        """
        Detail page should render when addressed by slug.
        """

        res = self.client.get(reverse("products:detail", args=[self.p.slug]))
        self.assertContains(res, "Novel")

    def test_filter_by_category(self):
        """
        Category URL should include the product that belongs to it.
        """

        url = self.cat.get_absolute_url()
        res = self.client.get(url)
        self.assertContains(res, "Novel")
