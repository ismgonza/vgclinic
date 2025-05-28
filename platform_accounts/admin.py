# platform_accounts/admin.py
from django.contrib import admin
from .models import Account, AccountOwner, AccountUser, AccountAuthorization, AccountInvitation, RolePermission

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'account_email', 'account_status', 'is_platform_account', 'account_created_at')
    list_filter = ('account_status', 'is_platform_account')
    search_fields = ('account_name', 'account_email')
    date_hierarchy = 'account_created_at'

@admin.register(AccountOwner)
class AccountOwnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'account', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'account__account_name')
    date_hierarchy = 'created_at'

@admin.register(AccountUser)
class AccountUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'account', 'role', 'specialty', 'is_active_in_account', 'created_at')
    list_filter = ('role', 'is_active_in_account', 'specialty', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'account__account_name')
    date_hierarchy = 'created_at'
    
@admin.register(AccountAuthorization)
class AccountAuthorizationAdmin(admin.ModelAdmin):
    list_display = ('user', 'account', 'authorization_type', 'get_auth_display', 'granted_by', 'is_active', 'granted_at', 'expires_at')
    list_filter = ('authorization_type', 'is_active', 'granted_at', 'account')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'account__account_name')
    ordering = ('-granted_at',)
    
    fieldsets = (
        ('Authorization Details', {
            'fields': ('user', 'account', 'authorization_type')
        }),
        ('Grant Information', {
            'fields': ('granted_by', 'is_active', 'expires_at')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Show all authorizations for superusers
        if request.user.is_superuser:
            return qs
        
        # For non-superusers, only show authorizations for accounts they own
        from .models import AccountOwner
        owned_accounts = AccountOwner.objects.filter(
            user=request.user, 
            is_active=True
        ).values_list('account', flat=True)
        
        return qs.filter(account__account_id__in=owned_accounts)
    
    def save_model(self, request, obj, form, change):
        # Auto-set granted_by to current user if not set
        if not change or not obj.granted_by:
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)

    def get_auth_display(self, obj):
        return obj.get_authorization_type_display()
    get_auth_display.short_description = 'Permission Name'
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Individual User Permissions'
        return super().changelist_view(request, extra_context)

@admin.register(AccountInvitation)
class AccountInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'account', 'role', 'status', 'invited_by', 'created_at', 'expires_at', 'is_valid_status')
    list_filter = ('status', 'role', 'created_at', 'expires_at')
    search_fields = ('email', 'account__account_name', 'invited_by__email')
    ordering = ('-created_at',)
    readonly_fields = ('token', 'created_at', 'accepted_at', 'accepted_by', 'is_valid_status', 'acceptance_url')
    
    fieldsets = (
        ('Invitation Details', {
            'fields': ('email', 'account', 'role', 'specialty')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'invited_by', 'created_at', 'expires_at', 'accepted_at', 'accepted_by')
        }),
        ('Security', {
            'fields': ('token', 'acceptance_url'),
            'classes': ('collapse',)
        }),
        ('Messages & Notes', {
            'fields': ('personal_message', 'notes'),
            'classes': ('collapse',)
        }),
    )
    
    def is_valid_status(self, obj):
        """Display if invitation is currently valid."""
        if obj.is_valid():
            return "✅ Valid"
        elif obj.is_expired():
            return "⏰ Expired"
        else:
            return f"❌ {obj.get_status_display()}"
    is_valid_status.short_description = "Valid"
    
    def acceptance_url(self, obj):
        """Display the acceptance URL for copying."""
        if obj.token:
            return obj.get_acceptance_url()
        return "-"
    acceptance_url.short_description = "Acceptance URL"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Show all invitations for superusers
        if request.user.is_superuser:
            return qs
        
        # For non-superusers, only show invitations for accounts they own or manage
        from .models import AccountOwner, AccountUser
        owned_accounts = AccountOwner.objects.filter(
            user=request.user, 
            is_active=True
        ).values_list('account', flat=True)
        
        # Also include accounts where user can invite users
        authorized_accounts = []
        for account_user in AccountUser.objects.filter(user=request.user, is_active_in_account=True):
            if account_user.has_authorization('invite_users'):
                authorized_accounts.append(account_user.account.account_id)
        
        all_account_ids = list(owned_accounts) + authorized_accounts
        return qs.filter(account__account_id__in=all_account_ids)
    
    def save_model(self, request, obj, form, change):
        # Auto-set invited_by to current user if not set
        if not change or not obj.invited_by:
            obj.invited_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_revoked', 'mark_as_expired']
    
    def mark_as_revoked(self, request, queryset):
        """Admin action to revoke selected invitations."""
        count = queryset.filter(status='pending').count()
        queryset.filter(status='pending').update(status='revoked')
        self.message_user(request, f'{count} invitations were revoked.')
    mark_as_revoked.short_description = "Revoke selected invitations"
    
    def mark_as_expired(self, request, queryset):
        """Admin action to expire selected invitations."""
        count = queryset.filter(status='pending').count()
        queryset.filter(status='pending').update(status='expired')
        self.message_user(request, f'{count} invitations were marked as expired.')
    mark_as_expired.short_description = "Mark selected invitations as expired"
    
@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'get_permission_display', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['permission_type']
    ordering = ['role', 'permission_type']
    
    def get_permission_display(self, obj):
        """Display the permission type with proper formatting."""
        # Get the display name from the centralized registry
        from .permissions import PERMISSION_REGISTRY
        
        # Search through all categories for this permission
        for category_data in PERMISSION_REGISTRY.values():
            if obj.permission_type in category_data['permissions']:
                return category_data['permissions'][obj.permission_type]
        
        # Fallback to the permission key if not found
        return obj.permission_type.replace('_', ' ').title()
    
    get_permission_display.short_description = 'Permission'
    get_permission_display.admin_order_field = 'permission_type'


from django import forms

class RolePermissionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set choices dynamically from centralized registry
        from .permissions import get_all_permissions
        self.fields['permission_type'].widget = forms.Select(choices=get_all_permissions())
    
    class Meta:
        model = RolePermission
        fields = '__all__'

class AccountAuthorizationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set choices dynamically from centralized registry
        from .permissions import get_all_permissions
        self.fields['authorization_type'].widget = forms.Select(choices=get_all_permissions())
    
    class Meta:
        model = AccountAuthorization
        fields = '__all__'

# Update the admin classes to use the forms:
RolePermissionAdmin.form = RolePermissionForm
AccountAuthorizationAdmin.form = AccountAuthorizationForm