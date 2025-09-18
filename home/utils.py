from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.conf import settings


def send_newsletter_confirmation(subscriber, request):
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
