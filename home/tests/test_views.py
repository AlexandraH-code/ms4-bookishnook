from django.test import TestCase
from django.urls import reverse
from django.core import mail

"""
AJAX subscribe flow and contact form rate limiting.
"""


class NewsletterTests(TestCase):
    """
    Covers newsletter AJAX subscription and contact form throttling.
    """

    def test_subscribe_flow(self):
        """
        AJAX subscribe should return requires_confirmation and send one email.
        """

        res = self.client.post(reverse("newsletter_subscribe"), {"email": "user@example.com"},
                               HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["requires_confirmation"])

        self.assertEqual(len(mail.outbox), 1)

    def test_contact_form_rate_limit(self):
        """
        6th POST to contact should be rate-limited and surface a friendly message.
        """

        url = reverse("contact")
        payload = {"name": "A", "email": "a@a.com", "message": "hi"}

        for _ in range(5):
            res = self.client.post(url, payload, follow=True)
            self.assertEqual(res.status_code, 200)

        res = self.client.post(url, payload, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Too many messages")
