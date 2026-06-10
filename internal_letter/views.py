from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.utils import timezone
from .models import InternalLetter, LetterStatus
from .forms import InternalLetterForm, ReplyForm


@login_required
def letter_list(request):
    """List all letters for the current user"""
    user = request.user
    
    # Get all letters involving the user
    letters = InternalLetter.objects.filter(
        Q(sender=user) | Q(recipient=user) | Q(cc=user)
    ).distinct()
    
    # Apply filters
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'inbox':
        letters = letters.filter(recipient=user, status=LetterStatus.SENT)
    elif filter_type == 'sent':
        letters = letters.filter(sender=user)
    elif filter_type == 'cc':
        letters = letters.filter(cc=user)
    elif filter_type == 'unread':
        letters = letters.filter(recipient=user, status=LetterStatus.SENT).exclude(read_by=user)
    
    # Pagination
    paginator = Paginator(letters, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Count unread letters
    unread_count = InternalLetter.objects.filter(
        recipient=user, 
        status=LetterStatus.SENT
    ).exclude(read_by=user).count()
    
    context = {
        'letters': page_obj,
        'unread_count': unread_count,
        'current_filter': filter_type,
    }
    return render(request, 'internal_letter/letter_list.html', context)


@login_required
def letter_create(request):
    """Create and send a new internal letter immediately"""
    if request.method == 'POST':
        form = InternalLetterForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                letter = form.save(commit=False)
                letter.sender = request.user
                # Send immediately
                letter.status = LetterStatus.SENT
                letter.sent_at = timezone.now()
                letter.save()
                form.save_m2m()  # Save the many-to-many CC field
                
                # Mark sender as read
                letter.read_by.add(request.user)
                
                messages.success(request, f"Letter '{letter.subject}' has been sent successfully!")
                return redirect(f'/letters/{letter.pk}/')
            except Exception as e:
                messages.error(request, f"Error sending letter: {str(e)}")
                return render(request, 'internal_letter/letter_form.html', {'form': form, 'action': 'Send'})
    else:
        form = InternalLetterForm(user=request.user)
    
    return render(request, 'internal_letter/letter_form.html', {'form': form, 'action': 'Send'})


@login_required
def letter_detail(request, pk):
    """View a single letter"""
    try:
        letter = get_object_or_404(
            InternalLetter.objects.prefetch_related('cc', 'read_by'),
            pk=pk
        )
        
        # Check if user has permission to view
        if request.user not in [letter.sender, letter.recipient] and request.user not in letter.cc.all():
            return HttpResponseForbidden("You don't have permission to view this letter.")
        
        # Mark as read if user is recipient or CC
        if letter.status == LetterStatus.SENT:
            letter.mark_as_read(request.user)
        
        # Handle reply
        reply_form = ReplyForm()
        if request.method == 'POST' and 'reply' in request.POST:
            reply_form = ReplyForm(request.POST)
            if reply_form.is_valid():
                try:
                    reply = letter.reply(request.user, reply_form.cleaned_data['body'])
                    messages.success(request, "Reply sent successfully!")
                    return redirect(f'/letters/{reply.pk}/')
                except PermissionError as e:
                    messages.error(request, str(e))
        
        context = {
            'letter': letter,
            'reply_form': reply_form,
            'can_reply': request.user in [letter.recipient, letter.sender] or request.user in letter.cc.all(),
        }
        return render(request, 'internal_letter/letter_detail.html', context)
    except Exception as e:
        messages.error(request, f"Error loading letter: {str(e)}")
        return redirect('/letters/')


@login_required
def letter_send(request, pk):
    """Send a draft letter"""
    try:
        letter = get_object_or_404(InternalLetter, pk=pk, sender=request.user)
        
        if letter.status == LetterStatus.DRAFT:
            letter.send()
            messages.success(request, f"Letter '{letter.subject}' has been sent.")
        else:
            messages.warning(request, "This letter has already been sent.")
        
        return redirect(f'/letters/{letter.pk}/')
    except Exception as e:
        messages.error(request, f"Error sending letter: {str(e)}")
        return redirect('/letters/')


@login_required
def letter_delete(request, pk):
    """Delete a letter"""
    try:
        letter = get_object_or_404(InternalLetter, pk=pk, sender=request.user)
        
        if letter.status == LetterStatus.DRAFT:
            letter.delete()
            messages.success(request, "Letter deleted successfully.")
        else:
            letter.status = LetterStatus.ARCHIVED
            letter.save()
            messages.success(request, "Letter archived successfully.")
        
        return redirect('/letters/')
    except Exception as e:
        messages.error(request, f"Error deleting letter: {str(e)}")
        return redirect('/letters/')


@login_required
def letter_mark_unread(request, pk):
    """Mark a letter as unread"""
    try:
        letter = get_object_or_404(InternalLetter, pk=pk, recipient=request.user)
        letter.read_by.remove(request.user)
        if letter.read_at:
            letter.read_at = None
            letter.save()
        messages.success(request, "Letter marked as unread.")
        return redirect(f'/letters/{letter.pk}/')
    except Exception as e:
        messages.error(request, f"Error marking letter: {str(e)}")
        return redirect('/letters/')
