from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.simple_tag(takes_context=True)
def active(context, url_name, *args, **kwargs):
    """
    Usage: class="nav-link {% active 'products:list' %}"
    Mark as active if current path starts with the target URL.
    """
    try:
        url = reverse(url_name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return ''
    path = context['request'].path
    return 'active' if path.startswith(url) else ''
