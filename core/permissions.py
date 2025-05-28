# core/permissions.py
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from platform_accounts.models import Account, AccountUser, AccountOwner

class AccountPermissionMixin:
    """
    Mixin to handle account context and permission checking.
    Use this in your ViewSets to avoid code repetition.
    """
    
    def get_account_context(self):
        """Get and validate account context from request header"""
        account_id = self.request.headers.get('X-Account-Context')
        
        if not account_id:
            return None
            
        try:
            account = Account.objects.get(account_id=account_id)
            
            # Check if user has access (unless they're staff/superuser)
            if self.request.user.is_staff or self.request.user.is_superuser:
                return account
            else:
                # Check if user is a member of this account
                if AccountUser.objects.filter(
                    user=self.request.user,
                    account=account,
                    is_active_in_account=True
                ).exists():
                    return account
                    
            return None
        except Account.DoesNotExist:
            return None
    
    def check_permission(self, permission_type, account=None):
        """
        Check if user has permission using the unified method.
        """
        if not account:
            account = self.get_account_context()
            
        if not account:
            return False
            
        # Staff/superuser always have access
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
            
        # Use the unified permission check method
        return AccountUser.user_has_permission(
            self.request.user, 
            account, 
            permission_type
        )
    
    def require_permission(self, permission_type, account=None):
        """
        Require specific permission or return 403 error.
        Use this in view methods to enforce permissions.
        """
        if not self.check_permission(permission_type, account):
            return Response(
                {'error': f'Permission denied. Required permission: {permission_type}'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return None
    
    def get_user_role_in_account(self, account=None):
        """Get the user's role in the account."""
        if not account:
            account = self.get_account_context()
            
        if not account:
            return None
            
        try:
            account_user = AccountUser.objects.get(
                user=self.request.user,
                account=account,
                is_active_in_account=True
            )
            return account_user.role
        except AccountUser.DoesNotExist:
            return None
    
    def is_account_owner(self, account=None):
        """Check if current user is an owner of the account."""
        if not account:
            account = self.get_account_context()
            
        if not account:
            return False
            
        return AccountOwner.objects.filter(
            user=self.request.user,
            account=account,
            is_active=True
        ).exists()
    
    def get_user_accounts_queryset(self):
        """Get queryset of accounts the user has access to."""
        if self.request.user.is_superuser:
            return Account.objects.all()
            
        return Account.objects.filter(
            models.Q(owners__user=self.request.user, owners__is_active=True) |
            models.Q(members__user=self.request.user, members__is_active_in_account=True)
        ).distinct()
        
class PatientAccessMixin:
    """
    Mixin specifically for patient access control.
    Handles doctor-specific patient filtering.
    """
    
    def get_accessible_patients_queryset(self, base_queryset, account):
        """
        Filter patients based on role and permissions.
        - Owners: See all patients
        - Others: Based on role defaults + individual permissions
        """
        # Owners see all patients in account
        if self.is_account_owner(account):
            return base_queryset
            
        user_role = self.get_user_role_in_account(account)
        
        # Doctors only see patients from their active treatments (unless they have manage_patient_basic)
        if user_role == 'doc' and not self.check_permission('manage_patient_basic', account):
            from clinic_treatments.models import Treatment
            
            # Get patients from active treatments assigned to this doctor
            doctor_patients = Treatment.objects.filter(
                doctor__user=self.request.user,
                doctor__account=account,
                status__in=['scheduled', 'in_progress', 'completed']  # Adjust statuses as needed
            ).values_list('patient', flat=True).distinct()
            
            return base_queryset.filter(id__in=doctor_patients)
        
        # All other roles with view_patients_list permission see all patients
        if self.check_permission('view_patients_list', account):
            return base_queryset
            
        # No access
        return base_queryset.none()
    
    def can_view_patient_detail(self, account=None):
        """Check if user can access individual patient details."""
        return self.check_permission('view_patient_detail', account)
    
    def can_access_patient_history(self, account=None):
        """Check if user can access sensitive patient history."""
        return self.check_permission('view_patient_history', account)
    
    def can_manage_patient_basic(self, account=None):
        """Check if user can create/edit basic patient info."""
        return self.check_permission('manage_patient_basic', account)
    
    def can_manage_patient_history(self, account=None):
        """Check if user can create/edit patient medical history."""
        return self.check_permission('manage_patient_history', account)