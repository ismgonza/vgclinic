from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import Account, AccountUser, AccountInvitation
from .serializers import AccountSerializer, AccountUserSerializer, AccountInvitationSerializer
from .permissions import IsAccountOwnerOrAdmin, IsAccountMember


class AccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows accounts to be viewed or edited.
    """
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Users can only see accounts they are members of.
        Staff users can see all accounts.
        """
        user = self.request.user
        if user.is_staff:
            return Account.objects.all()
        return Account.objects.filter(members__user=user)
    
    def perform_create(self, serializer):
        # Set the current user as the owner
        serializer.save(owner=self.request.user)


class AccountUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows account users to be viewed or edited.
    """
    serializer_class = AccountUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMember]
    
    def get_queryset(self):
        """
        Filter account users based on the current user's permissions.
        """
        user = self.request.user
        account_id = self.request.query_params.get('account_id')
        
        if user.is_staff:
            queryset = AccountUser.objects.all()
        else:
            # Only show memberships for accounts the user belongs to
            queryset = AccountUser.objects.filter(account__members__user=user)
        
        if account_id:
            queryset = queryset.filter(account_id=account_id)
            
        return queryset


class AccountInvitationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows account invitations to be viewed or edited.
    """
    serializer_class = AccountInvitationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountOwnerOrAdmin]
    
    def get_queryset(self):
        """
        Filter invitations based on the current user's permissions.
        """
        user = self.request.user
        account_id = self.request.query_params.get('account_id')
        
        if user.is_staff:
            queryset = AccountInvitation.objects.all()
        else:
            # Only show invitations for accounts the user is an admin of
            queryset = AccountInvitation.objects.filter(
                account__members__user=user,
                account__members__role__in=['admin', 'owner']
            )
        
        if account_id:
            queryset = queryset.filter(account_id=account_id)
            
        return queryset
    
    def perform_create(self, serializer):
        # Generate a unique invitation code and set expiration date
        invitation_code = str(uuid.uuid4())
        expires_at = timezone.now() + timedelta(days=7)  # Invitations expire after 7 days
        
        serializer.save(
            invitation_code=invitation_code,
            expires_at=expires_at,
            invited_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """
        Accept an invitation and create an account membership.
        """
        invitation = self.get_object()
        
        # Check if invitation is valid
        if invitation.status != 'pending':
            return Response(
                {'detail': 'This invitation is no longer valid.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.expires_at < timezone.now():
            invitation.status = 'expired'
            invitation.save()
            return Response(
                {'detail': 'This invitation has expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if email matches
        if invitation.email != request.user.email:
            return Response(
                {'detail': 'This invitation was sent to a different email address.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create account membership
        AccountUser.objects.create(
            account=invitation.account,
            user=request.user,
            role=invitation.role
        )
        
        # Update invitation status
        invitation.status = 'accepted'
        invitation.save()
        
        return Response({'status': 'invitation accepted'})
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """
        Decline an invitation.
        """
        invitation = self.get_object()
        
        if invitation.status == 'pending':
            invitation.status = 'declined'
            invitation.save()
        
        return Response({'status': 'invitation declined'})