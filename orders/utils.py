from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from email.utils import formataddr

"""
Utility functions for order-related emails.
"""


def send_order_confirmation(order, customer_email=None, customer_name=None):
    """
    Send the order confirmation email (text + HTML) to the customer.

    Args:
        order (orders.models.Order): The order to render in the email templates.
        customer_email (str | None): Optional override for the recipient email.
            If not provided, uses `order.email`. If neither is available, no
            email is sent and the function returns False.
        customer_name (str | None): Optional display name to include in templates.
            Typically the order's full name; templates can handle it being None.

    Templates used:
        - emails/order_confirmation_subject.txt
        - emails/order_confirmation.txt
        - emails/order_confirmation.html

    From address:
        Builds a pretty "From" header from:
          DEFAULT_FROM_NAME (fallback "Bookish Nook") + DEFAULT_FROM_EMAIL.

    Returns:
        bool: True if the email was sent, False if there was no recipient.

    Raises:
        Any exception raised by the underlying email backend if send fails
        (since `fail_silently=False` is used).
    """

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
        from_email=from_pretty,   # ← Name + address
        to=[to_email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
    return True
