from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def currency(value):
    try:
        amount = f"{value:,.2f}".replace(",", " ").replace(".", ",")  # sv stil
        return f"{amount}\u00A0SEK"  # NBSP
    except Exception:
        return f"{value} SEK"

