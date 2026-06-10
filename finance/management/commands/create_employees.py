from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from finance.models import Employee

User = get_user_model()

class Command(BaseCommand):
    help = 'Create employee records for all existing users'
    
    def handle(self, *args, **options):
        users = User.objects.all()
        created_count = 0
        existing_count = 0
        
        for user in users:
            employee, created = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'employee_code': f"EMP{user.id:06d}",
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"✅ Created employee for: {user.username}")
            else:
                existing_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"\n📊 Summary: {created_count} employees created, {existing_count} already existed"
        ))
