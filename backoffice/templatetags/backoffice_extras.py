from django import template

register = template.Library()

# Bootstrap badge-färger per status
STATUS_BADGES = {
    "pending":   "secondary",
    "paid":      "success",
    "processing":"info",
    "shipped":   "primary",
    "refunded":  "danger",
    "cancelled": "dark",
}

@register.filter
def status_badge(status: str) -> str:
    """Returnerar bootstrap badge-klass för en orderstatus."""
    return STATUS_BADGES.get((status or "").lower(), "secondary")

@register.filter
def capfirst(s: str) -> str:
    return (s or "").capitalize()
