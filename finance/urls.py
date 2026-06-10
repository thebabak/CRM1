from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Payroll URLs
    path('payroll/', views.payroll_dashboard, name='payroll_dashboard'),
    path('payroll/salaries/', views.salary_list, name='salary_list'),
    path('payroll/salaries/create/', views.salary_create, name='salary_create'),
    path('payroll/advances/', views.salary_advance_list, name='advance_list'),
    path('payroll/advances/request/', views.salary_advance_request, name='advance_request'),
    path('payroll/advances/approve/<int:pk>/', views.salary_advance_approve, name='advance_approve'),
    
    # Financial Management URLs
    path('management/', views.finance_dashboard, name='finance_dashboard'),
    path('management/expenses/', views.expense_list, name='expense_list'),
    path('management/expenses/create/', views.expense_create, name='expense_create'),
    path('management/incomes/', views.income_list, name='income_list'),
    path('management/incomes/create/', views.income_create, name='income_create'),
    path('management/budgets/', views.budget_list, name='budget_list'),
    path('management/bank-accounts/', views.bank_accounts, name='bank_accounts'),
    
    # Loan URLs
    path('loans/', views.loan_list, name='loan_list'),
    path('loans/request/', views.loan_request, name='loan_request'),
    path('loans/detail/<int:pk>/', views.loan_detail, name='loan_detail'),
    
    # Approval URLs
    path('approvals/', views.pending_approvals, name='pending_approvals'),
    path('approvals/approve/<int:request_id>/', views.approve_request, name='approve_request'),
    
    # All Requests URL
    path('all-requests/', views.all_requests, name='all_requests'),
]
