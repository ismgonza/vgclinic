# platform_accounts/urls.py
from django.urls import path
from .views import (
    AccountViewSet, 
    AccountUserViewSet, 
    AccountOwnerViewSet,
    AccountInvitationViewSet,
    InvitationAcceptanceView,
    AccountPermissionViewSet  # ADD THIS IMPORT
)

# Explicit patterns that WORK
urlpatterns = [
    # PUBLIC URLs FIRST (no auth required)
    path('accept-invitation/<str:token>/', InvitationAcceptanceView.as_view({
        'get': 'validate_token',
        'post': 'accept'
    }), name='accept-invitation-token'),
    path('accept-invitation/', InvitationAcceptanceView.as_view({
        'get': 'validate_token',
        'post': 'accept'
    }), name='accept-invitation'),
    
    # PERMISSIONS MANAGEMENT - ADD THESE NEW URLS
    path('permissions/available/', AccountPermissionViewSet.as_view({
        'get': 'available_permissions'
    }), name='permissions-available'),
    path('permissions/users/', AccountPermissionViewSet.as_view({
        'get': 'users_permissions'
    }), name='permissions-users'),
    path('permissions/update/', AccountPermissionViewSet.as_view({
        'post': 'update_user_permissions'
    }), name='permissions-update'),
    path('permissions/user/<int:user_id>/', AccountPermissionViewSet.as_view({
        'get': 'user_permissions'
    }), name='permissions-user-detail'),
    
    # ACCOUNT OWNERS
    path('owners/', AccountOwnerViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='owners-list'),
    path('owners/<int:pk>/', AccountOwnerViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='owners-detail'),
    
    # TEAM MEMBERS
    path('members/', AccountUserViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='members-list'),
    path('members/<int:pk>/', AccountUserViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='members-detail'),
    
    path('members/<int:pk>/deactivate/', AccountUserViewSet.as_view({
        'patch': 'deactivate'
    }), name='members-deactivate'),
    path('members/<int:pk>/reactivate/', AccountUserViewSet.as_view({
        'patch': 'reactivate'
    }), name='members-reactivate'),
    
    # INVITATIONS
    path('invitations/', AccountInvitationViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='invitations-list'),
    path('invitations/<int:pk>/', AccountInvitationViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='invitations-detail'),
    
    path('invitations/<int:pk>/resend/', AccountInvitationViewSet.as_view({
        'post': 'resend'
    }), name='invitations-resend'),
    path('invitations/<int:pk>/revoke/', AccountInvitationViewSet.as_view({
        'patch': 'revoke'
    }), name='invitations-revoke'),
    
    # BASE ACCOUNTS
    path('', AccountViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='accounts-list'),
    path('<str:pk>/', AccountViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='accounts-detail')
]