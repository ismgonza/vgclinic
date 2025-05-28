# platform_accounts/permissions.py

from django.utils.translation import gettext_lazy as _

# Centralized permission registry
PERMISSION_REGISTRY = {
    # Patient Management
    'patient': {
        'name': _('Patient Management'),
        'permissions': {
            'view_patients_list': _('View Patients List'),
            'view_patient_detail': _('View Patient Detail'),
            'view_patient_history': _('View Patient History'),
            'manage_patient_basic': _('Manage Patient Basic Info'),
            'manage_patient_history': _('Manage Patient History'),
        }
    },
    
    # Treatment Management
    'treatment': {
        'name': _('Treatment Management'),
        'permissions': {
            'view_treatments': _('View Treatments'),
            'view_all_treatments': _('View All Treatments'),
            'manage_treatments': _('Manage Treatments'),
            'manage_treatment_notes': _('Manage Treatment Notes'),
        }
    },
    
    # Location & Catalog Management
    'catalog': {
        'name': _('Location & Catalog Management'),
        'permissions': {
            'view_catalog': _('View Catalog'),
            'manage_catalog': _('Manage Catalog'),
            'manage_locations': _('Manage Locations'),
            'manage_procedures': _('Manage Procedures'),
        }
    },
    
    # Team & Administration
    'team': {
        'name': _('Team & Administration'),
        'permissions': {
            'view_team': _('View Team'),
            'invite_users': _('Invite Users'),
            'manage_users': _('Manage Users'),
            'remove_users': _('Remove Users'),
            'manage_permissions': _('Manage Permissions'),
        }
    },
    
    # Appointments & Scheduling
    'appointments': {
        'name': _('Appointments & Scheduling'),
        'permissions': {
            'view_appointments': _('View Appointments'),
            'view_all_appointments': _('View All Appointments'),
            'manage_appointments': _('Manage Appointments'),
            'manage_schedule': _('Manage Schedule'),
        }
    },
    
    # Financial & Billing
    'billing': {
        'name': _('Financial & Billing'),
        'permissions': {
            'view_billing': _('View Billing'),
            'manage_billing': _('Manage Billing'),
            'view_financial_reports': _('View Financial Reports'),
            'manage_pricing': _('Manage Pricing'),
        }
    },
    
    # Reports & Analytics
    'reports': {
        'name': _('Reports & Analytics'),
        'permissions': {
            'view_reports': _('View Reports'),
            'view_analytics': _('View Analytics'),
            'export_reports': _('Export Reports'),
        }
    }
}

# Default role permissions - Easy to modify
DEFAULT_ROLE_PERMISSIONS = {
    'adm': [  # Administrator - Full clinic management
        # Patient permissions
        'view_patients_list',
        
        # Treatment permissions
        'view_all_treatments',
        
        # Catalog permissions
        'view_catalog',
        
        # Team permissions
        'view_team',
        
        # Appointment permissions
        'view_all_appointments',
        
        # Billing permissions
        'view_billing', 'view_financial_reports',
        
        # Report permissions
        'view_reports', 'view_analytics', 'export_reports',
    ],
    
    'doc': [  # Doctor - Clinical focus
        'view_patients_list', 'view_patient_detail', 'view_patient_history',
        'manage_patient_basic', 'manage_patient_history',
        'view_treatments', 'manage_treatments', 'manage_treatment_notes',
        'view_catalog', 'view_appointments', 'manage_appointments',
    ],
    
    'ast': [  # Assistant - Administrative support
        'view_patients_list', 'view_patient_detail', 'manage_patient_basic',
        'view_treatments', 'view_catalog',
        'view_appointments', 'manage_appointments', 'manage_schedule',
        'view_billing',
    ],
    
    'rdo': [  # Read Only - Very limited access
        'view_patients_list', 'view_patient_detail',
        'view_treatments', 'view_catalog', 'view_appointments',
    ]
}

def get_all_permissions():
    """Get flat list of all available permissions."""
    permissions = []
    for category_data in PERMISSION_REGISTRY.values():
        for perm_key, perm_name in category_data['permissions'].items():
            permissions.append((perm_key, perm_name))
    return permissions

def get_permissions_by_category():
    """Get permissions organized by category."""
    return PERMISSION_REGISTRY

def get_default_role_permissions(role=None):
    """Get default permissions for a role or all roles."""
    if role:
        return DEFAULT_ROLE_PERMISSIONS.get(role, [])
    return DEFAULT_ROLE_PERMISSIONS

def add_permission_category(category_key, category_name, permissions):
    """Dynamically add a new permission category."""
    PERMISSION_REGISTRY[category_key] = {
        'name': category_name,
        'permissions': permissions
    }

def add_permission_to_category(category_key, permission_key, permission_name):
    """Dynamically add a permission to an existing category."""
    if category_key in PERMISSION_REGISTRY:
        PERMISSION_REGISTRY[category_key]['permissions'][permission_key] = permission_name

def add_permission_to_role(role, permission_key):
    """Dynamically add a permission to a role's defaults."""
    if role in DEFAULT_ROLE_PERMISSIONS:
        if permission_key not in DEFAULT_ROLE_PERMISSIONS[role]:
            DEFAULT_ROLE_PERMISSIONS[role].append(permission_key)