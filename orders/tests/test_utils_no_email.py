from django.test import TestCase
from orders.models import Order
from orders.utils import send_order_confirmation

"""
Unit test: order confirmation helper returns False when no email is available.
"""


class OrderEmailNoEmailTests(TestCase):
    """
    send_order_confirmation should short-circuit if no recipient email exists.
    """

    def test_no_email_returns_false(self):
        """
        Helper should return False when customer_email is None.
        """

        o = Order.objects.create(status="pending", grand_total=100)
        ok = send_order_confirmation(o, customer_email=None, customer_name="X")
        self.assertFalse(ok)
