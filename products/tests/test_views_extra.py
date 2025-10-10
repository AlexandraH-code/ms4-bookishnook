from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product


class ProductViewsExtraTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Bookmarks", slug="bookmarks")
        self.sub = Category.objects.create(name="Leather", slug="leather", parent=self.cat)
        Product.objects.create(category=self.cat, name="Bookmark A", price=20, slug="bookmark-a")
        Product.objects.create(category=self.sub, name="Bookmark B", price=15, slug="bookmark-b")

    def test_product_list_base_loads(self):
        res = self.client.get(reverse("products:list"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "All Products")

    def test_category_filter_loads_correct_products(self):
        # Använd modellens URL för att undvika NoReverseMatch
        url = self.cat.get_absolute_url()  # e.g. /products/category/bookmarks/
        res = self.client.get(url)
        # Parent category should display both its own and subcategory products
        self.assertContains(res, "Bookmark A")
        self.assertContains(res, "Bookmark B")

    def test_search_filters_results(self):
        url = reverse("products:list")
        # Select a search string that is only found in "Bookmark A"
        res = self.client.get(url, {"q": "Bookmark A"})
        self.assertContains(res, "Bookmark A")
        self.assertNotContains(res, "Bookmark B")

    def test_sorting_price_high_to_low(self):
        url = reverse("products:list")
        res = self.client.get(url, {"sort": "-price"})
        self.assertEqual(res.status_code, 200)
        products = list(res.context["products"])
        # first should be more expensive than last
        self.assertGreater(products[0].price, products[-1].price)
