from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from products.models import Product


"""
Cart views — manage the shopping cart stored in the user session.

The cart is stored as a dictionary in `request.session["cart"]`:
{
    "product_id": quantity,
    ...
}

Features:
- Display current cart contents.
- Add, update, or remove items.
- Automatic recalculation of totals.
- Feedback messages for user actions.
"""


# Create your views here.
def _get_cart(session):
    """
    Retrieve the cart dictionary from the session, creating it if needed.

    Args:
        session (SessionBase): The current Django session object.

    Returns:
        dict: The cart stored in the session.
              Keys are product IDs (as strings); values are quantities (int).
    """

    return session.setdefault("cart", {})  # { "product_id": qty, ... }


def view_cart(request):
    """
    Display the current contents of the cart.

    For each product in the cart, retrieves the `Product` instance from the
    database, calculates its subtotal, and accumulates the total price.

    Context:
        items (list[dict]): A list of dictionaries containing:
            - product (Product): The product instance.
            - qty (int): Quantity of that product.
            - subtotal (Decimal): Product price * quantity.
        total (Decimal): Total price of all items combined.

    Template:
        cart/cart.html
    """

    cart = _get_cart(request.session)
    items, total = [], 0
    for pid, qty in cart.items():
        product = get_object_or_404(Product, id=int(pid), is_active=True)
        subtotal = product.price * qty
        total += subtotal
        items.append({"product": product, "qty": qty, "subtotal": subtotal})
    return render(request, "cart/cart.html", {"items": items, "total": total})


def add_to_cart(request, product_id):
    """
    Add a product to the shopping cart.

    If the product is already in the cart, its quantity is increased.
    Only accepts POST requests.

    Args:
        product_id (int): The ID of the product to add.

    Redirects:
        - To the product detail page after adding.
        - To the cart page if accessed via a non-POST request.

    Messages:
        - Success message shown when the product is added.
    """

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
    """
    Remove a product from the cart.

    Args:
        product_id (int): The ID of the product to remove.

    Redirects:
        - Back to the cart page.

    Messages:
        - Info message shown when the product is removed.
    """

    cart = _get_cart(request.session)
    cart.pop(str(product_id), None)
    request.session.modified = True
    messages.info(request, "Item removed.")
    return redirect("cart:view")


def update_cart(request, product_id):
    """
    Update the quantity of a product in the cart.

    If the new quantity is 0 or negative, the item is removed from the cart.
    Otherwise, its quantity is updated to the given value.

    Args:
        product_id (int): The ID of the product to update.

    Redirects:
        - Back to the cart page after the update.
    """

    if request.method == "POST":
        qty = int(request.POST.get("qty", 1))
        cart = _get_cart(request.session)
        if qty <= 0:
            cart.pop(str(product_id), None)
        else:
            cart[str(product_id)] = qty
        request.session.modified = True
    return redirect("cart:view")
