from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from profiles.models import Address


User = get_user_model()


class ProfileViewsAuthAndCrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", email="u1@example.com", password="pass12345")

    def test_login_required_pages(self):
        # Alla ska kräva login
        need_login = [
            reverse("profiles:dashboard"),
            reverse("profiles:edit"),
            reverse("profiles:addresses"),
        ]
        for url in need_login:
            res = self.client.get(url)
            self.assertIn(res.status_code, (302, 301))  # redirect till login

        self.client.login(username="u1", password="pass12345")
        for url in need_login:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200)

    def test_address_crud(self):
        self.client.login(username="u1", password="pass12345")

        # Create
        res = self.client.post(
            reverse("profiles:address_create"),
            data={
                "kind": "shipping",
                "full_name": "Anna Test",
                "phone": "070-123",
                "line1": "Gatan 1",
                "line2": "",
                "postal_code": "123 45",
                "city": "Stad",
                "country": "SE",
                "is_default": True,
            },
            follow=True,
        )
        self.assertEqual(res.status_code, 200)
        addr = Address.objects.get(user=self.user, line1="Gatan 1")
        self.assertTrue(addr.is_default)

        # Edit
        res = self.client.post(
            reverse("profiles:address_edit", args=[addr.pk]),
            data={
                "kind": "shipping",
                "full_name": "Anna Uppd",
                "phone": "070-999",
                "line1": "Gatan 1",
                "line2": "",
                "postal_code": "123 45",
                "city": "Stad",
                "country": "SE",
                "is_default": True,
            },
            follow=True,
        )
        self.assertEqual(res.status_code, 200)
        addr.refresh_from_db()
        self.assertEqual(addr.full_name, "Anna Uppd")

        # Delete
        res = self.client.post(reverse("profiles:address_delete", args=[addr.pk]), follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(Address.objects.filter(pk=addr.pk).exists())
