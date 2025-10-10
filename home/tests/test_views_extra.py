from django.test import TestCase
from django.urls import reverse
from home.models import NewsletterSubscriber


class HomeViewsExtraTests(TestCase):
    def test_home_page_loads(self):
        res = self.client.get(reverse("home"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Newsletter")

    def test_faq_page_loads(self):
        res = self.client.get(reverse("faq"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "FAQ")

    def test_subscribe_newsletter_creates_subscriber(self):
        url = reverse("newsletter_subscribe")
        res = self.client.post(url, {"email": "test@example.com"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(NewsletterSubscriber.objects.filter(email="test@example.com").exists())

    def test_about_page_loads(self):
        res = self.client.get(reverse("about"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "About")

