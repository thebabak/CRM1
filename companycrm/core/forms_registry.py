# core/forms_registry.py
# A lightweight registry so the "New Request" page can list all forms.

FORMS = [
    {
        "key": "leave",
        "name": "Leave Request",
        "desc": "Daily or hourly leave with replacement and chain approval.",
        "url_name": "leave_new",  # must match your URL name
        "icon": "🗓️",
    },
    # Add more forms here over time...
]
