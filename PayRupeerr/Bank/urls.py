from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('loginpage/', views.loginpage, name='loginpage'),
    path('loginpage/loginpageprocess/', views.loginpageprocess, name='loginpageprocess'),
    path('registerpage/', views.registerpage, name='registerpage'),
    path('registerpage/registerpageprocess/', views.registerpageprocess, name='registerpageprocess'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('accounts/', views.accounts, name='accounts'),
    path('transfer/', views.transfer, name='transfer'),
    path('transfer/transferprocess/', views.transferprocess, name='transferprocess'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('withdraw/withdrawprocess/', views.withdrawprocess, name='withdrawprocess'),
    path('deposit/', views.deposit, name='deposit'),
    path('deposit/depositprocess/', views.depositprocess, name='depositprocess'),
    path('forgotpassword/', views.forgotpassword, name='forgotpassword'),
    path('security/', views.security, name='security'),
    path('settingss/', views.settingss, name='settingss'),
    path('logout/', views.logout_view, name='logout'),
    path('history/', views.transaction_history, name='transaction-history'),
    path('download-transactions-pdf/', views.download_transactions_pdf, name='download-transactions-pdf'),
    path('download-account-details-pdf/', views.download_account_details_pdf, name='download-account-details-pdf'),
    # Security URLs
    path('security/update-settings/', views.update_security_settings, name='update-security-settings'),
    path('security/trust-device/', views.trust_device, name='trust-device'),
    path('security/remove-trusted-device/', views.remove_trusted_device, name='remove-trusted-device'),
    path('security/resolve-activity/', views.resolve_suspicious_activity, name='resolve-suspicious-activity'),
    # Virtual Card URLs
    path('virtual-cards/', views.virtual_cards, name='virtual-cards'),
    path('virtual-cards/create/', views.create_virtual_card, name='create-virtual-card'),
    path('virtual-cards/<int:card_id>/', views.card_details, name='card-details'),
    path('virtual-cards/toggle-status/', views.toggle_card_status, name='toggle-card-status'),
    path('virtual-cards/update-limits/', views.update_card_limits, name='update-card-limits'),
    path('virtual-cards/delete/', views.delete_virtual_card, name='delete-virtual-card'),
    # AI Chatbot URLs
    path('ai/chat/start/', views.ai_chat_start, name='ai-chat-start'),
    path('ai/chat/message/', views.ai_chat_message, name='ai-chat-message'),
    path('ai/dashboard-insights/', views.ai_dashboard_insights, name='ai-dashboard-insights'),
    path('ai/update-memory/', views.ai_update_memory, name='ai-update-memory'),
]
