from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
# from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.cache import cache
from .forms import NewsletterForm, ContactForm
from .models import NewsletterSubscriber
from products.models import Category
from .utils import send_newsletter_confirmation

"""
Public-facing views for the Home app.

Includes:
- Homepage/landing and static pages (About, FAQ, Reviews).
- Newsletter double opt-in flow (subscribe, confirm, unsubscribe).
- Contact form handling with simple rate limiting.
"""


def index(request):
    """
    Minimal index view (alias of the homepage template).
    """

    return render(request, 'home/index.html')


def home(request):
    """
    Render the homepage with up to four featured or fallback root categories
    and an empty newsletter form.

    Selection logic:
      1) Try to show up to 4 categories marked as featured (ordered).
      2) If fewer than 4, fill the remaining slots with top-level categories.
    """

    qs = Category.objects.filter(is_active=True)

    featured = list(
        qs.filter(is_featured=True)
          .order_by("featured_order", "name")
          .select_related("parent")[:4]
    )

    # Fill in root categories if fewer than 4 are selected
    if len(featured) < 4:
        exclude_ids = [c.id for c in featured]
        filler = list(
            qs.filter(parent__isnull=True)
              .exclude(id__in=exclude_ids)
              .order_by("name")[:4 - len(featured)]
        )
        featured += filler

    return render(request, "home/index.html", {
        "featured_categories": featured,
        "newsletter_form": NewsletterForm()
        })


def about(request):
    """
    Render a simple static 'About Us' page.
    """
   
    return render(request, "home/about.html")
  
  
def contact(request):
    """
    Display and process the contact form.

    POST:
        - Validates form.
        - Applies a naive rate limit: 5 messages per 10 minutes per IP.
        - Sends an email to site admin (from DEFAULT_FROM_EMAIL).
        - Shows success/failure messages and redirects back to the contact page.

    GET:
        - Renders the contact form.
    """

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # rate limit (5 attempts/10 min per IP)
            ip = request.META.get("REMOTE_ADDR", "unknown")
            key = f"contact_rate:{ip}"
            count = cache.get(key, 0)
            if count >= 5:
                messages.error(request, "Too many messages, try again later.")
                return redirect("contact")
            cache.set(key, count+1, 600)

            body = (
                f"From: {form.cleaned_data['name']} <{form.cleaned_data['email']}>\n\n"
                f"{form.cleaned_data['message']}"
            )
            email = EmailMessage(
                subject="[Bookish Nook] Contact form",
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.DEFAULT_FROM_EMAIL],
                reply_to=[form.cleaned_data["email"]],
            )
            try:
                email.send(fail_silently=False)
                messages.success(request, "Thanks! We’ve received your message.")
                return redirect("contact")
            except Exception:
                messages.error(request, "Oops, something went wrong. Please try again.")
    else:
        form = ContactForm()
    return render(request, "home/contact.html", {"form": form})


def faq(request):
    """
    Render the FAQ page.
    """
    
    return render(request, "home/faq.html")


@require_POST
def subscribe_newsletter(request):
    """
    Subscribe an email address to the newsletter (AJAX-only).

    Behavior:
        - Validates email with `NewsletterForm`.
        - Creates or fetches a `NewsletterSubscriber`.
        - Resets unsubscribe/confirmed flags if previously unsubscribed.
        - Ensures tokens exist and, if not confirmed, sends a confirmation email
          and returns a JSON response indicating double opt-in is required.
        - If already confirmed, returns a JSON response indicating no action needed.

    Returns:
        JsonResponse with:
          { ok: bool, created: bool, requires_confirmation?: bool, already_confirmed?: bool }
        and HTTP 400 with { error: "..."} on invalid input.
    """

    form = NewsletterForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "error": "Please enter a valid email."}, status=400)

    email = form.cleaned_data["email"]
    sub, created = NewsletterSubscriber.objects.get_or_create(email=email)
    # Reactivate if they previously unsubscribed
    if sub.unsubscribed:
        sub.unsubscribed = False
        sub.confirmed = False

    # Tokens + send confirmation if not confirmed
    sub.ensure_tokens(save=True)
    if not sub.confirmed:
        send_newsletter_confirmation(sub, request)
        sub.confirm_sent_at = timezone.now()
        sub.save(update_fields=["confirm_sent_at", "unsubscribed", "confirmed"])
        return JsonResponse({"ok": True, "created": created, "requires_confirmation": True})

    # Already confirmed earlier
    return JsonResponse({"ok": True, "created": False, "already_confirmed": True})


def newsletter_confirm(request, token):
    """
    Confirm a newsletter subscription via token (double opt-in).

    Args:
        token (str): The confirmation token sent to the subscriber.

    Returns:
        Rendered confirmation page; sets `confirmed=True` and timestamp if needed.
    """

    sub = get_object_or_404(NewsletterSubscriber, confirm_token=token, unsubscribed=False)
    if not sub.confirmed:
        sub.confirmed = True
        sub.confirmed_at = timezone.now()
        sub.save(update_fields=["confirmed", "confirmed_at"])
    return render(request, "home/newsletter_confirmed.html", {"subscriber": sub})


def newsletter_unsubscribe(request, token):
    """
    Unsubscribe a newsletter subscriber via token.

    Args:
        token (str): The unsubscribe token sent to the subscriber.

    Returns:
        Rendered unsubscribe page; sets `unsubscribed=True` and `confirmed=False`.
    """

    sub = get_object_or_404(NewsletterSubscriber, unsubscribe_token=token)
    if not sub.unsubscribed:
        sub.unsubscribed = True
        sub.confirmed = False
        sub.save(update_fields=["unsubscribed", "confirmed"])
    return render(request, "home/newsletter_unsubscribed.html", {"subscriber": sub})
