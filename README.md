# MUTE — Tienda en línea

Tienda de ropa premium (hoodies y playeras) con carrito, pagos, panel de
administración y base de datos automatizada de ventas. Construida con Django.

![Stack](https://img.shields.io/badge/Django-4.2-092E20) ![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB) ![Pagos](https://img.shields.io/badge/Pagos-Stripe%20%2B%20MercadoPago-635BFF)

## ✨ Características

- **Catálogo animado** con GSAP: hero, reveals al hacer scroll y un **showcase
  deslizable** donde el cliente recorre la prenda y descubre tela, logo,
  capucha, puños, etc.
- **Carrito lateral** (varios productos, color y talla) con actualización en vivo.
- **Checkout con desglose completo**: subtotal, base gravable, **IVA incluido (16%)**,
  envío y total.
- **Envío automático por país**: 🇲🇽 México **gratis**, internacional **$300 MXN**.
  Se detecta y se suma al total en tiempo real al elegir el país / código postal.
- **Pagos**: Stripe Checkout + MercadoPago Checkout Pro (con webhooks). Si no hay
  llaves, funciona en **modo simulado** para probar todo el flujo.
- **Base de datos de ventas automatizada**: cada pedido se guarda con cliente,
  dirección, importes, IVA, envío y estado.
- **Panel de administración** (Django Admin) para productos, inventario, colores,
  tallas y pedidos — con total vendido y filtros.
- **Correo de confirmación**, inventario por talla, **WhatsApp** flotante e Instagram.

## 🚀 Puesta en marcha (local)

```bash
cd mute-store

# 1. Entorno virtual (ya creado en ./venv) — actívalo o usa ./venv/bin/python
source venv/bin/activate          # macOS / Linux
# 2. Instalar dependencias (si hace falta)
pip install -r requirements.txt

# 3. Configura tus variables (opcional para probar)
cp .env.example .env

# 4. Base de datos + productos
python manage.py migrate
python manage.py seed_products

# 5. Arranca
python manage.py runserver
```

Abre **http://127.0.0.1:8000**

- Tienda: `/`
- Admin: `/admin/` → usuario **admin** / contraseña **mute2026**
  (cámbiala con `python manage.py changepassword admin`)

> Nota: el proyecto ya trae creados el entorno `venv/`, la base SQLite con
> productos y el usuario admin, así que puedes ir directo al paso 5.

## 🛒 Productos y precios

| Producto | Colores | Precio (MXN) |
|---|---|---|
| Hoodie Alo Accolade | Black, Navy, Espresso, Grey | $2,500 |
| Crewneck Navy | Navy | $2,000 |
| Hoodie Essentials | Negra, Gris, Blanca | $1,500 |
| Playera Essentials | Negra, Gris, Blanca | $1,200 |

Edítalos en el admin o en `store/management/commands/seed_products.py`.

## 💳 Activar pagos reales

Pega tus llaves en `.env` y reinicia. En cuanto existan, el modo simulado se apaga.

**Stripe** (https://dashboard.stripe.com/test/apikeys):
```
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...   # opcional, para confirmación robusta
```
Webhook → apunta a `/webhooks/stripe/` (evento `checkout.session.completed`).

**MercadoPago** (https://www.mercadopago.com.mx/developers/panel/app):
```
MERCADOPAGO_PUBLIC_KEY=APP_USR-...
MERCADOPAGO_ACCESS_TOKEN=APP_USR-...
```
Webhook → `/webhooks/mercadopago/`.

## 🖼️ Imágenes con nano banana (Gemini)

Las prendas se muestran con un placeholder elegante hasta que subas fotos
(reales en el admin, o generadas por IA):

```bash
export GEMINI_API_KEY=tu_llave        # https://aistudio.google.com/apikey
python manage.py generate_images               # todos los productos + colores
python manage.py generate_images --features    # + fotos de detalle (tela, logo...)
```

Las imágenes se generan **y se adjuntan solas** a cada producto/color. Para una
tienda real, recomendamos **fotos reales** de tu inventario (súbelas en el admin);
usa la IA para fondos, hero y mockups.

## 🐘 Cambiar a PostgreSQL (producción / enterprise)

Sin tocar el código: solo define `DATABASE_URL` en `.env`.

```bash
# 1. Instala PostgreSQL y crea la base
createdb mute
# 2. En .env:
DATABASE_URL=postgres://usuario:contrasena@localhost:5432/mute
# 3. Migra y siembra
python manage.py migrate
python manage.py seed_products
```

`psycopg2-binary` ya está en `requirements.txt`. Mismos modelos, mismo admin.

## 🌐 Despliegue (resumen)

1. `DEBUG=False`, define `SECRET_KEY`, `ALLOWED_HOSTS` y `SITE_URL`.
2. Usa PostgreSQL (`DATABASE_URL`).
3. `python manage.py collectstatic` (WhiteNoise ya sirve los estáticos).
4. Arranca con Gunicorn: `gunicorn config.wsgi`.
5. Configura los webhooks de pago con tu dominio real (https).

## 📁 Estructura

```
mute-store/
├── config/              # settings, urls, wsgi
├── store/               # app principal
│   ├── models.py        # Product, Color, Variant, Image, Feature, Order, OrderItem
│   ├── admin.py         # panel de administración
│   ├── views.py         # catálogo, carrito, checkout, webhooks
│   ├── cart.py          # carrito en sesión
│   ├── pricing.py       # IVA y envío
│   ├── payments.py      # Stripe + MercadoPago
│   ├── services.py      # crear pedido, marcar pagado, inventario, correo
│   └── management/commands/
│       ├── seed_products.py
│       └── generate_images.py   # nano banana / Gemini
├── templates/           # base, home, producto, carrito, checkout, confirmación
├── static/              # css/ js/ (animaciones, carrito, showcase, checkout)
└── requirements.txt
```

## 📞 Contacto de la tienda

- WhatsApp / Tel: **9988416700**
- Instagram: **@mut3.mx**
