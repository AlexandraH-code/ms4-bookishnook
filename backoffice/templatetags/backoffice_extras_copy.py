from django import template

register = template.Library()

# Bootstrap badge-färger per status
STATUS_BADGES = {
    "pending":   "secondary",
    "paid":      "success",
    "processing": "info",
    "shipped":   "primary",
    "refunded":  "danger",
    "cancelled": "dark",
}

STATUS_ICONS = {
    "pending":   "fas fa-hourglass-half",   # pending
    "paid":      "fas fa-check-circle",     # paid
    "processing": "fas fa-cogs",             # processing
    "shipped":   "fas fa-truck",            # shipped
    "refunded":  "fas fa-undo",             # refunded
    "cancelled": "fas fa-times-circle",     # cancelled
}


@register.filter
def status_badge(status: str) -> str:
    """Returnerar bootstrap badge-klass för en orderstatus."""
    return STATUS_BADGES.get((status or "").lower(), "secondary")

@register.filter
def capfirst(s: str) -> str:
    return (s or "").capitalize()

@register.filter
def status_icon(status: str) -> str:
    """Returns the Font Awesome icon class for an order status."""
    return STATUS_ICONS.get((status or "").lower(), "fas fa-question-circle")
