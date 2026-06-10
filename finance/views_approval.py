from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import FinanceRequest, FinanceApprovalLevel

@login_required
def pending_approvals(request):
    """View pending approvals for the logged-in user"""
    # Get requests that need this user's approval
    user_levels = FinanceApprovalLevel.objects.filter(approver=request.user, is_active=True).values_list('level', flat=True)
    
    pending = FinanceRequest.objects.filter(
        current_level__in=user_levels,
        status__in=['pending_level1', 'pending_level2', 'pending_level3']
    )
    
    return render(request, 'finance/pending_approvals.html', {'pending_requests': pending})

@login_required
def approve_request(request, request_id):
    """Approve or reject a specific request"""
    finance_request = get_object_or_404(FinanceRequest, id=request_id)
    
    # Check permission
    user_levels = FinanceApprovalLevel.objects.filter(approver=request.user, is_active=True).values_list('level', flat=True)
    if finance_request.current_level not in user_levels and not request.user.is_superuser:
        messages.error(request, "You don't have permission to approve this request")
        return redirect('finance:pending_approvals')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')
        
        if action == 'approve':
            # Update the request
            if finance_request.current_level == 1:
                finance_request.level1_approved_by = request.user
                finance_request.level1_approved_at = timezone.now()
                finance_request.level1_comment = comment
                finance_request.current_level = 2
                finance_request.status = 'pending_level2'
                messages.success(request, f"Request approved at Level 1. Now pending Level 2 approval.")
                
            elif finance_request.current_level == 2:
                finance_request.level2_approved_by = request.user
                finance_request.level2_approved_at = timezone.now()
                finance_request.level2_comment = comment
                finance_request.status = 'approved'
                messages.success(request, "Request fully approved!")
            
            finance_request.save()
            
        elif action == 'reject':
            finance_request.status = 'rejected'
            if finance_request.current_level == 1:
                finance_request.level1_comment = comment
            else:
                finance_request.level2_comment = comment
            finance_request.save()
            messages.warning(request, "Request rejected.")
        
        return redirect('finance:pending_approvals')
    
    return render(request, 'finance/approve_request.html', {'request': finance_request})
