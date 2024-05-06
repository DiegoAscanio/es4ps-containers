
from __future__ import unicode_literals

from es4c_manager.celery import app

from samba.samdb import SamDB
from samba import param
from samba.credentials import Credentials
import ldb
import unicodedata
import os

'''
    This file is exactly the same as the tasks.py present either in django
    `es4c_manager/main/tasks.py` and in each of the samba workers,
    as the celery documentation, as far as the author knows, recommends.

    Here you can see that Samba Users operations are made by the use of
    the samba python library and LDAP filters.

    More information about the samba python library can be found at:
    https://www.samba.org/samba/docs and
    https://samba.tranquil.it/doc/en/samba_advanced_methods/samba_python_samdb.html
'''

server_admin_password = os.environ['SAMBA_ADMIN_PASSWORD']

lp = param.LoadParm()
lp.load_default()

# this badge is necessary to establish connection to the samba server and
# perform operations on it
badge = Credentials()
badge.guess(lp)
badge.set_username('Administrator')
badge.set_password(server_admin_password)

# this ldif template is used to update user attributes on the samba server.
# It is required by the update_user_attributes task.
ldif_template = '''dn: {dn}
changetype: modify
replace: {attr}
{attr}: {value}
'''

def normalize(s):
    return str(unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8'))

def user_exists(username):
    '''
        Check if a user exists in the Samba server.

        Parameters: username - the username of the user to check

        Returns: True if the user exists, False otherwise
    '''
    # Connect to the SamDB
    samdb = SamDB(url="ldap://localhost", session_info=None, credentials=badge, lp=lp)

    try:
        # Try to get the user DN thorugh samdb.search and the filter expression
        # (samAccountName=username). If the user does not exist, an exception
        # will be raised and the function will return False. Else, it will return
        # True.
        username = normalize(username)
        user_dn = samdb.search(base=samdb.domain_dn(), expression=f"(samAccountName={username})", attrs=["dn"])
        if user_dn:
            print(f"User {username} exists.")
            return True
    except Exception as e:
        print(f"User {username} does not exist. Error: {e}")

    return False

def _proceed_user_creation(username, password, **kwargs):
    # here all attributes from the celery user creation task
    # extracted and normalized to avoid encoding issues.
    givenname = normalize(kwargs.get('first_name', ''))
    surname = normalize(kwargs.get('last_name', ''))
    loginshell = normalize(kwargs.get('login_shell', '/bin/bash'))
    unixhome = normalize(kwargs.get('unix_home', '/home/' + username))
    username = normalize(username)

    # make connection to samdb through ldap and necessary credentials
    samdb = SamDB(url='ldap://localhost',lp=lp,credentials=badge)
    # create new user through the samba python's library samdb.newuser method
    samdb.newuser(username, password, force_password_change_at_next_login_req=False, givenname=givenname, surname=surname, loginshell=loginshell, unixhome=unixhome, useusernameascn=True)
    # and disable its account until the user verifies it through verification
    # code sent to its email. The disable_account is also performed through
    # the samdb's method disable_account.
    samdb.disable_account(
        '(samAccountName={})'.format(username)
    )

    return 'User ' + username + ' created'

@app.task(name='tasks.create_user')
def create_user(username, password, **kwargs):
    '''
        A task that will create a user if and only if the user
        does not exist in the Samba server.

        Parameters: username - the username of the user to create
                    password - the password of the user to create
                    kwargs - a dictionary with the attributes of the user to 
                             create

        Returns: 'User <username> created' if the user was created successfully,
                 'User <username> already exists' if the user already exists.
    '''
    if not user_exists(username):
        # if and only if the user does not exist, then proceed with the user
        # creation through the private function _proceed_user_creation
        return _proceed_user_creation(username, password, **kwargs)
    return 'User ' + username + ' already exists'

@app.task(name='tasks.enable_account')
def enable_account(username):
    '''
        A task that will enable a user account in the Samba server. It does
        not check if the user exists or not in the server, it forwards this
        responsibility for those who call this task.

        Parameters: username - the username of the user to enable

        Returns: 'Account <username> enabled'
    '''
    samdb = SamDB(url='ldap://localhost',lp=lp,credentials=badge)
    samdb.enable_account(
        '(samAccountName={})'.format(username)
    )
    return 'Account ' + username + ' enabled'

@app.task(name='tasks.update_user_attributes')
def update_user_attributes(username, **kwargs):
    '''
        A task that will update the attributes of a user in the Samba server.

        Parameters: username - the username of the user to update
                    kwargs - a dictionary with the attributes to update

        Returns: 'User <username> updated' if the user was updated successfully
                  An error message if something went wrong
    '''
    # make connection to samdb through ldap and necessary credentials
    samdb = SamDB(url='ldap://localhost',lp=lp,credentials=badge)
    # try to update user
    try:
        # Search for the user DN
        user_dn = samdb.search(base=samdb.domain_dn(), expression=f"(samAccountName={username})", attrs=["dn"])
        # if user don't exist
        if not user_dn:
            return 'User ' + username + ' does not exist'
        # Update attributes
        for key, value in kwargs.items():
            # Here we use the ldif_template to update the user attributes
            # through the samdb.modify_ldif method. This is benefical because
            # the template is the most generic as possible and can be used to
            # update (virtualy) any attribute of the user.
            samdb.modify_ldif(
                ldif_template.format(
                    dn=user_dn[0]['dn'],
                    attr=key,
                    value=value
                )
            )
        return 'User ' + username + ' updated'
    except Exception as e:
        return f"Error updating user {username}: {e}"


@app.task(name='tasks.update_user_password')
def update_user_password(username, password):
    '''
        A task that will update the password of a user in the Samba server.
        It needs to be different from update_user_attributes because there
        is a specific method in the samba python's library to update
        passwords.

        Parameters: username - the username of the user to update the password
                    password - the new password to set for the user

        Returns: 'Password updated for <username>' if the password was updated.
                  An error message if something went wrong.
    '''
    samdb = SamDB(url='ldap://localhost',lp=lp,credentials=badge)
    try:
        # samdb setpassword method needs two parameters: the filter expression
        # to find the user and the new password.
        samdb.setpassword(
            '(samAccountName={})'.format(username),
            password
        )
        return 'Password updated for ' + username
    except Exception as e:
        return f"Error updating password for {username}: {e}"

@app.task(name='tasks.delete_user')
def delete_user(username):
    '''
        A task that will delete a user from the Samba server.
        
        Parameters: username - the username of the user to delete

        Returns: 'User <username> deleted' if the user was deleted successfully
                  An error message if something went wrong.
    '''
    samdb = SamDB(url='ldap://localhost',lp=lp,credentials=badge)
    try:
        samdb.deleteuser(
            username
        )
        return 'User ' + username + ' deleted'
    except Exception as e:
        return f"Error deleting user {username}: {e}"
