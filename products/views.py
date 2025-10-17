from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category

"""
Views for browsing products and categories.
"""


def _resolve_category_by_path(slug_path: str):
    """
    Resolve a nested category from a slug path like "bookmarks/leather".

    Walks the slug chain from root to leaf and ensures each level exists
    under the previous one.

    Args:
        slug_path (str): Slash-separated category path (e.g., "parent/child").

    Returns:
        Category: The leaf Category that matches the given path.

    Raises:
        Http404: If any path segment does not match a category under the
                 expected parent.
    """

    parts = [p for p in slug_path.split("/") if p]
    parent = None
    cat = None
    for slug in parts:
        cat = get_object_or_404(Category, slug=slug, parent=parent)
        parent = cat
    return cat


def product_list(request, slug_path=None):
    """
    List and filter products, optionally scoped to a (nested) category.

    Supports:
      - Category context via `slug_path` (includes all descendants).
      - Full-text search on product name/description with `?q=...`.
      - Whitelisted sorting via `?sort=name|-name|price|-price|created|-created`.

    Args:
        request (HttpRequest): The incoming request.
        slug_path (str | None): Optional nested category path.

    Returns:
        HttpResponse: Rendered product list page.
    """

    # Basquery + preload category for less SQL
    products = Product.objects.filter(is_active=True).select_related("category")

    # Category (incl. all subcategories)
    category = None
    if slug_path:
        category = _resolve_category_by_path(slug_path)
        products = products.filter(category_id__in=category.descendant_ids())

    # Search
    q = request.GET.get("q")
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )

    # Sorting
    sort = request.GET.get("sort", "name")
    if sort not in ["name", "-name", "price", "-price", "created", "-created"]:
        sort = "name"
    products = products.order_by(sort)

    categories = Category.objects.filter(parent__isnull=True, is_active=True).order_by("name")

    context = {
        "categories": categories,
        "category": category,
        "products": products,
        "sort": sort,
        "q": q,
    }
    return render(request, "products/product_list.html", context)


def product_detail(request, slug):
    """
    Show a single product detail page plus a small set of related items.

    Related items are chosen from the same category and exclude the current product.

    Args:
        request (HttpRequest): The incoming request.
        slug (str): The product's unique slug.

    Returns:
        HttpResponse: Rendered product detail page.

    Raises:
        Http404: If the product does not exist or is not active.
    """

    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(is_active=True, category=product.category).exclude(id=product.id)[:4]
    return render(request, "products/product_detail.html", {"product": product, "related": related})
