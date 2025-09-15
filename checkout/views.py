from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from orders.utils import send_order_confirmation
from django.views.decorators.csrf import csrf_exempt
from products.models import Product
from orders.models import Order, OrderItem
from decimal import Decimal, ROUND_HALF_UP
import stripe
import logging
import json

logger = logging.getLogger(__name__)
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
    tax_rate = Decimal("0.25")  # exempelmoms i UI; (Stripe Tax kan aktiveras senare)
    tax_amount = (total * tax_rate).quantize(Decimal("0.01"))
    grand_total = total + shipping_amount + tax_amount

    # 1) Skapa pending Order i DB
    order = Order.objects.create(
        email=request.user.email if request.user.is_authenticated else None,
        total=total, shipping=shipping_amount, tax_amount=tax_amount, grand_total=grand_total,
        status="pending",
    )
    for it in items:
        p = it["product"]
        qty = it["qty"]
        OrderItem.objects.create(
            order=order, product=p, name=p.name, unit_price=p.price, qty=qty,
            subtotal=p.price * qty
        )

    # 2) Bygg Stripe line_items
    line_items = []
    for it in items:
        p = it["product"]
        qty = it["qty"]
        # För bilder på Stripe (frivilligt), bygg absolut URL om du har media:
        imgs = [request.build_absolute_uri(p.image.url)]if (p.image and hasattr(p.image, "url")) else []

        line_items.append({
            "price_data": {
                "currency": "sek",
                "unit_amount": _to_cents(p.price),
                "product_data": {
                    "name": p.name,
                    "images": imgs,
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

    success_url = request.build_absolute_uri(redirect("checkout:success").url) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(redirect("checkout:cancel").url)

    # 3) Skicka order-id i metadata
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,
        billing_address_collection="required", # <— lägg till
        shipping_address_collection={"allowed_countries": ["SE", "NO", "DK", "FI", "DE"]},
        # automatic_tax={"enabled": True},  # aktivera om du konfigurerat Stripe Tax
        customer_creation="always", # <— lägg till
        metadata={"order_id": str(order.id)},
    )

    # Spara session-id på ordern (hjälper på success-sidan)
    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id"])

    return redirect(session.url, permanent=False)


def success(request):
    # Valfritt: töm cart direkt, eller hämta session för kvitto-info
    session_id = request.GET.get("session_id")
    order = None
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            oid = session.get("metadata", {}).get("order_id")
            if oid:
                order = Order.objects.filter(id=oid).first()
        except Exception:
            pass

    # Töm kundvagn
    request.session["cart"] = {}
    request.session.modified = True
    return render(request, "checkout/success.html", {"order": order})


def cancel(request):
    messages.info(request, "You canceled the payment.")
    return render(request, "checkout/cancel.html")

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    event = None

    # 1) SÄKER VÄG: verifiera signatur om secret finns
    if secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, secret)
        except ValueError:
            logger.exception("Stripe webhook: invalid JSON payload")
            return HttpResponseBadRequest("Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.exception("Stripe webhook: invalid signature")
            return HttpResponseBadRequest("Invalid signature")
    else:
        # 2) DEV-FALLBACK (frivilligt): tillåt osignerat i DEBUG
        if settings.DEBUG:
            try:
                event = json.loads(payload.decode("utf-8"))
            except Exception:
                logger.exception("DEV webhook: JSON parse error")
                return HttpResponseBadRequest("Invalid payload (dev)")
        else:
            # i produktion kräver vi secret
            logger.error("Stripe webhook: missing secret in production")
            return HttpResponseBadRequest("Webhook secret not configured")

    event_type = event.get("type") if isinstance(event, dict) else event["type"]

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]

        # 1) Hitta ordern
        order_id = (session.get("metadata") or {}).get("order_id")
        if not order_id:
            return HttpResponse(status=200)

        order = Order.objects.filter(id=order_id).first()
        if not order:
            return HttpResponse(status=200)

        # 2) Läs ut e-post, shipping & billing från sessionen
        cust = session.get("customer_details") or {}       # billing info & email
        ship = session.get("shipping_details") or {}       # shipping info
        baddr = (cust.get("address") or {})                 # billing address
        saddr = (ship.get("address") or {})                 # shipping address

        # Låt Stripe-e-post vinna över tidigare (t.ex. inloggad användare)
        stripe_email = cust.get("email")
        if stripe_email and stripe_email != order.email:
            order.email = stripe_email

        # Shipping: namn/telefon/adress (om de finns)
        full_name = ship.get("name") or cust.get("name")
        phone = ship.get("phone") or cust.get("phone")

        order.full_name = full_name or order.full_name
        order.phone = phone or order.phone
        order.address_line1 = saddr.get("line1") or order.address_line1
        order.address_line2 = saddr.get("line2") or order.address_line2
        order.postal_code = saddr.get("postal_code") or order.postal_code
        order.city = saddr.get("city") or order.city
        order.country = saddr.get("country") or order.country

        # Billing: spara separat
        order.billing_name = cust.get("name") or order.billing_name
        order.billing_line1 = baddr.get("line1") or order.billing_line1
        order.billing_line2 = baddr.get("line2") or order.billing_line2
        order.billing_postal = baddr.get("postal_code") or order.billing_postal
        order.billing_city = baddr.get("city") or order.billing_city
        order.billing_country = baddr.get("country") or order.billing_country

        order.save()

        # 3) Markera betald & dra lager (din befintliga logik)
        if order.status != "paid":
            order.status = "paid"
            order.save(update_fields=["status"])
            for item in order.items.select_related("product"):
                p: Product = item.product
                new_stock = max(0, p.stock - item.qty)
                p.stock = new_stock
                if new_stock == 0:
                    p.is_active = False
                p.save(update_fields=["stock", "is_active"])

        # 4) Skicka orderbekräftelse till kundens e-post
        send_order_confirmation(order, customer_email=order.email, customer_name=order.full_name)
    else:
        logger.info(f"Unhandled Stripe event type: {event_type}")

    return HttpResponse(status=200)
