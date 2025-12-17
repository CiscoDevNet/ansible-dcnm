#!/usr/bin/python
#
# Copyright (c) 2020-2022 Cisco and/or its affiliates.
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

from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Mike Wiebe"

DOCUMENTATION = """
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
  data:
    description:
    - 'Additional data in JSON or TEXT to include with the REST API call'
    aliases:
    - json_data
    required: no
    type: raw
  urlencoded_data:
    description:
    - 'Dictionary data to be url-encoded for x-www-form-urlencoded type REST API call'
    required: no
    type: raw
author:
    - Mike Wiebe (@mikewiebe)
"""

EXAMPLES = """
# This module can be used to send any REST API requests that are supported by
# the DCNM controller.
#
# This module is not idempotent but can be used as a stop gap until a feature
# module can be developed for the target DCNM functionality.

- name: Gather List of Fabrics from DCNM
  dcnm_rest:
    method: GET
    path: /rest/control/fabrics

- name: Set deployment to false in lanAttachList for vrf
  dcnm_rest:
    method: POST
    path: /rest/top-down/fabrics/fabric1/vrfs/attachments
    json_data: >
      [{"vrfName":"sales66_vrf1","lanAttachList":[{"fabric":"fabric1","vrfName":"sales66_vrf1",
      "serialNumber":"FDO21392QKM","vlan":2000,"freeformConfig":"","deployment":false,
      "extensionValues":"","instanceValues":"{\"loopbackId\":\"\",\"loopbackIpAddress\":\"\",\"loopbackIpV6Address\":\"\"}"}]}]

- name: Save Robot Credentials - (urlencoded)
  dcnm_rest:
    method: POST
    path: /rest/lanConfig/saveRobotCredentials
    urlencoded_data: '{"password": "password", "username": "admin"}'

# Read payload data from file and validate a template
- set_fact:
    data: "{{ lookup('file', 'validate_payload') }}"

- name: Validate a template
  cisco.dcnm.dcnm_rest:
    method: POST
    path: /fm/fmrest/config/templates/validate
    json_data: "{{ data }}"
    register: result
"""  # noqa

RETURN = """
response:
    description:
    - Success or Error Data retrieved from DCNM
    returned: always
    type: list
    elements: dict
"""

import json
import urllib.parse
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
)


def main():
    # define available arguments/parameters a user can pass to the module
    argument_spec = dict(
        method=dict(required=True, choices=["GET", "POST", "PUT", "DELETE"]),
        path=dict(required=True, type="str"),
        data=dict(type="raw", required=False, default=None, aliases=["json_data"]),
        urlencoded_data=dict(type="raw", required=False, default=None),
    )

    # seed the result dict
    result = dict(changed=False, response=dict())

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    method = module.params["method"]
    path = module.params["path"]
    is_urlencoded = False

    for key in ["json_data", "data", "urlencoded_data"]:
        data = module.params.get(key)
        if data is not None:
            if key == "urlencoded_data":
                is_urlencoded = True
            break
    if data is None:
        data = "{}"

    # Determine if this is valid JSON or not
    try:
        json_data = json.loads(data)
        if is_urlencoded:
            # If the data is valid JSON but marked as urlencoded, we need to convert it
            # to a URL-encoded string before sending it.
            urlencoded_data = urllib.parse.urlencode(json_data)
            result["response"] = dcnm_send(module, method, path, urlencoded_data, "urlencoded")
        else:
            # If the data is valid JSON, send it as a JSON string
            result["response"] = dcnm_send(module, method, path, data)
    except json.JSONDecodeError:
        # Resend data as text since it's not valid JSON
        result["response"] = dcnm_send(module, method, path, data, "text")

    if result["response"]["RETURN_CODE"] >= 400:
        module.fail_json(msg=result["response"])

    module.exit_json(**result)


if __name__ == "__main__":
    main()
