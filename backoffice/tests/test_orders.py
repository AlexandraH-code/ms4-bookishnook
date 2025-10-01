from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from orders.models import Order
from decimal import Decimal

User = get_user_model()


class BackofficeOrdersTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(email="staff@example.com", password="pass12345", is_staff=True)
        cls.o = Order.objects.create(
            email="buyer@example.com",
            subtotal=Decimal("100.00"),
            tax_amount=Decimal("25.00"),
            shipping_amount=Decimal("0.00"),
            grand_total=Decimal("125.00"),
            status="paid",
        )
        cls.list_url = reverse("backoffice:orders_list")
        cls.det_url = reverse("backoffice:order_detail", args=[cls.o.id])

    def setUp(self):
        self.client.login(email="staff@example.com", password="pass12345")

    def test_orders_list(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "buyer@example.com")

    def test_order_detail(self):
        resp = self.client.get(self.det_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "#{}".format(self.o.id))
