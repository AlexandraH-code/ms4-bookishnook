from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class ExportCSVTests(TestCase):
    """
    The CSV export should be staff-protected and respond with attachment header.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="u", password="p")
        self.staff = User.objects.create_user(username="s", password="p", is_staff=True)

    def test_non_staff_redirected(self):
        self.client.login(username="u", password="p")
        res = self.client.get(reverse("backoffice:orders_export_csv"))
        self.assertEqual(res.status_code, 302)

    def test_staff_gets_csv_with_attachment_header(self):
        self.client.login(username="s", password="p")
        res = self.client.get(reverse("backoffice:orders_export_csv"))
        self.assertEqual(res.status_code, 200)
        self.assertIn('attachment; filename="orders.csv"', res.get("Content-Disposition", ""))
        # small sanity: first line should contain column names
        self.assertIn("id,email,status,total", res.content.decode("utf-8").splitlines()[0])
