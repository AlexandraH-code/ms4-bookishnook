import json
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from unittest.mock import patch
from orders.models import Order

"""
Idempotency: same event twice should not duplicate emails/stock changes.
"""


@override_settings(STRIPE_WEBHOOK_SECRET="")
class WebhookIdempotencyTests(TestCase):
    """
    Posting the same JSON twice should be a no-op on the second call.
    """

    def setUp(self):
        """
        Create a minimal pending order to be flipped to paid.
        """

        self.order = Order.objects.create(status="pending", grand_total=123)

    def _event_payload(self):
        """
        Return a realistic checkout.session.completed payload with inline PI dict.
        """

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
        """
        Two identical posts → 200 both times; only one email and order paid once.
        """

        url = reverse("checkout:webhook")
        payload = json.dumps(self._event_payload())

        res1 = self.client.post(url, data=payload, content_type="application/json")
        res2 = self.client.post(url, data=payload, content_type="application/json")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self.assertEqual(self.order.email, "buyer@example.com")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("order", mail.outbox[0].subject.lower())
