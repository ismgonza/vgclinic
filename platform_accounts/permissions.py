# platform_accounts/permissions.py - Updated with Custom role support
from django.utils.translation import gettext_lazy as _
from .roles import AccountRoles

# Define all available permissions with categories
AVAILABLE_PERMISSIONS = [
    # Patient Management
    ('view_patients_list', _('View Patients List'), 'patient_management'),
    ('view_patients_detail', _('View Patient Details'), 'patient_management'),
    ('view_patients_history', _('View Patient History'), 'patient_management'),
    ('manage_patients_basic', _('Manage Basic Patient Info'), 'patient_management'),
    ('manage_patients_history', _('Manage Patient History'), 'patient_management'),
    
    # Treatment Management
    ('view_treatments_list', _('View Treatments List'), 'treatment_management'),
    ('view_treatments_detail', _('View Treatment Details'), 'treatment_management'),
    ('view_treatments_assigned', _('View Assigned Treatments'), 'treatment_management'),
    ('create_treatments', _('Create Treatments'), 'treatment_management'),
    ('edit_treatments', _('Edit Treatments'), 'treatment_management'),
    
    # Treatment History
    ('view_treatment_history_list', _('View Treatment History List'), 'treatment_management'),
    ('view_treatment_history_detail', _('View Treatment History Details'), 'treatment_management'),
    ('create_treatment_history', _('Create Treatment History'), 'treatment_management'),
    ('edit_treatment_history', _('Edit Treatment History'), 'treatment_management'),
    
    # Treatment Notes
    ('view_treatment_notes_list', _('View Treatment Notes List'), 'treatment_management'),
    ('view_treatment_notes_detail', _('View Treatment Notes Details'), 'treatment_management'),
    ('create_treatment_notes', _('Create Treatment Notes'), 'treatment_management'),
    ('edit_treatment_notes', _('Edit Treatment Notes'), 'treatment_management'),
    
    # Location Management
    ('view_locations_list', _('View Locations List'), 'location_management'),
    ('view_locations_detail', _('View Location Details'), 'location_management'),
    ('manage_locations', _('Manage Locations'), 'location_management'),
    ('view_rooms_list', _('View Rooms List'), 'location_management'),
    ('view_rooms_detail', _('View Room Details'), 'location_management'),
    ('manage_rooms', _('Manage Rooms'), 'location_management'),
    
    # Catalog Management
    ('view_specialties_list', _('View Specialties List'), 'catalog_management'),
    ('view_specialties_detail', _('View Specialty Details'), 'catalog_management'),
    ('manage_specialties', _('Manage Specialties'), 'catalog_management'),
    ('view_procedures_list', _('View Procedures List'), 'catalog_management'),
    ('view_procedures_detail', _('View Procedure Details'), 'catalog_management'),
    ('manage_procedures', _('Manage Procedures'), 'catalog_management'),
    
    # Team Management
    ('view_team_members_list', _('View Team Members List'), 'team_management'),
    ('view_team_members_detail', _('View Team Member Details'), 'team_management'),
    ('manage_team_members', _('Manage Team Members'), 'team_management'),
    ('view_invitations_list', _('View Invitations List'), 'team_management'),
    ('view_invitations_detail', _('View Invitation Details'), 'team_management'),
    ('manage_invitations', _('Manage Invitations'), 'team_management'),
    ('view_permissions_list', _('View Permissions List'), 'team_management'),
    ('view_permissions_detail', _('View Permission Details'), 'team_management'),
    ('manage_permissions', _('Manage Permissions'), 'team_management'),
    
    # Appointment Management
    ('view_appointments_list', _('View Appointments List'), 'appointment_management'),
    ('view_appointments_detail', _('View Appointment Details'), 'appointment_management'),
    ('view_appointments_assigned', _('View Assigned Appointments'), 'appointment_management'),
    ('manage_appointments', _('Manage Appointments'), 'appointment_management'),
    ('manage_schedule', _('Manage Schedule'), 'appointment_management'),
    
    # Billing Management
    ('view_billing_list', _('View Billing List'), 'billing_management'),
    ('view_billing_detail', _('View Billing Details'), 'billing_management'),
    ('manage_billing', _('Manage Billing'), 'billing_management'),
    ('view_financial_reports', _('View Financial Reports'), 'billing_management'),
    ('manage_pricing', _('Manage Pricing'), 'billing_management'),
    
    # Reporting & Analytics
    ('view_reports_list', _('View Reports List'), 'reporting_analytics'),
    ('view_reports_detail', _('View Report Details'), 'reporting_analytics'),
    ('view_analytics', _('View Analytics'), 'reporting_analytics'),
    ('export_reports', _('Export Reports'), 'reporting_analytics'),
]

# Permission categories for UI grouping
PERMISSION_CATEGORIES = {
    'patient_management': _('Patient Management'),
    'treatment_management': _('Treatment Management'),
    'location_management': _('Location Management'), 
    'catalog_management': _('Catalog Management'),
    'team_management': _('Team Management'),
    'appointment_management': _('Appointment Management'),
    'billing_management': _('Billing Management'),
    'reporting_analytics': _('Reporting & Analytics'),
}

# Default permissions for each role
DEFAULT_ROLE_PERMISSIONS = {
    AccountRoles.ADMINISTRATOR: [
        # Administrators have broad access
        'view_patients_list', 'view_patients_detail', 'manage_patients_basic',
        'view_treatments_list', 'view_treatments_detail', 'create_treatments', 'edit_treatments',
        'view_treatment_notes_list', 'view_treatment_notes_detail', 'create_treatment_notes', 'edit_treatment_notes',
        'view_locations_list', 'view_locations_detail', 'manage_locations',
        'view_rooms_list', 'view_rooms_detail', 'manage_rooms',
        'view_specialties_list', 'view_specialties_detail', 'manage_specialties',
        'view_procedures_list', 'view_procedures_detail', 'manage_procedures',
        'view_team_members_list', 'view_team_members_detail', 'manage_team_members',
        'view_invitations_list', 'view_invitations_detail', 'manage_invitations',
        'view_permissions_list', 'view_permissions_detail', 'manage_permissions',
        'view_appointments_list', 'view_appointments_detail', 'manage_appointments', 'manage_schedule',
        'view_billing_list', 'view_billing_detail', 'manage_billing', 'view_financial_reports', 'manage_pricing',
        'view_reports_list', 'view_reports_detail', 'view_analytics', 'export_reports',
    ],
    
    AccountRoles.DOCTOR: [
        # Doctors have clinical focus
        'view_patients_list', 'view_patients_detail', 'view_patients_history', 'manage_patients_basic', 'manage_patients_history',
        'view_treatments_list', 'view_treatments_detail', 'view_treatments_assigned', 'create_treatments', 'edit_treatments',
        'view_treatment_history_list', 'view_treatment_history_detail', 'create_treatment_history', 'edit_treatment_history',
        'view_treatment_notes_list', 'view_treatment_notes_detail', 'create_treatment_notes', 'edit_treatment_notes',
        'view_locations_list', 'view_locations_detail',
        'view_rooms_list', 'view_rooms_detail',
        'view_specialties_list', 'view_specialties_detail',
        'view_procedures_list', 'view_procedures_detail',
        'view_appointments_list', 'view_appointments_detail', 'view_appointments_assigned', 'manage_appointments',
        'view_billing_list', 'view_billing_detail',
    ],
    
    AccountRoles.ASSISTANT: [
        # Assistants have administrative support role
        'view_patients_list', 'view_patients_detail', 'manage_patients_basic',
        'view_treatments_list', 'view_treatments_detail', 'create_treatments',
        'view_treatment_notes_list', 'view_treatment_notes_detail', 'create_treatment_notes',
        'view_locations_list', 'view_locations_detail',
        'view_rooms_list', 'view_rooms_detail',
        'view_specialties_list', 'view_specialties_detail',
        'view_procedures_list', 'view_procedures_detail',
        'view_appointments_list', 'view_appointments_detail', 'manage_appointments',
        'view_billing_list', 'view_billing_detail', 'manage_billing',
    ],
    
    AccountRoles.READ_ONLY: [
        # Read-only users have view access only
        'view_patients_list', 'view_patients_detail',
        'view_treatments_list', 'view_treatments_detail',
        'view_treatment_notes_list', 'view_treatment_notes_detail',
        'view_locations_list', 'view_locations_detail',
        'view_rooms_list', 'view_rooms_detail',
        'view_specialties_list', 'view_specialties_detail',
        'view_procedures_list', 'view_procedures_detail',
        'view_appointments_list', 'view_appointments_detail',
        'view_billing_list', 'view_billing_detail',
        'view_reports_list', 'view_reports_detail',
    ],
    
    AccountRoles.CUSTOM: [
        # Custom roles start with no default permissions
        # All permissions must be individually assigned
    ],
}

def get_all_permissions():
    """Get all available permissions as choices for forms."""
    return [(perm[0], perm[1]) for perm in AVAILABLE_PERMISSIONS]

def get_permissions_by_category():
    """Get permissions grouped by category."""
    permissions_by_category = {}
    
    for perm_code, perm_name, category in AVAILABLE_PERMISSIONS:
        if category not in permissions_by_category:
            permissions_by_category[category] = []
        permissions_by_category[category].append((perm_code, perm_name))
    
    return permissions_by_category

def get_default_permissions_for_role(role_code):
    """Get default permissions for a specific role."""
    return DEFAULT_ROLE_PERMISSIONS.get(role_code, [])

def is_custom_role(role_code):
    """Check if the role is a custom role."""
    return role_code == AccountRoles.CUSTOM

def get_permission_display_name(permission_code):
    """Get the display name for a permission code."""
    for perm_code, perm_name, _ in AVAILABLE_PERMISSIONS:
        if perm_code == permission_code:
            return str(perm_name)  # Convert lazy translation to string
    return permission_code

def get_permission_category(permission_code):
    """Get the category for a permission code."""
    for perm_code, _, category in AVAILABLE_PERMISSIONS:
        if perm_code == permission_code:
            return category
    return 'other'