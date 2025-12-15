from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import date, timedelta

# Create your models here.

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('administrator', 'Administrator'),
        ('maintenance', 'Maintenance/Calibration User'),
        ('quality', 'Quality Engineer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True, default='')
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

# Signal to automatically create/update profile when user is created/updated
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, default='') #default role

@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
     if created:
        UserProfile.objects.create(user=instance)
     else:
       
        try:
            instance.profile.save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance, role='')

#Equipment Database models
#update these fields per customer requirements
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

MACHINE_TYPE_CHOICES = [
    ('PRODUCTION', 'Production Equipment'),
    ('TESTING', 'Testing Equipment'),
    ('PACKAGING', 'Packaging Equipment'),
    ('CALIBRATION', 'Calibration Equipment'),
    ('OTHER', 'Other'),
]
#Defined Equipment fields for Migration
class Equipment(models.Model):
    machine_id = models.CharField(max_length=50, primary_key=True, help_text="Unique machine identifier")
    machine_name = models.CharField(max_length=200, help_text="Name/description of the machine")
    machine_type = models.CharField(max_length=20, choices=MACHINE_TYPE_CHOICES, default='PRODUCTION')
    machine_location = models.CharField(max_length=200, help_text="Physical location of the machine")
    last_calibration_date = models.DateField(null=True, blank=True, help_text="Date of last calibration")
    last_maintenance_date = models.DateField(null=True, blank=True, help_text="Date of last maintenance")
    
    # Interval fields
    calibration_interval_days = models.IntegerField(default=365, help_text="Days between calibrations")
    maintenance_interval_days = models.IntegerField(default=90, help_text="Days between maintenance")
    
    # Metadata fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['machine_name']
        verbose_name = 'Equipment'
        verbose_name_plural = 'Equipment'
    
    def __str__(self):
        return f"{self.machine_id} - {self.machine_name}"
    
    @property
    def next_calibration_date(self):
        """Calculate next calibration due date"""
        if self.last_calibration_date:
            return self.last_calibration_date + timedelta(days=self.calibration_interval_days)
        return None
    
    @property
    def next_maintenance_date(self):
        """Calculate next maintenance due date"""
        if self.last_maintenance_date:
            return self.last_maintenance_date + timedelta(days=self.maintenance_interval_days)
        return None
    
    @property
    def is_calibration_overdue(self):
        """Check if calibration is overdue"""
        next_date = self.next_calibration_date
        if next_date:
            return timezone.now().date() > next_date
        return False
    
    @property
    def is_maintenance_overdue(self):
        """Check if maintenance is overdue"""
        next_date = self.next_maintenance_date
        if next_date:
            return timezone.now().date() > next_date
        return False
    
    @property
    def days_until_calibration(self):
        """Days until next calibration (negative if overdue)"""
        next_date = self.next_calibration_date
        if next_date:
            return (next_date - timezone.now().date()).days
        return None
    
    @property
    def days_until_maintenance(self):
        """Days until next maintenance (negative if overdue)"""
        next_date = self.next_maintenance_date
        if next_date:
            return (next_date - timezone.now().date()).days
        return None