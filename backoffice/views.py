import csv
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from .forms import ProductForm
from orders.models import Order
from products.models import Product

"""
Backoffice views for staff/admin users.

Includes:
- Dashboard overview.
- Order list, filtering, pagination, and detailed view with status updates.
- CSV export for orders.
- CRUD views for products (list, create, edit, delete).

All views in this module require staff privileges (`@staff_member_required`).
"""

STATUSES = [
    ("pending", "Pending"),
    ("paid", "Paid"),
    ("processing", "Processing"),
    ("shipped", "Shipped"),
    ("refunded", "Refunded"),
    ("cancelled", "Cancelled"),
]


# Create your views here.
@staff_member_required
def dashboard(request):
    """
    Display the backoffice dashboard with a quick overview.

    Context:
        recent (QuerySet): The 5 most recent orders.
        open_count (int): Number of open orders (pending, paid, or processing).
        statuses (list): List of possible order statuses.

    Template:
        backoffice/dashboard.html
    """
    # Quick overview
    recent = Order.objects.order_by("-created")[:5]
    open_count = Order.objects.filter(status__in=["pending", "paid", "processing"]).count()
    return render(request, "backoffice/dashboard.html", {
        "recent": recent,
        "open_count": open_count,
        "statuses": STATUSES,
    })


@staff_member_required
def orders_list(request):
    """
    Display a paginated list of orders with optional search and status filters.

    Query parameters:
        q (str): Search string (matches ID or email, case-insensitive).
        status (str): Optional order status filter.
        page (int): Page number for pagination.

    Context:
        orders (QuerySet): Paginated order list.
        page_obj (Page): Current page object.
        elided_range (list): Page range for navigation.
        q (str): Search query string.
        status (str): Selected status filter.
        statuses (list): List of all available statuses.

    Template:
        backoffice/orders_list.html
    """
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    qs = Order.objects.all().order_by("-created")
    if q:
        qs = qs.filter(Q(id__icontains=q) | Q(email__icontains=q))
    if status:
        qs = qs.filter(status=status)
        
    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    try:
        elided_range = list(paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1))
    except AttributeError:
        elided_range = list(paginator.page_range)

    return render(request, "backoffice/orders_list.html", {
        "page_obj": page_obj,
        "orders": page_obj.object_list,
        "q": q,
        "status": status,
        "statuses": STATUSES,  # sends the list to template
        "elided_range": elided_range,
    })


@staff_member_required
def order_detail(request, pk):
    """
    Display and manage a single order.

    Supports updating the order status via POST:
    - action = "mark_<status>" (e.g. "mark_paid", "mark_shipped").
    - Automatically sets timestamps for specific statuses.

    Status timestamps:
        paid -> paid_at
        shipped -> shipped_at
        refunded -> refunded_at

    Args:
        pk (int): Primary key of the order.

    Template:
        backoffice/order_detail.html
    """

    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action.startswith("mark_"):
            new_status = action.replace("mark_", "")
            valid_statuses = [s[0] for s in STATUSES]
            if new_status in valid_statuses:
                order.status = new_status
                if new_status == "paid":
                    order.paid_at = timezone.now()
                elif new_status == "shipped":
                    order.shipped_at = timezone.now()
                elif new_status == "refunded":
                    order.refunded_at = timezone.now()
                order.save()
                messages.success(request, f"Order #{order.id} marked as {new_status.upper()}.")
                return redirect("backoffice:order_detail", pk=order.id)
    return render(request, "backoffice/order_detail.html", {
        "order": order,
        "statuses": STATUSES,  # sends the list to template
    })


@staff_member_required
def orders_export_csv(request):
    """
    Export all orders to a CSV file (UTF-8 with BOM for Excel compatibility).

    Columns:
        id, email, status, total, tax, shipping, grand_total, created

    Returns:
        HttpResponse: Downloadable CSV file.
    """

    qs = Order.objects.all().order_by("-created")
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="orders.csv"'
    resp.write("\ufeff")
    w = csv.writer(resp)
    w.writerow(["id", "email", "status", "total", "tax", "shipping", "grand_total", "created"])
    for o in qs.iterator():
        w.writerow([o.id, o.email, o.status, o.total, o.tax_amount, o.shipping, o.grand_total, o.created.isoformat()])
    return resp


@staff_member_required
def products_list(request):
    """
    Display a paginated list of products with optional search and active filters.

    Query parameters:
        q (str): Search by name, slug, or description.
        active (str): "1" = only active products, "0" = only inactive.
        page (int): Page number.

    Context:
        products (QuerySet): Paginated product list.
        page_obj (Page): Current page object.
        q (str): Search term.
        active (str): Active/inactive filter.

    Template:
        backoffice/products_list.html
    """

    q = request.GET.get("q", "").strip()
    active = request.GET.get("active", "")
    
    qs = Product.objects.select_related("category").order_by("-created")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(slug__icontains=q) | Q(description__icontains=q))
    if active in ("1","0"):
        qs = qs.filter(is_active=(active == "1"))
    
    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    try:
        elided_range = list(paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1))
    except AttributeError:
        elided_range = list(paginator.page_range)

    return render(request, "backoffice/products_list.html", {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "q": q,
        "active": active,
        "elided_range": elided_range, 
    })


@staff_member_required
def product_create(request):
    """
    Create a new product entry.

    GET:
        Renders an empty ProductForm.

    POST:
        Validates and saves a new Product.
        Redirects to product list with success message.

    Template:
        backoffice/product_form.html
    """

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" created.')
            return redirect("backoffice:products_list")
    else:
        form = ProductForm()
    return render(request, "backoffice/product_form.html", {"form": form, "title": "New Product"})


@staff_member_required
def product_edit(request, pk):
    """
    Edit an existing product.

    GET:
        Renders ProductForm prefilled with current product data.

    POST:
        Validates and saves the changes.
        Redirects to product list with success message.

    Args:
        pk (int): Primary key of the product.

    Template:
        backoffice/product_form.html
    """

    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated.')
            return redirect("backoffice:products_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "backoffice/product_form.html", {"form": form, "title": f'Edit: {product.name}', "product": product})


@staff_member_required
def product_delete(request, pk):
    """
    Delete a product with confirmation prompt.

    GET:
        Displays a confirmation page.

    POST:
        Deletes the product and redirects to product list.

    Args:
        pk (int): Primary key of the product.

    Template:
        backoffice/product_confirm_delete.html
    """

    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f'Product "{name}" deleted.')
        return redirect("backoffice:products_list")
    return render(request, "backoffice/product_confirm_delete.html", {"product": product})
