from typing import Any, Type
from django.db.models.base import Model
from django.db.models.signals import post_save
from django.dispatch import receiver
from loguru import logger
from config.settings.base import AUTH_USER_MODEL
from core_apps.user_profile.models import Profile

@receiver(signal=post_save, sender=AUTH_USER_MODEL)
def created_user_profile(sender: Type[Model], instance: Model, created:bool, **kwargs: Any) -> None:
    if created:
        Profile.objects.create(user=instance)
        logger.info(
            f"Profile created for {instance.first_name} {instance.last_name}"
        )

@receiver(signal=post_save, sender=AUTH_USER_MODEL)
def save_user_profile(sender: Type[Model], instance: Model, **kwargs: Any):
    instance.profile.save() # called after an instance is saved

    # now let the app knows about the signal for the model by declaring the ready functionin the app directory app.py file