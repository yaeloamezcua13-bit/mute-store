#!/usr/bin/env bash
# Render ejecuta esto en cada despliegue (build).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py bootstrap          # carga el catálogo si la BD está vacía
python manage.py normalize_sizes    # crea XS, elimina XL/XXL
