from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class ExportCSVTests(TestCase):
    """
    Export of orders to CSV: only staff, correct headers and basic structure.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="u", password="p")
        self.staff = User.objects.create_user(username="s", password="p", is_staff=True)

    def test_non_staff_redirected(self):
        """
        No staff downloading CSV should get a 302 redirect.
        """

        self.client.login(username="u", password="p")
        res = self.client.get(reverse("backoffice:orders_export_csv"))
        self.assertEqual(res.status_code, 302)

    def test_staff_gets_csv_with_attachment_header(self):
        """
        Staff gets 200 + Content-Disposition: attachment and column headings in the first row.
        """

        self.client.login(username="s", password="p")
        res = self.client.get(reverse("backoffice:orders_export_csv"))
        self.assertEqual(res.status_code, 200)
        self.assertIn('attachment; filename="orders.csv"', res.get("Content-Disposition", ""))
        self.assertIn("id,email,status,total", res.content.decode("utf-8").splitlines()[0])
