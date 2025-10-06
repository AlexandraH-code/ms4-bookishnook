from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ProfileForm, AddressForm
from .models import Address
from orders.models import Order
from profiles.models import Profile


# Create your views here.
@login_required
def dashboard(request):
    orders = Order.objects.filter(email=request.user.email).order_by("-created")[:10]
    return render(request, "profiles/dashboard.html", {"orders": orders})

@login_required
def edit_profile(request):
    # profile = request.user.profile
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("profiles:dashboard")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "profiles/edit_profile.html", {"form": form})

@login_required
def edit_profile(request):
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
    addrs = request.user.addresses.all()
    return render(request, "profiles/addresses.html", {"addresses": addrs})

@login_required
def address_create(request):
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
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    addr.delete()
    messages.success(request, "Address removed.")
    return redirect("profiles:addresses")

@login_required
def orders(request):
    qs = Order.objects.filter(email=request.user.email).order_by("-created")
    return render(request, "profiles/orders.html", {"orders": qs})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, email=request.user.email)
    return render(request, "profiles/order_detail.html", {"order": order})
