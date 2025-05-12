from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * (1 + float(arg))  # arg zaten 100'e bölünmüş geliyor
    except (ValueError, TypeError):
        return 0 