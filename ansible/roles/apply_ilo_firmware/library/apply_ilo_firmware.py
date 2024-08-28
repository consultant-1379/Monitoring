#!/usr/bin/python

#~# Includes
import json
import hpilo
import os
#~# Global Variables
FW_INFORMATION = {
    'ILO2' : {
        'steps': ['1.61','1.70','1.80','2.01','2.12','2.23','2.33'],
        'locations': {
            '1.61': 'ILO2/ilo2_161.bin',
            '1.70': 'ILO2/ilo2_170.bin',
            '1.80': 'ILO2/ilo2_180.bin',
            '2.01': 'ILO2/ilo2_201.bin',
            '2.12': 'ILO2/ilo2_212.bin',
            '2.23': 'ILO2/ilo2_223.bin',
            '2.33': 'ILO2/ilo2_233.bin'
        }
    },
    'ILO4' : {
        'steps': ['1.05','1.40','2.00','2.61','2.70','2.72','2.81'],
        'locations': {
            '1.05': 'ILO4/ilo4_105.bin',
            '1.40': 'ILO4/ilo4_140.bin',
            '2.00': 'ILO4/ilo4_200.bin',
            '2.61': 'ILO4/ilo4_261.bin',
            '2.70': 'ILO4/ilo4_270.bin',
            '2.72': 'ILO4/ilo4_272.bin',
            '2.81': 'ILO4/ilo4_281.bin'
        }
    },
    'ILO5' : {
        'steps': ['1.20','1.35','1.39','2.18','2.30','2.44', '2,78'],
        'locations': {
            '1.20': 'ILO5/ilo5_120.bin',
            '1.35': 'ILO5/ilo5_135.bin',
            '1.39': 'ILO5/ilo5_139.bin',
            '2.18': 'ILO5/ilo5_218.bin',
            '2.30': 'ILO5/ilo5_230.bin',
            '2.44': 'ILO5/ilo5_244.bin',
            '2.78': 'ILO5/ilo5_278.bin'
        }
    },
}
#~#
class HP_ILO_Firmware(object):
    #------------------------------------------------------
    def __init__(self, module, params):
        self.initial_fw     = 'Unknown'
        self.max_fw_version = 'Unknown'
        self.module         = module
        self.next_fw_step   = 'Unknown'
        self.ilo_data       = dict(
            ip_address          = params['ip_address'],
            ilo_username        = params['ilo_username'],
            ilo_password        = params['ilo_password'],
            firmware_location   = params['firmware_location'],
        )
        #~#
        self.connect_ilo()
    #------------------------------------------------------
    def connect_ilo(self):
        self.current_fw_version = 'Unknown'
        self.ilo_version = 'Unknown'
        #~# Create ILO Connection
        self.connected_ilo = hpilo.Ilo(self.ilo_data['ip_address'], self.ilo_data['ilo_username'], self.ilo_data['ilo_password'])
        #~#
        try:
            #~# First try and connect, retrieve current firmware version
            firmware_information = self.connected_ilo.get_fw_version()
            if 'firmware_version' in firmware_information:
                #~# Firmware version returned from ILO
                if self.initial_fw=='Unknown':
                    self.initial_fw = firmware_information['firmware_version']
                self.current_fw_version = firmware_information['firmware_version']
            if 'management_processor' in firmware_information:
                #~# Assign ILO type for firmware matching
                self.ilo_version = firmware_information['management_processor'].replace(" ", "").upper()
            #~# Now check for the next firmware step
            self.get_next_firmware_step()
        except Exception as conn_err:
            #~# Connection Failure
            self.module.exit_json(unreachable=True, msg='Could not connect to ILO via any of the standard user accounts')
    #------------------------------------------------------
    def get_next_firmware_step(self):
        self.next_fw_step = 'Unknown'
        #~# First, check if the retrieved firmware level & ILO version is not Unknown
        if self.current_fw_version is not 'Unknown' and self.ilo_version is not 'Unknown':
            #~# Not Unknown, now lets check if we have firmware for the ilo type
            if self.ilo_version in FW_INFORMATION:
                if len(FW_INFORMATION[self.ilo_version]['steps']) > 0:
                    #~# Compare against latest firmware version
                    self.max_fw_version = FW_INFORMATION[self.ilo_version]['steps'][-1]
                    if self.current_fw_version < self.max_fw_version:
                        #~# Less than latest FW, Upgrade Needed
                        for version in FW_INFORMATION[self.ilo_version]['steps']:
                            if self.current_fw_version < version:
                                #~# Assign the next step
                                self.next_fw_step = version
                                #~# Now exit loop
                                break
                            else:
                                pass
                        #~# Now proceed to attempt upgrade
                        self.upgrade_firmware(FW_INFORMATION[self.ilo_version]['locations'])
                    else:
                        #~# Greater then or equal to max version, pass
                        self.module.exit_json(changed=False, failed=False, msg=("Nothing to be done, Firmware version already at level '{}'").format(self.current_fw_version))
                else:
                    #~# No firmware upgrade path specified, pass
                    self.module.exit_json(changed=False, failed=False, msg=("Cannot perform upgrades, Firmware upgrade path not present"))
            else:
                #~# Firmware version unknown
                self.module.exit_json(changed=False, failed=False, msg=("Nothing can be done, Firmware upgrades for ILO type '{}' not supported by automation").format(self.ilo_version))
        else:
            #~# Unknown firmware version, exit
            self.ilo_data['fw_version'] = self.current_fw_version
            self.ilo_data['ilo_version'] = self.ilo_version
            self.module.exit_json(changed=False, failed=False, msg=self.ilo_data)
    #------------------------------------------------------
    def upgrade_firmware(self, fw_locations=dict()):
        #~# To be used to calculate need for further firmware flashes
        more_upgrades = False
        #~# Check we have image for next upgrade level
        if self.next_fw_step in fw_locations:
            #~# We have a path to a bin image for the next upgrade step
            fw_file_location = "{}/{}".format(self.ilo_data['firmware_location'],fw_locations[self.next_fw_step])
            fw_file_exists = os.path.isfile(fw_file_location)
            self.module.exit_json(changed=True, msg=('{}, {}, {}').format(self.ilo_data['ip_address'], fw_file_exists, fw_file_location))
        #     #~# Check if the path actually exists
        #     if fw_file_exists:
        #         #~# File location exists, continue to upgrade firmware
        #         try:
        #             #~# Try upgrading firmware, using the update file location in fw_locations
        #             self.connected_ilo.update_rib_firmware(filename=fw_file_location)
        #             #~# Flash process completed, Pause script to allow for ILO reboot
        #             time.sleep(120)
        #             #~# Now check if firmware upgrade was successful (True | False)
        #             upgraded = self.check_upgraded()
        #             #~# Now check if update was applied
        #             if upgraded:
        #                 if self.current_fw_version < self.max_fw_version:
        #                     #~# Upgrade completed, but still less than latest version
        #                     more_upgrades = True
        #                     #~# As a cautionary measure, Pause script before flashing again to allow ilo to fully take new changes
        #                     time.sleep(180)
        #                 else:
        #                     #~# Firware was updated, >= self.max_fw_version
        #                     upgrade_message=("Successfully Upgraded from fw version '{}' to fw version '{}'").format(self.initial_fw,self.ilo_data['fw_version'])
        #             else:
        #                 #~# Firware was not updated
        #                 upgrade_message=("Something wrong, found the firmware image '{}', but version wasn't upgraded!!").format(fw_file_location)
        #         except:
        #             #~# Connection Failure
        #             self.module.exit_json(changed=False, failed=True, msg=("Something wrong. Experienced issue trying to upgrade host: '{}'").format(self.ilo_data['ip_address']))
        #         #~# Now check if we exit or upgrade again
        #         if more_upgrades:
        #             #~# More upgrades needed, start process again
        #             self.connect_ilo()
        #         else:
        #             #~# No more upgrades needed, Exit
        #             self.module.exit_json(changed=upgraded, failed=(not upgraded), msg=upgrade_message)
        #     else:
        #         #~# Could not find the path location
        #         self.module.exit_json(changed=False, failed=True, msg=("Something wrong, could not find the firmware image '{}'!!").format(fw_file_location))
        # else:
        #     #~# Dont have image path for next upgrade step
        #     self.module.exit_json(changed=False, failed=True, msg=("Something wrong, no image found for next step '{}'!!").format(self.next_fw_step))
    #------------------------------------------------------
    def check_upgraded(self):
        try:
            #~# Try and connect, retrieve current firmware version
            firmware_information = self.connected_ilo.get_fw_version()
            if 'firmware_version' in firmware_information:
                #~# Firmware version returned from ILO
                if firmware_information['firmware_version'] != self.current_fw_version:
                    #~# Firmware version has changed from initial poll
                    if firmware_information['firmware_version'] == self.next_fw_step:
                        #~# Firmware version matches the previously set next_step, Upgrade was successful
                        self.current_fw_version     = firmware_information['firmware_version']
                        self.ilo_data['fw_version'] = firmware_information['firmware_version']
                        return True
                    else:
                        #~# Firmware version does not match next_step, doesnt look like successful upgrade
                        return False
                else:
                    #~# Firmware version matches version from initial poll, upgrade not successful
                    return False
            else:
                #~# No Firmware version returned
                return False
        except Exception as conn_err:
            #~# Connection Failure
            self.module.exit_json(unreachable=True, msg="Can't connect to host, ilo may still be rebooting.")
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
            ip_address          = dict(required=True, type='str'),
            ilo_username        = dict(required=True, type='str'),
            ilo_password        = dict(required=True, type='str'),
            firmware_location   = dict(required=True, type='str'),
        ),
        supports_check_mode=False
    )
    HP_ILO_Firmware(module, module.params)
#~#
# import module snippets
from ansible.module_utils.basic import *
#~#
main()