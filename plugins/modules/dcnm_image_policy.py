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
__author__ = "Allen Robel"

DOCUMENTATION = """
---
module: dcnm_image_policy
short_description: Image policy management for Nexus Dashboard Fabric Controller
version_added: "3.5.0"
description:
    - Create, delete, modify image policies.
author: Allen Robel (@quantumonion)
options:
    state:
        description:
            - The state of the feature or object after module completion
        type: str
        choices:
            - deleted
            - merged
            - overridden
            - query
            - replaced
        default: merged

    config:
        description:
            - List of dictionaries containing image policy parameters
        type: list
        elements: dict
        default: []
        suboptions:
            name:
                description:
                    - The image policy name.
                type: str
                required: true
            agnostic:
                description:
                    - The agnostic flag.
                type: bool
                default: false
                required: false
            description:
                description:
                    - The image policy description.
                type: str
                default: ""
                required: false
            epld_image:
                description:
                    - The epld image name.
                type: str
                default: ""
                required: false
            packages:
                description:
                    - A dictionary containing two keys, install and uninstall.
                type: dict
                required: false
                suboptions:
                    install:
                        description:
                            - A list of packages to install.
                        type: list
                        elements: str
                        required: false
                    uninstall:
                        description:
                            - A list of packages to uninstall.
                        type: list
                        elements: str
                        required: false
            platform:
                description:
                    - The platform to which the image policy applies e.g. N9K.
                type: str
                required: true
            release:
                description:
                    - The release associated with the image policy.
                    - This is derived from the image name as follows.
                    - From image name nxos64-cs.10.2.5.M.bin
                    - we need to extract version (10.2.5), platform (nxos64-cs), and bits (64bit).
                    - The release string conforms to format (version)_(platform)_(bits)
                    - so the resulting release string will be 10.2.5_nxos64-cs_64bit
                type: str
                required: true
            type:
                description:
                    - The type of the image policy e.g. PLATFORM.
                type: str
                default: PLATFORM
                required: false
"""

EXAMPLES = """
# This module supports the following states:
#
# deleted:
#   Delete image policies from the controller.
#
#   If an image policy has references (i.e. it is attached to a device),
#   the module will fail.  Use dcnm_image_upgrade module, state deleted,
#    to detach the image policy from all devices before deleting it.
#
# merged:
#   Create (or update) one or more image policies.
#
#   If an image policy does not exist on the controller, create it.
#   If an image policy already exists on the controller, edit it.
#
# overridden:
#   Create/delete one or more image policies.
#
#   If an image policy already exists on the controller, delete it and update
#   it with the configuration in the playbook task.
#
#   Remove any image policies from the controller that are not in the
#   playbook task.
#
# query:
#
#   Return the configuration for one or more image policies.
#
# replaced:
#
#   Replace image policies on the controller with policies in the playbook task.
#
#   If an image policy exists on the controller, but not in the playbook task,
#   do not delete it or modify it.
#
# Delete two image policies from the controller.

    -   name: Delete Image policies
        cisco.dcnm.dcnm_image_policy:
            state: deleted
            config:
            -   name: KR5M
            -   name: NR3F
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

# Merge two image policies into the controller.

    -   name: Merge Image policies
        cisco.dcnm.dcnm_image_policy:
            state: merged
            config:
            -   name: KR5M
                agnostic: false
                description: KR5M
                epld_image: n9000-epld.10.2.5.M.img
                packages:
                   install:
                   - mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm
                   uninstall:
                   - mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000
                platform: N9K
                release: 10.2.5_nxos64-cs_64bit
                type: PLATFORM
            -   name: NR3F
                description: NR3F
                platform: N9K
                epld_image: n9000-epld.10.3.1.F.img
                release: 10.3.1_nxos64-cs_64bit
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

# Override all policies on the controller and replace them with
# the policies in the playbook task.  Any policies other than
# KR5M and NR3F are deleted from the controller.

    -   name: Override Image policies
        cisco.dcnm.dcnm_image_policy:
            state: overridden
            config:
            -   name: KR5M
                agnostic: false
                description: KR5M
                epld_image: n9000-epld.10.2.5.M.img
                platform: N9K
                release: 10.2.5_nxos64-cs_64bit
                type: PLATFORM
            -   name: NR3F
                description: NR3F
                platform: N9K
                epld_image: n9000-epld.10.2.5.M.img
                release: 10.3.1_nxos64-cs_64bit
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

# Query the controller for the policies in the playbook task.

    -   name: Query Image policies
        cisco.dcnm.dcnm_image_policy:
            state: query
            config:
            -   name: NR3F
            -   name: KR5M
        register: result
    -   name: print result
        ansible.builtin.debug:
            var: result

# Replace any policies on the controller that are in the playbook task with
# the configuration given in the playbook task.  Policies not listed in the
# playbook task are not modified and are not deleted.

    -   name: Replace Image policies
        cisco.dcnm.dcnm_image_policy:
            state: replaced
            config:
            -   name: KR5M
                agnostic: false
                description: KR5M
                epld_image: n9000-epld.10.2.5.M.img
                platform: N9K
                release: 10.2.5_nxos64-cs_64bit
                type: PLATFORM
            -   name: NR3F
                description: Replaced NR3F
                platform: N9K
                epld_image: n9000-epld.10.3.1.F.img
                release: 10.3.1_nxos64-cs_64bit
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
from ..module_utils.common.log_v2 import Log
from ..module_utils.common.merge_dicts_v2 import MergeDicts
from ..module_utils.common.params_merge_defaults_v2 import ParamsMergeDefaults
from ..module_utils.common.params_validate_v2 import ParamsValidate
from ..module_utils.common.properties import Properties
from ..module_utils.common.response_handler import ResponseHandler
from ..module_utils.common.rest_send_v2 import RestSend
from ..module_utils.common.results import Results
from ..module_utils.common.sender_dcnm import Sender
from ..module_utils.image_policy.create import ImagePolicyCreateBulk
from ..module_utils.image_policy.delete import ImagePolicyDelete
from ..module_utils.image_policy.image_policies import ImagePolicies
from ..module_utils.image_policy.params_spec import ParamsSpec
from ..module_utils.image_policy.payload import Config2Payload
from ..module_utils.image_policy.query import ImagePolicyQuery
from ..module_utils.image_policy.replace import ImagePolicyReplaceBulk
from ..module_utils.image_policy.update import ImagePolicyUpdateBulk


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


@Properties.add_rest_send
class Common:
    """
    Common methods for all states
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.params = params

        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "check_mode is required."
            raise ValueError(msg)

        self._valid_states = ["deleted", "merged", "overridden", "query", "replaced"]
        self._states_require_config = {"merged", "overridden", "replaced", "query"}

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params is missing state parameter."
            raise ValueError(msg)
        if self.state not in self._valid_states:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid state: {self.state}. "
            msg += f"Expected one of: {','.join(self._valid_states)}."
            raise ValueError(msg)

        self.config = self.params.get("config", None)
        if self.state in self._states_require_config:
            if self.config is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += "params is missing config parameter."
                raise ValueError(msg)
            if not isinstance(self.config, list):
                msg = f"{self.class_name}.{method_name}: "
                msg += "Expected list of dict for self.config. "
                msg += f"Got {type(self.config).__name__}"
                raise TypeError(msg)

        self.results = Results()
        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self._rest_send = None

        self.have = None
        self.validated = []
        self.want = []

        # policies to created
        self.need_create = []
        # policies to updated
        self.need_delete = []
        # policies to deleted
        self.need_update = []
        # policies to query
        self.need_query = []
        self.validated_configs = []

        msg = f"ENTERED Common().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def get_have(self) -> None:
        """
        Caller: main()

        self.have consists of the current image policies on the controller
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.have = ImagePolicies()
        self.have.results = self.results
        self.have.rest_send = self.rest_send  # pylint: disable=no-member
        self.have.refresh()

    def get_want(self) -> None:
        """
        Caller: main()

        1. Validate the playbook configs
        2. Convert the validated configs to payloads
        3. Update self.want with this list of payloads
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        # Generate the params_spec used to validate the configs
        params_spec = ParamsSpec()
        params_spec.params = self.params
        params_spec.commit()

        # If a parameter is missing from the config, and it has a default
        # value, add it to the config.
        merged_configs = []
        merge_defaults = ParamsMergeDefaults()
        merge_defaults.params_spec = params_spec.params_spec
        for config in self.config:
            merge_defaults.parameters = config
            merge_defaults.commit()
            merged_configs.append(merge_defaults.merged_parameters)

        # validate the merged configs
        self.validated_configs = []
        validator = ParamsValidate()
        validator.params_spec = params_spec.params_spec
        for config in merged_configs:
            validator.parameters = config
            validator.commit()
            self.validated_configs.append(copy.deepcopy(validator.parameters))

        # convert the validated configs to payloads to more easily compare them
        # to self.have (the current image policies on the controller).
        for config in self.validated_configs:
            payload = Config2Payload()
            payload.config = config
            payload.params = self.params
            payload.commit()
            self.want.append(payload.payload)


class Replaced(Common):
    """
    Handle replaced state
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

        self.replace = ImagePolicyReplaceBulk()

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        Replace all policies on the controller that are in want
        """
        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.get_want()
        self.get_have()

        self.replace.results = self.results
        self.replace.payloads = self.want
        self.replace.rest_send = self.rest_send
        self.replace.params = self.params
        self.replace.commit()


class Deleted(Common):
    """
    Handle deleted state
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

        self.delete = ImagePolicyDelete()

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        If config is present, delete all policies in self.want that exist on the controller
        If config is not present, delete all policies on the controller
        """
        self.results.state = self.state
        self.results.check_mode = self.check_mode
        self.delete.policy_names = self.get_policies_to_delete()
        self.delete.results = self.results
        self.delete.rest_send = self.rest_send
        self.delete.params = self.params
        self.delete.commit()

    def get_policies_to_delete(self) -> list[str]:
        """
        Return a list of policy names to delete

        -   In config is present, return list of image policy names
            in self.want.
        -   If config is not present, return ["delete_all_image_policies"],
            which ``ImagePolicyDelete()`` interprets as "delete all image
            policies on the controller".
        """
        if not self.config:
            return ["delete_all_image_policies"]
        self.get_want()
        policy_names_to_delete = []
        for want in self.want:
            policy_names_to_delete.append(want["policyName"])
        return policy_names_to_delete


class Query(Common):
    """
    Handle query state
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

        self.query = ImagePolicyQuery()
        self.image_policies = ImagePolicies()

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        1.  query the fabrics in self.want that exist on the controller
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.get_want()

        if len(self.want) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Nothing to query."
            return

        self.image_policies.results = Results()
        self.image_policies.rest_send = self.rest_send

        self.query.params = self.params
        self.query.results = self.results
        self.query.rest_send = self.rest_send
        self.query.image_policies = self.image_policies
        policy_names_to_query = []
        for want in self.want:
            policy_names_to_query.append(want["policyName"])
        self.query.policy_names = policy_names_to_query
        self.query.commit()


class Overridden(Common):
    """
    ### Summary
    Handle overridden state

    ### Raises
    -   ``ValueError`` if:
            -   ``Common().__init__()`` raises ``TypeError`` or ``ValueError``.
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

        self.delete = ImagePolicyDelete()
        self.merged = Merged(params)

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        ### Summary
        -   Delete all policies on the controller that are not in self.want
        -   Instantiate`` Merged()`` and call ``Merged().commit()``
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.get_want()
        self.get_have()

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.want: {json_pretty(self.want)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.have.all_policies: {json_pretty(self.have.all_policies)}"
        self.log.debug(msg)

        self._delete_policies_not_in_want()
        # pylint: disable=attribute-defined-outside-init
        self.merged.rest_send = self.rest_send
        # pylint: enable=attribute-defined-outside-init
        self.merged.results = self.results
        self.merged.commit()

    def _delete_policies_not_in_want(self) -> None:
        """
        ### Summary
        Delete all policies on the controller that are not in self.want
        """
        method_name = inspect.stack()[0][3]
        want_policy_names = set()
        for want in self.want:
            want_policy_names.add(want["policyName"])

        policy_names_to_delete = []
        for policy_name in self.have.all_policies:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"policy_name: {policy_name}"
            self.log.debug(msg)
            if policy_name not in want_policy_names:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Appending to policy_names_to_delete: {policy_name}"
                self.log.debug(msg)
                policy_names_to_delete.append(policy_name)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"policy_names_to_delete: {policy_names_to_delete}"
        self.log.debug(msg)

        self.results.state = self.state
        self.results.check_mode = self.check_mode
        self.delete.policy_names = policy_names_to_delete
        self.delete.results = self.results
        self.delete.rest_send = self.rest_send
        self.delete.params = self.params
        self.delete.commit()


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

        self.create = ImagePolicyCreateBulk()
        self.update = ImagePolicyUpdateBulk()

        # new policies to be created
        self.need_create: list = []
        # existing policies to be updated
        self.need_update: list = []

        msg = f"ENTERED {self.class_name}().{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def get_need(self):
        """
        ### Summary
        Build self.need for merged state

        ### Description
        -   Populate self.need_create with items from self.want that are
            not in self.have
        -   Populate self.need_update with updated policies.  Policies are
            updated as follows:
                -   If a policy is in both self.want amd self.have, and they
                    contain differences, merge self.want into self.have,
                    with self.want keys taking precedence and append the
                    merged policy to self.need_update.
                -   If a policy is in both self.want and self.have, and they
                    are identical, do not append the policy to self.need_update
                    (i.e. do nothing).
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        for want in self.want:
            self.have.policy_name = want.get("policyName")

            # Policy does not exist on the controller so needs to be created.
            if self.have.policy is None:
                self.need_create.append(copy.deepcopy(want))
                continue

            # The policy exists on the controller.  Merge want parameters with
            # the controller's parameters and add the merged parameters to the
            # need_update list if they differ from the want parameters.
            have = copy.deepcopy(self.have.policy)
            merged, needs_update = self._merge_policies(have, want)

            if needs_update is True:
                self.need_update.append(copy.deepcopy(merged))

    def commit(self) -> None:
        """
        Commit the merged state requests
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.results.state = self.state
        self.results.check_mode = self.check_mode

        self.get_want()
        self.get_have()
        self.get_need()
        self.send_need_create()
        self.send_need_update()

    def _prepare_for_merge(self, have: dict, want: dict):
        """
        ### Summary
        -   Remove fields in "have" that are not part of a request payload i.e.
            imageName and ref_count.
        -   The controller returns "N9K/N3K" for the platform, but it expects
            "N9K" in the payload.  We change "N9K/N3K" to "N9K" in have so that
            the compare works.
        -   Remove all fields that are not set in both "have" and "want"
        """
        # Remove keys that the controller adds which are not part
        # of a request payload.
        for key in ["imageName", "ref_count", "platformPolicies"]:
            have.pop(key, None)

        # Change "N9K/N3K" to "N9K" in "have" to match the request payload.
        if have.get("platform", None) == "N9K/N3K":
            have["platform"] = "N9K"

        return (have, want)

    def _merge_policies(self, have: dict, want: dict) -> dict:
        """
        ### Summary
        Merge the parameters in want with the parameters in have.
        """
        method_name = inspect.stack()[0][3]
        (have, want) = self._prepare_for_merge(have, want)

        # Merge the parameters in want with the parameters in have.
        # The parameters in want take precedence.
        try:
            merge = MergeDicts()
            merge.dict1 = have
            merge.dict2 = want
            merge.commit()
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during MergeDicts(). "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error
        merged = copy.deepcopy(merge.dict_merged)

        needs_update = False

        if have != merged:
            needs_update = True

        return (merged, needs_update)

    def send_need_create(self) -> None:
        """
        ### Summary
        Create the policies in self.need_create

        """
        self.create.results = self.results
        self.create.payloads = self.need_create
        self.create.rest_send = self.rest_send
        self.create.params = self.params
        self.create.commit()

    def send_need_update(self) -> None:
        """
        ### Summary
        Update the policies in self.need_update

        """
        self.update.results = self.results
        self.update.payloads = self.need_update
        self.update.rest_send = self.rest_send
        self.update.params = self.params
        self.update.commit()


def main():
    """
    main entry point for module execution
    """

    argument_spec = {
        "config": {
            "required": False,
            "type": "list",
            "elements": "dict",
            "default": [],
        },
        "state": {
            "default": "merged",
            "choices": ["deleted", "merged", "overridden", "query", "replaced"],
        },
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
        if params["state"] == "overridden":
            task = Overridden(params)
        if params["state"] == "query":
            task = Query(params)
        if params["state"] == "replaced":
            task = Replaced(params)
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
