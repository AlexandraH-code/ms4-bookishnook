from django.db import models
from django.urls import reverse
from django.utils.text import slugify

"""
Product catalog models: Category (supports nesting) and Product.
"""


class Category(models.Model):
    """
    Hierarchical category for products.

    Fields:
        name (str): Display name.
        slug (str): URL-friendly identifier (unique within the same parent).
        parent (Category | None): Optional parent category to build a tree.
        is_active (bool): Hide/show in navigation and listings.
        is_featured (bool): Whether to highlight on the homepage.
        featured_order (int): Sort order for homepage featured slots (low first).
        description (str): Optional long text.
        image (ImageField): Optional category image.

    Uniqueness:
        (parent, slug) is unique so the same `slug` can appear under
        different parents.

    Helpful properties:
        - full_name: "Parent / Child / Leaf" display string.
        - slug_path: "parent/child/leaf" for URL patterns.

    Methods:
        descendant_ids(): Returns a flat list of this category's id plus
                          all descendants' ids (recursive).
    """

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
        unique_together = ("parent", "slug")  # the same slug can exist under different parents
        ordering = ["parent__id", "name"]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        """
        Return the full hierarchical display name, e.g. "Parent / Child / Leaf".
        """

        parts, c = [], self
        while c:
            parts.append(c.name)
            c = c.parent
        return " / ".join(reversed(parts))

    def save(self, *args, **kwargs):
        """
        Auto-generate a slug from `name` if not provided.
        """

        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    @property
    def slug_path(self):
        """
        Return the hierarchical slug path, e.g. "parent/child/leaf".
        """
        # e.g. "bookmarks/leather"
        parts, c = [], self
        while c:
            parts.append(c.slug)
            c = c.parent
        return "/".join(reversed(parts))

    def get_absolute_url(self):
        """
        URL to the category listing page for this node (including its descendants).
        """

        return f"/products/category/{self.slug_path}/"

    def descendant_ids(self):
        """
        Recursively collect this category's id and all descendant ids.

        Returns:
            list[int]: A flat list of category primary keys.
        """

        ids = [self.id]
        for child in self.children.all():
            ids.extend(child.descendant_ids())
        return ids


class Product(models.Model):
    """
    A sellable product that belongs to a Category.

    Fields:
        category (Category): The owning category (protected from deletion).
        name (str): Display name.
        slug (str): Unique URL slug. Auto-filled from `name` if blank.
        description (str): Optional long text.
        price (Decimal): Price (currency handled at display time).
        image (ImageField): Optional product image.
        is_active (bool): Whether the product is visible/purchasable.
        stock (int): Current stock on hand.
        created (datetime): Created timestamp.
        updated (datetime): Last updated timestamp.
    """

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
        """
        Auto-generate a unique slug from `name` if not provided.
        """

        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """
        URL to the product detail page.
        """

        return reverse("products:detail", args=[self.slug])
