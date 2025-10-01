from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Category, Product
from decimal import Decimal

User = get_user_model()


class BackofficeProductsPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(email="staff@example.com", password="pass12345", is_staff=True)
        cls.cat = Category.objects.create(name="Bookmarks", slug="bookmarks", is_active=True)

        # Skapa många produkter för att trigga paginering (justera vid behov)
        bulk = []
        for i in range(1, 101):  # 100 st
            bulk.append(Product(
                name=f"Prod {i}",
                slug=f"prod-{i}",
                price=Decimal("10.00") + i,
                category=cls.cat,
                is_active=True
            ))
        Product.objects.bulk_create(bulk)

        cls.list_url = reverse("backoffice:products_list")  # byt om du använder annat namn

    def setUp(self):
        self.client.login(email="staff@example.com", password="pass12345")

    def test_first_page_has_page_obj_and_elided_range(self):
        resp = self.client.get(self.list_url)  # page=1
        self.assertEqual(resp.status_code, 200)

        # Förutsätter att din vy skickar "page_obj" och "elided_range" (en lista)
        self.assertIn("page_obj", resp.context)
        self.assertIn("elided_range", resp.context)

        page_obj = resp.context["page_obj"]
        elided = resp.context["elided_range"]

        self.assertTrue(page_obj.has_next())
        self.assertGreater(len(elided), 0)  # kan innehålla siffror + '…'

    def test_middle_page_shows_ellipsis(self):
        # Välj en sida i mitten (ex page=5) – elided_range bör innehålla '…'
        resp = self.client.get(self.list_url, {"page": 5})
        self.assertEqual(resp.status_code, 200)
        elided = resp.context["elided_range"]
        self.assertTrue(any(x in ("…", "...") for x in elided), f"elided_range={elided}")

    def test_last_page_has_previous_only(self):
        # Hitta sista sidan
        resp = self.client.get(self.list_url, {"page": 9999})
        self.assertEqual(resp.status_code, 200)
        page_obj = resp.context["page_obj"]
        self.assertFalse(page_obj.has_next())
        self.assertTrue(page_obj.has_previous())

    def test_page_size_row_count(self):
        # Om du visar desktop-tabell i template, bekräfta att ungefär rätt antal rader visas.
        # Anta page_size=20 (byt till din size)
        page_size = 20
        resp = self.client.get(self.list_url, {"page": 1})
        self.assertEqual(resp.status_code, 200)

        # Räkna förekomst i HTML: “Prod ” är lite grovt men duger som sanity check.
        # Alternativ: använd context["products"] om din vy skickar just den listan per sida.
        products = resp.context.get("products")
        if products is not None:
            self.assertLessEqual(len(products), page_size)
        else:
            # fallback: textmatch (grovt)
            count = resp.content.decode("utf-8").count("Prod ")
            self.assertLessEqual(count, page_size)
