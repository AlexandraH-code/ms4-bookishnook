import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from products.models import Category, Product
from orders.models import Order, OrderItem

class WebhookInventoryIdempotentTests(TestCase):
    """The same event twice should not draw stock more than once and only send an email."""

    def setUp(self):
        c = Category.objects.create(name="C", slug="c")
        self.prod = Product.objects.create(category=c, name="P", slug="p", price=100, stock=5)
        self.order = Order.objects.create(status="pending", grand_total=100, email="buyer@example.com")
        OrderItem.objects.create(order=self.order, product=self.prod, name="P", unit_price=100, qty=2, subtotal=200)

        self.event = {
            "id": "evt_abc",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_abc",
                    "metadata": {"order_id": str(self.order.id)},
                    "customer_details": {"email": "buyer@example.com", "name": "Buyer",
                                         "address": {"line1":"L1","postal_code":"123","city":"C","country":"SE"}},
                    # minimi-PI för att din vy ska hitta email om den vill
                    "payment_intent": {"charges":{"data":[{"billing_details":{"email":"buyer@example.com"}}]}},
                }
            }
        }

    @patch("checkout.views.stripe.checkout.Session.retrieve", side_effect=Exception("skip external call"))
    def test_stock_deducted_once(self, _mock):
        with self.settings(STRIPE_WEBHOOK_SECRET=""):
            # first delivery
            res1 = self.client.post(reverse("checkout:webhook"),
                                    data=json.dumps(self.event),
                                    content_type="application/json")
            self.assertEqual(res1.status_code, 200)
            self.prod.refresh_from_db()
            self.order.refresh_from_db()
            self.assertEqual(self.order.status, "paid")
            self.assertEqual(self.prod.stock, 3)  # 5 - 2

            # repeat the same event-id → your code should protect via ProcessedStripeEvent
            res2 = self.client.post(reverse("checkout:webhook"),
                                    data=json.dumps(self.event),
                                    content_type="application/json")
            self.assertEqual(res2.status_code, 200)
            self.prod.refresh_from_db()
            self.assertEqual(self.prod.stock, 3)  # unchanged