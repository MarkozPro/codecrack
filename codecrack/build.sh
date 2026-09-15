#!/usr/bin/env bash
# Salir si hay error
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Recolectar archivos estáticos
python manage.py collectstatic --no-input

# Migrar base de datos
python manage.py migrate

# Crear superusuario (opcional)
# python manage.py createsuperuser --noinput