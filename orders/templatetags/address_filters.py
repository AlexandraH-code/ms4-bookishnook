from django import template
register = template.Library()

COUNTRY_NAMES = {
    "SE": "Sweden",
    "NO": "Norway",
    "FI": "Finland",
    "DK": "Denmark",
    "DE": "Germany",
    # fyll på vid behov
}

@register.filter
def country_name(code):
    return COUNTRY_NAMES.get((code or "").upper(), code or "")
