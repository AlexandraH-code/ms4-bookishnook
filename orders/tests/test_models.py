from django.test import TestCase
from decimal import Decimal
from django.contrib.auth import get_user_model
from products.models import Category, Product
from orders.models import Order, OrderItem

User = get_user_model()


class OrderModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="buyer@example.com", password="pass12345")
        cls.cat = Category.objects.create(name="Bookmarks", slug="bookmarks", is_active=True)
        cls.p1 = Product.objects.create(
            name="Leather Bookmark", slug="leather-bookmark", price=Decimal("49.00"),
            category=cls.cat, is_active=True
        )
        cls.p2 = Product.objects.create(
            name="Metal Bookmark", slug="metal-bookmark", price=Decimal("79.00"),
            category=cls.cat, is_active=True
        )
        cls.order = Order.objects.create(
            user=cls.user,
            email="buyer@example.com",
            subtotal=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            shipping_amount=Decimal("0.00"),
            grand_total=Decimal("0.00"),
            status="pending",
        )
        cls.item1 = OrderItem.objects.create(
            order=cls.order, product=cls.p1, quantity=2, price_each=cls.p1.price
        )
        cls.item2 = OrderItem.objects.create(
            order=cls.order, product=cls.p2, quantity=1, price_each=cls.p2.price
        )

    def test_orderitem_line_total(self):
        # Förutsätter att du beräknar line_total som quantity * price_each (i save() eller property)
        expected1 = Decimal("98.00")  # 2 * 49
        expected2 = Decimal("79.00")  # 1 * 79
        # Om line_total är fält:
        self.assertEqual(self.item1.line_total, expected1)
        self.assertEqual(self.item2.line_total, expected2)
        # Om line_total är property istället:
        # self.assertEqual(self.item1.line_total, expected1)
        # self.assertEqual(self.item2.line_total, expected2)

    def test_order_totals(self):
        # Simulera totals-beräkning (ersätt med din egen metod om du har t.ex. order.recalculate())
        subtotal = self.item1.line_total + self.item2.line_total
        tax = (subtotal * Decimal("0.25")).quantize(Decimal("0.01"))  # ex moms 25% (justera efter din logik)
        shipping = Decimal("0.00")

        self.order.subtotal = subtotal
        self.order.tax_amount = tax
        self.order.shipping_amount = shipping
        self.order.grand_total = subtotal + tax + shipping
        self.order.save()

        self.order.refresh_from_db()
        self.assertEqual(self.order.subtotal, subtotal)
        self.assertEqual(self.order.tax_amount, tax)
        self.assertEqual(self.order.shipping_amount, shipping)
        self.assertEqual(self.order.grand_total, subtotal + tax + shipping)

    def test_order_str(self):
        self.assertIn(str(self.order.id), str(self.order))
        self.assertIn(self.order.status, str(self.order))

    def test_status_values(self):
        # Byt till de statusar du använder
        self.order.status = "paid"
        self.order.save()
        self.assertEqual(self.order.status, "paid")
