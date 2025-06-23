from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import UserProfile
from .forms import CustomUserCreationForm  # Only import forms that exist
import logging

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
                # Form will handle saving (it will create profile automatically)
                user = form.save()
                
                print(f"User created - Email: '{user.email}'")
                print(f"User created - First name: '{user.first_name}'")
                print(f"User created - Last name: '{user.last_name}'")
                print(f"Profile role: '{user.profile.role}'")  # Will show default role

                  # Make sure profile exists and has no role
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
    
    # If we get here, user either has no role or default role
    context = {
        'user': request.user,
        'page_title': 'Welcome Dashboard',
    }
    return render(request, 'myapp/default_dashboard.html', context)
