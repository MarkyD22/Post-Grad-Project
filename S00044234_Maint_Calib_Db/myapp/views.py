from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
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
        user_role = request.user.profile.role
        
        if user_role == 'administrator':
            return redirect('admin_dashboard')
        elif user_role == 'maintenance':
            return redirect('maintenance_dashboard')
        elif user_role == 'quality':
            return redirect('quality_dashboard')
        else:
            messages.warning(request, "Your role hasn't been assigned yet. Please contact an administrator.")
            return render(request, 'myapp/pending_role.html')
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
    }
    return render(request, 'myapp/admin_dashboard.html', context)

#Maintenance Dashboard
@login_required
@role_required(['maintenance'])
def maintenance_dashboard(request):
    context = {
        'user_role': 'Maintenance/Calibration User',
        'page_title': 'Maintenance Dashboard',
    }
    return render(request, 'myapp/maintenance_dashboard.html', context)

#Quality Dashboard
@login_required
@role_required(['quality'])
def quality_dashboard(request):
    context = {
        'user_role': 'Quality Engineer',
        'page_title': 'Quality Dashboard',
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
                # Let the form handle saving (it will create profile automatically)
                user = form.save()
                
                print(f"User created - Email: '{user.email}'")
                print(f"User created - First name: '{user.first_name}'")
                print(f"User created - Last name: '{user.last_name}'")
                print(f"Profile role: '{user.profile.role}'")  # Will show default role
                
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
                return redirect('home')  # Change to your home page
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'myapp/login_page.html', {"form": form,
                                                'page_title': 'login',
                                                })

# Logout view
def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('myapp/login_page.html')  # Redirect to login page after logout
