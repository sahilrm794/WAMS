#!/usr/bin/env bash
set -o errexit

# Ensure the project directory is writable (SQLite DB lives here on hobby tier)
mkdir -p /opt/render/project/src

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py create_admin
python manage.py seed_data
