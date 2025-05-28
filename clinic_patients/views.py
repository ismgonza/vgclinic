# clinic_patients/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from platform_accounts.models import Account, AccountUser
from core.permissions import AccountPermissionMixin, PatientAccessMixin
from .models import Patient, PatientPhone, EmergencyContact, PatientAccount, MedicalHistory
from .serializers import (
    PatientSerializer, PatientCreateSerializer, PatientPhoneSerializer,
    EmergencyContactSerializer, PatientAccountSerializer, MedicalHistorySerializer
)

class PatientViewSet(AccountPermissionMixin, PatientAccessMixin, viewsets.ModelViewSet):
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['gender', 'marital_status', 'is_foreign', 'province', 'canton']
    search_fields = ['first_name', 'last_name1', 'last_name2', 'id_number', 'email']
    ordering_fields = ['first_name', 'last_name1', 'birth_date']

    def get_queryset(self):
        # Get account context
        account = self.get_account_context()
        
        if not account:
            # No account context - show patients from all user's accounts
            if self.request.user.is_superuser:
                return Patient.objects.all()
            else:
                user_accounts = AccountUser.objects.filter(
                    user=self.request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                return Patient.objects.filter(
                    clinic_memberships__account__in=user_accounts
                ).distinct()
        
        # FIXED: Use correct permission name
        if not self.check_permission('view_patients_list', account):
            return Patient.objects.none()
        
        # Get base queryset for this account
        base_queryset = Patient.objects.filter(
            clinic_memberships__account=account
        ).distinct()
        
        # Apply role-based filtering (doctors see only their patients)
        return self.get_accessible_patients_queryset(base_queryset, account)
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return PatientCreateSerializer
        return PatientSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to check manage_patient_basic permission."""
        account = self.get_account_context()
        
        # FIXED: Use correct permission name
        permission_error = self.require_permission('manage_patient_basic', account)
        if permission_error:
            return permission_error
            
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Override update to check manage_patient_basic permission."""
        account = self.get_account_context()
        
        # FIXED: Use correct permission name
        permission_error = self.require_permission('manage_patient_basic', account)
        if permission_error:
            return permission_error
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to check manage_patient_basic permission."""
        account = self.get_account_context()
        
        # FIXED: Use correct permission name  
        permission_error = self.require_permission('manage_patient_basic', account)
        if permission_error:
            return permission_error
            
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        """Get patient medical history - requires view_patient_history permission."""
        account = self.get_account_context()
        
        # Check permission for sensitive medical data
        if not self.can_access_patient_history(account):
            return Response(
                {'error': 'Permission denied. Required permission: view_patient_history'}, 
                status=403
            )
        
        patient = self.get_object()
        
        if account:
            try:
                patient_account = PatientAccount.objects.get(patient=patient, account=account)
                histories = patient_account.medical_histories.all()
                serializer = MedicalHistorySerializer(histories, many=True)
                return Response(serializer.data)
            except PatientAccount.DoesNotExist:
                return Response({"detail": "Patient not found in this clinic"}, status=404)
        else:
            # Admin view - all histories
            histories = MedicalHistory.objects.filter(
                patient_account__patient=patient
            )
            serializer = MedicalHistorySerializer(histories, many=True)
            return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_phone(self, request, pk=None):
        """Add phone to patient - requires manage_patients permission."""
        account = self.get_account_context()
        
        # Check permission
        permission_error = self.require_permission('manage_patients', account)
        if permission_error:
            return permission_error
        
        patient = self.get_object()
        serializer = PatientPhoneSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patient=patient)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
    @action(detail=True, methods=['post'])
    def add_emergency_contact(self, request, pk=None):
        """Add emergency contact to patient - requires manage_patients permission."""
        account = self.get_account_context()
        
        # Check permission
        permission_error = self.require_permission('manage_patients', account)
        if permission_error:
            return permission_error
        
        patient = self.get_object()
        serializer = EmergencyContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patient=patient)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
    @action(detail=True, methods=['post'])
    def add_to_clinic(self, request, pk=None):
        """Add patient to clinic - requires manage_patients permission."""
        account = self.get_account_context()
        
        # Check permission
        permission_error = self.require_permission('manage_patients', account)
        if permission_error:
            return permission_error
        
        patient = self.get_object()
        
        # Make sure account is provided
        if 'account' not in request.data:
            return Response({"detail": "Account ID is required"}, status=400)
        
        # Check if patient is already in this clinic
        if PatientAccount.objects.filter(patient=patient, account_id=request.data['account']).exists():
            return Response({"detail": "Patient already belongs to this clinic"}, status=400)
        
        serializer = PatientAccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patient=patient)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class PatientAccountViewSet(AccountPermissionMixin, viewsets.ModelViewSet):
    serializer_class = PatientAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        account = self.get_account_context()
        
        # Check permission
        if account and not self.check_permission('view_patients', account):
            return PatientAccount.objects.none()
        
        if account:
            return PatientAccount.objects.filter(account=account)
        else:
            # Fallback for admin users
            if self.request.user.is_superuser:
                return PatientAccount.objects.all()
            else:
                user_accounts = AccountUser.objects.filter(
                    user=self.request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                return PatientAccount.objects.filter(account__in=user_accounts)
    
    def create(self, request, *args, **kwargs):
        """Override create to check manage_patients permission."""
        account = self.get_account_context()
        
        # Check permission
        permission_error = self.require_permission('manage_patients', account)
        if permission_error:
            return permission_error
            
        return super().create(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def add_medical_history(self, request, pk=None):
        """Add medical history - requires manage_patients permission."""
        account = self.get_account_context()
        
        # Check permission
        permission_error = self.require_permission('manage_patients', account)
        if permission_error:
            return permission_error
        
        patient_account = self.get_object()
        serializer = MedicalHistorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(patient_account=patient_account)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class MedicalHistoryViewSet(AccountPermissionMixin, viewsets.ModelViewSet):
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        account = self.get_account_context()
        
        # Check permission for sensitive medical data
        if account and not self.check_permission('view_patient_history', account):
            return MedicalHistory.objects.none()
        
        if account:
            return MedicalHistory.objects.filter(patient_account__account=account)
        else:
            # Fallback for admin users
            if self.request.user.is_superuser:
                return MedicalHistory.objects.all()
            else:
                user_accounts = AccountUser.objects.filter(
                    user=self.request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                return MedicalHistory.objects.filter(patient_account__account__in=user_accounts)
    
    def create(self, request, *args, **kwargs):
        """Override create to check manage_patients permission."""
        account = self.get_account_context()
        
        # Check permission
        permission_error = self.require_permission('manage_patients', account)
        if permission_error:
            return permission_error
            
        return super().create(request, *args, **kwargs)