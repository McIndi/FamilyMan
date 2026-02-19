from django.urls import path
from . import views

urlpatterns = [
    path('add_fund/', views.add_fund, name='add_fund'),
    path('add_expense/', views.add_expense, name='add_expense'),
    path('upload_receipt/<int:expense_id>/', views.upload_receipt, name='upload_receipt'),
    path('transactions/', views.cash_transaction_list, name='cash_transaction_list'),
    path('transactions/dashboard/', views.cash_transaction_dashboard, name='cash_transaction_dashboard'),
    path('expense/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expense/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
    path('fund/<int:fund_id>/edit/', views.edit_fund, name='edit_fund'),
    path('fund/<int:fund_id>/delete/', views.delete_fund, name='delete_fund'),
    # Wallet (per-user cash tracking)
    path('wallet/', views.wallet_view, name='wallet_view'),
    path('wallet/cash-in/', views.add_wallet_cash_in, name='add_wallet_cash_in'),
    path('wallet/cash-in/from-expense/<int:expense_id>/', views.add_wallet_cash_in, name='wallet_from_expense'),
    path('wallet/cash-out/', views.add_wallet_cash_out, name='add_wallet_cash_out'),
    path('wallet/<int:transaction_id>/edit/', views.edit_wallet_transaction, name='edit_wallet_transaction'),
    path('wallet/<int:transaction_id>/delete/', views.delete_wallet_transaction, name='delete_wallet_transaction'),
]