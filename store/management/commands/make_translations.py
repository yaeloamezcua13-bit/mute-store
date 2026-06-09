"""
Compila el catálogo de traducción ES->EN a locale/en/LC_MESSAGES/django.mo
sin necesitar gettext/msgfmt (compilador .mo en Python puro).

    python manage.py make_translations
"""
import struct

from django.conf import settings
from django.core.management.base import BaseCommand

# msgid (español, texto fuente) -> msgstr (inglés)
CATALOG = {
    # --- barra / nav / footer (base.html) ---
    "ENVÍO GRATIS EN TODO MÉXICO 🇲🇽": "FREE SHIPPING ACROSS MEXICO 🇲🇽",
    "LOGO BORDADO · TELA PREMIUM": "EMBROIDERED LOGO · PREMIUM FABRIC",
    "HECHOS PARA DURAR": "MADE TO LAST",
    "Productos": "Products",
    "Calidad": "Quality",
    "Idioma": "Language",
    "Tu carrito": "Your cart",
    "Subtotal": "Subtotal",
    "IVA incluido · Envío calculado en el checkout": "VAT included · Shipping calculated at checkout",
    "Finalizar compra": "Checkout",
    "Tu carrito está vacío": "Your cart is empty",
    "Ver productos": "Shop products",
    "Streetwear premium. Tela pesada, logo bordado, hechos para durar.":
        "Premium streetwear. Heavyweight fabric, embroidered logo, made to last.",
    "Atención a clientes": "Customer service",
    "Llamar:": "Call:",
    "Síguenos": "Follow us",
    "Envíos": "Shipping",
    "México:": "Mexico:",
    "Gratis": "Free",
    "Internacional:": "International:",
    "Todos los derechos reservados.": "All rights reserved.",
    "Precios en MXN · IVA incluido": "Prices in MXN · VAT included",
    # --- home ---
    "Vístete en silencio": "Dress in silence",
    "DESLIZA": "SCROLL",
    "La colección": "The collection",
    "Elige tu pieza": "Choose your piece",
    "Cada pieza, hecha con la misma obsesión por el detalle. Precios en MXN, IVA incluido.":
        "Every piece, made with the same obsession for detail. Prices in MXN, VAT included.",
    "Ver": "View",
    "CALIDAD MUTE": "MUTE QUALITY",
    "Desliza para descubrir cada detalle: la tela, el logo, la capucha, los puños. Esto es lo que no se ve en la foto.":
        "Scroll to discover every detail: the fabric, the logo, the hood, the cuffs. This is what the photo doesn't show.",
    "Comprar": "Buy",
    "Envío gratis en México": "Free shipping in Mexico",
    "A todo el país, sin mínimo de compra.": "Nationwide, no minimum purchase.",
    "380 g/m², interior afelpado, logo bordado.": "380 g/m², brushed interior, embroidered logo.",
    "Pago seguro": "Secure payment",
    "Stripe y MercadoPago. Tus datos protegidos.": "Stripe and MercadoPago. Your data protected.",
    "Atención directa": "Direct support",
    "DESLIZA / SCROLL →": "SCROLL →",
    # --- producto ---
    "IVA incluido": "VAT included",
    "de IVA": "VAT",
    "Talla": "Size",
    "Selecciona color y talla": "Select color and size",
    "Selecciona una talla": "Select a size",
    "Agregar al carrito": "Add to cart",
    "Tela:": "Fabric:",
    "Envío:": "Shipping:",
    "Gratis en México · $300 MXN internacional": "Free in Mexico · $300 MXN international",
    "¿Dudas?": "Questions?",
    "Cada detalle importa": "Every detail matters",
    "Desliza para recorrer el": "Scroll through the",
    "por dentro: la tela, el logo, la capucha, los puños.":
        "inside out: the fabric, the logo, the hood, the cuffs.",
    "También te puede gustar": "You may also like",
    "Completa tu look": "Complete your look",
    # --- JS (carrito / tallas) ---
    "Disponible ✓": "Available ✓",
    "¡Solo quedan {n}!": "Only {n} left!",
    "Agregando...": "Adding...",
    "¡Agregado! ✓": "Added! ✓",
    "Error, intenta de nuevo": "Error, try again",
    "Quitar": "Remove",
    # --- categorías ---
    "Hoodie Essentials": "Essentials Hoodie",
    "Playera Essentials": "Essentials Tee",
    # --- nombres de producto ---
    "Hoodie Essentials · Negra": "Essentials Hoodie · Black",
    "Hoodie Essentials · Gris": "Essentials Hoodie · Grey",
    "Hoodie Essentials · Blanca": "Essentials Hoodie · White",
    "Playera Essentials · Negra": "Essentials Tee · Black",
    "Playera Essentials · Gris": "Essentials Tee · Grey",
    "Playera Essentials · Blanca": "Essentials Tee · White",
    # --- colores ---
    "Negra": "Black",
    "Gris": "Grey",
    "Blanca": "White",
    # --- badges ---
    "Nuevo": "New",
    # --- descripciones ---
    "El hoodie insignia de MUTE. Tela pesada con caída estructurada, capucha forrada y logo bordado. Hecho para durar años.":
        "MUTE's flagship hoodie. Heavyweight fabric with a structured drape, lined hood and embroidered logo. Built to last for years.",
    "La sudadera de cuello redondo de MUTE en navy profundo. Misma tela premium del hoodie, en silueta limpia y atemporal.":
        "MUTE's crew-neck sweatshirt in deep navy. The same premium fabric as the hoodie, in a clean, timeless silhouette.",
    "El básico esencial: cómodo, versátil y a buen precio. El hoodie de diario que combina con todo.":
        "The essential basic: comfortable, versatile and well priced. The everyday hoodie that goes with everything.",
    "La playera esencial de MUTE. Algodón con cuerpo, corte regular y cuello que no se vence.":
        "MUTE's essential tee. Cotton with body, a regular fit and a collar that holds its shape.",
    # --- telas ---
    "Algodón peinado 380 g/m², interior french terry afelpado.":
        "Combed cotton 380 g/m², brushed french terry interior.",
    "Algodón peinado 380 g/m², interior afelpado.": "Combed cotton 380 g/m², brushed interior.",
    "Algodón/poliéster 320 g/m², interior suave.": "Cotton/polyester 320 g/m², soft interior.",
    "100% algodón 220 g/m², peso medio.": "100% cotton 220 g/m², medium weight.",
    # --- features (títulos) ---
    "Tela premium": "Premium fabric",
    "Logo bordado": "Embroidered logo",
    "Capucha forrada": "Lined hood",
    "Puños y cintura tejidos": "Ribbed cuffs and hem",
    "Bolsillo canguro": "Kangaroo pocket",
    "Cuello redondo reforzado": "Reinforced crew neck",
    "Tela peso medio": "Medium-weight fabric",
    "Cuello reforzado": "Reinforced collar",
    "Corte regular": "Regular fit",
    # --- features (descripciones) ---
    "Algodón peinado de 380 g/m² con interior afelpado (french terry). Suave, pesada y con caída estructurada.":
        "Combed cotton 380 g/m² with brushed interior (french terry). Soft, heavy and with a structured drape.",
    "Logotipo MUTE bordado a hilo, no estampado. Resiste cientos de lavadas sin desgastarse.":
        "MUTE logo thread-embroidered, not printed. Withstands hundreds of washes without wearing out.",
    "Capucha de doble capa con cordón de algodón grueso y ojales metálicos antióxido.":
        "Double-layer hood with a thick cotton drawcord and rustproof metal eyelets.",
    "Rib acanalado 2x2 en puños y bastilla que mantiene la forma y no se vence.":
        "2x2 ribbed knit at the cuffs and hem that keeps its shape and won't sag.",
    "Bolsillo frontal reforzado con costura doble y entrada amplia.":
        "Reinforced front pocket with double stitching and a wide opening.",
    "Algodón peinado de 380 g/m² con interior afelpado. Estructura firme y abrigadora.":
        "Combed cotton 380 g/m² with brushed interior. Firm and warm structure.",
    "Logotipo MUTE bordado en el pecho con acabado tonal.":
        "MUTE logo embroidered on the chest with a tonal finish.",
    "Cuello rib 2x2 con cinta de hombro a hombro para que no se deforme.":
        "2x2 ribbed collar with shoulder-to-shoulder tape so it won't lose shape.",
    "Acanalado elástico que recupera su forma.": "Elastic ribbing that bounces back into shape.",
    "Jersey 100% algodón de 220 g/m². Fresca, opaca y con cuerpo.":
        "100% cotton jersey 220 g/m². Cool, opaque and with body.",
    "Detalle MUTE bordado, acabado premium.": "Embroidered MUTE detail, premium finish.",
    "Cuello redondo con rib y costura doble que no se estira.":
        "Crew neck with ribbing and double stitching that won't stretch.",
    "Silueta recta moderna, ni muy holgada ni entallada.":
        "Modern straight silhouette, neither too loose nor too fitted.",
    # --- checkout ---
    "Completa tus datos. El envío se calcula automáticamente según tu país.":
        "Fill in your details. Shipping is calculated automatically based on your country.",
    "Contacto": "Contact",
    "Nombre completo": "Full name",
    "Correo electrónico": "Email",
    "Teléfono": "Phone",
    "Dirección": "Address",
    "Ciudad": "City",
    "Estado / Provincia": "State / Province",
    "País": "Country",
    "Código postal": "Postal code",
    "Dirección de envío": "Shipping address",
    "Método de pago": "Payment method",
    "⚙️ Modo de prueba activo. Configura tus llaves de Stripe/MercadoPago para cobrar de verdad. El pedido se guardará igual.":
        "⚙️ Test mode active. Set up your Stripe/MercadoPago keys to charge for real. The order will be saved anyway.",
    "💳 Tarjeta de crédito / débito": "💳 Credit / debit card",
    "Pago seguro con Stripe. Visa, Mastercard, Amex.": "Secure payment with Stripe. Visa, Mastercard, Amex.",
    "Tarjetas, OXXO, SPEI y saldo MercadoPago.": "Cards, OXXO, SPEI and MercadoPago balance.",
    "Tu pedido": "Your order",
    "(IVA incl.)": "(VAT incl.)",
    "↳ Base gravable": "↳ Taxable base",
    "↳ IVA": "↳ VAT",
    "Envío": "Shipping",
    "GRATIS": "FREE",
    "Total": "Total",
    "🇲🇽 ¡Envío gratis a México!": "🇲🇽 Free shipping to Mexico!",
    "Pagar ahora": "Pay now",
    "🔒 Pago seguro · Datos cifrados": "🔒 Secure payment · Encrypted data",
    "Redirigiendo al pago...": "Redirecting to payment...",
    "🌎 Envío internacional detectado: se agregaron {x} MXN al total.":
        "🌎 International shipping detected: {x} MXN added to the total.",
    "El código postal de México debe tener 5 dígitos.": "Mexican postal code must be 5 digits.",
    "Tu nombre": "Your name",
    "tucorreo@ejemplo.com": "youremail@example.com",
    "10 dígitos": "10 digits",
    "Calle, número, colonia": "Street, number, neighborhood",
    "Estado": "State",
    "Ej. 77500": "e.g. 77500",
    # --- confirmación ---
    "¡Gracias por tu compra!": "Thank you for your purchase!",
    "¡Gracias": "Thank you",
    "fue recibido.": "was received.",
    "Te enviamos la confirmación a": "We sent the confirmation to",
    "Modo de prueba:": "Test mode:",
    "este pedido se guardó en la base de datos pero no se cobró dinero real. Configura tus llaves de pago para procesar cobros.":
        "this order was saved to the database but no real money was charged. Set up your payment keys to process charges.",
    "Subtotal (IVA incl.)": "Subtotal (VAT incl.)",
    "↳ IVA incluido": "↳ VAT included",
    "Enviaremos a:": "We'll ship to:",
    "CP": "ZIP",
    "Seguir comprando": "Continue shopping",
    "Dudas por WhatsApp": "Questions via WhatsApp",
    # --- carrito (página) ---
    "Tu selección": "Your selection",
    "Carrito": "Cart",
    "Tu carrito está vacío.": "Your cart is empty.",
    "IVA incluido · Envío en el checkout": "VAT included · Shipping at checkout",
    # --- países (envío) ---
    "México": "Mexico",
    "Estados Unidos": "United States",
    "Canadá": "Canada",
    "Brasil": "Brazil",
    "República Dominicana": "Dominican Republic",
    "Panamá": "Panama",
    "Perú": "Peru",
    "España": "Spain",
    "Francia": "France",
    "Alemania": "Germany",
    "Italia": "Italy",
    "Reino Unido": "United Kingdom",
    "Países Bajos": "Netherlands",
    "Japón": "Japan",
    "Otro país": "Other country",
}


def compile_mo(catalog):
    """Genera bytes .mo (little-endian) legibles por gettext de Python."""
    items = sorted(catalog.items(), key=lambda kv: kv[0].encode("utf-8"))
    keys = b""
    vals = b""
    offsets = []
    for k, v in items:
        kb = k.encode("utf-8")
        vb = v.encode("utf-8")
        offsets.append((len(kb), len(keys), len(vb), len(vals)))
        keys += kb + b"\x00"
        vals += vb + b"\x00"
    n = len(items)
    keytable_off = 7 * 4
    valtable_off = keytable_off + n * 8
    keystart = valtable_off + n * 8
    valstart = keystart + len(keys)
    out = struct.pack("<7I", 0x950412DE, 0, n, keytable_off, valtable_off, 0, 0)
    for klen, koff, vlen, voff in offsets:
        out += struct.pack("<II", klen, keystart + koff)
    for klen, koff, vlen, voff in offsets:
        out += struct.pack("<II", vlen, valstart + voff)
    out += keys + vals
    return out


class Command(BaseCommand):
    help = "Compila el catálogo ES->EN a locale/en/LC_MESSAGES/django.mo"

    def handle(self, *args, **opts):
        catalog = dict(CATALOG)
        # entrada vacía con metadatos (charset)
        catalog[""] = "Content-Type: text/plain; charset=UTF-8\n"
        out_dir = settings.BASE_DIR / "locale" / "en" / "LC_MESSAGES"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "django.mo"
        path.write_bytes(compile_mo(catalog))
        self.stdout.write(self.style.SUCCESS(
            f"¡Listo! {len(CATALOG)} traducciones -> {path}"))
