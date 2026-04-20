#!/usr/bin/env bash
set -o errexit

# Unset any stale DB_PATH from previous disk-mount configs
unset DB_PATH

echo "=== Filesystem check ==="
pwd
ls -la
touch test_write && rm test_write && echo "CWD is WRITABLE" || echo "CWD is NOT writable"

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py create_admin
python manage.py seed_data
