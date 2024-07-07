#!/usr/bin/python
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
# pylint: disable=wrong-import-position
from __future__ import absolute_import, division, print_function

__metaclass__ = type
__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

DOCUMENTATION = """
---
module: dcnm_image_upgrade
short_description: Image management for Nexus switches
version_added: "3.5.0"
description:
    - Stage, validate, upgrade images.
    - Attach, detach, image policies.
    - Query device issu details.
author: Allen Robel (@quantumonion)
options:
    state:
        description:
        - The state of the feature or object after module completion.
        - I(merged), I(deleted), and I(query) states are supported.
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
        required: true
        suboptions:
            policy:
                description:
                - Image policy name
                type: str
                required: true
            stage:
                description:
                - Stage (True) or unstage (False) an image policy
                type: bool
                required: false
                default: True
            validate:
                description:
                - Validate (True) or do not validate (False) the image after staging.
                - If True, triggers NX-OS to validate that the image is compatible with the switch platform hardware.
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
                        - If epld is true, options.nxos.mode must be set to disruptive
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
                                type: str
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
                                type: str
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
                                        type: str
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
                                        type: str
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

# merged:
#   Attach image policy to one or more devices.
#   Stage image on one or more devices.
#   Validate image on one or more devices.
#   Upgrade image on one or more devices.

# query:
#   Return ISSU details for one or more devices.

# deleted:
#   Delete image policy from one or more devices


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
                        mode: disruptive
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
                                mode: disruptive
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

# Query ISSU details for three devices
    -   name: query switch ISSU status
        cisco.dcnm.dcnm_image_upgrade:
            state: query
            config:
                policy: KMR5
                switches:
                -   ip_address: 192.168.1.1
                    policy: OR1F
                -   ip_address: 192.168.1.2
                    policy: NR2F
                -   ip_address: 192.168.1.3 # will query policy KMR5
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

"""


import copy
import inspect
import json
import logging

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log_v2 import \
    Log
from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts import \
    MergeDicts
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_merge_defaults import \
    ParamsMergeDefaults
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate import \
    ParamsValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_policy_action import \
    ImagePolicyAction
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_stage import \
    ImageStage
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_upgrade import \
    ImageUpgrade
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_upgrade_common import \
    ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_upgrade_task_result import \
    ImageUpgradeTaskResult
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_validate import \
    ImageValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.install_options import \
    ImageInstallOptions
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.switch_details import \
    SwitchDetails
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.switch_issu_details import \
    SwitchIssuDetailsByIpAddress


class ImageUpgradeTask(ImageUpgradeCommon):
    """
    Classes and methods for Ansible support of Nexus image upgrade.

    Ansible states "merged", "deleted", and "query" are implemented.

    merged: stage, validate, upgrade image for one or more devices
    deleted: delete image policy from one or more devices
    query: return switch issu details for one or more devices
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ImageUpgradeTask()")

        self.endpoints = ApiEndpoints()

        self.have = None
        self.idempotent_want = None
        # populated in self._merge_global_and_switch_configs()
        self.switch_configs = []

        self.path = None
        self.verb = None

        self.config = ansible_module.params.get("config", {})

        if not isinstance(self.config, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "expected dict type for self.config. "
            msg += f"got {type(self.config).__name__}"
            self.ansible_module.fail_json(msg)

        self.check_mode = False

        self.validated = {}
        self.want = []
        self.need = []

        self.task_result = ImageUpgradeTaskResult(self.ansible_module)
        self.task_result.changed = False

        self.switch_details = SwitchDetails(self.ansible_module)
        self.image_policies = ImagePolicies(self.ansible_module)

    def get_have(self) -> None:
        """
        Caller: main()

        Determine current switch ISSU state on the controller
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.have = SwitchIssuDetailsByIpAddress(self.ansible_module)
        self.have.refresh()

    def get_want(self) -> None:
        """
        Caller: main()

        Update self.want for all switches defined in the playbook
        """
        msg = "Calling _merge_global_and_switch_configs with "
        msg += f"self.config: {json.dumps(self.config, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self._merge_global_and_switch_configs(self.config)

        self._merge_defaults_to_switch_configs()

        msg = "Calling _validate_switch_configs with self.switch_configs: "
        msg += f"{json.dumps(self.switch_configs, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self._validate_switch_configs()

        self.want = self.switch_configs

        msg = f"self.want: {json.dumps(self.want, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if len(self.want) == 0:
            self.ansible_module.exit_json(**self.task_result.module_result)

    def _build_idempotent_want(self, want) -> None:
        """
        Build an itempotent want item based on the have item contents.

        The have item is obtained from an instance of SwitchIssuDetails
        created in self.get_have().

        Caller: self.get_need_merged()

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

        """
        msg = f"want: {json.dumps(want, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.have.filter = want["ip_address"]

        want["policy_changed"] = True
        # The switch does not have an image policy attached.
        # idempotent_want == want with policy_changed = True
        if self.have.serial_number is None:
            self.idempotent_want = copy.deepcopy(want)
            return

        # The switch has an image policy attached which is
        # different from the want policy.
        # idempotent_want == want with policy_changed = True
        if want["policy"] != self.have.policy:
            self.idempotent_want = copy.deepcopy(want)
            return

        # start with a copy of the want item
        self.idempotent_want = copy.deepcopy(want)
        # Give an indication to the caller that the policy has not changed
        # We can use this later to determine if we need to do anything in
        # the case where the image is already staged and/or upgraded.
        self.idempotent_want["policy_changed"] = False

        # if the image is already staged, don't stage it again
        if self.have.image_staged == "Success":
            self.idempotent_want["stage"] = False
        # if the image is already validated, don't validate it again
        if self.have.validated == "Success":
            self.idempotent_want["validate"] = False

        msg = f"self.have.reason: {self.have.reason}, "
        msg += f"self.have.policy: {self.have.policy}, "
        msg += f"idempotent_want[policy]: {self.idempotent_want['policy']}, "
        msg += f"self.have.upgrade: {self.have.upgrade}"
        self.log.debug(msg)

        # if the image is already upgraded, don't upgrade it again
        if (
            self.have.reason == "Upgrade"
            and self.have.policy == self.idempotent_want["policy"]
            # If upgrade is other than Success, we need to try to upgrade
            # again.  So only change upgrade.nxos if upgrade is Success.
            and self.have.upgrade == "Success"
        ):
            msg = "Set upgrade nxos to False"
            self.log.debug(msg)
            self.idempotent_want["upgrade"]["nxos"] = False

        # Get relevant install options from the controller
        # based on the options in our idempotent_want item
        instance = ImageInstallOptions(self.ansible_module)
        instance.policy_name = self.idempotent_want["policy"]
        instance.serial_number = self.have.serial_number

        instance.epld = want.get("upgrade", {}).get("epld", False)
        instance.issu = self.idempotent_want.get("upgrade", {}).get("nxos", False)
        instance.package_install = (
            want.get("options", {}).get("package", {}).get("install", False)
        )
        instance.refresh()

        msg = "ImageInstallOptions.response: "
        msg += f"{json.dumps(instance.response_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "self.idempotent_want PRE EPLD CHECK: "
        msg += f"{json.dumps(self.idempotent_want, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # if InstallOptions indicates that EPLD is already upgraded,
        # don't upgrade it again.
        if self.needs_epld_upgrade(instance.epld_modules) is False:
            self.idempotent_want["upgrade"]["epld"] = False

        msg = "self.idempotent_want POST EPLD CHECK: "
        msg += f"{json.dumps(self.idempotent_want, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def get_need_merged(self) -> None:
        """
        Caller: main()

        For merged state, populate self.need list() with items from
        our want list that are not in our have list.  These items will
        be sent to the controller.
        """
        need: list[dict] = []

        msg = "self.want: "
        msg += f"{json.dumps(self.want, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        for want in self.want:
            self.have.filter = want["ip_address"]

            msg = f"self.have.serial_number: {self.have.serial_number}"
            self.log.debug(msg)

            if self.have.serial_number is not None:
                self._build_idempotent_want(want)

                msg = "self.idempotent_want: "
                msg += f"{json.dumps(self.idempotent_want, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                test_idempotence = set()
                test_idempotence.add(self.idempotent_want["policy_changed"])
                test_idempotence.add(self.idempotent_want["stage"])
                test_idempotence.add(self.idempotent_want["upgrade"]["nxos"])
                test_idempotence.add(self.idempotent_want["upgrade"]["epld"])
                test_idempotence.add(
                    self.idempotent_want["options"]["package"]["install"]
                )
                # NOTE: InstallOptions doesn't seem to have a way to determine package uninstall.
                # NOTE: For now, we'll comment this out so that it doesn't muck up idempotence.
                # test_idempotence.add(self.idempotent_want["options"]["package"]["uninstall"])
                if True not in test_idempotence:
                    continue
                need.append(self.idempotent_want)
        self.need = copy.copy(need)

    def get_need_deleted(self) -> None:
        """
        Caller: main()

        For deleted state, populate self.need list() with items from our want
        list that are not in our have list.  These items will be sent to
        the controller.

        Policies are detached only if the policy name matches.
        """
        need = []
        for want in self.want:
            self.have.filter = want["ip_address"]
            if self.have.serial_number is None:
                continue
            if self.have.policy is None:
                continue
            if self.have.policy != want["policy"]:
                continue
            need.append(want)
        self.need = copy.copy(need)

    def get_need_query(self) -> None:
        """
        Caller: main()

        For query state, populate self.need list() with all items from
        our want list.  These items will be sent to the controller.

        policy name is ignored for query state.
        """
        need = []
        for want in self.want:
            need.append(want)
        self.need = copy.copy(need)

    def _build_params_spec(self) -> dict:
        method_name = inspect.stack()[0][3]
        if self.ansible_module.params["state"] == "merged":
            return self._build_params_spec_for_merged_state()
        if self.ansible_module.params["state"] == "deleted":
            return self._build_params_spec_for_merged_state()
        if self.ansible_module.params["state"] == "query":
            return self._build_params_spec_for_query_state()
        msg = f"{self.class_name}.{method_name}: "
        msg += f"Unsupported state: {self.ansible_module.params['state']}"
        self.ansible_module.fail_json(msg)
        return None  # we never reach this, but it makes pylint happy.

    @staticmethod
    def _build_params_spec_for_merged_state() -> dict:
        """
        Build the specs for the parameters expected when state == merged.

        Caller: _validate_switch_configs()
        Return: params_spec, a dictionary containing playbook
                parameter specifications.
        """
        params_spec: dict = {}
        params_spec["ip_address"] = {}
        params_spec["ip_address"]["required"] = True
        params_spec["ip_address"]["type"] = "ipv4"

        params_spec["policy"] = {}
        params_spec["policy"]["required"] = False
        params_spec["policy"]["type"] = "str"

        params_spec["reboot"] = {}
        params_spec["reboot"]["required"] = False
        params_spec["reboot"]["type"] = "bool"
        params_spec["reboot"]["default"] = False

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
        params_spec["upgrade"]["epld"] = {}
        params_spec["upgrade"]["epld"]["required"] = False
        params_spec["upgrade"]["epld"]["type"] = "bool"
        params_spec["upgrade"]["epld"]["default"] = False
        params_spec["upgrade"]["nxos"] = {}
        params_spec["upgrade"]["nxos"]["required"] = False
        params_spec["upgrade"]["nxos"]["type"] = "bool"
        params_spec["upgrade"]["nxos"]["default"] = True

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
        params_spec[section][sub_section]["mode"]["choices"] = [
            "disruptive",
            "non_disruptive",
            "force_non_disruptive",
        ]

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
        params_spec[section][sub_section]["module"]["required"] = False
        params_spec[section][sub_section]["module"]["type"] = ["str", "int"]
        params_spec[section][sub_section]["module"]["preferred_type"] = "str"
        params_spec[section][sub_section]["module"]["default"] = "ALL"
        params_spec[section][sub_section]["module"]["choices"] = [
            str(x) for x in range(1, 33)
        ]
        params_spec[section][sub_section]["module"]["choices"].extend(
            list(range(1, 33))
        )
        params_spec[section][sub_section]["module"]["choices"].append("ALL")

        params_spec[section][sub_section]["golden"] = {}
        params_spec[section][sub_section]["golden"]["required"] = False
        params_spec[section][sub_section]["golden"]["type"] = "bool"
        params_spec[section][sub_section]["golden"]["default"] = False

        sub_section = "reboot"
        params_spec[section][sub_section] = {}
        params_spec[section][sub_section]["required"] = False
        params_spec[section][sub_section]["type"] = "dict"
        params_spec[section][sub_section]["default"] = {}

        params_spec[section][sub_section]["config_reload"] = {}
        params_spec[section][sub_section]["config_reload"]["required"] = False
        params_spec[section][sub_section]["config_reload"]["type"] = "bool"
        params_spec[section][sub_section]["config_reload"]["default"] = False

        params_spec[section][sub_section]["write_erase"] = {}
        params_spec[section][sub_section]["write_erase"]["required"] = False
        params_spec[section][sub_section]["write_erase"]["type"] = "bool"
        params_spec[section][sub_section]["write_erase"]["default"] = False

        sub_section = "package"
        params_spec[section][sub_section] = {}
        params_spec[section][sub_section]["required"] = False
        params_spec[section][sub_section]["type"] = "dict"
        params_spec[section][sub_section]["default"] = {}

        params_spec[section][sub_section]["install"] = {}
        params_spec[section][sub_section]["install"]["required"] = False
        params_spec[section][sub_section]["install"]["type"] = "bool"
        params_spec[section][sub_section]["install"]["default"] = False

        params_spec[section][sub_section]["uninstall"] = {}
        params_spec[section][sub_section]["uninstall"]["required"] = False
        params_spec[section][sub_section]["uninstall"]["type"] = "bool"
        params_spec[section][sub_section]["uninstall"]["default"] = False

        return copy.deepcopy(params_spec)

    @staticmethod
    def _build_params_spec_for_query_state() -> dict:
        """
        Build the specs for the parameters expected when state == query.

        Caller: _validate_switch_configs()
        Return: params_spec, a dictionary containing playbook
                parameter specifications.
        """
        params_spec: dict = {}
        params_spec["ip_address"] = {}
        params_spec["ip_address"]["required"] = True
        params_spec["ip_address"]["type"] = "ipv4"

        return copy.deepcopy(params_spec)

    def _merge_global_and_switch_configs(self, config) -> None:
        """
        Merge the global config with each switch config and
        populate list of merged configs self.switch_configs.

        Merge rules:
        1.  switch_config takes precedence over global_config.
        2.  If switch_config is missing a parameter, use parameter
            from global_config.
        3.  If switch_config has a parameter, use it.
        4.  If global_config and switch_config are both missing a
            parameter, use the parameter's default value, if there
            is one (see self._merge_defaults_to_switch_configs)
        5.  If global_config and switch_config are both missing a
            mandatory parameter, fail (see self._validate_switch_configs)
        """
        method_name = inspect.stack()[0][3]

        if not config.get("switches"):
            msg = f"{self.class_name}.{method_name}: "
            msg += "playbook is missing list of switches"
            self.ansible_module.fail_json(msg)

        self.switch_configs = []
        merged_configs = []
        for switch in config["switches"]:
            # we need to rebuild global_config in this loop
            # because merge_dicts modifies it in place
            global_config = copy.deepcopy(config)
            global_config.pop("switches", None)
            msg = (
                f"global_config: {json.dumps(global_config, indent=4, sort_keys=True)}"
            )
            self.log.debug(msg)

            msg = f"switch PRE_MERGE : {json.dumps(switch, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            merge_dicts = MergeDicts(self.ansible_module)
            merge_dicts.dict1 = global_config
            merge_dicts.dict2 = switch
            merge_dicts.commit()
            switch_config = merge_dicts.dict_merged

            msg = f"switch POST_MERGE: {json.dumps(switch_config, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            merged_configs.append(switch_config)
        self.switch_configs = copy.copy(merged_configs)

    def _merge_defaults_to_switch_configs(self) -> None:
        """
        For any items in config which are not set, apply the default
        value from params_spec (if a default value exists).
        """
        configs_to_merge = copy.copy(self.switch_configs)
        merged_configs = []
        merge = ParamsMergeDefaults(self.ansible_module)
        merge.params_spec = self._build_params_spec()
        for switch_config in configs_to_merge:
            merge.parameters = switch_config
            merge.commit()
            merged_configs.append(merge.merged_parameters)
        self.switch_configs = copy.copy(merged_configs)

    def _validate_switch_configs(self) -> None:
        """
        Verify parameters for each switch
        - fail_json if any parameters are not valid
        - fail_json if any mandatory parameters are missing

        Callers:
            - self.get_want
        """
        validator = ParamsValidate(self.ansible_module)
        validator.params_spec = self._build_params_spec()

        for switch in self.switch_configs:
            validator.parameters = switch
            validator.commit()

    def _attach_or_detach_image_policy(self, action=None) -> None:
        """
        Attach or detach image policies to/from switches
        action valid values: attach, detach

        Caller:
            - self.handle_merged_state
            - self.handle_deleted_state

        NOTES:
        - Sanity checking for action is done in ImagePolicyAction
        """
        msg = f"ENTERED: action: {action}"
        self.log.debug(msg)

        serial_numbers_to_update: dict = {}
        self.switch_details.refresh()
        self.image_policies.refresh()

        for switch in self.need:
            self.switch_details.ip_address = switch.get("ip_address")
            self.image_policies.policy_name = switch.get("policy")
            # ImagePolicyAction wants a policy name and a list of serial_number
            # Build dictionary, serial_numbers_to_udate, keyed on policy name
            # whose value is the list of serial numbers to attach/detach.
            if self.image_policies.name not in serial_numbers_to_update:
                serial_numbers_to_update[self.image_policies.policy_name] = []

            serial_numbers_to_update[self.image_policies.policy_name].append(
                self.switch_details.serial_number
            )

        instance = ImagePolicyAction(self.ansible_module)
        if len(serial_numbers_to_update) == 0:
            msg = f"No policies to {action}"
            self.log.debug(msg)

            if action == "attach":
                self.task_result.diff_attach_policy = instance.diff_null
                self.task_result.diff = instance.diff_null
            if action == "detach":
                self.task_result.diff_detach_policy = instance.diff_null
                self.task_result.diff = instance.diff_null
            return

        for key, value in serial_numbers_to_update.items():
            instance.policy_name = key
            instance.action = action
            instance.serial_numbers = value
            instance.commit()
            if action == "attach":
                self.task_result.response_attach_policy = copy.deepcopy(
                    instance.response_current
                )
                self.task_result.response = copy.deepcopy(instance.response_current)
            if action == "detach":
                self.task_result.response_detach_policy = copy.deepcopy(
                    instance.response_current
                )
                self.task_result.response = copy.deepcopy(instance.response_current)

        for diff in instance.diff:
            msg = (
                f"{instance.action} diff: {json.dumps(diff, indent=4, sort_keys=True)}"
            )
            self.log.debug(msg)
            if action == "attach":
                self.task_result.diff_attach_policy = copy.deepcopy(diff)
                self.task_result.diff = copy.deepcopy(diff)
            elif action == "detach":
                self.task_result.diff_detach_policy = copy.deepcopy(diff)
                self.task_result.diff = copy.deepcopy(diff)

    def _stage_images(self, serial_numbers) -> None:
        """
        Initiate image staging to the switch(es) associated
        with serial_numbers

        Callers:
        - handle_merged_state
        """
        msg = f"serial_numbers: {serial_numbers}"
        self.log.debug(msg)

        instance = ImageStage(self.ansible_module)
        instance.serial_numbers = serial_numbers
        instance.commit()
        for diff in instance.diff:
            msg = "adding diff to task_result.diff_stage: "
            msg += f"{json.dumps(diff, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            self.task_result.diff_stage = copy.deepcopy(diff)
            self.task_result.diff = copy.deepcopy(diff)
        for response in instance.response:
            msg = "adding response to task_result.response_stage: "
            msg += f"{json.dumps(response, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            self.task_result.response_stage = copy.deepcopy(response)
            self.task_result.response = copy.deepcopy(response)

    def _validate_images(self, serial_numbers) -> None:
        """
        Validate the image staged to the switch(es)

        Callers:
        - handle_merged_state
        """
        msg = f"serial_numbers: {serial_numbers}"
        self.log.debug(msg)

        instance = ImageValidate(self.ansible_module)
        instance.serial_numbers = serial_numbers
        instance.commit()
        for diff in instance.diff:
            msg = "adding diff to task_result.diff_validate: "
            msg += f"{json.dumps(diff, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            self.task_result.diff_validate = copy.deepcopy(diff)
            self.task_result.diff = copy.deepcopy(diff)
        for response in instance.response:
            msg = "adding response to task_result.response_validate: "
            msg += f"{json.dumps(response, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            self.task_result.response_validate = copy.deepcopy(response)
            self.task_result.response = copy.deepcopy(response)

    def _verify_install_options(self, devices) -> None:
        """
        Verify that the install options for the device(s) are valid

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
        method_name = inspect.stack()[0][3]

        if len(devices) == 0:
            return

        install_options = ImageInstallOptions(self.ansible_module)
        self.switch_details.refresh()

        verify_devices = copy.deepcopy(devices)

        for device in verify_devices:
            msg = f"device: {json.dumps(device, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            self.switch_details.ip_address = device.get("ip_address")
            install_options.serial_number = self.switch_details.serial_number
            install_options.policy_name = device.get("policy")
            install_options.epld = device.get("upgrade", {}).get("epld", False)
            install_options.issu = device.get("upgrade", {}).get("nxos", False)
            install_options.refresh()

            msg = "install_options.response_data: "
            msg += (
                f"{json.dumps(install_options.response_data, indent=4, sort_keys=True)}"
            )
            self.log.debug(msg)

            if (
                install_options.status not in ["Success", "Skipped"]
                and device["upgrade"]["nxos"] is True
            ):
                msg = f"{self.class_name}.{method_name}: "
                msg += "NXOS upgrade is set to True for switch  "
                msg += f"{device['ip_address']}, but the image policy "
                msg += f"{install_options.policy_name} does not contain an "
                msg += "NX-OS image"
                self.ansible_module.fail_json(msg)

            msg = f"install_options.epld: {install_options.epld}"
            self.log.debug(msg)

            msg = "install_options.epld_modules: "
            msg += (
                f"{json.dumps(install_options.epld_modules, indent=4, sort_keys=True)}"
            )
            self.log.debug(msg)

            if install_options.epld_modules is None and install_options.epld is True:
                msg = f"{self.class_name}.{method_name}: "
                msg += "EPLD upgrade is set to True for switch "
                msg += f"{device['ip_address']}, but the image policy "
                msg += f"{install_options.policy_name} does not contain an "
                msg += "EPLD image."
                self.ansible_module.fail_json(msg)

    def needs_epld_upgrade(self, epld_modules) -> bool:
        """
        Determine if the switch needs an EPLD upgrade

        For all modules, compare EPLD oldVersion and newVersion.
        Returns:
        - True if newVersion > oldVersion for any module
        - False otherwise

        Callers:
        - self._build_idempotent_want
        """
        if epld_modules is None:
            return False
        if epld_modules.get("moduleList") is None:
            return False
        for module in epld_modules["moduleList"]:
            new_version = module.get("newVersion", "0x0")
            old_version = module.get("oldVersion", "0x0")
            # int(str, 0) enables python to guess the base
            # of the str when converting to int.  An
            # error is thrown without this.
            if int(new_version, 0) > int(old_version, 0):
                msg = f"(device: {module.get('deviceName')}), "
                msg += f"(IP: {module.get('ipAddress')}), "
                msg += f"(module#: {module.get('module')}), "
                msg += f"(module: {module.get('moduleType')}), "
                msg += f"new_version {new_version} > old_version {old_version}, "
                msg += "returning True"
                self.log.debug(msg)
                return True
        return False

    def _upgrade_images(self, devices) -> None:
        """
        Upgrade the switch(es) to the specified image

        Callers:
        - handle_merged_state
        """
        upgrade = ImageUpgrade(self.ansible_module)
        upgrade.devices = devices
        upgrade.commit()
        for diff in upgrade.diff:
            msg = "adding diff to diff_upgrade: "
            msg += f"{json.dumps(diff, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            self.task_result.diff_upgrade = copy.deepcopy(diff)
            self.task_result.diff = copy.deepcopy(diff)
        for response in upgrade.response:
            msg = "adding response to response_upgrade: "
            msg += f"{json.dumps(response, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            self.task_result.response_upgrade = copy.deepcopy(response)
            self.task_result.response = copy.deepcopy(response)

    def handle_merged_state(self) -> None:
        """
        Update the switch policy if it has changed.
        Stage the image if requested.
        Validate the image if requested.
        Upgrade the image if requested.

        Caller: main()
        """
        msg = "ENTERED"
        self.log.debug(msg)

        self._attach_or_detach_image_policy(action="attach")

        stage_devices: list[str] = []
        validate_devices: list[str] = []
        upgrade_devices: list[dict] = []

        self.switch_details.refresh()

        for switch in self.need:
            msg = f"switch: {json.dumps(switch, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            self.switch_details.ip_address = switch.get("ip_address")
            device = {}
            device["serial_number"] = self.switch_details.serial_number
            self.have.filter = self.switch_details.ip_address
            device["policy_name"] = switch.get("policy")
            device["ip_address"] = self.switch_details.ip_address

            if switch.get("stage") is not False:
                stage_devices.append(device["serial_number"])
            if switch.get("validate") is not False:
                validate_devices.append(device["serial_number"])
            if (
                switch.get("upgrade").get("nxos") is not False
                or switch.get("upgrade").get("epld") is not False
            ):
                upgrade_devices.append(switch)

        self._stage_images(stage_devices)
        self._validate_images(validate_devices)

        self._verify_install_options(upgrade_devices)
        self._upgrade_images(upgrade_devices)

    def handle_deleted_state(self) -> None:
        """
        Delete the image policy from the switch(es)

        Caller: main()
        """
        msg = "ENTERED"
        self.log.debug(msg)

        self._attach_or_detach_image_policy("detach")

    def handle_query_state(self) -> None:
        """
        Return the ISSU state of the switch(es) listed in the playbook

        Caller: main()
        """
        instance = SwitchIssuDetailsByIpAddress(self.ansible_module)
        instance.refresh()
        response_current = copy.deepcopy(instance.response_current)
        if "DATA" in response_current:
            response_current.pop("DATA")
        self.task_result.response_issu_status = copy.deepcopy(response_current)
        self.task_result.response = copy.deepcopy(response_current)
        for switch in self.need:
            instance.filter = switch.get("ip_address")
            msg = f"SwitchIssuDetailsByIpAddress.filter: {instance.filter}, "
            msg += f"SwitchIssuDetailsByIpAddress.filtered_data: {json.dumps(instance.filtered_data, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            if instance.filtered_data is None:
                continue
            self.task_result.diff_issu_status = instance.filtered_data
            self.task_result.diff = instance.filtered_data

    def _failure(self, resp) -> None:
        """
        Caller: self.attach_policies()
        """
        res = copy.deepcopy(resp)

        if resp.get("DATA"):
            data = copy.deepcopy(resp.get("DATA"))
            if data.get("stackTrace"):
                data.update(
                    {"stackTrace": "Stack trace is hidden, use '-vvvvv' to print it"}
                )
                res.update({"DATA": data})

        self.ansible_module.fail_json(msg=res)


def main():
    """main entry point for module execution"""

    element_spec = {
        "config": {"required": True, "type": "dict"},
        "state": {"default": "merged", "choices": ["merged", "deleted", "query"]},
    }

    ansible_module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)

    # Logging setup
    try:
        log = Log()
        log.commit()
    except ValueError as error:
        ansible_module.fail_json(str(error))

    task_module = ImageUpgradeTask(ansible_module)

    task_module.get_want()
    task_module.get_have()

    if ansible_module.params["state"] == "merged":
        task_module.get_need_merged()
    elif ansible_module.params["state"] == "deleted":
        task_module.get_need_deleted()
    elif ansible_module.params["state"] == "query":
        task_module.get_need_query()

    task_module.task_result.changed = False
    if len(task_module.need) == 0:
        ansible_module.exit_json(**task_module.task_result.module_result)

    if ansible_module.params["state"] in ["merged", "deleted"]:
        task_module.task_result.changed = True

    if ansible_module.params["state"] == "merged":
        task_module.handle_merged_state()
    elif ansible_module.params["state"] == "deleted":
        task_module.handle_deleted_state()
    elif ansible_module.params["state"] == "query":
        task_module.handle_query_state()

    ansible_module.exit_json(**task_module.task_result.module_result)


if __name__ == "__main__":
    main()
