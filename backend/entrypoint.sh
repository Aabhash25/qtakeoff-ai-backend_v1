#!/bin/bash
echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser if not exists..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='administrator').exists():
    User.objects.create_superuser(
        username='administrator',
        email='admin@gmail.com',
        password='admin',
        first_name='admin',
        last_name='admin'
    )
EOF

echo "Starting server..."
exec "$@"
