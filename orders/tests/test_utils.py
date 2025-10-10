from django.test import TestCase, override_settings
from django.core import mail
from products.models import Category, Product
from orders.models import Order, OrderItem
from orders.utils import send_order_confirmation


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class OrderEmailTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Cat", slug="cat")
        self.prod = Product.objects.create(category=cat, name="P", price=123, slug="p")
        self.order = Order.objects.create(email="cust@example.com", status="paid", grand_total=123)
        OrderItem.objects.create(order=self.order, product=self.prod, name="P", unit_price=123, qty=1, subtotal=123)

    def test_send_order_confirmation(self):
        ok = send_order_confirmation(self.order, customer_email=self.order.email, customer_name="Cust")
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 1)
        subject = mail.outbox[0].subject
        # check case-insensitive + that order-id is included
        self.assertIn("order", subject.lower())
        self.assertIn(f"#{Order.objects.first().id}", subject)
