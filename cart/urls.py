from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.view_cart, name="view"),
    path("add/<int:product_id>/", views.add_to_cart, name="add"),
    path("remove/<int:product_id>/", views.remove_from_cart, name="remove"),
    path("update/<int:product_id>/", views.update_cart, name="update"),
]
