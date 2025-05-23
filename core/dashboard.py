# core/dashboard.py - Fixed for UUID account IDs and import scope
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q, Sum
import datetime

# Import all models at module level to avoid scope issues
from clinic_patients.models import Patient, PatientAccount
from clinic_treatments.models import Treatment
from platform_accounts.models import Account, AccountUser
from platform_contracts.models import Contract
from platform_users.models import User

def get_account_context(request):
    """
    Extract account context from request headers - handles UUID strings
    """
    account_id = request.headers.get('X-Account-Context')
    if account_id:
        return account_id  # Return as string since it's UUID
    return None

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics - different views for staff vs regular users
    Now properly handles UUID account IDs
    """
    try:
        # Check if user is staff
        is_staff = request.user.is_staff
        
        if is_staff:
            # Admin/staff dashboard with platform-wide statistics
            
            # Total accounts
            total_accounts = Account.objects.all().count()
            active_accounts = Account.objects.filter(account_status='active').count()
            
            # Total users
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            
            # Contracts stats
            try:
                total_contracts = Contract.objects.count()
                active_contracts = Contract.objects.filter(status__code__in=['active', 'trial']).count()
            except:
                total_contracts = 0
                active_contracts = 0
            
            # Patients total (across all accounts)
            try:
                total_patients = Patient.objects.count()
            except:
                total_patients = 0
            
            # Total treatments across platform
            try:
                total_treatments = Treatment.objects.count()
                active_treatments = Treatment.objects.filter(status__in=['SCHEDULED', 'IN_PROGRESS']).count()
            except:
                total_treatments = 0
                active_treatments = 0
            
            # Total specialties across platform
            try:
                from clinic_catalog.models import Specialty
                total_specialties = Specialty.objects.filter(is_active=True).count()
            except:
                total_specialties = 0
            
            # Upcoming expiring contracts (next 30 days)
            try:
                from datetime import timedelta
                thirty_days_from_now = datetime.datetime.now() + timedelta(days=30)
                expiring_contracts = Contract.objects.filter(
                    status__code='active',
                    end_date__lte=thirty_days_from_now,
                    end_date__gte=datetime.datetime.now()
                ).select_related('account').order_by('end_date')[:5]
                
                expiring_contracts_data = [{
                    'id': contract.id,
                    'account_name': contract.account.account_name,
                    'end_date': contract.end_date,
                    'days_remaining': (contract.end_date.date() - datetime.datetime.now().date()).days
                } for contract in expiring_contracts]
            except Exception as e:
                print(f"DEBUG Dashboard: Error getting expiring contracts: {e}")
                expiring_contracts_data = []
            
            # Response with admin statistics
            response_data = {
                'isStaff': True,
                'totalAccounts': total_accounts,
                'activeAccounts': active_accounts,
                'totalUsers': total_users,
                'activeUsers': active_users,
                'totalContracts': total_contracts,
                'activeContracts': active_contracts,
                'totalPatients': total_patients,
                'totalTreatments': total_treatments,
                'activeTreatments': active_treatments,
                'totalSpecialties': total_specialties,
                'expiringContracts': expiring_contracts_data,
            }
            
        else:
            # Regular user - show account-specific stats
            # GET THE SPECIFIC ACCOUNT FROM HEADER (UUID STRING)
            account_id = get_account_context(request)
            
            print(f"DEBUG Dashboard: account_id from header = {account_id}")
            
            if not account_id:
                # No account selected - return zeros
                return Response({
                    'isStaff': False,
                    'patients': 0,
                    'treatments': 0,
                    'upcomingAppointments': 0,
                    'pendingPayments': 0,
                    'error': 'No account selected'
                })
            
            # Verify user has access to this account (UUID comparison)
            try:
                account_user = AccountUser.objects.get(
                    user=request.user,
                    account__account_id=account_id,  # UUID field comparison
                    is_active_in_account=True
                )
                print(f"DEBUG Dashboard: User has access to account {account_user.account.account_name}")
            except AccountUser.DoesNotExist:
                print(f"DEBUG Dashboard: User does not have access to account {account_id}")
                return Response({
                    'isStaff': False,
                    'patients': 0,
                    'treatments': 0,
                    'upcomingAppointments': 0,
                    'pendingPayments': 0,
                    'error': 'Access denied to this account'
                })
            
            try:
                # Patients count - ONLY for the selected account (UUID)
                try:
                    patients_count = PatientAccount.objects.filter(
                        account__account_id=account_id  # UUID field comparison
                    ).count()
                    print(f"DEBUG Dashboard: patients_count = {patients_count}")
                except Exception as e:
                    print(f"DEBUG Dashboard: Error counting patients: {e}")
                    patients_count = 0
                
                # Active treatments count - ONLY for the selected account (UUID)
                try:
                    active_treatments = Treatment.objects.filter(
                        specialty__account__account_id=account_id,  # UUID field comparison
                        status__in=['SCHEDULED', 'IN_PROGRESS']
                    ).count()
                    print(f"DEBUG Dashboard: active_treatments = {active_treatments}")
                except Exception as e:
                    print(f"DEBUG Dashboard: Error counting treatments: {e}")
                    active_treatments = 0
                
                # Upcoming appointments - ONLY for the selected account (UUID)
                try:
                    today = datetime.datetime.now()
                    upcoming_appointments = Treatment.objects.filter(
                        specialty__account__account_id=account_id,  # UUID field comparison
                        status='SCHEDULED',
                        scheduled_date__gte=today
                    ).count()
                    print(f"DEBUG Dashboard: upcoming_appointments = {upcoming_appointments}")
                except Exception as e:
                    print(f"DEBUG Dashboard: Error counting appointments: {e}")
                    upcoming_appointments = 0
                
                # Pending payments AMOUNT - ONLY for the selected account (UUID)
                try:
                    # Check if TreatmentCharge exists and has the right relationship
                    from django.apps import apps
                    
                    # Check if the model exists
                    if apps.is_installed('clinic_billing'):
                        from clinic_billing.models import TreatmentCharge
                        from django.db.models import Sum
                        
                        pending_payments_amount = TreatmentCharge.objects.filter(
                            treatment__specialty__account__account_id=account_id  # UUID field comparison
                        ).exclude(
                            payment_allocations__isnull=False
                        ).aggregate(total=Sum('amount'))['total'] or 0
                        
                        print(f"DEBUG Dashboard: pending_payments_amount = {pending_payments_amount}")
                    else:
                        pending_payments_amount = 0
                        print("DEBUG Dashboard: clinic_billing app not installed, setting pending_payments_amount = 0")
                except Exception as e:
                    print(f"DEBUG Dashboard: Error calculating payment amounts: {e}")
                    pending_payments_amount = 0
                
                response_data = {
                    'isStaff': False,
                    'patients': patients_count,
                    'treatments': active_treatments,
                    'upcomingAppointments': upcoming_appointments,
                    'pendingPaymentsAmount': pending_payments_amount,
                    'selectedAccountId': account_id,  # For debugging
                    'debug': f"Account: {account_user.account.account_name}"
                }
                
            except Exception as e:
                print(f"Error in dashboard_stats for regular user: {str(e)}")
                response_data = {
                    'isStaff': False,
                    'patients': 0,
                    'treatments': 0,
                    'upcomingAppointments': 0,
                    'pendingPaymentsAmount': 0,
                    'error': str(e)
                }
        
        return Response(response_data)
        
    except Exception as e:
        print(f"Unhandled error in dashboard_stats: {str(e)}")
        return Response({'error': 'An error occurred while fetching dashboard data'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_list(request):
    """
    Get list of accounts - only accessible to staff users
    """
    if not request.user.is_staff:
        return Response({"error": "You don't have permission to access this resource"}, status=403)
    
    accounts = Account.objects.filter(is_platform_account=True).order_by('account_name')
    
    account_data = [{
        'id': str(account.account_id),
        'name': account.account_name,
        'status': account.account_status,
        'email': account.account_email,
        'created_at': account.account_created_at
    } for account in accounts]
    
    return Response(account_data)