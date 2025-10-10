import json
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from unittest.mock import patch
from orders.models import Order


@override_settings(STRIPE_WEBHOOK_SECRET="")  # let the webhook take unsigned events in test
class WebhookIdempotencyTests(TestCase):
    def setUp(self):
        # Minimal pending-order
        self.order = Order.objects.create(status="pending", grand_total=123)

    def _event_payload(self):
        """Minimum payload that your webhook code can handle, without it needing to call the Stripe API (pi is dict, not str)."""
        return {
            "id": "evt_test_123",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "metadata": {"order_id": str(self.order.id)},
                    "customer_details": {
                        "email": "buyer@example.com",
                        "name": "Buyer Name",
                        "address": {"line1": "Road 1", "postal_code": "111 22", "city": "Town", "country": "SE"},
                        "phone": "+46123456",
                    },
                    # Make payment_intent a DICT so the code doesn't try to retrieve from Stripe
                    "payment_intent": {
                        "charges": {
                            "data": [
                                {
                                    "billing_details": {
                                        "email": "buyer@example.com",
                                        "name": "Buyer Name",
                                        "phone": "+46123456",
                                        "address": {"line1": "Bill 1", "postal_code": "333 44", "city": "Billtown", "country": "SE"},
                                    }
                                }
                            ]
                        }
                    },
                    # If your code looks here sometimes:
                    "collected_information": {
                        "shipping_details": {
                            "name": "Buyer Name",
                            "address": {"line1": "Ship 1", "postal_code": "222 33", "city": "Shipville", "country": "SE"},
                        }
                    },
                }
            },
        }

    @patch("stripe.checkout.Session.retrieve", side_effect=Exception("skip external call"))
    def test_event_processed_once_and_single_email(self, _mock_sess_retrieve):
        url = reverse("checkout:webhook")
        payload = json.dumps(self._event_payload())

        # Post the SAME event twice – only give ONE email
        res1 = self.client.post(url, data=payload, content_type="application/json")
        res2 = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(self.order.email, "buyer@example.com")

        # Exactly one dispatch (the webhook is idempotent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("order", mail.outbox[0].subject.lower())
