# app/templatetags/form_tags.py
from django import template
from django.utils.safestring import mark_safe
from django.forms.boundfield import BoundField
import re

register = template.Library()
# templatetags/extras.py
from django import template
register = template.Library()

def _render_with_attrs(bound_field: BoundField, extra: dict) -> str:
    """Render a BoundField with extra widget attrs, without mutating the global widget."""
    return bound_field.as_widget(attrs=extra)

def _ensure_attr_in_html(html: str, key: str, val: str) -> str:
    """
    Insert or merge an attribute into the first HTML tag of the rendered field.
    - If attribute exists, append/merge (special-care for class).
    - Else, add it.
    """
    # opening tag like <input ...> or <textarea ...>
    m = re.search(r'^<([a-zA-Z0-9:_-]+)\s([^>]*)>', html)
    if not m:
        return html  # bail out safely

    tag, attrs = m.group(1), m.group(2)

    def replace_attr(attrs_str: str, k: str, v: str) -> str:
        # find existing attr
        pattern = re.compile(r'(?P<pre>\s|^)' + re.escape(k) + r'="(?P<val>[^"]*)"')
        if pattern.search(attrs_str):
            def _merge(mo):
                existing = mo.group('val')
                if k == 'class':
                    # merge classes uniquely-ish
                    existing_set = existing.split()
                    for token in v.split():
                        if token not in existing_set:
                            existing_set.append(token)
                    merged = " ".join(existing_set)
                    return f'{mo.group("pre")}{k}="{merged}"'
                else:
                    # overwrite by default for other attrs
                    return f'{mo.group("pre")}{k}="{v}"'
            return pattern.sub(_merge, attrs_str, count=1)
        else:
            # add new attr at end
            sep = '' if attrs_str.endswith(' ') else ' '
            return attrs_str + f'{sep}{k}="{v}"'

    new_attrs = replace_attr(attrs, key, val)
    return re.sub(r'^<([a-zA-Z0-9:_-]+)\s([^>]*)>',
                  f'<{tag} {new_attrs}>',
                  html, count=1)

@register.filter
def add_class(field, css):
    """
    Add one or more classes to a field.
    Works with BoundField or rendered HTML string.
    """
    if isinstance(field, BoundField):
        # Merge with any class the widget already has
        existing = field.field.widget.attrs.get('class', '')
        merged = (existing + ' ' + css).strip()
        return mark_safe(_render_with_attrs(field, {'class': merged}))
    # already rendered HTML
    return mark_safe(_ensure_attr_in_html(str(field), 'class', css))

@register.filter(name="attr")
def attr(field, arg):
    """
    Set a single attribute: {{ field|attr:"placeholder:Title" }}
    Works with BoundField or rendered HTML string.
    """
    try:
        key, val = arg.split(":", 1)
    except ValueError:
        return field
    if isinstance(field, BoundField):
        return mark_safe(_render_with_attrs(field, {key.strip(): val.strip()}))
    return mark_safe(_ensure_attr_in_html(str(field), key.strip(), val.strip()))

@register.filter(name="attrs")
def attrs(field, arg):
    """
    Set multiple attributes: {{ field|attrs:"id:id_title, maxlength:60, placeholder:Title" }}
    Works with BoundField or rendered HTML string.
    """
    parts = [p.strip() for p in str(arg).split(",") if ":" in p]
    kv = {}
    for p in parts:
        k, v = p.split(":", 1)
        kv[k.strip()] = v.strip()

    if isinstance(field, BoundField):
        return mark_safe(_render_with_attrs(field, kv))

    html = str(field)
    for k, v in kv.items():
        html = _ensure_attr_in_html(html, k, v)
    return mark_safe(html)
