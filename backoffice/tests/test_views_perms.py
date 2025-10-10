from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from orders.models import Order


User = get_user_model()


class BackofficePermTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="staff", email="s@example.com", password="x", is_staff=True)
        self.user = User.objects.create_user(username="u", email="u@example.com", password="x")
        Order.objects.create(status="pending", grand_total=10)
        Order.objects.create(status="paid", grand_total=20)

    def test_non_staff_redirected(self):
        self.client.login(username="u", password="x")
        for name in ["backoffice:dashboard", "backoffice:orders_list", "backoffice:products_list"]:
            res = self.client.get(reverse(name))
            self.assertIn(res.status_code, (302, 301))

    def test_staff_can_access(self):
        self.client.login(username="staff", password="x")
        res = self.client.get(reverse("backoffice:dashboard"))
        self.assertEqual(res.status_code, 200)

        res = self.client.get(reverse("backoffice:orders_list"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "pending")
        self.assertContains(res, "paid")
