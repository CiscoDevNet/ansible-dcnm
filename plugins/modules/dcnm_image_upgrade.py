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
from __future__ import absolute_import, division, print_function

__metaclass__ = type # pylint: disable=invalid-name
__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"
__email__ = "arobel@cisco.com"

DOCUMENTATION = """
---
module: dcnm_image_upgrade
short_description: Image management for Nexus switches
version_added: "0.9.0"
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
#
# merged:
#   Attach image policy to one or more devices.
#   Stage image on one or more devices.
#   Validate image on one or more devices.
#   Upgrade image on one or more devices.
#
# query:
#   Return ISSU details for one or more devices.
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
from typing import Any, Dict, List

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate import \
    ParamsValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policy_action import \
    ImagePolicyAction
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_stage import \
    ImageStage
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade import \
    ImageUpgrade
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import \
    ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_validate import \
    ImageValidate
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.install_options import \
    ImageInstallOptions
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_details import \
    SwitchDetails
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import \
    SwitchIssuDetailsByIpAddress
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send


class ImageUpgradeTask(ImageUpgradeCommon):
    """
    Classes and methods for Ansible support of Nexus image upgrade.

    Ansible states "merged", "deleted", and "query" are implemented.

    merged: stage, validate, upgrade image for one or more devices
    deleted: delete image policy from one or more devices
    query: return switch issu details for one or more devices
    """

    def __init__(self, module):
        super().__init__(module)
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self._init_defaults()
        self.endpoints = ApiEndpoints()
        self.have = None
        self.idempotent_want = None
        # populated in self._merge_global_and_switch_configs()
        self.switch_configs = []

        self.path = None
        self.verb = None

        # populated in self._build_policy_attach_payload()
        self.payloads = []

        self.config = module.params.get("config", {})

        if not isinstance(self.config, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "expected dict type for self.config. "
            msg += f"got {type(self.config).__name__}"
            self.module.fail_json(msg)

        self.check_mode = False

        self.validated = {}
        self.want = []
        self.need = []

        self.result = {"changed": False, "diff": [], "response": []}

        self.mandatory_global_keys = {"switches"}

        self.switch_details = SwitchDetails(self.module)
        self.image_policies = ImagePolicies(self.module)

    def _init_defaults(self):
        """
        Default values for playbook parameters.
        These are merged with playbook parameters in
        self._merge_defaults_to_switch_config()
        """
        self.defaults: Dict[str, Any] = {}
        self.defaults["options"] = {}
        self.defaults["options"]["epld"] = {}
        self.defaults["options"]["epld"]["module"] = "ALL"
        self.defaults["options"]["epld"]["golden"] = False
        self.defaults["options"]["nxos"] = {}
        self.defaults["options"]["nxos"]["mode"] = "disruptive"
        self.defaults["options"]["nxos"]["bios_force"] = False
        self.defaults["options"]["package"] = {}
        self.defaults["options"]["package"]["install"] = False
        self.defaults["options"]["package"]["uninstall"] = False
        self.defaults["options"]["reboot"] = {}
        self.defaults["options"]["reboot"]["config_reload"] = False
        self.defaults["options"]["reboot"]["write_erase"] = False
        self.defaults["reboot"] = False
        self.defaults["stage"] = True
        self.defaults["upgrade"] = {}
        self.defaults["upgrade"]["epld"] = False
        self.defaults["upgrade"]["nxos"] = True
        self.defaults["validate"] = True

    def get_have(self) -> None:
        """
        Caller: main()

        Determine current switch ISSU state on the controller
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.have = SwitchIssuDetailsByIpAddress(self.module)
        self.have.refresh()

    def get_want(self) -> None:
        """
        Caller: main()

        Update self.want for all switches defined in the playbook
        """
        method_name = inspect.stack()[0][3]

        msg = f"DEBUG: {self.class_name}.{method_name}: "
        msg += "Calling _merge_global_and_switch_configs with "
        msg += f"self.config: {json.dumps(self.config, indent=4, sort_keys=True)}"
        self.log_msg(msg)

        self._merge_global_and_switch_configs(self.config)

        self._merge_defaults_to_switch_configs()

        msg = f"DEBUG: {self.class_name}.{method_name}: "
        msg += "Calling _validate_switch_configs with self.switch_configs: "
        msg += f"{json.dumps(self.switch_configs, indent=4, sort_keys=True)}"
        self.log_msg(msg)

        self._validate_switch_configs()

        self.want = self.switch_configs

        msg = f"DEBUG: {self.class_name}.{method_name}: "
        msg += f"self.want: {json.dumps(self.want, indent=4, sort_keys=True)}"
        self.log_msg(msg)

        if len(self.want) == 0:
            self.result["changed"] = False
            self.exit_json(**self.result)

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
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        msg = f"DEBUG: {self.class_name}.{method_name}: "
        msg += f"want: {json.dumps(want, indent=4, sort_keys=True)}"
        self.log_msg(msg)

        self.have.ip_address = want["ip_address"]

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
        # if the image is already upgraded, don't upgrade it again
        if (
            self.have.status == "In-Sync"
            and self.have.reason == "Upgrade"
            and self.have.policy == want["policy"]
            # If upgrade is other than Success, we need to try to upgrade
            # again.  So only change upgrade.nxos if upgrade is Success.
            and self.have.upgrade == "Success"
        ):
            self.idempotent_want["upgrade"]["nxos"] = False

        # Get relevant install options from the controller
        # based on the options in our want item
        instance = ImageInstallOptions(self.module)
        instance.policy_name = want["policy"]
        instance.serial_number = self.have.serial_number

        instance.epld = want.get("upgrade", {}).get("epld", False)
        instance.issu = want.get("upgrade", {}).get("nxos", False)
        instance.package_install = (
            want.get("options", {}).get("package", {}).get("install", False)
        )
        instance.refresh()

        msg = f"DEBUG: {self.class_name}.{method_name}: "
        msg += "Calling ImageInstallOptions.response "
        msg += "instance.response: "
        msg += f"{json.dumps(instance.response_data, indent=4, sort_keys=True)}"
        self.log_msg(msg)

        msg = f"DEBUG: {self.class_name}.{method_name}: "
        msg += "self.idempotent_want PRE EPLD CHECK: "
        msg += f"{json.dumps(self.idempotent_want, indent=4, sort_keys=True)}"
        self.log_msg(msg)

        # if InstallOptions indicates that EPLD is already upgraded,
        # don't upgrade it again.
        if self.needs_epld_upgrade(instance.epld_modules) is False:
            self.idempotent_want["upgrade"]["epld"] = False

        msg = f"DEBUG: {self.class_name}.{method_name}: "
        msg += "self.idempotent_want POST EPLD CHECK: "
        msg += f"{json.dumps(self.idempotent_want, indent=4, sort_keys=True)}"
        self.log_msg(msg)

    def get_need_merged(self) -> None:
        """
        Caller: main()

        For merged state, populate self.need list() with items from
        our want list that are not in our have list.  These items will
        be sent to the controller.
        """
        method_name = inspect.stack()[0][3]
        need: List[Dict] = []

        msg = f"DEBUG: {self.class_name}.{method_name}: "
        msg += "self.want: "
        msg += f"{json.dumps(self.want, indent=4, sort_keys=True)}"
        self.log_msg(msg)

        for want in self.want:
            self.have.ip_address = want["ip_address"]

            msg = f"DEBUG: {self.class_name}.{method_name}: "
            msg += f"self.have.serial_number: {self.have.serial_number}"
            self.log_msg(msg)

            if self.have.serial_number is not None:
                self._build_idempotent_want(want)

                msg = f"DEBUG: {self.class_name}.{method_name}: "
                msg += "self.idempotent_want: "
                msg += f"{json.dumps(self.idempotent_want, indent=4, sort_keys=True)}"
                self.log_msg(msg)

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
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        need = []
        for want in self.want:
            self.have.ip_address = want["ip_address"]
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
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        need = []
        for want in self.want:
            need.append(want)
        self.need = copy.copy(need)

    @staticmethod
    def _build_params_spec_for_merged_state() -> Dict[str, Any]:
        """
        Build the specs for the parameters expected when state == merged.

        Caller: _validate_switch_configs()
        Return: params_spec, a dictionary containing playbook
                parameter specifications.
        """
        params_spec: Dict[str, Any] = {}
        params_spec["ip_address"] = {}
        params_spec["ip_address"]["required"] = True
        params_spec["ip_address"]["type"] = "ipv4"

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
    def _build_params_spec_for_query_state() -> Dict[str, Any]:
        """
        Build the specs for the parameters expected when state == query.

        Caller: _validate_switch_configs()
        Return: params_spec, a dictionary containing playbook
                parameter specifications.
        """
        params_spec: Dict[str, Any] = {}
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
            self.module.fail_json(msg)

        self.switch_configs = []
        merged_configs = []
        for switch in config["switches"]:
            # we need to rebuild global_config in this loop
            # because merge_dicts modifies it in place
            global_config = copy.deepcopy(config)
            global_config.pop("switches", None)
            msg = f"DEBUG: {self.class_name}.{method_name}: "
            msg += (
                f"global_config: {json.dumps(global_config, indent=4, sort_keys=True)}"
            )
            self.log_msg(msg)

            msg = f"DEBUG: {self.class_name}.{method_name}: "
            msg += f"switch PRE_MERGE : {json.dumps(switch, indent=4, sort_keys=True)}"
            self.log_msg(msg)

            switch_config = self.merge_dicts(global_config, switch)

            msg = f"DEBUG: {self.class_name}.{method_name}: "
            msg += f"switch POST_MERGE: {json.dumps(switch_config, indent=4, sort_keys=True)}"
            self.log_msg(msg)

            merged_configs.append(switch_config)
        self.switch_configs = copy.copy(merged_configs)

    def _merge_defaults_to_switch_configs(self) -> None:
        """
        For any items in config which are not set, apply the default
        value from self.defaults.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        configs_to_merge = copy.copy(self.switch_configs)
        merged_configs = []
        for switch_config in configs_to_merge:
            # we need to rebuild default_config in this loop
            # because merge_dicts modifies it in place
            merged_config = self.merge_dicts(
                copy.deepcopy(self.defaults), copy.deepcopy(switch_config)
            )

            msg = f"DEBUG: {self.class_name}.{method_name}: "
            msg += (
                f"switch_config: {json.dumps(switch_config, indent=4, sort_keys=True)}"
            )
            self.log_msg(msg)

            msg = f"DEBUG: {self.class_name}.{method_name}: "
            msg += (
                f"merged_config: {json.dumps(merged_config, indent=4, sort_keys=True)}"
            )
            self.log_msg(msg)
            merged_configs.append(merged_config)
        self.switch_configs = copy.copy(merged_configs)

    def _validate_switch_configs(self) -> None:
        """
        Verify parameters for each switch
        - fail_json if any parameters are not valid
        - fail_json if any mandatory parameters are missing

        Callers:
            - self.get_want
        """
        method_name = inspect.stack()[0][3]
        validator = ParamsValidate(self.module)
        if self.module.params.get("state") == "merged":
            validator.params_spec = self._build_params_spec_for_merged_state()
        if self.module.params.get("state") == "deleted":
            validator.params_spec = self._build_params_spec_for_merged_state()
        if self.module.params.get("state") == "query":
            validator.params_spec = self._build_params_spec_for_query_state()

        for switch in self.switch_configs:
            validator.parameters = switch
            validator.validate()

    def _build_policy_attach_payload(self) -> None:
        """
        Build the payload for the policy attach request
        Verify that the image policy exists on the controller
        Verify that the image policy supports the switch platform

        Callers:
            - self.handle_merged_state
        """
        method_name = inspect.stack()[0][3]

        self.payloads = []
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
                msg = f"{self.class_name}.{method_name}: "
                msg += f"policy {switch.get('policy')} does not exist on "
                msg += "the controller"
                self.module.fail_json(msg)

            # Fail if the image policy does not support the switch platform
            if self.switch_details.platform not in self.image_policies.platform:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"policy {switch.get('policy')} does not support "
                msg += f"platform {self.switch_details.platform}. "
                msg += f"Policy {switch.get('policy')} "
                msg += "supports the following platform(s): "
                msg += f"{self.image_policies.platform}"
                self.module.fail_json(msg)

            payload: Dict[str, Any] = {}
            payload["policyName"] = self.image_policies.name
            # switch_details.host_name is always None in 12.1.2e
            # so we're using logical_name instead
            payload["hostName"] = self.switch_details.logical_name
            payload["ipAddr"] = self.switch_details.ip_address
            payload["platform"] = self.switch_details.platform
            payload["serialNumber"] = self.switch_details.serial_number
            # payload["bootstrapMode"] = switch.get('bootstrap_mode')

            for key, value in payload.items():
                if value is None:
                    msg = f"{self.class_name}.{method_name}: "
                    msg += f"Unable to determine {key} for switch "
                    msg += f"{switch.get('ip_address')}. "
                    msg += "Please verify that the switch is managed by "
                    msg += "the controller."
                    self.module.fail_json(msg)

            self.payloads.append(payload)

    def _send_policy_attach_payload(self) -> None:
        """
        Send the policy attach payload to the controller and
        handle the response

        Callers:
            - self.handle_merged_state
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        if len(self.payloads) == 0:
            return

        self.path = self.endpoints.policy_attach.get("path")
        self.verb = self.endpoints.policy_attach.get("verb")

        payload: Dict[str, Any] = {}
        payload["mappingList"] = self.payloads
        response = dcnm_send(
            self.module, self.verb, self.path, data=json.dumps(payload)
        )
        result = self._handle_response(response, self.verb)

        if not result["success"]:
            self._failure(response)

    def _stage_images(self, serial_numbers) -> None:
        """
        Initiate image staging to the switch(es) associated
        with serial_numbers

        Callers:
        - handle_merged_state
        """
        method_name = inspect.stack()[0][3]

        msg = f"DEBUG: {self.class_name}.{method_name}: "
        msg += f"serial_numbers: {serial_numbers}"
        self.log_msg(msg)

        instance = ImageStage(self.module)
        instance.serial_numbers = serial_numbers
        instance.commit()

    def _validate_images(self, serial_numbers) -> None:
        """
        Validate the image staged to the switch(es)

        Callers:
        - handle_merged_state
        """
        method_name = inspect.stack()[0][3]

        msg = f"DEBUG: {self.class_name}.{method_name}: "
        msg += f"serial_numbers: {serial_numbers}"
        self.log_msg(msg)

        instance = ImageValidate(self.module)
        instance.serial_numbers = serial_numbers
        instance.commit()

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

        install_options = ImageInstallOptions(self.module)
        self.switch_details.refresh()

        verify_devices = copy.deepcopy(devices)

        for device in verify_devices:
            msg = f"DEBUG: {self.class_name}.{method_name}: "
            msg += f"device: {json.dumps(device, indent=4, sort_keys=True)}"
            self.log_msg(msg)

            self.switch_details.ip_address = device.get("ip_address")
            install_options.serial_number = self.switch_details.serial_number
            install_options.policy_name = device.get("policy")
            install_options.epld = device.get("upgrade", {}).get("epld", False)
            install_options.issu = device.get("upgrade", {}).get("nxos", False)
            install_options.refresh()

            msg = f"DEBUG: {self.class_name}.{method_name}: "
            msg += "install_options.response_data: "
            msg += (
                f"{json.dumps(install_options.response_data, indent=4, sort_keys=True)}"
            )
            self.log_msg(msg)

            if (
                install_options.status not in ["Success", "Skipped"]
                and device["upgrade"]["nxos"] is True
            ):
                msg = f"{self.class_name}.{method_name}: "
                msg += "NXOS upgrade is set to True for switch  "
                msg += f"{device['ip_address']}, but the image policy "
                msg += f"{install_options.policy_name} does not contain an "
                msg += "NX-OS image"
                self.module.fail_json(msg)

            msg = f"DEBUG: {self.class_name}.{method_name}: "
            msg += f"install_options.epld: {install_options.epld}"
            self.log_msg(msg)

            msg = f"DEBUG: {self.class_name}.{method_name}: "
            msg += "install_options.epld_modules: "
            msg += (
                f"{json.dumps(install_options.epld_modules, indent=4, sort_keys=True)}"
            )
            self.log_msg(msg)

            if install_options.epld_modules is None and install_options.epld is True:
                msg = f"{self.class_name}.{method_name}: "
                msg += "EPLD upgrade is set to True for switch "
                msg += f"{device['ip_address']}, but the image policy "
                msg += f"{install_options.policy_name} does not contain an "
                msg += "EPLD image."
                self.module.fail_json(msg)

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
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

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
                msg = f"DEBUG: {self.class_name}.{method_name}: "
                msg += f"(device: {module.get('deviceName')}), "
                msg += f"(IP: {module.get('ipAddress')}), "
                msg += f"(module#: {module.get('module')}), "
                msg += f"(module: {module.get('moduleType')}), "
                msg += f"new_version {new_version} > old_version {old_version}, "
                msg += "returning True"
                self.log_msg(msg)
                return True
        return False

    def _upgrade_images(self, devices) -> None:
        """
        Upgrade the switch(es) to the specified image

        Callers:
        - handle_merged_state
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        upgrade = ImageUpgrade(self.module)
        upgrade.devices = devices
        upgrade.commit()

    def handle_merged_state(self) -> None:
        """
        Update the switch policy if it has changed.
        Stage the image if requested.
        Validate the image if requested.
        Upgrade the image if requested.

        Caller: main()
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self._build_policy_attach_payload()
        self._send_policy_attach_payload()

        stage_devices: List[str] = []
        validate_devices: List[str] = []
        upgrade_devices: List[Dict[str, Any]] = []

        self.switch_details.refresh()

        for switch in self.need:
            msg = f"DEBUG: {self.class_name}.{method_name}: "
            msg += f"switch: {json.dumps(switch, indent=4, sort_keys=True)}"
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
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        detach_policy_devices: Dict[str, Any] = {}

        self.switch_details.refresh()
        self.image_policies.refresh()

        for switch in self.need:
            self.switch_details.ip_address = switch.get("ip_address")
            self.image_policies.policy_name = switch.get("policy")

            if self.image_policies.name not in detach_policy_devices:
                detach_policy_devices[self.image_policies.policy_name] = []
            detach_policy_devices[self.image_policies.policy_name].append(
                self.switch_details.serial_number
            )

        if len(detach_policy_devices) == 0:
            self.result = {"changed": False, "diff": [], "response": []}
            return

        instance = ImagePolicyAction(self.module)
        for key, value in detach_policy_devices.items():
            instance.policy_name = key
            instance.action = "detach"
            instance.serial_numbers = value
            instance.commit()

    def handle_query_state(self) -> None:
        """
        Return the ISSU state of the switch(es) listed in the playbook

        Caller: main()
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        instance = SwitchIssuDetailsByIpAddress(self.module)
        instance.refresh()

        query_devices: List[Dict[str, Any]] = []
        for switch in self.need:
            instance.ip_address = switch.get("ip_address")
            if instance.filtered_data is None:
                continue
            query_devices.append(instance.filtered_data)

        self.result["response"] = query_devices
        self.result["diff"] = []
        self.result["changed"] = False

    def _failure(self, resp) -> None:
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

    element_spec = {
        "config": {"required": True, "type": "dict"},
        "state": {"default": "merged", "choices": ["merged", "deleted", "query"]},
    }

    ansible_module = AnsibleModule(argument_spec=element_spec, supports_check_mode=True)
    task_module = ImageUpgradeTask(ansible_module)

    task_module.get_want()
    task_module.get_have()

    if ansible_module.params["state"] == "merged":
        task_module.get_need_merged()
    elif ansible_module.params["state"] == "deleted":
        task_module.get_need_deleted()
    elif ansible_module.params["state"] == "query":
        task_module.get_need_query()

    task_module.result["changed"] = False
    if len(task_module.need) == 0:
        ansible_module.exit_json(**task_module.result)

    if ansible_module.check_mode:
        ansible_module.exit_json(**task_module.result)

    if ansible_module.params["state"] in ["merged", "deleted"]:
        task_module.result["changed"] = True

    if ansible_module.params["state"] == "merged":
        task_module.handle_merged_state()
    elif ansible_module.params["state"] == "deleted":
        task_module.handle_deleted_state()
    elif ansible_module.params["state"] == "query":
        task_module.handle_query_state()

    ansible_module.exit_json(**task_module.result)


if __name__ == "__main__":
    main()
