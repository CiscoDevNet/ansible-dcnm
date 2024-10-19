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
from ..module_utils.common.image_policies import ImagePolicies
from ..module_utils.common.log_v2 import Log
from ..module_utils.common.merge_dicts_v2 import MergeDicts
from ..module_utils.common.params_merge_defaults_v2 import ParamsMergeDefaults
from ..module_utils.common.params_validate_v2 import ParamsValidate
from ..module_utils.common.properties import Properties
from ..module_utils.common.response_handler import ResponseHandler
from ..module_utils.common.rest_send_v2 import RestSend
from ..module_utils.common.results import Results
from ..module_utils.common.sender_dcnm import Sender
from ..module_utils.common.switch_details import SwitchDetails
from ..module_utils.image_upgrade.image_policy_attach import ImagePolicyAttach
from ..module_utils.image_upgrade.image_policy_detach import ImagePolicyDetach
from ..module_utils.image_upgrade.image_stage import ImageStage
from ..module_utils.image_upgrade.image_upgrade import ImageUpgrade
from ..module_utils.image_upgrade.image_validate import ImageValidate
from ..module_utils.image_upgrade.install_options import ImageInstallOptions
from ..module_utils.image_upgrade.params_spec import ParamsSpec
from ..module_utils.image_upgrade.switch_issu_details import SwitchIssuDetailsByIpAddress


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


@Properties.add_rest_send
class Common:
    """
    ### Summary
    Common methods for Ansible support of Nexus image upgrade.

    ### Raises
    -   ``TypeError`` if
            -   ``params`` is not a dict.
    -   ``ValueError`` if
            -   params.check_mode is missing.
            -   params.state is missing.
            -   params.state is not one of
                    -   ``deleted``
                    -   ``merged``
                    -   ``query``
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.valid_states = ["deleted", "merged", "query"]
        self.check_mode = None
        self.config = None
        self.state = None
        self.params = params
        self.validate_params()

        self.results = Results()
        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self._rest_send = None
        self.have = None
        self.idempotent_want = None
        # populated in self._merge_global_and_switch_configs()
        self.switch_configs = []

        self.want = []
        self.need = []

        self.switch_details = SwitchDetails()
        self.image_policies = ImagePolicies()
        self.install_options = ImageInstallOptions()
        self.image_policy_attach = ImagePolicyAttach()
        self.params_spec = ParamsSpec()

        self.image_policies.results = self.results
        self.install_options.results = self.results
        self.image_policy_attach.results = self.results

        msg = f"ENTERED Common().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def validate_params(self):
        """
        ### Summary
        Validate ``params`` passed to __init__().

        ### Raises
        -   ``TypeError`` if
                -   ``params`` is not a dict.
        -   ``ValueError`` if
                -   params.check_mode is missing.
                -   params.state is missing.
                -   params.state is not one of
                        -   ``deleted``
                        -   ``merged``
                        -   ``query``
        """
        method_name = inspect.stack()[0][3]

        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "check_mode is required."
            raise ValueError(msg)
        self.config = self.params.get("config", None)
        if not isinstance(self.config, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "expected dict type for self.config. "
            msg += f"got {type(self.config).__name__}"
            raise TypeError(msg)
        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params is missing state parameter."
            raise ValueError(msg)
        if self.state not in self.valid_states:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid state: {self.state}. "
            msg += f"Expected one of: {','.join(self.valid_states)}."
            raise ValueError(msg)

    def get_have(self) -> None:
        """
        Caller: main()

        Determine current switch ISSU state on the controller
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)
        self.have = SwitchIssuDetailsByIpAddress()
        self.have.rest_send = self.rest_send  # pylint: disable=no-member
        # Set to Results() instead of self.results so as not to clutter
        # the playbook results.
        self.have.results = Results()
        self.have.refresh()

    def get_want(self) -> None:
        """
        ### Summary
        Update self.want for all switches defined in the playbook.
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += "Calling _merge_global_and_switch_configs with "
        msg += f"self.config: {json.dumps(self.config, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self._merge_global_and_switch_configs(self.config)
        self._merge_defaults_to_switch_configs()
        self._validate_switch_configs()

        self.want = self.switch_configs

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.want: {json.dumps(self.want, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _build_idempotent_want(self, want) -> None:
        """
        ### Summary
        Build an itempotent want item based on the have item contents.

        The have item is obtained from an instance of SwitchIssuDetails
        created in get_have().

        ### want structure
        ```json
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
        ```

        The returned idempotent_want structure is identical to the
        above structure, except that the policy_changed key is added,
        and values are modified based on results from the have item,
        and the information returned by ImageInstallOptions.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"want: {json.dumps(want, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # start with a copy of the want item with policy_changed = True
        want["policy_changed"] = True
        self.idempotent_want = copy.deepcopy(want)

        self.have.filter = want["ip_address"]

        # The switch does not have an image policy attached.
        # idempotent_want == want with policy_changed = True
        if self.have.serial_number is None:
            return

        # The switch has an image policy attached which is
        # different from the want policy.
        # idempotent_want == want with policy_changed = True
        if want["policy"] != self.have.policy:
            return

        # Give an indication to the caller that the image policy has not
        # changed.  This can be used later to determine if we need to do
        # anything in the case where the image is already staged and/or
        # upgraded.
        self.idempotent_want["policy_changed"] = False

        # if the image is already staged, don't stage it again
        if self.have.image_staged == "Success":
            self.idempotent_want["stage"] = False
        # if the image is already validated, don't validate it again
        if self.have.validated == "Success":
            self.idempotent_want["validate"] = False

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.have.reason: {self.have.reason}, "
        msg += f"self.have.policy: {self.have.policy}, "
        msg += f"idempotent_want[policy]: {self.idempotent_want['policy']}, "
        msg += f"self.have.upgrade: {self.have.upgrade}"
        self.log.debug(msg)

        # if the image is already upgraded, don't upgrade it again.
        # if the upgrade was previously unsuccessful, we need to try
        # to upgrade again.
        if self.have.reason == "Upgrade" and self.have.upgrade == "Success":
            msg = "Set upgrade nxos to False"
            self.log.debug(msg)
            self.idempotent_want["upgrade"]["nxos"] = False

        # Get relevant install options from the controller
        # based on the options in our idempotent_want item
        self.install_options.policy_name = self.idempotent_want["policy"]
        self.install_options.serial_number = self.have.serial_number
        self.install_options.epld = want.get("upgrade", {}).get("epld", False)
        self.install_options.issu = self.idempotent_want.get("upgrade", {}).get(
            "nxos", False
        )
        self.install_options.package_install = (
            want.get("options", {}).get("package", {}).get("install", False)
        )
        self.install_options.refresh()

        msg = f"{self.class_name}.{method_name}: "
        msg += "ImageInstallOptions.response: "
        msg += f"{json.dumps(self.install_options.response_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += "self.idempotent_want PRE EPLD CHECK: "
        msg += f"{json.dumps(self.idempotent_want, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}"
        msg += f"self.install_options.epld_modules: {self.install_options.epld_modules}"
        self.log.debug(msg)

        # if InstallOptions indicates that EPLD is already upgraded,
        # don't upgrade it again.
        if self.needs_epld_upgrade(self.install_options.epld_modules) is False:
            self.idempotent_want["upgrade"]["epld"] = False

        msg = "self.idempotent_want POST EPLD CHECK: "
        msg += f"{json.dumps(self.idempotent_want, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def needs_epld_upgrade(self, epld_modules) -> bool:
        """
        ### Summary
        Determine if the switch needs an EPLD upgrade.

        For all modules, compare EPLD oldVersion and newVersion.

        ### Raises
        None

        ### Returns
        -   ``True`` if newVersion > oldVersion for any module.
        -   ``False`` otherwise.
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"epld_modules: {epld_modules}"
        self.log.debug(msg)

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

    def _merge_global_and_switch_configs(self, config) -> None:
        """
        ### Summary
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

        ### Raises
        -   ``ValueError`` if:
                -   Playbook is missing list of switches.
                -   ``MergedDicts()`` raises an error.
        """
        method_name = inspect.stack()[0][3]

        if not config.get("switches"):
            msg = f"{self.class_name}.{method_name}: "
            msg += "playbook is missing list of switches"
            raise ValueError(msg)

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

            try:
                merge = MergeDicts()
                merge.dict1 = global_config
                merge.dict2 = switch
                merge.commit()
            except (TypeError, ValueError) as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Error during MergeDicts(). "
                msg += f"Error detail: {error}"
                raise ValueError(msg) from error
            switch_config = merge.dict_merged

            msg = f"switch POST_MERGE: {json.dumps(switch_config, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            merged_configs.append(switch_config)
        self.switch_configs = copy.copy(merged_configs)

    def _merge_defaults_to_switch_configs(self) -> None:
        """
        For any items in config which are not set, apply the default
        value from params_spec (if a default value exists).
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}."
        self.log.debug(msg)

        self.params_spec.params = self.params
        self.params_spec.commit()

        configs_to_merge = copy.copy(self.switch_configs)
        merged_configs = []
        merge_defaults = ParamsMergeDefaults()
        merge_defaults.params_spec = self.params_spec.params_spec
        for switch_config in configs_to_merge:
            merge_defaults.parameters = switch_config
            merge_defaults.commit()
            merged_configs.append(merge_defaults.merged_parameters)
        self.switch_configs = copy.copy(merged_configs)

    def _validate_switch_configs(self) -> None:
        """
        ### Summary
        Verify parameters for each switch.

        ### Raises
        -   ``ValueError`` if:
                -   Any parameter is not valid.
                -   Mandatory parameters are missing.
                -   params is not a dict.
                -   params is missing ``state`` key.
                -   params ``state`` is not one of:
                        -   ``deleted``
                        -   ``merged``
                        -   ``query``
        """
        method_name = inspect.stack()[0][3]

        try:
            self.params_spec.params = self.params
            self.params_spec.commit()
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during ParamsSpec(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        validator = ParamsValidate()
        try:
            validator.params_spec = self.params_spec.params_spec
            for switch in self.switch_configs:
                validator.parameters = switch
                validator.commit()
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during ParamsValidate(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error


class Merged(Common):
    """
    ### Summary
    Handle merged state

    ### Raises
    -   ``ValueError`` if:
        -   ``params`` is missing ``config`` key.
        -   ``commit()`` is issued before setting mandatory properties
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]
        try:
            super().__init__(params)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during super().__init__(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        msg = f"params: {json_pretty(self.params)}"
        self.log.debug(msg)
        if not params.get("config"):
            msg = f"playbook config is required for {self.state}"
            raise ValueError(msg)

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def validate_commit_parameters(self) -> None:
        """
        ### Summary
        Verify mandatory parameters are set before calling commit.

        ### Raises
        -   ``ValueError`` if:
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit()."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set before calling commit()."
            raise ValueError(msg)

    def commit(self) -> None:
        """
        ### Summary
        -   Update the switch policy if it has changed.
        -   Stage the image if requested.
        -   Validate the image if requested.
        -   Upgrade the image if requested.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.validate_commit_parameters()

        self.install_options.rest_send = self.rest_send
        self.image_policies.rest_send = self.rest_send
        self.image_policy_attach.rest_send = self.rest_send
        self.switch_details.rest_send = self.rest_send
        # We don't want switch_details results to be saved in self.results
        self.switch_details.results = Results()

        self.get_have()
        self.get_want()
        if len(self.want) == 0:
            return
        self.get_need()
        self.attach_image_policy()

        stage_devices: list[str] = []
        validate_devices: list[str] = []
        upgrade_devices: list[dict] = []

        self.switch_details.refresh()

        for switch in self.need:
            msg = f"{self.class_name}.{method_name}: "
            msg = f"switch: {json.dumps(switch, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            device = {}
            self.have.filter = switch.get("ip_address")
            device["serial_number"] = self.have.serial_number
            device["policy_name"] = switch.get("policy")
            device["ip_address"] = self.have.ip_address

            if switch.get("stage") is not False:
                stage_devices.append(device["serial_number"])
            if switch.get("validate") is not False:
                validate_devices.append(device["serial_number"])
            if (
                switch.get("upgrade").get("nxos") is not False
                or switch.get("upgrade").get("epld") is not False
            ):
                upgrade_devices.append(switch)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"stage_devices: {stage_devices}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"validate_devices: {validate_devices}"
        self.log.debug(msg)

        self._stage_images(stage_devices)
        self._validate_images(validate_devices)

        self._verify_install_options(upgrade_devices)
        self._upgrade_images(upgrade_devices)

    def get_need(self) -> None:
        """
        ### Summary
        For merged state, populate self.need list() with items from
        our want list that are not in our have list.  These items will
        be sent to the controller.
        """
        method_name = inspect.stack()[0][3]
        need: list[dict] = []

        msg = f"{self.class_name}.{method_name}: "
        msg += "self.want: "
        msg += f"{json.dumps(self.want, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        for want in self.want:
            self.have.filter = want["ip_address"]

            msg = f"{self.class_name}.{method_name}: "
            msg += f"self.have.serial_number: {self.have.serial_number}"
            self.log.debug(msg)

            if self.have.serial_number is not None:
                self._build_idempotent_want(want)

                msg = f"{self.class_name}.{method_name}: "
                msg += "self.idempotent_want: "
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
                need.append(copy.deepcopy(self.idempotent_want))
        self.need = copy.copy(need)

    def _stage_images(self, serial_numbers) -> None:
        """
        Initiate image staging to the switch(es) associated
        with serial_numbers

        Callers:
        - handle_merged_state
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"serial_numbers: {serial_numbers}"
        self.log.debug(msg)

        stage = ImageStage()
        stage.rest_send = self.rest_send
        stage.results = self.results
        stage.serial_numbers = serial_numbers
        stage.commit()

    def _validate_images(self, serial_numbers) -> None:
        """
        Validate the image staged to the switch(es)

        Callers:
        - handle_merged_state
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"serial_numbers: {serial_numbers}"
        self.log.debug(msg)

        validate = ImageValidate()
        validate.serial_numbers = serial_numbers
        validate.rest_send = self.rest_send
        validate.results = self.results
        validate.commit()

    def _upgrade_images(self, devices) -> None:
        """
        Upgrade the switch(es) to the specified image

        Callers:
        - handle_merged_state
        """
        upgrade = ImageUpgrade()
        upgrade.rest_send = self.rest_send
        upgrade.results = self.results
        upgrade.devices = devices
        upgrade.commit()

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

        msg = f"{self.class_name}.{method_name}: "
        msg += f"len(devices): {len(devices)}, "
        msg += f"self.results: {self.results}"
        self.log.debug(msg)

        if len(devices) == 0:
            return

        self.switch_details.refresh()

        verify_devices = copy.deepcopy(devices)

        for device in verify_devices:
            msg = f"device: {json.dumps(device, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            self.switch_details.ip_address = device.get("ip_address")
            self.install_options.serial_number = self.switch_details.serial_number
            self.install_options.policy_name = device.get("policy")
            self.install_options.epld = device.get("upgrade", {}).get("epld", False)
            self.install_options.issu = device.get("upgrade", {}).get("nxos", False)
            self.install_options.refresh()

            msg = "install_options.response_data: "
            msg += f"{json.dumps(self.install_options.response_data, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            if (
                self.install_options.status not in ["Success", "Skipped"]
                and device["upgrade"]["nxos"] is True
            ):
                msg = f"{self.class_name}.{method_name}: "
                msg += "NXOS upgrade is set to True for switch  "
                msg += f"{device['ip_address']}, but the image policy "
                msg += f"{self.install_options.policy_name} does not contain an "
                msg += "NX-OS image"
                raise ValueError(msg)

            msg = f"install_options.epld: {self.install_options.epld}"
            self.log.debug(msg)

            msg = "install_options.epld_modules: "
            msg += f"{json.dumps(self.install_options.epld_modules, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            if (
                self.install_options.epld_modules is None
                and self.install_options.epld is True
            ):
                msg = f"{self.class_name}.{method_name}: "
                msg += "EPLD upgrade is set to True for switch "
                msg += f"{device['ip_address']}, but the image policy "
                msg += f"{self.install_options.policy_name} does not contain an "
                msg += "EPLD image."
                raise ValueError(msg)

    def attach_image_policy(self) -> None:
        """
        ### Summary
        Attach image policies to switches.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}."
        self.log.debug(msg)

        serial_numbers_to_update: dict = {}
        self.switch_details.refresh()
        self.image_policies.refresh()

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.need: {json.dumps(self.need, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        for switch in self.need:
            self.switch_details.filter = switch.get("ip_address")
            self.image_policies.policy_name = switch.get("policy")
            # ImagePolicyAttach wants a policy name and a list of serial_number.
            # Build dictionary, serial_numbers_to_update, keyed on policy name,
            # whose value is the list of serial numbers to attach.
            if self.image_policies.name not in serial_numbers_to_update:
                serial_numbers_to_update[self.image_policies.policy_name] = []

            serial_numbers_to_update[self.image_policies.policy_name].append(
                self.switch_details.serial_number
            )

        if len(serial_numbers_to_update) == 0:
            msg = "No policies to attach."
            self.log.debug(msg)
            return

        for key, value in serial_numbers_to_update.items():
            self.image_policy_attach.policy_name = key
            self.image_policy_attach.serial_numbers = value
            self.image_policy_attach.commit()


class Deleted(Common):
    """
    ### Summary
    Handle deleted state.

    ### Raises
    -   ``ValueError`` if:
        -   ``params`` is missing ``config`` key.
        -   ``commit()`` is issued before setting mandatory properties
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]
        try:
            super().__init__(params)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during super().__init__(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        self.image_policy_detach = ImagePolicyDetach()
        self.switch_issu_details = SwitchIssuDetailsByIpAddress()

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def get_need(self) -> None:
        """
        ### Summary
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

    def validate_commit_parameters(self) -> None:
        """
        ### Summary
        Verify mandatory parameters are set before calling commit.

        ### Raises
        -   ``ValueError`` if:
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit()."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set before calling commit()."
            raise ValueError(msg)

    def commit(self) -> None:
        """
        ### Summary
        Detach image policies from switches.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}."
        self.log.debug(msg)

        self.validate_commit_parameters()

        self.get_have()
        self.get_want()
        if len(self.want) == 0:
            return
        self.get_need()

        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.image_policy_detach.rest_send = self.rest_send
        self.switch_issu_details.rest_send = self.rest_send

        self.image_policy_detach.results = self.results
        # We don't want switch_issu_details results
        # to clutter the results returned to the playbook.
        self.switch_issu_details.results = Results()

        self.detach_image_policy()

    def detach_image_policy(self) -> None:
        """
        ### Summary
        Detach image policies from switches.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}."
        self.log.debug(msg)

        self.switch_issu_details.refresh()

        serial_numbers_to_detach: list = []
        for switch in self.need:
            self.switch_issu_details.filter = switch.get("ip_address")
            if self.switch_issu_details.policy is None:
                continue
            serial_numbers_to_detach.append(self.switch_issu_details.serial_number)

        if len(serial_numbers_to_detach) == 0:
            msg = "No policies to detach."
            self.log.debug(msg)
            return

        self.image_policy_detach.serial_numbers = serial_numbers_to_detach
        self.image_policy_detach.commit()


class Query(Common):
    """
    ### Summary
    Handle query state.

    ### Raises
    -   ``ValueError`` if:
        -   ``params`` is missing ``config`` key.
        -   ``commit()`` is issued before setting mandatory properties
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]
        try:
            super().__init__(params)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during super().__init__(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        self.issu_detail = SwitchIssuDetailsByIpAddress()

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def validate_commit_parameters(self) -> None:
        """
        ### Summary
        Verify mandatory parameters are set before calling commit.

        ### Raises
        -   ``ValueError`` if:
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit()."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set before calling commit()."
            raise ValueError(msg)

    def get_need(self) -> None:
        """
        ### Summary
        For query state, populate self.need list() with all items from
        our want list.  These items will be sent to the controller.

        ``policy`` name is ignored for query state.
        """
        need = []
        for want in self.want:
            need.append(want)
        self.need = copy.copy(need)

    def commit(self) -> None:
        """
        Return the ISSU state of the switch(es) listed in the playbook

        Caller: main()
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}."
        self.log.debug(msg)

        self.validate_commit_parameters()
        self.get_want()

        self.issu_detail.rest_send = self.rest_send
        self.issu_detail.results = self.results
        self.issu_detail.refresh()
        msg = f"{self.class_name}.{method_name}: "
        msg += "self.results.metadata: "
        msg += f"{json.dumps(self.results.metadata, indent=4, sort_keys=True)}"
        self.log.debug(msg)


def main():
    """main entry point for module execution"""

    argument_spec = {
        "config": {"required": True, "type": "dict"},
        "state": {"default": "merged", "choices": ["merged", "deleted", "query"]},
    }

    ansible_module = AnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True
    )

    params = copy.deepcopy(ansible_module.params)
    params["check_mode"] = ansible_module.check_mode

    # Logging setup
    try:
        log = Log()
        log.commit()
    except ValueError as error:
        ansible_module.fail_json(str(error))

    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    # pylint: disable=attribute-defined-outside-init
    try:
        task = None
        if params["state"] == "deleted":
            task = Deleted(params)
        if params["state"] == "merged":
            task = Merged(params)
        if params["state"] == "query":
            task = Query(params)
        if task is None:
            ansible_module.fail_json(f"Invalid state: {params['state']}")
        task.rest_send = rest_send
        task.commit()
    except ValueError as error:
        ansible_module.fail_json(f"{error}", **task.results.failed_result)

    task.results.build_final_result()

    if True in task.results.failed:  # pylint: disable=unsupported-membership-test
        msg = "Module failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)


if __name__ == "__main__":
    main()
