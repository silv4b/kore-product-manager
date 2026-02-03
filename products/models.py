from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Product(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="products", null=True, blank=True
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="light")

    def __str__(self):
        return f"{self.user.username}'s profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


from django.contrib.auth.signals import user_logged_in


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, "profile"):
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


@receiver(user_logged_in)
def load_user_theme(sender, request, user, **kwargs):
    if hasattr(user, "profile"):
        request.session["theme"] = user.profile.theme
