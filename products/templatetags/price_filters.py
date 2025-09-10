from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def currency(value):
    """
    Format Decimal/float till pris med tusentalsavgränsning + ' kr'.
    Exempel:
        {{ 1299.5|currency }}  -> '1 299.50 kr'
    """
    try:
        dec = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return f"{value} kr"

    # Format: tusentalsavgränsning med mellanslag och två decimaler
    formatted = f"{dec:,.2f}".replace(",", " ").replace(".", ",")
    # Byt tillbaka punkt som decimaltecken om du vill (svenska brukar ha komma):
    # formatted = f"{dec:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} kr"
