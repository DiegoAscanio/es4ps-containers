from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from main.forms import CollegeUserRegistrationForm, CollegeUserChangeForm
from main.models import CollegeUser
from main.tasks import create_user, enable_account, update_user_attributes, delete_user

'''
    This file contains configuration to enable CollegeUserModel operations
    from the Django admin interface. This is extremely useful and until
    now the only way to allow an IT admin to delete users from the system —
    in Django as well in the Samba AD DC servers — since the CRUD methods
    call Celery tasks (when appropriate) to reflect the operations on the
    Samba AD DC servers.

    In future releases other models will be added to the admin interface,
    so this file will be updated to perform those changes.
'''

class CollegeUserAdmin(BaseUserAdmin):
    form = CollegeUserChangeForm
    add_form = CollegeUserRegistrationForm
    model = CollegeUser
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('is_admin', 'is_staff', 'is_superuser', 'is_active', 'is_verified')
        }),
    )
    add_fieldsets = (
        (None, {
            'fields': ('username', 'email', 'first_name', 'last_name', 'password_1', 'password_2', 'verification_token')
        }),
        ('Permissions', {
            'fields': ('is_admin', 'is_staff', 'is_superuser', 'is_active', 'is_verified')
        }),
    )

    exclude = (
        'date_joined', 
    )

    def _create_user(self, username, password, **kwargs):
        create_user.delay(username, password, **kwargs) # a call to a celery task for user creation
        enable_account.delay(username) # a call to a celery task to enable a user account

    def _update_user(self, username, **kwargs):
        update_user_attributes.delay(username, **kwargs)

    # override save_model method to call celery tasks on samba container
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        user_fields = {
            'first_name': form.cleaned_data['first_name'],
            'last_name': form.cleaned_data['last_name'],
        }
        if change:
            self._update_user(obj.username, **user_fields)
        self._create_user(obj.username, form.cleaned_data['password_1'], **user_fields)

    # override delete_model method to call celery tasks on samba container
    # to delete user from samba container
    def delete_model(self, request, obj):
        print('Here Hagrid!')
        super().delete_model(request, obj)
        delete_user.delay(obj.username)

    # override delete_queryset method to call celery tasks on samba container
    # for bulk deletion of users
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)


admin.site.register(CollegeUser, CollegeUserAdmin)
admin.site.unregister(Group)
