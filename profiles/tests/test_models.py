from django.test import TestCase
from django.contrib.auth import get_user_model
from profiles.models import Address

"""
Duplicate of default-address constraint with slightly different data.
"""

User = get_user_model()


class AddressDefaultTests(TestCase):
    """
    Re-check default toggling for shipping addresses.
    """

    def setUp(self):
        """
        User for the address instances.
        """

        self.u = User.objects.create_user(username="u", password="pw", email="u@e.com")

    def test_only_one_default_per_kind(self):
        """
        Newest default=True should win; previous default should be unset.
        """

        a1 = Address.objects.create(user=self.u, kind="shipping", line1="A", postal_code="1", city="C", country="SE", is_default=True)
        a2 = Address.objects.create(user=self.u, kind="shipping", line1="B", postal_code="2", city="C", country="SE", is_default=True)
        a1.refresh_from_db(); a2.refresh_from_db()
        self.assertTrue(a2.is_default)
        self.assertFalse(a1.is_default)
