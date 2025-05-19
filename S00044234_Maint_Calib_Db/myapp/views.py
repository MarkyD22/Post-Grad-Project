from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import Item
from .forms import ItemForm, SignUpForm

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

# Signup views
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            messages.success(request, "New account created: {username}")
            return redirect('home')
        else:
            messages.error(request, "Account creation failed")
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
                return redirect('item_list')  # Change to your home page
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
