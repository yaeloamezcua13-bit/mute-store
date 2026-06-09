"""Lista de países para el selector de envío. México primero (envío gratis)."""
from django.utils.translation import gettext_lazy as _

COUNTRIES = [
    ("MX", _("México")),
    ("US", _("Estados Unidos")),
    ("CA", _("Canadá")),
    ("AR", _("Argentina")),
    ("BO", _("Bolivia")),
    ("BR", _("Brasil")),
    ("CL", _("Chile")),
    ("CO", _("Colombia")),
    ("CR", _("Costa Rica")),
    ("CU", _("Cuba")),
    ("DO", _("República Dominicana")),
    ("EC", _("Ecuador")),
    ("SV", _("El Salvador")),
    ("GT", _("Guatemala")),
    ("HN", _("Honduras")),
    ("NI", _("Nicaragua")),
    ("PA", _("Panamá")),
    ("PY", _("Paraguay")),
    ("PE", _("Perú")),
    ("PR", _("Puerto Rico")),
    ("UY", _("Uruguay")),
    ("VE", _("Venezuela")),
    ("ES", _("España")),
    ("FR", _("Francia")),
    ("DE", _("Alemania")),
    ("IT", _("Italia")),
    ("GB", _("Reino Unido")),
    ("PT", _("Portugal")),
    ("NL", _("Países Bajos")),
    ("JP", _("Japón")),
    ("CN", _("China")),
    ("AU", _("Australia")),
    ("OTHER", _("Otro país")),
]

COUNTRY_DICT = dict(COUNTRIES)


def country_name(code):
    return str(COUNTRY_DICT.get((code or "").upper(), _("Otro país")))
