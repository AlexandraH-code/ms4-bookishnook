from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
# from django.contrib.messages import get_messages
from products.models import Category, Product
from orders.models import Order

User = get_user_model()
"""
Extra coverage for Backoffice views: order actions, product filters and form errors.
"""


class BackofficeExtraCoverageTests(TestCase):
    """
    Covers no-op order actions, product filtering/search, and invalid create form flow.
    """
   
    @classmethod
    def setUpTestData(cls):
        """
        Seed staff user, one category/product, and a pending order.
        """

        cls.staff = User.objects.create_user(username="s", password="x", is_staff=True)
        cls.cat = Category.objects.create(name="Cat", slug="cat")
        cls.prod = Product.objects.create(category=cls.cat, name="P1", slug="p1", price=100, stock=10)
        cls.order = Order.objects.create(email="a@b.com", status="pending", total=100, grand_total=100)

    def setUp(self):
        """
        Log in staff before each test.
        """
      
        self.client.login(username="s", password="x")

    def test_order_detail_ignores_unknown_action(self):
        """
        Posting an unknown action keeps the order unchanged and re-renders the page.
        """
      
        url = reverse("backoffice:order_detail", args=[self.order.id])
        res = self.client.post(url, {"action": "mark_whatever"})
        # Will render the page without redirect (no change)
        self.assertEqual(res.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_products_list_active_zero_and_search(self):
        """
        active=0 shows only inactive products; search matches name/slug/description.
        """
       
        Product.objects.create(category=self.cat, name="Inactive", slug="inactive", price=50, stock=1, is_active=False)
        url = reverse("backoffice:products_list")
        # active=0 should only show inactive
        res = self.client.get(url, {"active": "0"})
        self.assertContains(res, "Inactive")
        self.assertNotContains(res, "P1")

        # Search should match description/name/slug (here the name)
        res2 = self.client.get(url, {"q": "P1"})
        self.assertContains(res2, "P1")

    def test_product_create_invalid_shows_errors(self):
        """
        Invalid create POST re-renders the form and shows field error messages.
        """
        
        # Missing required fields -> form invalid, page rerendered
        url = reverse("backoffice:product_create")
        res = self.client.post(url, {
            # missing required fields (category/price/name)
            "name": "",
            "price": "",
        })
        self.assertEqual(res.status_code, 200)
        # Field names in error messages are enough to ensure we stayed on the form page
        self.assertContains(res, "This field is required")
