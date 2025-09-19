from django.urls import path
from . import views

app_name = "profiles"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("edit/", views.edit_profile, name="edit"),
    path("addresses/", views.addresses, name="addresses"),
    path("addresses/new/", views.address_create, name="address_create"),
    path("addresses/<int:pk>/edit/", views.address_edit, name="address_edit"),
    path("addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),
    path("orders/", views.orders, name="orders"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
]
