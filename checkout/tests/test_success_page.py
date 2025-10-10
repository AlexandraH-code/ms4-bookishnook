from django.test import TestCase
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest


class CheckoutSuccessPageTests(TestCase):
    def _get_request_with_session(self):
        req = HttpRequest()
        mw = SessionMiddleware(lambda r: None)
        mw.process_request(req)
        req.session.save()
        return req

    def test_success_clears_cart_even_without_session_id(self):
        # No Stripe session_id → view should still clear the cart and render
        # (we simulate session via client, easier than HttpRequest hack)
        session = self.client.session
        session["cart"] = {"123": 2}
        session.save()

        res = self.client.get(reverse("checkout:success"))
        self.assertEqual(res.status_code, 200)

        session2 = self.client.session
        self.assertEqual(session2.get("cart", {}), {})

    def test_success_handles_bad_session_id_gracefully(self):
        # Invalid session_id → view should not crash
        res = self.client.get(reverse("checkout:success") + "?session_id=cs_bad")
        self.assertEqual(res.status_code, 200)
        # order in context can be None when we cannot retrieve
        self.assertIn("order", res.context)
