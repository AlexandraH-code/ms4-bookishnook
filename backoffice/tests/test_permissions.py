from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class BackofficePermissionsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@example.com", password="pass12345")
        self.staff = User.objects.create_user(email="s@example.com", password="pass12345", is_staff=True)
        self.home_url = reverse("backoffice:home")

    def test_requires_staff(self):
        resp = self.client.get(self.home_url)
        login_url = reverse("account_login")
        self.assertEqual(resp.status_code, 302)
        self.assertIn(login_url, resp.url)

        self.client.login(email="u@example.com", password="pass12345")
        resp2 = self.client.get(self.home_url)
        # beroende på din guard: 403 eller redirect
        self.assertIn(resp2.status_code, (302, 403))

        self.client.login(email="s@example.com", password="pass12345")
        resp3 = self.client.get(self.home_url)
        self.assertEqual(resp3.status_code, 200)
