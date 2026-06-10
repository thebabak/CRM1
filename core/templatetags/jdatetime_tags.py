# core/templatetags/jdatetime_tags.py
from django import template
from django.utils import timezone
import jdatetime

register = template.Library()

@register.filter
def to_jalali(value, format_string='%Y/%m/%d'):
    """Convert Gregorian date to Jalali (Persian) date"""
    if not value:
        return ''
    
    try:
        # Make timezone aware if naive
        if hasattr(value, 'date'):
            # It's a datetime
            if timezone.is_naive(value):
                value = timezone.make_aware(value)
            jalali_date = jdatetime.date.fromgregorian(date=value.date())
        else:
            # It's a date
            jalali_date = jdatetime.date.fromgregorian(date=value)
        
        return jalali_date.strftime(format_string)
    except:
        return str(value)