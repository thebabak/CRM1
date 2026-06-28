from django import forms
from django.contrib.auth import get_user_model

from core.models import Department
from .models import Notification

User = get_user_model()


class RecipientChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        profile = getattr(obj, 'profile', None)
        full_name = obj.get_full_name() or obj.get_username()
        if not profile:
            return full_name

        role = profile.get_role_display() if getattr(profile, 'role', None) else ''
        department_names = ', '.join(profile.departments.values_list('name', flat=True))
        parts = [full_name]
        if role:
            parts.append(role)
        if department_names:
            parts.append(department_names)
        return ' — '.join(parts)


class NotificationForm(forms.ModelForm):
    send_to_all = forms.BooleanField(
        required=False,
        label='Send to all users',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    recipients = RecipientChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '12'}),
        help_text='Leave empty when sending to everyone.',
    )
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '8'}),
        help_text='Optional: send to everyone in one or more departments.',
    )

    class Meta:
        model = Notification
        fields = ['title', 'body']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notification title'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Write the message here'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        qs = User.objects.filter(is_active=True).select_related('profile').prefetch_related('profile__departments').distinct()
        if self.request and self.request.user.is_authenticated:
            qs = qs.exclude(pk=self.request.user.pk)

        qs = qs.order_by('first_name', 'last_name', 'username')
        self.fields['recipients'].queryset = qs
        self.fields['departments'].queryset = Department.objects.order_by('name')

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('send_to_all') and not cleaned.get('recipients') and not cleaned.get('departments'):
            self.add_error('recipients', 'Choose at least one user, one department, or enable send to all.')
        return cleaned

