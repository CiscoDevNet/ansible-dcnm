#!/usr/bin/python
# -*- coding: utf-8 -*-
"""dcnm_rest module
Copyright (c) 2019 Cisco and/or its affiliates.
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
__license__ = "Cisco Sample Code License, Version 1.0"
__author__ = "Mike Wiebe"

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: dcnm_rest
short_description: Send REST API requests to DCNM controller.
version_added: "2.10"
description:
    - "Send REST API requests to DCNM controller."
options:
  method:
    description:
    - 'REST API Method'
    required: yes
    choices: ['GET', 'POST', 'PUT', 'DELETE']
  path:
    description:
    - 'REST API Path Endpoint'
    required: yes
  json_data:
    description:
    - 'Additional JSON data to include with the REST API call'
    required: no
author:
    - Mike Wiebe (@mikewiebe)
'''

EXAMPLES = '''
- name: Gather List of Fabrics from DCNM
  dcnm_rest:
    method: GET
    path: /rest/control/fabrics
'''

RETURN = '''
response:
    description: Success or Error Data retrieved from DCNM
    type: list
    elements: dict
'''

from ansible.module_utils.connection import Connection
from ansible.module_utils.basic import AnsibleModule


def main():
    # define available arguments/parameters a user can pass to the module
    argument_spec = dict(
        method=dict(required=True, choices=['GET', 'POST', 'PUT', 'DELETE']),
        path=dict(required=True, type='str'),
        json_data=dict(type='raw', required=False, default=None))

    # seed the result dict
    result = dict(
        changed=False,
        response=dict()
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    method = module.params['method']
    path = module.params['path']
    json_data = {}
    if module.params['json_data'] is not None:
        json_data = module.params['json_data']

    conn = Connection(module._socket_path)
    result['response'] = conn.send_request(method, path, json_data)

    res = result['response']
    if res and isinstance(res, list) and res[0].get('ERROR'):
        module.fail_json(msg=res)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
