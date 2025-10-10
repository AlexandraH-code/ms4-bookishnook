from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.conf import settings

"""
Utilities for the Home app (newsletter-related email helpers).
"""


def send_newsletter_confirmation(subscriber, request):
    """
    Send the double opt-in confirmation email for a newsletter subscription.

    Builds absolute confirm/unsubscribe URLs from the current request, renders
    subject/text/HTML templates, and sends a multipart email to the subscriber.

    Args:
        subscriber (home.models.NewsletterSubscriber): The subscriber receiving the email.
        request (django.http.HttpRequest): Used to construct absolute URLs
            for confirmation and unsubscribe links.

    Templates used:
        - emails/newsletter_confirm_subject.txt
        - emails/newsletter_confirm.txt
        - emails/newsletter_confirm.html

    From address:
        Uses `settings.DEFAULT_FROM_EMAIL` as the sender.

    Returns:
        None

    Raises:
        Any exception from the email backend if sending fails
        (because `fail_silently=False` is used).
    """

    confirm_url = request.build_absolute_uri(
        reverse("newsletter_confirm", args=[subscriber.confirm_token])
    )
    unsubscribe_url = request.build_absolute_uri(
        reverse("newsletter_unsubscribe", args=[subscriber.unsubscribe_token])
    )

    ctx = {"subscriber": subscriber, "confirm_url": confirm_url, "unsubscribe_url": unsubscribe_url}
    subject = render_to_string("emails/newsletter_confirm_subject.txt", ctx).strip()
    text_body = render_to_string("emails/newsletter_confirm.txt", ctx)
    html_body = render_to_string("emails/newsletter_confirm.html", ctx)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[subscriber.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
