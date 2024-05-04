from django.conf import settings
import pdb
from django import forms
from main.models import CollegeUser
from django.core.exceptions import ValidationError
import re

def _clean_password_1(password, email):
    email_username = email.split('@')[0]
    domain = email.split('@')[-1]
    if len(password) < 10:
        raise ValidationError('Password must be at least 10 characters long.')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter.')
    if not re.search(r'[0-9]', password):
        raise ValidationError('Password must contain at least one digit.')
    if not re.search(r'\W', password):
        raise ValidationError('Password must contain at least one special character.')
    if (
        email in password and email != ''
    ) or (
        email_username in password and email_username != ''
    ) or (
        domain in password and domain != ''
    ):
        raise ValidationError('Password must not contain email or username.')
    return password

class CollegeUserLoginForm(forms.Form):
    username = forms.CharField(
        label = 'Username',
        widget=forms.TextInput
    )
    password = forms.CharField(
        label = 'Password',
        widget=forms.PasswordInput
    )

class CollegeUserRegistrationForm(forms.ModelForm):
    password_1 = forms.CharField(
        label = 'Password',
        widget=forms.PasswordInput
    )
    password_2 = forms.CharField(
        label = 'Confirm Password',
        widget=forms.PasswordInput
    )
    class Meta:
        model = CollegeUser
        fields = ['username', 'email', 'first_name', 'last_name']
    def clean_email(self):
        email = self.cleaned_data['email']
        domain = email.split('@')[1]
        for allowed_domain in settings.ALLOWED_EMAIL_DOMAINS:
            if re.match(domain, allowed_domain):
                return email
        error = 'Email domain must be one of the following: ' + ', '.join(settings.ALLOWED_EMAIL_DOMAINS)
        raise ValidationError(error)

    def clean_password_1(self):
        email =\
            self.cleaned_data['email'] if 'email' in self.cleaned_data else ''
        password =\
            self.cleaned_data['password_1'] if 'password_1' in self.cleaned_data else ''
        return _clean_password_1(password, email)

    def clean_password_2(self):
        if 'password_1' not in self.cleaned_data:
            raise ValidationError('Password 1 is required.')
        password_1 = self.cleaned_data['password_1']
        password_2 = self.cleaned_data['password_2']
        if password_1 != password_2:
            raise ValidationError('Passwords do not match.')
        return self.cleaned_data['password_2']

class CollegeUserChangeForm(forms.ModelForm):
    class Meta:
        model = CollegeUser
        fields = ['first_name', 'last_name']

class CollegeUserPasswordChangeForm(forms.ModelForm):
    password_1 = forms.CharField(
        label = 'Password',
        widget=forms.PasswordInput
    )
    password_2 = forms.CharField(
        label = 'Confirm Password',
        widget=forms.PasswordInput
    )
    class Meta:
        model = CollegeUser
        fields = []
    def clean_password_1(self):
        email = self.instance.email
        password = self.cleaned_data['password_1']
        return _clean_password_1(password, email)
    def clean_password_2(self):
        if 'password_1' not in self.cleaned_data:
            raise ValidationError('Password 1 is required.')
        password_1 = self.cleaned_data['password_1']
        password_2 = self.cleaned_data['password_2']
        if password_1 != password_2:
            raise ValidationError('Passwords do not match.')
        return self.cleaned_data['password_2']
