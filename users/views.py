from django.shortcuts import render,redirect, HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from users.forms import CustomRegisterForm,AssignRoleForm,CreateRoleForm
from django.contrib import messages
from users.forms import LoginForm
from django.contrib.auth.tokens import default_token_generator
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
User= get_user_model()
def sign_up(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data.get('password1'))
            user.is_active = False 
            user.save()
            messages.success(request, "A confirmation email has been sent. Please check your inbox to activate your account.")
            return redirect('sign-in')
    else:
        form = CustomRegisterForm()
    return render(request, 'registration/sign_up.html', {'form': form})

def sign_in(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next') or 'home'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})

def activate_user(request, user_id, token):
    try:
        user= User.objects.get(id=user_id)
        if default_token_generator.check_token(user, token):
            user.is_active= True
            user.save()
            messages.success(request, "Your account has been activated! Please log in.")
            return redirect('sign-in')
        else:
            messages.error(request, "Activation link is invalid or has expired.")
            return redirect('sign-in')
    except User.DoesNotExist:
        messages.error(request, "User does not exist.")
        return redirect('sign-in')

@login_required
def sign_out(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')