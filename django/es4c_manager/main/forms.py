from django.conf import settings
import pdb
from django import forms
from main.models import CollegeUser
from django.core.exceptions import ValidationError
import re

'''
    This is the component responsible to validate all data that comes from the
    end user as well to prepare the data for end user manipulation through
    html forms in the application's templates.

    It is important to validate all data that comes from the end user
    in order to keep the minimum functionality of the application.
    The validation made here is done following the Django documentation. If
    you are not familiar with Django, it is necessary to read its
    documentation (and making its beginner tutorial) to fully understand
    how this component works and how to perform validations in general.

    The documentation is available at: https://docs.djangoproject.com/ and
    you can follow the first steps to accomplish Django's beginner tutorial.

    To explain in a general way how Django validation works, the developer
    should create a class that is bond (in some way) to the model that
    represents the data to be stored. This can achieved by inheriting from
    the forms.ModelForm class or can be done by direct coding the necessary
    fields and methods to validate the data in generic form class that
    inherits from forms.Form class.

    The majority of the classes in this file inherit from forms.ModelForm
    so the explanation will be based on this inheritance.

    The class that inherits from forms.ModelForm must have an inner Meta
    class that points to the model that the form bonds to. It also must
    contain any fields that the model does not have by itself and for
    some reason is necessary to be stored and validated.

    It also must contain clean methods bond to each field that needs
    validation to perform the validation logic specific to the field.

    The documentation of the class CollegeUserRegistrationForm is
    enough to understand how the validation works in this file,
    so please, read it and generalize the knowledge to the other classes.
'''

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
    '''
        A form class that is used to structure the data for end user
        manipulation as well as to validate it when the user fills the
        registration form in the application.

        The ColleUserModel as it inherits from django's abstract user model
        contains a password field, but it is not recommended to make 
        password manipulations directly in this field. For this reason
        two password fields are defined: password_1 and password_2.
        This way the end user is forced to type the password twice
        to avoid typing mistakes.
    '''
    password_1 = forms.CharField(
        label = 'Password',
        widget=forms.PasswordInput
    )
    password_2 = forms.CharField(
        label = 'Confirm Password',
        widget=forms.PasswordInput
    )
    class Meta:
        '''
            The inner Meta class bonds the form to the CollegeUser model
            and defines the fields that the form will handle through the
            fields attribute.
        '''
        model = CollegeUser
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_email(self):
        '''
            In this method the main feature of ES4ALL platform is achieved:
            The application will restrict user registration to only the
            allowed email domains from an organization and no one
            outside this organization will be able to register.

            How does it work?
            The domain is extracted from the email field (through the
            email.split('@')[1] method) and it is compared to the allowed
            email domains defined by the organization.

            If a match happens, the email is valid and the method returns
            it. If not, a ValidationError is raised with a message that
            informs the user about the allowed email domains.
        '''
        email = self.cleaned_data['email']
        domain = email.split('@')[1]
        for allowed_domain in settings.ALLOWED_EMAIL_DOMAINS:
            if re.match(domain, allowed_domain):
                return email
        error = 'Email domain must be one of the following: ' + ', '.join(settings.ALLOWED_EMAIL_DOMAINS)
        raise ValidationError(error)

    def clean_password_1(self):
        '''
            This method calls a private function _clean_password_1 where
            the password validation logic is implemented, such as the
            password length, the presence of uppercase and lowercase
            letters, digits and special characters.

            Whenever a user tried to register an account with an invalid
            email, the email field wouldn't be present in the cleaned_data
            and this was throwing a key error. To avoid this, the email
            field is checked if it is present in the cleaned_data and if
            not, it is set to an empty string. The same happens to the
            password field and only then the password validation is
            performed by _clean_password_1.
        '''
        email =\
            self.cleaned_data['email'] if 'email' in self.cleaned_data else ''
        password =\
            self.cleaned_data['password_1'] if 'password_1' in self.cleaned_data else ''
        return _clean_password_1(password, email)

    def clean_password_2(self):
        '''
            clean_password_2 should only check if the password_1 and
            password_2 are equal. If not, a ValidationError is raised
            with a message that informs the user that the passwords
            do not match.
        '''
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
