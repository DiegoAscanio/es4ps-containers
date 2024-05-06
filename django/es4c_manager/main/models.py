from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from main.managers import CollegeUserManager

'''
    There are defined three models in this file:
        1. CollegeUser: The main model for the application, it is used to store
           user information and is used for creation, authentication, modifica-
           tion and deletion of users both in django web-app as well as in the
           ADDC samba server. As it is possible to see, this model is a subclass
           of AbstractBaseUser and PermissionsMixin, which means that it is
           fully compatible with the django authentication system which helps
           a lot in dealing with the AAA basic requirements of the application.
        2. ADDCUserCreationTask: This model is intended to store the tasks
           creation tasks sent to celery workers in SAMBA ADDC servers.
           In the current release of the application, this model isn't being
           used and it mostly likely to be refactored in future releases to
           deal with tasks in a more generic way.
        3. Campus: This model is used to store the information about the
           sites where samba workers will be deployed. It is not currently
           used and in future releases it will be refactored to be more generic
           (as well as the CollegeUser may be renamed) to represent any kind
           of institution that may use the application.
'''

class CollegeUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=40, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=100)
    verification_token = models.CharField(max_length=8, unique = True)
    is_verified = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CollegeUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        return self.first_name + ' ' + self.last_name

class ADDCUserCreationTask(models.Model):
    user = models.ForeignKey(CollegeUser, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    result = models.TextField(null=True)

class Campus(models.Model):
    name = models.CharField(max_length=255)
    server_address = models.CharField(max_length=255)
    def __str__(self):
        return self.name
