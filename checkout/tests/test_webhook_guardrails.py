from django.test import TestCase, override_settings
from django.urls import reverse
from orders.models import Order
from unittest.mock import patch
import stripe
import json

"""
Guardrails for Stripe webhook: signatures, event types, and debug network calls.
"""


class WebhookGuardrailTests(TestCase):
    """
    Verify signature errors become 400 and debug path avoids network calls.
    """

    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_dummy")
    @patch("stripe.Webhook.construct_event")
    def test_bad_signature_returns_400(self, mock_construct):
        """
        If Stripe signature verification fails, return 400.
        """

        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            "bad", http_body="", sig_header=None
        )
        res = self.client.post(
            reverse("checkout:webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="whatever",
        )
        self.assertEqual(res.status_code, 400)


class WebhookOtherEventTests(TestCase):
    """
    Non-target event types should be treated as no-ops.
    """

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_non_checkout_event_is_noop(self):
        """
        Webhook returns 200 with no side effects for unrelated event types.
        """

        event = {"type": "payment_intent.succeeded", "data": {"object": {}}}
        res = self.client.post(
            reverse("checkout:webhook"),
            data=json.dumps(event),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)


class WebhookDebugPathTests(TestCase):
    """
    In DEBUG (and empty secret), we should not hit Stripe network APIs.
    """

    @override_settings(DEBUG=True, STRIPE_WEBHOOK_SECRET="")
    @patch("stripe.checkout.Session.retrieve")
    def test_debug_uses_raw_payload_no_network_calls(self, mock_retrieve):
        """
        Webhook should rely on raw payload only in debug path.
        """

        o = Order.objects.create(status="pending", grand_total=100)
        event = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_x", "metadata": {"order_id": str(o.id)}}},
        }
        res = self.client.post(
            reverse("checkout:webhook"),
            data=json.dumps(event),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        o.refresh_from_db()
        self.assertEqual(o.status, "paid")
        mock_retrieve.assert_not_called()
