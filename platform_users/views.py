# platform_users/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer, ProfileUpdateSerializer, ChangePasswordSerializer, ProfileDetailSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # If user is superuser, return all users
        # Otherwise, return only the user making the request
        if self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Get current user's profile
        """
        # FIXED: Add context so serializer can access request headers
        serializer = ProfileDetailSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """
        Update current user's profile (limited fields)
        """
        # FIXED: Add context here too so the serializer can access X-Account-Context header
        serializer = ProfileUpdateSerializer(
            request.user, 
            data=request.data, 
            partial=True,
            context={'request': request}  # ← ESTA ES LA LÍNEA CLAVE QUE FALTABA
        )
        
        if serializer.is_valid():
            serializer.save()
            # Return updated profile - FIXED: Add context here too
            profile_serializer = ProfileDetailSerializer(request.user, context={'request': request})
            return Response(profile_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """
        Change current user's password
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Set the new password
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_memberships(self, request):
        """
        Get current user's team memberships (roles and specialties)
        """
        user = request.user
        
        # Skip for staff users (they don't have clinic memberships)
        if user.is_staff:
            return Response([])
        
        try:
            # Import here to avoid circular imports
            from platform_accounts.models import AccountUser
            
            memberships = AccountUser.objects.filter(
                user=user,
                is_active_in_account=True
            ).select_related('account', 'specialty')
            
            memberships_data = []
            for membership in memberships:
                membership_data = {
                    'account_id': str(membership.account.account_id),  # Convert UUID to string
                    'account_name': membership.account.account_name,
                    'role': membership.role,
                    'role_display': membership.get_role_display(),
                    'specialty_id': membership.specialty.id if membership.specialty else None,
                    'specialty_name': membership.specialty.name if membership.specialty else None,
                    'joined_date': membership.created_at,
                    'is_active': membership.is_active_in_account,
                }
                memberships_data.append(membership_data)
            
            return Response(memberships_data)
            
        except Exception as e:
            # If there's any error, return empty list
            return Response([])