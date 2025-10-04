# checkout/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from products.models import Product
from orders.models import Order, OrderItem
from orders.utils import send_order_confirmation  # justera om din path skiljer sig

from decimal import Decimal, ROUND_HALF_UP
import stripe
import logging
import json

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


# --------- Hjälpare ----------
def _to_cents(dec: Decimal) -> int:
    # SEK i ören; alltid Decimal in, avrunda halvor upp
    return int((dec * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


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


def _extract_addresses(session_like: dict) -> dict:
    """
    Tar en Stripe Checkout Session (eller expanderad variant) och plockar ut bästa möjliga
    e-post, namn, telefon, shipping- och billing-adresser. Har fallback via PaymentIntent->charges.
    Returnerar en dict med nycklar som matchar Order-fälten.
    """

    # Grund: det här brukar räcka
    cust = (session_like.get("customer_details") or {})
    ship = (session_like.get("shipping_details") or {})
    baddr = (cust.get("address") or {})
    saddr = (ship.get("address") or {})

    email = cust.get("email")
    full_name = ship.get("name") or cust.get("name")
    phone = ship.get("phone") or cust.get("phone")

    # Fallback via PaymentIntent -> charges[0]
    pi = session_like.get("payment_intent")
    charges = []
    if isinstance(pi, dict):
        charges = (pi.get("charges") or {}).get("data") or []
    elif isinstance(pi, str):
        try:
            pi_obj = stripe.PaymentIntent.retrieve(pi, expand=["charges.data"])
            charges = (pi_obj.get("charges") or {}).get("data") or []
        except Exception:
            logger.exception("PI fallback misslyckades")

    if charges:
        ch0 = charges[0]
        bd = ch0.get("billing_details") or {}
        sh = ch0.get("shipping") or {}
        # Uppdatera om saknas
        email = email or bd.get("email")
        full_name = full_name or bd.get("name") or sh.get("name")
        phone = phone or bd.get("phone") or sh.get("phone")
        baddr = baddr or (bd.get("address") or {})
        saddr = saddr or (sh.get("address") or {})

    # Logga vad vi faktiskt hittade (hjälper felsökning)
    logger.info("Stripe addr debug | email=%s | ship=%s | bill=%s", email, saddr, baddr)

    return {
        # primär info
        "email": email,
        "full_name": full_name,
        "phone": phone,

        # shipping
        "address_line1": saddr.get("line1"),
        "address_line2": saddr.get("line2"),
        "postal_code": saddr.get("postal_code"),
        "city": saddr.get("city"),
        "country": saddr.get("country"),

        # billing
        "billing_name":  full_name,  # om Stripe saknar separat namn för billing använder vi orderns namn
        "billing_line1": (baddr.get("line1") or None),
        "billing_line2": (baddr.get("line2") or None),
        "billing_postal": (baddr.get("postal_code") or None),
        "billing_city": (baddr.get("city") or None),
        "billing_country": (baddr.get("country") or None),
    }


def _apply_addresses(order: Order, data: dict):
    """
    Sätter bara fält om de finns (None hoppar vi över) för att inte skriva över tidigare värden.
    """
    fields = [
        "email", "full_name", "phone",
        "address_line1", "address_line2", "postal_code", "city", "country",
        "billing_name", "billing_line1", "billing_line2", "billing_postal", "billing_city", "billing_country",
    ]
    updated = []
    for f in fields:
        val = data.get(f)
        if val not in (None, ""):
            setattr(order, f, val)
            updated.append(f)
    if updated:
        order.save(update_fields=updated)


# --------- Views ----------
def start_checkout(request):
    items, total = _cart_items_and_total(request)
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("cart:view")

    # enkla exempelvärden
    tax_rate = Decimal("0.25")
    tax_amount = (total * tax_rate).quantize(Decimal("0.01"))
    shipping = Decimal("49.00") if total < Decimal("500.00") else Decimal("0.00")
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


def create_checkout_session(request):
    if request.method != "POST":
        return redirect("checkout:start")

    items, total = _cart_items_and_total(request)
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("cart:view")

    shipping_amount = Decimal("49.00") if total < Decimal("500.00") else Decimal("0.00")
    tax_rate = Decimal("0.25")
    tax_amount = (total * tax_rate).quantize(Decimal("0.01"))
    grand_total = total + shipping_amount + tax_amount

    # 1) pending order
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

    # 2) Stripe line_items
    line_items = []
    for it in items:
        p = it["product"]
        qty = it["qty"]
        imgs = [request.build_absolute_uri(p.image.url)] if (p.image and hasattr(p.image, "url")) else []
        line_items.append({
            "price_data": {
                "currency": "sek",
                "unit_amount": _to_cents(p.price),
                "product_data": {"name": p.name, "images": imgs},
            },
            "quantity": qty,
        })

    if shipping_amount > 0:
        line_items.append({
            "price_data": {
                "currency": "sek",
                "unit_amount": _to_cents(shipping_amount),
                "product_data": {"name": "Shipping"},
            },
            "quantity": 1,
        })

    success_url = request.build_absolute_uri(redirect("checkout:success").url) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(redirect("checkout:cancel").url)

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,
        billing_address_collection="required",
        shipping_address_collection={"allowed_countries": ["SE", "NO", "DK", "FI", "DE"]},
        customer_creation="always",
        metadata={"order_id": str(order.id)},
    )

    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id"])
    return redirect(session.url, permanent=False)


def success(request):
    session_id = request.GET.get("session_id")
    order = None
    if session_id:
        try:
            sess = stripe.checkout.Session.retrieve(
                session_id,
                expand=[
                    "customer", "customer_details", "shipping_details",
                    "payment_intent", "payment_intent.charges.data",
                ],
            )
            oid = (sess.get("metadata") or {}).get("order_id")
            if oid:
                order = Order.objects.filter(id=oid).first()

            if order:
                # Skriv in adresser här också (best effort)
                data = _extract_addresses(sess)
                
                logger.warning("APPLY DBG (webhook) | order=%s | data=%s", order.id, data)

                _apply_addresses(order, data)
        except Exception:
            logger.exception("Checkout success: could not enrich addresses")

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
        if settings.DEBUG:
            try:
                event = json.loads(payload.decode("utf-8"))
            except Exception:
                logger.exception("DEV webhook: JSON parse error")
                return HttpResponseBadRequest("Invalid payload (dev)")
        else:
            logger.error("Stripe webhook: missing secret in production")
            return HttpResponseBadRequest("Webhook secret not configured")

    event_type = event.get("type") if isinstance(event, dict) else event["type"]

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = (session.get("metadata") or {}).get("order_id")
        if not order_id:
            return HttpResponse(status=200)

        order = Order.objects.filter(id=order_id).first()
        if not order:
            return HttpResponse(status=200)

        # Skriv adresser från event-session (ev. utan expand)
        data = _extract_addresses(session)
        
        logger.warning("APPLY DBG (success) | order=%s | data=%s", order.id, data)
        
        _apply_addresses(order, data)

        # Markera Paid + lager
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

        # Kvitto
        send_order_confirmation(order, customer_email=order.email, customer_name=order.full_name)

    else:
        logger.info(f"Unhandled Stripe event type: {event_type}")

    return HttpResponse(status=200)
