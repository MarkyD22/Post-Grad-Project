from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from .models import UserProfile, Equipment, MACHINE_TYPE_CHOICES

#Signup Form
class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    employee_id = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'employee_id', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # The profile will be automatically created with default role 'maintenance'
            # due to the signal in models.py
            if hasattr(user, 'profile'):
                user.profile.employee_id = self.cleaned_data.get('employee_id', '')
                user.profile.save()
        
        return user
#Defined fields for Equipment    
class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = [
            'machine_id',
            'machine_name',
            'machine_type',
            'machine_location',
            'last_calibration_date',
            'last_maintenance_date',
            'calibration_interval_days',
            'maintenance_interval_days',
        ]
        
widgets = {
            'machine_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., MCH-001'}),
            'machine_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Equipment Name'}),
            'machine_type': forms.Select(attrs={'class': 'form-control'}),
            'machine_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'last_calibration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'last_maintenance_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'calibration_interval_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Days (default: 365)'}),
            'maintenance_interval_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Days (default: 90)'}),
        }
        
labels = {
            'machine_id': 'Machine ID',
            'machine_name': 'Machine Name',
            'machine_type': 'Machine Type',
            'machine_location': 'Location',
            'last_calibration_date': 'Last Calibration Date',
            'last_maintenance_date': 'Last Maintenance Date',
            'calibration_interval_days': 'Calibration Interval (Days)',
            'maintenance_interval_days': 'Maintenance Interval (Days)',
        }
    
def clean_machine_id(self):
        """Validate machine ID format and uniqueness"""
        machine_id = self.cleaned_data['machine_id']
        
        # Check if updating existing equipment
        if self.instance and self.instance.pk:
            # If updating, exclude current instance from uniqueness check
            if Equipment.objects.exclude(pk=self.instance.pk).filter(machine_id=machine_id).exists():
                raise forms.ValidationError("Machine ID already exists.")
        else:
            # If creating new, check for uniqueness
            if Equipment.objects.filter(machine_id=machine_id).exists():
                raise forms.ValidationError("Machine ID already exists.")
        
        return machine_id.upper()  # Convert to uppercase for consistency
    
def clean_last_calibration_date(self):
        """Validate calibration date is not in the future"""
        date = self.cleaned_data.get('last_calibration_date')
        if date and date > timezone.now().date():
            raise forms.ValidationError("Calibration date cannot be in the future.")
        return date
    
def clean_last_maintenance_date(self):
        """Validate maintenance date is not in the future"""
        date = self.cleaned_data.get('last_maintenance_date')
        if date and date > timezone.now().date():
            raise forms.ValidationError("Maintenance date cannot be in the future.")
        return date

class EquipmentFilterForm(forms.Form):
    """Form for filtering equipment list"""
    STATUS_CHOICES = [
        ('all', 'All Equipment'),
        ('overdue_maintenance', 'Overdue Maintenance'),
        ('overdue_calibration', 'Overdue Calibration'),
        ('due_soon', 'Due Soon (2 weeks)'),
    ]
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by ID, name, or location...',
            'class': 'form-control'
        })
    )
    
    machine_type = forms.ChoiceField(
        choices=[('', 'All Types')] + list(MACHINE_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class QuickUpdateForm(forms.ModelForm):
    """Form for quickly updating maintenance and calibration dates"""
    class Meta:
        model = Equipment
        fields = ['last_maintenance_date', 'last_calibration_date']
        widgets = {
            'last_maintenance_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'last_calibration_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            )
        }
    
 #   def __init__(self, *args, **kwargs):
 #      super().__init__(*args, **kwargs)
 #       self.fields['last_maintenance_date'].help_text = 'Enter the date maintenance was completed'
 #       self.fields['last_calibration_date'].help_text = 'Enter the date calibration was completed'

class ProcedureCompleteForm(forms.Form):
    """Form for marking procedures complete"""
    PROCEDURE_CHOICES = [
        ('calibration', 'Calibration'),
        ('maintenance', 'Maintenance'),
    ]
    
    procedure_type = forms.ChoiceField(
        choices=PROCEDURE_CHOICES,
        widget=forms.RadioSelect,
        label="Procedure Type"
    )
    completion_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=date.today,
        label="Completion Date"
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        label="Notes (optional)"
    )