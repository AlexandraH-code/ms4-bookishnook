from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def currency(value):
    """
    Format Decimal/float till pris med tusentalsavgränsning + ' SEK'.
    Exempel:
        {{ 1299.5|currency }}  -> '1 299.50 SEK'
    """
    try:
        dec = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return f"{value} SEK"

    # Format: tusentalsavgränsning med mellanslag och två decimaler
    formatted = f"{dec:,.2f}".replace(",", " ").replace(".", ",")
    # Byt tillbaka punkt som decimaltecken om du vill (svenska brukar ha komma):
    # formatted = f"{dec:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} SEK"
