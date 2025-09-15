from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.utils import formataddr


def send_order_confirmation(order, customer_email=None, customer_name=None):
    to_email = customer_email or order.email
    if not to_email:
        return False

    ctx = {"order": order, "customer_name": customer_name}
    subject = render_to_string("emails/order_confirmation_subject.txt", ctx).strip()
    text_body = render_to_string("emails/order_confirmation.txt", ctx)
    html_body = render_to_string("emails/order_confirmation.html", ctx)

    from_pretty = formataddr((getattr(settings, "DEFAULT_FROM_NAME", "Bookish Nook"),
                              settings.DEFAULT_FROM_EMAIL))

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_pretty,   # ← Namn + adress
        to=[to_email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
    return True
