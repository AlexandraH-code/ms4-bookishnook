from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from .forms import NewsletterForm, ContactForm
from .models import NewsletterSubscriber
from products.models import Category


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
        # eget, vänligt fel
        return JsonResponse({"ok": False, "error": "Please enter a valid email."}, status=400)

    email = form.cleaned_data["email"]
    sub, created = NewsletterSubscriber.objects.get_or_create(email=email)
    # Markera confirmed=True om du kör enkla varianten:
    if not sub.confirmed:
        sub.confirmed = True
        sub.save(update_fields=["confirmed"])

    return JsonResponse({
        "ok": True,
        "created": created,
        "already_confirmed": not created
    })