from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .models import UserProfile, Equipment, MACHINE_TYPE_CHOICES  
from .forms import CustomUserCreationForm, EquipmentForm, EquipmentFilterForm, QuickUpdateForm, ProcedureCompleteForm
from datetime import datetime, timedelta
import logging
import json

# Add logging 
logger = logging.getLogger(__name__)

#  DECORATORS 
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

# HOME Page
def home(request):
    """
    Homepage view - displays landing page with login/signup options
    """
    return render(request, 'myapp/home.html')

#SIGNUP VIEW
def signup_view(request):
    """
    User registration view
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created successfully for {username}! Please log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'myapp/signup.html', {'form': form})

#LOGIN VIEW
def login_view(request):
    """
    User login view
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('dashboard')  # We'll create this later
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'myapp/login.html')

#LOGOUT VIEW
def logout_view(request):
    """
    User logout view
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def default_dashboard(request):
    """Default dashboard for users without a specific role"""
    context = {
        'user_role': 'User',
        'page_title': 'Dashboard',
        'page_subtitle': 'Welcome to the Maintenance & Calibration System',
        'welcome_message': 'Please contact your administrator to assign you a role.',
    }
    return render(request, 'myapp/default_dashboard.html', context)

# MAIN DASHBOARD 
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
        return redirect('default_dashboard')

# ROLE-SPECIFIC DASHBOARDS
#@login_required
#@role_required(['administrator'])
#def equipment_create(request):
    #"""Create new equipment (Administrator or Maintenance only)"""
    #if request.method == 'POST':
       # form = EquipmentForm(request.POST)
       # if form.is_valid():
            #equipment = form.save()
            #messages.success(request, f'Equipment "{equipment.machine_name}" created successfully!')
            #return redirect('equipment_detail', pk=equipment.pk)
    #else:
        #form = EquipmentForm()
    
    #context = {
        #'form': form,
        #'form_title': 'Add New Equipment',
        #'submit_text': 'Create Equipment',
    #}
    
    #return render(request, 'myapp/equipment_form.html', context)

#def equipment_update(request, pk):
    #"""Edit existing equipment (Administrator or Maintenance only)"""
    #equipment = get_object_or_404(Equipment, pk=pk)
    
    #if request.method == 'POST':
        #form = EquipmentForm(request.POST, instance=equipment)
        #if form.is_valid():
            #equipment = form.save()
            #messages.success(request, f'Equipment "{equipment.machine_name}" updated successfully!')
            #return redirect('equipment_detail', pk=equipment.pk)
    #else:
        #form = EquipmentForm(instance=equipment)
    
    #context = {
        #'form': form,
        #'equipment': equipment,
        #'form_title': f'Edit Equipment: {equipment.machine_name}',
        #'submit_text': 'Update Equipment',
    #}
    
    #return render(request, 'myapp/equipment_form.html', context)

#def equipment_delete(request, pk):
   # """Delete equipment (Administrator only)"""
   # equipment = get_object_or_404(Equipment, pk=pk)
    
    #if request.method == 'POST':
       # machine_name = equipment.machine_name
       # equipment.delete()
       # messages.success(request, f'Equipment "{machine_name}" has been deleted.')
       # return redirect('myapp/equipment/equipment_list')
    
   # context = {
        #'equipment': equipment,
   # }
    
   # return render(request, 'myapp/equipment_confirm_delete.html', context)

def admin_dashboard(request):
    # Handle search functionality
    search = request.GET.get('search', '').strip()
    machine_type = request.GET.get('machine_type', '')
    status = request.GET.get('status', 'all')
    
    # Start with all equipment
    equipment_queryset = Equipment.objects.all()
    
    # Apply search filter if provided
    if search:
        equipment_queryset = equipment_queryset.filter(
            Q(machine_id__icontains=search) |
            Q(machine_name__icontains=search) |
            Q(machine_location__icontains=search)
        )
        print(f"Admin Dashboard - Search term: '{search}'")  # Debug line
        print(f"Admin Dashboard - Results found: {equipment_queryset.count()}")  # Debug line
    
    # Apply machine type filter
    if machine_type:
        equipment_queryset = equipment_queryset.filter(machine_type=machine_type)
    
    # Calculate status-based equipment lists
    today = timezone.now().date()
    two_weeks = today + timedelta(days=14)
    
    overdue_maintenance = []
    overdue_calibration = []
    due_soon = []
    filtered_equipment = []
    
    for equipment in equipment_queryset:
        # Add to filtered list for display
        filtered_equipment.append(equipment)
        
        # Check maintenance status
        if equipment.is_maintenance_overdue:
            overdue_maintenance.append(equipment)
        
        # Check calibration status    
        if equipment.is_calibration_overdue:
            overdue_calibration.append(equipment)
            
        # Check if due soon
        maintenance_due = equipment.next_maintenance_date
        calibration_due = equipment.next_calibration_date
        
        if maintenance_due and today <= maintenance_due <= two_weeks:
            if equipment not in due_soon:
                due_soon.append(equipment)
        if calibration_due and today <= calibration_due <= two_weeks:
            if equipment not in due_soon:
                due_soon.append(equipment)
    
    # Apply status filter
    if status == 'overdue_maintenance':
        filtered_equipment = overdue_maintenance
    elif status == 'overdue_calibration':
        filtered_equipment = overdue_calibration
    elif status == 'due_soon':
        filtered_equipment = due_soon
    
    # Create filter form instance
    from .forms import EquipmentFilterForm
    filter_form = EquipmentFilterForm(initial={
        'search': search,
        'machine_type': machine_type,
        'status': status
    })
    
    context = {
        'user_role': 'Administrator',
        'page_title': 'Administrator Dashboard',
        'page_subtitle': 'Complete system administration and management',
        'welcome_message': 'You have full administrative access to the system.',
        'total_users': UserProfile.objects.count(),
        'total_equipment': Equipment.objects.count(),
        'filtered_equipment_count': len(filtered_equipment),
        'overdue_maintenance_count': len(overdue_maintenance),
        'overdue_calibration_count': len(overdue_calibration),
        'due_soon_count': len(due_soon),
        'overdue_maintenance': overdue_maintenance[:3],  # Show first 3
        'overdue_calibration': overdue_calibration[:3],  # Show first 3
        'due_soon': due_soon[:3],  # Show first 3
        # Search-related context
        'search': search,
        'filter_form': filter_form,
        'filtered_equipment': filtered_equipment,
        'has_filters': bool(search or machine_type or status != 'all'),
    }
    return render(request, 'myapp/admin_dashboard.html', context)


@login_required
def maintenance_dashboard(request):

     # Check if user has maintenance role
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'maintenance':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
     # Handle search functionality  
    search = request.GET.get('search', '').strip()
    machine_type = request.GET.get('machine_type', '')
    status = request.GET.get('status', 'all')

    # Start with all equipment
    equipment_queryset = Equipment.objects.all()
    
    # Apply search filter if provided
    if search:
        equipment_queryset = equipment_queryset.filter(
            Q(machine_id__icontains=search) |
            Q(machine_name__icontains=search) |
            Q(machine_location__icontains=search)
        )
        print(f"Maintenance Dashboard - Search term: '{search}'")  # Debug line
        print(f"Maintenance Dashboard - Results found: {equipment_queryset.count()}")  # Debug line
    
    # Apply machine type filter
    if machine_type:
        equipment_queryset = equipment_queryset.filter(machine_type=machine_type)
    
    # Calculate status-based equipment lists
    today = timezone.now().date()
    two_weeks = today + timedelta(days=14)
    all_equipment = Equipment.objects.all()
    due_calibration = []
    due_maintenance = []
    
    overdue_maintenance = []
    due_soon_maintenance = []
    overdue_calibration = []
    due_soon_calibration = []
    filtered_equipment = []
    
    for equipment in equipment_queryset:
        # Add to filtered list for display
        filtered_equipment.append(equipment)
        
        # Check maintenance status
        if equipment.is_maintenance_overdue:
            overdue_maintenance.append(equipment)
        else:
            maintenance_due = equipment.next_maintenance_date
            if maintenance_due and today <= maintenance_due <= two_weeks:
                due_soon_maintenance.append(equipment)
        
        # Check calibration status
        if equipment.is_calibration_overdue:
            overdue_calibration.append(equipment)
        else:
            calibration_due = equipment.next_calibration_date
            if calibration_due and today <= calibration_due <= two_weeks:
                due_soon_calibration.append(equipment)
    
    # Apply status filter
    if status == 'overdue_maintenance':
        filtered_equipment = overdue_maintenance
    elif status == 'overdue_calibration':
        filtered_equipment = overdue_calibration
    elif status == 'due_soon':
        # Combine both due soon lists
        filtered_equipment = list(set(due_soon_maintenance + due_soon_calibration))
    
    # Create filter form instance
    from .forms import EquipmentFilterForm
    filter_form = EquipmentFilterForm(initial={
        'search': search,
        'machine_type': machine_type,
        'status': status     
    })

    for equipment in all_equipment:
        # Check calibration
        next_cal = equipment.next_calibration_date
        if next_cal and next_cal <= two_weeks:
            due_calibration.append(equipment)
        
        # Check maintenance
        next_maint = equipment.next_maintenance_date
        if next_maint and next_maint <= two_weeks:
            due_maintenance.append(equipment)
    
    context = {
        'user_role': 'Maintenance/Calibration User',
        'page_title': 'Maintenance Dashboard',
        'page_subtitle': 'Track and complete maintenance and calibration tasks',
        'welcome_message': 'Review your assigned tasks and equipment due for maintenance.',
        'total_equipment': Equipment.objects.count(),
        'filtered_equipment_count': len(filtered_equipment),
        'overdue_maintenance': overdue_maintenance,
        'due_soon_maintenance': due_soon_maintenance,
        'overdue_calibration': overdue_calibration,
        'due_soon_calibration': due_soon_calibration,
        'overdue_maintenance_count': len(overdue_maintenance),
        'overdue_calibration_count': len(overdue_calibration),
        'due_soon_maintenance_count': len(due_soon_maintenance),
        'due_soon_calibration_count': len(due_soon_calibration),
        # Search-related context
        'search': search,
        'filter_form': filter_form,
        'filtered_equipment': filtered_equipment,
        'has_filters': bool(search or machine_type or status != 'all'),
        'due_calibration': due_calibration,
        'due_maintenance': due_maintenance,
        'total_equipment': all_equipment.count(),
        'today': today,
    }
    return render(request, 'myapp/maintenance_dashboard.html', context)
    
@login_required
@role_required(['quality'])
def quality_dashboard(request):
    """Quality Engineer Dashboard - Monitor compliance and generate reports"""
    
    # Handle search functionality  
    search = request.GET.get('search', '').strip()
    machine_type = request.GET.get('machine_type', '')
    status = request.GET.get('status', 'all')
    
    # Start with all equipment
    equipment_queryset = Equipment.objects.all()
    
    # Apply search filter if provided
    if search:
        equipment_queryset = equipment_queryset.filter(
            Q(machine_id__icontains=search) |
            Q(machine_name__icontains=search) |
            Q(machine_location__icontains=search)
        )
        print(f"Quality Dashboard - Search term: '{search}'")  # Debug line
        print(f"Quality Dashboard - Results found: {equipment_queryset.count()}")  # Debug line
    
    # Apply machine type filter
    if machine_type:
        equipment_queryset = equipment_queryset.filter(machine_type=machine_type)
    
    # Calculate status-based equipment lists
    today = timezone.now().date()
    two_weeks = today + timedelta(days=14)
    
    overdue_maintenance = []
    overdue_calibration = []
    due_soon = []
    compliant_equipment = []
    filtered_equipment = []
    
    for equipment in equipment_queryset:
        # Add to filtered list for display
        filtered_equipment.append(equipment)
        
        is_overdue = False
        
        # Check maintenance status
        if equipment.is_maintenance_overdue:
            overdue_maintenance.append(equipment)
            is_overdue = True
        
        # Check calibration status    
        if equipment.is_calibration_overdue:
            overdue_calibration.append(equipment)
            is_overdue = True
            
        # Check if due soon
        maintenance_due = equipment.next_maintenance_date
        calibration_due = equipment.next_calibration_date
        
        if maintenance_due and today <= maintenance_due <= two_weeks:
            if equipment not in due_soon:
                due_soon.append(equipment)
        if calibration_due and today <= calibration_due <= two_weeks:
            if equipment not in due_soon:
                due_soon.append(equipment)
        
        # Track compliant equipment (not overdue and not due soon)
        if not is_overdue and equipment not in due_soon:
            compliant_equipment.append(equipment)
    
    # Apply status filter
    if status == 'overdue_maintenance':
        filtered_equipment = overdue_maintenance
    elif status == 'overdue_calibration':
        filtered_equipment = overdue_calibration
    elif status == 'due_soon':
        filtered_equipment = due_soon
    elif status == 'compliant':
        filtered_equipment = compliant_equipment
    
    # Calculate compliance percentage
    total_equipment = Equipment.objects.count()
    compliant_count = len(compliant_equipment)
    compliance_percentage = (compliant_count / total_equipment * 100) if total_equipment > 0 else 0
    
    # Create filter form instance
    from .forms import EquipmentFilterForm
    filter_form = EquipmentFilterForm(initial={
        'search': search,
        'machine_type': machine_type,
        'status': status
    })
    
    context = {
        'user_role': 'Quality Engineer',
        'page_title': 'Quality Dashboard',
        'page_subtitle': 'Monitor compliance and ensure all procedures are up to date',
        'welcome_message': 'Review equipment compliance and generate quality reports.',
        'total_equipment': total_equipment,
        'filtered_equipment_count': len(filtered_equipment),
        'overdue_maintenance_count': len(overdue_maintenance),
        'overdue_calibration_count': len(overdue_calibration),
        'due_soon_count': len(due_soon),
        'compliant_count': compliant_count,
        'compliance_percentage': round(compliance_percentage, 1),
        'overdue_maintenance': overdue_maintenance[:5],  # Show first 5
        'overdue_calibration': overdue_calibration[:5],  # Show first 5
        'due_soon': due_soon[:5],  # Show first 5
        # Search-related context
        'search': search,
        'filter_form': filter_form,
        'filtered_equipment': filtered_equipment,
        'has_filters': bool(search or machine_type or status != 'all'),
    }
    return render(request, 'myapp/quality_dashboard.html', context)

#Equipment List View
@login_required
def equipment_list(request):
    """Display list of all equipment with search and filter capabilities"""
    
    # Handle search and filters
    search = request.GET.get('search', '').strip()
    machine_type = request.GET.get('machine_type', '')
    status = request.GET.get('status', 'all')
    
    # Start with all equipment
    equipment_queryset = Equipment.objects.all().order_by('machine_id')
    
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
    
    # Calculate status for filtering
    today = timezone.now().date()
    two_weeks = today + timedelta(days=14)
    
    filtered_equipment = []
    
    for equipment in equipment_queryset:
        # Determine equipment status
        equipment.status_display = 'Compliant'
        equipment.status_class = 'compliant'
        
        if equipment.is_maintenance_overdue or equipment.is_calibration_overdue:
            equipment.status_display = 'Overdue'
            equipment.status_class = 'overdue'
        else:
            # Check if due soon
            maintenance_due = equipment.next_maintenance_date
            calibration_due = equipment.next_calibration_date
            
            if (maintenance_due and today <= maintenance_due <= two_weeks) or \
               (calibration_due and today <= calibration_due <= two_weeks):
                equipment.status_display = 'Due Soon'
                equipment.status_class = 'due-soon'
        
        # Apply status filter
        if status == 'all':
            filtered_equipment.append(equipment)
        elif status == 'overdue' and equipment.status_class == 'overdue':
            filtered_equipment.append(equipment)
        elif status == 'due_soon' and equipment.status_class == 'due-soon':
            filtered_equipment.append(equipment)
        elif status == 'compliant' and equipment.status_class == 'compliant':
            filtered_equipment.append(equipment)
    
    # Pagination
    paginator = Paginator(filtered_equipment, 10)  # Show 10 equipment per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Create filter form
    from .forms import EquipmentFilterForm
    filter_form = EquipmentFilterForm(initial={
        'search': search,
        'machine_type': machine_type,
        'status': status
    })
    
    context = {
        'page_obj': page_obj,
        'equipment_list': filtered_equipment,
        'total_equipment': len(filtered_equipment),
        'filter_form': filter_form,
        'search': search,
        'machine_type': machine_type,
        'status': status,
        'has_filters': bool(search or machine_type or status != 'all'),
    }
    
    return render(request, 'myapp/equipment/equipment_list.html', context)

@login_required
@login_required
def equipment_detail(request, machine_id):
    """Display detailed information about a specific equipment"""
    equipment = get_object_or_404(Equipment, machine_id=machine_id)
    
    # Calculate status
    today = timezone.now().date()
    two_weeks = today + timedelta(days=14)
    
    status_info = {
        'maintenance_status': 'Up to date',
        'maintenance_class': 'compliant',
        'calibration_status': 'Up to date',
        'calibration_class': 'compliant',
    }
    
    # Check maintenance status
    if equipment.is_maintenance_overdue:
        status_info['maintenance_status'] = 'Overdue'
        status_info['maintenance_class'] = 'overdue'
    elif equipment.next_maintenance_date and today <= equipment.next_maintenance_date <= two_weeks:
        status_info['maintenance_status'] = 'Due Soon'
        status_info['maintenance_class'] = 'due-soon'
    
    # Check calibration status
    if equipment.is_calibration_overdue:
        status_info['calibration_status'] = 'Overdue'
        status_info['calibration_class'] = 'overdue'
    elif equipment.next_calibration_date and today <= equipment.next_calibration_date <= two_weeks:
        status_info['calibration_status'] = 'Due Soon'
        status_info['calibration_class'] = 'due-soon'
    
    context = {
        'equipment': equipment,
        'status_info': status_info,
    }
    
    return render(request, 'myapp/equipment_detail.html', context)

@login_required
@role_required(['administrator', 'maintenance'])
def mark_task_complete(request, pk):
    """Mark maintenance or calibration task as complete and update dates"""
    equipment = get_object_or_404(Equipment, pk=pk)
    
    if request.method == 'POST':
        task_type = request.POST.get('task_type')
        completion_date = request.POST.get('completion_date')
        is_scheduled = request.POST.get('is_scheduled') == 'on'
        notes = request.POST.get('notes', '')
        
        # Convert date string to date object
        try:
            completion_date_obj = datetime.strptime(completion_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            completion_date_obj = timezone.now().date()
        
        if task_type == 'maintenance':
            equipment.last_maintenance_date = completion_date_obj
            task_name = 'Maintenance'
            messages.success(
                request, 
                f'Maintenance task completed for "{equipment.machine_name}". Next maintenance due: {equipment.next_maintenance_date}'
            )
        elif task_type == 'calibration':
            equipment.last_calibration_date = completion_date_obj
            task_name = 'Calibration'
            messages.success(
                request, 
                f'Calibration task completed for "{equipment.machine_name}". Next calibration due: {equipment.next_calibration_date}'
            )
        else:
            messages.error(request, 'Invalid task type.')
            return redirect('equipment_detail', pk=pk)
        
        equipment.save()
        
        # Log the completion (optional - for audit trail)
        logger.info(
            f"{task_name} completed for {equipment.machine_name} (ID: {equipment.machine_id}) "
            f"by {request.user.username} on {completion_date_obj}. "
            f"Scheduled: {is_scheduled}. Notes: {notes}"
        )
        
        return redirect('equipment_detail', pk=pk)
    
    # GET request - show the form
    context = {
        'equipment': equipment,
        'today': timezone.now().date(),
    }
    
    return render(request, 'myapp/mark_task_complete.html', context)

@login_required
@role_required(['administrator', 'maintenance'])
@require_POST
def quick_task_complete(request, pk):
    """Quick task completion via AJAX or POST"""
    equipment = get_object_or_404(Equipment, pk=pk)
    task_type = request.POST.get('task_type')
    
    today = timezone.now().date()
    
    if task_type == 'maintenance':
        equipment.last_maintenance_date = today
        task_name = 'Maintenance'
    elif task_type == 'calibration':
        equipment.last_calibration_date = today
        task_name = 'Calibration'
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Invalid task type'})
        messages.error(request, 'Invalid task type.')
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    
    equipment.save()
    
    # Log the completion
    logger.info(
        f"{task_name} quick-completed for {equipment.machine_name} "
        f"by {request.user.username}"
    )
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{task_name} completed successfully',
            'next_date': equipment.next_maintenance_date if task_type == 'maintenance' else equipment.next_calibration_date
        })
    
    messages.success(request, f'{task_name} completed for "{equipment.machine_name}"')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def equipment_api_status(request, pk):
    """API endpoint to get equipment status in JSON format"""
    try:
        equipment = get_object_or_404(Equipment, pk=pk)
        
        today = timezone.now().date()
        two_weeks = today + timedelta(days=14)
        
        # Calculate maintenance status
        maintenance_status = 'compliant'
        if equipment.is_maintenance_overdue:
            maintenance_status = 'overdue'
        elif equipment.next_maintenance_date and today <= equipment.next_maintenance_date <= two_weeks:
            maintenance_status = 'due_soon'
        
        # Calculate calibration status
        calibration_status = 'compliant'
        if equipment.is_calibration_overdue:
            calibration_status = 'overdue'
        elif equipment.next_calibration_date and today <= equipment.next_calibration_date <= two_weeks:
            calibration_status = 'due_soon'
        
        # Prepare response data
        data = {
            'success': True,
            'equipment': {
                'id': equipment.pk,
                'machine_id': equipment.machine_id,
                'machine_name': equipment.machine_name,
                'machine_type': equipment.machine_type,
                'machine_location': equipment.machine_location,
                'last_maintenance_date': equipment.last_maintenance_date.strftime('%Y-%m-%d') if equipment.last_maintenance_date else None,
                'next_maintenance_date': equipment.next_maintenance_date.strftime('%Y-%m-%d') if equipment.next_maintenance_date else None,
                'last_calibration_date': equipment.last_calibration_date.strftime('%Y-%m-%d') if equipment.last_calibration_date else None,
                'next_calibration_date': equipment.next_calibration_date.strftime('%Y-%m-%d') if equipment.next_calibration_date else None,
                'maintenance_interval_days': equipment.maintenance_interval_days,
                'calibration_interval_days': equipment.calibration_interval_days,
                'maintenance_status': maintenance_status,
                'calibration_status': calibration_status,
                'is_maintenance_overdue': equipment.is_maintenance_overdue,
                'is_calibration_overdue': equipment.is_calibration_overdue,
            }
        }
        
        return JsonResponse(data)
        
    except Equipment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Equipment not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in equipment_api_status: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred'
        }, status=500)
    

@login_required
def equipment_api_stats(request):
    """API endpoint to get overall equipment statistics"""
    try:
        equipment_list = Equipment.objects.all()
        today = timezone.now().date()
        two_weeks = today + timedelta(days=14)
        
        stats = {
            'total_equipment': equipment_list.count(),
            'overdue_maintenance': 0,
            'overdue_calibration': 0,
            'due_soon_maintenance': 0,
            'due_soon_calibration': 0,
            'compliant': 0,
        }
        
        for equipment in equipment_list:
            is_overdue = False
            is_due_soon = False
            
            # Check maintenance
            if equipment.is_maintenance_overdue:
                stats['overdue_maintenance'] += 1
                is_overdue = True
            elif equipment.next_maintenance_date and today <= equipment.next_maintenance_date <= two_weeks:
                stats['due_soon_maintenance'] += 1
                is_due_soon = True
            
            # Check calibration
            if equipment.is_calibration_overdue:
                stats['overdue_calibration'] += 1
                is_overdue = True
            elif equipment.next_calibration_date and today <= equipment.next_calibration_date <= two_weeks:
                stats['due_soon_calibration'] += 1
                is_due_soon = True
            
            # Count compliant equipment
            if not is_overdue and not is_due_soon:
                stats['compliant'] += 1
        
        # Calculate compliance percentage
        stats['compliance_percentage'] = round(
            (stats['compliant'] / stats['total_equipment'] * 100) if stats['total_equipment'] > 0 else 0,
            1
        )
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error in equipment_api_stats: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred'
        }, status=500)
    
    """API endpoint to get equipment status"""
    try:
        equipment = get_object_or_404(Equipment, machine_id=machine_id)
        
        data = {
            'machine_id': equipment.machine_id,
            'machine_name': equipment.machine_name,
            'maintenance_status': equipment.maintenance_status,
            'calibration_status': equipment.calibration_status,
            'is_maintenance_overdue': equipment.is_maintenance_overdue,
            'is_calibration_overdue': equipment.is_calibration_overdue,
            'next_maintenance_date': equipment.next_maintenance_date.isoformat() if equipment.next_maintenance_date else None,
            'next_calibration_date': equipment.next_calibration_date.isoformat() if equipment.next_calibration_date else None,
        }
        
        return JsonResponse(data)
        
    except Equipment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Equipment not found'
        }, status=404)
    
    # API VIEWS
@login_required
def equipment_api_status(request, pk):
    """API endpoint to get equipment status in JSON format"""
    try:
        equipment = get_object_or_404(Equipment, pk=pk)
        
        today = timezone.now().date()
        two_weeks = today + timedelta(days=14)
        
        # Calculate maintenance status
        maintenance_status = 'compliant'
        if equipment.is_maintenance_overdue:
            maintenance_status = 'overdue'
        elif equipment.next_maintenance_date and today <= equipment.next_maintenance_date <= two_weeks:
            maintenance_status = 'due_soon'
        
        # Calculate calibration status
        calibration_status = 'compliant'
        if equipment.is_calibration_overdue:
            calibration_status = 'overdue'
        elif equipment.next_calibration_date and today <= equipment.next_calibration_date <= two_weeks:
            calibration_status = 'due_soon'
        
        # Prepare response data
        data = {
            'success': True,
            'equipment': {
                'id': equipment.pk,
                'machine_id': equipment.machine_id,
                'machine_name': equipment.machine_name,
                'machine_type': equipment.machine_type,
                'machine_location': equipment.machine_location,
                'last_maintenance_date': equipment.last_maintenance_date.strftime('%Y-%m-%d') if equipment.last_maintenance_date else None,
                'next_maintenance_date': equipment.next_maintenance_date.strftime('%Y-%m-%d') if equipment.next_maintenance_date else None,
                'last_calibration_date': equipment.last_calibration_date.strftime('%Y-%m-%d') if equipment.last_calibration_date else None,
                'next_calibration_date': equipment.next_calibration_date.strftime('%Y-%m-%d') if equipment.next_calibration_date else None,
                'maintenance_interval_days': equipment.maintenance_interval_days,
                'calibration_interval_days': equipment.calibration_interval_days,
                'maintenance_status': maintenance_status,
                'calibration_status': calibration_status,
                'is_maintenance_overdue': equipment.is_maintenance_overdue,
                'is_calibration_overdue': equipment.is_calibration_overdue,
            }
        }
        
        return JsonResponse(data)
        
    except Equipment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Equipment not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error in equipment_api_status: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred'
        }, status=500)


@login_required
def equipment_api_list(request):
    """API endpoint to get list of all equipment with their status"""
    try:
        equipment_list = Equipment.objects.all()
        today = timezone.now().date()
        two_weeks = today + timedelta(days=14)
        
        data = []
        for equipment in equipment_list:
            # Calculate statuses
            maintenance_status = 'compliant'
            if equipment.is_maintenance_overdue:
                maintenance_status = 'overdue'
            elif equipment.next_maintenance_date and today <= equipment.next_maintenance_date <= two_weeks:
                maintenance_status = 'due_soon'
            
            calibration_status = 'compliant'
            if equipment.is_calibration_overdue:
                calibration_status = 'overdue'
            elif equipment.next_calibration_date and today <= equipment.next_calibration_date <= two_weeks:
                calibration_status = 'due_soon'
            
            data.append({
                'id': equipment.pk,
                'machine_id': equipment.machine_id,
                'machine_name': equipment.machine_name,
                'machine_type': equipment.machine_type,
                'machine_location': equipment.machine_location,
                'maintenance_status': maintenance_status,
                'calibration_status': calibration_status,
                'next_maintenance_date': equipment.next_maintenance_date.strftime('%Y-%m-%d') if equipment.next_maintenance_date else None,
                'next_calibration_date': equipment.next_calibration_date.strftime('%Y-%m-%d') if equipment.next_calibration_date else None,
            })
        
        return JsonResponse({
            'success': True,
            'count': len(data),
            'equipment': data
        })
        
    except Exception as e:
        logger.error(f"Error in equipment_api_list: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred'
        }, status=500)
    
@login_required
def maintenance_add_equipment(request):
    """Allow maintenance users to add new equipment"""
    
    # Check permissions
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'maintenance':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Equipment {form.cleaned_data['machine_id']} added successfully!")
            return redirect('maintenance_dashboard')
    else:
        form = EquipmentForm()
    
    return render(request, 'myapp/maintenance_add_equipment.html', {'form': form})   

@login_required
def maintenance_delete_equipment(request, machine_id):
    """Allow maintenance users to delete equipment"""
    
    # Check permissions
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'maintenance':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    equipment = get_object_or_404(Equipment, machine_id=machine_id)
    
    if request.method == 'POST':
        equipment_name = equipment.machine_name
        equipment.delete()
        messages.success(request, f"Equipment '{equipment_name}' has been removed from the system.")
        return redirect('maintenance_dashboard')
    
    return render(request, 'myapp/maintenance_confirm_delete.html', {'equipment': equipment})

@login_required
def maintenance_complete_procedure(request, machine_id):
    """Mark a calibration or maintenance procedure as complete"""
    
    # Check permissions
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'maintenance':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    equipment = get_object_or_404(Equipment, machine_id=machine_id)
    
    if request.method == 'POST':
        form = ProcedureCompleteForm(request.POST)
        if form.is_valid():
            procedure_type = form.cleaned_data['procedure_type']
            completion_date = form.cleaned_data['completion_date']
            
            # Update the appropriate date field
            if procedure_type == 'calibration':
                equipment.last_calibration_date = completion_date
                message = f"Calibration completed for {equipment.machine_name}"
            else:  # maintenance
                equipment.last_maintenance_date = completion_date
                message = f"Maintenance completed for {equipment.machine_name}"
            
            equipment.save()
            messages.success(request, message)
            return redirect('maintenance_dashboard')
    else:
        form = ProcedureCompleteForm()
    
    context = {
        'form': form,
        'equipment': equipment,
    }
    
    return render(request, 'myapp/maintenance_complete_procedure.html', context)
@login_required
def admin_add_equipment(request):
    """Allow administrators to add new equipment"""
    
    # Universal profile check
    user_profile = None
    if hasattr(request.user, 'profile'):
        user_profile = request.user.profile
    elif hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile
    
    if not user_profile or user_profile.role != 'administrator':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save()
            messages.success(request, f"Equipment {equipment.machine_id} - {equipment.machine_name} added successfully!")
            return redirect('admin_dashboard')
    else:
        form = EquipmentForm()
    
    context = {
        'form': form,
        'page_title': 'Add New Equipment',
        'user_role': 'Administrator',
    }
    return render(request, 'myapp/admin_add_equipment.html', context)


@login_required
def admin_delete_equipment(request, machine_id):
    """Allow administrators to delete equipment"""
    
    # Universal profile check
    user_profile = None
    if hasattr(request.user, 'profile'):
        user_profile = request.user.profile
    elif hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile
    
    if not user_profile or user_profile.role != 'administrator':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    equipment = get_object_or_404(Equipment, machine_id=machine_id)
    
    if request.method == 'POST':
        equipment_name = equipment.machine_name
        equipment.delete()
        messages.success(request, f"Equipment '{equipment_name}' has been removed from the system.")
        return redirect('admin_dashboard')
    
    context = {
        'equipment': equipment,
        'user_role': 'Administrator',
    }
    return render(request, 'myapp/admin_confirm_delete.html', context)


@login_required
def admin_edit_equipment(request, machine_id):
    """Allow administrators to edit equipment"""
    
    # Universal profile check
    user_profile = None
    if hasattr(request.user, 'profile'):
        user_profile = request.user.profile
    elif hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile
    
    if not user_profile or user_profile.role != 'administrator':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    equipment = get_object_or_404(Equipment, machine_id=machine_id)
    
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            equipment = form.save()
            messages.success(request, f"Equipment {equipment.machine_name} updated successfully!")
            return redirect('admin_dashboard')
    else:
        form = EquipmentForm(instance=equipment)
    
    context = {
        'form': form,
        'equipment': equipment,
        'page_title': f'Edit Equipment: {equipment.machine_name}',
        'user_role': 'Administrator',
    }
    return render(request, 'myapp/admin_edit_equipment.html', context)


@login_required
def admin_complete_procedure(request, machine_id):
    """Allow administrators to mark procedures complete"""
    
    # Universal profile check
    user_profile = None
    if hasattr(request.user, 'profile'):
        user_profile = request.user.profile
    elif hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile
    
    if not user_profile or user_profile.role != 'administrator':
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    equipment = get_object_or_404(Equipment, machine_id=machine_id)
    
    if request.method == 'POST':
        form = ProcedureCompleteForm(request.POST)
        if form.is_valid():
            procedure_type = form.cleaned_data['procedure_type']
            completion_date = form.cleaned_data['completion_date']
            
            # Update the appropriate date field
            if procedure_type == 'calibration':
                equipment.last_calibration_date = completion_date
                message = f"Calibration completed for {equipment.machine_name}"
            else:  # maintenance
                equipment.last_maintenance_date = completion_date
                message = f"Maintenance completed for {equipment.machine_name}"
            
            equipment.save()
            messages.success(request, message)
            return redirect('admin_dashboard')
    else:
        form = ProcedureCompleteForm()
    
    context = {
        'form': form,
        'equipment': equipment,
        'user_role': 'Administrator',
    }
    return render(request, 'myapp/admin_complete_procedure.html', context)