from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from orders.models import Order

class BackofficeOrdersFiltersPaginationTests(TestCase):
    """Testing the list view's search/filter and pagination (20 per page)."""

    def setUp(self):
        # staff-användare
        self.staff = User.objects.create_user(username="s", password="p", is_staff=True)
        # 25 orders: 15 paid + 10 pending
        for i in range(15):
            Order.objects.create(status="paid", email=f"paid{i}@ex.com")
        for i in range(10):
            Order.objects.create(status="pending", email=f"pen{i}@ex.com")

    def test_filter_by_status(self):
        self.client.login(username="s", password="p")
        res = self.client.get(reverse("backoffice:orders_list"), {"status": "paid"})
        self.assertEqual(res.status_code, 200)
        # first page shows max 20 but we have 15 paid → all are visible
        self.assertEqual(len(res.context["orders"]), 15)

    def test_search_by_email(self):
        self.client.login(username="s", password="p")
        # Search for an exact email address we know exists
        target = "paid12@ex.com"
        res = self.client.get(reverse("backoffice:orders_list"), {"q": target})
        self.assertEqual(res.status_code, 200)
        orders = res.context["orders"]
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].email, target)

    def test_pagination_page1_has_20(self):
        self.client.login(username="s", password="p")
        res = self.client.get(reverse("backoffice:orders_list"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context["orders"]), 20)

    def test_pagination_page2_has_remaining(self):
        self.client.login(username="s", password="p")
        res = self.client.get(reverse("backoffice:orders_list"), {"page": 2})
        self.assertEqual(res.status_code, 200)
        # 25 total → page 1 (20) + page 2 (5)
        self.assertEqual(len(res.context["orders"]), 5)
