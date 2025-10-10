from django.test import TestCase, override_settings
from django.urls import reverse
import json
from orders.models import Order

class WebhookSmokeTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(status="pending", grand_total=100)

    @override_settings(STRIPE_WEBHOOK_SECRET="", DEBUG=True)
    def test_checkout_session_completed_minimal(self):
        event = {
            "id": "evt_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_123",
                    "metadata": {"order_id": str(self.order.id)},
                    "customer_details": {
                        "email": "x@example.com",
                        "name": "X",
                        "address": {"line1": "L1","postal_code":"123","city":"C","country":"SE"},
                    },
                    # put minimal charge billing email here for fallback:
                    "payment_intent": {"charges": {"data": [{"billing_details": {"email": "x@example.com"}}]}},
                }
            }
        }
        res = self.client.post(
            reverse("checkout:webhook"),
            data=json.dumps(event),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(self.order.email, "x@example.com")
