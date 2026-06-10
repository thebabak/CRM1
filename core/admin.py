from django.contrib import admin
from .models import Department, Position, Profile, Request, Approval, LeaveRequest, LeaveBalanceAdjustment

# Simple registrations
admin.site.register(Department)
admin.site.register(Position)
admin.site.register(Profile)
admin.site.register(Request)
admin.site.register(Approval)
admin.site.register(LeaveRequest)
admin.site.register(LeaveBalanceAdjustment)
