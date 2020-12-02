from django import template


register = template.Library()

@register.simple_tag
def print_tag_eds_01(file):
    import codecs
    import os
    from nltest import settings

    try:
        BASE_DIR = settings.BASE_DIR
        sArray =file.split(':')
        sPath = os.path.join(BASE_DIR, sArray[0], 'templates', sArray[0], sArray[1])

        f = codecs.open(sPath, "r", "utf-8")
        return f.read()
        # return 'useing filter: ' + file #file.read()
    except Exception as e :
        return 'error: ' + str(e)




@register.filter
def filter_tag_eds_01(file):
    import codecs
    import os
    from nltest import settings

    try:
        BASE_DIR = settings.BASE_DIR
        sArray =file.split(':')
        sPath = os.path.join(BASE_DIR, sArray[0], 'templates', sArray[0], sArray[1])

        f = codecs.open(sPath, "r", "utf-8")
        return f.read()
        # return 'useing filter: ' + file #file.read()
    except Exception as e :
        return 'error: ' + str(e)
