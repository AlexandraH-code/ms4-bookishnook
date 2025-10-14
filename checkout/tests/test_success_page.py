from django.test import TestCase
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest

"""
Success page behavior after (or without) Stripe session.
"""


class CheckoutSuccessPageTests(TestCase):
    """
    Ensure success view is robust with/without session params and clears cart.
    """

    def _get_request_with_session(self):
        """
        Helper to create a raw HttpRequest with session (unused in current tests).
        """

        req = HttpRequest()
        mw = SessionMiddleware(lambda r: None)
        mw.process_request(req)
        req.session.save()
        return req

    def test_success_clears_cart_even_without_session_id(self):
        """
        No session_id → view still renders and empties the cart.
        """

        session = self.client.session
        session["cart"] = {"123": 2}
        session.save()

        res = self.client.get(reverse("checkout:success"))
        self.assertEqual(res.status_code, 200)

        session2 = self.client.session
        self.assertEqual(session2.get("cart", {}), {})

    def test_success_handles_bad_session_id_gracefully(self):
        """
        Invalid session_id must not crash; template still renders.
        """

        res = self.client.get(reverse("checkout:success") + "?session_id=cs_bad")
        self.assertEqual(res.status_code, 200)
        self.assertIn("order", res.context)
