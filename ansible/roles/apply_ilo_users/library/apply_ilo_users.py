#!/usr/bin/python

#~# Includes
import json
import hpilo
#~# Global Variables
OTHER_LOGINS    = dict(
    bete        = 'beter00t',
    root        = 'shroot12',
    cloud       = 'cl0udroot',
    ADDM_ilo    = 'Ath@10n3'
)
#~#
class HP_ILO_Users(object):
    #------------------------------------------------------
    def __init__(self, module, params):
        self.added_users    = list()
        self.module         = module
        self.ilo_data       = dict(
            ip_address      = params['ip_address'],
            ilo_username    = params['ilo_username'],
            ilo_password    = params['ilo_password'],
        )
        #~#
        self.connect_ilo()
    #------------------------------------------------------
    def connect_ilo(self):
        connection_successful = False
        #~# Create ILO Conncetion
        self.connected_ilo = hpilo.Ilo(self.ilo_data['ip_address'], self.ilo_data['ilo_username'], self.ilo_data['ilo_password'])
        #~#
        try:
            #~# First try and connect, retrieve list of users
            self.current_ilo_users  = self.connected_ilo.get_all_users()
            #~#
            connection_successful   = True
        except Exception as conn_err:
            #~# Connection Failure
            pass
        #~# Figure out what to do next
        if connection_successful:
            #~# Connection was established to ILO, Check all user accounts are present
            self.check_user_accounts()
        else:
            #~# Connection Failure, try connecting via other logins
            self.try_other_logins()

    #------------------------------------------------------
    def try_other_logins(self):
        connection_successful = False
        #~#
        for login in OTHER_LOGINS:
            if not connection_successful:
                self.connected_ilo = hpilo.Ilo(self.ilo_data['ip_address'], login, OTHER_LOGINS[login])
                #~#
                try:
                    #~# First try and connect, retrieve list of users
                    self.current_ilo_users  = self.connected_ilo.get_all_users()
                    #~#
                    connection_successful   = True
                except Exception as conn_err:
                    #~# Connection Failure, move onto next user account
                    pass
            else:
                break
        #~#
        if connection_successful:
            #~# Now check for ilo licence & ensure all user accounts are present
            self.check_user_accounts()
        else:
            self.module.exit_json(unreachable=True, msg='Could not conect to ILO via any of the standard user accounts')
    #------------------------------------------------------
    def check_user_accounts(self):
        #~# Check all user accounts are present on ilo
        if self.ilo_data['ilo_username'] not in self.current_ilo_users:
            #~# Default user account is not installed on ilo, add it
            self.connected_ilo.add_user(self.ilo_data['ilo_username'], self.ilo_data['ilo_username'], self.ilo_data['ilo_password'], admin_priv=True, remote_cons_priv=True, reset_server_priv=True, virtual_media_priv=True, config_ilo_priv=True)
            #~#
            if self.ilo_data['ilo_username'] not in self.added_users:
                self.added_users.append(self.ilo_data['ilo_username'])
        #~# Now check that all other necessary user accounts are present
        for login in OTHER_LOGINS:
            if login not in self.current_ilo_users and login is not 'root' and login is not 'cloud': #~# Dont want to add cloud & root all the time. Remove "and" clause where neccessary
                #~# Current account is not installed on the ilo, add it
                self.connected_ilo.add_user(login, login, OTHER_LOGINS[login], admin_priv=True, remote_cons_priv=True, reset_server_priv=True, virtual_media_priv=True, config_ilo_priv=True)
                #~#
                if login not in self.added_users:
                    self.added_users.append(login)
        #~# Now Exit
        self.calc_exit_conditions()
    #------------------------------------------------------
    def calc_exit_conditions(self):
        if len(self.added_users) > 0:
            #~# User accounts were added
            self.module.exit_json(changed=True, failed=False, msg=("User accounts added to ILO : '{}'").format(self.json_format_dict(self.added_users)))
        else:
            #~# All accounts were present
            self.module.exit_json(changed=False, failed=False, msg='All Accounts were present, nothing to add')
    #------------------------------------------------------
    def display_output(self):
        #~# Prints the ilo_data dict containing all the relevant information
        print(self.json_format_dict(self.ilo_data, True))
    #------------------------------------------------------
    def json_format_dict(self, data, pretty=False):
        #~# Converts a dict to a JSON object and dumps it as a formatted string
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)
    #------------------------------------------------------
#~#
def main():
    module = AnsibleModule(
        argument_spec = dict(
            ip_address   = dict(required=True, type='str'),
            ilo_username = dict(required=True, type='str'),
            ilo_password = dict(required=True, type='str'),
        ),
        supports_check_mode=False
    )
    HP_ILO_Users(module, module.params)
#~#
# import module snippets
from ansible.module_utils.basic import *
#~#
main()