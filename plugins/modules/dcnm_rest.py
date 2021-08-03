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

__author__ = "Mike Wiebe"

DOCUMENTATION = '''
---
module: dcnm_rest
short_description: Send REST API requests to DCNM controller.
version_added: "0.9.0"
description:
    - "Send REST API requests to DCNM controller."
options:
  method:
    description:
    - 'REST API Method'
    required: yes
    type: str
    choices: ['GET', 'POST', 'PUT', 'DELETE']
  path:
    description:
    - 'REST API Path Endpoint'
    required: yes
    type: str
  json_data:
    description:
    - 'Additional JSON data to include with the REST API call'
    required: no
    type: raw
author:
    - Mike Wiebe (@mikewiebe)
'''

EXAMPLES = '''
# This module can be used to send any REST API requests that are supported by
# the DCNM controller.
#
# This module is not idempotent but can be used as a stop gap until a feature
# module can be developed for the target DCNM functionality.

- name: Gather List of Fabrics from DCNM
  dcnm_rest:
    method: GET
    path: /rest/control/fabrics
'''

RETURN = '''
response:
    description:
    - Success or Error Data retrieved from DCNM
    returned: always
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
    if res and res['RETURN_CODE'] >= 400:
        module.fail_json(msg=res)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
