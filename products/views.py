from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category


# Create your views here.
def product_list(request, slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)

    if slug:
        category = get_object_or_404(Category, slug=slug)
        products = products.filter(category=category)

    q = request.GET.get("q")
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))

    sort = request.GET.get("sort", "name")
    if sort not in ["name", "-name", "price", "-price", "created", "-created"]:
        sort = "name"
    products = products.order_by(sort)

    context = {"categories": categories, "category": category, "products": products, "sort": sort, "q": q}
    return render(request, "products/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(is_active=True, category=product.category).exclude(id=product.id)[:4]
    return render(request, "products/product_detail.html", {"product": product, "related": related})
