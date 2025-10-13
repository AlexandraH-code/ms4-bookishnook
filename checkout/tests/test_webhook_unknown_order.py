import json
from django.test import TestCase
from django.urls import reverse


class WebhookUnknownOrderTests(TestCase):
    """
    If the webhook receives an unknown order_id, nothing should happen but 200 will be returned.
    """

    def test_unknown_order_id(self):
        event = {
            "id": "evt_x",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_x", "metadata": {"order_id": "999999"}}},
        }
        # Our view accepts unsigned in DEBUG/with empty secret
        with self.settings(STRIPE_WEBHOOK_SECRET=""):
            res = self.client.post(
                reverse("checkout:webhook"),
                data=json.dumps(event),
                content_type="application/json",
            )
        self.assertEqual(res.status_code, 200)
