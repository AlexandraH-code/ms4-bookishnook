from django.test import TestCase
from django.urls import reverse
from django.core import mail


class NewsletterTests(TestCase):
    def test_subscribe_flow(self):
        res = self.client.post(reverse("newsletter_subscribe"), {"email": "user@example.com"},
                               HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["requires_confirmation"])
        # an email is sent
        self.assertEqual(len(mail.outbox), 1)

    def test_contact_form_rate_limit(self):
        url = reverse("contact")
        payload = {"name": "A", "email": "a@a.com", "message": "hi"}

        # 5 attempts allowed
        for _ in range(5):
            res = self.client.post(url, payload, follow=True)
            self.assertEqual(res.status_code, 200)

        # 6th -> rate limited + redirect back to contact
        res = self.client.post(url, payload, follow=True)  # <— follow redirect
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Too many messages")
