# platform_accounts/management/commands/setup_role_permissions.py

from django.core.management.base import BaseCommand
from platform_accounts.models import RolePermission
from platform_accounts.permissions import get_default_role_permissions

class Command(BaseCommand):
    help = 'Set up default role permissions'

    def handle(self, *args, **options):
        # Clear existing role permissions
        RolePermission.objects.all().delete()
        
        # Get role permissions from centralized registry
        role_permissions = get_default_role_permissions()
        
        # Create role permissions
        created_count = 0
        for role, permissions in role_permissions.items():
            for permission in permissions:
                RolePermission.objects.create(
                    role=role,
                    permission_type=permission,
                    is_active=True
                )
                created_count += 1
                self.stdout.write(f"Created {role} -> {permission}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully set up {created_count} role permissions')
        )