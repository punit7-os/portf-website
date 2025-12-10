# shop/templatetags/form_tags.py
from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(bound_field, css_class):
    """
    Usage in template:
      {{ form.somefield|add_class:"input-full" }}

    Adds or merges the CSS class to the form widget's attrs, returning the rendered widget HTML.
    This handles existing widget attrs by merging the 'class' attribute rather than overwriting.
    """
    try:
        # bound_field is a BoundField
        widget = bound_field.field.widget
        # copy existing widget attrs (if any)
        attrs = {}
        if hasattr(widget, "attrs") and widget.attrs:
            attrs.update(widget.attrs)

        existing = attrs.get("class", "")
        if existing:
            # avoid duplicate classes
            classes = existing.split()
            if css_class not in classes:
                classes.append(css_class)
            attrs["class"] = " ".join(classes)
        else:
            attrs["class"] = css_class

        return bound_field.as_widget(attrs=attrs)
    except Exception:
        # fallback: render the field as-is
        return bound_field
