from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile

"""
Signal handlers that ensure a Profile exists for every User.
"""

User = get_user_model()


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    """
    Create a Profile for every newly created User.
    """

    if kwargs.get("raw"):
        return
    if created:
        Profile.objects.get_or_create(user=instance)
