from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Category, Product
from decimal import Decimal

User = get_user_model()


class BackofficeProductsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(email="staff@example.com", password="pass12345", is_staff=True)
        cls.cat = Category.objects.create(name="Bookmarks", slug="bookmarks", is_active=True)
        cls.p = Product.objects.create(
            name="Admin Bookmark", slug="admin-bookmark", price=Decimal("59.00"),
            category=cls.cat, is_active=True
        )
        cls.list_url = reverse("backoffice:products_list")
        cls.create_url = reverse("backoffice:product_create")
        cls.edit_url = reverse("backoffice:product_edit", args=[cls.p.id])
        cls.del_url = reverse("backoffice:product_delete", args=[cls.p.id])

    def setUp(self):
        self.client.login(email="staff@example.com", password="pass12345")

    def test_products_list_loads(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        # self.assertTemplateUsed(resp, "backoffice/products_list.html")
        self.assertContains(resp, "Admin Bookmark")

    def test_create_product(self):
        payload = {
            "name": "New Admin Product",
            "slug": "new-admin-product",
            "price": "79.00",
            "category": self.cat.id,
            "is_active": "on",
        }
        resp = self.client.post(self.create_url, data=payload, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Product.objects.filter(slug="new-admin-product").exists())

    def test_edit_product(self):
        payload = {
            "name": "Edited Name",
            "slug": self.p.slug,
            "price": "69.00",
            "category": self.cat.id,
            "is_active": "on",
        }
        resp = self.client.post(self.edit_url, data=payload, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.p.refresh_from_db()
        self.assertEqual(self.p.name, "Edited Name")

    def test_delete_product(self):
        resp = self.client.post(self.del_url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Product.objects.filter(id=self.p.id).exists())
