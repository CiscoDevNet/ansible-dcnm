#!/usr/bin/python
# -*- coding: utf-8 -*-
# mypy: disable-error-code="import-untyped"
#
# Copyright (c) 2020-2023 Cisco and/or its affiliates.
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
# pylint: disable=wrong-import-position
from __future__ import absolute_import, division, print_function

# pylint: disable=invalid-name
__metaclass__ = type
__author__ = "Shrishail Kariyappanavar, Karthik Babu Harichandra Babu, Praveen Ramoorthy, Allen Robel"
# pylint: enable=invalid-name
DOCUMENTATION = """
---
module: dcnm_vrf_v2
short_description: Add and remove VRFs from a DCNM managed VXLAN fabric.
version_added: "0.9.0"
description:
    - "Add and remove VRFs and VRF Lite Extension from a DCNM managed VXLAN fabric."
    - "In Multisite fabrics, VRFs can be created only on Multisite fabric"
    - "In Multisite fabrics, VRFs cannot be created on member fabric"
author: Shrishail Kariyappanavar(@nkshrishail), Karthik Babu Harichandra Babu (@kharicha), Praveen Ramoorthy(@praveenramoorthy)
options:
  fabric:
    description:
    - Name of the target fabric for vrf operations
    type: str
    required: yes
  state:
    description:
    - The state of DCNM after module completion.
    type: str
    choices:
      - merged
      - replaced
      - overridden
      - deleted
      - query
    default: merged
  config:
    description:
    - List of details of vrfs being managed. Not required for state deleted
    type: list
    elements: dict
    suboptions:
      vrf_name:
        description:
        - Name of the vrf being managed
        type: str
        required: true
      vrf_id:
        description:
        - ID of the vrf being managed
        type: int
        required: false
      vlan_id:
        description:
        - vlan ID for the vrf attachment
        - If not specified in the playbook, DCNM will auto-select an available vlan_id
        type: int
        required: false
      vrf_template:
        description:
        - Name of the config template to be used
        type: str
        default: 'Default_VRF_Universal'
      vrf_extension_template:
        description:
        - Name of the extension config template to be used
        type: str
        default: 'Default_VRF_Extension_Universal'
      service_vrf_template:
        description:
        - Service vrf template
        type: str
        default: None
      vrf_vlan_name:
        description:
        - VRF Vlan Name
        - if > 32 chars enable - system vlan long-name
        - Not applicable to L3VNI w/o VLAN config
        type: str
        required: false
      vrf_intf_desc:
        description:
        - VRF Intf Description
        - Not applicable to L3VNI w/o VLAN config
        type: str
        required: false
      vrf_description:
        description:
        - VRF Description
        type: str
        required: false
      vrf_int_mtu:
        description:
        - VRF interface MTU
        - Not applicable to L3VNI w/o VLAN config
        type: int
        required: false
        default: 9216
      loopback_route_tag:
        description:
        - Loopback Routing Tag
        type: int
        required: false
        default: 12345
      redist_direct_rmap:
        description:
        - Redistribute Direct Route Map
        type: str
        required: false
        default: 'FABRIC-RMAP-REDIST-SUBNET'
      max_bgp_paths:
        description:
        - Max BGP Paths
        type: int
        required: false
        default: 1
      max_ibgp_paths:
        description:
        - Max iBGP Paths
        type: int
        required: false
        default: 2
      ipv6_linklocal_enable:
        description:
        - Enable IPv6 link-local Option
        - Not applicable to L3VNI w/o VLAN config
        type: bool
        required: false
        default: true
      l3vni_wo_vlan:
        description:
        - Enable L3 VNI without VLAN
        type: bool
        required: false
        default: Inherited from fabric level settings
      trm_enable:
        description:
        - Enable Tenant Routed Multicast
        type: bool
        required: false
        default: false
      no_rp:
        description:
        - No RP, only SSM is used
        - supported on NDFC only
        type: bool
        required: false
        default: false
      rp_external:
        description:
        - Specifies if RP is external to the fabric
        - Can be configured only when TRM is enabled
        type: bool
        required: false
        default: false
      rp_address:
        description:
        - IPv4 Address of RP
        - Can be configured only when TRM is enabled
        type: str
        required: false
      rp_loopback_id:
        description:
        - loopback ID of RP
        - Can be configured only when TRM is enabled
        type: int
        required: false
      underlay_mcast_ip:
        description:
        - Underlay IPv4 Multicast Address
        - Can be configured only when TRM is enabled
        type: str
        required: false
      overlay_mcast_group:
        description:
        - Underlay IPv4 Multicast group (224.0.0.0/4 to 239.255.255.255/4)
        - Can be configured only when TRM is enabled
        type: str
        required: false
      trm_bgw_msite:
        description:
        - Enable TRM on Border Gateway Multisite
        - Can be configured only when TRM is enabled
        type: bool
        required: false
        default: false
      adv_host_routes:
        description:
        - Flag to Control Advertisement of /32 and /128 Routes to Edge Routers
        type: bool
        required: false
        default: false
      adv_default_routes:
        description:
        - Flag to Control Advertisement of Default Route Internally
        type: bool
        required: false
        default: true
      static_default_route:
        description:
        - Flag to Control Static Default Route Configuration
        type: bool
        required: false
        default: true
      bgp_password:
        description:
        - VRF Lite BGP neighbor password
        - Password should be in Hex string format
        type: str
        required: false
      bgp_passwd_encrypt:
        description:
        - VRF Lite BGP Key Encryption Type
        - Allowed values are 3 (3DES) and 7 (Cisco)
        type: int
        choices:
          - 3
          - 7
        required: false
        default: 3
      netflow_enable:
        description:
        - Enable netflow on VRF-LITE Sub-interface
        - Netflow is supported only if it is enabled on fabric
        - Netflow configs are supported on NDFC only
        type: bool
        required: false
        default: false
      nf_monitor:
        description:
        - Netflow Monitor
        - Netflow configs are supported on NDFC only
        type: str
        required: false
      disable_rt_auto:
        description:
        - Disable RT Auto-Generate
        - supported on NDFC only
        type: bool
        required: false
        default: false
      import_vpn_rt:
        description:
        - VPN routes to import
        - supported on NDFC only
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      export_vpn_rt:
        description:
        - VPN routes to export
        - supported on NDFC only
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      import_evpn_rt:
        description:
        - EVPN routes to import
        - supported on NDFC only
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      export_evpn_rt:
        description:
        - EVPN routes to export
        - supported on NDFC only
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      import_mvpn_rt:
        description:
        - MVPN routes to import
        - supported on NDFC only
        - Can be configured only when TRM is enabled
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      export_mvpn_rt:
        description:
        - MVPN routes to export
        - supported on NDFC only
        - Can be configured only when TRM is enabled
        - Use ',' to separate multiple route-targets
        type: str
        required: false
      attach:
        description:
        - List of vrf attachment details
        type: list
        elements: dict
        suboptions:
          ip_address:
            description:
            - IP address of the switch where vrf will be attached or detached
            type: str
            required: true
            suboptions:
              vrf_lite:
                type: list
                description:
                - VRF Lite Extensions options
                elements: dict
                required: false
                suboptions:
                  peer_vrf:
                    description:
                    - VRF Name to which this extension is attached
                    type: str
                    required: false
                  interface:
                    description:
                    - Interface of the switch which is connected to the edge router
                    type: str
                    required: true
                  ipv4_addr:
                    description:
                    - IP address of the interface which is connected to the edge router
                    type: str
                    required: false
                  neighbor_ipv4:
                    description:
                    - Neighbor IP address of the edge router
                    type: str
                    required: false
                  ipv6_addr:
                    description:
                    - IPv6 address of the interface which is connected to the edge router
                    type: str
                    required: false
                  neighbor_ipv6:
                    description:
                    - Neighbor IPv6 address of the edge router
                    type: str
                    required: false
                  dot1q:
                    description:
                    - DOT1Q Id
                    type: str
                    required: false
          import_evpn_rt:
            description:
            - import evpn route-target
            - supported on NDFC only
            - Use ',' to separate multiple route-targets
            type: str
            required: false
          export_evpn_rt:
            description:
            - export evpn route-target
            - supported on NDFC only
            - Use ',' to separate multiple route-targets
            type: str
            required: false
          deploy:
            description:
            - Per switch knob to control whether to deploy the attachment
            - This knob has been deprecated from Ansible NDFC Collection Version 2.1.0 onwards.
              There will not be any functional impact if specified in playbook.
            type: bool
            default: true
      deploy:
        description:
        - Global knob to control whether to deploy the attachment
        - Ansible NDFC Collection Behavior for Version 2.0.1 and earlier
        - This knob will create and deploy the attachment in DCNM only when set to "True" in playbook
        - Ansible NDFC Collection Behavior for Version 2.1.0 and later
        - Attachments specified in the playbook will always be created in DCNM.
          This knob, when set to "True",  will deploy the attachment in DCNM, by pushing the configs to switch.
          If set to "False", the attachments will be created in DCNM, but will not be deployed
        type: bool
        default: true
"""

EXAMPLES = """
# This module supports the following states:
#
# Merged:
#   VRFs defined in the playbook will be merged into the target fabric.
#     - If the VRF does not exist it will be added.
#     - If the VRF exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - VRFs that are not specified in the playbook will be untouched.
#
# Replaced:
#   VRFs defined in the playbook will be replaced in the target fabric.
#     - If the VRF does not exist it will be added.
#     - If the VRF exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are  not specified
#       in the playbook will be deleted or defaulted if possible.
#     - VRFs that are not specified in the playbook will be untouched.
#
# Overridden:
#   VRFs defined in the playbook will be overridden in the target fabric.
#     - If the VRF does not exist it will be added.
#     - If the VRF exists but properties managed by the playbook are different
#       they will be updated if possible.
#     - Properties that can be managed by the module but are not specified
#       in the playbook will be deleted or defaulted if possible.
#     - VRFs that are not specified in the playbook will be deleted.
#
# Deleted:
#   VRFs defined in the playbook will be deleted.
#   If no VRFs are provided in the playbook, all VRFs present on that DCNM fabric will be deleted.
#
# Query:
#   Returns the current DCNM state for the VRFs listed in the playbook.
#
# rollback functionality:
# This module supports task level rollback functionality. If any task runs into failures, as part of failure
# handling, the module tries to bring the state of the DCNM back to the state captured in have structure at the
# beginning of the task execution. Following few lines provide a logical description of how this works,
# if (failure)
#     want data = have data
#     have data = get state of DCNM
#     Run the module in override state with above set of data to produce the required set of diffs
#     and push the diff payloads to DCNM.
# If rollback fails, the module does not attempt to rollback again, it just quits with appropriate error messages.

# The two VRFs below will be merged into the target fabric.
- name: Merge vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: merged
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      - ip_address: 192.168.1.225
    - vrf_name: ansible-vrf-r2
      vrf_id: 9008012
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      - ip_address: 192.168.1.225

# VRF LITE Extension attached
- name: Merge vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: merged
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      - ip_address: 192.168.1.225
        vrf_lite:
          - peer_vrf: test_vrf_1 # optional
            interface: Ethernet1/16 # mandatory
            ipv4_addr: 10.33.0.2/30 # optional
            neighbor_ipv4: 10.33.0.1 # optional
            ipv6_addr: 2010::10:34:0:7/64 # optional
            neighbor_ipv6: 2010::10:34:0:3 # optional
            dot1q: 2 # dot1q can be got from dcnm/optional
          - peer_vrf: test_vrf_2 # optional
            interface: Ethernet1/17 # mandatory
            ipv4_addr: 20.33.0.2/30 # optional
            neighbor_ipv4: 20.33.0.1 # optional
            ipv6_addr: 3010::10:34:0:7/64 # optional
            neighbor_ipv6: 3010::10:34:0:3 # optional
            dot1q: 3 # dot1q can be got from dcnm/optional

# The two VRFs below will be replaced in the target fabric.
- name: Replace vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: replaced
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      # Delete this attachment
      # - ip_address: 192.168.1.225
      # Create the following attachment
      - ip_address: 192.168.1.226
    # Dont touch this if its present on DCNM
    # - vrf_name: ansible-vrf-r2
    #   vrf_id: 9008012
    #   vrf_template: Default_VRF_Universal
    #   vrf_extension_template: Default_VRF_Extension_Universal
    #   attach:
    #   - ip_address: 192.168.1.224
    #   - ip_address: 192.168.1.225

# The two VRFs below will be overridden in the target fabric.
- name: Override vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: overridden
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
      attach:
      - ip_address: 192.168.1.224
      # Delete this attachment
      # - ip_address: 192.168.1.225
      # Create the following attachment
      - ip_address: 192.168.1.226
    # Delete this vrf
    # - vrf_name: ansible-vrf-r2
    #   vrf_id: 9008012
    #   vrf_template: Default_VRF_Universal
    #   vrf_extension_template: Default_VRF_Extension_Universal
    #   vlan_id: 2000
    #   service_vrf_template: null
    #   attach:
    #   - ip_address: 192.168.1.224
    #   - ip_address: 192.168.1.225

- name: Delete selected vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: deleted
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null
    - vrf_name: ansible-vrf-r2
      vrf_id: 9008012
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      vlan_id: 2000
      service_vrf_template: null

- name: Delete all the vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: deleted

- name: Query vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: query
    config:
    - vrf_name: ansible-vrf-r1
    - vrf_name: ansible-vrf-r2
"""
import traceback
from typing import Union

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

HAS_FIRST_PARTY_IMPORTS: set[bool] = set()
HAS_THIRD_PARTY_IMPORTS: set[bool] = set()

FIRST_PARTY_IMPORT_ERROR: Union[str, None]
THIRD_PARTY_IMPORT_ERROR: Union[str, None]

FIRST_PARTY_FAILED_IMPORT: set[str] = set()
THIRD_PARTY_FAILED_IMPORT: set[str] = set()

try:
    import pydantic  # pylint: disable=unused-import

    HAS_THIRD_PARTY_IMPORTS.add(True)
    THIRD_PARTY_IMPORT_ERROR = None
except ImportError as import_error:
    HAS_THIRD_PARTY_IMPORTS.add(False)
    THIRD_PARTY_FAILED_IMPORT.add("pydantic")
    THIRD_PARTY_IMPORT_ERROR = traceback.format_exc()

from ..module_utils.common.enums.ansible import AnsibleStates
from ..module_utils.common.log_v2 import Log
from ..module_utils.network.dcnm.dcnm import dcnm_version_supported

DcnmVrf11 = None  # pylint: disable=invalid-name
NdfcVrf12 = None  # pylint: disable=invalid-name

try:
    from ..module_utils.vrf.dcnm_vrf_v11 import DcnmVrf11

    HAS_FIRST_PARTY_IMPORTS.add(True)
except ImportError as import_error:
    HAS_FIRST_PARTY_IMPORTS.add(False)
    FIRST_PARTY_FAILED_IMPORT.add("DcnmVrf11")
    FIRST_PARTY_IMPORT_ERROR = traceback.format_exc()

try:
    from ..module_utils.vrf.dcnm_vrf_v12 import NdfcVrf12

    HAS_FIRST_PARTY_IMPORTS.add(True)
except ImportError as import_error:
    HAS_FIRST_PARTY_IMPORTS.add(False)
    FIRST_PARTY_FAILED_IMPORT.add("NdfcVrf12")
    FIRST_PARTY_IMPORT_ERROR = traceback.format_exc()


class DcnmVrf:  # pylint: disable=too-few-public-methods
    """
    Stub class used only to return the controller version.

    We needed this to satisfy the unittest patch that is done in the dcnm_vrf unit tests.

    TODO: This can be removed when we move to pytest-based unit tests.
    """

    def __init__(self, module: AnsibleModule):
        self.module = module
        self.version: int = dcnm_version_supported(self.module)

    @property
    def controller_version(self) -> int:
        """
        # Summary

        Return the controller major version as am integer.
        """
        return self.version


def main() -> None:
    """main entry point for module execution"""

    # Logging setup
    try:
        log: Log = Log()
        log.commit()
    except (TypeError, ValueError):
        pass

    argument_spec: dict = {}
    argument_spec["config"] = {}
    argument_spec["config"]["elements"] = "dict"
    argument_spec["config"]["required"] = False
    argument_spec["config"]["type"] = "list"
    argument_spec["fabric"] = {}
    argument_spec["fabric"]["required"] = True
    argument_spec["fabric"]["type"] = "str"
    argument_spec["state"] = {}
    argument_spec["state"]["choices"] = [x.value for x in AnsibleStates]
    argument_spec["state"]["default"] = AnsibleStates.MERGED.value

    module: AnsibleModule = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if False in HAS_THIRD_PARTY_IMPORTS:
        module.fail_json(msg=missing_required_lib(f"3rd party: {','.join(THIRD_PARTY_FAILED_IMPORT)}"), exception=THIRD_PARTY_IMPORT_ERROR)

    if False in HAS_FIRST_PARTY_IMPORTS:
        module.fail_json(msg=missing_required_lib(f"1st party: {','.join(FIRST_PARTY_FAILED_IMPORT)}"), exception=FIRST_PARTY_IMPORT_ERROR)

    dcnm_vrf_launch: DcnmVrf = DcnmVrf(module)

    if DcnmVrf11 is None:
        module.fail_json(msg="Unable to import DcnmVrf11")
    if NdfcVrf12 is None:
        module.fail_json(msg="Unable to import DcnmVrf12")

    if dcnm_vrf_launch.controller_version == 12:
        dcnm_vrf = NdfcVrf12(module)
    else:
        dcnm_vrf = DcnmVrf11(module)
        if not dcnm_vrf.ip_sn:
            msg = f"Fabric {dcnm_vrf.fabric} missing on the controller or "
            msg += "does not have any switches"
            module.fail_json(msg=msg)

    dcnm_vrf.validate_input()

    dcnm_vrf.get_want()
    dcnm_vrf.get_have()

    if module.params["state"] == "merged":
        dcnm_vrf.get_diff_merge()

    if module.params["state"] == "replaced":
        dcnm_vrf.get_diff_replace()

    if module.params["state"] == "overridden":
        dcnm_vrf.get_diff_override()

    if module.params["state"] == "deleted":
        dcnm_vrf.get_diff_delete()

    if module.params["state"] == "query":
        dcnm_vrf.get_diff_query()
        dcnm_vrf.result["response"] = dcnm_vrf.query

    dcnm_vrf.format_diff()
    dcnm_vrf.result["diff"] = dcnm_vrf.diff_input_format

    module_result: set[bool] = set()
    module_result.add(len(dcnm_vrf.diff_create) != 0)
    module_result.add(len(dcnm_vrf.diff_attach) != 0)
    module_result.add(len(dcnm_vrf.diff_detach) != 0)
    module_result.add(len(dcnm_vrf.diff_deploy) != 0)
    module_result.add(len(dcnm_vrf.diff_undeploy) != 0)
    module_result.add(len(dcnm_vrf.diff_delete) != 0)
    module_result.add(len(dcnm_vrf.diff_create_quick) != 0)
    module_result.add(len(dcnm_vrf.diff_create_update) != 0)

    if True in module_result:
        dcnm_vrf.result["changed"] = True
    else:
        module.exit_json(**dcnm_vrf.result)

    if module.check_mode:
        dcnm_vrf.result["changed"] = False
        msg = f"dcnm_vrf.result: {dcnm_vrf.result}"
        dcnm_vrf.log.debug(msg)
        module.exit_json(**dcnm_vrf.result)

    dcnm_vrf.push_to_remote()

    msg = f"dcnm_vrf.result: {dcnm_vrf.result}"
    dcnm_vrf.log.debug(msg)
    module.exit_json(**dcnm_vrf.result)


if __name__ == "__main__":
    main()
