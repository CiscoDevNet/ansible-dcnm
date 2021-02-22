#!/usr/bin/python
#
# Copyright (c) 2020 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import copy
import json
import re
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send, validate_list_of_dicts, dcnm_get_ip_addr_info

__author__ = "Karthik Babu Harichandra Babu"

DOCUMENTATION = '''
---
module: dcnm_inventory
short_description: Add and remove Switches from a DCNM managed VXLAN fabric.
version_added: "0.9.0"
description:
    - "Add and remove Switches from a DCNM managed VXLAN fabric."
author: Karthik Babu Harichandra Babu(kharicha@cisco.com)
options:
  fabric:
    description:
      - 'Name of the target fabric for Inventory operations'
    type: str
    required: yes
  state:
    description:
      - The state of DCNM after module completion.
    type: str
    choices:
      - merged
      - overridden
      - deleted
      - query
    default: merged
  config:
    description: 'List of switches being managed'
    type: list
    elements: dict
    required: true
    note: Not required for state deleted
    suboptions:
      seed_ip:
        description: 'Seed Name(support both IP address and dns_name) of the switch which needs to be added to the DCNM Fabric'
        type: ipv4
        required: true
      auth_proto:
        description: 'Name of the authentication protocol to be used'
        choices: ['MD5', 'SHA', 'MD5_DES', 'MD5_AES', 'SHA_DES', 'SHA_AES']
        type: str
        required: true (except for state 'deleted' and 'query')
      user_name:
        description: 'Login username to the switch'
        type: str
        required: true (except for state 'deleted' and 'query')
      password:
        description: 'Login password to the switch'
        type: str
        required: true (except for state 'deleted' and 'query')
      max_hops:
        description: 'Maximum Hops to reach the switch'
        type: str
        required: true (except for state 'deleted' and 'query')
      role:
        description: 'Role which needs to be assigned to the switch'
        choices: ['leaf', 'spine', 'border', 'border_spine', 'border_gateway', 'border_gateway_spine',
                 'super_spine', 'border_super_spine', 'border_gateway_super_spine']
        type: str
        required: true
        default: leaf
      preserve_configs:
        description: 'Set this to false for greenfield deployment and true for brownfield deployment'
        type: str
        required: true (except for state 'deleted' and 'query')
'''

EXAMPLES = '''
This module supports the following states:

Merged:
  Switches defined in the playbook will be merged into the target fabric.
    - If the switch does not exist it will be added.
    - Switches that are not specified in the playbook will be untouched.

Overridden:
  The playbook will serve as source of truth for the target fabric.
    - If the switch does not exist it will be added.
    - If the switch is not defined in the playbook but exists in DCNM it will be removed.
    - If the switch exists, properties that need to be modified and can be modified will be modified.

Deleted:
  Deletes the list of switches specified in the playbook.
  If no switches are provided in the playbook, all the switches present on that DCNM fabric will be deleted.

Query:
  Returns the current DCNM state for the switches listed in the playbook.


# The following two switches will be merged into the existing fabric
-name: Merge switch into fabric
    cisco.dcnm.dcnm_inventory:
      fabric: vxlan-fabric
      state: merged # merged / deleted / overridden / query
      config:
       - seed_ip: 192.168.0.1
         auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
         user_name: switch_username
         password: switch_password
         max_hops: 0
         role: spine
         preserve_config: False # boolean, default is  true
       - seed_ip: 192.168.0.2
         auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
         user_name: switch_username
         password: switch_password
         max_hops: 0
         role: leaf
         preserve_config: False # boolean, default is  true

# The following two switches will be added or updated in the existing fabric and all other
# switches will be removed from the fabric
- name: Override Switch
    cisco.dcnm.dcnm_inventory:
      fabric: vxlan-fabric
      state: merged # merged / deleted / overridden / query
      config:
       - seed_ip: 192.168.0.1
         auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
         user_name: switch_username
         password: switch_password
         max_hops: 0
         role: spine
         preserve_config: False # boolean, default is  true
       - seed_ip: 192.168.0.2
         auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
         user_name: switch_username
         password: switch_password
         max_hops: 0
         role: leaf
         preserve_config: False # boolean, default is  true

# The following two switches will be deleted in the existing fabric
- name: Delete selected switches
    cisco.dcnm.dcnm_inventory:
      fabric: vxlan-fabric
      state: deleted # merged / deleted / overridden / query
      config:
       - seed_ip: 192.168.0.1
         auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
         user_name: switch_username
         password: switch_password
         max_hops: 0
         role: spine
         preserve_config: False # boolean, default is  true
       - seed_ip: 192.168.0.2
         auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
         user_name: switch_username
         password: switch_password
         max_hops: 0
         role: leaf
         preserve_config: False # boolean, default is  true

# All the switches will be deleted in the existing fabric
- name: Delete all the switches
    cisco.dcnm.dcnm_inventory:
      fabric: vxlan-fabric
      state: deleted # merged / deleted / overridden / query

# The following two switches information will be queried in the existing fabric
-name: Query switch into fabric
    cisco.dcnm.dcnm_inventory:
      fabric: vxlan-fabric
      state: query # merged / deleted / overridden / query
      config:
       - seed_ip: 192.168.0.1
         role: spine
       - seed_ip: 192.168.0.2
         role: leaf

# All the existing switches will be queried in the existing fabric
- name: Query all the switches in the fabric
    cisco.dcnm.dcnm_inventory:
      fabric: vxlan-fabric
      state: query # merged / deleted / overridden / query
      '''


class DcnmInventory:

    def __init__(self, module):
        self.switches = {}
        self.module = module
        self.params = module.params
        self.fabric = module.params['fabric']
        self.config = module.params.get('config')
        self.check_mode = False
        self.validated = []
        self.have_create = []
        self.want_create = []
        self.diff_create = []
        self.diff_save = {}
        self.diff_delete = {}
        self.query = []
        self.node_migration = False

        self.result = dict(
            changed=False,
            diff=[],
            response=[]
        )

    def update_discover_params(self, inv):

        # with the inv parameters perform the test-reachability (discover)
        method = 'POST'
        path = '/rest/control/fabrics/{}/inventory/test-reachability'.format(self.fabric)
        response = dcnm_send(self.module, method, path, json.dumps(inv))
        self.result['response'].append(response)
        fail, self.result['changed'] = self.handle_response(response, "create")

        if fail:
            self.module.fail_json(msg=response)

        if ('DATA' in response):
            return response['DATA']

        else:
            return 0

    def update_create_params(self, inv):

        s_ip = 'None'
        if inv['seed_ip']:
            s_ip = dcnm_get_ip_addr_info(self.module, inv['seed_ip'], None, None)

        state = self.params['state']

        if state == 'deleted':
            inv_upd = {
                "seedIP": s_ip,
            }
        elif state == 'query':
            inv_upd = {
                "seedIP": s_ip,
                "role": inv['role'].replace(" ", "")
            }
        else:
            if inv['auth_proto'] == 'MD5':
                pro = 0
            elif inv['auth_proto'] == 'SHA':
                pro = 1
            elif inv['auth_proto'] == 'MD5_DES':
                pro = 2
            elif inv['auth_proto'] == 'MD5_AES':
                pro = 3
            elif inv['auth_proto'] == 'SHA_DES':
                pro = 4
            elif inv['auth_proto'] == 'SHA_AES':
                pro = 5
            else:
                pro = 0

            inv_upd = {
                "seedIP": s_ip,
                "snmpV3AuthProtocol": pro,
                "username": inv['user_name'],
                "password": inv['password'],
                "maxHops": inv['max_hops'],
                "cdpSecondTimeout": "5",
                "role": inv['role'].replace(" ", ""),
                "preserveConfig": inv['preserve_config']
            }

            resp = (self.update_discover_params(inv_upd))

            inv_upd["switches"] = resp

        return inv_upd

    def get_have(self):

        method = 'GET'
        path = '/rest/control/fabrics/{}/inventory'.format(self.fabric)
        inv_objects = dcnm_send(self.module, method, path)
        missing_fabric, not_ok = self.handle_response(inv_objects, 'query_dcnm')

        if inv_objects.get('ERROR') == 'Not Found' and inv_objects.get('RETURN_CODE') == 404:
            self.module.fail_json(msg="Fabric {} not present on DCNM".format(self.fabric))
            return

        if missing_fabric or not_ok:
            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find inventories under fabric: {}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not inv_objects['DATA']:
            return

        have_switch = []

        for inv in inv_objects['DATA']:
            get_switch = {}
            get_switch.update({'sysName': inv['logicalName']})
            get_switch.update({'serialNumber': inv['serialNumber']})
            get_switch.update({'ipaddr': inv['ipAddress']})
            get_switch.update({'platform': inv['nonMdsModel']})
            get_switch.update({'version': inv['release']})
            get_switch.update({'deviceIndex': inv['logicalName'] + '(' + inv['serialNumber'] + ')'})
            get_switch.update({'role': inv['switchRole'].replace(" ", "")})
            get_switch.update({'mode': inv['mode']})
            get_switch.update({'serialNumber': inv['serialNumber']})
            switchdict = {}
            switchlst = []
            switchlst.append(get_switch)
            switchdict["switches"] = switchlst
            have_switch.append(switchdict)

        self.have_create = have_switch

    def get_want(self):

        want_create = []

        if not self.config:
            return

        for inv in self.validated:
            want_create.append(self.update_create_params(inv))

        if not want_create:
            return

        self.want_create = want_create

    def get_diff_override(self):

        self.get_diff_replace()
        self.get_diff_replace_delete()

        diff_create = self.diff_create
        diff_delete = self.diff_delete

        self.diff_create = diff_create
        self.diff_delete = diff_delete

    def get_diff_replace(self):

        self.get_diff_merge()
        diff_create = self.diff_create

        self.diff_create = diff_create

    def get_diff_replace_delete(self):

        diff_delete = []

        def have_in_want(have_c):
            match_found = False
            for want_c in self.want_create:
                match = re.search(r'\S+\((\S+)\)', want_c["switches"][0]['deviceIndex'])
                if match is None:
                    continue
                want_serial_num = match.groups()[0]
                if have_c["switches"][0]['serialNumber'] == want_serial_num:
                    if have_c["switches"][0]['ipaddr'] == want_c["switches"][0]['ipaddr'] and \
                            have_c["switches"][0]['platform'] == want_c["switches"][0]['platform'] and \
                            have_c["switches"][0]['version'] == want_c["switches"][0]['version'] and \
                            have_c["switches"][0]['sysName'] == want_c["switches"][0]['sysName'] and \
                            have_c["switches"][0]['role'] == want_c['role']:
                        match_found = True

            return match_found

        for have_c in self.have_create:
            if have_in_want(have_c):
                continue
            else:
                diff_delete.append(have_c["switches"][0]['serialNumber'])

        self.diff_delete = diff_delete

    def get_diff_delete(self):

        diff_delete = []

        if self.config:
            for want_c in self.want_create:
                for have_c in self.have_create:
                    if (have_c["switches"][0]['ipaddr'] == want_c['seedIP']):
                        diff_delete.append(have_c["switches"][0]['serialNumber'])
                        continue

        else:
            for have_c in self.have_create:
                diff_delete.append(have_c["switches"][0]['serialNumber'])

        self.diff_delete = diff_delete

    def get_diff_merge(self):

        diff_create = []

        for want_c in self.want_create:
            found = False
            for have_c in self.have_create:
                match = re.search(r'\S+\((\S+)\)', want_c["switches"][0]['deviceIndex'])
                if match is None:
                    continue
                serial_num = match.groups()[0]
                if want_c["switches"][0]['ipaddr'] == have_c["switches"][0]['ipaddr'] and \
                        serial_num == have_c["switches"][0]['serialNumber'] \
                        and want_c["switches"][0]['platform'] == have_c["switches"][0]['platform'] and \
                        want_c["switches"][0]['version'] == have_c["switches"][0]['version'] \
                        and want_c["switches"][0]['sysName'] == have_c["switches"][0]['sysName'] \
                        and want_c['role'] == have_c["switches"][0]['role']:

                    found = True

                    if have_c["switches"][0]['mode'] == "Migration":
                        # Switch is already discovered using DCNM GUI
                        # Perform assign-role/config-save/config-deploy
                        self.node_migration = True
                        diff_create.append(want_c)
                        self.diff_create = diff_create

                        # Assign Role
                        self.assign_role()

                        for x in range(1, 5):
                            if not self.all_switches_ok():
                                time.sleep(300)
                            else:
                                break

                        # Config-save all switches
                        self.config_save()

                        # Config-deploy all switches
                        self.config_deploy()

            if not found:
                diff_create.append(want_c)

        self.diff_create = diff_create

    def validate_input(self):

        """Parse the playbook values, validate to param specs."""

        state = self.params['state']

        if state == 'merged' or state == 'overridden':

            inv_spec = dict(
                seed_ip=dict(required=True, type='str'),
                auth_proto=dict(type='str',
                                choices=['MD5', 'SHA', 'MD5_DES', 'MD5_AES', 'SHA_DES', 'SHA_AES'],
                                default='MD5'),
                user_name=dict(required=True, type='str', length_max=32),
                password=dict(required=True, type='str', no_log=True, length_max=32),
                max_hops=dict(type='int', default=0),
                role=dict(type='str',
                          choices=['leaf', 'spine', 'border', 'border_spine', 'border_gateway', 'border_gateway_spine',
                                   'super_spine', 'border_super_spine', 'border_gateway_super_spine'],
                          default='leaf'),
                preserve_config=dict(type='bool', default=False)
            )

            msg = None
            if self.config:
                for inv in self.config:
                    if 'seed_ip' not in inv or 'user_name' not in inv or 'password' not in inv:
                        msg = "seed ip/user name and password are mandatory under inventory parameters"

            else:
                if state == 'merged':
                    msg = "config: element is mandatory for this state {}".format(state)

            if msg:
                self.module.fail_json(msg=msg)

            if self.config:
                valid_inv, invalid_params = validate_list_of_dicts(self.config, inv_spec)
                for inv in valid_inv:
                    self.validated.append(inv)

                if invalid_params:
                    msg = 'Invalid parameters in playbook: {}'.format('\n'.join(invalid_params))
                    self.module.fail_json(msg=msg)

        elif state == 'deleted':

            inv_spec = dict(
                seed_ip=dict(required=True, type='str')
            )

            msg = None
            if self.config:
                for inv in self.config:
                    if 'seed_ip' not in inv:
                        msg = "seed ip is mandatory under inventory parameters for switch deletion"

            if msg:
                self.module.fail_json(msg=msg)

            if self.config:
                valid_inv, invalid_params = validate_list_of_dicts(self.config, inv_spec)
                for inv in valid_inv:
                    self.validated.append(inv)

                if invalid_params:
                    msg = 'Invalid parameters in playbook: {}'.format('\n'.join(invalid_params))
                    self.module.fail_json(msg=msg)

        else:

            inv_spec = dict(
                seed_ip=dict(type='str'),
                role=dict(type='str',
                          choices=['leaf', 'spine', 'border', 'border_spine', 'border_gateway', 'border_gateway_spine',
                                   'super_spine', 'border_super_spine', 'border_gateway_super_spine', 'None'],
                          default='None')
            )

            if self.config:
                valid_inv, invalid_params = validate_list_of_dicts(self.config, inv_spec)
                for inv in valid_inv:
                    self.validated.append(inv)

                if invalid_params:
                    msg = 'Invalid parameters in playbook: {}'.format('\n'.join(invalid_params))
                    self.module.fail_json(msg=msg)

    def import_switches(self):

        method = 'POST'
        path = '/rest/control/fabrics/{}'.format(self.fabric)
        create_path = path + '/inventory/discover?gfBlockingCall=true'

        if self.diff_create:
            for create in self.diff_create:
                import_response = dcnm_send(self.module, method, create_path, json.dumps(create))
                self.result['response'].append(import_response)
                fail, self.result['changed'] = self.handle_response(import_response, "create")
                if fail:
                    self.failure(import_response)

    def rediscover_switch(self, serial_num):

        method = 'POST'
        redisc_path = '/rest/control/fabrics/{}/inventory/rediscover/{}'.format(self.fabric, serial_num)
        response = dcnm_send(self.module, method, redisc_path)
        self.result['response'].append(response)
        fail, self.result['changed'] = self.handle_response(response, "create")
        if fail:
            self.failure(response)

    def rediscover_all_switches(self):

        # Get Fabric Inventory Details
        method = 'GET'
        inv_path = '/rest/control/fabrics/{}/inventory'.format(self.fabric)
        get_inv = dcnm_send(self.module, method, inv_path)
        missing_fabric, not_ok = self.handle_response(get_inv, 'query_dcnm')

        if missing_fabric or not_ok:
            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find inventories under fabric: {}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not get_inv.get('DATA'):
            return

        for inv in get_inv['DATA']:
            self.rediscover_switch(inv['serialNumber'])

    def all_switches_ok(self):

        all_ok = True
        # Get Fabric Inventory Details
        method = 'GET'
        inv_path = '/rest/control/fabrics/{}/inventory'.format(self.fabric)
        get_inv = dcnm_send(self.module, method, inv_path)
        missing_fabric, not_ok = self.handle_response(get_inv, 'query_dcnm')

        if missing_fabric or not_ok:
            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find inventories under fabric: {}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        for inv in get_inv['DATA']:
            if inv['status'] != "ok":
                all_ok = False
                self.rediscover_switch(inv['serialNumber'])

        return all_ok

    def set_lancred_switch(self, set_lan):

        method = 'POST'
        set_lan_path = '/fm/fmrest/lanConfig/saveSwitchCredentials'

        response = dcnm_send(self.module, method, set_lan_path, urlencode(set_lan))
        self.result['response'].append(response)
        fail, self.result['changed'] = self.handle_response(response, "create")
        if fail:
            self.failure(response)

    def lancred_all_switches(self):

        # Get Fabric Inventory Details
        method = 'GET'
        lan_path = '/fm/fmrest/lanConfig/getLanSwitchCredentials'
        get_lan = dcnm_send(self.module, method, lan_path)
        missing_fabric, not_ok = self.handle_response(get_lan, 'query_dcnm')

        if missing_fabric or not_ok:
            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
            msg2 = "Unable to getLanSwitchCredentials under fabric: {}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not get_lan.get('DATA'):
            return

        for create in self.want_create:
            for lan in get_lan['DATA']:
                if not lan['switchDbID']:
                    msg = "Unable to SWITCHDBID using getLanSwitchCredentials under fabric: {}".format(self.fabric)
                    self.module.fail_json(msg=msg)
                if lan['ipAddress'] == create["switches"][0]['ipaddr']:
                    set_lan = {
                        "switchIds": lan['switchDbID'],
                        "userName": create['username'],
                        "password": create['password'],
                        "v3Protocol": "0"
                    }
                    self.set_lancred_switch(set_lan)

    def assign_role(self):

        method = 'GET'
        inv_path = '/rest/control/fabrics/{}/inventory'.format(self.fabric)
        get_role = dcnm_send(self.module, method, inv_path)
        missing_fabric, not_ok = self.handle_response(get_role, 'query_dcnm')

        if missing_fabric or not_ok:
            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find inventories under fabric: {}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not get_role.get('DATA'):
            return

        for create in self.want_create:
            for role in get_role['DATA']:
                if not role['switchDbID']:
                    msg = "Unable to get SWITCHDBID using getLanSwitchCredentials under fabric: {}".format(self.fabric)
                    self.module.fail_json(msg=msg)
                if role['ipAddress'] == create["switches"][0]['ipaddr']:
                    method = 'PUT'
                    assign_path = '/fm/fmrest/topology/role/{}?newRole={}'.format(role['switchDbID'], create['role'])
                    response = dcnm_send(self.module, method, assign_path)
                    self.result['response'].append(response)
                    fail, self.result['changed'] = self.handle_response(response, "create")
                    if fail:
                        self.failure(response)

    def config_save(self):

        success = False
        no_of_tries = 3

        for x in range(0, no_of_tries):
            # Get Fabric ID
            method = 'GET'
            fid_path = '/rest/control/fabrics/{}'.format(self.fabric)
            get_fid = dcnm_send(self.module, method, fid_path)
            missing_fabric, not_ok = self.handle_response(get_fid, 'create_dcnm')

            if not get_fid.get('DATA'):
                return

            if not get_fid['DATA']['id']:
                msg = "Unable to find id for fabric: {}".format(self.fabric)
                self.module.fail_json(msg=msg)

            fabric_id = get_fid['DATA']['id']

            # config-save
            method = 'POST'
            path = '/rest/control/fabrics/{}'.format(self.fabric)
            save_path = path + '/config-save'
            response = dcnm_send(self.module, method, save_path)
            self.result['response'].append(response)
            fail, self.result['changed'] = self.handle_response(response, "create")
            if fail:
                self.failure(response)

            if response["RETURN_CODE"] != 200:

                # Get Fabric Errors
                method = 'GET'
                fiderr_path = '/rest/control/fabrics/{}/errors'.format(fabric_id)
                get_fiderr = dcnm_send(self.module, method, fiderr_path)
                missing_fabric, not_ok = self.handle_response(get_fiderr, 'query_dcnm')

                if missing_fabric or not_ok:
                    msg1 = "Fabric {} not present on DCNM".format(self.fabric)
                    msg2 = "Could not get any fabric errors for fabric: {}".format(self.fabric)
                    self.module.fail_json(msg=msg1 if missing_fabric else msg2)

            else:
                time.sleep(5)
                success = True
                break

            if not success and x in range(0, no_of_tries - 1):
                time.sleep(600)

    def config_deploy(self):

        # config-deploy
        method = 'POST'
        path = '/rest/control/fabrics/{}'.format(self.fabric)
        deploy_path = path + '/config-deploy'
        response = dcnm_send(self.module, method, deploy_path)
        self.result['response'].append(response)
        fail, self.result['changed'] = self.handle_response(response, "create")

        if fail:
            self.failure(response)

    def delete_switch(self):

        if self.diff_delete:
            method = 'DELETE'
            for sn in self.diff_delete:
                delete_path = '/rest/control/fabrics/{}/switches/{}'.format(self.fabric, sn)
                response = dcnm_send(self.module, method, delete_path)
                self.result['response'].append(response)
                fail, self.result['changed'] = self.handle_response(response, "delete")

                if fail:
                    self.failure(response)

    def get_diff_query(self):

        query = []

        method = 'GET'
        path = '/rest/control/fabrics/{}/inventory'.format(self.fabric)
        inv_objects = dcnm_send(self.module, method, path)
        missing_fabric, not_ok = self.handle_response(inv_objects, 'query_dcnm')

        if inv_objects.get('ERROR') == 'Not Found' and inv_objects.get('RETURN_CODE') == 404:
            self.module.fail_json(msg="Fabric {} not present on DCNM".format(self.fabric))
            return

        if missing_fabric or not_ok:
            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find inventories under fabric: {}".format(self.fabric)
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not inv_objects['DATA']:
            return

        if self.config:
            for want_c in self.want_create:
                for inv in inv_objects['DATA']:
                    if want_c['role'] == 'None' and want_c["seedIP"] != 'None':
                        if want_c["seedIP"] == inv['ipAddress']:
                            query.append(inv)
                            continue
                    elif want_c['role'] != 'None' and want_c["seedIP"] == 'None':
                        if want_c['role'] == inv['switchRole'].replace(" ", ""):
                            query.append(inv)
                            continue
                    else:
                        if want_c["seedIP"] == inv['ipAddress'] and \
                                want_c['role'] == inv['switchRole'].replace(" ", ""):
                            query.append(inv)
                            continue
        else:
            for inv in inv_objects['DATA']:
                query.append(inv)

        self.query = query

    def handle_response(self, res, op):

        fail = False
        changed = True

        if op == 'query_dcnm':
            # This if blocks handles responses to the query APIs against DCNM.
            # Basically all GET operations.
            if res.get('ERROR') == 'Not Found' and res['RETURN_CODE'] == 404:
                return True, False
            if res['RETURN_CODE'] != 200 or res['MESSAGE'] != 'OK':
                return False, True
            return False, False

        # Responses to all other operations POST and PUT are handled here.
        if res.get('MESSAGE') != 'OK':
            fail = True
            changed = False
            return fail, changed
        if res.get('ERROR'):
            fail = True
            changed = False

        return fail, changed

    def failure(self, resp):

        res = copy.deepcopy(resp)

        if not resp.get('DATA'):
            data = copy.deepcopy(resp.get('DATA'))
            if data.get('stackTrace'):
                data.update({'stackTrace': 'Stack trace is hidden, use \'-vvvvv\' to print it'})
                res.update({'DATA': data})

        self.module.fail_json(msg=res)


def main():
    """ main entry point for module execution
    """

    element_spec = dict(
        fabric=dict(required=True, type='str'),
        config=dict(required=False, type='list'),
        state=dict(default='merged',
                   choices=['merged', 'overridden', 'deleted', 'query'])
    )

    module = AnsibleModule(argument_spec=element_spec,
                           supports_check_mode=True)

    dcnm_inv = DcnmInventory(module)

    dcnm_inv.validate_input()
    dcnm_inv.get_want()
    dcnm_inv.get_have()

    if module.params['state'] == 'merged':
        dcnm_inv.get_diff_merge()

    if module.params['state'] == 'overridden':
        dcnm_inv.get_diff_override()

    if module.params['state'] == 'deleted':
        dcnm_inv.get_diff_delete()

    if module.params['state'] == 'query':
        dcnm_inv.get_diff_query()
        dcnm_inv.result['changed'] = False
        dcnm_inv.result['response'] = dcnm_inv.query

    if not dcnm_inv.diff_delete and module.params['state'] == 'deleted':
        dcnm_inv.result['changed'] = False
        dcnm_inv.result['response'] = "The switch provided is not part of the fabric and cannot be deleted"

    if not dcnm_inv.diff_create and module.params['state'] == 'merged':
        dcnm_inv.result['changed'] = False
        dcnm_inv.result['response'] = "The switch provided is already part of the fabric and cannot be created again"

    if not dcnm_inv.diff_create and not dcnm_inv.diff_delete and module.params['state'] == 'overridden':
        dcnm_inv.result['changed'] = False
        dcnm_inv.result[
            'response'] = "The switch provided is already part of the fabric and there is no more device to delete in the fabric"

    if not dcnm_inv.query and module.params['state'] == 'query':
        dcnm_inv.result['changed'] = False
        dcnm_inv.result['response'] = "The queried switch is not part of the fabric configured"

    if dcnm_inv.diff_create or dcnm_inv.diff_delete:
        dcnm_inv.result['changed'] = True
    else:
        module.exit_json(**dcnm_inv.result)

    if module.check_mode:
        module.exit_json(**dcnm_inv.result)

    # Delete Switch
    if dcnm_inv.diff_delete:
        # Step 1
        # Delete specific switch/all switch
        dcnm_inv.delete_switch()

    # Discover & Register Switch
    if not dcnm_inv.node_migration:

        if dcnm_inv.diff_create:

            # Step 1
            # Import all switches
            dcnm_inv.import_switches()

            # sleep for 2mins
            time.sleep(120)

            # Step 2
            # Rediscover all switches
            dcnm_inv.rediscover_all_switches()

            # sleep for 10mins
            time.sleep(600)

            # Step 3
            # Check all devices are up
            for x in range(1, 5):
                if not dcnm_inv.all_switches_ok():
                    time.sleep(300)
                else:
                    break

            # Step 4
            # Verify all devices came up finally
            if not dcnm_inv.all_switches_ok():
                msg = "Unable to make all the switches up after discover under fabric: {}".format(dcnm_inv.fabric)
                module.fail_json(msg=msg)

            # Step 5
            # Save LAN Credentials for each switch
            dcnm_inv.lancred_all_switches()

            # Step 6
            # Assign Role
            dcnm_inv.assign_role()

            # Step 7
            # Config-save all switches
            dcnm_inv.config_save()

            # Step 8
            # Config-deploy all switches
            dcnm_inv.config_deploy()

    module.exit_json(**dcnm_inv.result)


if __name__ == '__main__':
    main()
