from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from products.models import Product


# Create your views here.
def _get_cart(session):
    return session.setdefault("cart", {})  # { "product_id": qty, ... }


def view_cart(request):
    cart = _get_cart(request.session)
    items, total = [], 0
    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=int(pid), is_active=True)
        subtotal = product.price * qty
        total += subtotal
        items.append({"product": product, "qty": qty, "subtotal": subtotal})
    return render(request, "cart/cart.html", {"items": items, "total": total})


def add_to_cart(request, product_id):
    if request.method != "POST":
        return redirect("cart:view")
    product = get_object_or_404(Product, id=product_id, is_active=True)
    qty = max(1, int(request.POST.get("qty", 1)))
    cart = _get_cart(request.session)
    cart[str(product_id)] = cart.get(str(product_id), 0) + qty
    request.session.modified = True
    messages.success(request, f"Added {product.name} to cart.")
    return redirect(product.get_absolute_url())


def remove_from_cart(request, product_id):
    cart = _get_cart(request.session)
    cart.pop(str(product_id), None)
    request.session.modified = True
    messages.info(request, "Item removed.")
    return redirect("cart:view")


def update_cart(request, product_id):
    if request.method == "POST":
        qty = int(request.POST.get("qty", 1))
        cart = _get_cart(request.session)
        if qty <= 0:
            cart.pop(str(product_id), None)
        else:
            cart[str(product_id)] = qty
        request.session.modified = True
    return redirect("cart:view")
