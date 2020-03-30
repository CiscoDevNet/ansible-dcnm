#!/usr/bin/python
# -*- coding: utf-8 -*-
"""dcnm_interface module
Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.0 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

__copyright__ = "Copyright (c) 2019 Cisco and/or its affiliates."
__author__ = "Mike Wiebe"

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: dcnm_interface
short_description: DCNM Ansible Module for managing interfaces.
version_added: "2.10"
description:
    - "DCNM Ansible Module for the following interface service operations"
    - "Create, Delete, Modify PortChannel, VPC, Loopback and Sub-Interfaces"
    - "Modify Ethernet Interfaces"
options:
  fabric:
    description:
    - 'Name of the target fabric for interface operations'
    type: str
    required: true
  config:
    description: A dictionary of interface operations
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Full name of the interface. Example, PortChannel55, Ethernet2/1.
        type: str
        required: true
      switch:
        description:
          - IP address or DNS name of the management interface.
        type: list
        required: true
      type: #TBD We should be able to get this from the name?
        description:
          - Interface type. Example, pc, vpc, sub_int, lo
        type: str
        required: true
        choices: ['pc', 'vpc', 'sub_int', 'lo']
      mode:
        description:
          - Interface port mode.
        type: str
        required: true
        choices: ['trunk', 'access', 'mirror', 'routed']
      profile:
        description:
          - Interface profile.
        # TBD: Fill in more later
author:
    - Mike Wiebe (@mikewiebe)
'''

EXAMPLES = '''
- name: Create Interace Object in DCNM
  dcnm_interface:
    # TBD
'''

RETURN = '''
response:
    description: Success or Error Data retrieved from DCNM
    type: list
    elements: dict
'''

import json
from textwrap import dedent

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.common.utils import dict_diff
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import get_fabric_inventory_details

import datetime
def logit(msg):
    with open('/tmp/logit.txt', 'a') as of:
        of.write("\n---- _network: %s\n" % (msg))


def send(facts, method, path, payload=None):
    logit('send: path: %s' %path)
    if payload:
        resp = facts['conn'].send_request(method, path, payload)
    else:
        resp = facts['conn'].send_request(method, path)
    if isinstance(resp, dict):
        return resp
    elif isinstance(resp, list):
        return resp[0]
    else:
        logit('#### send: exception: %s' %resp)
        raise Exception('foo')


def validate_playbook(facts):
    """ Validate playbook entries, set defaults, normalize the 'want' data. """
    pass


def populate_facts(facts):
    """Check for existing interfaces objects and states.
    ** facts db structure: facts[have|want][netwrk1,netwrk2,...][net|att]
    """
    # GET all interfaces
    path = '/rest/interface/detail?serialNumber=FOX1821H035'
    all_int_raw = send(facts, 'GET', path)

    return all_int_raw


def get_diffs(facts):
    """ Create diffs for each network in 'want'
    """
    pass


def merged(facts):
    """ Check for non-idempotent networks, create payloads, update DCNM.
    """
    # Use bulk-create for all new networks, use PUT networks for updates.

    # TBD: check_mode
    fabric = facts['fabric']
    have = facts['have']
    want = facts['want']
    diff = facts['diff']
    config = facts['config'][0]

    # Merge want interfaces with have interfaces.
    # path = '/rest/interface'
    # payload = {}
    # payload['policy'] = 'int_loopback_11_1'
    # payload['interfaceType'] = 'INTERFACE_LOOPBACK'
    # payload['interfaces'] = [{
    #     'serialNumber': 'FOX1821H035',
    #     'interfaceType': 'INTERFACE_LOOPBACK',
    #     'ifName': 'Loopback55',
    #     'fabricName': 'wiebe55',
    #     'nvPairs': {
    #         'INTF_VRF': '',
    #         'IP': '192.168.55.55',
    #         'V6IP': '',
    #         'ROUTE_MAP_TAG': '12345',
    #         'DESC': 'mike_manual_int',
    #         'CONF': '',
    #         'ADMIN_STATE': True,
    #         'INTF_NAME': 'Loopback55'
    #     }
    # }]

    path = '/rest/interface'
    payload = {}
    payload['policy'] = 'int_loopback_11_1'
    payload['interfaceType'] = 'INTERFACE_LOOPBACK'
    payload['interfaces'] = [{
        'serialNumber': facts['inventory'].get(config['switch'][0]),
        'interfaceType': 'INTERFACE_LOOPBACK',
        'ifName': config['name'],
        'fabricName': fabric,
        'nvPairs': {
            'INTF_VRF': '',
            'IP': config['profile']['ipv4_addr'],
            'V6IP': '',
            'ROUTE_MAP_TAG': config['profile']['route_map_tag'],
            'DESC': config['profile']['descr'],
            'CONF': '',
            'ADMIN_STATE': config['profile']['admin_state'],
            'INTF_NAME': config['name']
        }
    }]
    json_payload = json.dumps(payload)

    resp = send(facts, 'POST', path, json_payload)

    return resp


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        fabric=dict(required=True, type='str'),
        config=dict(required=True, type=list),
        state=dict(type='str', default='merged'),
    )
    module = AnsibleModule(argument_spec=element_spec,
                           # required_one_of=required_one_of,
                           # mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)
    facts = {
        'conn': Connection(module._socket_path),
        'fabric': module.params['fabric'],
        'config': module.params['config'],
        'have': {},  # Normalized data below...
        'want': {},
        'diff': {},
    }

    facts['inventory'] = get_fabric_inventory_details(module, facts['fabric'])

    validate_playbook(facts)
    populate_facts(facts)
    get_diffs(facts)
    resp = merged(facts)

    import epdb ; epdb.serve()

    if resp['RETURN_CODE'] >= 400:
        module.fail_json(msg=resp)

    result = dict(changed=False, response=dict())
    module.exit_json(**result)


if __name__ == '__main__':
    main()
