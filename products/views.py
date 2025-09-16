from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category


# Create your views here.
def _resolve_category_by_path(slug_path: str):
    """'bookmarks/leather' -> Category('Leather' under 'Bookmarks')."""
    parts = [p for p in slug_path.split("/") if p]
    parent = None
    cat = None
    for slug in parts:
        cat = get_object_or_404(Category, slug=slug, parent=parent)
        parent = cat
    return cat


def product_list(request, slug_path=None):
    # Basquery + preload kategori för mindre SQL
    products = Product.objects.filter(is_active=True).select_related("category")

    # Kategori (inkl. alla underkategorier)
    category = None
    if slug_path:
        category = _resolve_category_by_path(slug_path)
        products = products.filter(category_id__in=category.descendant_ids())

    # Sök
    q = request.GET.get("q")
    if q:
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )

    # Sortering (samma whitelist som du hade)
    sort = request.GET.get("sort", "name")
    if sort not in ["name", "-name", "price", "-price", "created", "-created"]:
        sort = "name"
    products = products.order_by(sort)

    # (Om du behöver visa alla root-kategorier i sidans filter/meny:)
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
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(is_active=True, category=product.category).exclude(id=product.id)[:4]
    return render(request, "products/product_detail.html", {"product": product, "related": related})
