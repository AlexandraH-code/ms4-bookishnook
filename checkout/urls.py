from django.urls import path
from . import views

app_name = "checkout"

urlpatterns = [
    path("", views.start_checkout, name="start"),
    path("create-session/", views.create_checkout_session, name="create_session"),  # placeholder för Stripe
    path("success/", views.success, name="success"),
    path("cancel/", views.cancel, name="cancel"),
]
