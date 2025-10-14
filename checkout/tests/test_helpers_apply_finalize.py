from django.test import TestCase
from unittest.mock import patch
from orders.models import Order, OrderItem
from products.models import Category, Product
from checkout import views as v

"""
Unit-like tests for helper functions that parse/apply data and finalize orders.
"""


class CheckoutHelpersTests(TestCase):
    """
    Validate address extraction, application to Order, and finalize logic.
    """

    def setUp(self):
        """
        Create a pending order and a product with limited stock.
        """

        self.order = Order.objects.create(status="pending", total=0, grand_total=0, email=None)
        cat = Category.objects.create(name="C", slug="c")
        self.p = Product.objects.create(category=cat, name="P", slug="p", price=100, stock=2)

    def test_extract_best_contact_prefers_shipping_and_billing_sources(self):
        """
        _extract_best_contact should prioritize shipping/billing fields correctly.
        """

        sess = {
            "customer_details": {"email": "cust@example.com", "name": "Cust", "address": {"line1": "B1", "city":"BC","postal_code":"111","country":"SE"}},
            "shipping_details": {"name": "Ship Name", "phone": "0700", "address": {"line1":"S1","city":"SC","postal_code":"222","country":"SE"}},
            "payment_intent": {"charges":{"data":[{"billing_details":{"email":"bill@example.com","name":"Bill","phone":"0701","address":{"line1":"B2","city":"BC2","postal_code":"333","country":"SE"}}}]}},
        }
        data = v._extract_best_contact(sess)
        self.assertEqual(data["email"], "cust@example.com")
        self.assertEqual(data["address_line1"], "S1")
        self.assertEqual(data["billing_line1"], "B1")
        self.assertEqual(data["full_name"], "Ship Name")
        self.assertEqual(data["phone"], "0700")

    def test_apply_addresses_sets_only_provided_fields(self):
        """
        _apply_addresses should only set non-empty values (leave None/empty untouched).
        """

        v._apply_addresses(self.order, {"email":"x@example.com", "full_name":"X", "address_line1":"S1"})
        self.order.refresh_from_db()
        self.assertEqual(self.order.email, "x@example.com")
        self.assertEqual(self.order.full_name, "X")
        self.assertEqual(self.order.address_line1, "S1")
        self.assertIsNone(self.order.address_line2)

    @patch("checkout.views.send_order_confirmation")
    def test_finalize_paid_marks_paid_and_deducts_stock_and_sends_email(self, mock_send):
        """
        _finalize_paid: set paid status, decrement stock, deactivate zero-stock, and send email.
        """

        OrderItem.objects.create(order=self.order, product=self.p, name=self.p.name, unit_price=self.p.price, qty=2, subtotal=200)
        v._finalize_paid(self.order)
        self.order.refresh_from_db()
        self.p.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(self.p.stock, 0)
        self.assertFalse(self.p.is_active)
        mock_send.assert_called_once()
