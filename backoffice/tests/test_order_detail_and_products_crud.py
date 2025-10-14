from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Category, Product
from orders.models import Order

User = get_user_model()
"""
Backoffice: order detail actions + product CRUD smoke tests.
"""


class BackofficeDetailAndCrudTests(TestCase):
    """
    Ensure order status transitions and product create/edit/delete flows work.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Seed staff user, category/product, and a pending order.
        """

        cls.staff = User.objects.create_user(username="s", password="x", is_staff=True)
        cls.cat = Category.objects.create(name="Cat", slug="cat")
        cls.prod = Product.objects.create(category=cls.cat, name="P1", slug="p1", price=100, stock=10)
        cls.order = Order.objects.create(email="a@b.com", status="pending", total=100, grand_total=100)

    def setUp(self):
        """
        Log in staff before each test.
        """

        self.client.login(username="s", password="x")

    def test_order_detail_mark_paid_changes_status(self):
        """
        Posting 'mark_paid' transitions the order to PAID and redirects back.
        """

        url = reverse("backoffice:order_detail", args=[self.order.id])
        res = self.client.post(url, {"action": "mark_paid"})
        self.assertRedirects(res, url)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    def test_orders_list_filters_and_search(self):
        """
        Orders list supports filtering by status and searching by email.
        """

        Order.objects.create(email="x@example.com", status="paid", total=10, grand_total=10)
        Order.objects.create(email="y@example.com", status="processing", total=20, grand_total=20)
        url = reverse("backoffice:orders_list")
        res = self.client.get(url, {"status": "paid"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(any(o.status == "paid" for o in res.context["orders"]))
        res2 = self.client.get(url, {"q": "y@example.com"})
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(all("y@example.com" in (o.email or "") for o in res2.context["orders"]))

    def test_products_list_filters_active_and_search(self):
        """
        Products list supports active filter and search results.
        """

        Product.objects.create(category=self.cat, name="Searchable", slug="search", price=50, stock=1, is_active=False)
        url = reverse("backoffice:products_list")
        res = self.client.get(url, {"q": "Search"})
        self.assertContains(res, "Searchable")
        res2 = self.client.get(url, {"active": "1"})
        self.assertContains(res2, "P1")
        self.assertNotContains(res2, "Searchable")

    def test_product_create_edit_delete(self):
        """
        Create → edit → delete product roundtrip with redirects and persisted changes.
        """

        create_url = reverse("backoffice:product_create")
        res = self.client.post(create_url, {
            "category": self.cat.id,
            "name": "New P",
            "slug": "new-p",
            "description": "d",
            "price": "123.45",
            "is_active": "on",
        })
        self.assertRedirects(res, reverse("backoffice:products_list"))
        p = Product.objects.get(slug="new-p")

        edit_url = reverse("backoffice:product_edit", args=[p.id])
        res2 = self.client.post(edit_url, {
            "category": self.cat.id,
            "name": "New P edited",
            "slug": "new-p",
            "description": "dd",
            "price": "111.00",
            "is_active": "on",
        })
        self.assertRedirects(res2, reverse("backoffice:products_list"))
        p.refresh_from_db()
        self.assertEqual(p.name, "New P edited")
        self.assertEqual(p.price, 111)

        del_url = reverse("backoffice:product_delete", args=[p.id])
        self.assertEqual(self.client.get(del_url).status_code, 200)
        res3 = self.client.post(del_url)
        self.assertRedirects(res3, reverse("backoffice:products_list"))
        self.assertFalse(Product.objects.filter(id=p.id).exists())
