"""Filtros de plantilla de MUTE."""
from django import template
from django.utils.translation import gettext

register = template.Library()


@register.filter(name="t")
def translate(value):
    """Traduce un texto (de plantilla o de BD) según el idioma activo.
    En español devuelve el mismo texto; en inglés, su traducción del catálogo."""
    if value is None:
        return ""
    return gettext(str(value))
