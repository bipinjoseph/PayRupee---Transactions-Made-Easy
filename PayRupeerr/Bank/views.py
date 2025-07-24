from django.shortcuts import render,redirect
from django.http import HttpResponse, JsonResponse
from Bank.models import Useracc,Account
from django.views.decorators.csrf import csrf_exempt
from .deco import login_required_custom
from Bank.models import (
    Transaction, SecuritySettings, DeviceFingerprint, LoginActivity,
    SuspiciousActivity, TransactionLimit, VirtualCard, CardTransaction,
    ChatConversation, ChatMessage, AIInsight
)
from .ai_assistant import AIFinancialAssistant
from django.core.mail import send_mail
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import json
import hashlib
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum

def send_transaction_email(to_email, subject, message):
    send_mail(
        subject,
        message,
        'your_email@gmail.com',  # 👈 Same Gmail as above
        [to_email],
        fail_silently=False,
    )

# Create your views here.

def homepage(request):
    return render(request,'homepage.html')



def loginpage(request):
    return render(request,'loginpage.html')


@csrf_exempt

def loginpageprocess(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        if 'msgl' in request.session:
            del request.session['msgl']
        msgl=''
        try:
            user = Useracc.objects.get(username=username)
            # if check_password(password, user.password):
            if password==user.passwrd:

                request.session['username'] = user.username  # Create session
                return redirect('/dashboard/')
            else:

                msgl="inv"
        except Useracc.DoesNotExist:
            msgl='non'

        request.session['msgl'] = msgl
    return redirect('/loginpage/')






def registerpage(request):
    return render(request,'registerpage.html')

def registerpageprocess(request):
    if request.method=="POST":
        username=request.POST['username']
        fullname=request.POST['fullname']
        email=request.POST['email']
        password=request.POST['password']
        password2=request.POST['password2']

        msgr=''
        if 'msgr' in request.session:
            del request.session['msgr']
        if password==password2 and username!=None:
            try:
                userexist=Useracc.objects.get(username=username)
                msgr=f"Username {userexist.username} already exists.!!!"
                request.session['msgr'] = msgr
                return redirect('/registerpage/')


            except Useracc.DoesNotExist:

                user1=Useracc(username=username,fullname=fullname,email=email,passwrd=password)
                user1.save()
                etrail=10000

                acctnm=Account.objects.count()
                acctnm=acctnm+1
                etrail=str(etrail+acctnm)

                account1=Account(AccountHolder=fullname,AccountNumber=f"PAYR-{etrail}",AccountType="Savings",AccountStatus="Active",AccountBalance=0.0,AccountUsername=username)
                account1.save()

                # Send welcome email notification
                send_transaction_email(
                    to_email=email,
                    subject='Welcome to PayRupee - Account Created Successfully!',
                    message=f'''Dear {fullname},

Welcome to PayRupee Banking!

We are delighted to inform you that your account has been successfully created. Here are your account details:

Account Information:
- Account Holder: {fullname}
- Username: {username}
- Account Number: {account1.AccountNumber}
- Account Type: Savings
- Account Status: Active
- Initial Balance: ₹0.00

You can now log in to your PayRupee account using your username and password to:
- Check your account balance
- Make deposits and withdrawals
- Transfer funds to other accounts
- Create virtual cards
- Access our AI financial assistant
- Monitor your transaction history

Security Tips:
- Keep your login credentials secure
- Never share your password with anyone
- Log out after each session
- Monitor your account regularly

Thank you for choosing PayRupee Banking. We look forward to serving your banking needs.

Best regards,
PayRupee Banking Team

For support, contact us at: 37347@yenepoya.edu.in
For customer support, call us at: +918590191091
'''
                )

                return redirect('/loginpage/')
        else:
            msg=True
            con={
                'msg':msg
            }
            return render(request,'registerpage.html',con)


    return render(request,'registerpage.html')




@login_required_custom

def dashboard(request):
    username = request.session.get('username')
    act=Account.objects.get(AccountUsername=username)
    et=act.AccountNumber.split()

    # Get success message if exists
    success_message = request.session.pop('success_message', None)

    con={
        "act":act,
        'et':et[-1],
        'success_message': success_message
    }

    return render(request,'dashboard.html',con)




@login_required_custom

def accounts(request):
    username = request.session.get('username')
    act=Account.objects.get(AccountUsername=username)
    con={
        "act":act,
    }

    return render(request,'accounts.html',con)







@login_required_custom

def transfer(request):
    username = request.session.get('username')
    act=Account.objects.get(AccountUsername=username)
    virtual_cards = VirtualCard.objects.filter(account=act, status='active')

    # Get success message if exists
    success_message = request.session.pop('transfer_success', None)

    con={
        "act":act,
        "virtual_cards":virtual_cards,
        "success_message": success_message,
    }

    return render(request,'transfer.html',con)


@login_required_custom
def transferprocess(request):
    username = request.session.get('username')
    sender_account = Account.objects.get(AccountUsername=username)

    if 'msgt' in request.session:
        del request.session['msgt']
    msgt = ''

    if request.method == "POST":
        tramount = int(request.POST['amount'])
        traccountnum = request.POST['account-number']
        descr = request.POST['description']
        from_account = request.POST['from-account']

        try:
            receiver_account = Account.objects.get(AccountNumber=traccountnum)

            if sender_account.AccountNumber == receiver_account.AccountNumber:
                msgt = 'same_account'
                request.session['msgt'] = msgt
                return redirect('/transfer/')

            # Check if transfer is from virtual card
            if from_account.startswith('virtual_card_'):
                card_id = from_account.replace('virtual_card_', '')
                virtual_card = VirtualCard.objects.get(id=card_id, account=sender_account)

                # Reset daily and monthly spending if needed
                from datetime import date
                today = date.today()
                if virtual_card.last_transaction_date != today:
                    virtual_card.daily_spent = 0.0
                    virtual_card.last_transaction_date = today

                virtual_card.reset_monthly_spending_if_needed()

                # Check virtual card limits
                if tramount > virtual_card.get_remaining_daily_limit():
                    msgt = 'card_daily_limit'
                    request.session['msgt'] = msgt
                    return redirect('/transfer/')

                if tramount > virtual_card.get_remaining_monthly_limit():
                    msgt = 'card_monthly_limit'
                    request.session['msgt'] = msgt
                    return redirect('/transfer/')

                # Check if card is active
                if virtual_card.status != 'active':
                    msgt = 'card_inactive'
                    request.session['msgt'] = msgt
                    return redirect('/transfer/')

                # For virtual card, check if account has sufficient balance
                available_balance = sender_account.AccountBalance
            else:
                # Regular account transfer
                available_balance = sender_account.AccountBalance

            if available_balance >= tramount:
                # Perform transfer
                if from_account.startswith('virtual_card_'):
                    # For virtual card transfers, deduct from card limits instead of account balance
                    card_id = from_account.replace('virtual_card_', '')
                    virtual_card = VirtualCard.objects.get(id=card_id, account=sender_account)

                    # Update virtual card spending
                    virtual_card.daily_spent += tramount
                    virtual_card.monthly_spent += tramount
                    virtual_card.save()

                    # Still deduct from account balance for actual money transfer
                    sender_account.AccountBalance -= tramount
                else:
                    # Regular account transfer
                    sender_account.AccountBalance -= tramount

                receiver_account.AccountBalance += tramount
                sender_account.save()
                receiver_account.save()

                # Create transaction record
                if from_account.startswith('virtual_card_'):
                    card_id = from_account.replace('virtual_card_', '')
                    virtual_card = VirtualCard.objects.get(id=card_id, account=sender_account)

                    # Create regular transaction for account tracking
                    transaction = Transaction.objects.create(
                        account=sender_account,
                        transaction_type="Virtual Card Transfer",
                        amount=tramount,
                        description=f"Virtual Card Transfer to {receiver_account.AccountNumber} - {descr}"
                    )

                    # Create card transaction linked to the transaction
                    CardTransaction.objects.create(
                        virtual_card=virtual_card,
                        transaction=transaction,
                        merchant_name=f"Transfer to {receiver_account.AccountHolder}",
                        merchant_category="Transfer",
                        is_online=True
                    )

                    # Update AI memory for virtual card transaction
                    from django.utils import timezone
                    try:
                        user = Useracc.objects.get(username=username)
                        AIInsight.objects.create(
                            user=user,
                            insight_type='card_transaction',
                            title='Virtual Card Transfer',
                            description=f'Transfer of ₹{tramount} made using virtual card to {receiver_account.AccountHolder}. Remaining daily limit: ₹{virtual_card.get_remaining_daily_limit()}',
                            confidence_score=0.95,
                            metadata={
                                'card_id': virtual_card.id,
                                'amount': tramount,
                                'recipient': receiver_account.AccountHolder,
                                'remaining_daily_limit': virtual_card.get_remaining_daily_limit(),
                                'remaining_monthly_limit': virtual_card.get_remaining_monthly_limit()
                            }
                        )
                    except Exception as e:
                        pass  # Don't fail the transaction if AI memory update fails
                else:
                    Transaction.objects.create(
                        account=sender_account,
                        transaction_type="Transfer Out",
                        amount=tramount,
                        description=f"To {receiver_account.AccountNumber} - {descr}"
                    )

                # Log receiver transaction
                Transaction.objects.create(
                    account=receiver_account,
                    transaction_type="Transfer In",
                    amount=tramount,
                    description=f"From {sender_account.AccountNumber} - {descr}"
                )

                # Get sender and receiver user details
                sender_user = Useracc.objects.get(username=username)
                receiver_username = receiver_account.AccountUsername
                receiver_user = Useracc.objects.get(username=receiver_username)
                print(receiver_user)
                print(receiver_username)

                # receiver_user = Useracc.objects.get(username=receiver_username)

                # To sender
                send_transaction_email(
                    to_email=sender_user.email,
                    subject='PayRupee: Fund Transfer Confirmation',
                    message=f'''Dear {sender_user.fullname},

We are writing to confirm that a fund transfer of ₹{tramount} has been successfully processed from your account to {receiver_account.AccountHolder} (Account: {receiver_account.AccountNumber}).

Transaction Details:
- Amount: ₹{tramount}
- Recipient: {receiver_account.AccountHolder}
- Account Number: {receiver_account.AccountNumber}
- Description: {descr}

Your updated account balance is ₹{sender_account.AccountBalance}.

If you did not authorize this transaction or notice any discrepancies, please contact our customer support immediately at 37347@yenepoya.edu.in or call our 24/7 helpline at +918590191091.

Thank you for banking with PayRupee.

Regards,
PayRupee Banking Team
'''
                )

                # To recipient
                send_transaction_email(
                    to_email=receiver_user.email,
                    subject='PayRupee: Fund Received Notification',
                    message=f'''Dear {receiver_user.fullname},

We are pleased to inform you that your PayRupee account has been credited with ₹{tramount} through a fund transfer from {sender_account.AccountHolder} (Account: {sender_account.AccountNumber}).

Transaction Details:
- Amount Received: ₹{tramount}
- From: {sender_account.AccountHolder}
- Account Number: {sender_account.AccountNumber}
- Description: {descr}

Your updated account balance is ₹{receiver_account.AccountBalance}.

Thank you for banking with PayRupee.

Regards,
PayRupee Banking Team
'''
                )

                # Set success message for transfer page
                request.session['transfer_success'] = f'Transfer of ₹{tramount} completed successfully!'
                return redirect('/transfer/')
            else:
                msgt = 'insufficient'
                request.session['msgt'] = msgt

        except Account.DoesNotExist:
            msgt = 'non'
            request.session['msgt'] = msgt

    return redirect('/transfer/')









@login_required_custom

def withdraw(request):
    username = request.session.get('username')
    act=Account.objects.get(AccountUsername=username)
    virtual_cards = VirtualCard.objects.filter(account=act, status='active')

    # Get success message if exists
    success_message = request.session.pop('withdraw_success', None)

    con={
        "act":act,
        "virtual_cards":virtual_cards,
        "success_message": success_message,
    }
    return render(request,'withdraw.html',con)


@login_required_custom

def withdrawprocess(request):
    username = request.session.get('username')
    act=Account.objects.get(AccountUsername=username)
    if request.method=="POST":
        wamount=int(request.POST['amount'])
        descr=request.POST['description']
        account_type = request.POST['account']

        # Check if withdrawal is from virtual card
        if account_type.startswith('virtual_card_'):
            card_id = account_type.replace('virtual_card_', '')
            virtual_card = VirtualCard.objects.get(id=card_id, account=act)

            # Reset daily and monthly spending if needed
            from datetime import date
            today = date.today()
            if virtual_card.last_transaction_date != today:
                virtual_card.daily_spent = 0.0
                virtual_card.last_transaction_date = today

            virtual_card.reset_monthly_spending_if_needed()

            # Check virtual card limits
            if wamount > virtual_card.get_remaining_daily_limit():
                # Handle daily limit exceeded
                return redirect('/withdraw/')

            if wamount > virtual_card.get_remaining_monthly_limit():
                # Handle monthly limit exceeded
                return redirect('/withdraw/')

            # Check if card is active
            if virtual_card.status != 'active':
                # Handle inactive card
                return redirect('/withdraw/')

            # Update virtual card spending
            virtual_card.daily_spent += wamount
            virtual_card.monthly_spent += wamount
            virtual_card.save()

            # Create regular transaction for account tracking
            transaction = Transaction.objects.create(
                account=act,
                transaction_type="Virtual Card Withdraw",
                amount=wamount,
                description=f"Virtual Card Withdrawal - {descr}"
            )

            # Create card transaction linked to the transaction
            CardTransaction.objects.create(
                virtual_card=virtual_card,
                transaction=transaction,
                merchant_name="ATM Withdrawal",
                merchant_category="ATM",
                is_online=False
            )

            # Update AI memory for virtual card withdrawal
            try:
                user = Useracc.objects.get(username=username)
                AIInsight.objects.create(
                    user=user,
                    insight_type='card_transaction',
                    title='Virtual Card Withdrawal',
                    description=f'ATM withdrawal of ₹{wamount} made using virtual card. Remaining daily limit: ₹{virtual_card.get_remaining_daily_limit()}',
                    confidence_score=0.95,
                    metadata={
                        'card_id': virtual_card.id,
                        'amount': wamount,
                        'transaction_type': 'withdrawal',
                        'remaining_daily_limit': virtual_card.get_remaining_daily_limit(),
                        'remaining_monthly_limit': virtual_card.get_remaining_monthly_limit()
                    }
                )
            except Exception as e:
                pass  # Don't fail the transaction if AI memory update fails
        else:
            # Regular account withdrawal
            Transaction.objects.create(
                account=act,
                transaction_type="Withdraw",
                amount=wamount,
                description=descr
            )

        # Deduct from account balance regardless of source
        act.AccountBalance-=wamount
        act.save()
        # Get user email from Useracc model
        user = Useracc.objects.get(username=username)
        send_transaction_email(
            to_email=user.email,
            subject='PayRupee: Withdrawal Confirmation',
            message=f'''Dear {user.fullname},

This is to confirm that a withdrawal of ₹{wamount} has been processed from your PayRupee account.

Transaction Details:
- Amount Withdrawn: ₹{wamount}
- Account Number: {act.AccountNumber}
- Transaction Type: Withdrawal
- Description: {descr}

Your updated account balance is ₹{act.AccountBalance}.

If you did not authorize this withdrawal or notice any discrepancies, please contact our customer support immediately at 37347@yenepoya.edu.in or call our 24/7 helpline at +918590191091.

Thank you for banking with PayRupee.

Regards,
PayRupee Banking Team
'''
        )

        # Set success message for withdraw page
        request.session['withdraw_success'] = f'Withdrawal of ₹{wamount} completed successfully!'
        return redirect('/withdraw/')






@login_required_custom

def deposit(request):
    username = request.session.get('username')
    act=Account.objects.get(AccountUsername=username)

    # Get success message if exists
    success_message = request.session.pop('deposit_success', None)

    con={
        "act":act,
        "success_message": success_message,
    }

    return render(request,'deposit.html',con)



@login_required_custom

def depositprocess(request):
    username = request.session.get('username')
    act=Account.objects.get(AccountUsername=username)
    if request.method=="POST":
        depamount=request.POST['amount']
        descr=request.POST['description']
        act.AccountBalance+=int(depamount)
        act.save()
        Transaction.objects.create(
    account=act,
    transaction_type="Deposit",
    amount=depamount,
    description=descr
)

        # Get user email from Useracc model
        user = Useracc.objects.get(username=username)
        send_transaction_email(
            to_email=user.email,
            subject='PayRupee: Deposit Confirmation',
            message=f'''Dear {user.fullname},

We are pleased to confirm that a deposit of ₹{depamount} has been successfully credited to your PayRupee account.

Transaction Details:
- Amount Deposited: ₹{depamount}
- Account Number: {act.AccountNumber}
- Transaction Type: Deposit
- Description: {descr}

Your updated account balance is ₹{act.AccountBalance}.

Thank you for choosing PayRupee for your banking needs. If you have any questions or require further assistance, please contact our customer support at 37347@yenepoya.edu.in or call our 24/7 helpline at +918590191091.

Regards,
PayRupee Banking Team
'''
        )

        # Set success message for deposit page
        request.session['deposit_success'] = f'Deposit of ₹{depamount} completed successfully!'
        return redirect('/deposit/')












@login_required_custom

def forgotpassword(request):
    return render(request,'forgotpassword.html')





# Security utility functions
def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def generate_device_fingerprint(request):
    """Generate device fingerprint from request data"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')

    # Create a unique device ID based on browser characteristics
    device_string = f"{user_agent}{accept_language}{accept_encoding}"
    device_id = hashlib.md5(device_string.encode()).hexdigest()

    return device_id

def get_location_from_ip(ip_address):
    """Get location data from IP address (mock implementation)"""
    # In a real implementation, you would use a service like ipapi.co or similar
    # For demo purposes, returning mock data
    return {
        'city': 'Mumbai',
        'region': 'Maharashtra',
        'country': 'India',
        'latitude': 19.0760,
        'longitude': 72.8777
    }

def check_suspicious_activity(user, activity_type, details=None):
    """Check and log suspicious activity"""
    risk_level = 'low'
    description = ''

    if activity_type == 'high_amount':
        amount = details.get('amount', 0) if details else 0
        if amount > 100000:
            risk_level = 'critical'
            description = f'High amount transaction of ₹{amount}'
        elif amount > 50000:
            risk_level = 'high'
            description = f'Large transaction of ₹{amount}'

    elif activity_type == 'new_device':
        risk_level = 'medium'
        description = 'Login from new device detected'

    elif activity_type == 'unusual_login':
        risk_level = 'medium'
        description = 'Login from unusual location'

    # Create suspicious activity record
    SuspiciousActivity.objects.create(
        user=user,
        activity_type=activity_type,
        risk_level=risk_level,
        description=description,
        details=json.dumps(details) if details else ''
    )

@login_required_custom
def security(request):
    username = request.session.get('username')
    user = Useracc.objects.get(username=username)

    # Get or create security settings
    security_settings, created = SecuritySettings.objects.get_or_create(
        user=user,
        defaults={
            'daily_transaction_limit': 50000.0,
            'single_transaction_limit': 25000.0,
            'monthly_spending_cap': 200000.0,
        }
    )

    # Get recent login activities
    recent_logins = LoginActivity.objects.filter(user=user).order_by('-login_time')[:10]

    # Get trusted devices
    trusted_devices = DeviceFingerprint.objects.filter(user=user, is_trusted=True)

    # Get suspicious activities
    suspicious_activities = SuspiciousActivity.objects.filter(
        user=user, resolved=False
    ).order_by('-detected_at')[:5]

    # Get current spending for today and this month
    today = timezone.now().date()
    current_month = today.replace(day=1)

    today_spending = TransactionLimit.objects.filter(
        user=user, date=today
    ).first()

    monthly_spending = TransactionLimit.objects.filter(
        user=user, date__gte=current_month
    ).aggregate(total=Sum('daily_spent'))['total'] or 0

    # Get account information to match other templates
    account = Account.objects.get(AccountUsername=username)

    context = {
        'user': user,
        'act': account,  # Add account info for consistency with other templates
        'security_settings': security_settings,
        'recent_logins': recent_logins,
        'trusted_devices': trusted_devices,
        'suspicious_activities': suspicious_activities,
        'today_spending': today_spending.daily_spent if today_spending else 0,
        'monthly_spending': monthly_spending,
        'spending_percentage': (monthly_spending / security_settings.monthly_spending_cap * 100) if monthly_spending else 0,
    }

    return render(request, 'security.html', context)

@login_required_custom
@csrf_exempt
def update_security_settings(request):
    """Update user security settings"""
    if request.method == 'POST':
        username = request.session.get('username')
        user = Useracc.objects.get(username=username)

        security_settings, created = SecuritySettings.objects.get_or_create(user=user)

        # Update settings from form data
        security_settings.daily_transaction_limit = float(request.POST.get('daily_limit', 50000))
        security_settings.single_transaction_limit = float(request.POST.get('single_limit', 25000))
        security_settings.monthly_spending_cap = float(request.POST.get('monthly_cap', 200000))
        security_settings.security_alerts_enabled = request.POST.get('security_alerts') == 'on'
        security_settings.login_notifications = request.POST.get('login_notifications') == 'on'
        security_settings.transaction_notifications = request.POST.get('transaction_notifications') == 'on'

        security_settings.save()

        return JsonResponse({'status': 'success', 'message': 'Security settings updated successfully'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required_custom
@csrf_exempt
def trust_device(request):
    """Mark a device as trusted"""
    if request.method == 'POST':
        username = request.session.get('username')
        user = Useracc.objects.get(username=username)
        device_id = request.POST.get('device_id')
        device_name = request.POST.get('device_name', 'Unknown Device')
        browser_info = request.POST.get('browser_info', 'Unknown Browser')

        try:
            # Try to get existing device or create new one
            device, created = DeviceFingerprint.objects.get_or_create(
                device_id=device_id,
                user=user,
                defaults={
                    'device_name': device_name,
                    'browser_info': browser_info,
                    'is_trusted': True,
                    'last_seen': timezone.now()
                }
            )

            if not created:
                # Update existing device
                device.is_trusted = True
                device.last_seen = timezone.now()
                device.save()

            return JsonResponse({'status': 'success', 'message': 'Device marked as trusted'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error trusting device: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required_custom
@csrf_exempt
def remove_trusted_device(request):
    """Remove a device from trusted list"""
    if request.method == 'POST':
        username = request.session.get('username')
        user = Useracc.objects.get(username=username)
        device_id = request.POST.get('device_id')

        try:
            device = DeviceFingerprint.objects.get(device_id=device_id, user=user)
            device.is_trusted = False
            device.save()
            return JsonResponse({'status': 'success', 'message': 'Device removed from trusted list'})
        except DeviceFingerprint.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Device not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required_custom
@csrf_exempt
def resolve_suspicious_activity(request):
    """Mark suspicious activity as resolved"""
    if request.method == 'POST':
        username = request.session.get('username')
        user = Useracc.objects.get(username=username)
        activity_id = request.POST.get('activity_id')

        try:
            activity = SuspiciousActivity.objects.get(id=activity_id, user=user)
            activity.resolved = True
            activity.resolved_at = timezone.now()
            activity.resolved_by = username
            activity.save()
            return JsonResponse({'status': 'success', 'message': 'Activity marked as resolved'})
        except SuspiciousActivity.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Activity not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required_custom
def settingss(request):
    return render(request,'settingss.html')




@login_required_custom

def logout_view(request):
    request.session.flush()
    if 'msgl' in request.session:
            del request.session['msgl']
    # Clears all session data
    return redirect('/')

@login_required_custom
def transaction_history(request):
    username = request.session.get('username')
    account = Account.objects.get(AccountUsername=username)
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')

    return render(request, 'transaction_history.html', {
        'account': account,
        'transactions': transactions
    })

@login_required_custom
def download_transactions_pdf(request):
    # Get user account and transactions
    username = request.session.get('username')
    account = Account.objects.get(AccountUsername=username)
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')

    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file"
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Set up the PDF document
    p.setTitle(f"Transaction History - {account.AccountNumber}")

    # Add header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(inch, height - inch, "PayRupee Banking")

    # Add document title
    p.setFont("Helvetica-Bold", 14)
    p.drawString(inch, height - 1.5*inch, "Transaction History")

    # Add account information
    p.setFont("Helvetica-Bold", 12)
    p.drawString(inch, height - 2*inch, "Account Details:")

    p.setFont("Helvetica", 10)
    p.drawString(inch, height - 2.3*inch, f"Account Number: {account.AccountNumber}")
    p.drawString(inch, height - 2.5*inch, f"Account Holder: {account.AccountHolder}")
    p.drawString(inch, height - 2.7*inch, f"Current Balance: ₹{account.AccountBalance}")

    # Add current date
    from datetime import datetime
    current_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    p.setFont("Helvetica", 10)
    p.drawString(inch, height - 3*inch, f"Generated on: {current_date}")

    # Draw a simple line
    p.line(inch, height - 3.2*inch, width - inch, height - 3.2*inch)

    # Create table data
    data = [["Date & Time", "Transaction Type", "Amount", "Description"]]

    # Add transaction data to table
    for txn in transactions:
        # Format the timestamp
        timestamp = txn.timestamp.strftime("%d-%m-%Y %H:%M")

        # Format the amount with ₹ symbol
        if txn.transaction_type in ["Deposit", "Transfer In"]:
            amount = f"₹{txn.amount} (Credit)"
        else:
            amount = f"₹{txn.amount} (Debit)"

        data.append([timestamp, txn.transaction_type, amount, txn.description])

    # Create the table
    table = Table(data, colWidths=[1.3*inch, 1.3*inch, 1.3*inch, 3*inch])

    # Style the table - simple black and white
    table_style = TableStyle([
        # Header style
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),

        # Row styles
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

        # Column alignment
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),  # Amount column right-aligned
    ])

    table.setStyle(table_style)

    # Draw the table on the PDF
    table.wrapOn(p, width - 2*inch, height)
    table.drawOn(p, inch, height - 3.5*inch - len(data)*15)  # Adjust position based on table size

    # Add footer
    p.setFont("Helvetica", 8)
    p.drawString(inch, inch, "PayRupee Banking - Transactions Made Easy")
    p.drawString(inch, 0.8*inch, "For any queries, please contact 37347@yenepoya.edu.in | +91 8590191091")

    # Add page number
    p.drawRightString(width - inch, 0.8*inch, f"Page 1")

    # Close the PDF object cleanly
    p.showPage()
    p.save()

    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()

    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    filename = f"PayRupee_Statement_{account.AccountNumber.replace(' ', '_').replace('-', '_')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = len(pdf)
    response.write(pdf)

    return response

@login_required_custom
def download_account_details_pdf(request):
    try:
        # Get user account
        username = request.session.get('username')
        if not username:
            return HttpResponse("User not logged in", status=401)

        account = Account.objects.get(AccountUsername=username)
        user = Useracc.objects.get(username=username)

        # Get recent transactions (limit to 5)
        recent_transactions = Transaction.objects.filter(account=account).order_by('-timestamp')[:5]

        # Create a file-like buffer to receive PDF data
        buffer = io.BytesIO()

        # Create the PDF object, using the buffer as its "file"
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Set up the PDF document
        p.setTitle(f"Account Details - {account.AccountNumber}")

        # Add header with logo styling
        p.setFillColorRGB(0.9, 0.49, 0.13)  # Orange color for PayRupee
        p.setFont("Helvetica-Bold", 24)
        p.drawString(inch, height - inch, "Pay")
        p.setFillColorRGB(0.2, 0.29, 0.37)  # Dark blue for Rupee
        p.drawString(inch + 50, height - inch, "Rupee")

        # Reset color to black
        p.setFillColorRGB(0, 0, 0)

        # Add tagline
        p.setFont("Helvetica", 12)
        p.drawString(inch, height - 1.3*inch, "Transactions Made Easy")

        # Add document title
        p.setFont("Helvetica-Bold", 18)
        p.drawString(inch, height - 2*inch, "Account Details")

        # Add decorative line
        p.setStrokeColorRGB(0.9, 0.49, 0.13)  # Orange color
        p.setLineWidth(2)
        p.line(inch, height - 2.2*inch, 3*inch, height - 2.2*inch)

        # Reset stroke color
        p.setStrokeColorRGB(0, 0, 0)
        p.setLineWidth(1)

        # Add account holder information section
        p.setFont("Helvetica-Bold", 14)
        p.drawString(inch, height - 2.7*inch, "Account Holder Information")

        p.setFont("Helvetica", 11)
        p.drawString(inch, height - 3*inch, f"Name: {account.AccountHolder}")
        p.drawString(inch, height - 3.3*inch, f"Username: {username}")
        p.drawString(inch, height - 3.6*inch, f"Email: {user.email}")

        # Add account details section
        p.setFont("Helvetica-Bold", 14)
        p.drawString(inch, height - 4.1*inch, "Account Details")

        p.setFont("Helvetica", 11)
        p.drawString(inch, height - 4.4*inch, f"Account Number: {account.AccountNumber}")
        p.drawString(inch, height - 4.7*inch, f"Account Type: {account.AccountType}")
        p.drawString(inch, height - 5*inch, f"Account Status: {account.AccountStatus}")
        p.drawString(inch, height - 5.3*inch, f"Current Balance: ₹{account.AccountBalance}")
        p.drawString(inch, height - 5.6*inch, f"Date Opened: {account.DateOpened.strftime('%d-%m-%Y')}")

        # Add recent activity section if there are transactions
        if recent_transactions:
            p.setFont("Helvetica-Bold", 14)
            p.drawString(inch, height - 6.1*inch, "Recent Activity")

            # Create table data for recent transactions
            data = [["Date", "Type", "Amount", "Description"]]

            for txn in recent_transactions:
                # Format the timestamp
                timestamp = txn.timestamp.strftime("%d-%m-%Y")

                # Format the amount with ₹ symbol
                if txn.transaction_type in ["Deposit", "Transfer In"]:
                    amount = f"₹{txn.amount} (Credit)"
                else:
                    amount = f"₹{txn.amount} (Debit)"

                # Truncate description if too long
                description = txn.description[:30] + "..." if len(txn.description) > 30 else txn.description

                data.append([timestamp, txn.transaction_type, amount, description])

            # Create the table
            table = Table(data, colWidths=[1*inch, 1.2*inch, 1.3*inch, 3*inch])

            # Style the table
            table_style = TableStyle([
                # Header style
                ('BACKGROUND', (0, 0), (-1, 0), colors.black),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),

                # Row styles
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),

                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

                # Column alignment
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),  # Amount column right-aligned
            ])

            table.setStyle(table_style)

            # Draw the table on the PDF
            table.wrapOn(p, width - 2*inch, height)
            table.drawOn(p, inch, height - 6.3*inch - len(data)*15)

        # Add current date
        from datetime import datetime
        current_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        p.setFont("Helvetica", 9)
        p.drawString(inch, 2*inch, f"Generated on: {current_date}")

        # Add footer with contact information
        p.setFont("Helvetica", 8)
        p.drawString(inch, 1.5*inch, "PayRupee Banking - Transactions Made Easy")
        p.drawString(inch, 1.3*inch, "For any queries, please contact 37347@yenepoya.edu.in | +91 8590191091")

        # Add security note
        p.setFont("Helvetica", 7)
        p.drawString(inch, 1*inch, "This document contains confidential information. Please keep it secure.")

        # Add page number
        p.drawRightString(width - inch, inch, f"Page 1 of 1")

        # Close the PDF object cleanly
        p.showPage()
        p.save()

        # Get the value of the BytesIO buffer and write it to the response
        pdf = buffer.getvalue()
        buffer.close()

        # Create the HttpResponse object with PDF headers
        response = HttpResponse(content_type='application/pdf')
        filename = f"PayRupee_Account_Details_{account.AccountNumber.replace(' ', '_').replace('-', '_')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(pdf)
        response.write(pdf)

        return response

    except Account.DoesNotExist:
        return HttpResponse("Account not found", status=404)
    except Useracc.DoesNotExist:
        return HttpResponse("User not found", status=404)
    except Exception as e:
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)


# AI Chatbot Views
@login_required_custom
def ai_chat_start(request):
    """Start a new AI chat conversation"""
    if request.method == 'POST':
        username = request.session.get('username')
        user = Useracc.objects.get(username=username)

        # Create AI assistant instance
        ai_assistant = AIFinancialAssistant(user)

        # Start conversation
        conversation = ai_assistant.start_conversation()

        # Get welcome message
        welcome_message = conversation.messages.first().content

        return JsonResponse({
            'status': 'success',
            'conversation_id': conversation.id,
            'welcome_message': welcome_message
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required_custom
def ai_chat_message(request):
    """Process AI chat message"""
    if request.method == 'POST':
        username = request.session.get('username')
        user = Useracc.objects.get(username=username)

        conversation_id = request.POST.get('conversation_id')
        message = request.POST.get('message')

        try:
            conversation = ChatConversation.objects.get(id=conversation_id, user=user)

            # Create AI assistant instance
            ai_assistant = AIFinancialAssistant(user)

            # Process message and get response
            response = ai_assistant.process_message(conversation, message)

            return JsonResponse({
                'status': 'success',
                'response': response
            })

        except ChatConversation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Conversation not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required_custom
def ai_dashboard_insights(request):
    """Get AI-generated dashboard insights"""
    username = request.session.get('username')
    user = Useracc.objects.get(username=username)

    # Create AI assistant instance
    ai_assistant = AIFinancialAssistant(user)

    # Generate fresh insights
    insights = ai_assistant.generate_insights()

    # Get recent insights from database
    recent_insights = AIInsight.objects.filter(user=user)[:5]

    insights_data = []
    for insight in recent_insights:
        insights_data.append({
            'type': insight.insight_type,
            'title': insight.title,
            'description': insight.description,
            'created_at': insight.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return JsonResponse({
        'status': 'success',
        'insights': insights_data
    })


# Virtual Card Views
@login_required_custom
def virtual_cards(request):
    """Display all virtual cards for the user"""
    username = request.session.get('username')
    account = Account.objects.get(AccountUsername=username)
    cards = VirtualCard.objects.filter(account=account).order_by('-created_at')

    # Return JSON data for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        cards_data = []
        for card in cards:
            cards_data.append({
                'id': card.id,
                'card_type': card.card_type,
                'masked_card_number': card.masked_card_number,
                'card_holder_name': card.card_holder_name,
                'status': card.status,
                'daily_limit': card.daily_limit,
                'monthly_limit': card.monthly_limit,
                'expiry_month': card.expiry_month,
                'expiry_year': card.expiry_year,
                'online_transactions_enabled': card.online_transactions_enabled,
                'international_transactions_enabled': card.international_transactions_enabled,
                'contactless_enabled': card.contactless_enabled,
            })

        return JsonResponse({
            'status': 'success',
            'cards': cards_data
        })

    # For regular requests, return a simple HTML response
    html_content = '<div class="virtual-cards-data">'
    for card in cards:
        status_emoji = "✅" if card.status == 'active' else "❄️" if card.status == 'frozen' else "❌"
        features = []
        if card.online_transactions_enabled:
            features.append("🌐 Online")
        if card.international_transactions_enabled:
            features.append("✈️ International")
        if card.contactless_enabled:
            features.append("📱 Contactless")

        freeze_btn = f"<button class='card-action-btn' onclick='toggleCardStatus({card.id}, \"freeze\")'><i class='fas fa-pause'></i> Freeze</button>" if card.status == 'active' else ""
        activate_btn = f"<button class='card-action-btn' onclick='toggleCardStatus({card.id}, \"activate\")'><i class='fas fa-play'></i> Activate</button>" if card.status == 'frozen' else ""

        html_content += f'''
        <div class="virtual-card" data-card-id="{card.id}">
            <div class="card-header">
                <div class="card-type">{card.card_type.title()} Card</div>
                <div class="card-status {card.status}">{card.status.title()}</div>
            </div>
            <div class="card-number">{card.masked_card_number}</div>
            <div class="card-details">
                <div class="card-holder">
                    <div class="card-holder-label">Card Holder</div>
                    <div class="card-holder-name">{card.card_holder_name}</div>
                </div>
                <div class="card-expiry">
                    <div class="card-expiry-label">Expires</div>
                    <div class="card-expiry-date">{card.expiry_month}/{card.expiry_year}</div>
                </div>
            </div>
            <div class="card-limits">
                <div class="limit-item">
                    <span class="limit-label">Daily Limit:</span>
                    <span class="limit-value">₹{card.daily_limit:,.0f}</span>
                </div>
                <div class="limit-item">
                    <span class="limit-label">Monthly Limit:</span>
                    <span class="limit-value">₹{card.monthly_limit:,.0f}</span>
                </div>
            </div>
            <div class="card-features">
                {" ".join([f'<span class="feature-badge enabled">{feature}</span>' for feature in features])}
            </div>
            <div class="card-actions">
                {freeze_btn}{activate_btn}
                <button class="card-action-btn" onclick="viewCardDetails({card.id})">
                    <i class="fas fa-eye"></i> Details
                </button>
                <button class="card-action-btn" onclick="manageCardLimits({card.id})">
                    <i class="fas fa-cog"></i> Settings
                </button>
            </div>
        </div>
        '''

    html_content += '</div>'

    from django.http import HttpResponse
    return HttpResponse(html_content)


@login_required_custom
def create_virtual_card(request):
    """Create a new virtual card"""
    if request.method == 'POST':
        username = request.session.get('username')
        account = Account.objects.get(AccountUsername=username)

        # Generate card details
        import random
        from datetime import datetime, timedelta

        # Generate card number (starting with 4 for Visa-like)
        card_number = '4' + ''.join([str(random.randint(0, 9)) for _ in range(15)])

        # Generate CVV
        cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])

        # Set expiry date (3 years from now)
        expiry_date = datetime.now() + timedelta(days=365*3)
        expiry_month = f"{expiry_date.month:02d}"
        expiry_year = str(expiry_date.year)

        # Get form data
        card_type = request.POST.get('card_type', 'debit')
        daily_limit = float(request.POST.get('daily_limit', 25000))
        monthly_limit = float(request.POST.get('monthly_limit', 100000))
        online_enabled = request.POST.get('online_transactions') == 'on'
        international_enabled = request.POST.get('international_transactions') == 'on'
        contactless_enabled = request.POST.get('contactless_enabled') == 'on'

        # Create virtual card
        virtual_card = VirtualCard.objects.create(
            account=account,
            card_number=card_number,
            card_holder_name=account.AccountHolder.upper(),
            expiry_month=expiry_month,
            expiry_year=expiry_year,
            cvv=cvv,
            card_type=card_type,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
            online_transactions_enabled=online_enabled,
            international_transactions_enabled=international_enabled,
            contactless_enabled=contactless_enabled,
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Virtual card created successfully!',
            'card_id': virtual_card.id
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required_custom
def card_details(request, card_id):
    """Redirect to accounts page since card details are now shown in popup"""
    return redirect('accounts')


@login_required_custom
def toggle_card_status(request):
    """Freeze/Unfreeze a virtual card"""
    if request.method == 'POST':
        username = request.session.get('username')
        account = Account.objects.get(AccountUsername=username)
        card_id = request.POST.get('card_id')

        try:
            card = VirtualCard.objects.get(id=card_id, account=account)

            if card.status == 'active':
                card.status = 'frozen'
                message = 'Card has been frozen successfully'
            elif card.status == 'frozen':
                card.status = 'active'
                message = 'Card has been activated successfully'
            else:
                return JsonResponse({'status': 'error', 'message': 'Cannot change status of this card'})

            card.save()

            return JsonResponse({
                'status': 'success',
                'message': message,
                'new_status': card.status
            })
        except VirtualCard.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Card not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required_custom
def update_card_limits(request):
    """Update card spending limits"""
    if request.method == 'POST':
        username = request.session.get('username')
        account = Account.objects.get(AccountUsername=username)
        card_id = request.POST.get('card_id')

        try:
            card = VirtualCard.objects.get(id=card_id, account=account)

            daily_limit = float(request.POST.get('daily_limit', card.daily_limit))
            monthly_limit = float(request.POST.get('monthly_limit', card.monthly_limit))

            card.daily_limit = daily_limit
            card.monthly_limit = monthly_limit
            card.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Card limits updated successfully'
            })
        except VirtualCard.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Card not found'})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid limit values'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required_custom
def delete_virtual_card(request):
    """Delete/Cancel a virtual card"""
    if request.method == 'POST':
        username = request.session.get('username')
        account = Account.objects.get(AccountUsername=username)
        card_id = request.POST.get('card_id')

        try:
            card = VirtualCard.objects.get(id=card_id, account=account)
            card.status = 'cancelled'
            card.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Card has been cancelled successfully'
            })
        except VirtualCard.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Card not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required_custom
def ai_update_memory(request):
    """Update AI chatbot memory with new events"""
    if request.method == 'POST':
        import json
        username = request.session.get('username')
        user = Useracc.objects.get(username=username)

        try:
            data = json.loads(request.body)
            event_type = data.get('event_type')
            event_data = data.get('data')

            # Create AI insight based on the event
            if event_type == 'virtual_card_created':
                title = "New Virtual Card Created"
                description = f"You created a new {event_data.get('card_type')} virtual card with daily limit ₹{event_data.get('daily_limit')} and monthly limit ₹{event_data.get('monthly_limit')}."
                insight_type = 'card_management'

            elif event_type == 'virtual_card_status_changed':
                action = event_data.get('action')
                new_status = event_data.get('new_status')
                title = f"Virtual Card {action.title()}d"
                description = f"Your virtual card status has been changed to {new_status}."
                insight_type = 'card_management'

            elif event_type == 'virtual_card_limits_updated':
                title = "Card Limits Updated"
                description = f"Virtual card spending limits updated: Daily ₹{event_data.get('daily_limit')}, Monthly ₹{event_data.get('monthly_limit')}."
                insight_type = 'card_management'

            else:
                title = "Account Activity"
                description = f"New activity recorded: {event_type}"
                insight_type = 'general'

            # Create AI insight record
            AIInsight.objects.create(
                user=user,
                insight_type=insight_type,
                title=title,
                description=description,
                confidence_score=0.95,
                metadata=event_data
            )

            return JsonResponse({
                'status': 'success',
                'message': 'AI memory updated successfully'
            })

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
