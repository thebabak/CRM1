from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from .models import SalaryAdvance, Expense, Income, Budget, BankAccount, EmployeeSalary, Employee, Loan, FinanceRequest, FinanceApprovalLevel
from .forms import SalaryAdvanceForm, LoanRequestForm, LoanApprovalForm


def _profile_meta(user):
    profile = getattr(user, 'profile', None)
    if not profile:
        return '-', '-'

    role = profile.get_role_display() if getattr(profile, 'role', None) else '-'
    departments = profile.departments.all() if hasattr(profile, 'departments') else []
    department = ', '.join(departments.values_list('name', flat=True)) if hasattr(departments, 'values_list') and departments.exists() else '-'
    return role, department

# Payroll Views
@login_required
def payroll_dashboard(request):
    today = timezone.localdate()
    current_month_salaries = EmployeeSalary.objects.filter(year=today.year, month=today.month).select_related('employee')
    recent_salaries = EmployeeSalary.objects.select_related('employee')[:5]
    recent_advances = SalaryAdvance.objects.select_related('employee')[:4]

    context = {
        'total_employees': Employee.objects.count(),
        'current_month_salary_count': current_month_salaries.count(),
        'monthly_payroll_total': current_month_salaries.aggregate(total=Sum('net_salary'))['total'] or 0,
        'pending_advances_count': SalaryAdvance.objects.filter(status='pending').count(),
        'delayed_payments_count': EmployeeSalary.objects.filter(status='delayed').count(),
        'recent_salaries': recent_salaries,
        'recent_advances': recent_advances,
        'current_year': today.year,
        'current_month': today.month,
    }
    return render(request, 'finance/payroll_dashboard.html', context)

@login_required
def salary_list(request):
    salaries = EmployeeSalary.objects.all().select_related('employee')
    return render(request, 'finance/payroll/salary_list.html', {'salaries': salaries})

@login_required
def salary_create(request):
    return render(request, 'finance/payroll/salary_form.html')

@login_required
def salary_advance_list(request):
    is_approver = FinanceApprovalLevel.objects.filter(approver=request.user, is_active=True).exists()

    if request.user.is_superuser or is_approver:
        advances = SalaryAdvance.objects.all().select_related('employee', 'approved_by')
    else:
        advances = SalaryAdvance.objects.filter(employee=request.user).select_related('employee', 'approved_by')

    summary = {
        'advance_count': advances.count(),
        'pending_count': advances.filter(status='pending').count(),
        'approved_count': advances.filter(status='approved').count(),
        'rejected_count': advances.filter(status='rejected').count(),
        'can_review': request.user.is_superuser or is_approver,
    }
    return render(request, 'finance/payroll/advance_list.html', {'advances': advances, 'summary': summary})

@login_required
def salary_advance_request(request):
    if request.method == 'POST':
        form = SalaryAdvanceForm(request.POST)
        if form.is_valid():
            advance = form.save(commit=False)
            advance.employee = request.user
            advance.requested_date = timezone.now().date()
            advance.save()

            # Salary advances follow the same 2-level finance approval flow as loans.
            FinanceRequest.objects.get_or_create(
                request_type='advance',
                reference_id=advance.id,
                defaults={
                    'current_level': 1,
                    'status': 'pending_level1',
                },
            )

            messages.success(request, 'Your salary advance request has been submitted successfully!')
            return redirect('finance:advance_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SalaryAdvanceForm()
    return render(request, 'finance/payroll/advance_form.html', {'form': form})

@login_required
def salary_advance_approve(request, pk):
    advance = get_object_or_404(SalaryAdvance, pk=pk)
    finance_request, _ = FinanceRequest.objects.get_or_create(
        request_type='advance',
        reference_id=advance.id,
        defaults={'current_level': 1, 'status': 'pending_level1'},
    )
    return redirect('finance:approve_request', request_id=finance_request.id)

# Financial Management Views
@login_required
def finance_dashboard(request):
    return render(request, 'finance/finance_dashboard.html')

@login_required
def expense_list(request):
    expenses = Expense.objects.all().select_related('category', 'created_by')
    return render(request, 'finance/management/expense_list.html', {'expenses': expenses})

@login_required
def expense_create(request):
    return render(request, 'finance/management/expense_form.html')

@login_required
def income_list(request):
    incomes = Income.objects.all().select_related('created_by')
    return render(request, 'finance/management/income_list.html', {'incomes': incomes})

@login_required
def income_create(request):
    return render(request, 'finance/management/income_form.html')

@login_required
def budget_list(request):
    budgets = Budget.objects.all().select_related('category')
    return render(request, 'finance/management/budget_list.html', {'budgets': budgets})

@login_required
def bank_accounts(request):
    accounts = BankAccount.objects.all()
    return render(request, 'finance/management/bank_accounts.html', {'accounts': accounts})

# Loan Views
@login_required
def loan_list(request):
    if request.user.is_superuser:
        loans = Loan.objects.all().select_related('employee', 'employee__user')
    else:
        try:
            employee = Employee.objects.get(user=request.user)
            loans = Loan.objects.filter(employee=employee)
        except Employee.DoesNotExist:
            loans = []
    return render(request, 'finance/loans/loan_list.html', {'loans': loans})

@login_required
def loan_request(request):
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        employee = Employee.objects.create(
            user=request.user,
            employee_code=f"EMP{request.user.id:06d}",
            is_active=True
        )
    if request.method == 'POST':
        form = LoanRequestForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.employee = employee
            loan.request_date = timezone.now().date()
            loan.status = 'pending'
            loan.save()

            # Ensure every submitted loan enters the approval queue at Level 1.
            FinanceRequest.objects.get_or_create(
                request_type='loan',
                reference_id=loan.id,
                defaults={
                    'current_level': 1,
                    'status': 'pending_level1',
                },
            )

            messages.success(request, f'Your loan request for {loan.amount_requested} has been submitted!')
            return redirect('finance:all_requests')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LoanRequestForm()
    return render(request, 'finance/loans/loan_request_form.html', {'form': form})

@login_required
def loan_detail(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    return render(request, 'finance/loans/loan_detail.html', {'loan': loan})

# All Requests View
@login_required
def all_requests(request):
    """Show all requests with their statuses"""
    from .models import FinanceRequest, Loan, SalaryAdvance
    from core.models import Profile, Role
    
    all_requests_list = []
    
    finance_requests = FinanceRequest.objects.all().order_by('-created_at')
    
    for fr in finance_requests:
        if fr.request_type == 'loan':
            try:
                loan = Loan.objects.get(id=fr.reference_id)
                employee = loan.employee
                
                user_role = "-"
                user_department = "-"
                
                if employee.user and hasattr(employee.user, 'profile'):
                    profile = employee.user.profile
                    if profile.role:
                        user_role = profile.get_role_display()
                    departments = profile.departments.all()
                    if departments.exists():
                        user_department = ", ".join([dept.name for dept in departments])
                
                if fr.status == 'pending_level1':
                    status_badge = '<span class="badge bg-warning">Pending Level 1</span>'
                    status_text = 'pending_level1'
                elif fr.status == 'pending_level2':
                    status_badge = '<span class="badge bg-warning">Pending Level 2</span>'
                    status_text = 'pending_level2'
                elif fr.status == 'approved':
                    status_badge = '<span class="badge bg-success">Approved</span>'
                    status_text = 'approved'
                elif fr.status == 'rejected':
                    status_badge = '<span class="badge bg-danger">Rejected</span>'
                    status_text = 'rejected'
                else:
                    status_badge = f'<span class="badge bg-secondary">{fr.status}</span>'
                    status_text = fr.status
                
                amount_toman = f"{int(loan.amount_requested):,}"
                
                approved_by = []
                if fr.level1_approved_by:
                    approved_by.append(f"L1: {fr.level1_approved_by.username}")
                if fr.level2_approved_by:
                    approved_by.append(f"L2: {fr.level2_approved_by.username}")
                approved_by_text = ", ".join(approved_by) if approved_by else "-"
                
                all_requests_list.append({
                    'id': fr.id,
                    'type': 'Loan',
                    'type_icon': '🏦',
                    'employee_name': employee.user.get_full_name() or employee.user.username,
                    'employee_code': employee.employee_code,
                    'role': user_role,
                    'department': user_department,
                    'amount': amount_toman,
                    'request_date': fr.created_at,
                    'status_badge': status_badge,
                    'status_text': status_text,
                    'approved_by': approved_by_text,
                })
            except Loan.DoesNotExist:
                pass
        elif fr.request_type == 'advance':
            try:
                advance = SalaryAdvance.objects.get(id=fr.reference_id)
                employee = advance.employee

                user_role = "-"
                user_department = "-"

                if hasattr(employee, 'employee_profile'):
                    profile = employee.employee_profile
                    departments = profile.departments.all() if hasattr(profile, 'departments') else []
                    if hasattr(profile, 'role') and profile.role:
                        user_role = profile.get_role_display()
                    if hasattr(departments, 'exists') and departments.exists():
                        user_department = ", ".join([dept.name for dept in departments])

                if fr.status == 'pending_level1':
                    status_badge = '<span class="badge bg-warning">Pending Level 1</span>'
                    status_text = 'pending_level1'
                elif fr.status == 'pending_level2':
                    status_badge = '<span class="badge bg-warning">Pending Level 2</span>'
                    status_text = 'pending_level2'
                elif fr.status == 'approved':
                    status_badge = '<span class="badge bg-success">Approved</span>'
                    status_text = 'approved'
                elif fr.status == 'rejected':
                    status_badge = '<span class="badge bg-danger">Rejected</span>'
                    status_text = 'rejected'
                else:
                    status_badge = f'<span class="badge bg-secondary">{fr.status}</span>'
                    status_text = fr.status

                approved_by = []
                if fr.level1_approved_by:
                    approved_by.append(f"L1: {fr.level1_approved_by.username}")
                if fr.level2_approved_by:
                    approved_by.append(f"L2: {fr.level2_approved_by.username}")
                approved_by_text = ", ".join(approved_by) if approved_by else "-"

                all_requests_list.append({
                    'id': fr.id,
                    'type': 'Salary Advance',
                    'type_icon': '💸',
                    'employee_name': employee.get_full_name() or employee.username,
                    'employee_code': employee.employee_profile.employee_code if hasattr(employee, 'employee_profile') else '-',
                    'role': user_role,
                    'department': user_department,
                    'amount': f"{int(advance.amount):,}",
                    'request_date': fr.created_at,
                    'status_badge': status_badge,
                    'status_text': status_text,
                    'approved_by': approved_by_text,
                })
            except SalaryAdvance.DoesNotExist:
                pass
    
    return render(request, 'finance/all_requests.html', {'requests': all_requests_list})

# Approval Views
@login_required
def pending_approvals(request):
    # Backfill approval records for legacy pending loans that do not have a FinanceRequest row yet.
    linked_loan_ids = FinanceRequest.objects.filter(request_type='loan').values_list('reference_id', flat=True)
    missing_pending_loan_ids = Loan.objects.filter(status='pending').exclude(id__in=linked_loan_ids).values_list('id', flat=True)
    if missing_pending_loan_ids:
        FinanceRequest.objects.bulk_create([
            FinanceRequest(
                request_type='loan',
                reference_id=loan_id,
                current_level=1,
                status='pending_level1',
            )
            for loan_id in missing_pending_loan_ids
        ])

    linked_advance_ids = FinanceRequest.objects.filter(request_type='advance').values_list('reference_id', flat=True)
    missing_pending_advance_ids = SalaryAdvance.objects.filter(status='pending').exclude(id__in=linked_advance_ids).values_list('id', flat=True)
    if missing_pending_advance_ids:
        FinanceRequest.objects.bulk_create([
            FinanceRequest(
                request_type='advance',
                reference_id=advance_id,
                current_level=1,
                status='pending_level1',
            )
            for advance_id in missing_pending_advance_ids
        ])

    user_levels = FinanceApprovalLevel.objects.filter(approver=request.user, is_active=True).values_list('level', flat=True)
    pending = FinanceRequest.objects.filter(current_level__in=user_levels, status__in=['pending_level1', 'pending_level2'])
    return render(request, 'finance/pending_approvals.html', {'pending_requests': pending})

@login_required
def approve_request(request, request_id):
    """View and approve/reject a specific request"""
    from .models import FinanceRequest, FinanceApprovalLevel, Loan, SalaryAdvance
    from django.contrib import messages
    from core.models import Profile, Role
    
    finance_request = get_object_or_404(FinanceRequest, id=request_id)
    
    loan_details = None
    advance_details = None
    user_role = "-"
    user_department = "-"
    
    if finance_request.request_type == "loan":
        try:
            loan = Loan.objects.get(id=finance_request.reference_id)
            loan_details = loan

            user_role, user_department = _profile_meta(loan.employee.user)
        except Loan.DoesNotExist:
            pass
    elif finance_request.request_type == "advance":
        try:
            advance = SalaryAdvance.objects.get(id=finance_request.reference_id)
            advance_details = advance

            user_role, user_department = _profile_meta(advance.employee)
        except SalaryAdvance.DoesNotExist:
            pass
    
    user_levels = FinanceApprovalLevel.objects.filter(approver=request.user, is_active=True).values_list("level", flat=True)
    can_approve = (finance_request.current_level in user_levels or request.user.is_superuser) and "pending" in finance_request.status
    
    if request.method == "POST" and can_approve:
        action = request.POST.get("action")
        comment = request.POST.get("comment", "")
        
        if action == "approve":
            if finance_request.current_level == 1:
                finance_request.level1_approved_by = request.user
                finance_request.level1_approved_at = timezone.now()
                finance_request.level1_comment = comment
                finance_request.current_level = 2
                finance_request.status = "pending_level2"
                messages.success(request, "Request approved at Level 1. Now pending Level 2 approval.")
            elif finance_request.current_level == 2:
                finance_request.level2_approved_by = request.user
                finance_request.level2_approved_at = timezone.now()
                finance_request.level2_comment = comment
                finance_request.status = "approved"
                if loan_details:
                    loan_details.status = "approved"
                    loan_details.approved_by = request.user
                    loan_details.approval_date = timezone.now().date()
                    loan_details.save()
                if advance_details:
                    advance_details.status = "approved"
                    advance_details.approved_by = request.user
                    advance_details.approved_date = timezone.now().date()
                    advance_details.save()
                messages.success(request, "Request fully approved!")
            finance_request.save()
        elif action == "reject":
            finance_request.status = "rejected"
            finance_request.save()
            if loan_details:
                loan_details.status = "rejected"
                loan_details.save()
            if advance_details:
                advance_details.status = "rejected"
                advance_details.save()
            messages.warning(request, "Request rejected.")
        
        return redirect("finance:all_requests")
    
    return render(request, "finance/approve_request.html", {
        "finance_request": finance_request,
        "loan_details": loan_details,
        "advance_details": advance_details,
        "can_approve": can_approve,
        "user_role": user_role,
        "user_department": user_department
    })

@login_required
def all_requests(request):
    """Show requests related to the logged-in user"""
    from .models import FinanceRequest, Loan, SalaryAdvance
    from core.models import Profile, Role
    
    all_requests_list = []
    
    # Get all finance requests
    finance_requests = FinanceRequest.objects.all().order_by('-created_at')
    
    for fr in finance_requests:
        if fr.request_type == 'loan':
            try:
                loan = Loan.objects.get(id=fr.reference_id)
                employee = loan.employee
                
                # Check if request is related to current user
                is_related = False
                
                # Case 1: User is the employee who requested the loan
                if employee.user == request.user:
                    is_related = True
                
                # Case 2: User is a Finance Manager or Director (can see all)
                if request.user.is_superuser:
                    is_related = True
                else:
                    # Check if user is an approver at any level
                    from .models import FinanceApprovalLevel
                    user_levels = FinanceApprovalLevel.objects.filter(
                        approver=request.user, 
                        is_active=True
                    ).values_list('level', flat=True)
                    if user_levels:
                        is_related = True
                
                # Only add if related
                if is_related:
                    user_role = "-"
                    user_department = "-"
                    
                    user_role, user_department = _profile_meta(employee.user)
                    
                    if fr.status == 'pending_level1':
                        status_badge = '<span class="badge bg-warning">Pending Level 1</span>'
                        status_text = 'pending_level1'
                    elif fr.status == 'pending_level2':
                        status_badge = '<span class="badge bg-warning">Pending Level 2</span>'
                        status_text = 'pending_level2'
                    elif fr.status == 'approved':
                        status_badge = '<span class="badge bg-success">Approved</span>'
                        status_text = 'approved'
                    elif fr.status == 'rejected':
                        status_badge = '<span class="badge bg-danger">Rejected</span>'
                        status_text = 'rejected'
                    else:
                        status_badge = f'<span class="badge bg-secondary">{fr.status}</span>'
                        status_text = fr.status
                    
                    amount_toman = f"{int(loan.amount_requested):,}"
                    
                    approved_by = []
                    if fr.level1_approved_by:
                        approved_by.append(f"L1: {fr.level1_approved_by.username}")
                    if fr.level2_approved_by:
                        approved_by.append(f"L2: {fr.level2_approved_by.username}")
                    approved_by_text = ", ".join(approved_by) if approved_by else "-"
                    
                    all_requests_list.append({
                        'id': fr.id,
                        'type': 'Loan',
                        'type_icon': '🏦',
                        'employee_name': employee.user.get_full_name() or employee.user.username,
                        'employee_code': employee.employee_code,
                        'role': user_role,
                        'department': user_department,
                        'amount': amount_toman,
                        'request_date': fr.created_at,
                        'status_badge': status_badge,
                        'status_text': status_text,
                        'approved_by': approved_by_text,
                    })
            except Loan.DoesNotExist:
                pass
        elif fr.request_type == 'advance':
            try:
                advance = SalaryAdvance.objects.get(id=fr.reference_id)
                employee = advance.employee

                is_related = False
                if employee == request.user:
                    is_related = True
                if request.user.is_superuser:
                    is_related = True
                else:
                    from .models import FinanceApprovalLevel
                    user_levels = FinanceApprovalLevel.objects.filter(
                        approver=request.user,
                        is_active=True
                    ).values_list('level', flat=True)
                    if user_levels:
                        is_related = True

                if is_related:
                    user_role = "-"
                    user_department = "-"

                    user_role, user_department = _profile_meta(employee)

                    if fr.status == 'pending_level1':
                        status_badge = '<span class="badge bg-warning">Pending Level 1</span>'
                        status_text = 'pending_level1'
                    elif fr.status == 'pending_level2':
                        status_badge = '<span class="badge bg-warning">Pending Level 2</span>'
                        status_text = 'pending_level2'
                    elif fr.status == 'approved':
                        status_badge = '<span class="badge bg-success">Approved</span>'
                        status_text = 'approved'
                    elif fr.status == 'rejected':
                        status_badge = '<span class="badge bg-danger">Rejected</span>'
                        status_text = 'rejected'
                    else:
                        status_badge = f'<span class="badge bg-secondary">{fr.status}</span>'
                        status_text = fr.status

                    approved_by = []
                    if fr.level1_approved_by:
                        approved_by.append(f"L1: {fr.level1_approved_by.username}")
                    if fr.level2_approved_by:
                        approved_by.append(f"L2: {fr.level2_approved_by.username}")
                    approved_by_text = ", ".join(approved_by) if approved_by else "-"

                    all_requests_list.append({
                        'id': fr.id,
                        'type': 'Salary Advance',
                        'type_icon': '💸',
                        'employee_name': employee.get_full_name() or employee.username,
                        'employee_code': employee.employee_profile.employee_code if hasattr(employee, 'employee_profile') else '-',
                        'role': user_role,
                        'department': user_department,
                        'amount': f"{int(advance.amount):,}",
                        'request_date': fr.created_at,
                        'status_badge': status_badge,
                        'status_text': status_text,
                        'approved_by': approved_by_text,
                    })
            except SalaryAdvance.DoesNotExist:
                pass
    
    return render(request, 'finance/all_requests.html', {'requests': all_requests_list})

@login_required
def loan_list(request):
    """List loan requests - shows user's own loans or all if manager"""
    from .models import Loan, Employee, FinanceApprovalLevel
    
    # Check if user is a finance manager/approver or superuser
    is_approver = FinanceApprovalLevel.objects.filter(
        approver=request.user, 
        is_active=True
    ).exists()
    
    if request.user.is_superuser or is_approver:
        # Finance managers see all loans
        loans = Loan.objects.all().select_related('employee', 'employee__user')
    else:
        # Regular employees see only their own loans
        try:
            employee = Employee.objects.get(user=request.user)
            loans = Loan.objects.filter(employee=employee).select_related('employee__user')
        except Employee.DoesNotExist:
            loans = []
    
    return render(request, 'finance/loans/loan_list.html', {'loans': loans})
