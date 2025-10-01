from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product
from decimal import Decimal

class ProductViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Root + ev. child-kategori för slug_path-stöd
        cls.root = Category.objects.create(name="Bookmarks", slug="bookmarks", is_active=True)
        cls.child = Category.objects.create(name="Metal", slug="metal", is_active=True, parent=cls.root)

        cls.p1 = Product.objects.create(
            name="Cozy Bookmark", slug="cozy-bookmark", price=Decimal("39.00"),
            category=cls.root, is_active=True
        )
        cls.p2 = Product.objects.create(
            name="Metal Feather", slug="metal-feather", price=Decimal("79.00"),
            category=cls.child, is_active=True
        )
        cls.p3 = Product.objects.create(
            name="Hidden Product", slug="hidden", price=Decimal("19.00"),
            category=cls.root, is_active=False
        )

        cls.list_url = reverse("products:list")  # byt om du använder annat namn
        # Ex: /products/category/<slug_path>/
        # Om din url tar slug_path med “bookmarks” eller “bookmarks/metal”
        # så kan du reverse:a med kwargs={"slug_path": "..."}
        cls.cat_root_url = reverse("products:category", kwargs={"slug_path": "bookmarks"})
        cls.cat_child_url = reverse("products:category", kwargs={"slug_path": "bookmarks/metal"})

    def test_list_status_template_and_context(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        # self.assertTemplateUsed(resp, "products/product_list.html")
        self.assertIn("products", resp.context)

        products = resp.context["products"]
        # Bara aktiva ska visas
        self.assertIn(self.p1, products)
        self.assertIn(self.p2, products)
        self.assertNotIn(self.p3, products)

    def test_category_root_filter(self):
        resp = self.client.get(self.cat_root_url)
        self.assertEqual(resp.status_code, 200)
        products = resp.context["products"]
        # root-sidan får visa både root och barn (beroende på din logik)
        self.assertIn(self.p1, products)
        self.assertIn(self.p2, products)  # om du visar barn på root-kategori
        # self.assertNotIn(self.p2, products)  # …eller kommentera ovan och använd denna om du INTE visar barn

    def test_category_child_filter(self):
        resp = self.client.get(self.cat_child_url)
        self.assertEqual(resp.status_code, 200)
        products = resp.context["products"]
        self.assertIn(self.p2, products)
        self.assertNotIn(self.p1, products)

    def test_search_query(self):
        resp = self.client.get(self.list_url, {"q": "Cozy"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Cozy Bookmark")
        self.assertNotContains(resp, "Metal Feather")  # om sök inte matchar “Cozy”

    def test_sorting_name_and_price(self):
        # sort=name
        resp = self.client.get(self.list_url, {"sort": "name"})
        self.assertEqual(resp.status_code, 200)
        products = list(resp.context["products"])
        # Alfabetiskt: Cozy Bookmark före Metal Feather
        self.assertEqual([p.slug for p in products], ["cozy-bookmark", "metal-feather"])

        # sort=-price (dyrast först)
        resp2 = self.client.get(self.list_url, {"sort": "-price"})
        products2 = list(resp2.context["products"])
        self.assertEqual([p.slug for p in products2], ["metal-feather", "cozy-bookmark"])

    def test_product_detail(self):
        url = reverse("products:detail", kwargs={"slug": self.p1.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # self.assertTemplateUsed(resp, "products/product_detail.html")
        self.assertEqual(resp.context["product"].id, self.p1.id)

    def test_inactive_product_detail_404(self):
        url = reverse("products:detail", kwargs={"slug": self.p3.slug})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
