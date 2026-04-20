import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create default admin user if none exists'

    def handle(self, *args, **options):
        from core.models import User
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        password = os.environ.get('ADMIN_PASSWORD', 'Admin@1234')
        email = os.environ.get('ADMIN_EMAIL', 'admin@wams.com')

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                password=password,
                email=email,
                role='admin',
            )
            self.stdout.write(self.style.SUCCESS(f'Admin user "{username}" created.'))
        else:
            self.stdout.write(f'Admin user "{username}" already exists.')
