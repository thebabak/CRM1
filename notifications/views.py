from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.models import Role

from .forms import NotificationForm
from .models import Notification, NotificationRecipient


def is_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True

    profile = getattr(user, 'profile', None)
    return getattr(profile, 'role', None) in [Role.MIDDLE, Role.EXECUTIVE, Role.BOARD]


@login_required
def notification_inbox(request):
    deliveries = (
        NotificationRecipient.objects
        .select_related('notification', 'notification__sender', 'recipient')
        .filter(recipient=request.user)
        .order_by('-notification__sent_at', '-notification__created_at')
    )

    unread_count = deliveries.filter(read_at__isnull=True).count()

    context = {
        'deliveries': deliveries,
        'unread_count': unread_count,
        'can_manage_notifications': is_manager(request.user),
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_detail(request, pk):
    delivery = get_object_or_404(
        NotificationRecipient.objects.select_related('notification', 'notification__sender', 'recipient'),
        pk=pk,
        recipient=request.user,
    )

    if delivery.read_at is None:
        delivery.mark_read()

    context = {
        'delivery': delivery,
        'notification': delivery.notification,
    }
    return render(request, 'notifications/notification_detail.html', context)


@login_required
@user_passes_test(is_manager)
def notification_create(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST, request=request)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.sender = request.user
            notification.send_to_all = form.cleaned_data['send_to_all']
            notification.save()
            notification.target_departments.set(form.cleaned_data['departments'])
            notification.send(
                recipients=form.cleaned_data['recipients'],
                departments=form.cleaned_data['departments'],
            )
            messages.success(request, 'Notification sent successfully.')
            return redirect('notifications:sent')
    else:
        form = NotificationForm(request=request)

    return render(request, 'notifications/notification_form.html', {'form': form})


@login_required
@user_passes_test(is_manager)
def notification_sent_list(request):
    notifications = (
        Notification.objects
        .filter(sender=request.user)
        .prefetch_related('deliveries__recipient', 'target_departments')
        .order_by('-sent_at', '-created_at')
    )

    rows = []
    for notification in notifications:
        deliveries = list(notification.deliveries.all())
        total_recipients = len(deliveries)
        read_count = sum(1 for delivery in deliveries if delivery.read_at is not None)
        departments = list(notification.target_departments.all())
        rows.append({
            'notification': notification,
            'total_recipients': total_recipients,
            'read_count': read_count,
            'departments': departments,
        })

    return render(request, 'notifications/notification_sent_list.html', {'rows': rows})


@login_required
@user_passes_test(is_manager)
def notification_sent_detail(request, pk):
    notification = get_object_or_404(
        Notification.objects.prefetch_related('deliveries__recipient', 'deliveries__recipient__profile', 'target_departments'),
        pk=pk,
        sender=request.user,
    )

    deliveries = notification.deliveries.select_related('recipient', 'recipient__profile').order_by('recipient__username')
    read_count = deliveries.filter(read_at__isnull=False).count()

    context = {
        'notification': notification,
        'deliveries': deliveries,
        'read_count': read_count,
        'total_recipients': deliveries.count(),
        'departments': notification.target_departments.all(),
    }
    return render(request, 'notifications/notification_sent_detail.html', context)

