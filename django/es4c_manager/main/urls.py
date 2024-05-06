from django.urls import path
from main.views import register, verify_email, index, update_user_attributes, login_view, logout_view, update_user_password

'''
    This file maps URLs that represent actions to the views responsible
    for handling them. As for the current release, only 8 URLs are
    enough to provide the functionalities for the MVP.

    In future releases there'll be more URLs to handle new features
'''

urlpatterns = [
    path('', index, name='index'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('change-user/', update_user_attributes, name='update_user_attributes'),
    path('change-password/', update_user_password, name='update_user_password'),
    path('register/', register, name='register'),
    path('verify-email/', verify_email, name='verify_email'),
    path('verify-email/<str:token>/', verify_email, name='verify_email'),
]
