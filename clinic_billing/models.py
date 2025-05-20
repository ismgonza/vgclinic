from django.db import models
from django.utils import timezone
from decimal import Decimal


class PatientAccount(models.Model):
    """Tracks the financial account for each patient"""
    patient = models.OneToOneField('clinic_patients.Patient', on_delete=models.CASCADE, related_name='account')
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Positive balance means patient has credit, negative means they owe money
    
    def __str__(self):
        balance_str = f"${self.current_balance}" if self.current_balance >= 0 else f"-${abs(self.current_balance)}"
        return f"Account for {self.patient}: {balance_str}"


class TreatmentCharge(models.Model):
    """Financial charges associated with treatments"""
    treatment = models.OneToOneField('clinic_treatments.Treatment', on_delete=models.CASCADE, related_name='charge')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date_created = models.DateTimeField(default=timezone.now)
    
    def save(self, *args, **kwargs):
        # When a charge is created, automatically create a transaction
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            Transaction.objects.create(
                patient=self.treatment.patient,
                amount=-self.amount,  # Negative because it's a charge
                transaction_type='CHARGE',
                treatment_charge=self,
                date=timezone.now(),
                description=f"Charge for {self.treatment.name}"
            )
    
    def __str__(self):
        return f"Charge of ${self.amount} for {self.treatment}"


class Transaction(models.Model):
    """Records every financial movement (payments, refunds, etc.)"""
    TRANSACTION_TYPES = [
        ('PAYMENT', 'Payment Received'),
        ('CHARGE', 'Treatment Charge'),
        ('REFUND', 'Refund Issued'),
        ('ADJUSTMENT', 'Balance Adjustment'),
    ]
    
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit/Debit Card'),
        ('TRANSFER', 'Bank Transfer'),
        ('CHECK', 'Check'),
        ('CREDIT', 'Account Credit'),
        ('OTHER', 'Other'),
    ]
    
    patient = models.ForeignKey('clinic_patients.Patient', on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Positive amount for money coming in (payments), negative for money going out (charges, refunds)
    
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, blank=True, null=True)
    treatment_charge = models.ForeignKey(TreatmentCharge, on_delete=models.SET_NULL, blank=True, null=True, related_name='transactions')
    # If related to a specific treatment charge
    
    date = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        # Update patient account balance when transaction is saved
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Only update balance for new transactions to avoid double-counting on updates
        if is_new:
            account, created = PatientAccount.objects.get_or_create(patient=self.patient)
            account.current_balance += self.amount
            account.save()
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${abs(self.amount)}"


class PaymentAllocation(models.Model):
    """Tracks how a payment is allocated to specific treatment charges"""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='allocations')
    treatment_charge = models.ForeignKey(TreatmentCharge, on_delete=models.CASCADE, related_name='payment_allocations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"${self.amount} from {self.transaction} to {self.treatment_charge}"


def create_payment(patient, amount, payment_method, allocations=None, description=None, notes=None):
    """
    Helper function to create a payment and allocate it to treatment charges
    
    Args:
        patient: The Patient instance
        amount: Decimal amount of the payment
        payment_method: String payment method from Transaction.PAYMENT_METHODS
        allocations: Dict mapping TreatmentCharge IDs to allocation amounts
        description: Optional payment description
        notes: Optional payment notes
    
    Returns:
        The created Transaction instance
    """
    if amount <= 0:
        raise ValueError("Payment amount must be positive")
    
    if description is None:
        description = f"Payment of ${amount}"
    
    # Create the payment transaction
    transaction = Transaction.objects.create(
        patient=patient,
        amount=amount,  # Positive for incoming payment
        transaction_type='PAYMENT',
        payment_method=payment_method,
        description=description,
        notes=notes or ""
    )
    
    # If allocations are specified, create PaymentAllocation records
    if allocations:
        total_allocated = Decimal('0.00')
        
        for charge_id, allocation_amount in allocations.items():
            treatment_charge = TreatmentCharge.objects.get(id=charge_id)
            allocation_amount = Decimal(str(allocation_amount))
            
            if allocation_amount <= 0:
                raise ValueError("Allocation amount must be positive")
            
            total_allocated += allocation_amount
            
            PaymentAllocation.objects.create(
                transaction=transaction,
                treatment_charge=treatment_charge,
                amount=allocation_amount
            )
        
        # Verify that allocations don't exceed payment amount
        if total_allocated > amount:
            transaction.delete()  # Rollback the transaction
            raise ValueError("Total allocations exceed payment amount")
    
    return transaction