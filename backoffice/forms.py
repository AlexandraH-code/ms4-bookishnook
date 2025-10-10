from django import forms
from django.utils.text import slugify
from products.models import Product

"""
Forms used in the Backoffice app for product administration.
"""


class ProductForm(forms.ModelForm):
    """
    Form for creating and editing `Product` instances.

    Fields:
        category, name, slug, description, price, image, is_active

    Behavior:
        - Automatically generates a slug from `name` if not provided.
        - Ensures the slug is unique, appending "-2", "-3", etc. if necessary.

    Used in:
        - backoffice.product_create
        - backoffice.product_edit
    """

    class Meta:
        model = Product
        fields = ["category", "name", "slug", "description", "price", "image", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_slug(self):
        """
        Validate and/or generate a unique slug for the product.

        Logic:
            - If no slug is entered, generate one using `slugify(name)`.
            - If the slug already exists, append "-2", "-3", etc. until unique.
            - During edit, the current instance is excluded from uniqueness checks.

        Returns:
            str: The final unique slug.
        """

        s = self.cleaned_data.get("slug") or slugify(self.cleaned_data.get("name") or "")
        if not s:
            raise forms.ValidationError("Slug could not be generated.")
        # Make sure the slug is unique
        qs = Product.objects.filter(slug=s)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        base = s
        i = 2
        while qs.exists():
            s = f"{base}-{i}"
            qs = Product.objects.filter(slug=s)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            i += 1
        return s
