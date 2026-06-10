from django import forms
from .models import SalaryAdvance, Loan

class SalaryAdvanceForm(forms.ModelForm):
    installment_months = forms.TypedChoiceField(
        choices=[
            ('', 'Select installment period'),
            (1, '1 month'),
            (2, '2 months'),
            (3, '3 months'),
            (6, '6 months'),
            (12, '12 months'),
        ],
        coerce=int,
        empty_value='',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = SalaryAdvance
        fields = ['amount', 'reason', 'installment_months', 'description']
        labels = {
            'amount': 'Amount Requested',
            'reason': 'Reason',
            'installment_months': 'Installment Period',
            'description': 'Additional Notes',
        }
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount in Toman', 'min': '0', 'step': '100000'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Explain why you need this advance'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes (optional)'}),
        }


class LoanRequestForm(forms.ModelForm):
    """Form for employees to request a loan"""
    
    loan_type = forms.ChoiceField(
        choices=[
            ('personal', 'Personal Loan'),
            ('emergency', 'Emergency Loan'),
            ('housing', 'Housing Loan'),
            ('education', 'Education Loan'),
            ('vehicle', 'Vehicle Loan'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    amount_requested = forms.DecimalField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount',
            'min': '0',
            'step': '1000'
        })
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please explain why you need this loan'
        })
    )
    
    tenure_months = forms.ChoiceField(
        choices=[
            (6, '6 months'),
            (12, '12 months (1 year)'),
            (24, '24 months (2 years)'),
            (36, '36 months (3 years)'),
            (48, '48 months (4 years)'),
            (60, '60 months (5 years)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Loan
        fields = ['loan_type', 'amount_requested', 'reason', 'tenure_months']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure tenure_months choices are set
        self.fields['tenure_months'].choices = [
            (6, '6 months'),
            (12, '12 months (1 year)'),
            (24, '24 months (2 years)'),
            (36, '36 months (3 years)'),
            (48, '48 months (4 years)'),
            (60, '60 months (5 years)'),
        ]


class LoanApprovalForm(forms.ModelForm):
    """Form for finance management to approve/reject loan"""
    
    class Meta:
        model = Loan
        fields = ['amount_approved', 'interest_rate', 'tenure_months', 'status', 'comments']
        widgets = {
            'amount_approved': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Approved amount'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Annual interest rate %', 'step': '0.01'}),
            'tenure_months': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add comments or conditions'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tenure_months'].choices = [
            (6, '6 months'),
            (12, '12 months (1 year)'),
            (24, '24 months (2 years)'),
            (36, '36 months (3 years)'),
            (48, '48 months (4 years)'),
            (60, '60 months (5 years)'),
        ]

class LoanRequestForm(forms.ModelForm):
    """Form for employees to request a loan"""
    
    loan_type = forms.ChoiceField(
        choices=[
            ('personal', 'Personal Loan'),
            ('emergency', 'Emergency Loan'),
            ('housing', 'Housing Loan'),
            ('education', 'Education Loan'),
            ('vehicle', 'Vehicle Loan'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    amount_requested = forms.DecimalField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount in Toman',
            'min': '0',
            'step': '100000'
        })
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please explain why you need this loan'
        })
    )
    
    tenure_months = forms.ChoiceField(
        choices=[
            (6, '6 months'),
            (12, '12 months (1 year)'),
            (24, '24 months (2 years)'),
            (36, '36 months (3 years)'),
            (48, '48 months (4 years)'),
            (60, '60 months (5 years)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Loan
        fields = ['loan_type', 'amount_requested', 'reason', 'tenure_months']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tenure_months'].choices = [
            (6, '6 months'),
            (12, '12 months (1 year)'),
            (24, '24 months (2 years)'),
            (36, '36 months (3 years)'),
            (48, '48 months (4 years)'),
            (60, '60 months (5 years)'),
        ]

class LoanRequestForm(forms.ModelForm):
    """Form for employees to request a loan"""
    
    loan_type = forms.ChoiceField(
        choices=[
            ('personal', 'Personal Loan'),
            ('emergency', 'Emergency Loan'),
            ('housing', 'Housing Loan'),
            ('education', 'Education Loan'),
            ('vehicle', 'Vehicle Loan'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    amount_requested = forms.DecimalField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount in Toman',
            'min': '0',
            'step': '100000'
        })
    )
    
    reason = forms.CharField(
        required=False,  # Make it optional
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Optional - Please explain why you need this loan (not required)'
        })
    )
    
    tenure_months = forms.ChoiceField(
        choices=[
            (6, '6 months'),
            (12, '12 months (1 year)'),
            (24, '24 months (2 years)'),
            (36, '36 months (3 years)'),
            (48, '48 months (4 years)'),
            (60, '60 months (5 years)'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Loan
        fields = ['loan_type', 'amount_requested', 'reason', 'tenure_months']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tenure_months'].choices = [
            (6, '6 months'),
            (12, '12 months (1 year)'),
            (24, '24 months (2 years)'),
            (36, '36 months (3 years)'),
            (48, '48 months (4 years)'),
            (60, '60 months (5 years)'),
        ]
