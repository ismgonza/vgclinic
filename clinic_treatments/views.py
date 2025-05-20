# clinic_treatments/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from platform_accounts.models import AccountUser
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
    filterset_fields = ['status', 'specialty', 'doctor', 'patient', 'scheduled_date']
    search_fields = ['patient__first_name', 'patient__last_name1', 'patient__id_number', 'catalog_item__name', 'notes']
    ordering_fields = ['scheduled_date', 'completed_date', 'status']
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return TreatmentCreateSerializer
        return TreatmentSerializer
    
    def get_queryset(self):
        # Check if date range filter is applied
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        queryset = Treatment.objects.all()
        
        if start_date and end_date:
            queryset = queryset.filter(scheduled_date__range=[start_date, end_date])
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
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