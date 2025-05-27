# platform_accounts/admin.py
from django.contrib import admin
from .models import Account, AccountOwner, AccountUser, AccountAuthorization, AccountInvitation

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
    list_display = ('user', 'account', 'authorization_type', 'granted_by', 'is_active', 'expires_at', 'granted_at')
    list_filter = ('authorization_type', 'is_active', 'granted_at', 'expires_at')
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