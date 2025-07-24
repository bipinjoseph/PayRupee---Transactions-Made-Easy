from django.db import models
from django.utils import timezone
import json

# Create your models here.


class Useracc(models.Model):
    username=models.CharField(max_length=100)
    fullname=models.CharField(max_length=100)
    email=models.EmailField()
    passwrd=models.CharField(max_length=100)



class Account(models.Model):
    AccountHolder=models.CharField(max_length=100)
    AccountNumber=models.CharField(max_length=100,blank=True)
    AccountType=models.CharField(max_length=100)
    AccountStatus=models.CharField(max_length=100)
    AccountBalance=models.FloatField()
    DateOpened=models.DateTimeField(default=timezone.now)
    AccountUsername=models.CharField(max_length=100)




class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('Deposit', 'Deposit'),
        ('Withdraw', 'Withdraw'),
        ('Transfer Out', 'Transfer Out'),  # Sent to someone
        ('Transfer In', 'Transfer In'),    # Received from someone
        ('Virtual Card Transfer', 'Virtual Card Transfer'),  # Virtual card transfers
        ('Virtual Card Withdraw', 'Virtual Card Withdraw'),  # Virtual card withdrawals
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    amount = models.FloatField()
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.account.AccountUsername} - {self.transaction_type} - {self.amount}"


# Security Models
class SecuritySettings(models.Model):
    user = models.OneToOneField(Useracc, on_delete=models.CASCADE, related_name='security_settings')
    daily_transaction_limit = models.FloatField(default=50000.0)  # Default 50,000 INR
    single_transaction_limit = models.FloatField(default=25000.0)  # Default 25,000 INR
    monthly_spending_cap = models.FloatField(default=200000.0)  # Default 2,00,000 INR
    security_alerts_enabled = models.BooleanField(default=True)
    login_notifications = models.BooleanField(default=True)
    transaction_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Security Settings for {self.user.username}"


class DeviceFingerprint(models.Model):
    user = models.ForeignKey(Useracc, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=200, blank=True)
    browser_info = models.TextField()
    screen_resolution = models.CharField(max_length=50, blank=True)
    user_timezone = models.CharField(max_length=100, blank=True)
    language = models.CharField(max_length=50, blank=True)
    is_trusted = models.BooleanField(default=False)
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)
    login_count = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.user.username} - {self.device_name or 'Unknown Device'}"


class LoginActivity(models.Model):
    user = models.ForeignKey(Useracc, on_delete=models.CASCADE, related_name='login_activities')
    device = models.ForeignKey(DeviceFingerprint, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    location_data = models.TextField(blank=True)  # JSON string for location info
    login_time = models.DateTimeField(default=timezone.now)
    success = models.BooleanField(default=True)
    risk_score = models.IntegerField(default=0)  # 0-100 risk score
    user_agent = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.login_time} - {'Success' if self.success else 'Failed'}"

    def get_location_data(self):
        if self.location_data:
            try:
                return json.loads(self.location_data)
            except:
                return {}
        return {}


class SuspiciousActivity(models.Model):
    ACTIVITY_TYPES = [
        ('unusual_login', 'Unusual Login Location'),
        ('high_amount', 'High Amount Transaction'),
        ('frequent_transactions', 'Frequent Transactions'),
        ('new_device', 'New Device Login'),
        ('failed_login', 'Multiple Failed Logins'),
        ('limit_exceeded', 'Transaction Limit Exceeded'),
    ]

    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    user = models.ForeignKey(Useracc, on_delete=models.CASCADE, related_name='suspicious_activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS)
    description = models.TextField()
    details = models.TextField(blank=True)  # JSON string for additional details
    detected_at = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.risk_level}"

    def get_details(self):
        if self.details:
            try:
                return json.loads(self.details)
            except:
                return {}
        return {}


class TransactionLimit(models.Model):
    user = models.ForeignKey(Useracc, on_delete=models.CASCADE, related_name='transaction_limits')
    date = models.DateField(default=timezone.now)
    daily_spent = models.FloatField(default=0.0)
    monthly_spent = models.FloatField(default=0.0)
    transaction_count = models.IntegerField(default=0)
    last_transaction = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.username} - {self.date} - ₹{self.daily_spent}"


# Virtual Card Models
class VirtualCard(models.Model):
    CARD_STATUS_CHOICES = [
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    CARD_TYPE_CHOICES = [
        ('debit', 'Debit Card'),
        ('prepaid', 'Prepaid Card'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='virtual_cards')
    card_number = models.CharField(max_length=16, unique=True)
    card_holder_name = models.CharField(max_length=100)
    expiry_month = models.CharField(max_length=2)
    expiry_year = models.CharField(max_length=4)
    cvv = models.CharField(max_length=3)
    card_type = models.CharField(max_length=10, choices=CARD_TYPE_CHOICES, default='debit')
    status = models.CharField(max_length=10, choices=CARD_STATUS_CHOICES, default='active')
    daily_limit = models.FloatField(default=25000.0)
    monthly_limit = models.FloatField(default=100000.0)
    daily_spent = models.FloatField(default=0.0)
    monthly_spent = models.FloatField(default=0.0)
    last_transaction_date = models.DateField(null=True, blank=True)
    online_transactions_enabled = models.BooleanField(default=True)
    international_transactions_enabled = models.BooleanField(default=False)
    contactless_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.card_holder_name} - {self.card_number[-4:]} - {self.status}"

    @property
    def masked_card_number(self):
        return f"**** **** **** {self.card_number[-4:]}"

    @property
    def is_expired(self):
        from datetime import datetime
        current_date = datetime.now()
        expiry_date = datetime(int(self.expiry_year), int(self.expiry_month), 1)
        return current_date > expiry_date

    def reset_monthly_spending_if_needed(self):
        """Reset monthly spending if it's a new month"""
        from datetime import date
        today = date.today()
        if self.last_transaction_date:
            if self.last_transaction_date.month != today.month or self.last_transaction_date.year != today.year:
                self.monthly_spent = 0.0
        return self

    def get_remaining_daily_limit(self):
        """Get remaining daily limit"""
        return max(0, self.daily_limit - self.daily_spent)

    def get_remaining_monthly_limit(self):
        """Get remaining monthly limit"""
        return max(0, self.monthly_limit - self.monthly_spent)


class CardTransaction(models.Model):
    TRANSACTION_STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
        ('declined', 'Declined'),
    ]

    virtual_card = models.ForeignKey(VirtualCard, on_delete=models.CASCADE, related_name='card_transactions')
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='card_transaction')
    merchant_name = models.CharField(max_length=200, blank=True)
    merchant_category = models.CharField(max_length=100, blank=True)
    transaction_status = models.CharField(max_length=10, choices=TRANSACTION_STATUS_CHOICES, default='success')
    is_online = models.BooleanField(default=True)
    is_international = models.BooleanField(default=False)
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.virtual_card.card_number[-4:]} - {self.merchant_name} - ₹{self.transaction.amount}"


# AI Financial Assistant Models
class FinancialGoal(models.Model):
    GOAL_TYPES = [
        ('savings', 'Savings Goal'),
        ('investment', 'Investment Goal'),
        ('debt_payoff', 'Debt Payoff'),
        ('emergency_fund', 'Emergency Fund'),
        ('vacation', 'Vacation Fund'),
        ('home', 'Home Purchase'),
        ('education', 'Education Fund'),
        ('retirement', 'Retirement Fund'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(Useracc, on_delete=models.CASCADE, related_name='financial_goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_amount = models.FloatField()
    current_amount = models.FloatField(default=0.0)
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    ai_suggestions = models.TextField(blank=True)  # JSON string for AI recommendations

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return min((self.current_amount / self.target_amount) * 100, 100)
        return 0

    @property
    def remaining_amount(self):
        return max(self.target_amount - self.current_amount, 0)


class ExpenseCategory(models.Model):
    CATEGORY_TYPES = [
        ('food', 'Food & Dining'),
        ('transportation', 'Transportation'),
        ('shopping', 'Shopping'),
        ('entertainment', 'Entertainment'),
        ('bills', 'Bills & Utilities'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('travel', 'Travel'),
        ('investment', 'Investment'),
        ('savings', 'Savings'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(Useracc, on_delete=models.CASCADE, related_name='expense_categories')
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    monthly_budget = models.FloatField(default=0.0)
    current_spending = models.FloatField(default=0.0)
    ai_recommended_budget = models.FloatField(default=0.0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'category_type']

    def __str__(self):
        return f"{self.user.username} - {self.get_category_type_display()}"

    @property
    def budget_utilization(self):
        if self.monthly_budget > 0:
            return min((self.current_spending / self.monthly_budget) * 100, 100)
        return 0


class TransactionCategory(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='category')
    category_type = models.CharField(max_length=20, choices=ExpenseCategory.CATEGORY_TYPES)
    confidence_score = models.FloatField(default=0.0)  # AI confidence in categorization
    is_manual = models.BooleanField(default=False)  # Whether user manually categorized
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.transaction} - {self.get_category_type_display()}"


class UpcomingTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('Deposit', 'Deposit'),
        ('Withdraw', 'Withdraw'),
        ('Transfer Out', 'Transfer Out'),  # Sent to someone
        ('Transfer In', 'Transfer In'),    # Received from someone
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='upcoming_transactions')
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    amount = models.FloatField()
    description = models.TextField(blank=True)
    scheduled_date = models.DateTimeField()  # When the transaction is scheduled to execute
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    recipient_account = models.CharField(max_length=100, blank=True)  # For transfers
    recipient_name = models.CharField(max_length=100, blank=True)  # For transfers
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    executed_at = models.DateTimeField(null=True, blank=True)  # When actually executed

    class Meta:
        ordering = ['scheduled_date']
        verbose_name = 'Upcoming Transaction'
        verbose_name_plural = 'Upcoming Transactions'

    def __str__(self):
        return f"{self.account.AccountUsername} - {self.transaction_type} - ₹{self.amount} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_overdue(self):
        """Check if scheduled transaction is overdue"""
        return self.scheduled_date < timezone.now() and self.status == 'scheduled'

    @property
    def days_until_execution(self):
        """Calculate days until execution"""
        if self.status in ['completed', 'cancelled', 'failed']:
            return None
        delta = self.scheduled_date.date() - timezone.now().date()
        return delta.days


class ChatConversation(models.Model):
    user = models.ForeignKey(Useracc, on_delete=models.CASCADE, related_name='chat_conversations')
    session_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.session_id}"


class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('user', 'User Message'),
        ('ai', 'AI Response'),
        ('system', 'System Message'),
    ]

    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    metadata = models.TextField(blank=True)  # JSON string for additional data
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.conversation.user.username} - {self.message_type} - {self.timestamp}"


class AIInsight(models.Model):
    INSIGHT_TYPES = [
        ('spending_pattern', 'Spending Pattern'),
        ('budget_recommendation', 'Budget Recommendation'),
        ('goal_suggestion', 'Goal Suggestion'),
        ('saving_opportunity', 'Saving Opportunity'),
        ('risk_alert', 'Risk Alert'),
        ('achievement', 'Achievement'),
    ]

    user = models.ForeignKey(Useracc, on_delete=models.CASCADE, related_name='ai_insights')
    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    data = models.TextField(blank=True)  # JSON string for supporting data
    is_read = models.BooleanField(default=False)
    is_actionable = models.BooleanField(default=False)
    action_taken = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
