# platform_accounts/urls.py - COMPLETE WORKING CONFIGURATION
from django.urls import path
from .views import (
    AccountViewSet, 
    AccountUserViewSet, 
    AccountOwnerViewSet,
    AccountInvitationViewSet,
    InvitationAcceptanceView
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
    
    # BASE ACCOUNTS
    path('', AccountViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='accounts-list'),
    path('<str:pk>/', AccountViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='accounts-detail'),
]