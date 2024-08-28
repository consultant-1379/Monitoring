#!/usr/bin/python

### Imports ###
import datetime
import json
import os
import subprocess
import xmltodict



class ChassisData(object):
    """docstring for ChassisData"""
    def __init__(self, passed_module, params):
        super(ChassisData, self).__init__()
        self.module         = passed_module
        self.hostname       = params["hostname"]
        self.dns_oa1        = params["dns_oa1"]
        self.dns_oa2        = params["dns_oa2"]
        self.current_date   = time.strftime("%Y-%m-%d %H:%M:%S")
        self.output_file    = '/etc/ansible/test_output_eeoiosu.csv'
        #~#
        self.result = {
            'hostname':     self.hostname,
            'pinging':    False,
            'oa_used':      0,
            'bays':         dict(),
            'seen_bays':    list(),
            'firmware':     dict()
        }
        #~#
        self.check_oas()

    def check_oas(self):
        if self.dns_oa1 != 'Unknown' and self.is_pinging(self.dns_oa1):
            self.get_data(self.dns_oa1)
        elif self.dns_oa2 != 'Unknown' and self.is_pinging(self.dns_oa2):
            self.get_data(self.dns_oa2)
        else:
            self.module.exit_json(unreachable=True, result=self.result)

    def is_pinging(self, passed_oa):
        if os.system("ping -c 1 -w2 %s >/dev/null 2>&1" % passed_oa) == 0:
            self.result['pinging'] = True
            return True
        else:
            return False

    def get_data(self, passed_oa):
        try:
            xml_data_command = 'wget -q --tries=1 -O - --no-check-certificate --no-proxy https://' + passed_oa + '/xmldata?item=all'
            xml_data = xmltodict.parse(subprocess.check_output(xml_data_command, shell=True))
            #~#
            self.result['oa_used'] = passed_oa
            #~#
            if 'ENCL' in xml_data['RIMP']['INFRA2']:
                self.result['hostname'] = xml_data['RIMP']['INFRA2']['ENCL']
            if 'STATUS' in xml_data['RIMP']['INFRA2']:
                self.result['chassis_status'] = xml_data['RIMP']['INFRA2']['STATUS']
            #~# First check for the chassis oa firmware
            if 'MANAGER' not in xml_data['RIMP']['INFRA2']['MANAGERS']:
                self.module.exit_json(changed=False, result=self.result)
            elif 'FWRI' in xml_data['RIMP']['INFRA2']['MANAGERS']['MANAGER']:
                self.getFirmware(xml_data['RIMP']['INFRA2']['MANAGERS']['MANAGER'])
                self.module.exit_json(changed=False, result=self.result)
            else:
                for chassis_oa in xml_data['RIMP']['INFRA2']['MANAGERS']['MANAGER']:
                    self.getFirmware(chassis_oa);
            #~# Now check the VCs / SANs
            if 'SWITCH' not in xml_data['RIMP']['INFRA2']['SWITCHES']:
                self.module.exit_json(changed=False, result=self.result)
            elif 'FWRI' in xml_data['RIMP']['INFRA2']['SWITCHES']['SWITCH']:
                self.getFirmware(xml_data['RIMP']['INFRA2']['SWITCHES']['SWITCH'])
                self.module.exit_json(changed=False, result=self.result)
            else:
                for chassis_oa in xml_data['RIMP']['INFRA2']['SWITCHES']['SWITCH']:
                    self.getFirmware(chassis_oa);
            #~# Now check for the Bay Info
            if 'BLADE' not in xml_data['RIMP']['INFRA2']['BLADES']:
                self.module.exit_json(changed=False, result=self.result)
            elif 'BSN' in xml_data['RIMP']['INFRA2']['BLADES']['BLADE']:
                self.getBaysInfo(xml_data['RIMP']['INFRA2']['BLADES']['BLADE'])
                self.module.exit_json(changed=False, result=self.result)
            else:
                for bay_info in xml_data['RIMP']['INFRA2']['BLADES']['BLADE']:
                    self.getBaysInfo(bay_info)
                self.module.exit_json(changed=False, result=self.result)
        except Exception as e:
            self.module.exit_json(failed=True, result=self.result, msg='Oh oh!')

    def getFirmware(self,passed_object):
        if 'BAY' in passed_object:
            if 'CONNECTION' in passed_object['BAY']:
                if 'SPN' in passed_object:
                    if 'Onboard Admin' in passed_object['SPN']:
                        #~# We know its an oa
                        self.result['firmware']['oa'+passed_object['BAY']['CONNECTION']] = 'Unknown'
                        #~# Now get the firmare
                        if 'FWRI' in passed_object:
                            self.result['firmware']['oa'+passed_object['BAY']['CONNECTION']] = passed_object['FWRI']
                    elif 'HP VC' in passed_object['SPN']:
                        #~# We know its a VC
                        self.result['firmware']['vc'+passed_object['BAY']['CONNECTION']] = 'Unknown'
                        #~# Now get the firmare
                        if 'FWRI' in passed_object:
                            self.result['firmware']['vc'+passed_object['BAY']['CONNECTION']] = passed_object['FWRI']


    def getBaysInfo(self, passed_object):
        if 'BAY' in passed_object:
            if 'CONNECTION' in passed_object['BAY']:
                self.result['seen_bays'].append(passed_object['BAY']['CONNECTION'])
                self.result['bays'][passed_object['BAY']['CONNECTION']] = {
                    'bsn':          'Unknown',
                    'status':       'Unknown',
                    'spn':          'Unknown',
                    'mgmtipaddr':   'Unknown',
                    'mgmtdnsname':  'Unknown',
                    'hostname':     'Unknown',
                    'mgmtfwversion':'Unknown',
                    'iloversion':   'Unknown',
                    'powerstate':   'Unknown',
                    'temperature':  0,
                    'wwpns':        list()
                }
                # Full length blade
                if 'OCCUPIES' in passed_object['BAY']:
                    self.result['bays'][passed_object['BAY']['CONNECTION']]['occupies'] = passed_object['BAY']['OCCUPIES']
                # Blade serial number
                if 'BSN' in passed_object:
                    self.result['bays'][passed_object['BAY']['CONNECTION']]['bsn'] = passed_object['BSN']
                # Status
                if 'STATUS' in passed_object:
                    self.result['bays'][passed_object['BAY']['CONNECTION']]['status'] = passed_object['STATUS']
                # Server product name
                if 'SPN' in passed_object:
                    self.result['bays'][passed_object['BAY']['CONNECTION']]['spn'] = passed_object['SPN']
                # Management Host Name
                if 'NAME' in passed_object:
                    self.result['bays'][passed_object['BAY']['CONNECTION']]['hostname'] = passed_object['NAME']
                # Management DNS Name
                if 'MGMTDNSNAME' in passed_object:
                    self.result['bays'][passed_object['BAY']['CONNECTION']]['mgmtdnsname'] = passed_object['MGMTDNSNAME']
                # Management IP address
                if 'MGMTIPADDR' in passed_object:
                    self.result['bays'][passed_object['BAY']['CONNECTION']]['mgmtipaddr'] = passed_object['MGMTIPADDR']
                # Management Firmware Version
                if 'MGMTFWVERSION' in passed_object:
                    #~# Split the string to only get the version. eg 1.22 instead of 1.22 Apr 19 2013
                    self.result['bays'][passed_object['BAY']['CONNECTION']]['mgmtfwversion'] = passed_object['MGMTFWVERSION'].split()[0]
                # ILO Version
                if 'MGMTPN' in passed_object:
                    self.result['bays'][passed_object['BAY']['CONNECTION']]['iloversion'] = passed_object['MGMTPN']
                # Power state
                if 'POWER' in passed_object:
                    if 'POWERSTATE' in passed_object['POWER']:
                        self.result['bays'][passed_object['BAY']['CONNECTION']]['powerstate'] = passed_object['POWER']['POWERSTATE']
                # Temperature
                if 'TEMPS' in passed_object:
                    if 'TEMP' in passed_object['TEMPS']:
                        if 'C' in passed_object['TEMPS']['TEMP']:
                            self.result['bays'][passed_object['BAY']['CONNECTION']]['temperature'] = passed_object['TEMPS']['TEMP']['C']
                # World wide port numbers
                if 'PORTMAP' in passed_object:
                    if 'MEZZ' in passed_object['PORTMAP']:
                        for mezz in passed_object['PORTMAP']['MEZZ']:
                            if 'DEVICE' in mezz:
                                if 'PORT' in mezz['DEVICE']:
                                    for port in mezz['DEVICE']['PORT']:
                                        if 'WWPN' in port:
                                            self.result['bays'][passed_object['BAY']['CONNECTION']]['wwpns'].append(port['WWPN'])

#~# Main
def main():
    module = AnsibleModule(
        argument_spec = dict(
            hostname    = dict(required=True, type='str'),
            dns_oa1     = dict(required=True, type='str'),
            dns_oa2     = dict(required=True, type='str')
        ),
        supports_check_mode=False
    )
    ChassisData(module, module.params)
    # check_chassis(module, module.params)

# Import module snippets
from ansible.module_utils.basic import *
main()