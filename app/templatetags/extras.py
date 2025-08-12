# templatetags/extras.py
from django import template
register = template.Library()

@register.filter
def getattribute(obj, name):
    return getattr(obj, name, "")
