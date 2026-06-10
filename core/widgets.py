# core/widgets.py
from django import forms
from django.forms.widgets import DateInput
from django.utils.dateparse import parse_date
import jdatetime


class PersianDateInput(DateInput):
    """
    Custom widget that accepts Persian/Jalali dates and converts them to Gregorian.
    Displays dates in Persian format (YYYY/MM/DD).
    """
    
    def __init__(self, attrs=None, format='%Y/%m/%d'):
        default_attrs = {'class': 'form-control persian-date-input', 'placeholder': '۱۴۰۳/۰۱/۰۱'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, format=format)
    
    def value_from_datadict(self, data, files, name):
        """
        Convert Persian date to Gregorian before saving
        """
        raw_value = data.get(name)
        if raw_value:
            try:
                # Try parsing as Persian date
                parts = raw_value.strip().replace('/', '-').split('-')
                if len(parts) == 3:
                    # Convert Persian (Jalali) to Gregorian
                    persian_date = jdatetime.date(
                        year=int(parts[0]),
                        month=int(parts[1]),
                        day=int(parts[2])
                    )
                    gregorian_date = persian_date.togregorian()
                    return gregorian_date.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                # If parsing fails, try to parse as Gregorian
                try:
                    parsed = parse_date(raw_value)
                    if parsed:
                        return parsed.strftime('%Y-%m-%d')
                except:
                    pass
            return raw_value
        return None
    
    def format_value(self, value):
        """
        Format the displayed value in Persian calendar
        """
        if value is None:
            return ''
        try:
            # If value is a string, parse it
            if isinstance(value, str):
                value = parse_date(value)
            # Convert Gregorian to Persian for display
            if value:
                persian_date = jdatetime.date.fromgregorian(date=value)
                return persian_date.strftime('%Y/%m/%d')
        except:
            pass
        return str(value) if value else ''


class PersianDateField(forms.DateField):
    """
    Form field that handles Persian dates
    """
    widget = PersianDateInput
    
    def clean(self, value):
        if not value:
            return super().clean(value)
        
        try:
            # Parse Persian date
            if isinstance(value, str):
                parts = value.strip().replace('/', '-').split('-')
                if len(parts) == 3:
                    persian_date = jdatetime.date(
                        year=int(parts[0]),
                        month=int(parts[1]),
                        day=int(parts[2])
                    )
                    value = persian_date.togregorian()
        except (ValueError, TypeError, AttributeError):
            pass
        
        return super().clean(value)