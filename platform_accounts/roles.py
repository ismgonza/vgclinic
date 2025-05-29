# platform_accounts/roles.py - CORRECT Python version
from django.utils.translation import gettext_lazy as _

class AccountRoles:
    """Centralized role definitions for the platform"""
    
    # Role codes
    ADMINISTRATOR = 'adm'
    DOCTOR = 'doc'
    ASSISTANT = 'ast'
    READ_ONLY = 'rdo'
    CUSTOM = 'cus'
    
    # Role choices for Django models
    ROLE_CHOICES = [
        (ADMINISTRATOR, _('Administrator')),
        (DOCTOR, _('Doctor')),
        (ASSISTANT, _('Assistant')),
        (READ_ONLY, _('Read Only')),
        (CUSTOM, _('Custom')),
    ]
    
    # Role display names (for API serialization)
    ROLE_DISPLAY_NAMES = {
        ADMINISTRATOR: 'Administrator',
        DOCTOR: 'Doctor',
        ASSISTANT: 'Assistant',
        READ_ONLY: 'Read Only',
        CUSTOM: 'Custom',
    }
    
    # Role badge colors for frontend
    ROLE_COLORS = {
        ADMINISTRATOR: '#dc3545',  # danger/red
        DOCTOR: '#0d6efd',        # primary/blue
        ASSISTANT: '#0dcaf0',     # info/cyan
        READ_ONLY: '#6c757d',     # secondary/gray
        CUSTOM: '#ffc107',        # warning/yellow
    }
    
    # All role codes as a list
    ALL_ROLES = [ADMINISTRATOR, DOCTOR, ASSISTANT, READ_ONLY, CUSTOM]
    
    @classmethod
    def get_role_display(cls, role_code):
        """Get the display name for a role code"""
        return cls.ROLE_DISPLAY_NAMES.get(role_code, role_code)
    
    @classmethod
    def get_role_color(cls, role_code):
        """Get the color for a role code"""
        return cls.ROLE_COLORS.get(role_code, cls.ROLE_COLORS[cls.READ_ONLY])
    
    @classmethod
    def is_valid_role(cls, role_code):
        """Check if a role code is valid"""
        return role_code in cls.ALL_ROLES
    
    @classmethod
    def get_roles_for_api(cls):
        """Get roles formatted for API responses"""
        return [
            {
                'code': code,
                'display': display,
                'color': cls.get_role_color(code)
            }
            for code, display in cls.ROLE_CHOICES
        ]