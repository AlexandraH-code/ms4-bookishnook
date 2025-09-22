from django.urls import path
from . import views

app_name = "backoffice"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("orders/", views.orders_list, name="orders_list"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/export/csv/", views.orders_export_csv, name="orders_export_csv"),
   
    # Product CRUD
    path("products/", views.products_list, name="products_list"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),

]
