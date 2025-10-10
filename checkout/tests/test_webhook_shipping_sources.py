import json
from django.test import TestCase
from django.urls import reverse
from orders.models import Order


class WebhookShippingSourcesTests(TestCase):
    def setUp(self):
        self.order = Order.objects.create(status="pending", grand_total=50)

    def test_shipping_from_collected_information_and_billing_from_charges(self):
        event = {
            "id": "evt_collected_1",
            "type": "checkout.session.completed",
            "data": {"object": {
                "id": "cs_x",
                "metadata": {"order_id": str(self.order.id)},
                "collected_information": {
                    "shipping_details": {
                        "name": "Ship Name",
                        "address": {"line1": "S1", "city": "SC", "postal_code": "123", "country": "SE"}
                    }
                },
                "customer_details": {"email": "u@example.com"},
                "payment_intent": {"charges": {"data": [{
                    "billing_details": {
                        "email": "u@example.com",
                        "name": "Bill Name",
                        "address": {"line1": "B1", "city": "BC", "postal_code": "456", "country": "SE"}
                    }
                }]}}
            }}
        }
        # Let the webhook accept unsigned in test
        with self.settings(STRIPE_WEBHOOK_SECRET=""):
            res = self.client.post(reverse("checkout:webhook"),
                                   data=json.dumps(event),
                                   content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.address_line1, "S1")
        self.assertEqual(self.order.billing_line1, "B1")
