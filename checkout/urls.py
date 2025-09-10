from django.urls import path
from . import views

app_name = "checkout"

urlpatterns = [
    path("", views.start_checkout, name="start"),
    path("create-session/", views.create_checkout_session, name="create_session"),  # placeholder för Stripe
]
