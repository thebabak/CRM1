from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from core.models import Department


class Notification(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sent_notifications',
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    send_to_all = models.BooleanField(default=False)
    target_departments = models.ManyToManyField(Department, blank=True, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title

    def send(self, recipients=None, departments=None):
        if self.sent_at:
            return []

        user_model = get_user_model()

        if self.send_to_all:
            recipient_qs = user_model.objects.filter(is_active=True)
        else:
            recipient_qs = user_model.objects.none()

        if recipients is not None:
            recipient_qs = recipient_qs | recipients

        if departments is not None:
            department_users = user_model.objects.filter(
                is_active=True,
                profile__departments__in=departments,
            )
            recipient_qs = recipient_qs | department_users

        recipient_qs = recipient_qs.exclude(pk=self.sender_id).distinct()

        recipient_ids = list(recipient_qs.values_list('pk', flat=True))

        self.sent_at = timezone.now()
        self.save(update_fields=['sent_at'])

        NotificationRecipient.objects.bulk_create(
            [
                NotificationRecipient(notification=self, recipient_id=recipient_id)
                for recipient_id in recipient_ids
            ]
        )
        return recipient_ids


class NotificationRecipient(models.Model):
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='deliveries',
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_deliveries',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['notification', 'recipient'],
                name='unique_notification_recipient',
            )
        ]

    def __str__(self) -> str:
        return f'{self.notification.title} -> {self.recipient}'

    def mark_read(self):
        if self.read_at is None:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])

