#!/usr/bin/env bash

# Activa el modo de salida inmediata ante errores
set -o errexit

# Instala las dependencias
pip install -r requirements.txt

# Recoge archivos estáticos
python manage.py collectstatic --no-input

# Ejecuta las migraciones de la base de datos
python manage.py migrate
