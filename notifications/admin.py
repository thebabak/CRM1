from django.contrib import admin

from .models import Notification, NotificationRecipient


class NotificationRecipientInline(admin.TabularInline):
    model = NotificationRecipient
    extra = 0
    readonly_fields = ('created_at', 'read_at')
    autocomplete_fields = ('recipient',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'sender', 'send_to_all', 'sent_at', 'created_at', 'recipient_count', 'read_count')
    list_filter = ('send_to_all', 'sent_at', 'created_at')
    search_fields = ('title', 'body', 'sender__username', 'sender__first_name', 'sender__last_name')
    filter_horizontal = ('target_departments',)
    inlines = [NotificationRecipientInline]

    def recipient_count(self, obj):
        return obj.deliveries.count()

    def read_count(self, obj):
        return obj.deliveries.filter(read_at__isnull=False).count()

    recipient_count.short_description = 'Recipients'
    read_count.short_description = 'Read'


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ('notification', 'recipient', 'read_at', 'created_at')
    list_filter = ('read_at', 'created_at')
    search_fields = ('notification__title', 'recipient__username', 'recipient__first_name', 'recipient__last_name')

