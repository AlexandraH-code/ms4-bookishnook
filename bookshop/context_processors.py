from products.models import Category


def cart_count(request):
    cart = request.session.get("cart", {})
    return {"cart_count": sum(cart.values())}


def nav_categories(request):
    roots = Category.objects.filter(parent__isnull=True, is_active=True).order_by("name")
    bookmarks = Category.objects.filter(slug="bookmarks", parent__isnull=True).first()
    return {
        "root_categories": roots,      # alla rotkategorier
        "bookmarks_cat": bookmarks,    # Bookmarks-objektet (rot)
    }
    return {"root_categories": roots}

