from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class BackofficeCSVHeaderTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(username="s", password="x", is_staff=True)

    def test_csv_has_bom_and_headers(self):
        self.client.login(username="s", password="x")
        res = self.client.get(reverse("backoffice:orders_export_csv"))
        self.assertEqual(res.status_code, 200)
        self.assertIn('attachment; filename="orders.csv"', res["Content-Disposition"])

        raw = res.content
        # 1) BOM exists
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))

        # 2) Remove BOM when decoding and check the first line
        text = raw.decode("utf-8-sig")
        lines = text.splitlines()
        self.assertGreaterEqual(len(lines), 1)
        header = lines[0]
        self.assertEqual(
            header,
            "id,email,status,total,tax,shipping,grand_total,created",
        )
