from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class BackofficeAuthTests(TestCase):
    """
    Auth/authorization to back office: only staff should get 200 on dashboard.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="u", password="p")
        self.staff = User.objects.create_user(username="s", password="p", is_staff=True)

    def test_dashboard_requires_staff(self):
        """
        Anon → 302, not logged in staff → 302, staff → 200.
        """
        
        # Anonymous user → redirect (302) to login
        res = self.client.get(reverse("backoffice:dashboard"))
        self.assertEqual(res.status_code, 302)

        # Logged in but not staff → still redirect (302)
        self.client.login(username="u", password="p")
        res = self.client.get(reverse("backoffice:dashboard"))
        self.assertEqual(res.status_code, 302)

        # Staff → 200 OK
        self.client.login(username="s", password="p")
        res = self.client.get(reverse("backoffice:dashboard"))
        self.assertEqual(res.status_code, 200)
