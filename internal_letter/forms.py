# internal_letter/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import InternalLetter

User = get_user_model()


class InternalLetterForm(forms.ModelForm):
    class Meta:
        model = InternalLetter
        fields = ['subject', 'body', 'recipient', 'cc']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter subject'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Write your message here...'
            }),
            'recipient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cc': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Exclude the current user from recipient and CC choices
        if user:
            self.fields['recipient'].queryset = User.objects.exclude(pk=user.pk)
            self.fields['cc'].queryset = User.objects.exclude(pk=user.pk)
        
        # Add helpful labels
        self.fields['recipient'].label = "To"
        self.fields['cc'].help_text = "Hold Ctrl/Cmd to select multiple users"


class ReplyForm(forms.Form):
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Write your reply here...'
        }),
        label="Your Reply"
    )