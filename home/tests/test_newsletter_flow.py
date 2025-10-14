from django.test import TestCase
from django.urls import reverse
from home.models import NewsletterSubscriber

"""
End-to-end newsletter confirm/unsubscribe flow.
"""


class NewsletterFlowTests(TestCase):
    """
    Confirming a subscriber and then unsubscribing should flip the flags accordingly.
    """

    def test_confirm_and_unsubscribe(self):
        """
        Confirm sets confirmed=True; unsubscribe sets unsubscribed=True and confirmed=False.
        """

        sub = NewsletterSubscriber.objects.create(email="x@example.com", confirm_token="CT", unsubscribe_token="UT")
        res = self.client.get(reverse("newsletter_confirm", args=["CT"]))
        self.assertEqual(res.status_code, 200)
        sub.refresh_from_db()
        self.assertTrue(sub.confirmed)

        res = self.client.get(reverse("newsletter_unsubscribe", args=["UT"]))
        self.assertEqual(res.status_code, 200)
        sub.refresh_from_db()
        self.assertTrue(sub.unsubscribed)
        self.assertFalse(sub.confirmed)
