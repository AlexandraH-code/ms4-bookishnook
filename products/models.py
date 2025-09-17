from django.db import models
from django.urls import reverse
from django.utils.text import slugify


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, unique=False)
    parent = models.ForeignKey(
        "self", null=True, blank=True,
        related_name="children", on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Show on homepage")
    featured_order = models.PositiveIntegerField(default=0, help_text="Order on homepage (low first)")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="category_images/", blank=True, null=True)

    class Meta:
        unique_together = ("parent", "slug")  # samma slug kan finnas under olika föräldrar
        ordering = ["parent__id", "name"]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        parts, c = [], self
        while c:
            parts.append(c.name)
            c = c.parent
        return " / ".join(reversed(parts))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    @property
    def slug_path(self):
        # t.ex. "bookmarks/leather"
        parts, c = [], self
        while c:
            parts.append(c.slug)
            c = c.parent
        return "/".join(reversed(parts))

    def get_absolute_url(self):
        return f"/products/category/{self.slug_path}/"

    def descendant_ids(self):
        ids = [self.id]
        for child in self.children.all():
            ids.extend(child.descendant_ids())
        return ids


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:detail", args=[self.slug])
