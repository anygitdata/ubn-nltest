from django import template
register = template.Library()

@register.filter
def my_anyfilter():
    return 'verifing string'
