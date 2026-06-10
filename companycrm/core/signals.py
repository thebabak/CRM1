from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, Role

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    # Create a Profile whenever a user is created
    if created:
        Profile.objects.get_or_create(
            user=instance,
            defaults={"employee_id": f"E{instance.id:05d}", "role": Role.EMPLOYEE},
        )
