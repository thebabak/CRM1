from django.contrib import admin
from .models import (
    Employee,
    EmployeeSalary,
    SalaryAdvance,
    ExpenseCategory,
    Expense,
    Income,
    Budget,
    BankAccount,
    Transaction,
    Loan,
    LoanRepayment,
    FinanceApprovalLevel,
    FinanceRequest,
)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_code', 'user', 'department', 'position', 'employment_type', 'is_active']
    list_filter = ['is_active', 'employment_type', 'department']
    search_fields = ['employee_code', 'user__username', 'user__first_name', 'user__last_name', 'department', 'position']
    ordering = ['employee_code']


@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'year', 'month', 'gross_salary', 'net_salary', 'status', 'payment_date']
    list_filter = ['status', 'year', 'month']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name', 'employee_code']
    list_select_related = ['employee']


@admin.register(SalaryAdvance)
class SalaryAdvanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'amount', 'installment_months', 'monthly_installment', 'status', 'requested_date', 'approved_by']
    list_filter = ['status', 'installment_months', 'requested_date']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name', 'reason']
    list_select_related = ['employee', 'approved_by']


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent']
    list_filter = ['parent']
    search_fields = ['code', 'name', 'description']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'amount', 'date', 'payment_method', 'created_by']
    list_filter = ['payment_method', 'date', 'category']
    search_fields = ['title', 'vendor', 'invoice_number', 'description', 'category__name']
    list_select_related = ['category', 'created_by']


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['title', 'income_type', 'amount', 'date', 'created_by']
    list_filter = ['income_type', 'date']
    search_fields = ['title', 'client', 'invoice_number', 'description']
    list_select_related = ['created_by']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['year', 'category', 'planned_amount', 'actual_amount']
    list_filter = ['year', 'category']
    search_fields = ['category__name', 'category__code', 'description']
    list_select_related = ['category']


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['bank_name', 'account_number', 'account_type', 'branch_name', 'balance', 'is_active']
    list_filter = ['account_type', 'is_active', 'bank_name']
    search_fields = ['bank_name', 'account_number', 'branch_name', 'description']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['bank_account', 'transaction_type', 'amount', 'date', 'created_by']
    list_filter = ['transaction_type', 'date', 'bank_account']
    search_fields = ['reference', 'description', 'bank_account__bank_name', 'bank_account__account_number']
    list_select_related = ['bank_account', 'created_by']


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['employee', 'loan_type', 'amount_requested', 'amount_approved', 'status', 'request_date', 'approved_by']
    list_filter = ['status', 'loan_type', 'request_date']
    search_fields = ['employee__user__username', 'employee__user__first_name', 'employee__user__last_name', 'reason']
    list_select_related = ['employee', 'employee__user', 'approved_by']


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ['loan', 'installment_number', 'payment_date', 'amount', 'remaining_balance', 'created_by']
    list_filter = ['payment_date']
    search_fields = ['loan__employee__user__username', 'reference_number', 'notes']
    list_select_related = ['loan', 'loan__employee', 'created_by']


@admin.register(FinanceApprovalLevel)
class FinanceApprovalLevelAdmin(admin.ModelAdmin):
    list_display = ['level', 'role_name', 'approver', 'is_active', 'order']
    list_filter = ['is_active', 'level']
    search_fields = ['role_name', 'approver__username']


@admin.register(FinanceRequest)
class FinanceRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'request_type', 'reference_id', 'status', 'current_level', 'created_at']
    list_filter = ['status', 'request_type', 'current_level']
    search_fields = ['reference_id']
