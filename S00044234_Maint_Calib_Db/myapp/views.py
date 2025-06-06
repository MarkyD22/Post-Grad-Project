from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import Item
from .forms import ItemForm, SignUpForm
import logging

#Add logging
logger=logging.getLogger(__name__)

#Apply the decorator to the following views
@login_required

def item_list(request):
    items = Item.objects.all()
    return render(request, 'myapp/item_list.html', {'items': items})

def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('item_list')
    else:
        form = ItemForm()
    return render(request, 'myapp/add_item.html', {'form': form})

#Home page view
def home(request):
    return render(request, 'myapp/home.html')

#test veiw
def test(request):
    return render(request, 'myapp/test.html')

#Signup View
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import SignUpForm

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        
        print("Form is valid:", form.is_valid())
        
        if form.is_valid():
            print("Cleaned data:", form.cleaned_data)
            
            try:
                # Save the user but don't commit yet
                user = form.save(commit=False)
                
                # Manually set the additional fields
                user.email = form.cleaned_data['email']
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                
                # Now save to database
                user.save()
                
                print(f"Manually saved - Email: '{user.email}'")
                print(f"Manually saved - First name: '{user.first_name}'")
                print(f"Manually saved - Last name: '{user.last_name}'")
                
                # Get the username and password for authentication
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                
                # Authenticate and login the user
                authenticated_user = authenticate(username=username, password=raw_password)
                if authenticated_user is not None:
                    login(request, authenticated_user)
                    messages.success(request, f'Account created successfully for {username}!')
                    return redirect('home')
                else:
                    messages.error(request, 'Account created but there was an error logging you in.')
                    
            except Exception as error:
                print(f"Error creating user: {error}")
                messages.error(request, f'Error creating account: {error}')
                
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignUpForm()
    
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
