from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product

"""
Product list/search/sort and category filter behavior.
"""


class ProductViewsExtraTests(TestCase):
    """
    Covers base list, parent category including children, search and sorting.
    """

    def setUp(self):
        """
        Create a parent and subcategory with one product each.
        """

        self.cat = Category.objects.create(name="Bookmarks", slug="bookmarks")
        self.sub = Category.objects.create(name="Leather", slug="leather", parent=self.cat)
        Product.objects.create(category=self.cat, name="Bookmark A", price=20, slug="bookmark-a")
        Product.objects.create(category=self.sub, name="Bookmark B", price=15, slug="bookmark-b")

    def test_product_list_base_loads(self):
        """
        Plain list should render and include a default heading.
        """

        res = self.client.get(reverse("products:list"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "All Products")

    def test_category_filter_loads_correct_products(self):
        """
        Parent category page should contain both parent and child products.
        """

        url = self.cat.get_absolute_url()
        res = self.client.get(url)
        self.assertContains(res, "Bookmark A")
        self.assertContains(res, "Bookmark B")

    def test_search_filters_results(self):
        """
        Search query should narrow down to matching product names/descriptions.
        """

        url = reverse("products:list")
        res = self.client.get(url, {"q": "Bookmark A"})
        self.assertContains(res, "Bookmark A")
        self.assertNotContains(res, "Bookmark B")

    def test_sorting_price_high_to_low(self):
        """
        Sorting by -price should put higher priced items first.
        """

        url = reverse("products:list")
        res = self.client.get(url, {"sort": "-price"})
        self.assertEqual(res.status_code, 200)
        products = list(res.context["products"])

        self.assertGreater(products[0].price, products[-1].price)
