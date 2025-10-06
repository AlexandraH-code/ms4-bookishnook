from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError
from django.utils import timezone

from products.models import Product
from orders.models import Order, OrderItem, ProcessedStripeEvent
from orders.utils import send_order_confirmation  

from decimal import Decimal, ROUND_HALF_UP
import stripe
import logging
import json
import os

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
        # shipping_address_collection={"allowed_countries": ["SE", "NO", "DK", "FI", "DE"]},
        shipping_address_collection={"allowed_countries": ["US", "CA", "GB", "SE", "NO", "DK", "FI", "DE", "FR", "ES", "IT", "NL", "PL", "IE", "AU", "NZ"]},
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
    if session_id:
        try:
            sess = stripe.checkout.Session.retrieve(
                session_id,
                # INTE "shipping_details" här – det är inte expanderbart
                expand=[
                    "customer",
                    "customer_details",
                    "payment_intent",
                    "payment_intent.charges.data",
                ],
            )
            oid = (getattr(sess, "metadata", {}) or {}).get("order_id") if hasattr(sess, "to_json") \
                  else (sess.get("metadata") or {}).get("order_id")
            if oid:
                order = Order.objects.filter(id=oid).first()

            # valfritt: försök enricha (best effort), rör inte e-post eller status här
            # ... du kan lämna det som du har eller ta bort enrichment om du vill minimera brus
        except Exception:
            # lugn fallback: visa bara kvittosidan
            pass

    request.session["cart"] = {}
    request.session.modified = True
    return render(request, "checkout/success.html", {"order": order})


def cancel(request):
    messages.info(request, "You canceled the payment.")
    return render(request, "checkout/cancel.html")


def _first(*vals):
    for v in vals:
        if v not in (None, "", {}):
            return v
    return None


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    # --- Verifiera event ---
    if secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, secret)
        except ValueError:
            return HttpResponseBadRequest("Invalid payload")
        except stripe.error.SignatureVerificationError:
            return HttpResponseBadRequest("Invalid signature")
    else:
        if settings.DEBUG:
            try:
                event = json.loads(payload.decode("utf-8"))
            except Exception:
                return HttpResponseBadRequest("Invalid payload (dev)")
        else:
            return HttpResponseBadRequest("Webhook secret not configured")

    etype = event.get("type") if isinstance(event, dict) else event["type"]
    evt_id = event.get("id")

    # --- Idempotenslager A: processa aldrig samma Stripe-event två gånger ---
    if evt_id:
        try:
            ProcessedStripeEvent.objects.create(event_id=evt_id)
        except IntegrityError:
            # Redan processat – returnera 200 så Stripe inte re-enqueue:ar
            return HttpResponse(status=200)

    if etype != "checkout.session.completed":
        return HttpResponse(status=200)

    raw = event["data"]["object"]
    session_id = raw.get("id")

    # --- Hämta expanderad session & PI (behåll 'to_json'-vägen som gav korrekta adresser) ---
    try:
        sess = stripe.checkout.Session.retrieve(
            session_id,
            expand=[
                "customer",
                "customer_details",
                "shipping_details",
                "payment_intent",
                "payment_intent.charges.data",
            ],
        )
        sess_dict = json.loads(sess.to_json()) if hasattr(sess, "to_json") else sess
    except Exception:
        # fallback: använd eventets objekt
        sess_dict = raw

    # --- Hitta Order ---
    meta = sess_dict.get("metadata") or {}
    order_id = meta.get("order_id")
    order = Order.objects.filter(id=order_id).first() if order_id else None
    if not order:
        order = Order.objects.filter(stripe_session_id=session_id).first()
    if not order:
        return HttpResponse(status=200)

    # === Plocka fält (EXAKT samma prioritering som i din fungerande version) ===
    customer_details = sess_dict.get("customer_details") or {}

    # SHIPPING: vanlig väg eller collected_information (som i din dump)
    shipping_details = _first(
        sess_dict.get("shipping_details"),
        (sess_dict.get("collected_information") or {}).get("shipping_details"),
    ) or {}

    # PaymentIntent/charges fallback
    pi = sess_dict.get("payment_intent")
    charges = []
    if isinstance(pi, dict):
        charges = (pi.get("charges") or {}).get("data") or []
    elif isinstance(pi, str):
        try:
            pi_obj = stripe.PaymentIntent.retrieve(pi, expand=["charges.data"])
            pi_dict = json.loads(pi_obj.to_json()) if hasattr(pi_obj, "to_json") else pi_obj
            charges = (pi_dict.get("charges") or {}).get("data") or []
        except Exception:
            charges = []
    ch0 = charges[0] if charges else {}
    billing_details_pi = ch0.get("billing_details") or {}
    shipping_pi = ch0.get("shipping") or {}

    # Email, namn, telefon
    email = _first(customer_details.get("email"), billing_details_pi.get("email"), order.email)
    full_name = _first(
        shipping_details.get("name"),
        shipping_pi.get("name"),
        customer_details.get("name"),
        billing_details_pi.get("name"),
        order.full_name,
    )
    phone = _first(
        shipping_details.get("phone"),
        shipping_pi.get("phone"),
        customer_details.get("phone"),
        billing_details_pi.get("phone"),
        order.phone,
    )

    # SHIPPING = ENBART från shipping-källor
    saddr = _first(shipping_details.get("address"), shipping_pi.get("address")) or {}
    s_line1 = saddr.get("line1"); s_line2 = saddr.get("line2")
    s_post = saddr.get("postal_code"); s_city = saddr.get("city"); s_ctry = saddr.get("country")

    # BILLING = ENBART från billing-källor
    baddr = _first(customer_details.get("address"), billing_details_pi.get("address")) or {}
    b_line1 = baddr.get("line1"); b_line2 = baddr.get("line2")
    b_post = baddr.get("postal_code"); b_city = baddr.get("city"); b_ctry = baddr.get("country")
    b_name = _first(customer_details.get("name"), billing_details_pi.get("name"), full_name)

    # --- Skriv ändringar (bara fält med värde) ---
    to_update = []
    
    def setif(attr, val):
        if val not in (None, "") and getattr(order, attr) != val:
            setattr(order, attr, val)
            to_update.append(attr)

    # Bas
    setif("email", email)
    setif("full_name", full_name)
    setif("phone", phone)

    # Shipping
    setif("address_line1", s_line1)
    setif("address_line2", s_line2)
    setif("postal_code",  s_post)
    setif("city",         s_city)
    setif("country",      s_ctry)

    # Billing
    setif("billing_name",    b_name)
    setif("billing_line1",   b_line1)
    setif("billing_line2",   b_line2)
    setif("billing_postal",  b_post)
    setif("billing_city",    b_city)
    setif("billing_country", b_ctry)

    if to_update:
        order.save(update_fields=to_update)

    # Markera paid + dra lager
    just_paid = False
    if order.status != "paid":
        order.status = "paid"
        order.save(update_fields=["status"])
        just_paid = True
        for item in order.items.select_related("product"):
            p: Product = item.product
            new_stock = max(0, p.stock - item.qty)
            p.stock = new_stock
            if new_stock == 0:
                p.is_active = False
            p.save(update_fields=["stock", "is_active"])

    # --- Idempotenslager B: skicka mejl exakt en gång per order ---
    # --- PER-ORDER-spärr: skicka bara ett mejl per order ---
    send_now = False
    with transaction.atomic():
        rows = Order.objects.filter(
            pk=order.pk,
            confirmation_sent_at__isnull=True
        ).update(confirmation_sent_at=timezone.now())
        send_now = (rows == 1)

    if send_now and order.email:
        try:
            send_order_confirmation(order, customer_email=order.email, customer_name=order.full_name)
        except Exception:
            logger.exception("Failed to send confirmation email")