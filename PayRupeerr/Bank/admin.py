from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

# Register your models here.
from Bank.models import (
    Useracc, Account, Transaction, UpcomingTransaction,
    TransactionCategory, SecuritySettings, DeviceFingerprint,
    LoginActivity, SuspiciousActivity, TransactionLimit,
    FinancialGoal, ExpenseCategory, ChatConversation,
    ChatMessage, AIInsight, VirtualCard, CardTransaction
)

class UseraccAdmin(admin.ModelAdmin):
    list_display=['id','username','fullname','email']
    search_fields = ['username', 'fullname', 'email']
    list_filter = ['email']


class AccountAdmin(admin.ModelAdmin):
    list_display=['id','AccountUsername','AccountHolder','AccountNumber','AccountType','AccountStatus','AccountBalance','DateOpened']
    search_fields = ['AccountUsername', 'AccountHolder', 'AccountNumber']
    list_filter = ['AccountType', 'AccountStatus', 'DateOpened']
    readonly_fields = ['DateOpened']


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'account_username', 'transaction_type', 'formatted_amount', 'description_short', 'timestamp', 'category_display']
    list_filter = ['transaction_type', 'timestamp', 'account__AccountType']
    search_fields = ['account__AccountUsername', 'description', 'amount']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

    def account_username(self, obj):
        return obj.account.AccountUsername
    account_username.short_description = 'Account Username'

    def formatted_amount(self, obj):
        if obj.transaction_type in ['Deposit', 'Transfer In']:
            return format_html('<span style="color: green;">₹{}</span>', obj.amount)
        else:
            return format_html('<span style="color: red;">₹{}</span>', obj.amount)
    formatted_amount.short_description = 'Amount'

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

    def category_display(self, obj):
        try:
            category = obj.category
            return category.get_category_type_display()
        except:
            return 'Uncategorized'
    category_display.short_description = 'Category'


class UpcomingTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'account_username', 'transaction_type', 'formatted_amount',
        'scheduled_date', 'status', 'days_remaining', 'recipient_info', 'created_at'
    ]
    list_filter = [
        'transaction_type', 'status', 'scheduled_date',
        'account__AccountType', 'created_at'
    ]
    search_fields = [
        'account__AccountUsername', 'description', 'recipient_name',
        'recipient_account', 'amount'
    ]
    readonly_fields = ['created_at', 'updated_at', 'executed_at', 'days_remaining', 'is_overdue_display']
    date_hierarchy = 'scheduled_date'

    fieldsets = (
        ('Transaction Details', {
            'fields': ('account', 'transaction_type', 'amount', 'description')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'status')
        }),
        ('Transfer Details', {
            'fields': ('recipient_account', 'recipient_name'),
            'classes': ('collapse',),
            'description': 'Only applicable for Transfer transactions'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'executed_at', 'days_remaining', 'is_overdue_display'),
            'classes': ('collapse',)
        }),
    )

    def account_username(self, obj):
        return obj.account.AccountUsername
    account_username.short_description = 'Account Username'

    def formatted_amount(self, obj):
        color = 'green' if obj.transaction_type in ['Deposit', 'Transfer In'] else 'red'
        return format_html('<span style="color: {};">₹{}</span>', color, obj.amount)
    formatted_amount.short_description = 'Amount'

    def days_remaining(self, obj):
        days = obj.days_until_execution
        if days is None:
            return 'N/A'
        elif days < 0:
            return format_html('<span style="color: red;">Overdue by {} days</span>', abs(days))
        elif days == 0:
            return format_html('<span style="color: orange;">Today</span>')
        elif days <= 3:
            return format_html('<span style="color: orange;">{} days</span>', days)
        else:
            return f'{days} days'
    days_remaining.short_description = 'Days Remaining'

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">YES</span>')
        return 'No'
    is_overdue_display.short_description = 'Overdue'

    def recipient_info(self, obj):
        if obj.transaction_type in ['Transfer Out', 'Transfer In'] and obj.recipient_name:
            return f'{obj.recipient_name} ({obj.recipient_account})'
        return 'N/A'
    recipient_info.short_description = 'Recipient'


# Security Models Admin
class SecuritySettingsAdmin(admin.ModelAdmin):
    list_display = ['user_username', 'daily_transaction_limit', 'single_transaction_limit', 'monthly_spending_cap', 'security_alerts_enabled', 'created_at']
    list_filter = ['security_alerts_enabled', 'created_at']
    search_fields = ['user__username', 'user__fullname']
    readonly_fields = ['created_at', 'updated_at']

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'


class DeviceFingerprintAdmin(admin.ModelAdmin):
    list_display = ['user_username', 'device_name', 'device_id_short', 'user_timezone', 'location_short', 'first_seen', 'last_seen']
    list_filter = ['first_seen', 'last_seen']
    search_fields = ['user__username', 'device_name', 'device_id']
    readonly_fields = ['first_seen', 'last_seen']

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'

    def device_id_short(self, obj):
        return obj.device_id[:20] + '...' if len(obj.device_id) > 20 else obj.device_id
    device_id_short.short_description = 'Device ID'

    def location_short(self, obj):
        return obj.location[:30] + '...' if len(obj.location) > 30 else obj.location
    location_short.short_description = 'Location'


class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ['user_username', 'ip_address', 'location_display', 'device_name', 'login_time']
    list_filter = ['login_time']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['login_time']
    date_hierarchy = 'login_time'

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'

    def device_name(self, obj):
        return obj.device.device_name if obj.device else 'Unknown'
    device_name.short_description = 'Device'

    def location_display(self, obj):
        location_data = obj.get_location_data()
        if location_data:
            return f"{location_data.get('city', 'Unknown')}, {location_data.get('country', 'Unknown')}"
        return 'Unknown'
    location_display.short_description = 'Location'


class SuspiciousActivityAdmin(admin.ModelAdmin):
    list_display = ['user_username', 'activity_type', 'description_short', 'detected_at']
    list_filter = ['activity_type', 'detected_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['detected_at']
    date_hierarchy = 'detected_at'

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'


class TransactionLimitAdmin(admin.ModelAdmin):
    list_display = ['user_username', 'date', 'daily_spent', 'monthly_spent', 'transaction_count']
    list_filter = ['date']
    search_fields = ['user__username']
    date_hierarchy = 'date'

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'


# Register models
admin.site.register(Useracc, UseraccAdmin)
admin.site.register(Account, AccountAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(UpcomingTransaction, UpcomingTransactionAdmin)
# Virtual Card Models Admin
class VirtualCardAdmin(admin.ModelAdmin):
    list_display = ['card_number_masked', 'account_username', 'card_type', 'status', 'daily_limit', 'monthly_limit', 'daily_spent', 'monthly_spent', 'created_at']
    list_filter = ['status', 'card_type', 'created_at', 'online_transactions_enabled', 'international_transactions_enabled']
    search_fields = ['account__AccountUsername', 'card_number', 'cardholder_name']
    readonly_fields = ['created_at', 'updated_at', 'card_number', 'cvv', 'expiry_month', 'expiry_year']

    def account_username(self, obj):
        return obj.account.AccountUsername
    account_username.short_description = 'Account Username'

    def card_number_masked(self, obj):
        return f"****-****-****-{obj.card_number[-4:]}"
    card_number_masked.short_description = 'Card Number'


class CardTransactionAdmin(admin.ModelAdmin):
    list_display = ['card_number_masked', 'merchant_name', 'merchant_category', 'amount', 'transaction_status', 'is_online', 'created_at']
    list_filter = ['transaction_status', 'merchant_category', 'is_online', 'created_at']
    search_fields = ['virtual_card__card_number', 'merchant_name', 'transaction__description']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def card_number_masked(self, obj):
        return f"****-{obj.virtual_card.card_number[-4:]}"
    card_number_masked.short_description = 'Card'

    def amount(self, obj):
        return f"₹{obj.transaction.amount}"
    amount.short_description = 'Amount'


# Financial Goal Models Admin
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ['user_username', 'title', 'goal_type', 'target_amount', 'current_amount', 'progress_percentage', 'target_date', 'status']
    list_filter = ['goal_type', 'status', 'target_date', 'created_at']
    search_fields = ['user__username', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'progress_percentage', 'remaining_amount']

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'

    def progress_percentage(self, obj):
        return f"{obj.progress_percentage:.1f}%"
    progress_percentage.short_description = 'Progress'


class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['user_username', 'category_type', 'monthly_budget', 'current_spending', 'budget_utilization_display']
    list_filter = ['category_type', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at', 'budget_utilization_display']

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'

    def budget_utilization_display(self, obj):
        return f"{obj.budget_utilization:.1f}%"
    budget_utilization_display.short_description = 'Budget Used'


class TransactionCategoryAdmin(admin.ModelAdmin):
    list_display = ['transaction_info', 'category_type', 'confidence_score', 'is_manual', 'created_at']
    list_filter = ['category_type', 'is_manual', 'created_at']
    search_fields = ['transaction__account__AccountUsername', 'transaction__description']
    readonly_fields = ['created_at']

    def transaction_info(self, obj):
        return f"{obj.transaction.account.AccountUsername} - ₹{obj.transaction.amount}"
    transaction_info.short_description = 'Transaction'


admin.site.register(SecuritySettings, SecuritySettingsAdmin)
admin.site.register(DeviceFingerprint, DeviceFingerprintAdmin)
admin.site.register(LoginActivity, LoginActivityAdmin)
admin.site.register(SuspiciousActivity, SuspiciousActivityAdmin)
admin.site.register(TransactionLimit, TransactionLimitAdmin)
# AI and Chat Models Admin
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ['user_username', 'session_id', 'is_active', 'message_count', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['user__username', 'session_id']
    readonly_fields = ['created_at', 'updated_at', 'message_count']

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation_user', 'message_type', 'content_short', 'timestamp']
    list_filter = ['message_type', 'timestamp']
    search_fields = ['conversation__user__username', 'content']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

    def conversation_user(self, obj):
        return obj.conversation.user.username
    conversation_user.short_description = 'User'

    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = 'Content'


class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['user_username', 'insight_type', 'title', 'is_read', 'is_actionable', 'action_taken', 'created_at']
    list_filter = ['insight_type', 'is_read', 'is_actionable', 'action_taken', 'created_at']
    search_fields = ['user__username', 'title', 'description']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'


admin.site.register(VirtualCard, VirtualCardAdmin)
admin.site.register(CardTransaction, CardTransactionAdmin)
admin.site.register(FinancialGoal, FinancialGoalAdmin)
admin.site.register(ExpenseCategory, ExpenseCategoryAdmin)
admin.site.register(TransactionCategory, TransactionCategoryAdmin)
admin.site.register(ChatConversation, ChatConversationAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(AIInsight, AIInsightAdmin)