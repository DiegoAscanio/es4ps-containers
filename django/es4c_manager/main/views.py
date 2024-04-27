from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from main.forms import CollegeUserRegistrationForm, CollegeUserLoginForm, CollegeUserChangeForm, CollegeUserPasswordChangeForm
from main.utils import generate_secure_otp, send_email_verification_token
from main.tasks import create_user, enable_account, update_user_attributes as celery_update_user_attributes, update_user_password as celery_update_user_password
from django.contrib.auth.decorators import login_required
import pdb

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

# Create your views here.

# index view
@login_required
def index(request):
    return render(request, 'index/index.html')

# login view
def login_view(request):
    if request.method == 'POST':
        form = CollegeUserLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username = form.cleaned_data['username'], password = form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                return redirect('/')
            else:
                return render(request, 'login/login.html', {'form': form, 'error': 'Invalid username or password'})
    else:
        form = CollegeUserLoginForm()
    return render(request, 'login/login.html', {'form': form})

# logout view
@login_required
def logout_view(request):
    logout(request)
    return redirect('/')

# Views to register a new user
def _perform_registration(request):
    if request.method == 'POST':
        form = CollegeUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit = False)
            user.set_password(form.cleaned_data['password_1']) # ensure password is hashed
            # generate a random token for email verification
            user.verification_token = generate_secure_otp()
            # send this token through email
            send_email_verification_token(user)
            # save our user object
            user.save()
            # perform user creation on samba addc servers
            new_user_fields = {
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
            create_user.delay(
                user.username,
                form.cleaned_data['password_1'],
                **new_user_fields
            )
            # login the user
            user = authenticate(request, username = user.username, password = form.cleaned_data['password_1'])
            # login the user
            login(request, user)
            # redirect to the verify email page
            return redirect('/verify-email/')
    else:
        form = CollegeUserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def register(request):
    if request.user.is_authenticated:
        return redirect('/')
    else:
        return _perform_registration(request)

# View to update user information
@login_required
def update_user_attributes(request):
    if request.method == 'POST':
        form = CollegeUserChangeForm(request.POST, instance = request.user)
        if form.is_valid():
            form.save()
            update_data = {
                'givenName': form.cleaned_data['first_name'],
                'sn': form.cleaned_data['last_name'],
            }
            celery_update_user_attributes.delay(
                request.user.username,
                **update_data
            )
            return redirect('/')
    else:
        form = CollegeUserChangeForm(instance = request.user)
    return render(request, 'change-user/change-user.html', {'form': form})

# View to change user password
@login_required
def update_user_password(request):
    if request.method == 'POST':
        form = CollegeUserPasswordChangeForm(request.POST, instance = request.user)
        if form.is_valid():
            user = form.save(commit = False)
            user.set_password(form.cleaned_data['password_1'])
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully')
            # call celery task to update password on samba addc servers
            celery_update_user_password.delay(
                user.username,
                form.cleaned_data['password_1']
            )
            return redirect('/')
        else:
            messages.error(request, 'Please correct the error below')
    else:
        form = CollegeUserPasswordChangeForm(instance = request.user)
    return render(request, 'change-password/change-password.html', {'form': form})

# view to proceed with user activation
# only authenticated users can access this view
@login_required
def _proceed_user_activation(request, token):
    if request.user.verification_token == token:
        request.user.is_verified = True
        request.user.save()
        enable_account.delay(
            request.user.username
        )
        return render(request, 'activation/successful.html')
    else:
        return render(request, 'activation/invalid.html')

# View to verify email
# only authenticated users can access this view
@login_required
def verify_email(request, token = None):
    if request.user.is_verified:
        return render(request, 'activation/already_verified.html')
    else:
        if token:
            return _proceed_user_activation(request, token)
        else:
            return render(request, 'verification/verify.html')
