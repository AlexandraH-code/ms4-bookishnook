from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from orders.models import Order

"""
Access control: users may only view their own orders in profile pages.
"""


class ProfileOrderAccessTests(TestCase):
    """A user is only allowed to see orders with the same email as their account."""

    def setUp(self):
        """
        Two users; one order belongs to u1's email address.
        """

        self.u1 = User.objects.create_user(username="u1", password="p", email="a@ex.com")
        self.u2 = User.objects.create_user(username="u2", password="p", email="b@ex.com")
        self.o1 = Order.objects.create(email="a@ex.com", status="paid", grand_total=10)

    def test_cannot_view_others_order(self):
        """
        A different user should get 404 on another user's order detail.
        """

        self.client.login(username="u2", password="p")
        res = self.client.get(reverse("profiles:order_detail", args=[self.o1.id]))
        self.assertEqual(res.status_code, 404)

    def test_owner_can_view(self):
        """
        Owner should see their own order detail.
        """

        self.client.login(username="u1", password="p")
        res = self.client.get(reverse("profiles:order_detail", args=[self.o1.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, f"Order #{self.o1.id}")
