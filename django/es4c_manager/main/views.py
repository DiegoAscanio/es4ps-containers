from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from main.forms import CollegeUserRegistrationForm, CollegeUserLoginForm, CollegeUserChangeForm, CollegeUserPasswordChangeForm
from main.utils import generate_secure_otp, send_email_verification_token
from main.tasks import create_user, enable_account, update_user_attributes as celery_update_user_attributes, update_user_password as celery_update_user_password
from django.contrib.auth.decorators import login_required
import pdb

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

'''
    This file is the most important for the application as it contains all the
    operations responsible for allowing an end user to perform self
    registration and self management of their account.

    These operations are represented by views, which in django are functions
    responsible for handling end users requests and responding them with
    the appropriate answers.

    We have a register view which is responsible for allowing an end user to
    register a new account. For the convenience of implementation this view
    was broken into a public view and a private view. The public view is
    responsible to check if the user is authenticated and to redirect the user
    to the main page if so (since authenticated users should not be able to
    reregister themselves). The private view is responsible for the actual
    registration of the user and is called by the public view whenever
    someone who does not have an account (so, who's not authenticated)
    tries to register a new one. Please read the comments in the private
    view _perform_registration to understand how a new user is created
    within the ES4ALL ecosystem.
'''

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
                next_url = request.GET.get('next','/')
                return redirect(next_url)
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
    '''
        _perform_registration is a private view that is responsible for
        handling the registration of a new user. This view is called by the
        public view register whenever a user tries to register a new account.

        If an user is accessing the registration page for the first time,
        it is performing a GET request, so a new CollegeUserRegistrationForm
        object is created and passed as a parameter to the registration
        template ('registration/register.html') which is then rendered by
        the instruction return render(request, 'registration/register.html',
        {'form': form}).

        If the user already filled its data and clicked the submit button,
        it performs a POST request with the filled data within the request.
        In this case a form object is created through the CollegeUserRegistrationForm
        with the data present in request.POST and if the form is valid, a new
        user object is created with the data present in the form.

        A verification token is generated for the new user and sent to its
        email address in order to restrain user registration within an
        organization scope to only those who have access to email addresses
        allowed by the organization.

        Then the user object is saved and a new user is created on the samba
        addc servers through the create_user celery task. At the end, the user
        is authenticated, logged in the system and redirected to the verify
        email page so the user can end its registration process.

        If the form is not valid, django helps the developer putting error
        messages (thrown in forms.py file) in the form object that will be 
        rendered by the template, in this case, when errors happen,
        {{field.errors}} template tag is set.

        We recommend reading the templates files in order to understand how
        the final user interacts with the system.

    '''
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


'''
    Django really helps the developer to control the access for protected
    resources. Whenever you need to restrain access to resources for only
    authenticated users, you can use the @login_required decorator as shown
    in the view below.

    You can also use other kinds of decorators such as @permission_required
    to restrain access to resources for users with specific permissions, i.e.,
    staff users or users that belongs to a specific group.
'''

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
    '''
        This is the view that check the user bond with the organization
        that uses ES4ALL for AD/DC services. A random token is generated
        for the user and sent to its email when it registers itself in
        the system.

        Then when the users check its inbox and click the link sent by
        the system, or input the token in the verify email page, this
        view is called to check if the token is valid and if so, the
        user is activated and can start using computers managed by the
        ES4ALL Samba AD/DC servers.

        For default any new user registered is disable in samba, but
        when the user inputs its correct token, its verified flag
        is set to True and the user is enabled in the samba addc servers
        through the enable_account celery task.
    '''
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
