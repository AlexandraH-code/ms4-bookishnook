from django.test import TestCase
from orders.models import Order
from orders.utils import send_order_confirmation


class OrderEmailNoEmailTests(TestCase):
    def test_no_email_returns_false(self):
        o = Order.objects.create(status="pending", grand_total=100)
        ok = send_order_confirmation(o, customer_email=None, customer_name="X")
        self.assertFalse(ok)
