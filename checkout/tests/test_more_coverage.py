import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.messages import get_messages
from products.models import Category, Product
from orders.models import Order

"""
Extra coverage for redirects, messages, success page, and email guard.
"""


class CheckoutExtraCoverageTests(TestCase):
    """
    Covers corner cases and UX paths not in the core flows.
    """

    def setUp(self):
        """
        Create a simple product for cart usage.
        """

        cat = Category.objects.create(name="Cat", slug="cat")
        self.p = Product.objects.create(category=cat, name="P1", slug="p1", price=100, stock=5)

    def test_create_session_get_redirects(self):
        """
        GET create_session should redirect start → cart (and finish with 200)
        """

        res = self.client.get(reverse("checkout:create_session"), follow=True)
        expected_chain = [
            (reverse("checkout:start"), 302),
            (reverse("cart:view"), 302),
        ]
        self.assertEqual(res.redirect_chain, expected_chain)
        self.assertEqual(res.status_code, 200)

    def test_create_session_empty_cart_redirects_with_message(self):
        """
        POST create_session with empty cart should redirect and flash a message.
        """

        res = self.client.post(reverse("checkout:create_session"))
        self.assertEqual(res.status_code, 302)

        res_follow = self.client.post(reverse("checkout:create_session"), follow=True)
        msgs = [m.message for m in get_messages(res_follow.wsgi_request)]
        self.assertTrue(any("Your cart is empty" in m for m in msgs))

    def test_success_without_session_param_renders_ok(self):
        """
        GET success without session_id should still render and clear session cart.
        """

        res = self.client.get(reverse("checkout:success"))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "checkout/success.html")


class WebhookEmailGuardTests(TestCase):
    """
    Ensure we don't send duplicate confirmation mails.
    """

    def setUp(self):
        """
        Create an already-confirmed paid order.
        """

        self.order = Order.objects.create(
            status="paid", email="x@example.com",
            total=100, grand_total=100, stripe_session_id="cs_abc"
        )

    @patch("orders.utils.send_order_confirmation")
    def test_no_email_if_already_confirmed(self, send_mail):
        """
        If confirmation_sent_at is set, webhook should not dispatch another email.
        """

        self.order.confirmation_sent_at = timezone.now()
        self.order.save(update_fields=["confirmation_sent_at"])

        event = {
            "id": "evt_1",
            "type": "checkout.session.completed",
            "data": {"object": {
                "id": "cs_abc",
                "metadata": {"order_id": str(self.order.id)},
                "customer_details": {"email": "x@example.com"}
            }},
        }

        with self.settings(STRIPE_WEBHOOK_SECRET=""):
            res = self.client.post(
                reverse("checkout:webhook"),
                data=json.dumps(event),
                content_type="application/json",
            )
        self.assertEqual(res.status_code, 200)
        send_mail.assert_not_called()
