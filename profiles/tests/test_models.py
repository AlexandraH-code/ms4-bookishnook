from django.test import TestCase
from django.contrib.auth import get_user_model
from profiles.models import Address

User = get_user_model()


class AddressDefaultTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pw", email="u@e.com")

    def test_only_one_default_per_kind(self):
        a1 = Address.objects.create(user=self.u, kind="shipping", line1="A", postal_code="1", city="C", country="SE", is_default=True)
        a2 = Address.objects.create(user=self.u, kind="shipping", line1="B", postal_code="2", city="C", country="SE", is_default=True)
        a1.refresh_from_db(); a2.refresh_from_db()
        self.assertTrue(a2.is_default)
        self.assertFalse(a1.is_default)
