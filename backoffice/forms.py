from django import forms
from django.utils.text import slugify
from products.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["category", "name", "slug", "description", "price", "image", "is_active"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_slug(self):
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

