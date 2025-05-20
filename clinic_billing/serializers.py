# clinic_billing/serializers.py
from rest_framework import serializers
from .models import PatientAccount, TreatmentCharge, Transaction, PaymentAllocation
from clinic_patients.serializers import PatientSerializer
from clinic_treatments.serializers import TreatmentSerializer

class PatientAccountSerializer(serializers.ModelSerializer):
    patient_details = PatientSerializer(source='patient', read_only=True)
    
    class Meta:
        model = PatientAccount
        fields = ('id', 'patient', 'current_balance', 'patient_details')
        read_only_fields = ('current_balance',)

class TreatmentChargeSerializer(serializers.ModelSerializer):
    treatment_details = TreatmentSerializer(source='treatment', read_only=True)
    
    class Meta:
        model = TreatmentCharge
        fields = ('id', 'treatment', 'amount', 'description', 'date_created', 'treatment_details')
        read_only_fields = ('date_created',)

class PaymentAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentAllocation
        fields = ('id', 'transaction', 'treatment_charge', 'amount')

class TransactionSerializer(serializers.ModelSerializer):
    patient_details = PatientSerializer(source='patient', read_only=True)
    treatment_charge_details = TreatmentChargeSerializer(source='treatment_charge', read_only=True)
    allocations = PaymentAllocationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Transaction
        fields = ('id', 'patient', 'amount', 'transaction_type', 'payment_method',
                  'treatment_charge', 'date', 'description', 'notes',
                  'patient_details', 'treatment_charge_details', 'allocations')

class CreatePaymentSerializer(serializers.Serializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=PatientAccount.objects.all())
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=Transaction.PAYMENT_METHODS)
    allocations = serializers.DictField(child=serializers.DecimalField(max_digits=10, decimal_places=2), required=False)
    description = serializers.CharField(max_length=255, required=False)
    notes = serializers.CharField(required=False)
    
    def create(self, validated_data):
        from .models import create_payment
        
        patient = validated_data.pop('patient')
        allocations = validated_data.pop('allocations', None)
        
        return create_payment(
            patient=patient,
            allocations=allocations,
            **validated_data
        )