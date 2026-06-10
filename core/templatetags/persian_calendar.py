from django import template
from django.template.defaultfilters import stringfilter
import datetime

register = template.Library()

# Persian digits mapping
PERSIAN_DIGITS = {
    '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
    '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
}

def to_persian_number(num):
    """Convert English numbers to Persian (Eastern Arabic) numerals"""
    return ''.join(PERSIAN_DIGITS.get(c, c) for c in str(num))

def gregorian_to_persian(year, month, day):
    """Convert Gregorian date to Persian (Jalali) date"""
    persian_year = year - 621
    
    # Calculate day of year
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day_of_year = sum(month_days[:month-1]) + day
    
    # Adjust for leap year
    if month > 2 and ((year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)):
        day_of_year += 1
    
    # Persian calendar starts on March 21 (day 80-81 of Gregorian year)
    persian_day_of_year = day_of_year - 79
    if persian_day_of_year <= 0:
        persian_year -= 1
        persian_day_of_year += 366
    
    # Persian months
    persian_month_days = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]
    
    persian_month = 1
    for days_in_month in persian_month_days:
        if persian_day_of_year <= days_in_month:
            break
        persian_day_of_year -= days_in_month
        persian_month += 1
    
    return {
        'year': persian_year,
        'month': persian_month,
        'day': persian_day_of_year
    }

@register.filter
@stringfilter
def to_persian_date(value):
    """Convert Gregorian date string to Persian date (LTR format)"""
    if not value:
        return ''
    
    try:
        if isinstance(value, str):
            if ' ' in value:
                value = value.split(' ')[0]
            year, month, day = map(int, value.split('-'))
        elif isinstance(value, datetime.date):
            year, month, day = value.year, value.month, value.day
        else:
            return value
        
        persian = gregorian_to_persian(year, month, day)
        # Return in LTR format: YYYY/MM/DD with Persian digits
        return f"{to_persian_number(persian['year'])}/{to_persian_number(persian['month'])}/{to_persian_number(persian['day'])}"
    except:
        return value

@register.filter
@stringfilter
def to_persian_datetime(value):
    """Convert datetime to Persian date and time (LTR format)"""
    if not value:
        return ''
    
    try:
        if ' ' in value:
            date_part, time_part = value.split(' ')
            return to_persian_date(date_part) + ' ' + time_part
        else:
            return to_persian_date(value)
    except:
        return value

@register.filter
def persian_digits(value):
    """Convert any number to Persian digits"""
    return to_persian_number(str(value))

@register.simple_tag
def persian_today():
    """Return today's date in Persian calendar (LTR format)"""
    today = datetime.date.today()
    persian = gregorian_to_persian(today.year, today.month, today.day)
    return f"{to_persian_number(persian['year'])}/{to_persian_number(persian['month'])}/{to_persian_number(persian['day'])}"

@register.simple_tag
def persian_year():
    """Return current Persian year"""
    today = datetime.date.today()
    persian = gregorian_to_persian(today.year, today.month, today.day)
    return to_persian_number(persian['year'])
