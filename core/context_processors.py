def unread_letter_count(request):
    """Add unread letter count to all templates"""
    if request.user.is_authenticated:
        try:
            from internal_letter.models import InternalLetter, LetterStatus
            unread_count = InternalLetter.objects.filter(
                recipient=request.user,
                status=LetterStatus.SENT
            ).exclude(read_by=request.user).count()
            return {'unread_letter_count': unread_count}
        except (ImportError, Exception):
            return {'unread_letter_count': 0}
    return {'unread_letter_count': 0}


def unread_notification_count(request):
    """Add unread notification count to all templates"""
    if request.user.is_authenticated:
        try:
            from notifications.models import NotificationRecipient

            unread_qs = NotificationRecipient.objects.filter(
                recipient=request.user,
                read_at__isnull=True,
            ).select_related('notification', 'notification__sender').order_by('-notification__sent_at', '-notification__created_at')

            unread_count = unread_qs.count()
            latest_unread = unread_qs.first()
            latest_unread_id = latest_unread.pk if latest_unread else None
            show_popup = bool(unread_count and latest_unread_id and request.session.get('notification_popup_last_seen_id') != latest_unread_id)

            if show_popup:
                request.session['notification_popup_last_seen_id'] = latest_unread_id

            return {
                'unread_notification_count': unread_count,
                'unread_notification_items': list(unread_qs[:5]),
                'show_notification_popup': show_popup,
            }
        except (ImportError, Exception):
            return {
                'unread_notification_count': 0,
                'unread_notification_items': [],
                'show_notification_popup': False,
            }
    return {
        'unread_notification_count': 0,
        'unread_notification_items': [],
        'show_notification_popup': False,
    }
