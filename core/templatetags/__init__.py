# core/templatetags/persian_calendar.py
from django import template
from django.utils import timezone
import jdatetime
from datetime import date

register = template.Library()

@register.filter
def to_persian_date(value):
    """Convert Gregorian date to Persian (Jalali) date string"""
    if not value:
        return ""
    
    if isinstance(value, str):
        return value
    
    try:
        # Convert to jdatetime
        if isinstance(value, date):
            jd = jdatetime.date.fromgregorian(date=value)
        else:
            jd = jdatetime.date.fromgregorian(datetime=value)
        
        # Format: ۱۴۰۳/۱۲/۲۵
        persian_months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 
                         'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
        
        return f"{jd.year}/{jd.month:02d}/{jd.day:02d}"
    except Exception:
        return str(value)

@register.filter
def to_persian_date_long(value):
    """Convert to long Persian date format: ۲۵ اسفند ۱۴۰۳"""
    if not value:
        return ""
    
    try:
        if isinstance(value, date):
            jd = jdatetime.date.fromgregorian(date=value)
        else:
            jd = jdatetime.date.fromgregorian(datetime=value)
        
        persian_months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 
                         'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
        
        return f"{jd.day} {persian_months[jd.month - 1]} {jd.year}"
    except Exception:
        return str(value)

@register.filter
def to_persian_datetime(value):
    """Convert Gregorian datetime to Persian datetime string"""
    if not value:
        return ""
    
    try:
        jd = jdatetime.datetime.fromgregorian(datetime=value)
        return f"{jd.year}/{jd.month:02d}/{jd.day:02d} - {jd.hour:02d}:{jd.minute:02d}"
    except Exception:
        return str(value)

@register.simple_tag
def persian_year():
    """Return current Persian year"""
    return str(jdatetime.date.today().year)

@register.simple_tag
def persian_today():
    """Return today's Persian date"""
    today = jdatetime.date.today()
    return f"{today.year}/{today.month:02d}/{today.day:02d}"