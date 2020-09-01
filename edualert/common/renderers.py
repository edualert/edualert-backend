from rest_framework.renderers import JSONRenderer


class UTF8JSONRenderer(JSONRenderer):
    """
    JSON renderer which uses a utf-8 encoding.
    """
    charset = 'utf-8'
