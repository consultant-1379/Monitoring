#!/usr/bin/python

#~# Includes
import json
import hpilo
#~#
class HP_ILO_Licence(object):
    #------------------------------------------------------
    def __init__(self, module, params):
        self.module     = module
        self.ilo_data       = dict(
            ip_address      = params['ip_address'],
            ilo_username    = params['ilo_username'],
            ilo_password    = params['ilo_password'],
            licence_key     = params['ilo_licence']
        )
        self.change_made = False
        #~#
        self.connect_ilo()
    #------------------------------------------------------
    def connect_ilo(self):
        self.current_ilo_licence = 'Unknown'
        #~# Create ILO Conncetion
        self.connected_ilo = hpilo.Ilo(self.ilo_data['ip_address'], self.ilo_data['ilo_username'], self.ilo_data['ilo_password'])
        #~#
        try:
            #~# First try and connect, retrieve the current ilo licence information. [0] because the data is returned in an array FFS!!!!!
            licence_data = self.connected_ilo.get_all_licenses()[0]
            if 'license_key' in licence_data:
                #~# Assign the current ilo licence removing any dashes "-"
                self.current_ilo_licence = licence_data['license_key'].replace("-", "")
            #~# Now check ilo licence
            self.check_and_update_licence()
        except Exception as conn_err:
            #~# Connection Failure
            self.module.exit_json(unreachable=True, msg='Could not conect to ILO via any of the standard user accounts')
    #------------------------------------------------------
    def check_and_update_licence(self):
        #~# Check if the current ILO licence is the latest
        if self.current_ilo_licence == self.ilo_data['ilo_licence']:
            #~# Current Installed matches, can exit successfully with no changes needed
            self.ilo_data['new_licence']        = self.ilo_data['ilo_licence']
            self.ilo_data['licence_installed']  = self.current_ilo_licence
            self.module.exit_json(changed=self.change_made, failed=False, msg=self.ilo_data)
        else:
            #~# Current Installed does not match, try update licence
            try:
                self.connected_ilo.activate_license(self.ilo_data['ilo_licence'])
                #~# Command Successfully ran, so assume change was made
                self.change_made = True
                #~# Now try and get the new current licence for verification
                try:
                    #~# First try and connect, retrieve the current ilo licence information. [0] because the data is returned in an array FFS!!!!!
                    licence_data = self.connected_ilo.get_all_licenses()[0]
                    if 'license_key' in licence_data:
                        #~# Assign the current ilo licence removing any dashes "-"
                        self.current_ilo_licence = licence_data['license_key'].replace("-", "")
                        self.check_and_update_licence()
                except Exception as verif_err:
                    self.module.exit_json(changed=self.change_made, failed=True, msg=("Something wrong. Successfully installed licence on host: '{}' but got error verifying").format(self.ilo_data['ip_address']))
            except Exception as conn_err:
                #~# Connection Failure
                self.module.exit_json(changed=self.change_made, failed=True, msg=("Something wrong. Experienced issue trying to install licence on host: '{}'").format(self.ilo_data['ip_address']))
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
            ilo_licence  = dict(required=True, type='str'),
        ),
        supports_check_mode=False
    )
    HP_ILO_Licence(module, module.params)
#~#
# import module snippets
from ansible.module_utils.basic import *
main()