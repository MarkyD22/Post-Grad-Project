from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('administrator', 'Administrator'),
        ('maintenance', 'Maintenance/Calibration User'),
        ('quality', 'Quality Engineer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='maintenance')
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
        UserProfile.objects.create(user=instance, role='') #default role

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance, role='')

#Equipment Database models
class Equipment(models.Model):
    #update these fields per customer requirements
    EQUIPMENT_TYPE_CHOICES = [
        ('cnc_machine', 'CNC Machine'),
        ('press', 'Press'),
        ('conveyor', 'Conveyor System'),
        ('scale', 'Scale/Balance'),
        ('gauge', 'Measurement Gauge'),
        ('torque_wrench', 'Torque Wrench'),
        ('test_equipment', 'Test Equipment'),
        ('packaging', 'Packaging Equipment'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('calibration', 'Under Calibration'),
        ('inactive', 'Inactive'),
        ('decommissioned', 'Decommissioned'),
    ]
    
    # Primary key as specified in requirements
    Machine_ID = models.CharField(max_length=50, primary_key=True, help_text="Unique machine identifier")
    Machine_Name = models.CharField(max_length=200, help_text="Descriptive name of the equipment")
    Machine_Type = models.CharField(max_length=50, choices=EQUIPMENT_TYPE_CHOICES, help_text="Type/category of equipment")
    Machine_Location = models.CharField(max_length=200, help_text="Physical location of the equipment")
    
    # Editable date fields as specified
    Last_Calibration_Date = models.DateField(null=True, blank=True, help_text="Date of last calibration")
    Last_Maintenance_Date = models.DateField(null=True, blank=True, help_text="Date of last maintenance")
    
    # Additional useful fields for a complete system
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    manufacturer = models.CharField(max_length=100, blank=True, help_text="Equipment manufacturer")
    model_number = models.CharField(max_length=100, blank=True, help_text="Model/serial number")
    installation_date = models.DateField(null=True, blank=True, help_text="Date equipment was installed")
    
    # Maintenance and calibration intervals (in days), may need to add extra intervals fror calibrations and maintenance
    maintenance_interval = models.PositiveIntegerField(default=90, help_text="Days between maintenance (default: 90)")
    calibration_interval = models.PositiveIntegerField(default=365, help_text="Days between calibration (default: 365)")
    
    # Tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment_created')
    last_updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipment_updated')
    
    class Meta:
        verbose_name = "Equipment"
        verbose_name_plural = "Equipment"
        ordering = ['Machine_ID']
    
    def __str__(self):
        return f"{self.Machine_ID} - {self.Machine_Name}"
    
    @property
    def next_maintenance_due(self):
        """Calculate when next maintenance is due"""
        if self.Last_Maintenance_Date:
            return self.Last_Maintenance_Date + timedelta(days=self.maintenance_interval)
        return None
    
    @property
    def next_calibration_due(self):
        """Calculate when next calibration is due"""
        if self.Last_Calibration_Date:
            return self.Last_Calibration_Date + timedelta(days=self.calibration_interval)
        return None
    
    @property
    def maintenance_status(self):
        """Get maintenance status (overdue, due soon, ok)"""
        if not self.Last_Maintenance_Date:
            return 'no_data'
        
        next_due = self.next_maintenance_due
        if not next_due:
            return 'no_data'
        
        today = timezone.now().date()
        days_until_due = (next_due - today).days
        
        if days_until_due < 0:
            return 'overdue'
        elif days_until_due <= 14:  # Due within 2 weeks
            return 'due_soon'
        else:
            return 'ok'
    
    @property
    def calibration_status(self):
        """Get calibration status (overdue, due soon, ok)"""
        if not self.Last_Calibration_Date:
            return 'no_data'
        
        next_due = self.next_calibration_due
        if not next_due:
            return 'no_data'
        
        today = timezone.now().date()
        days_until_due = (next_due - today).days
        
        if days_until_due < 0:
            return 'overdue'
        elif days_until_due <= 14:  # Due within 2 weeks
            return 'due_soon'
        else:
            return 'ok'
    
    @property
    def days_until_maintenance(self):
        """Days until next maintenance (negative if overdue)"""
        if not self.next_maintenance_due:
            return None
        return (self.next_maintenance_due - timezone.now().date()).days
    
    @property
    def days_until_calibration(self):
        """Days until next calibration (negative if overdue)"""
        if not self.next_calibration_due:
            return None
        return (self.next_calibration_due - timezone.now().date()).days
    
