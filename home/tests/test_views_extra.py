from django.test import TestCase
from django.urls import reverse
from home.models import NewsletterSubscriber

"""
Simple smoke tests for static pages and newsletter subscription view.
"""


class HomeViewsExtraTests(TestCase):
    """
    Basic rendering and minimal behavior checks.
    """

    def test_home_page_loads(self):
        """
        Home page should render and expose newsletter section.
        """

        res = self.client.get(reverse("home"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Newsletter")

    def test_faq_page_loads(self):
        """
        FAQ page should render and contain 'FAQ' text.
        """

        res = self.client.get(reverse("faq"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "FAQ")

    def test_subscribe_newsletter_creates_subscriber(self):
        """
        POST to subscribe endpoint should create a NewsletterSubscriber.
        """

        url = reverse("newsletter_subscribe")
        res = self.client.post(url, {"email": "test@example.com"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(NewsletterSubscriber.objects.filter(email="test@example.com").exists())

    def test_about_page_loads(self):
        """
        About page should render and contain 'About' text.
        """

        res = self.client.get(reverse("about"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "About")
