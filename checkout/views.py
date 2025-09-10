from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from products.models import Product
from decimal import Decimal


# Create your views here.
def _cart_items_and_total(request):
    """
    Returnerar (items, total) från sessionens cart.
    items: [{product, qty, subtotal}]
    total: Decimal-summa
    """
    cart = request.session.get("cart", {})
    items, total = [], 0
    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=int(pid), is_active=True)
        qty = int(qty)
        subtotal = product.price * qty
        total += subtotal
        items.append({"product": product, "qty": qty, "subtotal": subtotal})
    return items, total


def start_checkout(request):
    items, total = _cart_items_and_total(request)
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("cart:view")

    # (valfritt) demonstrativ moms/ship för känsla – justera eller ta bort
    tax_rate = Decimal("0.25")  # 25% (exempel), byt sen när du bygger riktigt
    tax_amount = (total * tax_rate).quantize(Decimal("0.01"))  # avrunda till 2 decimaler
    shipping = 49 if total < 500 else 0  # fri frakt över 500 kr, exempel
    grand_total = total + tax_amount + shipping

    ctx = {
        "items": items,
        "total": total,
        "tax_amount": tax_amount,
        "shipping": shipping,
        "grand_total": grand_total,
    }
    return render(request, "checkout/checkout_start.html", ctx)


def create_checkout_session(request):
    """
    Placeholder för Stripe. Just nu visar vi bara ett meddelande och
    skickar tillbaka användaren till checkout-sidan.
    """
    messages.warning(request, "Stripe checkout is not configured yet.")
    return redirect("checkout:start")
