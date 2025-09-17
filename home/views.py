from django.shortcuts import render
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

    return render(request, "home/index.html", {"featured_categories": featured})