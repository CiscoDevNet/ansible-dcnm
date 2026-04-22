#!/usr/bin/python
#
# Copyright (c) 2026 Cisco and/or its affiliates.
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
__author__ = "Slawomir Kaszlikowski"

DOCUMENTATION = """
---
module: dcnm_acl
short_description: Manage Access Control Lists (ACLs) on Nexus Dashboard
version_added: "1.0"
description:
    - This module manages Access Control Lists (ACLs) on Nexus Dashboard (ND).
    - It supports creating, updating, deleting, and querying IPv4 and IPv6 ACLs.
    - Requires ND 4.1 or later; build_version: 4.1.x +
author: Slawomir Kaszlikowski
options:
  fabric:
    description:
    - Name of the target fabric for ACL operations.
    type: str
    required: true

  state:
    description:
    - The required state of the configuration after module completion.
    - C(merged) - ACLs defined in the playbook will be merged into the fabric.
      If an ACL exists, its entries will be merged. If it does not exist, it will be created.
    - C(replaced) - ACLs defined in the playbook will replace existing ACLs.
      If an ACL exists, it will be completely replaced. If it does not exist, it will be created.
    - C(deleted) - ACLs defined in the playbook will be deleted from the fabric.
      If no config is provided, all ACLs in the fabric will be deleted.
    - C(query) - Returns the current ND state for the ACLs listed in the playbook.
      If no config is provided, all ACLs in the fabric will be returned.
    type: str
    required: false
    choices:
      - merged
      - replaced
      - deleted
      - query
    default: merged

  config:
    description:
    - A list of dictionaries containing ACL configurations.
    type: list
    elements: dict
    default: []
    suboptions:
      name:
        description:
        - Name of the ACL.
        - Must be 1-63 characters, containing only alphanumeric characters, underscores, and hyphens.
        type: str
        required: true

      type:
        description:
        - Type of the ACL.
        - C(ipv4) for IPv4 Access Control Lists.
        - C(ipv6) for IPv6 Access Control Lists.
        type: str
        required: true
        choices:
          - ipv4
          - ipv6

      entries:
        description:
        - List of ACL entries (Access Control Entries).
        - Each entry can be a permit, deny, or remark entry.
        type: list
        elements: dict
        default: []
        suboptions:
          sequence_number:
            description:
            - Sequence number of the ACL entry.
            - Must be between 1 and 4294967295.
            type: int
            required: true

          action:
            description:
            - Action for this ACL entry.
            - C(permit) - Allow matching traffic.
            - C(deny) - Deny matching traffic.
            - C(remark) - Add a comment/remark entry.
            type: str
            required: true
            choices:
              - permit
              - deny
              - remark

          remark_comment:
            description:
            - Comment text for remark entries.
            - Required when action is C(remark).
            - Maximum 100 characters.
            type: str

          protocol:
            description:
            - IP protocol to match.
            - Required when action is C(permit) or C(deny).
            - Common values include ip, ipv6, tcp, udp, icmp, igmp, eigrp, ospf, pim, ahp, gre, nos, esp.
            - Use C(custom) to specify a custom protocol number.
            type: str
            choices:
              - ip
              - ipv6
              - tcp
              - udp
              - icmp
              - igmp
              - eigrp
              - ospf
              - pim
              - ahp
              - gre
              - nos
              - esp
              - custom

          custom_protocol:
            description:
            - Custom protocol number when protocol is set to C(custom).
            - Must be between 0 and 255.
            type: int

          src:
            description:
            - Source address specification.
            - Can be C(any), a host address (e.g., C(host 10.1.1.1)) or C(2001:db8::/32) for IPv6).
            - Required when action is C(permit) or C(deny).
            type: str

          dst:
            description:
            - Destination address specification.
            - Can be C(any), a host address (e.g., C(host 10.1.1.1)) for IPv4 or C(2001:db8::/32) for IPv6).
            - Required when action is C(permit) or C(deny).
            type: str

          src_port_action:
            description:
            - Source port matching action for TCP/UDP protocols.
            - C(none) - No source port filtering.
            - C(equal_to) - Match packets with source port equal to src_port.
            - C(greater_than) - Match packets with source port greater than src_port.
            - C(less_than) - Match packets with source port less than src_port.
            - C(not_equal_to) - Match packets with source port not equal to src_port.
            - C(port_range) - Match packets with source port in range src_port_range_start to src_port_range_end.
            type: str
            choices:
              - none
              - equal_to
              - greater_than
              - less_than
              - not_equal_to
              - port_range
            default: none

          src_port:
            description:
            - Source port number for TCP/UDP when src_port_action is equal_to, greater_than, less_than, or not_equal_to.
            - Must be between 0 and 65535.
            type: int

          src_port_range_start:
            description:
            - Start of source port range when src_port_action is C(port_range).
            - Must be between 0 and 65535.
            type: int

          src_port_range_end:
            description:
            - End of source port range when src_port_action is C(port_range).
            - Must be between 0 and 65535.
            type: int

          dst_port_action:
            description:
            - Destination port matching action for TCP/UDP protocols.
            - C(none) - No destination port filtering.
            - C(equal_to) - Match packets with destination port equal to dst_port.
            - C(greater_than) - Match packets with destination port greater than dst_port.
            - C(less_than) - Match packets with destination port less than dst_port.
            - C(not_equal_to) - Match packets with destination port not equal to dst_port.
            - C(port_range) - Match packets with destination port in range dst_port_range_start to dst_port_range_end.
            type: str
            choices:
              - none
              - equal_to
              - greater_than
              - less_than
              - not_equal_to
              - port_range
            default: none

          dst_port:
            description:
            - Destination port number for TCP/UDP when dst_port_action is equal_to, greater_than, less_than, or not_equal_to.
            - Must be between 0 and 65535.
            type: int

          dst_port_range_start:
            description:
            - Start of destination port range when dst_port_action is C(port_range).
            - Must be between 0 and 65535.
            type: int

          dst_port_range_end:
            description:
            - End of destination port range when dst_port_action is C(port_range).
            - Must be between 0 and 65535.
            type: int

          icmp_option:
            description:
            - ICMP message type to match when protocol is C(icmp).
            - Examples include echo, echo-reply, unreachable, redirect, etc.
            type: str

          tcp_option:
            description:
            - TCP flags option when protocol is C(tcp).
            - Examples include established, syn, ack, fin, rst, etc.
            type: str
"""

EXAMPLES = """
# States:
# This module supports the following states:
#
# Merged:
#   ACLs defined in the playbook will be merged into the target fabric.
#   - If an ACL does not exist, it will be created.
#   - If an ACL exists, entries will be merged (existing entries preserved, new entries added).
#
# Replaced:
#   ACLs defined in the playbook will replace existing ACLs.
#   - If an ACL does not exist, it will be created.
#   - If an ACL exists, it will be completely replaced with the playbook definition.
#
# Deleted:
#   ACLs defined in the playbook will be deleted from the fabric.
#   - If no config is provided, all ACLs in the fabric will be deleted.
#
# Query:
#   Returns the current state of ACLs from ND.
#   - If config is provided, only those ACLs are returned.
#   - If no config is provided, all ACLs in the fabric are returned.

# Create a simple IPv4 ACL with permit and deny entries
- name: Create IPv4 ACL
  cisco.dcnm.dcnm_acl:
    fabric: "{{ fabric_name }}"
    state: merged
    config:
      - name: my-ipv4-acl
        type: ipv4
        entries:
          - sequence_number: 10
            action: remark
            remark_comment: "Allow web traffic"
          - sequence_number: 20
            action: permit
            protocol: tcp
            src: any
            dst: 10.1.1.0 0.0.0.255
            dst_port_action: equal_to
            dst_port: 80
          - sequence_number: 30
            action: permit
            protocol: tcp
            src: any
            dst: 10.1.1.0 0.0.0.255
            dst_port_action: equal_to
            dst_port: 443
          - sequence_number: 100
            action: deny
            protocol: ip
            src: any
            dst: any

# Create an IPv6 ACL
- name: Create IPv6 ACL
  cisco.dcnm.dcnm_acl:
    fabric: "{{ fabric_name }}"
    state: merged
    config:
      - name: my-ipv6-acl
        type: ipv6
        entries:
          - sequence_number: 10
            action: permit
            protocol: tcp
            src: any
            dst: 2001:db8::/32
            dst_port_action: port_range
            dst_port_range_start: 80
            dst_port_range_end: 443
          - sequence_number: 20
            action: deny
            protocol: ip
            src: any
            dst: any

# Create ACL with TCP options
- name: Create ACL with TCP established
  cisco.dcnm.dcnm_acl:
    fabric: "{{ fabric_name }}"
    state: merged
    config:
      - name: tcp-established-acl
        type: ipv4
        entries:
          - sequence_number: 10
            action: permit
            protocol: tcp
            src: any
            dst: any
            tcp_option: established

# Create ACL with ICMP options
- name: Create ACL for ICMP
  cisco.dcnm.dcnm_acl:
    fabric: "{{ fabric_name }}"
    state: merged
    config:
      - name: icmp-acl
        type: ipv4
        entries:
          - sequence_number: 10
            action: permit
            protocol: icmp
            src: any
            dst: any
            icmp_option: echo
          - sequence_number: 20
            action: permit
            protocol: icmp
            src: any
            dst: any
            icmp_option: echo-reply

# Replace an existing ACL completely
- name: Replace ACL
  cisco.dcnm.dcnm_acl:
    fabric: "{{ fabric_name }}"
    state: replaced
    config:
      - name: my-ipv4-acl
        type: ipv4
        entries:
          - sequence_number: 10
            action: permit
            protocol: ip
            src: 192.168.1.0 0.0.0.255
            dst: any

# Delete specific ACLs
- name: Delete specific ACLs
  cisco.dcnm.dcnm_acl:
    fabric: "{{ fabric_name }}"
    state: deleted
    config:
      - name: my-ipv4-acl
      - name: my-ipv6-acl

# Delete all ACLs in fabric
- name: Delete all ACLs
  cisco.dcnm.dcnm_acl:
    fabric: "{{ fabric_name }}"
    state: deleted

# Query specific ACLs
- name: Query specific ACLs
  cisco.dcnm.dcnm_acl:
    fabric: "{{ fabric_name }}"
    state: query
    config:
      - name: my-ipv4-acl

# Query all ACLs in fabric
- name: Query all ACLs
  cisco.dcnm.dcnm_acl:
    fabric: "{{ fabric_name }}"
    state: query
"""

RETURN = """
response:
  description: Response from ND API calls.
  type: list
  elements: dict
  returned: always

diff:
  description: Diff information showing what changed.
  type: list
  elements: dict
  returned: always

changed:
  description: Whether any changes were made.
  type: bool
  returned: always

failed:
  description: Whether the module execution failed.
  type: bool
  returned: always

acls:
  description: List of ACLs returned for query state.
  type: list
  elements: dict
  returned: when state is query
  contains:
    name:
      description: Name of the ACL.
      type: str
    type:
      description: Type of the ACL (ipv4 or ipv6).
      type: str
    entries:
      description: List of ACL entries.
      type: list
      elements: dict
"""

import json
import re
import copy

from ansible.module_utils.basic import AnsibleModule

# dcnm_version_supported() requires update to support ND 4.1+
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    validate_list_of_dicts,
    dcnm_version_supported,
)


class DcnmAcl:
    """Class to manage Access Control Lists on ND"""

    # API paths for ACL operations - only supporting ND 4.1+

    dcnm_acl_paths = {
        12: {
            "ACL_LIST": "/api/v1/manage/fabrics/{}/accessControlLists",
            "ACL_GET": "/api/v1/manage/fabrics/{}/accessControlLists/{}",
            "ACL_CREATE": "/api/v1/manage/fabrics/{}/accessControlLists",
            "ACL_UPDATE": "/api/v1/manage/fabrics/{}/accessControlLists/{}",
            "ACL_DELETE": "/api/v1/manage/fabrics/{}/accessControlLists/{}",
        },
    }

    # Parameter name mapping from Ansible (snake_case) to API (camelCase)
    PARAM_TO_API_MAP = {
        "sequence_number": "sequenceNumber",
        "src_port_action": "srcPortAction",
        "src_port": "srcPort",
        "src_port_range_start": "srcPortRangeStart",
        "src_port_range_end": "srcPortRangeEnd",
        "dst_port_action": "dstPortAction",
        "dst_port": "dstPort",
        "dst_port_range_start": "dstPortRangeStart",
        "dst_port_range_end": "dstPortRangeEnd",
        "custom_protocol": "customProtocol",
        "icmp_option": "icmpOption",
        "tcp_option": "tcpOption",
        "remark_comment": "remarkComment",
    }

    # Reverse mapping from API to Ansible
    API_TO_PARAM_MAP = {v: k for k, v in PARAM_TO_API_MAP.items()}

    # Port action mapping from Ansible to API values
    PORT_ACTION_TO_API = {
        "equal_to": "equalTo",
        "greater_than": "greaterThan",
        "less_than": "lessThan",
        "not_equal_to": "notEqualTo",
        "port_range": "portRange",
        "none": "none",
    }

    # Reverse mapping from API to Ansible
    API_TO_PORT_ACTION = {v: k for k, v in PORT_ACTION_TO_API.items()}

    def __init__(self, module):
        """Initialize the DcnmAcl class."""
        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        self.state = module.params["state"]
        self.config = copy.deepcopy(module.params.get("config", []))
        self.check_mode = module.check_mode

        # State tracking lists
        self.want = []  # Desired state from playbook
        self.have = []  # Current state from ND
        self.diff_create = []  # ACLs to create
        self.diff_replace = []  # ACLs to replace/update
        self.diff_delete = []  # ACLs to delete
        self.diff_query = []  # ACLs to query

        # Result tracking
        self.result = dict(
            changed=False,
            diff=[],
            response=[],
            acls=[],
        )
        self.changed_dict = [
            {
                "merged": [],
                "replaced": [],
                "deleted": [],
                "query": [],
            }
        ]

        # Get ND version (the current dcnm_version_supported() doesn't works with ND 4.x)
        self.dcnm_version = dcnm_version_supported(self.module)

        # Verify minimum version (must be 12+)
        if self.dcnm_version < 12:
            self.module.fail_json(
                msg="dcnm_acl module requires ND 4.1 or later. "
                f"Detected version: {self.dcnm_version}"
            )

        self.paths = self.dcnm_acl_paths[12]

    def validate_input(self):
        """Validate the playbook input configuration."""
        if not self.config:
            # Empty config is valid for delete/query (means all ACLs)
            if self.state in ["deleted", "query"]:
                return
            else:
                self.module.fail_json(
                    msg="config is required for state 'merged' and 'replaced'"
                )

        # Validation spec for ACL
        acl_spec = dict(
            name=dict(required=True, type="str", length_max=63),
            type=dict(required=False, type="str", choices=["ipv4", "ipv6"]),
            entries=dict(required=False, type="list", default=[]),
        )

        # Validation spec for ACL entries
        entry_spec = dict(
            sequence_number=dict(
                required=True, type="int", range_min=1, range_max=2147483647
            ),
            action=dict(
                required=True, type="str", choices=["permit", "deny", "remark"]
            ),
            remark_comment=dict(required=False, type="str", length_max=100),
            protocol=dict(
                required=False,
                type="str",
                choices=[
                    "ip",
                    "ipv6",
                    "tcp",
                    "udp",
                    "icmp",
                    "igmp",
                    "eigrp",
                    "ospf",
                    "pim",
                    "ahp",
                    "gre",
                    "nos",
                    "esp",
                    "custom",
                ],
            ),
            custom_protocol=dict(
                required=False, type="int", range_min=0, range_max=255
            ),
            src=dict(required=False, type="str"),
            dst=dict(required=False, type="str"),
            src_port_action=dict(
                required=False,
                type="str",
                choices=[
                    "none",
                    "equal_to",
                    "greater_than",
                    "less_than",
                    "not_equal_to",
                    "port_range",
                ],
            ),
            src_port=dict(required=False, type="int", range_min=0, range_max=65535),
            src_port_range_start=dict(
                required=False, type="int", range_min=0, range_max=65535
            ),
            src_port_range_end=dict(
                required=False, type="int", range_min=0, range_max=65535
            ),
            dst_port_action=dict(
                required=False,
                type="str",
                choices=[
                    "none",
                    "equal_to",
                    "greater_than",
                    "less_than",
                    "not_equal_to",
                    "port_range",
                ],
            ),
            dst_port=dict(required=False, type="int", range_min=0, range_max=65535),
            dst_port_range_start=dict(
                required=False, type="int", range_min=0, range_max=65535
            ),
            dst_port_range_end=dict(
                required=False, type="int", range_min=0, range_max=65535
            ),
            icmp_option=dict(required=False, type="str"),
            tcp_option=dict(required=False, type="str"),
        )

        for acl in self.config:
            # Validate ACL-level parameters
            acl_list = [acl]
            invalid_params = validate_list_of_dicts(acl_list, acl_spec)
            if invalid_params:
                self.module.fail_json(
                    msg=f"Invalid parameters in ACL '{acl.get('name', 'unknown')}': {invalid_params}"
                )

            # Validate ACL name format
            name = acl.get("name", "")
            if not re.match(r"^[a-zA-Z0-9_-]+$", name):
                self.module.fail_json(
                    msg=f"ACL name '{name}' is invalid. Must contain only alphanumeric characters, "
                    "underscores, and hyphens."
                )

            # For merged/replaced, type is required
            if self.state in ["merged", "replaced"]:
                if not acl.get("type"):
                    self.module.fail_json(
                        msg=f"ACL '{name}': 'type' is required for state '{self.state}'"
                    )

            # Validate entries
            entries = acl.get("entries", [])
            if entries:
                invalid_params = validate_list_of_dicts(entries, entry_spec)
                if invalid_params:
                    self.module.fail_json(
                        msg=f"Invalid parameters in entries for ACL '{name}': {invalid_params}"
                    )

                # Additional entry-level validation
                for entry in entries:
                    self._validate_entry(name, entry)

    def _validate_entry(self, acl_name, entry):
        """Validate a single ACL entry."""
        action = entry.get("action")
        seq_num = entry.get("sequence_number")

        if action == "remark":
            # Remark entries require remark_comment
            if not entry.get("remark_comment"):
                self.module.fail_json(
                    msg=f"ACL '{acl_name}' entry {seq_num}: 'remark_comment' is required for remark entries"
                )
        else:
            # Permit/deny entries require protocol, src, dst
            if not entry.get("protocol"):
                self.module.fail_json(
                    msg=f"ACL '{acl_name}' entry {seq_num}: 'protocol' is required for permit/deny entries"
                )
            if not entry.get("src"):
                self.module.fail_json(
                    msg=f"ACL '{acl_name}' entry {seq_num}: 'src' is required for permit/deny entries"
                )
            if not entry.get("dst"):
                self.module.fail_json(
                    msg=f"ACL '{acl_name}' entry {seq_num}: 'dst' is required for permit/deny entries"
                )

            # Validate protocol-specific options
            protocol = entry.get("protocol")
            if protocol == "custom" and entry.get("custom_protocol") is None:
                self.module.fail_json(
                    msg=f"ACL '{acl_name}' entry {seq_num}: 'custom_protocol' is required when protocol is 'custom'"
                )

            # Validate port options for TCP/UDP
            if protocol in ["tcp", "udp"]:
                self._validate_port_options(acl_name, entry, "src")
                self._validate_port_options(acl_name, entry, "dst")

            # Validate ICMP option only for ICMP protocol
            if entry.get("icmp_option") and protocol != "icmp":
                self.module.fail_json(
                    msg=f"ACL '{acl_name}' entry {seq_num}: 'icmp_option' is only valid for ICMP protocol"
                )

            # Validate TCP option only for TCP protocol
            if entry.get("tcp_option") and protocol != "tcp":
                self.module.fail_json(
                    msg=f"ACL '{acl_name}' entry {seq_num}: 'tcp_option' is only valid for TCP protocol"
                )

    def _validate_port_options(self, acl_name, entry, prefix):
        """Validate port-related options (src or dst)."""
        seq_num = entry.get("sequence_number")
        port_action = entry.get(f"{prefix}_port_action")
        port = entry.get(f"{prefix}_port")
        port_range_start = entry.get(f"{prefix}_port_range_start")
        port_range_end = entry.get(f"{prefix}_port_range_end")

        if port_action and port_action != "none":
            if port_action == "port_range":
                if port_range_start is None or port_range_end is None:
                    self.module.fail_json(
                        msg=f"ACL '{acl_name}' entry {seq_num}: '{prefix}_port_range_start' and "
                        f"'{prefix}_port_range_end' are required when {prefix}_port_action is 'port_range'"
                    )
                if port_range_start > port_range_end:
                    self.module.fail_json(
                        msg=f"ACL '{acl_name}' entry {seq_num}: '{prefix}_port_range_start' must be "
                        f"less than or equal to '{prefix}_port_range_end'"
                    )
            else:
                if port is None:
                    self.module.fail_json(
                        msg=f"ACL '{acl_name}' entry {seq_num}: '{prefix}_port' is required when "
                        f"{prefix}_port_action is '{port_action}'"
                    )

    def _transform_entry_to_api(self, entry):
        """Transform an entry from Ansible format to API format."""
        api_entry = {}

        for key, value in entry.items():
            if value is None:
                continue

            # Map parameter names
            api_key = self.PARAM_TO_API_MAP.get(key, key)

            # Transform port action values
            if key in ["src_port_action", "dst_port_action"]:
                value = self.PORT_ACTION_TO_API.get(value, value)

            api_entry[api_key] = value

        return api_entry

    def _transform_entry_from_api(self, api_entry):
        """Transform an entry from API format to Ansible format."""
        entry = {}

        for key, value in api_entry.items():
            if value is None:
                continue

            # Map parameter names
            ansible_key = self.API_TO_PARAM_MAP.get(key, key)

            # Transform port action values
            if key in ["srcPortAction", "dstPortAction"]:
                value = self.API_TO_PORT_ACTION.get(value, value)

            entry[ansible_key] = value

        return entry

    def _transform_acl_to_api(self, acl):
        """Transform an ACL from Ansible format to API format."""
        api_acl = {
            "name": acl["name"],
            "type": acl["type"],
            "entries": [],
        }

        for entry in acl.get("entries", []):
            api_entry = self._transform_entry_to_api(entry)
            api_acl["entries"].append(api_entry)

        return api_acl

    def _transform_acl_from_api(self, api_acl):
        """Transform an ACL from API format to Ansible format."""
        acl = {
            "name": api_acl["name"],
            "type": api_acl["type"],
            "entries": [],
        }

        for api_entry in api_acl.get("entries", []):
            entry = self._transform_entry_from_api(api_entry)
            acl["entries"].append(entry)

        return acl

    def get_have(self):
        """Get current ACLs from ND."""
        path = self.paths["ACL_LIST"].format(self.fabric)
        resp = dcnm_send(self.module, "GET", path)

        # Handle response - could be dict or string on error
        if not isinstance(resp, dict):
            self.module.fail_json(
                msg=f"Failed to get ACLs from ND: Invalid response - {resp}"
            )

        if resp.get("RETURN_CODE") == 200:
            data = resp.get("DATA", {})
            # Handle both wrapped {"accessControlLists": [...]} and unwrapped [...] formats
            if isinstance(data, dict):
                acl_list = data.get("accessControlLists", [])
            elif isinstance(data, list):
                acl_list = data
            else:
                acl_list = []

            for api_acl in acl_list:
                acl = self._transform_acl_from_api(api_acl)
                self.have.append(acl)
        elif resp.get("RETURN_CODE") == 404:
            # No ACLs found - this is OK
            pass
        else:
            self.module.fail_json(msg=f"Failed to get ACLs from ND: {resp}")

    def get_want(self):
        """Build the desired state from playbook config."""
        if not self.config:
            return

        for acl in self.config:
            want_acl = {
                "name": acl["name"],
            }

            # For delete/query, we may not have type/entries
            if acl.get("type"):
                want_acl["type"] = acl["type"]

            # Process entries
            entries = acl.get("entries", [])
            processed_entries = []
            for entry in entries:
                processed_entry = self._process_entry(entry)
                processed_entries.append(processed_entry)

            want_acl["entries"] = processed_entries
            self.want.append(want_acl)

    def _process_entry(self, entry):
        """Process an entry and apply defaults."""
        processed = {
            "sequence_number": entry["sequence_number"],
            "action": entry["action"],
        }

        if entry["action"] == "remark":
            processed["remark_comment"] = entry.get("remark_comment", "")
        else:
            # Permit/deny entries
            processed["protocol"] = entry.get("protocol")
            processed["src"] = entry.get("src")
            processed["dst"] = entry.get("dst")

            # Optional fields
            if entry.get("custom_protocol") is not None:
                processed["custom_protocol"] = entry["custom_protocol"]

            # Source port options
            src_port_action = entry.get("src_port_action", "none")
            if src_port_action and src_port_action != "none":
                processed["src_port_action"] = src_port_action
                if src_port_action == "port_range":
                    processed["src_port_range_start"] = entry.get(
                        "src_port_range_start"
                    )
                    processed["src_port_range_end"] = entry.get("src_port_range_end")
                else:
                    processed["src_port"] = entry.get("src_port")

            # Destination port options
            dst_port_action = entry.get("dst_port_action", "none")
            if dst_port_action and dst_port_action != "none":
                processed["dst_port_action"] = dst_port_action
                if dst_port_action == "port_range":
                    processed["dst_port_range_start"] = entry.get(
                        "dst_port_range_start"
                    )
                    processed["dst_port_range_end"] = entry.get("dst_port_range_end")
                else:
                    processed["dst_port"] = entry.get("dst_port")

            # ICMP/TCP options
            if entry.get("icmp_option"):
                processed["icmp_option"] = entry["icmp_option"]
            if entry.get("tcp_option"):
                processed["tcp_option"] = entry["tcp_option"]

        return processed

    def _find_have_acl(self, name):
        """Find an ACL in have list by name."""
        for acl in self.have:
            if acl["name"] == name:
                return acl
        return None

    def _entries_equal(self, entry1, entry2):
        """Compare two entries for equality."""
        # Compare all relevant fields
        fields_to_compare = [
            "sequence_number",
            "action",
            "protocol",
            "src",
            "dst",
            "remark_comment",
            "custom_protocol",
            "src_port_action",
            "src_port",
            "src_port_range_start",
            "src_port_range_end",
            "dst_port_action",
            "dst_port",
            "dst_port_range_start",
            "dst_port_range_end",
            "icmp_option",
            "tcp_option",
        ]

        for field in fields_to_compare:
            val1 = entry1.get(field)
            val2 = entry2.get(field)
            if val1 != val2:
                return False
        return True

    def _acls_equal(self, acl1, acl2):
        """Compare two ACLs for equality."""
        if acl1["name"] != acl2["name"]:
            return False
        if acl1.get("type") != acl2.get("type"):
            return False

        entries1 = acl1.get("entries", [])
        entries2 = acl2.get("entries", [])

        if len(entries1) != len(entries2):
            return False

        # Compare entries by sequence number
        entries1_by_seq = {e["sequence_number"]: e for e in entries1}
        entries2_by_seq = {e["sequence_number"]: e for e in entries2}

        if set(entries1_by_seq.keys()) != set(entries2_by_seq.keys()):
            return False

        for seq_num in entries1_by_seq:
            if not self._entries_equal(
                entries1_by_seq[seq_num], entries2_by_seq[seq_num]
            ):
                return False

        return True

    def get_diff_merged(self):
        """Calculate differences for merged state."""
        for want_acl in self.want:
            have_acl = self._find_have_acl(want_acl["name"])

            if have_acl is None:
                # ACL doesn't exist, create it
                self.diff_create.append(want_acl)
                self.changed_dict[0]["merged"].append(want_acl["name"])
            else:
                # ACL exists, check if we need to update
                # For merged state, we merge entries
                merged_acl = self._merge_acl_entries(have_acl, want_acl)
                if not self._acls_equal(have_acl, merged_acl):
                    self.diff_replace.append(merged_acl)
                    self.changed_dict[0]["merged"].append(want_acl["name"])

    def _merge_acl_entries(self, have_acl, want_acl):
        """Merge entries from want into have."""
        merged_acl = {
            "name": want_acl["name"],
            "type": want_acl.get("type", have_acl.get("type")),
            "entries": [],
        }

        # Build a map of existing entries by sequence number
        have_entries = {e["sequence_number"]: e for e in have_acl.get("entries", [])}
        want_entries = {e["sequence_number"]: e for e in want_acl.get("entries", [])}

        # Merge: want entries override have entries with same sequence number
        all_seq_nums = sorted(set(have_entries.keys()) | set(want_entries.keys()))

        for seq_num in all_seq_nums:
            if seq_num in want_entries:
                merged_acl["entries"].append(want_entries[seq_num])
            else:
                merged_acl["entries"].append(have_entries[seq_num])

        return merged_acl

    def get_diff_replaced(self):
        """Calculate differences for replaced state."""
        for want_acl in self.want:
            have_acl = self._find_have_acl(want_acl["name"])

            if have_acl is None:
                # ACL doesn't exist, create it
                self.diff_create.append(want_acl)
                self.changed_dict[0]["replaced"].append(want_acl["name"])
            else:
                # ACL exists, check if we need to replace
                if not self._acls_equal(have_acl, want_acl):
                    self.diff_replace.append(want_acl)
                    self.changed_dict[0]["replaced"].append(want_acl["name"])

    def get_diff_deleted(self):
        """Calculate differences for deleted state."""
        if not self.want:
            # No config provided - delete all ACLs
            for have_acl in self.have:
                self.diff_delete.append(have_acl["name"])
                self.changed_dict[0]["deleted"].append(have_acl["name"])
        else:
            # Delete only specified ACLs
            for want_acl in self.want:
                have_acl = self._find_have_acl(want_acl["name"])
                if have_acl is not None:
                    self.diff_delete.append(want_acl["name"])
                    self.changed_dict[0]["deleted"].append(want_acl["name"])

    def get_diff_query(self):
        """Calculate differences for query state."""
        if not self.want:
            # No config provided - query all ACLs
            self.diff_query = self.have.copy()
            self.changed_dict[0]["query"] = [acl["name"] for acl in self.have]
        else:
            # Query only specified ACLs
            for want_acl in self.want:
                have_acl = self._find_have_acl(want_acl["name"])
                if have_acl is not None:
                    self.diff_query.append(have_acl)
                    self.changed_dict[0]["query"].append(want_acl["name"])

    def _create_acl(self, acl):
        """Create an ACL via API."""
        path = self.paths["ACL_CREATE"].format(self.fabric)
        api_acl = self._transform_acl_to_api(acl)

        # API expects {"accessControlLists": [...]} wrapper for bulk create
        payload = json.dumps({"accessControlLists": [api_acl]})
        resp = dcnm_send(self.module, "POST", path, payload)

        # Handle response - could be dict or string on error
        if not isinstance(resp, dict):
            self.module.fail_json(
                msg=f"Failed to create ACL '{acl['name']}': Invalid response - {resp}"
            )

        # Handle success codes (200, 201, 207)
        if resp.get("RETURN_CODE") in [200, 201, 207]:
            self.result["response"].append(resp)
            # Check for failures in 207 Multi-Status response
            if resp.get("RETURN_CODE") == 207:
                data = resp.get("DATA", {})
                # DATA might be wrapped in accessControlLists
                if isinstance(data, dict):
                    items = data.get("accessControlLists", [])
                elif isinstance(data, list):
                    items = data
                else:
                    items = []
                for item in items:
                    if isinstance(item, dict) and item.get("statusCode", 200) >= 400:
                        self.module.fail_json(
                            msg=f"Failed to create ACL '{acl['name']}': {item}"
                        )
            return True
        else:
            self.module.fail_json(msg=f"Failed to create ACL '{acl['name']}': {resp}")
        return False

    def _update_acl(self, acl):
        """Update an ACL via API."""
        path = self.paths["ACL_UPDATE"].format(self.fabric, acl["name"])
        api_acl = self._transform_acl_to_api(acl)

        payload = json.dumps(api_acl)
        resp = dcnm_send(self.module, "PUT", path, payload)

        # Handle response - could be dict or string on error
        if not isinstance(resp, dict):
            self.module.fail_json(
                msg=f"Failed to update ACL '{acl['name']}': Invalid response - {resp}"
            )

        if resp.get("RETURN_CODE") in [200, 204]:
            self.result["response"].append(resp)
            return True
        else:
            self.module.fail_json(msg=f"Failed to update ACL '{acl['name']}': {resp}")
        return False

    def _delete_acl(self, acl_name):
        """Delete an ACL via API."""
        path = self.paths["ACL_DELETE"].format(self.fabric, acl_name)
        resp = dcnm_send(self.module, "DELETE", path)

        # Handle response - could be dict or string on error
        if not isinstance(resp, dict):
            self.module.fail_json(
                msg=f"Failed to delete ACL '{acl_name}': Invalid response - {resp}"
            )

        if resp.get("RETURN_CODE") in [200, 204]:
            self.result["response"].append(resp)
            return True
        elif resp.get("RETURN_CODE") == 404:
            # ACL doesn't exist - that's fine for delete
            return True
        else:
            self.module.fail_json(msg=f"Failed to delete ACL '{acl_name}': {resp}")
        return False

    def send_to_dcnm(self):
        """Send changes to ND."""
        if self.check_mode:
            self.result["changed"] = bool(
                self.diff_create or self.diff_replace or self.diff_delete
            )
            return

        # Process creates
        for acl in self.diff_create:
            self._create_acl(acl)
            self.result["changed"] = True

        # Process updates/replacements
        for acl in self.diff_replace:
            self._update_acl(acl)
            self.result["changed"] = True

        # Process deletes
        for acl_name in self.diff_delete:
            self._delete_acl(acl_name)
            self.result["changed"] = True

    def run(self):
        """Main execution method."""
        # Validate input
        self.validate_input()

        # Get current state from ND
        self.get_have()

        # Build desired state from playbook
        self.get_want()

        # Calculate differences based on state
        if self.state == "merged":
            self.get_diff_merged()
        elif self.state == "replaced":
            self.get_diff_replaced()
        elif self.state == "deleted":
            self.get_diff_deleted()
        elif self.state == "query":
            self.get_diff_query()

        # Build diff for result
        self.result["diff"] = self.changed_dict

        # For query state, return the ACLs
        if self.state == "query":
            self.result["acls"] = self.diff_query
            return self.result

        # Send changes to ND (unless in check mode)
        self.send_to_dcnm()

        return self.result


def main():
    """Module entry point."""
    element_spec = dict(
        fabric=dict(required=True, type="str"),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "replaced", "deleted", "query"],
        ),
        config=dict(type="list", elements="dict", default=[]),
    )

    module = AnsibleModule(
        argument_spec=element_spec,
        supports_check_mode=True,
    )

    dcnm_acl = DcnmAcl(module)
    result = dcnm_acl.run()

    module.exit_json(**result)


if __name__ == "__main__":
    main()
