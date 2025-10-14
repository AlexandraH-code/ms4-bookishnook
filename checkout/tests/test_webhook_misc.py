import json
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

"""
Miscellaneous webhook behaviors: non-target event and unknown order id.
"""


@override_settings(STRIPE_WEBHOOK_SECRET="")
class WebhookMiscTests(TestCase):
    """
    Unrelated event types should be accepted with 200 and no side effects.
    """

    def test_non_checkout_event_is_ignored(self):
        """
        payment_intent.succeeded should be a noop for our webhook.
        """

        event = {
            "id": "evt_xxx",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_x"}},
        }
        res = self.client.post(
            reverse("checkout:webhook"),
            data=json.dumps(event),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)


@override_settings(STRIPE_WEBHOOK_SECRET="")
class WebhookUnknownOrderIdTests(TestCase):
    """
    Unknown order_id (no DB hit), return 200 without crashing.
    """

    @patch("checkout.views.stripe.checkout.Session.retrieve", return_value={"id": "cs_123"})
    def test_unknown_order_returns_200(self, _mock):
        """
        Webhook must be robust if the referenced order does not exist.
        """

        event = {
            "id": "evt_123",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_123", "metadata": {"order_id": "99999"}}},
        }
        res = self.client.post(
            reverse("checkout:webhook"),
            data=json.dumps(event),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
