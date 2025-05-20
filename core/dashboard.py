# core/dashboard.py (updated)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q, Sum
from clinic_patients.models import Patient, PatientAccount
from clinic_treatments.models import Treatment
from clinic_billing.models import TreatmentCharge, Transaction
from platform_accounts.models import Account, AccountUser
from platform_contracts.models import Contract
from platform_users.models import User
import datetime

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics - different views for staff vs regular users
    """
    try:
        # Check if user is staff
        is_staff = request.user.is_staff
        
        # Base response - will be enhanced for staff
        response_data = {}
        
        if is_staff:
            # Admin/staff dashboard with platform-wide statistics
            from platform_accounts.models import Account
            from platform_users.models import User
            from platform_contracts.models import Contract 
            from clinic_patients.models import Patient
            from clinic_treatments.models import Treatment
            
            # Debug: Check what accounts actually exist
            all_accounts = list(Account.objects.all().values('account_id', 'account_name', 'is_platform_account', 'account_status'))
            print(f"All accounts in DB: {all_accounts}")
            
            # Total accounts - ensure we're counting correctly
            total_accounts = Account.objects.all().count()
            active_accounts = Account.objects.filter(account_status='active').count()
            
            # Total users
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            
            # Contracts stats - use try/except in case tables don't exist
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
            }
            
            # For debugging
            print(f"Dashboard stats for staff: {response_data}")
            
        else:
            # Regular user - show account-specific stats
            try:
                from platform_accounts.models import AccountUser
                from clinic_patients.models import PatientAccount
                from clinic_treatments.models import Treatment
                from clinic_billing.models import TreatmentCharge, Transaction
                import datetime
                
                # Get the user's accounts
                user_accounts = AccountUser.objects.filter(
                    user=request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                
                # If the user has no accounts, return empty stats
                if not user_accounts:
                    return Response({
                        'isStaff': False,
                        'patients': 0,
                        'treatments': 0,
                        'upcomingAppointments': 0,
                        'pendingPayments': 0
                    })
                
                # Patients count (patients in user's accounts)
                try:
                    patients_count = PatientAccount.objects.filter(
                        account__in=user_accounts
                    ).count()
                except:
                    patients_count = 0
                
                # Active treatments count
                try:
                    active_treatments = Treatment.objects.filter(
                        specialty__account__in=user_accounts,
                        status__in=['SCHEDULED', 'IN_PROGRESS']
                    ).count()
                except:
                    active_treatments = 0
                
                # Upcoming appointments (treatments with scheduled_date in the future)
                try:
                    today = datetime.datetime.now()
                    upcoming_appointments = Treatment.objects.filter(
                        specialty__account__in=user_accounts,
                        status='SCHEDULED',
                        scheduled_date__gte=today
                    ).count()
                except:
                    upcoming_appointments = 0
                
                # Pending payments (outstanding treatment charges)
                try:
                    pending_payments = TreatmentCharge.objects.filter(
                        treatment__specialty__account__in=user_accounts
                    ).exclude(
                        payment_allocations__isnull=False
                    ).count()
                except:
                    pending_payments = 0
                
                response_data = {
                    'isStaff': False,
                    'patients': patients_count,
                    'treatments': active_treatments,
                    'upcomingAppointments': upcoming_appointments,
                    'pendingPayments': pending_payments
                }
                
                print(f"Dashboard stats for regular user: {response_data}")
            except Exception as e:
                print(f"Error in dashboard_stats for regular user: {str(e)}")
                # If there's an error, return a simple placeholder
                response_data = {
                    'isStaff': False,
                    'patients': 0,
                    'treatments': 0,
                    'upcomingAppointments': 0,
                    'pendingPayments': 0
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