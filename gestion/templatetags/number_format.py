from django import template

register = template.Library()

@register.filter
def short_number(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value

    if value >= 1_000_000:
        return f"{value/1_000_000:.2f}".rstrip('0').rstrip('.') + "M"
    elif value >= 1_000:
        return f"{value/1_000:.2f}".rstrip('0').rstrip('.') + "K"
    else:
        return f"{value:.0f}"