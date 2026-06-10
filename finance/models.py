from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


# =========================
# Payroll Section
# =========================

class EmployeeSalary(models.Model):
    """Employee salary records"""
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salary_records')
    employee_code = models.CharField(max_length=50, blank=True)
    
    # Base salary components
    base_salary = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    housing_allowance = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    food_allowance = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    transportation = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    child_allowance = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    
    # Additions
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    commission = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    
    # Deductions
    insurance = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    loan_installment = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    absence_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    absence_deduction = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    
    # Final amounts
    gross_salary = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    net_salary = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    
    # Time info
    month = models.IntegerField()
    year = models.IntegerField()
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Additional info
    bank_account = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_salaries')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['employee', 'month', 'year']
    
    def __str__(self):
        return f"{self.employee.username} - {self.year}/{self.month}"
    
    def calculate_gross_salary(self):
        self.gross_salary = (
            self.base_salary + self.housing_allowance + self.food_allowance + 
            self.transportation + self.child_allowance + self.overtime_pay + 
            self.bonus + self.commission
        )
        return self.gross_salary
    
    def calculate_net_salary(self):
        total_deductions = (
            self.insurance + self.tax + self.loan_installment + 
            self.absence_deduction + self.other_deductions
        )
        self.net_salary = self.gross_salary - total_deductions
        return self.net_salary


class SalaryAdvance(models.Model):
    """Salary advance request"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salary_advances')
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    reason = models.TextField()
    requested_date = models.DateField(default=timezone.now)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_advances')
    approved_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    installment_months = models.IntegerField(default=1)
    monthly_installment = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.username} - {self.amount} - {self.status}"
    
    def save(self, *args, **kwargs):
        if self.amount and self.installment_months:
            self.monthly_installment = self.amount / self.installment_months
        super().save(*args, **kwargs)


# =========================
# Financial Management Section
# =========================

class ExpenseCategory(models.Model):
    """Expense categories"""
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['code']
        verbose_name_plural = "Expense Categories"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Expense(models.Model):
    """Expense records"""
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
        ('credit', 'Credit Card'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    date = models.DateField(default=timezone.now)
    vendor = models.CharField(max_length=200, blank=True)
    invoice_number = models.CharField(max_length=50, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    description = models.TextField(blank=True)
    receipt_file = models.FileField(upload_to='expense_receipts/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_expenses')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} - {self.amount}"


class Income(models.Model):
    """Income records"""
    
    INCOME_TYPES = [
        ('service', 'Service Income'),
        ('product', 'Product Sales'),
        ('investment', 'Investment'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    income_type = models.CharField(max_length=20, choices=INCOME_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    date = models.DateField(default=timezone.now)
    client = models.CharField(max_length=200, blank=True)
    invoice_number = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_incomes')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.title} - {self.amount}"


class Budget(models.Model):
    """Annual budgeting"""
    
    year = models.IntegerField()
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name='budgets')
    planned_amount = models.DecimalField(max_digits=15, decimal_places=0)
    actual_amount = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['year', 'category']
    
    def __str__(self):
        return f"{self.year} - {self.category.name}"
    
    @property
    def variance(self):
        return self.actual_amount - self.planned_amount
    
    @property
    def variance_percentage(self):
        if self.planned_amount:
            return (self.variance / self.planned_amount) * 100
        return 0


class BankAccount(models.Model):
    """Bank accounts"""
    
    ACCOUNT_TYPES = [
        ('current', 'Current Account'),
        ('savings', 'Savings Account'),
        ('deposit', 'Deposit'),
    ]
    
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50, unique=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    branch_name = models.CharField(max_length=100, blank=True)
    balance = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class Transaction(models.Model):
    """Bank transactions"""
    
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('transfer', 'Transfer'),
    ]
    
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    date = models.DateField(default=timezone.now)
    reference = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}"

class Employee(models.Model):
    """Employee profile linked to User"""
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_code = models.CharField(max_length=50, unique=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=100, blank=True)
    hire_date = models.DateField(default=timezone.now)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    is_active = models.BooleanField(default=True)
    
    # Contact info
    phone = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    
    # Bank info
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.employee_code}"
    
    def save(self, *args, **kwargs):
        if not self.employee_code:
            # Generate employee code: EMP + year + sequential number
            import random
            import string
            year = timezone.now().strftime('%Y')
            random_num = ''.join(random.choices(string.digits, k=4))
            self.employee_code = f"EMP{year}{random_num}"
        super().save(*args, **kwargs)


# Signal to automatically create Employee for every User
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_employee_for_user(sender, instance, created, **kwargs):
    """Automatically create an Employee record when a new User is created"""
    if created:
        Employee.objects.get_or_create(
            user=instance,
            defaults={
                'employee_code': f"EMP{instance.id:06d}",
                'is_active': True
            }
        )
        print(f"Employee profile created for {instance.username}")

@receiver(post_save, sender=User)
def save_employee_for_user(sender, instance, **kwargs):
    """Save Employee record when User is saved"""
    if hasattr(instance, 'employee_profile'):
        instance.employee_profile.save()

# =========================
# Loan Request Section
# =========================

class Loan(models.Model):
    """Loan request model"""
    
    LOAN_TYPES = [
        ('personal', 'Personal Loan'),
        ('emergency', 'Emergency Loan'),
        ('housing', 'Housing Loan'),
        ('education', 'Education Loan'),
        ('vehicle', 'Vehicle Loan'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
        ('repaid', 'Fully Repaid'),
    ]
    
    # Employee information
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loan_requests')
    
    # Loan details
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES, default='personal')
    amount_requested = models.DecimalField(max_digits=15, decimal_places=0, help_text="Requested loan amount")
    amount_approved = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, help_text="Approved loan amount")
    reason = models.TextField(help_text="Reason for loan request")
    
    # Loan terms
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Annual interest rate %")
    tenure_months = models.IntegerField(default=12, help_text="Loan repayment period in months")
    monthly_installment = models.DecimalField(max_digits=15, decimal_places=0, default=0, help_text="Calculated monthly payment")
    total_repayment = models.DecimalField(max_digits=15, decimal_places=0, default=0, help_text="Total amount to repay")
    
    # Dates
    request_date = models.DateField(default=timezone.now, help_text="Date of request")
    approval_date = models.DateField(null=True, blank=True)
    disbursement_date = models.DateField(null=True, blank=True)
    first_payment_date = models.DateField(null=True, blank=True)
    
    # Approval workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')
    comments = models.TextField(blank=True, help_text="Admin comments")
    
    # Tracking
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-request_date']
    
    def __str__(self):
        return f"{self.employee.user.username} - {self.loan_type} - {self.amount_requested}"
    
    def calculate_monthly_installment(self):
        """Calculate monthly installment based on amount, interest rate, and tenure"""
        if self.amount_approved and self.interest_rate and self.tenure_months:
            # Simple interest calculation
            principal = float(self.amount_approved)
            rate = float(self.interest_rate) / 100 / 12  # Monthly interest rate
            months = int(self.tenure_months)
            
            if rate > 0:
                monthly = principal * rate * (1 + rate)**months / ((1 + rate)**months - 1)
            else:
                monthly = principal / months
            
            self.monthly_installment = int(monthly)
            self.total_repayment = self.monthly_installment * months
        return self.monthly_installment


class LoanRepayment(models.Model):
    """Track loan repayments"""
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    payment_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=15, decimal_places=0)
    installment_number = models.IntegerField(help_text="Which installment number")
    remaining_balance = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    payment_method = models.CharField(max_length=50, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_payments')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['payment_date']
    
    def __str__(self):
        return f"Payment #{self.installment_number} - {self.loan.employee.user.username}"

# =========================
# Finance Approval Levels
# =========================

class FinanceApprovalLevel(models.Model):
    """Configurable approval levels for finance"""
    
    LEVEL_CHOICES = [
        (1, 'Level 1 - Finance Manager'),
        (2, 'Level 2 - Finance Director'),
        (3, 'Level 3 - CFO'),
    ]
    
    level = models.IntegerField(choices=LEVEL_CHOICES, unique=True)
    role_name = models.CharField(max_length=100)
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='finance_approvals')
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, help_text="Approval order (1,2,3)")
    
    class Meta:
        ordering = ['order']
        verbose_name = "Finance Approval Level"
        verbose_name_plural = "Finance Approval Levels"
    
    def __str__(self):
        return f"Level {self.level}: {self.role_name}"


class FinanceRequest(models.Model):
    """Base model for all finance requests that need approval"""
    
    REQUEST_TYPES = [
        ('advance', 'Salary Advance'),
        ('loan', 'Loan Request'),
        ('expense', 'Expense Reimbursement'),
        ('budget', 'Budget Request'),
    ]
    
    STATUS_CHOICES = [
        ('pending_level1', 'Pending Level 1 Approval'),
        ('pending_level2', 'Pending Level 2 Approval'),
        ('approved', 'Fully Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    reference_id = models.IntegerField(help_text="ID of the original request (advance/loan/etc)")
    
    # Approval tracking
    current_level = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_level1')
    
    # Approver tracking
    level1_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='finance_level1_approved')
    level1_approved_at = models.DateTimeField(null=True, blank=True)
    level1_comment = models.TextField(blank=True)
    
    level2_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='finance_level2_approved')
    level2_approved_at = models.DateTimeField(null=True, blank=True)
    level2_comment = models.TextField(blank=True)
    
    level3_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='finance_level3_approved')
    level3_approved_at = models.DateTimeField(null=True, blank=True)
    level3_comment = models.TextField(blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_request_type_display()} - {self.reference_id} - {self.status}"
    
    def get_current_approver(self):
        """Get the approver for current level"""
        try:
            approval_level = FinanceApprovalLevel.objects.get(level=self.current_level, is_active=True)
            return approval_level.approver
        except FinanceApprovalLevel.DoesNotExist:
            return None
    
    def can_approve(self, user):
        """Check if user can approve at current level"""
        approver = self.get_current_approver()
        return approver and approver.id == user.id
    
    def approve(self, user, comment=""):
        """Approve at current level"""
        if not self.can_approve(user):
            return False, "You don't have permission to approve this request"
        
        if self.current_level == 1:
            self.level1_approved_by = user
            self.level1_approved_at = timezone.now()
            self.level1_comment = comment
            self.current_level = 2
            self.status = 'pending_level2'
        elif self.current_level == 2:
            self.level2_approved_by = user
            self.level2_approved_at = timezone.now()
            self.level2_comment = comment
            self.current_level = 3
            self.status = 'pending_level3'
        elif self.current_level == 3:
            self.level3_approved_by = user
            self.level3_approved_at = timezone.now()
            self.level3_comment = comment
            self.status = 'approved'
        
        self.save()
        return True, "Approved successfully"
    
    def reject(self, user, comment=""):
        """Reject the request"""
        if self.current_level == 1:
            self.level1_approved_by = user
            self.level1_comment = comment
        elif self.current_level == 2:
            self.level2_approved_by = user
            self.level2_comment = comment
        elif self.current_level == 3:
            self.level3_approved_by = user
            self.level3_comment = comment
        
        self.status = 'rejected'
        self.save()
        return True, "Request rejected"

# Update Loan model - add this to the existing Loan class
# Add these fields to the Loan class if they don't exist:

# In the Loan class, add:
# finance_request = models.OneToOneField(FinanceRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='loan_request')

# And update the save method to create finance request

# Fix the signal - remove Unicode characters
@receiver(post_save, sender=User)
def create_employee_for_user(sender, instance, created, **kwargs):
    """Automatically create an Employee record when a new User is created"""
    if created:
        Employee.objects.get_or_create(
            user=instance,
            defaults={
                'employee_code': f"EMP{instance.id:06d}",
                'is_active': True
            }
        )
        # Using ASCII characters only
        print(f"Employee profile created for {instance.username}")

@receiver(post_save, sender=User)
def save_employee_for_user(sender, instance, **kwargs):
    """Save Employee record when User is saved"""
    if hasattr(instance, 'employee_profile'):
        instance.employee_profile.save()

# Update the approve method in FinanceRequest class - replace the existing approve method
# Find the approve method and replace with this:

    def approve(self, user, comment=""):
        """Approve at current level - only 2 levels"""
        if not self.can_approve(user):
            return False, "You don't have permission to approve this request"
        
        if self.current_level == 1:
            # Level 1 (Finance Manager) approved → Move to Level 2
            self.level1_approved_by = user
            self.level1_approved_at = timezone.now()
            self.level1_comment = comment
            self.current_level = 2
            self.status = 'pending_level2'
            
        elif self.current_level == 2:
            # Level 2 (Finance Director) approved → Final approval
            self.level2_approved_by = user
            self.level2_approved_at = timezone.now()
            self.level2_comment = comment
            self.status = 'approved'  # Fully approved, no more levels
            
        self.save()
        return True, "Approved successfully"
    
    def reject(self, user, comment=""):
        """Reject the request"""
        if self.current_level == 1:
            self.level1_approved_by = user
            self.level1_comment = comment
        elif self.current_level == 2:
            self.level2_approved_by = user
            self.level2_comment = comment
        
        self.status = 'rejected'
        self.save()
        return True, "Request rejected"

# Fix FinanceApprovalLevel model - replace the existing class
# First, delete the old class (if exists), then add this:

class FinanceApprovalLevel(models.Model):
    """Configurable approval levels for finance"""
    
    LEVEL_CHOICES = [
        (1, 'Level 1 - Finance Manager'),
        (2, 'Level 2 - Finance Director'),
    ]
    
    level = models.IntegerField(choices=LEVEL_CHOICES, unique=True)
    role_name = models.CharField(max_length=100)
    approver = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='finance_approval_levels'
    )
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Finance Approval Level"
        verbose_name_plural = "Finance Approval Levels"
    
    def __str__(self):
        return f"{self.get_level_display()}: {self.role_name}"
