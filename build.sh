#!/usr/bin/env bash
set -o errexit

# Ensure persistent disk directory exists before DB operations
mkdir -p /var/data

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py create_admin
python manage.py seed_data