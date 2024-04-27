
from __future__ import unicode_literals

from .celery import app

from samba.samdb import SamDB
from samba import param
from samba.credentials import Credentials
import ldb
import unicodedata
import os
import pdb

server_admin_password = os.environ['SAMBA_ADMIN_PASSWORD']

lp = param.LoadParm()
lp.load_default()
badge = Credentials()
badge.guess(lp)
badge.set_username('Administrator')
badge.set_password(server_admin_password)

ldif_template = '''dn: {dn}
changetype: modify
replace: {attr}
{attr}: {value}
'''

def normalize(s):
    return str(unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('utf-8'))

def user_exists(username):
    # Connect to the SamDB
    samdb = SamDB(url="ldap://localhost", session_info=None, credentials=badge, lp=lp)

    try:
        # Try to get the user DN; this will raise an exception if the user does not exist
        username = normalize(username)
        user_dn = samdb.search(base=samdb.domain_dn(), expression=f"(samAccountName={username})", attrs=["dn"])
        if user_dn:
            print(f"User {username} exists.")
            return True
    except Exception as e:
        print(f"User {username} does not exist. Error: {e}")

    return False

def _proceed_user_creation(username, password, **kwargs):
    givenname = normalize(kwargs.get('first_name', ''))
    surname = normalize(kwargs.get('last_name', ''))
    loginshell = normalize(kwargs.get('login_shell', '/bin/bash'))
    unixhome = normalize(kwargs.get('unix_home', '/home/' + username))
    username = normalize(username)

    # make connection to samdb through ldap and necessary credentials
    samdb = SamDB(url='ldap://localhost',lp=lp,credentials=badge)
    # create new user
    samdb.newuser(username, password, force_password_change_at_next_login_req=False, givenname=givenname, surname=surname, loginshell=loginshell, unixhome=unixhome, useusernameascn=True)
    # and disable its account until the user verifies it through verification
    # code sent to its email
    samdb.disable_account(
        '(samAccountName={})'.format(username)
    )

    return 'User ' + username + ' created'

@app.task(name='tasks.create_user')
def create_user(username, password, **kwargs):
    if not user_exists(username):
        return _proceed_user_creation(username, password, **kwargs)
    return 'User ' + username + ' already exists'

@app.task(name='tasks.enable_account')
def enable_account(username):
    samdb = SamDB(url='ldap://localhost',lp=lp,credentials=badge)
    samdb.enable_account(
        '(samAccountName={})'.format(username)
    )
    return 'Account ' + username + ' enabled'

@app.task(name='tasks.update_user_attributes')
def update_user_attributes(username, **kwargs):
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
    samdb = SamDB(url='ldap://localhost',lp=lp,credentials=badge)
    try:
        samdb.setpassword(
            '(samAccountName={})'.format(username),
            password
        )
        return 'Password updated for ' + username
    except Exception as e:
        return f"Error updating password for {username}: {e}"

@app.task(name='tasks.delete_user')
def delete_user(username):
    samdb = SamDB(url='ldap://localhost',lp=lp,credentials=badge)
    try:
        samdb.deleteuser(
            username
        )
        return 'User ' + username + ' deleted'
    except Exception as e:
        return f"Error deleting user {username}: {e}"
