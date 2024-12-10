#!/usr/bin/env python
#
# Copyright (c) 2024 Cisco and/or its affiliates.
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
__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import json
from os import environ

"""
# Summary

Dynamic inventory for DCNM Collection integration tests.
Inventory is built from environment variables.

# Usage

See README.md in the top-level of this repository and define the environment
variables described there appropriately for your environment.
"""
nd_role = environ.get("ND_ROLE", "dcnm_vrf")
nd_testcase = environ.get("ND_TESTCASE", "query")

fabric_1 = environ.get("ND_FABRIC_1")
nd_ip4 = environ.get("ND_IP4")
nd_password = environ.get("ND_PASSWORD")
nd_username = environ.get("ND_USERNAME", "admin")
nxos_password = environ.get("NXOS_PASSWORD")
nxos_username = environ.get("NXOS_USERNAME", "admin")

# Base set of switches
bgw_1 = environ.get("ND_BGW_1_IP4", "10.1.1.211")
bgw_2 = environ.get("ND_BGW_2_IP4", "10.1.1.212")
leaf_1 = environ.get("ND_LEAF_1_IP4", "10.1.1.106")
leaf_2 = environ.get("ND_LEAF_2_IP4", "10.1.1.107")
leaf_3 = environ.get("ND_LEAF_3_IP4", "10.1.1.108")
leaf_4 = environ.get("ND_LEAF_4_IP4", "10.1.1.109")
spine_1 = environ.get("ND_SPINE_1_IP4", "10.1.1.112")
spine_2 = environ.get("ND_SPINE_2_IP4", "10.1.1.113")

# Base set of interfaces
interface_1 = environ.get("ND_INTERFACE_1", "Ethernet1/1")
interface_2 = environ.get("ND_INTERFACE_2", "Ethernet1/2")
interface_3 = environ.get("ND_INTERFACE_3", "Ethernet1/3")

if nd_role == "dcnm_vrf":
    # VXLAN/EVPN Fabric Name
    # fabric_1
    #   - all tests
    # switch_1
    #   - all tests
    #     - vrf capable
    switch_1 = spine_1
    # switch_2
    #   - all tests
    #     - vrf-lite capable
    switch_2 = spine_2
    # switch_3
    #   - merged
    #     - NOT vrf-lite capable
    switch_3 = leaf_3
    # interface_1
    #   - no tests
    # interface_2
    #   - all tests
    #      - switch_2 VRF LITE extensions
    # interface_3
    #   - merged
    #     - switch_3 non-vrf-lite capable switch
    #   - overridden
    #     - Removed from test due to unrelated IP POOL errors.
    #     - It appears that fabric would need to have SUBNET
    #       resource added?
    # 
elif nd_role == "vrf_lite":
    # VXLAN/EVPN Fabric Name
    # Uses fabric_1
    # switch_1: vrf-lite capable
    switch_1 = spine_1
    # switch_2: vrf-lite capable
    switch_2 = spine_2
    # switch_3: vrf-lite capable
    switch_3 = bgw_1
    interface_1 = interface_1
    interface_2 = interface_2
    interface_3 = interface_3
else:
    switch_1 = leaf_1
    switch_2 = spine_1
    switch_3 = bgw_1

# output is printed to STDOUT, where ansible-playbook -i reads it.
# If you change any vars above, be sure to add them below.
# We'll clean this up as the integration test vars are standardized.

output = {
    "_meta": {"hostvars": {}},
    "all": {
        "children": ["ungrouped", "dcnm", "ndfc", "nxos"],
        "vars": {
            "ansible_httpapi_use_ssl": "true",
            "ansible_httpapi_validate_certs": "false",
            "ansible_password": nd_password,
            "ansible_python_interpreter": "python",
            "ansible_user": nd_username,
            "fabric_1": fabric_1,
            "bgw1": bgw_1,
            "bgw2": bgw_2,
            "leaf1": leaf_1,
            "leaf2": leaf_2,
            "leaf_1": leaf_1,
            "leaf_2": leaf_2,
            "leaf3": leaf_3,
            "leaf4": leaf_4,
            "nxos_username": nxos_username,
            "nxos_password": nxos_password,
            "switch_password": nxos_password,
            "switch_username": nxos_username,
            "spine1": spine_1,
            "spine2": spine_2,
            "switch1": switch_1,
            "switch2": switch_2,
            "switch_1": switch_1,
            "switch_2": switch_2,
            "switch_3": switch_3,
            "interface_1": interface_1,
            "interface_2": interface_2,
            "interface_3": interface_3,
            "testcase": nd_testcase
        },
    },
    "dcnm": {
        "hosts": [nd_ip4],
        "vars": {
            "ansible_connection": "ansible.netcommon.httpapi",
            "ansible_network_os": "cisco.dcnm.dcnm",
        },
    },
    "ndfc": {
        "hosts": [nd_ip4],
        "vars": {
            "ansible_connection": "ansible.netcommon.httpapi",
            "ansible_network_os": "cisco.dcnm.dcnm",
        },
    },
    "nxos": {
        "children": [
            "bgw1",
            "bgw2",
            "leaf_1",
            "leaf_2",
            "leaf1",
            "leaf2",
            "leaf3",
            "leaf4",
            "spine1",
            "spine2",
            "switch1",
            "switch2",
        ],
        "vars": {
            "ansible_become": "true",
            "ansible_become_method": "enable",
            "ansible_connection": "ansible.netcommon.httpapi",
            "ansible_network_os": "cisco.nxos.nxos",
        },
    },
    "bgw1": {"hosts": [bgw_1]},
    "bgw2": {"hosts": [bgw_2]},
    "leaf_1": {"hosts": [leaf_1]},
    "leaf_2": {"hosts": [leaf_2]},
    "leaf1": {"hosts": [leaf_1]},
    "leaf2": {"hosts": [leaf_2]},
    "leaf3": {"hosts": [leaf_3]},
    "leaf4": {"hosts": [leaf_4]},
    "spine1": {"hosts": [spine_1]},
    "spine2": {"hosts": [spine_2]},
    "switch1": {"hosts": [switch_1]},
    "switch2": {"hosts": [switch_2]},
}

print(json.dumps(output))
