# core/middleware.py - ADD debug prints
from platform_accounts.models import Account, AccountUser

class AccountContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get account context from header
        account_id = request.headers.get('X-Account-Context')
        
        print(f"MIDDLEWARE DEBUG: account_id = {account_id}")
        print(f"MIDDLEWARE DEBUG: user authenticated = {request.user.is_authenticated}")
        
        if account_id and request.user.is_authenticated:
            try:
                print(f"MIDDLEWARE DEBUG: Looking for account with ID: {account_id}")
                # Validate that the user has access to this account
                account = Account.objects.get(account_id=account_id)
                print(f"MIDDLEWARE DEBUG: Found account: {account.account_name}")
                
                # Check if user has access (unless they're staff/superuser)
                if request.user.is_staff or request.user.is_superuser:
                    print(f"MIDDLEWARE DEBUG: User is staff/superuser, granting access")
                    request.account = account
                else:
                    # Check if user is a member of this account
                    membership = AccountUser.objects.filter(
                        user=request.user,
                        account=account,
                        is_active_in_account=True
                    )
                    print(f"MIDDLEWARE DEBUG: Membership query result: {membership.exists()}")
                    if membership.exists():
                        print(f"MIDDLEWARE DEBUG: User has membership, setting account")
                        request.account = account
                    else:
                        print(f"MIDDLEWARE DEBUG: User has no membership")
                        request.account = None
                        
            except Account.DoesNotExist:
                print(f"MIDDLEWARE DEBUG: Account not found")
                request.account = None
            except Exception as e:
                print(f"MIDDLEWARE DEBUG: Exception: {e}")
                request.account = None
        else:
            print(f"MIDDLEWARE DEBUG: No account_id or user not authenticated")
            request.account = None
            
        response = self.get_response(request)
        return response