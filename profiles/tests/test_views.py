from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from profiles.models import Profile  # byt importväg om annorlunda

User = get_user_model()


class ProfileViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="u@example.com", password="pass12345")
        # Om du har signal som skapar Profile automatiskt, räcker detta:
        # Annars: Profile.objects.create(user=cls.user)
        cls.dashboard_url = reverse("profiles:dashboard")
        cls.edit_url = reverse("profiles:edit")  # byt till din url-name

    def test_dashboard_requires_login(self):
        resp = self.client.get(self.dashboard_url)
        login_url = reverse("account_login")
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith(f"{login_url}?next="))

    def test_dashboard_when_logged_in(self):
        self.client.login(email="u@example.com", password="pass12345")
        resp = self.client.get(self.dashboard_url)
        self.assertEqual(resp.status_code, 200)
        # self.assertTemplateUsed(resp, "profiles/dashboard.html")
        self.assertIn("orders", resp.context)  # om du visar orderhistorik

    def test_update_profile_post(self):
        self.client.login(email="u@example.com", password="pass12345")
        payload = {
            "first_name": "Alex",
            "last_name": "Andersson",
            "phone": "0701234567",
            "shipping_address1": "Street 1",
            "shipping_city": "City",
            "shipping_zip": "11111",
            "shipping_country": "SE",
            # Lägg fler fält som din form kräver
        }
        resp = self.client.post(self.edit_url, data=payload, follow=True)
        self.assertEqual(resp.status_code, 200)
        prof = Profile.objects.get(user=self.user)
        self.assertEqual(prof.first_name, "Alex")
        self.assertEqual(prof.shipping_city, "City")
