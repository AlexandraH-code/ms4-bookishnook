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


# Create your views here.
def index(request):
    return render(request, 'home/index.html')


def home(request):
    qs = Category.objects.filter(is_active=True)

    featured = list(
        qs.filter(is_featured=True)
          .order_by("featured_order", "name")
          .select_related("parent")[:4]
    )

    # Fyll på med root-kategorier om färre än 4 är markerade
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
    return render(request, "home/about.html")
   
   
def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            body = (
                f"From: {form.cleaned_data['name']} <{form.cleaned_data['email']}>\n\n"
                f"{form.cleaned_data['message']}"
            )
            EmailMessage(
                subject="Contact form – Bookish Nook",
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.DEFAULT_FROM_EMAIL],  # skicka till din inkorg
                reply_to=[form.cleaned_data['email']],
            ).send()
            messages.success(request, "Thanks! We’ve received your message.")
            return redirect("contact")
    else:
        form = ContactForm()
    return render(request, "home/contact.html", {"form": form})


def faq(request):
    return render(request, "home/faq.html")


def reviews(request):
    return render(request, "home/reviews.html")


@require_POST
def subscribe_newsletter(request):
    form = NewsletterForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "error": "Please enter a valid email."}, status=400)

    email = form.cleaned_data["email"]
    sub, created = NewsletterSubscriber.objects.get_or_create(email=email)
    # Återaktivera om de tidigare avregistrerat sig
    if sub.unsubscribed:
        sub.unsubscribed = False
        sub.confirmed = False

    # Tokens + skicka bekräftelse om ej confirmed
    sub.ensure_tokens(save=True)
    if not sub.confirmed:
        send_newsletter_confirmation(sub, request)
        sub.confirm_sent_at = timezone.now()
        sub.save(update_fields=["confirm_sent_at", "unsubscribed", "confirmed"])
        return JsonResponse({"ok": True, "created": created, "requires_confirmation": True})

    # Redan klar sedan tidigare
    return JsonResponse({"ok": True, "created": False, "already_confirmed": True})


def newsletter_confirm(request, token):
    sub = get_object_or_404(NewsletterSubscriber, confirm_token=token, unsubscribed=False)
    if not sub.confirmed:
        sub.confirmed = True
        sub.confirmed_at = timezone.now()
        sub.save(update_fields=["confirmed", "confirmed_at"])
    return render(request, "home/newsletter_confirmed.html", {"subscriber": sub})


def newsletter_unsubscribe(request, token):
    sub = get_object_or_404(NewsletterSubscriber, unsubscribe_token=token)
    if not sub.unsubscribed:
        sub.unsubscribed = True
        sub.confirmed = False
        sub.save(update_fields=["unsubscribed", "confirmed"])
    return render(request, "home/newsletter_unsubscribed.html", {"subscriber": sub})
