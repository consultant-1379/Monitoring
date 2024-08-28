#!/usr/bin/python

import json
import re
import os
import csv
from datetime import datetime
#~# Global Variables
CHASSIS_DIR    = '../host_files/chassis_oas.csv'

class ChassisInventory(object):
    def __init__(self):
        self.chassis_list = list()
        self.inventory = {
            '_meta': {
                'hostvars': dict()
            },
            'chassis': {
                'hosts': list()
            }
        }
        self.chassis_hosts_pwd = "{}/{}".format(os.path.dirname(os.path.realpath(__file__)),CHASSIS_DIR)
        #~#
        #~# Check if the ilo_list exists
        chassis_list_exists = os.path.isfile(self.chassis_hosts_pwd)
        #~#
        if chassis_list_exists:
            #~# File exists, continue to import from file
            self.chassis_list_data = self.parse_input_csv()
        #~#
        self.get_chassis_inventory()
        self.display_output()
    #------------------------------------------------------
    def parse_input_csv(self):
        tmp_chassis_list = list()
        tmp_chassis_vars = dict()
        #~# Read from ilo_list file & import ilo list
        with open(self.chassis_hosts_pwd) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                chassis_name = row[0].split("oa")[0]
                tmp_chassis_list.append(chassis_name)
                if chassis_name not in tmp_chassis_vars:
                    tmp_chassis_vars[chassis_name] = dict(
                        hostname = chassis_name,
                        excluded = 0,
                        dns_oa1 = self.add_host_var(row, 0),
                        ip_oa1 = self.add_host_var(row, 1),
                        dns_oa2 = self.add_host_var(row, 2),
                        ip_oa2 = self.add_host_var(row, 3)
                    )

        #~# Now return the imported list
        return dict(host_list = tmp_chassis_list, host_vars = tmp_chassis_vars)
    #------------------------------------------------------
    def get_chassis_inventory(self):
        if(len(self.chassis_list_data['host_list']) > 0):
            for chassis in self.chassis_list_data['host_list']:
                if chassis not in self.inventory['chassis']['hosts']:
                    self.inventory['chassis']['hosts'].append(chassis)
                if chassis not in self.inventory['_meta']['hostvars']:
                    if chassis in self.chassis_list_data['host_vars']:
                        self.inventory['_meta']['hostvars'][chassis] = self.chassis_list_data['host_vars'][chassis]
    #------------------------------------------------------
    def add_host_var(self, row, item_index):
        try:
            return row[item_index]
        except IndexError:
            return 'Unknown'
    #------------------------------------------------------
    def display_output(self):
        print(self.json_format_dict(self.inventory, True))
    #------------------------------------------------------
    def json_format_dict(self, data, pretty=False):
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)
    #------------------------------------------------------

ChassisInventory()