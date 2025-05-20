# clinic_billing/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from decimal import Decimal
from .models import PatientAccount, TreatmentCharge, Transaction, PaymentAllocation, create_payment
from .serializers import (
    PatientAccountSerializer, TreatmentChargeSerializer, 
    TransactionSerializer, PaymentAllocationSerializer,
    CreatePaymentSerializer
)

class PatientAccountViewSet(viewsets.ModelViewSet):
    queryset = PatientAccount.objects.all()
    serializer_class = PatientAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['patient']
    search_fields = ['patient__first_name', 'patient__last_name1', 'patient__id_number']

class TreatmentChargeViewSet(viewsets.ModelViewSet):
    queryset = TreatmentCharge.objects.all()
    serializer_class = TreatmentChargeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['treatment', 'treatment__patient']
    search_fields = ['description', 'treatment__patient__first_name', 'treatment__patient__last_name1']
    ordering_fields = ['date_created', 'amount']

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient', 'transaction_type', 'payment_method', 'date']
    search_fields = ['description', 'notes', 'patient__first_name', 'patient__last_name1']
    ordering_fields = ['date', 'amount']
    
    @action(detail=False, methods=['post'])
    def create_payment(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                transaction = serializer.save()
                result_serializer = TransactionSerializer(transaction)
                return Response(result_serializer.data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def patient_statement(self, request):
        patient_id = request.query_params.get('patient_id', None)
        if not patient_id:
            return Response({'error': 'patient_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get account balance
        try:
            account = PatientAccount.objects.get(patient_id=patient_id)
            balance = account.current_balance
        except PatientAccount.DoesNotExist:
            balance = Decimal('0.00')
        
        # Get all charges
        charges = TreatmentCharge.objects.filter(treatment__patient_id=patient_id)
        charges_total = charges.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Get all payments
        payments = Transaction.objects.filter(
            patient_id=patient_id, 
            transaction_type='PAYMENT'
        )
        payments_total = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            patient_id=patient_id
        ).order_by('-date')[:10]
        
        # Unpaid charges
        unpaid_charges = []
        for charge in charges:
            paid_amount = PaymentAllocation.objects.filter(
                treatment_charge=charge
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            if paid_amount < charge.amount:
                unpaid_charges.append({
                    'id': charge.id,
                    'treatment': charge.treatment.id,
                    'treatment_name': charge.treatment.catalog_item.name,
                    'date': charge.date_created,
                    'amount': float(charge.amount),
                    'paid_amount': float(paid_amount),
                    'balance': float(charge.amount - paid_amount)
                })
        
        return Response({
            'patient_id': patient_id,
            'current_balance': float(balance),
            'charges_total': float(charges_total),
            'payments_total': float(payments_total),
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data,
            'unpaid_charges': unpaid_charges
        })

class PaymentAllocationViewSet(viewsets.ModelViewSet):
    queryset = PaymentAllocation.objects.all()
    serializer_class = PaymentAllocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transaction', 'treatment_charge']