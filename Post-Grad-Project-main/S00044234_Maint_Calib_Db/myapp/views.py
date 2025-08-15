from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import UserProfile
from .forms import CustomUserCreationForm  # Only import forms that exist
from django.http import JsonResponse
from django.core.paginator import Paginator
import logging
import json
from .models import Equipment, MACHINE_TYPE_CHOICES  
from .forms import EquipmentForm  
from datetime import datetime, timedelta

#Add logging
logger=logging.getLogger(__name__)

#Apply the decorator to the following views
@login_required
def dashboard(request):
    """Main dashboard that redirects based on user role"""
    try:
        user_profile = request.user.profile
        user_role = request.user.profile.role
        
        if user_role == 'administrator':
            return redirect('admin_dashboard')
        elif user_role == 'maintenance':
            return redirect('maintenance_dashboard')
        elif user_role == 'quality':
            return redirect('quality_dashboard')
        else:
            return redirect('default_dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, "Profile not found. Please contact administrator.")
        return redirect('home')
    
def role_required(allowed_roles):
    """Decorator to check if user has required role"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            try:
                user_role = request.user.profile.role
                if user_role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    return HttpResponseForbidden("You don't have permission to access this page.")
            except UserProfile.DoesNotExist:
                return HttpResponseForbidden("Profile not found.")
        return wrapper
    return decorator  
#Admin Dashboard
@login_required
@role_required(['administrator'])
def admin_dashboard(request):
    context = {
        'user_role': 'Administrator',
        'page_title': 'Administrator Dashboard',
        'page_subtitle': 'Complete system administration and management',
        'welcome_message': 'You have full administrative access to the system.',
        'total_users': UserProfile.objects.count(),
        'total_equipment': 45,  # To be replaced with actual Equipment.objects.count() later
        'pending_tasks': 8,
        'overdue_items': 2,
    }
    return render(request, 'myapp/admin_dashboard.html', context)

#Maintenance Dashboard
@login_required
@role_required(['maintenance'])
def maintenance_dashboard(request):
    context = {
        'user_role': 'Maintenance/Calibration User',
        'page_title': 'Maintenance Dashboard',
        'page_subtitle': 'Track and complete maintenance and calibration tasks',
        'welcome_message': 'Review your assigned tasks and equipment due for maintenance.',
        'tasks_this_week': 12,
        'completed_tasks': 89,
        'total_equipment': 45,
        'open_issues': 3,
    }
    return render(request, 'myapp/maintenance_dashboard.html', context)

#Quality Dashboard
@login_required
@role_required(['quality'])
def quality_dashboard(request):
    context = {
'user_role': 'Quality Engineer',
        'page_title': 'Quality Dashboard',
        'page_subtitle': 'Monitor compliance and generate quality reports',
        'welcome_message': 'Ensure equipment compliance and track quality metrics.',
        
        # New operational compliance data
        'overdue_calibrations': 3,  # Replace with real query later
        'overdue_maintenance': 2,   # Replace with real query later
        'unplanned_calibrations': 5,  # Replace with real query later
        'unplanned_maintenance': 8,   # Replace with real query later
        
        # Existing metrics
        'equipment_uptime': '96.8',
        'scheduled_completion': '94.2',
        'quality_score': '97.1',
        'cost_savings': '15.2',
    }
    return render(request, 'myapp/quality_dashboard.html', context) 

#Home page view
def home(request):
    return render(request, 'myapp/home.html')

#test veiw
def test(request):
    return render(request, 'myapp/test.html')

#Signup View

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        print("Form is valid:", form.is_valid())
        
        if form.is_valid():
            print("Cleaned data:", form.cleaned_data)
            
            try:
                # This Form will handle saving (it will create profile automatically)
                user = form.save()
                
                print(f"User created - Email: '{user.email}'")
                print(f"User created - First name: '{user.first_name}'")
                print(f"User created - Last name: '{user.last_name}'")
                print(f"Profile role: '{user.profile.role}'")  # Will show default role

                  # Check that profile exists and has no role
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.role = ''  # No role assigned for default users, role to be assigned by admin
                profile.save()
                print(f"Profile role: '{profile.role}'")
                
                # Get the username and password for authentication
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                
                # Authenticate and login the user
                authenticated_user = authenticate(username=username, password=raw_password)
                if authenticated_user is not None:
                    login(request, authenticated_user)
                    messages.success(request, f'Account created successfully for {username}! Your role will be assigned by an administrator.')
                    return redirect('dashboard')  # Changed from 'home' to 'dashboard'
                else:
                    messages.error(request, 'Account created but there was an error logging you in.')
                    
            except Exception as error:
                print(f"Error creating user: {error}")
                messages.error(request, f'Error creating account: {error}')
                
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()  # Changed from SignUpForm to CustomUserCreationForm
    
    return render(request, 'myapp/signup.html', {'form': form})

# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}")
                return redirect('dashboard')  # returns user to relevant dashboard
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'myapp/login_page.html', {"form": form,
                                                'page_title': 'login',
                                                })

# Logout view
def logout_view(request):
    if request.method== 'Post':
        logout(request)
        messages.success(request, "You have successfully logged out.")
        return redirect('myapp/home.html')  # Redirect to login page after logout
    else: 
        return redirect('home')


#Default dasboard for when no role has been assigned
@login_required
def default_dashboard(request):
    """Default dashboard for users without assigned roles"""
    try:
        user_role = request.user.profile.role
        # If user has a specific role, redirect to appropriate dashboard
        if user_role == 'administrator':
            return redirect('admin_dashboard')
        elif user_role == 'maintenance':
            return redirect('maintenance_dashboard')
        elif user_role == 'quality':
            return redirect('quality_dashboard')
    except UserProfile.DoesNotExist:
        # User has no profile, create one with default role
        UserProfile.objects.create(user=request.user, role='maintenance')
    
    # If we get here, user either has no role or default role. For security reasons, roles to be designated by admin or superuser
    context = {
        'user': request.user,
        'page_title': 'Welcome Dashboard',
    }
    return render(request, 'myapp/default_dashboard.html', context)

#Adding the ability to add Data to the Maintenance and Admin Views:
@login_required
def dashboard(request):
    """Dashboard showing overview of maintenance and calibration status"""
    today = timezone.now().date()
    two_weeks = today + timedelta(days=14)
    
    # Get counts for different statuses
    all_equipment = Equipment.objects.all()
    
    overdue_maintenance = []
    overdue_calibration = []
    due_soon = []
    
    for equipment in all_equipment:
        if equipment.is_maintenance_overdue:
            overdue_maintenance.append(equipment)
        if equipment.is_calibration_overdue:
            overdue_calibration.append(equipment)
            
        # Check if due soon (within 2 weeks)
        maintenance_due = equipment.next_maintenance_date
        calibration_due = equipment.next_calibration_date
        
        if maintenance_due and today <= maintenance_due <= two_weeks:
            if equipment not in due_soon:
                due_soon.append(equipment)
        if calibration_due and today <= calibration_due <= two_weeks:
            if equipment not in due_soon:
                due_soon.append(equipment)
    
    context = {
        'total_equipment': all_equipment.count(),
        'overdue_maintenance_count': len(overdue_maintenance),
        'overdue_calibration_count': len(overdue_calibration),
        'due_soon_count': len(due_soon),
        'overdue_maintenance': overdue_maintenance[:5],  # Show first 5
        'overdue_calibration': overdue_calibration[:5],  # Show first 5
        'due_soon': due_soon[:5],  # Show first 5
    }
    
    return render(request, 'equipment/dashboard.html', context)

@login_required
def equipment_list(request):
    """Display equipment list with filtering options"""
    # Get filter parameters
    status = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    machine_type = request.GET.get('machine_type', '')
    
    # Start with all equipment
    equipment_queryset = Equipment.objects.all()
    
    # Apply search filter
    if search:
        equipment_queryset = equipment_queryset.filter(
            Q(machine_id__icontains=search) |
            Q(machine_name__icontains=search) |
            Q(machine_location__icontains=search)
        )
    
    # Apply machine type filter
    if machine_type:
        equipment_queryset = equipment_queryset.filter(machine_type=machine_type)
    
    # Apply status filters
    today = timezone.now().date()
    two_weeks = today + timedelta(days=14)
    
    if status == 'overdue_maintenance':
        equipment_list = []
        for equipment in equipment_queryset:
            if equipment.is_maintenance_overdue:
                equipment_list.append(equipment)
        equipment_queryset = equipment_list
        
    elif status == 'overdue_calibration':
        equipment_list = []
        for equipment in equipment_queryset:
            if equipment.is_calibration_overdue:
                equipment_list.append(equipment)
        equipment_queryset = equipment_list
        
    elif status == 'due_soon':
        equipment_list = []
        for equipment in equipment_queryset:
            maintenance_due = equipment.next_maintenance_date
            calibration_due = equipment.next_calibration_date
            
            due_soon = False
            if maintenance_due and today <= maintenance_due <= two_weeks:
                due_soon = True
            if calibration_due and today <= calibration_due <= two_weeks:
                due_soon = True
                
            if due_soon:
                equipment_list.append(equipment)
        equipment_queryset = equipment_list
    
    # Pagination
    paginator = Paginator(equipment_queryset, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Create filter form
    filter_form = EquipmentFilterForm(initial={
        'search': search,
        'machine_type': machine_type,
        'status': status
    })
    
    context = {
        'page_obj': page_obj,
        'equipment_list': page_obj,
        'filter_form': filter_form,
        'status': status,
        'search': search,
        'machine_type': machine_type,
        'machine_types': MACHINE_TYPE_CHOICES,
        'total_count': len(equipment_queryset) if isinstance(equipment_queryset, list) else equipment_queryset.count(),
    }
    
    return render(request, 'equipment/equipment_list.html', context)

@login_required
def equipment_detail(request, machine_id):
    """Display detailed view of a specific equipment"""
    equipment = get_object_or_404(Equipment, machine_id=machine_id)
    
    context = {
        'equipment': equipment,
    }
    return render(request, 'equipment/equipment_detail.html', context)

@login_required
def equipment_create(request):
    """Create new equipment"""
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.created_by = request.user
            equipment.save()
            messages.success(request, f'Equipment {equipment.machine_id} created successfully!')
            return redirect('equipment_detail', machine_id=equipment.machine_id)
    else:
        form = EquipmentForm()
    
    return render(request, 'equipment/equipment_form.html', {
        'form': form,
        'title': 'Add New Equipment',
        'button_text': 'Create Equipment'
    })

@login_required
def equipment_update(request, machine_id):
    """Update existing equipment"""
    equipment = get_object_or_404(Equipment, machine_id=machine_id)
    
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Equipment {equipment.machine_id} updated successfully!')
            return redirect('equipment_detail', machine_id=equipment.machine_id)
    else:
        form = EquipmentForm(instance=equipment)
    
    return render(request, 'equipment/equipment_form.html', {
        'form': form,
        'equipment': equipment,
        'title': f'Update {equipment.machine_id}',
        'button_text': 'Update Equipment'
    })

@login_required
def equipment_delete(request, machine_id):
    """Delete equipment"""
    equipment = get_object_or_404(Equipment, machine_id=machine_id)
    
    if request.method == 'POST':
        equipment_id = equipment.machine_id
        equipment.delete()
        messages.success(request, f'Equipment {equipment_id} deleted successfully!')
        return redirect('equipment_list')
    
    return render(request, 'equipment/equipment_confirm_delete.html', {
        'equipment': equipment
    })

@login_required
def equipment_quick_update(request, machine_id):
    """Quick update for maintenance and calibration dates"""
    equipment = get_object_or_404(Equipment, machine_id=machine_id)
    
    if request.method == 'POST':
        form = QuickUpdateForm(request.POST, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Equipment {equipment.machine_id} dates updated successfully!')
            return redirect('equipment_detail', machine_id=equipment.machine_id)
    else:
        form = QuickUpdateForm(instance=equipment)
    
    return render(request, 'equipment/equipment_quick_update.html', {
        'form': form,
        'equipment': equipment
    })

@login_required
def equipment_api_status(request, machine_id):
    """API endpoint to get equipment status"""
    equipment = get_object_or_404(Equipment, machine_id=machine_id)
    
    data = {
        'machine_id': equipment.machine_id,
        'machine_name': equipment.machine_name,
        'next_calibration_date': equipment.next_calibration_date.isoformat() if equipment.next_calibration_date else None,
        'next_maintenance_date': equipment.next_maintenance_date.isoformat() if equipment.next_maintenance_date else None,
        'is_calibration_overdue': equipment.is_calibration_overdue,
        'is_maintenance_overdue': equipment.is_maintenance_overdue,
        'days_until_calibration': equipment.days_until_calibration,
        'days_until_maintenance': equipment.days_until_maintenance,
    }
    
    return JsonResponse(data)