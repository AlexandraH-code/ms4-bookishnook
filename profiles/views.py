from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ProfileForm, AddressForm
from .models import Address
from orders.models import Order
from profiles.models import Profile

"""
Views for the user's account area: dashboard, profile editing,
address CRUD, and viewing past orders.
"""


# Create your views here.
@login_required
def dashboard(request):
    """
    Render a lightweight account dashboard for the current user.

    Shows the 10 most recent orders matched by the user's email,
    ordered by newest first.

    Args:
        request (HttpRequest): Authenticated request.

    Returns:
        HttpResponse: Rendered dashboard page.
    """

    orders = Order.objects.filter(email=request.user.email).order_by("-created")[:10]
    return render(request, "profiles/dashboard.html", {"orders": orders})


@login_required
def edit_profile(request):
    """
    Create or edit the current user's profile.

    On GET:
        Renders a form bound to the user's Profile (created if missing).
    On POST:
        Validates and saves the Profile, then redirects back with a flash message.

    Args:
        request (HttpRequest): Authenticated request.

    Returns:
        HttpResponse: Rendered profile form or redirect after successful save.
    """

    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("profiles:edit")  # eller vart du vill tillbaka
    else:
        form = ProfileForm(instance=profile)

    return render(request, "profiles/edit_profile.html", {"form": form})


@login_required
def addresses(request):
    """
    List all addresses belonging to the current user.

    Args:
        request (HttpRequest): Authenticated request.

    Returns:
        HttpResponse: Rendered address list page.
    """

    addrs = request.user.addresses.all()
    return render(request, "profiles/addresses.html", {"addresses": addrs})


@login_required
def address_create(request):
    """
    Create a new address for the current user.

    On POST, validates and saves the address (assigning `user`),
    then redirects back to the address list with a success message.

    Args:
        request (HttpRequest): Authenticated request.

    Returns:
        HttpResponse: Rendered form or redirect after successful save.
    """

    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            addr.save()
            messages.success(request, "Address saved.")
            return redirect("profiles:addresses")
    else:
        form = AddressForm()
    return render(request, "profiles/address_form.html", {"form": form, "title":"New Address"})


@login_required
def address_edit(request, pk):
    """
    Edit an existing address owned by the current user.

    Args:
        request (HttpRequest): Authenticated request.
        pk (int): Primary key of the Address to edit.

    Returns:
        HttpResponse: Rendered form or redirect after successful save.

    Raises:
        Http404: If the address does not belong to the user or does not exist.
    """

    addr = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=addr)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated.")
            return redirect("profiles:addresses")
    else:
        form = AddressForm(instance=addr)
    return render(request, "profiles/address_form.html", {"form": form, "title":"Edit Address"})


@login_required
def address_delete(request, pk):
    """
    Delete an address owned by the current user.

    Args:
        request (HttpRequest): Authenticated request.
        pk (int): Primary key of the Address to delete.

    Returns:
        HttpResponseRedirect: Redirect to the address list after deletion.

    Raises:
        Http404: If the address does not belong to the user or does not exist.
    """

    addr = get_object_or_404(Address, pk=pk, user=request.user)
    addr.delete()
    messages.success(request, "Address removed.")
    return redirect("profiles:addresses")


@login_required
def orders(request):
    """
    Show all orders associated with the current user's email.

    Args:
        request (HttpRequest): Authenticated request.

    Returns:
        HttpResponse: Rendered order list page.
    """

    qs = Order.objects.filter(email=request.user.email).order_by("-created")
    return render(request, "profiles/orders.html", {"orders": qs})


@login_required
def order_detail(request, pk):
    """
    Show details for a single order belonging to the current user's email.

    Args:
        request (HttpRequest): Authenticated request.
        pk (int): Primary key of the order.

    Returns:
        HttpResponse: Rendered order detail page.

    Raises:
        Http404: If the order doesn't exist or is not associated with the user's email.
    """

    order = get_object_or_404(Order, pk=pk, email=request.user.email)
    return render(request, "profiles/order_detail.html", {"order": order})
