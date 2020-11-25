from django import template


register = template.Library()


#(name='print_tag_eds_01')
@register.filter
def print_tag_eds_01(file):
    try:
        return 'useing filter: ' + file #file.read()
    except :
        return 'error'
