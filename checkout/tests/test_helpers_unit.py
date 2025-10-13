from django.test import TestCase
from django.core import mail
from orders.models import Order, OrderItem
from products.models import Category, Product
from checkout.views import _apply_addresses, _finalize_paid


class ApplyAddressesUnitTests(TestCase):
    def test_only_non_empty_values_are_saved(self):
        """
        _apply_addresses only sets non-empty fields.
        """
        
        o = Order.objects.create(status="pending", grand_total=0)
        data = {
            "email": "a@b.com",
            "full_name": "",
            "phone": None,
            "address_line1": "L1",
            "address_line2": "",
            "postal_code": "123",
            "city": "X",
            "country": "SE",
            "billing_name": None,
            "billing_line1": "BL1",
            "billing_line2": "",
            "billing_postal": "999",
            "billing_city": "BC",
            "billing_country": "SE",
        }
        _apply_addresses(o, data)
        o.refresh_from_db()
        self.assertEqual(o.email, "a@b.com")
        self.assertEqual(o.address_line1, "L1")
        self.assertEqual(o.address_line2, None)  # left untouched
        self.assertEqual(o.billing_line1, "BL1")
        self.assertEqual(o.full_name, None)


class FinalizePaidUnitTests(TestCase):
    """
    _finalize_paid is idempotent and pulls layers once.
    """
    
    def setUp(self):
        cat = Category.objects.create(name="C", slug="c")
        self.p = Product.objects.create(category=cat, name="P", price=100, stock=5, slug="p")
        self.o = Order.objects.create(status="pending", grand_total=100, email="x@y.z")
        OrderItem.objects.create(order=self.o, product=self.p, name="P", unit_price=100, qty=2, subtotal=200)

    def test_finalize_paid_is_idempotent(self):
        _finalize_paid(self.o)
        self.o.refresh_from_db(); self.p.refresh_from_db()
        self.assertEqual(self.o.status, "paid")
        self.assertEqual(self.p.stock, 3)  # 5 - 2

        # Run again → no more stock deductions, but no crashes
        prev_outbox = len(mail.outbox)
        _finalize_paid(self.o)
        self.o.refresh_from_db(); self.p.refresh_from_db()
        self.assertEqual(self.p.stock, 3)
        self.assertEqual(len(mail.outbox), prev_outbox)  # no extra emails in our implementation
