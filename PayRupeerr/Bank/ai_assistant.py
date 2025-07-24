import json
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from .models import (
    Transaction, Account, Useracc, VirtualCard, CardTransaction,
    ChatConversation, ChatMessage, AIInsight, SecuritySettings,
    SuspiciousActivity, TransactionLimit
)
import random


class AIFinancialAssistant:
    """AI-powered financial assistant for analyzing spending patterns and providing insights"""

    def __init__(self, user):
        self.user = user
        self.account = Account.objects.get(AccountUsername=user.username)

    def start_conversation(self):
        """Start a new chat conversation"""
        session_id = f"{self.user.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        conversation = ChatConversation.objects.create(
            user=self.user,
            session_id=session_id
        )
        
        # Welcome message
        welcome_msg = self.generate_welcome_message()
        ChatMessage.objects.create(
            conversation=conversation,
            message_type='ai',
            content=welcome_msg
        )
        
        return conversation

    def generate_welcome_message(self):
        """Generate personalized welcome message"""
        balance = self.account.AccountBalance
        recent_transactions = Transaction.objects.filter(account=self.account).count()
        virtual_cards = VirtualCard.objects.filter(account=self.account).count()
        
        welcome = f"👋 Hello {self.account.AccountHolder}! I'm your AI Financial Assistant.\n\n"
        welcome += f"💰 Current Balance: ₹{balance:,.2f}\n"
        welcome += f"📊 Total Transactions: {recent_transactions}\n"
        welcome += f"💳 Virtual Cards: {virtual_cards}\n\n"
        welcome += "I can help you with:\n"
        welcome += "• Account balance and transaction analysis\n"
        welcome += "• Virtual card management\n"
        welcome += "• Spending insights and budgeting\n"
        welcome += "• Security monitoring\n"
        welcome += "• Financial planning tips\n\n"
        welcome += "What would you like to know about your finances today?"
        
        return welcome

    def process_message(self, conversation, message):
        """Process user message and generate AI response"""
        # Save user message
        ChatMessage.objects.create(
            conversation=conversation,
            message_type='user',
            content=message
        )

        # Generate AI response
        response = self.generate_response(message.lower())
        
        # Save AI response
        ChatMessage.objects.create(
            conversation=conversation,
            message_type='ai',
            content=response
        )
        
        return response

    def generate_response(self, message):
        """Generate contextual AI responses"""
        message = message.lower()
        
        # Balance queries
        if any(word in message for word in ['balance', 'money', 'amount']):
            return self.get_balance_info()
        
        # Transaction queries
        elif any(word in message for word in ['transaction', 'payment', 'history', 'spent']):
            return self.get_transaction_analysis()
        
        # Virtual card queries
        elif any(word in message for word in ['card', 'virtual', 'freeze', 'limit']):
            return self.get_virtual_card_info()
        
        # Security queries
        elif any(word in message for word in ['security', 'safe', 'suspicious', 'alert']):
            return self.get_security_status()
        
        # Spending analysis
        elif any(word in message for word in ['spending', 'expense', 'budget', 'analysis']):
            return self.get_spending_analysis()
        
        # Investment/savings
        elif any(word in message for word in ['save', 'saving', 'invest', 'goal']):
            return self.get_savings_advice()
        
        # Help queries
        elif any(word in message for word in ['help', 'what', 'how', 'can']):
            return self.get_help_info()
        
        else:
            return self.get_general_response()

    def get_balance_info(self):
        """Get detailed balance information"""
        balance = self.account.AccountBalance
        
        # Get recent transactions for context
        recent_transactions = Transaction.objects.filter(
            account=self.account,
            timestamp__gte=timezone.now() - timedelta(days=7)
        )
        
        total_spent_week = recent_transactions.filter(
            transaction_type__in=['Withdraw', 'Transfer Out']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_received_week = recent_transactions.filter(
            transaction_type__in=['Deposit', 'Transfer In']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        response = f"💰 **Your Account Balance**\n\n"
        response += f"Current Balance: ₹{balance:,.2f}\n\n"
        response += f"📊 **This Week's Activity:**\n"
        response += f"• Money Spent: ₹{total_spent_week:,.2f}\n"
        response += f"• Money Received: ₹{total_received_week:,.2f}\n"
        response += f"• Net Change: ₹{total_received_week - total_spent_week:,.2f}\n\n"
        
        if balance < 1000:
            response += "⚠️ Your balance is running low. Consider making a deposit."
        elif balance > 50000:
            response += "💡 You have a healthy balance! Consider investing some funds."
        
        return response

    def get_transaction_analysis(self):
        """Analyze recent transactions"""
        transactions = Transaction.objects.filter(
            account=self.account
        ).order_by('-timestamp')[:10]
        
        if not transactions:
            return "📊 No transactions found in your account yet."
        
        response = f"📊 **Recent Transaction Analysis**\n\n"
        response += f"**Last 10 Transactions:**\n"
        
        for txn in transactions:
            emoji = "💸" if txn.transaction_type in ['Withdraw', 'Transfer Out'] else "💰"
            response += f"{emoji} {txn.transaction_type}: ₹{txn.amount:,.2f}\n"
            response += f"   {txn.timestamp.strftime('%b %d, %Y at %I:%M %p')}\n"
            if txn.description:
                response += f"   📝 {txn.description}\n"
            response += "\n"
        
        # Monthly summary
        this_month = timezone.now().replace(day=1)
        monthly_transactions = Transaction.objects.filter(
            account=self.account,
            timestamp__gte=this_month
        )
        
        monthly_spent = monthly_transactions.filter(
            transaction_type__in=['Withdraw', 'Transfer Out']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        response += f"📅 **This Month's Summary:**\n"
        response += f"Total Spent: ₹{monthly_spent:,.2f}\n"
        response += f"Transaction Count: {monthly_transactions.count()}\n"
        
        return response

    def get_virtual_card_info(self):
        """Get virtual card information and suggestions"""
        cards = VirtualCard.objects.filter(account=self.account)
        
        if not cards:
            response = "💳 **Virtual Cards**\n\n"
            response += "You don't have any virtual cards yet.\n\n"
            response += "💡 **Benefits of Virtual Cards:**\n"
            response += "• Secure online shopping\n"
            response += "• Control spending limits\n"
            response += "• Freeze/unfreeze instantly\n"
            response += "• Track online expenses\n\n"
            response += "Would you like me to help you create one?"
            return response
        
        response = f"💳 **Your Virtual Cards ({cards.count()})**\n\n"
        
        for card in cards:
            status_emoji = "✅" if card.status == 'active' else "❄️" if card.status == 'frozen' else "❌"
            response += f"{status_emoji} **{card.card_type.title()} Card**\n"
            response += f"   Number: {card.masked_card_number}\n"
            response += f"   Status: {card.status.title()}\n"
            response += f"   Daily Limit: ₹{card.daily_limit:,.0f}\n"
            response += f"   Monthly Limit: ₹{card.monthly_limit:,.0f}\n\n"
        
        # Card usage insights
        active_cards = cards.filter(status='active').count()
        frozen_cards = cards.filter(status='frozen').count()
        
        if frozen_cards > 0:
            response += f"❄️ You have {frozen_cards} frozen card(s). "
            response += "Consider activating them if needed.\n\n"
        
        response += "💡 **Quick Actions:**\n"
        response += "• View card details\n"
        response += "• Freeze/unfreeze cards\n"
        response += "• Update spending limits\n"
        response += "• Create new virtual card\n"
        
        return response

    def get_security_status(self):
        """Get security status and alerts"""
        try:
            security_settings = SecuritySettings.objects.get(user=self.user)
        except SecuritySettings.DoesNotExist:
            security_settings = None
        
        response = "🔒 **Security Status**\n\n"
        
        # Check for suspicious activities
        suspicious_activities = SuspiciousActivity.objects.filter(
            user=self.user,
            resolved=False
        )
        
        if suspicious_activities.exists():
            response += f"⚠️ **{suspicious_activities.count()} Security Alert(s)**\n"
            for activity in suspicious_activities[:3]:
                response += f"• {activity.activity_type}: {activity.description}\n"
            response += "\n"
        else:
            response += "✅ **No Security Alerts**\n"
            response += "Your account looks secure!\n\n"
        
        # Security settings info
        if security_settings:
            response += "🛡️ **Security Settings:**\n"
            response += f"• Daily Limit: ₹{security_settings.daily_transaction_limit:,.0f}\n"
            response += f"• Single Transaction Limit: ₹{security_settings.single_transaction_limit:,.0f}\n"
            response += f"• Alerts: {'Enabled' if security_settings.security_alerts_enabled else 'Disabled'}\n\n"
        
        # Recent login activity
        response += "📱 **Account Activity:**\n"
        response += "• Last login: Today\n"
        response += "• Login notifications: Enabled\n"
        response += "• Transaction alerts: Enabled\n\n"
        
        response += "💡 **Security Tips:**\n"
        response += "• Use virtual cards for online shopping\n"
        response += "• Monitor your transactions regularly\n"
        response += "• Keep your login credentials secure\n"
        
        return response

    def get_spending_analysis(self):
        """Analyze spending patterns and provide insights"""
        # Get last 30 days transactions
        thirty_days_ago = timezone.now() - timedelta(days=30)
        transactions = Transaction.objects.filter(
            account=self.account,
            timestamp__gte=thirty_days_ago,
            transaction_type__in=['Withdraw', 'Transfer Out']
        )
        
        if not transactions:
            return "📊 No spending data available for the last 30 days."
        
        total_spent = transactions.aggregate(total=Sum('amount'))['total'] or 0
        avg_transaction = transactions.aggregate(avg=Avg('amount'))['avg'] or 0
        transaction_count = transactions.count()
        
        response = f"📊 **Spending Analysis (Last 30 Days)**\n\n"
        response += f"💸 Total Spent: ₹{total_spent:,.2f}\n"
        response += f"📈 Average Transaction: ₹{avg_transaction:,.2f}\n"
        response += f"🔢 Transaction Count: {transaction_count}\n"
        response += f"📅 Daily Average: ₹{total_spent/30:,.2f}\n\n"
        
        # Spending insights
        if total_spent > 50000:
            response += "💡 **Insight:** You're a high spender. Consider setting monthly budgets.\n\n"
        elif total_spent < 5000:
            response += "💡 **Insight:** Your spending is quite conservative. Great for savings!\n\n"
        
        # Weekly comparison
        this_week = timezone.now() - timedelta(days=7)
        this_week_spent = transactions.filter(timestamp__gte=this_week).aggregate(
            total=Sum('amount'))['total'] or 0
        
        response += f"📅 **This Week:** ₹{this_week_spent:,.2f}\n"
        response += f"📊 **Weekly Average:** ₹{total_spent/4:,.2f}\n\n"
        
        if this_week_spent > (total_spent/4):
            response += "⚠️ This week's spending is above average.\n"
        else:
            response += "✅ This week's spending is within normal range.\n"
        
        return response

    def get_savings_advice(self):
        """Provide savings and investment advice"""
        balance = self.account.AccountBalance
        
        # Calculate monthly spending
        thirty_days_ago = timezone.now() - timedelta(days=30)
        monthly_spending = Transaction.objects.filter(
            account=self.account,
            timestamp__gte=thirty_days_ago,
            transaction_type__in=['Withdraw', 'Transfer Out']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        response = f"💰 **Savings & Investment Advice**\n\n"
        response += f"Current Balance: ₹{balance:,.2f}\n"
        response += f"Monthly Spending: ₹{monthly_spending:,.2f}\n\n"
        
        # Savings recommendations
        if balance > monthly_spending * 6:
            response += "🎯 **Excellent!** You have 6+ months of expenses saved.\n"
            response += "Consider investing surplus funds for better returns.\n\n"
        elif balance > monthly_spending * 3:
            response += "👍 **Good!** You have 3-6 months of expenses saved.\n"
            response += "Try to build up to 6 months emergency fund.\n\n"
        else:
            response += "⚠️ **Focus on Emergency Fund**\n"
            response += "Aim to save 3-6 months of expenses first.\n\n"
        
        # Savings suggestions
        suggested_savings = monthly_spending * 0.2  # 20% of spending
        response += f"💡 **Savings Suggestions:**\n"
        response += f"• Target monthly savings: ₹{suggested_savings:,.2f}\n"
        response += f"• Emergency fund goal: ₹{monthly_spending * 6:,.2f}\n"
        response += f"• Investment consideration: Above ₹{monthly_spending * 6:,.2f}\n\n"
        
        response += "🚀 **Investment Options:**\n"
        response += "• Fixed Deposits (Safe, 6-7% returns)\n"
        response += "• Mutual Funds (Moderate risk, 8-12% returns)\n"
        response += "• SIP (Systematic Investment Plan)\n"
        response += "• PPF (Tax saving, 15-year lock-in)\n"
        
        return response

    def get_help_info(self):
        """Provide help information"""
        response = "🤖 **AI Assistant Help**\n\n"
        response += "I can help you with:\n\n"
        response += "💰 **Account Information:**\n"
        response += "• Check balance\n"
        response += "• Transaction history\n"
        response += "• Monthly summaries\n\n"
        response += "💳 **Virtual Cards:**\n"
        response += "• Card status and limits\n"
        response += "• Usage recommendations\n"
        response += "• Security features\n\n"
        response += "📊 **Financial Analysis:**\n"
        response += "• Spending patterns\n"
        response += "• Budget suggestions\n"
        response += "• Savings advice\n\n"
        response += "🔒 **Security:**\n"
        response += "• Account security status\n"
        response += "• Suspicious activity alerts\n"
        response += "• Security recommendations\n\n"
        response += "💡 **Just ask me questions like:**\n"
        response += "• 'What's my balance?'\n"
        response += "• 'Show my recent transactions'\n"
        response += "• 'How are my virtual cards?'\n"
        response += "• 'Is my account secure?'\n"
        response += "• 'Give me spending analysis'\n"
        
        return response

    def get_general_response(self):
        """Generate general helpful response"""
        responses = [
            "I'm here to help with your financial questions! Try asking about your balance, transactions, or virtual cards.",
            "I can provide insights about your spending, security status, or savings advice. What would you like to know?",
            "Feel free to ask me about your account balance, recent transactions, or virtual card management.",
            "I'm your AI financial assistant! Ask me about spending analysis, security alerts, or investment advice.",
        ]
        return random.choice(responses)

    def generate_insights(self):
        """Generate AI insights for the user"""
        insights = []
        
        # Spending pattern insight
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_spending = Transaction.objects.filter(
            account=self.account,
            timestamp__gte=thirty_days_ago,
            transaction_type__in=['Withdraw', 'Transfer Out']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if recent_spending > 0:
            insight = AIInsight.objects.create(
                user=self.user,
                insight_type='spending_pattern',
                title='Monthly Spending Analysis',
                description=f'You spent ₹{recent_spending:,.2f} in the last 30 days. This is your current spending pattern.',
                data=json.dumps({'amount': recent_spending, 'period': '30_days'})
            )
            insights.append(insight)
        
        return insights
