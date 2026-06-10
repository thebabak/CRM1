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
