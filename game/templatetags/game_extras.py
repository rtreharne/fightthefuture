from django import template

register = template.Library()


@register.filter
def get_item(value, key):
    if value is None:
        return ""
    try:
        return value.get(key, "")
    except AttributeError:
        return ""
