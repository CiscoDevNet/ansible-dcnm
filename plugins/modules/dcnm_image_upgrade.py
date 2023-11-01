#!/usr/bin/python
#
# Copyright (c) 2020-2024 Cisco and/or its affiliates.
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
"""
Classes and methods for Ansible support of Nexus image upgrade.

Ansible states "merged", "deleted", and "query" are implemented.

merged: attach image policy to one or more devices
deleted: delete image policy from one or more devices
query: return image policy details for one or more devices
"""
from __future__ import absolute_import, division, print_function

import copy
import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policy_action import ImagePolicyAction
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_stage import ImageStage
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade import ImageUpgrade
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_validate import ImageValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.install_options import ImageInstallOptions
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_details import SwitchDetails
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import SwitchIssuDetailsByIpAddress
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    validate_list_of_dicts,
)

__metaclass__ = type
__author__ = "Cisco Systems, Inc."

DOCUMENTATION = """
---
module: dcnm_image_upgrade
short_description: Attach, detach, and query device image policies.
version_added: "0.9.0"
description:
    - Attach, detach, and query device image policies.
author: Cisco Systems, Inc.
options:
    state:
        description:
        - The state of the feature or object after module completion.
        - I(merged) and I(query) are the only states supported.
        type: str
        choices:
        - merged
        - deleted
        - query
        default: merged
    config:
        description:
        - A dictionary containing the image policy configuration.
        type: dict
        suboptions:
            policy:
                description:
                - Image policy name
                type: str
                required: true
                default: False
            stage:
                description:
                - Stage (True) or unstage (False) an image policy
                type: bool
                required: false
                default: True
            validate:
                description:
                - Validate (True) or do not validate (False) the image
                - after staging
                type: bool
                required: false
                default: True
            reboot:
                description:
                - Reboot the switch after upgrade
                type: bool
                required: false
                default: False
            upgrade:
                description:
                - A dictionary containing upgrade toggles for nxos and epld
                type: dict
                suboptions:
                    nxos:
                        description:
                        - Enable (True) or disable (False) image upgrade
                        type: bool
                        required: false
                        default: True
                    epld:
                        description:
                        - Enable (True) or disable (False) EPLD upgrade
                        - If upgrade.nxos is false, epld and packages cannot both be true
                        - If epld is true, nxos_option must be disruptive
                        type: bool
                        required: false
                        default: False
            options:
                description:
                - A dictionary containing options for each of the upgrade types
                type: dict
                suboptions:
                    nxos:
                        description:
                        - A dictionary containing nxos upgrade options
                        type: dict
                        suboptions:
                            mode:
                                description:
                                - nxos upgrade mode
                                - Choose between distruptive, non_disruptive, force_non_disruptive
                                type: string
                                required: false
                                default: distruptive
                            bios_force:
                                description:
                                - Force BIOS upgrade
                                type: bool
                                required: false
                                default: False
                    epld:
                        description:
                        - A dictionary containing epld upgrade options
                        type: dict
                        suboptions:
                            module:
                                description:
                                - The switch module to upgrade
                                - Choose between ALL, or integer values
                                type: string
                                required: false
                                default: ALL
                            golden:
                                description:
                                - Enable (True) or disable (False) reverting to the golden EPLD image
                                type: bool
                                required: false
                                default: False
                    reboot:
                        description:
                        - A dictionary containing reboot options
                        type: dict
                        suboptions:
                            config_reload:
                                description:
                                - Reload the configuration
                                type: bool
                                required: false
                                default: False
                            write_erase:
                                description:
                                - Erase the startup configuration
                                type: bool
                                required: false
                                default: False
                    package:
                        description:
                        - A dictionary containing package upgrade options
                        type: dict
                        suboptions:
                            install:
                                description:
                                - Install the package
                                type: bool
                                required: false
                                default: False
                            uninstall:
                                description:
                                - Uninstall the package
                                type: bool
                                required: false
                                default: False
            switches:
                description:
                - A list of devices to attach the image policy to.
                type: list
                elements: dict
                required: true
                suboptions:
                    ip_address:
                        description:
                        - The IP address of the device to which the policy will be attached.
                        type: str
                        required: true
                    policy:
                        description:
                        - Image policy name
                        type: str
                        required: true
                        default: False
                    stage:
                        description:
                        - Stage (True) or unstage (False) an image policy
                        type: bool
                        required: false
                        default: True
                    validate:
                        description:
                        - Validate (True) or do not validate (False) the image
                        - after staging
                        type: bool
                        required: false
                        default: True
                    reboot:
                        description:
                        - Reboot the switch after upgrade
                        type: bool
                        required: false
                        default: False
                    upgrade:
                        description:
                        - A dictionary containing upgrade toggles for nxos and epld
                        type: dict
                        suboptions:
                            nxos:
                                description:
                                - Enable (True) or disable (False) image upgrade
                                type: bool
                                required: false
                                default: True
                            epld:
                                description:
                                - Enable (True) or disable (False) EPLD upgrade
                                - If upgrade.nxos is false, epld and packages cannot both be true
                                - If epld is true, nxos_option must be disruptive
                                type: bool
                                required: false
                                default: False
                    options:
                        description:
                        - A dictionary containing options for each of the upgrade types
                        type: dict
                        suboptions:
                            nxos:
                                description:
                                - A dictionary containing nxos upgrade options
                                type: dict
                                suboptions:
                                    mode:
                                        description:
                                        - nxos upgrade mode
                                        - Choose between distruptive, non_disruptive, force_non_disruptive
                                        type: string
                                        required: false
                                        default: distruptive
                                    bios_force:
                                        description:
                                        - Force BIOS upgrade
                                        type: bool
                                        required: false
                                        default: False
                            epld:
                                description:
                                - A dictionary containing epld upgrade options
                                type: dict
                                suboptions:
                                    module:
                                        description:
                                        - The switch module to upgrade
                                        - Choose between ALL, or integer values
                                        type: string
                                        required: false
                                        default: ALL
                                    golden:
                                        description:
                                        - Enable (True) or disable (False) reverting to the golden EPLD image
                                        type: bool
                                        required: false
                                        default: False
                            reboot:
                                description:
                                - A dictionary containing reboot options
                                type: dict
                                suboptions:
                                    config_reload:
                                        description:
                                        - Reload the configuration
                                        type: bool
                                        required: false
                                        default: False
                                    write_erase:
                                        description:
                                        - Erase the startup configuration
                                        type: bool
                                        required: false
                                        default: False
                            package:
                                description:
                                - A dictionary containing package upgrade options
                                type: dict
                                suboptions:
                                    install:
                                        description:
                                        - Install the package
                                        type: bool
                                        required: false
                                        default: False
                                    uninstall:
                                        description:
                                        - Uninstall the package
                                        type: bool
                                        required: false
                                        default: False

"""

EXAMPLES = """
# This module supports the following states:
#
# merged:
#   Attach image policy to one or more devices.
#
# query:
#   Return image policy details for one or more devices.
#   
# deleted:
#   Delete image policy from one or more devices
#

# Attach image policy NR3F to two devices
# Stage and validate the image on two devices but do not upgrade
    -   name: stage/validate images
        cisco.dcnm.dcnm_image_upgrade:
            state: merged
            config:
                policy: NR3F
                stage: true
                validate: true
                upgrade:
                    nxos: false
                    epld: false
                switches:
                -   ip_address: 192.168.1.1
                -   ip_address: 192.168.1.2

# Attach image policy NR1F to device 192.168.1.1
# Attach image policy NR2F to device 192.168.1.2
# Stage the image on device 192.168.1.1, but do not upgrade
# Stage the image and upgrade device 192.168.1.2
    -   name: stage/upgrade devices
        cisco.dcnm.dcnm_image_upgrade:
            state: merged
            config:
                validate: false
                stage: false
                upgrade:
                    nxos: false
                    epld: false
                options:
                    nxos:
                        type: disruptive
                    epld:
                        module: ALL
                        golden: false
                switches:
                    -   ip_address: 192.168.1.1
                        policy: NR1F
                        stage: true
                        validate: true
                        upgrade:
                            nxos: true
                            epld: false
                    -   ip_address: 192.168.1.2
                        policy: NR2F
                        stage: true
                        validate: true
                        upgrade:
                            nxos: true
                            epld: true
                        options:
                            nxos:
                                type: disruptive
                            epld:
                                module: ALL
                                golden: false

# Detach image policy NR3F from two devices
    -   name: stage/upgrade devices
        cisco.dcnm.dcnm_image_upgrade:
            state: deleted
            config:
                policy: NR3F
                switches:
                -   ip_address: 192.168.1.1
                -   ip_address: 192.168.1.2

"""

class ImageUpgradeTask(ImageUpgradeCommon):
    """
    Ansible support for image policy attach, detach, and query.
    """

    def __init__(self, module):
        super().__init__(module)
        self.params = self.module.params
        self.class_name = self.__class__.__name__
        self.endpoints = ApiEndpoints()
        self.log_msg(f"{self.class_name}.__init__")
        # populated in self._build_policy_attach_payload()
        self.payloads = []

        self.config = module.params.get("config")
        self.log_msg(f"{self.class_name}.__init__() self.config {self.config}")
        if not isinstance(self.config, dict):
            msg = "expected dict type for self.config. "
            msg = +f"got {type(self.config).__name__}"
            self.module.fail_json(msg)

        self.check_mode = False
        self.validated = []
        self.have_create = []
        self.want_create = []
        self.need = []
        self.diff_save = {}
        self.query = []
        self.result = dict(changed=False, diff=[], response=[])

        self.mandatory_global_keys = {"switches"}
        self.mandatory_switch_keys = {"ip_address"}

        if not self.mandatory_global_keys.issubset(self.config):
            msg = f"{self.class_name}.__init__: "
            msg += "Missing mandatory key(s) in playbook global config. "
            msg += f"expected {self.mandatory_global_keys}, "
            msg += f"got {self.config.keys()}"
            self.module.fail_json(msg)

        if self.config["switches"] is None:
            msg = f"{self.class_name}.__init__: "
            msg += "missing list of switches in playbook config."
            self.module.fail_json(msg)

        for switch in self.config["switches"]:
            if not self.mandatory_switch_keys.issubset(switch):
                msg = f"{self.class_name}.__init__: "
                msg += f"missing mandatory key(s) in playbook switch config. "
                msg += f"expected {self.mandatory_switch_keys}, "
                msg += f"got {switch.keys()}"
                self.module.fail_json(msg)

        self.log_msg(f"{self.class_name}.__init__: instantiate SwitchDetails")
        self.switch_details = SwitchDetails(self.module)
        self.log_msg(f"{self.class_name}.__init__: instantiate ImagePolicies")
        self.image_policies = ImagePolicies(self.module)

    def get_have(self):
        """
        Caller: main()

        Determine current switch ISSU state on NDFC
        """
        self.have = SwitchIssuDetailsByIpAddress(self.module)
        self.have.refresh()

    def get_want(self):
        """
        Caller: main()

        Update self.want_create for all switches defined in the playbook
        """
        self._merge_global_and_switch_configs(self.config)
        self._validate_switch_configs()
        if not self.switch_configs:
            return
        self.log_msg(f"{self.class_name}.get_want() self.switch_configs: {self.switch_configs}")
        self.want_create = self.switch_configs

    def _get_idempotent_want(self, want):
        """
        Return an itempotent want item based on the have item contents.

        The have item is obtained from an instance of SwitchIssuDetails
        created in self.get_have().
        
        want structure passed to this method:

        {
            'policy': 'KR3F',
            'stage': True,
            'upgrade': {
                'nxos': True,
                'epld': False
            },
            'options': {
                'nxos': {
                    'mode': 'non_disruptive'
                    'bios_force': False
                },
                'epld': {
                    'module': 'ALL',
                    'golden': False
                }
            },
            'validate': True,
            'ip_address': '172.22.150.102'
        }

        The returned idempotent_want structure is identical to the
        above structure, except that the policy_changed key is added,
        and values are modified based on results from the have item,
        and the information returned by ImageInstallOptions. 

        Caller: self.get_need_merged()
        """
        self.log_msg(f"{self.class_name}._get_idempotent_want() want: {want}")
        self.have.ip_address = want["ip_address"]

        want["policy_changed"] = True
        # In NDFC, the switch does not have an image policy attached
        # Return the want item as-is with policy_changed = True
        if self.have.serial_number is None:
            self.log_msg(f"{self.class_name}._get_idempotent_want() no serial_number. returning want: {want}")
            return want
        # The switch has an image policy attached which is
        # different from the want policy.
        # Return the want item as-is with policy_changed = True
        if want["policy"] != self.have.policy:
            self.log_msg(f"{self.class_name}._get_idempotent_want() different policy attached. returning want: {want}")
            return want

        # start with a copy of the want item
        idempotent_want = copy.deepcopy(want)
        # Give an indication to the caller that the policy has not changed
        # We can use this later to determine if we need to do anything in
        # the case where the image is already staged and/or upgraded.
        idempotent_want["policy_changed"] = False

        # if the image is already staged, don't stage it again
        if self.have.image_staged == "Success":
            idempotent_want["stage"] = False
        # if the image is already validated, don't validate it again
        if self.have.validated == "Success":
            idempotent_want["validate"] = False
        # if the image is already upgraded, don't upgrade it again
        if self.have.status == "In-Sync" and self.have.reason == "Upgrade" and self.have.policy == want["policy"]:
            idempotent_want["upgrade"]["nxos"] = False

        # Get relevant install options from NDFC based on the
        # options in our want item
        instance = ImageInstallOptions(self.module)
        instance.policy_name = want["policy"]
        msg = f"REMOVE: {self.class_name}._get_idempotent_want() "
        msg += f"calling ImageInstallOptions.refresh() with "
        msg += f"serial_number {self.have.serial_number} "
        msg += f"ip_address {self.have.ip_address} "
        msg += f"device_name {self.have.device_name}"
        self.log_msg(msg)
        instance.serial_number = self.have.serial_number
        instance.epld = want["upgrade"]["epld"]
        instance.issu = want["upgrade"]["nxos"]
        instance.refresh()

        if instance.epld_modules is None:
            idempotent_want["upgrade"]["epld"] = False
        self.log_msg(f"REMOVE: {self.class_name}._get_idempotent_want() returned idempotent_want: {idempotent_want}")
        return idempotent_want

    def get_need_merged(self):
        """
        Caller: main()

        For merged state, populate self.need list() with items from
        our want list that are not in our have list.  These items will be sent
        to NDFC.
        """
        need = []

        for want_create in self.want_create:
            self.have.ip_address = want_create["ip_address"]
            if self.have.serial_number is not None:
                idempotent_want = self._get_idempotent_want(want_create)
                if (
                    idempotent_want["policy_changed"] is False
                    and idempotent_want["stage"] is False
                    and idempotent_want["upgrade"]["nxos"] is False
                    and idempotent_want["upgrade"]["epld"] is False
                ):
                    continue
                need.append(idempotent_want)
        self.need = need
        msg = f"REMOVE: {self.class_name}.get_need_merged: "
        msg += f"need: {self.need}"
        self.log_msg(msg)

    def get_need_deleted(self):
        """
        Caller: main()

        For deleted state, populate self.need list() with items from our want
        list that are not in our have list.  These items will be sent to NDFC.
        """
        need = []
        for want in self.want_create:
            self.have.ip_address = want["ip_address"]
            if self.have.serial_number is None:
                continue
            if self.have.policy is None:
                continue
            need.append(want)
        self.need = need

    def get_need_query(self):
        """
        Caller: main()

        For query state, populate self.need list() with all items from our want
        list.  These items will be sent to NDFC.
        """
        need = []
        for want in self.want_create:
            need.append(want)
        self.need = need

    @staticmethod
    def _build_params_spec_for_merged_state():
        """
        Build the specs for the parameters expected when state == merged.

        Caller: _validate_input_for_merged_state()
        Return: params_spec, a dictionary containing the set of
                playbook parameter specifications.
        """
        params_spec = {}
        params_spec["policy"] = {}
        params_spec["policy"]["required"] = False
        params_spec["policy"]["type"] = "str"

        params_spec["stage"] = {}
        params_spec["stage"]["required"] = False
        params_spec["stage"]["type"] = "bool"
        params_spec["stage"]["default"] = True

        params_spec["validate"] = {}
        params_spec["validate"]["required"] = False
        params_spec["validate"]["type"] = "bool"
        params_spec["validate"]["default"] = True

        params_spec["upgrade"] = {}
        params_spec["upgrade"]["required"] = False
        params_spec["upgrade"]["type"] = "dict"
        params_spec["upgrade"]["default"] = {}

        section = "options"
        params_spec[section] = {}
        params_spec[section]["required"] = False
        params_spec[section]["type"] = "dict"
        params_spec[section]["default"] = {}

        sub_section = "nxos"
        params_spec[section][sub_section] = {}
        params_spec[section][sub_section]["required"] = False
        params_spec[section][sub_section]["type"] = "dict"
        params_spec[section][sub_section]["default"] = {}

        params_spec[section][sub_section]["mode"] = {}
        params_spec[section][sub_section]["mode"]["required"] = False
        params_spec[section][sub_section]["mode"]["type"] = "str"
        params_spec[section][sub_section]["mode"]["default"] = "disruptive"

        params_spec[section][sub_section]["bios_force"] = {}
        params_spec[section][sub_section]["bios_force"]["required"] = False
        params_spec[section][sub_section]["bios_force"]["type"] = "bool"
        params_spec[section][sub_section]["bios_force"]["default"] = False

        sub_section = "epld"
        params_spec[section][sub_section] = {}
        params_spec[section][sub_section]["required"] = False
        params_spec[section][sub_section]["type"] = "dict"
        params_spec[section][sub_section]["default"] = {}

        params_spec[section][sub_section]["module"] = {}
        params_spec[section][sub_section]["module"] ["required"] = False
        params_spec[section][sub_section]["module"] ["type"] = "str"
        params_spec[section][sub_section]["module"] ["default"] = "ALL"

        params_spec[section][sub_section]["golden"] = {}
        params_spec[section][sub_section]["golden"] ["required"] = False
        params_spec[section][sub_section]["golden"] ["type"] = "bool"
        params_spec[section][sub_section]["golden"] ["default"] = False

        sub_section = "reboot"
        params_spec[section][sub_section] = {}
        params_spec[section][sub_section]["required"] = False
        params_spec[section][sub_section]["type"] = "dict"
        params_spec[section][sub_section]["default"] = {}

        params_spec[section][sub_section]["config_reload"] = {}
        params_spec[section][sub_section]["config_reload"] ["required"] = False
        params_spec[section][sub_section]["config_reload"] ["type"] = "bool"
        params_spec[section][sub_section]["config_reload"] ["default"] = False

        params_spec[section][sub_section]["write_erase"] = {}
        params_spec[section][sub_section]["write_erase"] ["required"] = False
        params_spec[section][sub_section]["write_erase"] ["type"] = "bool"
        params_spec[section][sub_section]["write_erase"] ["default"] = False

        sub_section = "package"
        params_spec[section][sub_section] = {}
        params_spec[section][sub_section]["required"] = False
        params_spec[section][sub_section]["type"] = "dict"
        params_spec[section][sub_section]["default"] = {}

        params_spec[section][sub_section]["install"] = {}
        params_spec[section][sub_section]["install"] ["required"] = False
        params_spec[section][sub_section]["install"] ["type"] = "bool"
        params_spec[section][sub_section]["install"] ["default"] = False

        params_spec[section][sub_section]["uninstall"] = {}
        params_spec[section][sub_section]["uninstall"] ["required"] = False
        params_spec[section][sub_section]["uninstall"] ["type"] = "bool"
        params_spec[section][sub_section]["uninstall"] ["default"] = False

        return copy.deepcopy(params_spec)

    def validate_input(self):
        """
        Caller: main()

        Validate the playbook parameters
        """
        state = self.params["state"]
        self.log_msg(f"{self.class_name}.validate_input: state: {state}")

        if state not in ["merged", "deleted", "query"]:
            msg = f"This module supports deleted, merged, and query states. Got state {state}"
            self.module.fail_json(msg)

        if state == "merged":
            self.log_msg(f"{self.class_name}.validate_input: call _validate_input_for_merged_state()")
            self._validate_input_for_merged_state()
            return
        if state == "deleted":
            self._validate_input_for_deleted_state()
            return
        if state == "query":
            self._validate_input_for_query_state()
            return

    def _validate_input_for_merged_state(self):
        """
        Caller: self.validate_input()

        Validate that self.config contains appropriate values for merged state
        """
        if not self.config:
            msg = "config: element is mandatory for state merged"
            self.module.fail_json(msg)

        params_spec = self._build_params_spec_for_merged_state()

        self.log_msg(f"{self.class_name}._validate_input_for_merged_state: params_spec: {params_spec}")
        self.log_msg(f"{self.class_name}._validate_input_for_merged_state: self.config: {self.config}")
        valid_params, invalid_params = validate_list_of_dicts(
            self.config.get("switches"), params_spec, self.module
        )
        # We're not using self.validated. Keeping this to avoid
        # linter error due to non-use of valid_params
        self.validated = copy.deepcopy(valid_params)

        if invalid_params:
            msg = "Invalid parameters in playbook: "
            msg += f"{','.join(invalid_params)}"
            self.module.fail_json(msg)

    def _validate_input_for_deleted_state(self):
        """
        Caller: self.validate_input()

        Validate that self.config contains appropriate values for deleted state

        NOTES:
        1. This is currently identical to _validate_input_for_merged_state()
        2. Adding in case there are differences in the future
        """
        params_spec = self._build_params_spec_for_merged_state()
        if not self.config:
            msg = "config: element is mandatory for state deleted"
            self.module.fail_json(msg)

        valid_params, invalid_params = validate_list_of_dicts(
            self.config.get("switches"), params_spec, self.module
        )
        # We're not using self.validated. Keeping this to avoid
        # linter error due to non-use of valid_params
        self.validated = copy.deepcopy(valid_params)

        if invalid_params:
            msg = "Invalid parameters in playbook: "
            msg += f"{','.join(invalid_params)}"
            self.module.fail_json(msg)

    def _validate_input_for_query_state(self):
        """
        Caller: self.validate_input()

        Validate that self.config contains appropriate values for query state

        NOTES:
        1. This is currently identical to _validate_input_for_merged_state()
        2. Adding in case there are differences in the future
        """
        params_spec = self._build_params_spec_for_merged_state()
        if not self.config:
            msg = "config: element is mandatory for state query"
            self.module.fail_json(msg)

        valid_params, invalid_params = validate_list_of_dicts(
            self.config.get("switches"), params_spec, self.module
        )
        # We're not using self.validated. Keeping this to avoid
        # linter error due to non-use of valid_params
        self.validated = copy.deepcopy(valid_params)

        if invalid_params:
            msg = "Invalid parameters in playbook: "
            msg += f"{','.join(invalid_params)}"
            self.module.fail_json(msg)

    def _merge_global_and_switch_configs(self, config):
        """
        Merge the global config with each switch config and return
        a dict of switch configs keyed on switch ip_address.

        Merge rules:
        1.  switch_config takes precedence over global_config.
        2.  If switch_config is missing a parameter, use parameter
            from global_config.
        3.  If a switch_config has a parameter, use it.
        4.  If global_config and switch_config are both missing an
            optional parameter, use the parameter's default value.
        5.  If global_config and switch_config are both missing a
            mandatory parameter, fail.
        """
        if not config.get("switches"):
            msg = f"{self.class_name}._merge_global_and_switch_configs: "
            msg += "playbook is missing list of switches"
            self.module.fail_json(msg)

        msg = f"REMOVE: {self.class_name}._merge_global_and_switch_configs: "
        msg += f"config: {config}"
        self.log_msg(msg)
        global_config = {}
        global_config["policy"] = config.get("policy")
        global_config["stage"] = config.get("stage")
        global_config["upgrade"] = config.get("upgrade")
        global_config["options"] = config.get("options")
        global_config["validate"] = config.get("validate")
        msg = f"REMOVE: {self.class_name}._merge_global_and_switch_configs: "
        msg += f"global_config: {global_config}"
        self.log_msg(msg)
        self.switch_configs = []
        for switch in config["switches"]:
            switch_config = global_config.copy() | switch.copy()
            msg = f"REMOVE: {self.class_name}._merge_global_and_switch_configs: "
            msg += f"merged switch_config: {switch_config}"
            self.log_msg(msg)
            self.switch_configs.append(switch_config)

    def _validate_switch_configs(self):
        """
        Ensure mandatory parameters are present for each switch
            - fail_json if this isn't the case
        Set defaults for missing optional parameters

        NOTES:
        1.  Final application of missing default parameters is done in
            ImageUpgrade.commit()

        Callers:
            - self.get_want
        """
        for switch in self.switch_configs:
            msg = f"REMOVE: {self.class_name}._validate_switch_configs: "
            msg += f"switch: {switch}"
            self.log_msg(msg)
            if not switch.get("ip_address"):
                msg = "playbook is missing ip_address for at least one switch"
                self.module.fail_json(msg)
            # for query state, the only mandatory parameter is ip_address
            # so skip the remaining checks
            if self.params.get("state") == "query":
                continue
            if switch.get("policy") is None:
                msg = "playbook is missing image policy for switch "
                msg += f"{switch.get('ip_address')} "
                msg += "and global image policy is not defined."
                self.module.fail_json(msg)

    def _build_policy_attach_payload(self):
        """
        Build the payload for the policy attach request to NDFC
        Verify that the image policy exists on NDFC
        Verify that the image policy supports the switch platform

        Callers:
            - self.handle_merged_state
        """
        self.payloads = []
        # TODO:2 Need a way to call refresh() once in __init__() and mock in unit tests
        self.switch_details.refresh()
        self.image_policies.refresh()
        for switch in self.need:
            if switch.get("policy_changed") is False:
                continue
            self.switch_details.ip_address = switch.get("ip_address")
            self.image_policies.policy_name = switch.get("policy")

            # Fail if the image policy does not exist.
            # Image policy creation is handled by a different module.
            if self.image_policies.name is None:
                msg = f"policy {switch.get('policy')} does not exist on NDFC"
                self.module.fail_json(msg)

            # Fail if the image policy does not support the switch platform
            if self.switch_details.platform not in self.image_policies.platform:
                msg = f"policy {switch.get('policy')} does not support platform "
                msg += f"{self.switch_details.platform}. {switch.get('policy')} "
                msg += "supports the following platform(s): "
                msg += f"{self.image_policies.platform}"
                self.module.fail_json(msg)

            payload = {}
            payload["policyName"] = self.image_policies.name
            # switch_details.host_name is always None in 12.1.2e
            # so we're using logical_name instead
            payload["hostName"] = self.switch_details.logical_name
            payload["ipAddr"] = self.switch_details.ip_address
            payload["platform"] = self.switch_details.platform
            payload["serialNumber"] = self.switch_details.serial_number
            # payload["bootstrapMode"] = switch.get('bootstrap_mode')

            for item in payload:
                if payload[item] is None:
                    msg = f"Unable to determine {item} for switch {switch.get('ip_address')}. "
                    msg += "Please verify that the switch is managed by NDFC."
                    self.module.fail_json(msg)
            self.payloads.append(payload)

    def _send_policy_attach_payload(self):
        """
        Send the policy attach payload to NDFC and handle the response

        Callers:
            - self.handle_merged_state
        """
        if len(self.payloads) == 0:
            return
        path = self.endpoints.policy_attach.get("path")
        verb = self.endpoints.policy_attach.get("verb")
        payload = {}
        payload["mappingList"] = self.payloads
        response = dcnm_send(self.module, verb, path, data=json.dumps(payload))
        result = self._handle_response(response, verb)

        if not result["success"]:
            self._failure(response)

    def _stage_images(self, serial_numbers):
        """
        Initiate image staging to the switch(es) associated with serial_numbers

        Callers:
        - handle_merged_state
        """
        instance = ImageStage(self.module)
        instance.serial_numbers = serial_numbers
        instance.commit()

    def _validate_images(self, serial_numbers):
        """
        Validate the image staged to the switch(es)

        Callers:
        - handle_merged_state
        """
        instance = ImageValidate(self.module)
        instance.serial_numbers = serial_numbers
        # TODO:2 Discuss with Mike/Shangxin - ImageValidate.non_disruptive
        # Should we add this option to the playbook?
        # It's supported in ImageValidate with default of False
        # instance.non_disruptive = False
        instance.commit()

    def _verify_install_options(self, devices):
        """
        Verify that the install options for the devices(es) are valid

        Example devices structure:

        [
            {
                'policy': 'KR3F',
                'stage': False,
                'upgrade': {
                    'nxos': True, 
                    'epld': False
                },
                'options': {
                    'nxos': {
                        'mode': 'non_disruptive'
                    },
                    'epld': {
                        'module': 'ALL',
                        'golden': False
                    }
                },
                'validate': False,
                'ip_address': '172.22.150.102',
                'policy_changed': False
            },
            etc...
        ]

        Callers:
        - self.handle_merged_state
        """
        if len(devices) == 0:
            return
        install_options = ImageInstallOptions(self.module)
        # TODO:2 Need a way to call refresh() once in __init__() and mock in unit tests
        self.switch_details.refresh()
        for device in devices:
            self.log_msg(f"REMOVE: {self.class_name}._verify_install_options: device: {device}")
            self.switch_details.ip_address = device.get("ip_address")
            install_options.serial_number = self.switch_details.serial_number
            install_options.policy_name = device["policy"]
            install_options.epld = device["upgrade"]["epld"]
            install_options.issu = device["upgrade"]["nxos"]
            install_options.refresh()
            if install_options.status not in ["Success", "Skipped"] and device["upgrade"]["nxos"] is True:
                msg = f"NXOS upgrade is set to True for switch  "
                msg += f"{device['ip_address']}, but the image policy "
                msg += f"{install_options.policy_name} does not contain an "
                msg += f"NX-OS image"
                self.module.fail_json(msg)
            if install_options.epld_modules is None and device["upgrade"]["epld"] is True:
                msg = f"EPLD upgrade is set to True for switch "
                msg += f"{device['ip_address']}, but the image policy "
                msg += f"{install_options.policy_name} does not contain an "
                msg += f"EPLD image."
                self.module.fail_json(msg)

    def _upgrade_images(self, devices):
        """
        Upgrade the switch(es) to the specified image

        Callers:
        - handle_merged_state
        """
        self.log_msg(f"REMOVE: {self.class_name}._upgrade_images: devices: {devices}")
        upgrade = ImageUpgrade(self.module)
        upgrade.devices = devices
        # TODO:2 Discuss with Mike/Shangxin. Upgrade option handling mutex options.
        # I'm leaning toward doing this in ImageUpgrade().validate_options()
        # which would cover the various scenarios and fail_json() on invalid
        # combinations.
        # For epld upgrade disrutive must be True and non_disruptive must be False
        # upgrade.epld_upgrade = True
        # upgrade.disruptive = True
        # upgrade.non_disruptive = False
        # upgrade.epld_module = "ALL"
        upgrade.commit()

    def handle_merged_state(self):
        """
        Update the switch policy if it has changed.
        Stage the image if requested.
        Validate the image if requested.
        Upgrade the image if requested.

        Caller: main()
        """
        # TODO:1 Replace these with ImagePolicyAction
        # See commented code below
        self._build_policy_attach_payload()
        self._send_policy_attach_payload()

        # Use (or not) below for policy attach/detach
        # instance = ImagePolicyAction(self.module)
        # instance.policy_name = "NR3F"
        # instance.action = "attach" # or detach
        # instance.serial_numbers = ["FDO211218GC", "FDO211218HH"]
        # instance.commit()
        # policy_attach_devices = []
        # policy_detach_devices = []

        stage_devices = []
        validate_devices = []
        upgrade_devices = []

        # TODO:2 Need a way to call refresh() once in __init__() and mock in unit tests
        self.switch_details.refresh()
        for switch in self.need:
            msg = f"REMOVE: {self.class_name}.handle_merged_state: switch: {switch}"
            self.log_msg(msg)
            self.switch_details.ip_address = switch.get("ip_address")
            device = {}
            device["serial_number"] = self.switch_details.serial_number
            self.have.ip_address = self.switch_details.ip_address
            device["policy_name"] = switch.get("policy")
            device["ip_address"] = self.switch_details.ip_address
            if switch.get("stage") is not False:
                stage_devices.append(device["serial_number"])
            if switch.get("validate") is not False:
                validate_devices.append(device["serial_number"])
            if (
                switch.get("upgrade").get("nxos") is not False or
                switch.get("upgrade").get("epld") is not False):
                upgrade_devices.append(switch)

        msg = f"REMOVE: {self.class_name}.handle_merged_state: stage_devices: {stage_devices}"
        self.log_msg(msg)
        self._stage_images(stage_devices)

        self.log_msg(
            f"REMOVE: {self.class_name}.handle_merged_state: validate_devices: {validate_devices}"
        )
        self._validate_images(validate_devices)

        self.log_msg(
            f"REMOVE: {self.class_name}.handle_merged_state: upgrade_devices: {upgrade_devices}"
        )
        self._verify_install_options(upgrade_devices)
        self._upgrade_images(upgrade_devices)

    def handle_deleted_state(self):
        """
        Delete the image policy from the switch(es)

        Caller: main()
        """
        msg = f"REMOVE: {self.class_name}.handle_deleted_state: "
        msg += f"Entered with self.need {self.need}"
        self.log_msg(msg)
        detach_policy_devices = {}
        # TODO:2 Need a way to call refresh() once in __init__() and mock in unit tests
        self.switch_details.refresh()
        self.image_policies.refresh()
        for switch in self.need:
            self.switch_details.ip_address = switch.get("ip_address")
            self.image_policies.policy_name = switch.get("policy")
            # if self.image_policies.name is None:
            #     continue
            if self.image_policies.name not in detach_policy_devices:
                detach_policy_devices[self.image_policies.policy_name] = []
            detach_policy_devices[self.image_policies.policy_name].append(
                self.switch_details.serial_number
            )
        msg = f"REMOVE: {self.class_name}.handle_deleted_state: "
        msg += f"detach_policy_devices: {detach_policy_devices}"
        self.log_msg(msg)

        if len(detach_policy_devices) == 0:
            self.result = dict(changed=False, diff=[], response=[])
            return
        instance = ImagePolicyAction(self.module)
        for policy_name in detach_policy_devices:
            msg = f"REMOVE: {self.class_name}.handle_deleted_state: "
            msg += f"detach policy_name: {policy_name}"
            msg += f" from devices: {detach_policy_devices[policy_name]}"
            self.log_msg(msg)
            instance.policy_name = policy_name
            instance.action = "detach"
            instance.serial_numbers = detach_policy_devices[policy_name]
            instance.commit()

    def handle_query_state(self):
        """
        Return the ISSU state of the switch(es) listed in the playbook

        Caller: main()
        """
        instance = SwitchIssuDetailsByIpAddress(self.module)
        instance.refresh()
        msg = f"REMOVE: {self.class_name}.handle_query_state: "
        msg += f"Entered. self.need {self.need}"
        self.log_msg(msg)
        query_devices = []
        for switch in self.need:
            instance.ip_address = switch.get("ip_address")
            if instance.filtered_data is None:
                continue
            query_devices.append(instance.filtered_data)
        msg = f"REMOVE: {self.class_name}.handle_query_state: "
        msg += f"query_policies: {query_devices}"
        self.log_msg(msg)
        self.result["response"] = query_devices
        self.result["diff"] = []
        self.result["changed"] = False


    def _failure(self, resp):
        """
        Caller: self.attach_policies()

        This came from dcnm_inventory.py, but doesn't seem to be correct
        for the case where resp["DATA"] does not exist?

        If resp["DATA"] does not exist, the contents of the
        if block don't seem to actually do anything:
            - data will be None
            - Hence, data.get("stackTrace") will also be None
            - Hence, data.update() and res.update() are never executed

        So, the only two lines that will actually ever be executed are
        the happy path:

        res = copy.deepcopy(resp)
        self.module.fail_json(msg=res)
        """
        res = copy.deepcopy(resp)

        if not resp.get("DATA"):
            data = copy.deepcopy(resp.get("DATA"))
            if data.get("stackTrace"):
                data.update(
                    {"stackTrace": "Stack trace is hidden, use '-vvvvv' to print it"}
                )
                res.update({"DATA": data})

        self.module.fail_json(msg=res)





def main():
    """main entry point for module execution"""

    element_spec = dict(
        config=dict(required=True, type="dict"),
        state=dict(default="merged", choices=["merged", "deleted", "query"]),
    )

    ansible_module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)
    task_module = ImageUpgradeTask(ansible_module)
    task_module.validate_input()
    task_module.get_have()
    task_module.get_want()

    if ansible_module.params["state"] == "merged":
        task_module.get_need_merged()
    elif ansible_module.params["state"] == "deleted":
        task_module.get_need_deleted()
    elif ansible_module.params["state"] == "query":
        task_module.get_need_query()

    if ansible_module.params["state"] == "query":
        task_module.result["changed"] = False
    if ansible_module.params["state"] in ["merged", "deleted"]:
        if task_module.need:
            task_module.result["changed"] = True
        else:
            ansible_module.exit_json(**task_module.result)

    if ansible_module.check_mode:
        task_module.result["changed"] = False
        ansible_module.exit_json(**task_module.result)

    if task_module.need:
        if ansible_module.params["state"] == "merged":
            task_module.handle_merged_state()
        elif ansible_module.params["state"] == "deleted":
            task_module.handle_deleted_state()
        elif ansible_module.params["state"] == "query":
            task_module.handle_query_state()

    ansible_module.exit_json(**task_module.result)


if __name__ == "__main__":
    main()