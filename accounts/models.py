from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    title = models.CharField(max_length=100, verbose_name="Ünvan", blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"

    class Meta:
        verbose_name = "Kullanıcı Ünvanı"
        verbose_name_plural = "Kullanıcı Ünvanları"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
