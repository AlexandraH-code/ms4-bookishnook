import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from products.models import Category, Product
from orders.models import Order


class CheckoutExtraCoverageTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Cat", slug="cat")
        self.p = Product.objects.create(category=cat, name="P1", slug="p1", price=100, stock=5)

    def test_create_session_get_redirects(self):
        """
        GET to create_session -> redirect to checkout:start,
        which in turn (with empty cart) redirects to cart:view.
        We follow the entire redirect chain and verify the end.
        """
        res = self.client.get(reverse("checkout:create_session"), follow=True)
        # Check the redirect chain (2 hops)
        expected_chain = [
            (reverse("checkout:start"), 302),
            (reverse("cart:view"), 302),
        ]
        self.assertEqual(res.redirect_chain, expected_chain)
        self.assertEqual(res.status_code, 200)

    def test_create_session_empty_cart_redirects_with_message(self):
        res = self.client.post(reverse("checkout:create_session"))
        # the first jump can be to checkout:start → which then jumps to cart:view
        # we only care that POST with empty cart not 200s here
        self.assertEqual(res.status_code, 302)

        # follow the chain and check message on the final destination
        res_follow = self.client.post(reverse("checkout:create_session"), follow=True)
        msgs = [m.message for m in get_messages(res_follow.wsgi_request)]
        self.assertTrue(any("Your cart is empty" in m for m in msgs))

    def test_success_without_session_param_renders_ok(self):
        """
       /checkout/success/ without session_id should still render a page (200).
        We test status + that the correct template is used, instead of text content.
        """
        res = self.client.get(reverse("checkout:success"))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "checkout/success.html")


class WebhookEmailGuardTests(TestCase):
    """Cover the per-order idempotence: if confirmation_sent_at is set, no email should be sent."""
    def setUp(self):
        self.order = Order.objects.create(
            status="paid", email="x@example.com",
            total=100, grand_total=100, stripe_session_id="cs_abc"
        )

    @patch("orders.utils.send_order_confirmation")
    def test_no_email_if_already_confirmed(self, send_mail):
        from django.utils import timezone
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
