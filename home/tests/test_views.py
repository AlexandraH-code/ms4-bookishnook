from django.test import TestCase
from django.urls import reverse
from products.models import Category


class HomeViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Några kategorier för startsidans “featured”
        cls.c1 = Category.objects.create(
            name="Bookmarks", slug="bookmarks", is_active=True, featured_order=2
        )
        cls.c2 = Category.objects.create(
            name="Book Sleeves", slug="book-sleeves", is_active=True, featured_order=1
        )
        # En inaktiv kategori ska inte visas
        cls.c3 = Category.objects.create(
            name="Hidden", slug="hidden", is_active=False, featured_order=3
        )

    def test_home_status_and_template(self):
        url = reverse("home:index")  # byt till din url-name
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # self.assertTemplateUsed(resp, "home/index.html")

    def test_home_featured_categories_present_and_sorted(self):
        url = reverse("home:index")
        resp = self.client.get(url)

        # Justera om din context key heter något annat (t.ex. 'featured_cats')
        featured = resp.context.get("featured_categories")
        self.assertIsNotNone(featured)

        # Inaktiva kategorier ska inte vara med
        self.assertIn(self.c1, featured)
        self.assertIn(self.c2, featured)
        self.assertNotIn(self.c3, featured)

        # Sortering enligt featured_order (c2=1 före c1=2)
        self.assertEqual(list(featured), [self.c2, self.c1])
