from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("contact/", views.contact, name="contact"),
    path("about/", views.about, name="about"),
    path("faq/", views.faq, name="faq"),
    path("reviews/", views.reviews, name="reviews"),
    path("newsletter/subscribe/", views.subscribe_newsletter, name="newsletter_subscribe"),
]