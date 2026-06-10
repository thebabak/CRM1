from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from finance.models import FinanceApprovalLevel

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup default finance approval levels'
    
    def handle(self, *args, **options):
        # Create default approval levels
        levels = [
            {'level': 1, 'role_name': 'Finance Manager', 'order': 1},
            {'level': 2, 'role_name': 'Finance Director', 'order': 2},
            {'level': 3, 'role_name': 'CFO', 'order': 3},
        ]
        
        for level_data in levels:
            level, created = FinanceApprovalLevel.objects.get_or_create(
                level=level_data['level'],
                defaults={
                    'role_name': level_data['role_name'],
                    'order': level_data['order'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created Level {level.level}: {level.role_name}'))
            else:
                self.stdout.write(f'Level {level.level} already exists')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Finance approval levels configured successfully!'))
        self.stdout.write('\n📝 Next steps:')
        self.stdout.write('1. Go to Admin Panel → Finance → Finance Approval Levels')
        self.stdout.write('2. Assign approvers to each level')
        self.stdout.write('3. Set active status for each level')
