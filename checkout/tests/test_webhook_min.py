import json
from django.test import TestCase, override_settings
from django.urls import reverse
from orders.models import Order

"""
Minimal happy-path webhook smoke test.
"""


class WebhookSmokeTests(TestCase):
    """
    Ensure the leanest payload flips a pending order to paid and captures email.
    """

    def setUp(self):
        """
        Create a basic pending order.
        """

        self.order = Order.objects.create(status="pending", grand_total=100)

    @override_settings(STRIPE_WEBHOOK_SECRET="", DEBUG=True)
    def test_checkout_session_completed_minimal(self):
        """
        Unsigned payload in DEBUG with minimal structure should pass.
        """

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
                        "address": {"line1": "L1", "postal_code": "123", "city": "C", "country": "SE"},
                    },

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
