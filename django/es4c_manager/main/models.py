from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from main.managers import CollegeUserManager

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
