from django.db import models
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

User = get_user_model()


class Plant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    plant_name = models.CharField(max_length=255)
   
    def __str__(self):
        return self.plant_name
    
class GardenBox(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    row = models.IntegerField()
    col = models.IntegerField()
    plant = models.CharField(max_length=100)
    plant_image = models.ImageField(upload_to='garden_images')  

    def __str__(self):
        return f"{self.user.username}'s box at {self.row}, {self.col} with {self.plant}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    id_user = models.IntegerField()
    bio = models.TextField(blank=True, max_length=500)
    profileimg = models.ImageField(upload_to='profile_images', default='blank-profile-picture.png')
    location = models.CharField(max_length=100, blank=True)
    score = models.IntegerField(default=100)
    badge = models.CharField(max_length=50, blank=True)
    dark_mode = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)
    location_services = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='en', choices=[
        ('en', 'English'),
        ('es', 'Español'),
        ('fr', 'Français'),
        ('de', 'Deutsch')
    ])

    def __str__(self):
        return self.user.username

    def add_score(self, points):
        self.score += points
        self.check_badges()
        self.save()

    def check_badges(self):
        if self.score >= 80:
            self.badge = "Legend"
        elif self.score >= 50:
            self.badge = "Gold"
        elif self.score >= 30:
            self.badge = "Silver"
        elif self.score >= 10:
            self.badge = "Bronze"
        else:
            self.badge = ""
        self.save()

    def save(self, *args, **kwargs):
        # Ensure id_user is always set to the user's id
        if not self.id_user:
            self.id_user = self.user.id
        super().save(*args, **kwargs)
