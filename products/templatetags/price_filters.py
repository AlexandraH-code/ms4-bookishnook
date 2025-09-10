from django import template

register = template.Library()


@register.filter
def currency(value):
    """
    Format Decimal/float till pris med två decimaler + ' kr'.
    Exempel:
        {{ product.price|currency }}
    Output:
        129.00 kr
    """
    try:
        return f"{value:.2f} kr"
    except (ValueError, TypeError):
        return f"{value} kr"
