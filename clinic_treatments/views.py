# clinic_treatments/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from platform_accounts.models import Account, AccountUser
from platform_users.models import User
from .models import Treatment, TreatmentNote, TreatmentDetail
from .serializers import (
    TreatmentSerializer, TreatmentCreateSerializer, 
    TreatmentNoteSerializer, TreatmentDetailSerializer
)

class TreatmentViewSet(viewsets.ModelViewSet):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'specialty', 'doctor', 'patient', 'scheduled_date', 'location']
    search_fields = ['patient__first_name', 'patient__last_name1', 'patient__id_number', 'catalog_item__name', 'notes']
    ordering_fields = ['scheduled_date', 'completed_date', 'status']
    
    def get_queryset(self):
        # Get account context
        account = self.get_account_context()

        # Start with base queryset
        queryset = Treatment.objects.all()
        
        # Filter by account if we have one
        if account:
            # Filter treatments by specialty's account (since treatments are linked to catalog items, which are linked to specialties, which are linked to accounts)
            queryset = queryset.filter(specialty__account=account)
            print(f"DEBUG: Filtered queryset count = {queryset.count()}")
        else:
            print("DEBUG: No account context - showing all treatments")
        
        # Apply date range filter if provided
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date and end_date:
            queryset = queryset.filter(scheduled_date__range=[start_date, end_date])
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return TreatmentCreateSerializer
        return TreatmentSerializer
    
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
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
        
    @action(detail=False, methods=['get'])
    def form_options(self, request):
        """Get all options needed for treatment forms"""
        try:
            # Get doctors from accounts the user has access to
            user_accounts = AccountUser.objects.filter(
                user=request.user,
                is_active_in_account=True
            ).values_list('account', flat=True)
            
            # Get all users who are doctors in these accounts
            doctors = User.objects.filter(
                account_memberships__account__in=user_accounts,
                account_memberships__role__id='doc',
                account_memberships__is_active_in_account=True,
                is_active=True
            ).distinct()
            
            # Also include owners as potential doctors
            owners = User.objects.filter(
                account_memberships__account__in=user_accounts,
                account_memberships__role__id='own',
                account_memberships__is_active_in_account=True,
                is_active=True
            ).distinct()
            
            # Combine doctors and owners
            all_doctors = doctors.union(owners).order_by('first_name', 'last_name')
            
            # Serialize the data
            from platform_users.serializers import UserSerializer
            doctors_data = UserSerializer(all_doctors, many=True).data
            
            return Response({
                'doctors': doctors_data
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        treatment = self.get_object()
        treatment.complete()
        serializer = self.get_serializer(treatment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        treatment = self.get_object()
        treatment.cancel()
        serializer = self.get_serializer(treatment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        treatment = self.get_object()
        serializer = TreatmentNoteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(treatment=treatment, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TreatmentNoteViewSet(viewsets.ModelViewSet):
    queryset = TreatmentNote.objects.all()
    serializer_class = TreatmentNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['treatment']
    ordering_fields = ['date']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class TreatmentDetailViewSet(viewsets.ModelViewSet):
    queryset = TreatmentDetail.objects.all()
    serializer_class = TreatmentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['treatment', 'field_name']