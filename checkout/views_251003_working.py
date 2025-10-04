# checkout/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from products.models import Product
from orders.models import Order, OrderItem
from orders.utils import send_order_confirmation  # justera path om du har annan struktur

from decimal import Decimal, ROUND_HALF_UP
import stripe
import logging
import json

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


# -------------------- Hjälpare --------------------
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


def _extract_best_contact(sess: dict) -> dict:
    """
    Plockar ut e-post, namn, telefon + shipping/billing från:
    - session.customer_details / session.shipping_details
    - payment_intent.shipping och charges[0].billing_details
    - (ev. expanderad) session.customer
    Returnerar en dict med nycklar som matchar Order-fälten.
    """
    # 1) Grundkällor
    customer_details = sess.get("customer_details") or {}
    shipping_details = sess.get("shipping_details") or {}
    cust_addr = customer_details.get("address") or {}
    ship_addr = shipping_details.get("address") or {}

    # 2) PaymentIntent + charges fallback
    pi = sess.get("payment_intent")
    pi_obj = None
    if isinstance(pi, dict):
        pi_obj = pi
    elif isinstance(pi, str):
        try:
            pi_obj = stripe.PaymentIntent.retrieve(pi, expand=["charges.data"])
        except Exception:
            pi_obj = None

    pi_shipping = (pi_obj or {}).get("shipping") or {}               # {name,phone,address{...}}
    pi_ship_addr = pi_shipping.get("address") or {}

    charges = ((pi_obj or {}).get("charges") or {}).get("data") or []
    ch0 = charges[0] if charges else {}
    billing_details = ch0.get("billing_details") or {}               # {email,name,phone,address{...}}
    bill_addr_bd = billing_details.get("address") or {}

    # 3) Expanderad customer (om vi bad om expand=customer)
    customer_obj = sess.get("customer")
    if isinstance(customer_obj, str):
        try:
            customer_obj = stripe.Customer.retrieve(customer_obj)
        except Exception:
            customer_obj = {}
    if not isinstance(customer_obj, dict):
        customer_obj = {}

    cust_email2 = customer_obj.get("email")
    cust_addr2 = customer_obj.get("address") or {}

    # --- epost / namn / telefon ---
    email = (customer_details.get("email")
             or billing_details.get("email")
             or cust_email2
             or None)

    full_name = (shipping_details.get("name")
                 or customer_details.get("name")
                 or billing_details.get("name")
                 or pi_shipping.get("name")
                 or None)

    phone = (shipping_details.get("phone")
             or customer_details.get("phone")
             or billing_details.get("phone")
             or pi_shipping.get("phone")
             or None)

    # --- SHIPPING: session → PI.shipping ---
    ship = {
        "line1":       ship_addr.get("line1") or pi_ship_addr.get("line1"),
        "line2":       ship_addr.get("line2") or pi_ship_addr.get("line2"),
        "postal_code": ship_addr.get("postal_code") or pi_ship_addr.get("postal_code"),
        "city":        ship_addr.get("city") or pi_ship_addr.get("city"),
        "country":     ship_addr.get("country") or pi_ship_addr.get("country"),
    }

    # --- BILLING: customer_details → charges.billing → (ev.) expanded customer address ---
    bill = {
        "name":        full_name,
        "line1":       cust_addr.get("line1") or bill_addr_bd.get("line1") or cust_addr2.get("line1"),
        "line2":       cust_addr.get("line2") or bill_addr_bd.get("line2") or cust_addr2.get("line2"),
        "postal_code": cust_addr.get("postal_code") or bill_addr_bd.get("postal_code") or cust_addr2.get("postal_code"),
        "city":        cust_addr.get("city") or bill_addr_bd.get("city") or cust_addr2.get("city"),
        "country":     cust_addr.get("country") or bill_addr_bd.get("country") or cust_addr2.get("country"),
    }

    # Logg (hjälper felsökning i terminalen)
    logger.info("CONTACT DEBUG | email=%s | ship=%s | bill=%s", email, ship, bill)

    return {
        "email": email, "full_name": full_name, "phone": phone,
        # Shipping
        "address_line1": ship.get("line1"),
        "address_line2": ship.get("line2"),
        "postal_code": ship.get("postal_code"),
        "city": ship.get("city"),
        "country": ship.get("country"),
        # Billing
        "billing_name": bill.get("name"),
        "billing_line1": bill.get("line1"),
        "billing_line2": bill.get("line2"),
        "billing_postal": bill.get("postal_code"),
        "billing_city": bill.get("city"),
        "billing_country": bill.get("country"),
    }


def _apply_addresses(order: Order, data: dict):
    """
    Sätter endast fält som har värde (None/"" hoppar vi över), så vi inte råkar
    skriva över redan ifylld data.
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


def _finalize_paid(order: Order):
    """
    Markera Paid + dra lager + skicka kvitto (idempotent).
    """
    if order.status != "paid":
        order.status = "paid"
        order.save(update_fields=["status"])
        for item in order.items.select_related("product"):
            p = item.product
            new_stock = max(0, p.stock - item.qty)
            p.stock = new_stock
            if new_stock == 0:
                p.is_active = False
            p.save(update_fields=["stock", "is_active"])
    # Skicka kvitto
    send_order_confirmation(order, customer_email=order.email, customer_name=order.full_name)


# -------------------- Views --------------------
def start_checkout(request):
    items, total = _cart_items_and_total(request)
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("cart:view")

    # exempelmoms/frakt
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
        phone_number_collection={"enabled": True},   # <= lägg till
        metadata={"order_id": str(order.id)},
    )

    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id"])

    # Spara även order-id i sessionen för fallback på success
    request.session["last_order_id"] = order.id

    return redirect(session.url, permanent=False)


def success(request):
    session_id = request.GET.get("session_id")
    order = None
    sess = None

    if session_id:
        try:
            sess = stripe.checkout.Session.retrieve(
                session_id,
                expand=[
                    "customer", "customer_details", "shipping_details",
                    "payment_intent", "payment_intent.charges.data",
                ],
            )
        except Exception:
            logger.exception("SUCCESS: could not retrieve session")

    # hitta order
    oid = (sess.get("metadata") or {}).get("order_id") if sess else None
    if oid:
        order = Order.objects.filter(id=oid).first()

    if not order:
        last_id = request.session.get("last_order_id")
        if last_id:
            order = Order.objects.filter(id=last_id).first()

    if not order and session_id:
        order = Order.objects.filter(stripe_session_id=session_id).first()

    # uppdatera kontakt + adresser + finalisera
    if order:
        if sess:
            data = _extract_best_contact(sess)
            _apply_addresses(order, data)
        _finalize_paid(order)

    # töm cart
    request.session["cart"] = {}
    request.session.modified = True
    return render(request, "checkout/success.html", {"order": order})


def cancel(request):
    messages.info(request, "You canceled the payment.")
    return render(request, "checkout/cancel.html")


# checkout/views.py (ersätt HELA stripe_webhook med detta)
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
            logger.exception("WEBHOOK: invalid JSON payload")
            return HttpResponseBadRequest("Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.exception("WEBHOOK: invalid signature")
            return HttpResponseBadRequest("Invalid signature")
    else:
        if settings.DEBUG:
            try:
                event = json.loads(payload.decode("utf-8"))
            except Exception:
                logger.exception("WEBHOOK DEV: JSON parse error")
                return HttpResponseBadRequest("Invalid payload (dev)")
        else:
            logger.error("WEBHOOK: missing secret in production")
            return HttpResponseBadRequest("Webhook secret not configured")

    event_type = event.get("type") if isinstance(event, dict) else event["type"]
    logger.info("WEBHOOK: received event type=%s", event_type)

    if event_type != "checkout.session.completed":
        return HttpResponse(status=200)

    # ---- Hämta session, expandera för säkerhets skull ----
    raw_session = event["data"]["object"]
    session_id = raw_session.get("id")
    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=[
                "customer", "customer_details", "shipping_details",
                "payment_intent", "payment_intent.charges.data",
            ],
        )
        logger.info("WEBHOOK: expanded session ok id=%s", session_id)
    except Exception:
        logger.exception("WEBHOOK: could not expand session; using raw")
        session = raw_session

    # ---- Hitta order: 1) metadata.order_id -> 2) stripe_session_id fallback ----
    meta = session.get("metadata") or {}
    order_id = meta.get("order_id")
    order = None
    if order_id:
        order = Order.objects.filter(id=order_id).first()
        logger.info("WEBHOOK: lookup by metadata order_id=%s -> %s", order_id, "FOUND" if order else "MISSING")

    if not order:
        # Fallback: matcha mot fältet du sparade när du skapade sessionen
        order = Order.objects.filter(stripe_session_id=session_id).first()
        logger.info("WEBHOOK: lookup by stripe_session_id=%s -> %s", session_id, "FOUND" if order else "MISSING")

    if not order:
        logger.error("WEBHOOK: No order found for session id=%s (no update done)", session_id)
        return HttpResponse(status=200)

    # ---- Plocka ut email/namn/telefon/adresser (med fallback via PI) ----
    cust = session.get("customer_details") or {}
    ship = session.get("shipping_details") or {}
    baddr = (cust.get("address") or {})
    saddr = (ship.get("address") or {})

    # Fallback från PaymentIntent->charges[0]
    billing_details = {}
    shipping_pi = {}
    pi = session.get("payment_intent")
    charges = []
    if isinstance(pi, dict):
        charges = (pi.get("charges") or {}).get("data") or []
    elif isinstance(pi, str):
        try:
            pi_obj = stripe.PaymentIntent.retrieve(pi, expand=["charges.data"])
            charges = (pi_obj.get("charges") or {}).get("data") or []
        except Exception:
            logger.exception("WEBHOOK: PI fallback failed")
    if charges:
        ch0 = charges[0]
        billing_details = ch0.get("billing_details") or {}
        shipping_pi = ch0.get("shipping") or {}

    def first(*vals):
        for v in vals:
            if v:
                return v
        return None

    stripe_email = first(cust.get("email"), billing_details.get("email"), order.email)
    full_name    = first(ship.get("name"), shipping_pi.get("name"), cust.get("name"),
                         billing_details.get("name"), order.full_name)
    phone        = first(ship.get("phone"), shipping_pi.get("phone"), cust.get("phone"),
                         billing_details.get("phone"), order.phone)

    # Shipping
    s_line1 = first(saddr.get("line1"), (shipping_pi.get("address") or {}).get("line1"))
    s_line2 = first(saddr.get("line2"), (shipping_pi.get("address") or {}).get("line2"))
    s_post  = first(saddr.get("postal_code"), (shipping_pi.get("address") or {}).get("postal_code"))
    s_city  = first(saddr.get("city"), (shipping_pi.get("address") or {}).get("city"))
    s_ctry  = first(saddr.get("country"), (shipping_pi.get("address") or {}).get("country"))

    # Billing (fallback till shipping om billing saknas)
    bd = (billing_details.get("address") or {})
    b_line1 = first(baddr.get("line1"), bd.get("line1"), s_line1)
    b_line2 = first(baddr.get("line2"), bd.get("line2"), s_line2)
    b_post  = first(baddr.get("postal_code"), bd.get("postal_code"), s_post)
    b_city  = first(baddr.get("city"), bd.get("city"), s_city)
    b_ctry  = first(baddr.get("country"), bd.get("country"), s_ctry)
    b_name  = first(cust.get("name"), billing_details.get("name"), full_name)

    logger.info("WEBHOOK DATA: email=%s | ship=%s %s %s %s %s | bill=%s %s %s %s %s",
                stripe_email, s_line1, s_post, s_city, s_ctry, phone,
                b_line1, b_post, b_city, b_ctry, b_name)

    # ---- Skriv in fält (sätt bara om vi har värden) ----
    to_update = []
    def setif(attr, value):
        if value not in (None, "") and getattr(order, attr) != value:
            setattr(order, attr, value); to_update.append(attr)

    setif("email", stripe_email)
    setif("full_name", full_name)
    setif("phone", phone)

    setif("address_line1", s_line1)
    setif("address_line2", s_line2)
    setif("postal_code",  s_post)
    setif("city",         s_city)
    setif("country",      s_ctry)

    setif("billing_name",   b_name)
    setif("billing_line1",  b_line1)
    setif("billing_line2",  b_line2)
    setif("billing_postal", b_post)
    setif("billing_city",   b_city)
    setif("billing_country",b_ctry)

    if to_update:
        order.save(update_fields=to_update)
        logger.info("WEBHOOK: updated fields -> %s", ", ".join(to_update))
    else:
        logger.info("WEBHOOK: nothing to update on order %s", order.id)

    # ---- Markera paid + lager ----
    if order.status != "paid":
        order.status = "paid"
        order.save(update_fields=["status"])
        for item in order.items.select_related("product"):
            p = item.product
            new_stock = max(0, p.stock - item.qty)
            p.stock = new_stock
            if new_stock == 0:
                p.is_active = False
            p.save(update_fields=["stock", "is_active"])
        logger.info("WEBHOOK: order %s marked PAID and stock updated", order.id)

    # ---- Skicka kvitto ----
    try:
        send_order_confirmation(order, customer_email=order.email, customer_name=order.full_name)
        logger.info("WEBHOOK: order confirmation sent to %s", order.email)
    except Exception:
        logger.exception("WEBHOOK: could not send order confirmation")

    return HttpResponse(status=200)