from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from products.models import Product
from decimal import Decimal, ROUND_HALF_UP
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


# Create your views here.
def _cart_items_and_total(request):
    """
    Returnerar (items, total) från sessionens cart.
    items: [{product, qty, subtotal}]
    total: Decimal-summa
    """
    cart = request.session.get("cart", {})
    items, total = [], Decimal("0.00")
    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=int(pid), is_active=True)
        qty = int(qty)
        subtotal = (product.price * qty)
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
    shipping = Decimal("49.00") if total < Decimal("500.00") else Decimal("0.00")  # fri frakt över 500 kr, exempel
    grand_total = total + tax_amount + shipping

    ctx = {
        "items": items,
        "total": total,
        "tax_amount": tax_amount,
        "shipping": shipping,
        "grand_total": grand_total,
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, "checkout/checkout_start.html", ctx)


def _to_cents(dec: Decimal) -> int:
    # SEK i ören; alltid Decimal in, avrunda halvor upp
    return int((dec * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def create_checkout_session(request):
    if request.method != "POST":
        return redirect("checkout:start")

    items, total = _cart_items_and_total(request)
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("cart:view")

    # Fraktlogik (samma som i start_checkout)
    shipping_amount = Decimal("49.00") if total < Decimal("500.00") else Decimal("0.00")

    # Bygg line items
    line_items = []
    for it in items:
        p = it["product"]
        qty = it["qty"]
        # För bilder på Stripe (frivilligt), bygg absolut URL om du har media:
        image_urls = []
        if p.image and hasattr(p.image, "url"):
            image_urls = [request.build_absolute_uri(p.image.url)]

        line_items.append({
            "price_data": {
                "currency": "sek",
                "unit_amount": _to_cents(p.price),
                "product_data": {
                    "name": p.name,
                    "images": image_urls,
                },
            },
            "quantity": qty,
        })

    # Lägg frakt som en egen rad (om > 0)
    if shipping_amount > 0:
        line_items.append({
            "price_data": {
                "currency": "sek",
                "unit_amount": _to_cents(shipping_amount),
                "product_data": {"name": "Shipping"},
            },
            "quantity": 1,
        })

    # (Val: lägg tax som egen rad — enklast är att låta Stripe sköta tax via Tax Rates/Automatic Tax.
    # I denna minimala version skippar vi tax på Stripe-sidan, och visar den bara i vårt UI.)

    success_url = request.build_absolute_uri(
        redirect("checkout:success").url
    ) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(redirect("checkout:cancel").url)

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,
        billing_address_collection="auto",
        shipping_address_collection={"allowed_countries": ["SE", "NO", "DK", "FI", "DE"]},
        # automatic_tax={"enabled": True},  # aktivera om du konfigurerat Stripe Tax
    )

    return redirect(session.url, permanent=False)


def success(request):
    # Valfritt: töm cart direkt, eller hämta session för kvitto-info
    session_id = request.GET.get("session_id")
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            payment_status = session.get("payment_status")  # 'paid' vid lyckad betalning
            # Här kan du skapa en Order, spara betalnings-id, osv.
        except Exception:
            payment_status = None
    # Töm kundvagn
    request.session["cart"] = {}
    request.session.modified = True
    return render(request, "checkout/success.html", {"session_id": session_id})

def cancel(request):
    messages.info(request, "You canceled the payment.")
    return render(request, "checkout/cancel.html")

