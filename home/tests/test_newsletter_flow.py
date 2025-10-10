from django.test import TestCase
from django.urls import reverse
from home.models import NewsletterSubscriber


class NewsletterFlowTests(TestCase):
    def test_confirm_and_unsubscribe(self):
        sub = NewsletterSubscriber.objects.create(email="x@example.com", confirm_token="CT", unsubscribe_token="UT")
        # confirm
        res = self.client.get(reverse("newsletter_confirm", args=["CT"]))
        self.assertEqual(res.status_code, 200)
        sub.refresh_from_db()
        self.assertTrue(sub.confirmed)
        # unsubscribe
        res = self.client.get(reverse("newsletter_unsubscribe", args=["UT"]))
        self.assertEqual(res.status_code, 200)
        sub.refresh_from_db()
        self.assertTrue(sub.unsubscribed)
        self.assertFalse(sub.confirmed)
