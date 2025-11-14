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
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging

from ..common.api.v1.imagemanagement.rest.policymgnt.policymgnt import \
    EpPolicyEdit
from ..common.merge_dicts_v2 import MergeDicts
from ..common.properties import Properties
from ..common.results import Results
from .image_policies import ImagePolicies


@Properties.add_rest_send
@Properties.add_results
@Properties.add_params
class ImagePolicyReplaceBulk:
    """
    ### Summary
    Handle Ansible replaced state for image policies

    Given a list of payloads, bulk-replace the image policies therein.
    The payload format is given below.

    ```
    agnostic        bool(), optional. true or false
    epldImgName     str(), optional. name of an EPLD image to install.
    nxosVersion     str(), required. NX-OS version as version_type_arch
    packageName:    str(), optional, A comma-separated list of packages
    platform:       str(), optional, one of N9K, N6K, N5K, N3K
    policyDesc      str(), optional, description for the image policy
    policyName:     str(), required.  Name of the image policy.
    policyType      str(), required. PLATFORM or UMBRELLA
    rpmimages:      str(), optional. A comma-separated list of packages to uninstall
    ```

    ### Example usage (replacing two policies)):

    ```python
    policies = [
        {
            "agnostic": false,
            "epldImgName": "n9000-epld.10.3.2.F.img",
            "nxosVersion": "10.3.1_nxos64-cs_64bit",
            "packageName": "mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm",
            "platform": "N9K",
            "policyDescr": "10.3(3)F",
            "policyName": "FOO",
            "policyType": "PLATFORM",
            "rpmimages": "mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000"
        },
        {
            "policyDescr": "new policy description for BAR",
            "policyName": "BAR
        },
    ]

    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    instance = ImagePolicyReplaceBulk()
    instance.payloads = policies
    instance.rest_send = rest_send
    instance.params = rest_send.params
    instance.commit()
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.action = "replace"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED ImagePolicyReplaceBulk(): "
        msg += f"action: {self.action}, "
        self.log.debug(msg)

        self._image_policies = ImagePolicies()
        self._image_policies.results = Results()

        self.endpoint = EpPolicyEdit()
        self.path = self.endpoint.path
        self.verb = self.endpoint.verb

        self._payloads_to_commit = []

        self._mandatory_payload_keys = set()
        self._mandatory_payload_keys.add("nxosVersion")
        self._mandatory_payload_keys.add("policyName")
        self._mandatory_payload_keys.add("policyType")

        self._params = None
        self._payloads = None
        self._rest_send = None
        self._results = None

    def verify_payload(self, payload):
        """
        ### Summary
        Verify that the payload is a dict and contains all mandatory keys.

        ### Raises
        -   ``TypeError`` if payload is not a dict.
        -   ``ValueError`` if payload is missing mandatory keys.
        """
        method_name = inspect.stack()[0][3]
        if not isinstance(payload, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be a dict. "
            msg += f"Got type {type(payload).__name__}, "
            msg += f"value {payload}"
            raise TypeError(msg)

        missing_keys = []
        for key in self._mandatory_payload_keys:
            if key not in payload:
                missing_keys.append(key)
        if len(missing_keys) == 0:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += "payload is missing mandatory keys: "
        msg += f"{sorted(missing_keys)}"
        raise ValueError(msg)

    def _verify_image_policy_ref_count(self, instance, policy_names):
        """
        ### Summary
        Verify that all image policies in policy_names have a ref_count of 0
        (i.e. no devices are using the policy).

        ### Raises
        -   ``ValueError`` if any policy in policy_names has a ref_count
            greater than 0.

        ### Parameters
        -   ``instance`` : ImagePolicies() instance
        -   ``policy_names`` : list of policy names
        """
        method_name = inspect.stack()[0][3]
        _non_zero_ref_counts = {}
        for policy_name in policy_names:
            instance.policy_name = policy_name
            msg = f"instance.policy_name: {instance.policy_name}, "
            msg += f"instance.ref_count: {instance.ref_count}."
            self.log.debug(msg)
            # If the policy does not exist on the controller, the ref_count
            # will be None. We skip these too.
            if instance.ref_count in [0, None]:
                continue
            _non_zero_ref_counts[policy_name] = instance.ref_count
        if len(_non_zero_ref_counts) == 0:
            return
        msg = f"{self.class_name}.{method_name}: "
        msg += "One or more policies have devices attached. "
        msg += "Detach these policies from all devices first using "
        msg += "the dcnm_image_upgrade module, with state == deleted. "
        for policy_name, ref_count in _non_zero_ref_counts.items():
            msg += f"policy_name: {policy_name}, "
            msg += f"ref_count: {ref_count}. "
        raise ValueError(msg)

    def default_policy(self, policy_name):
        """
        ### Summary
        Return a default policy payload for policy name.

        ### Raises
        -   ``TypeError`` if policy_name is not a string.
        """
        method_name = inspect.stack()[0][3]
        if not isinstance(policy_name, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_name must be a string. "
            msg += f"Got type {type(policy_name).__name__} for "
            msg += f"value {policy_name}."
            self.log.debug(msg)
            raise TypeError(msg)

        policy = {
            "agnostic": False,
            "epldImgName": "",
            "nxosVersion": "",
            "packageName": "",
            "platform": "",
            "policyDescr": "",
            "policyName": policy_name,
            "policyType": "PLATFORM",
            "rpmimages": "",
        }
        return policy

    def build_payloads_to_commit(self):
        """
        ### Summary
        Build the payloads to commit to the controller.
        Populates the list self._payloads_to_commit

        ### Raises
        -   ``ValueError`` if:
                -   ``payloads`` is not set prior to calling commit.
                -   ref_count for any policy is not 0.
        """
        method_name = inspect.stack()[0][3]

        # pylint: disable=no-member
        self._image_policies.rest_send = self.rest_send
        # pylint: enable=no-member
        self._image_policies.refresh()

        msg = "self.payloads: "
        msg += f"{json.dumps(self.payloads, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # Populate a list of policies on the contoller that match our payloads
        controller_policies = []
        policy_names = []
        for payload in self.payloads:
            if payload.get("policyName", None) not in self._image_policies.all_policies:
                continue
            controller_policies.append(payload)
            policy_names.append(payload["policyName"])

        msg = "controller_policies: "
        msg += f"{json.dumps(controller_policies, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # raise ValueError if the ref_count for any policy is not 0 (i.e. the
        # policy is in use and cannot be replaced)
        try:
            self._verify_image_policy_ref_count(self._image_policies, policy_names)
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while verifying image policy ref counts. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        # If we made it this far, the ref_counts for all policies are 0
        # Merge the default image policy with the user's payload to create a
        # complete playload and add it to self._payloads_to_commit
        self._payloads_to_commit = []
        for payload in controller_policies:
            merge = MergeDicts()
            merge.dict1 = copy.deepcopy(self.default_policy(payload["policyName"]))
            merge.dict2 = payload
            msg = f"merge.dict1: {json.dumps(merge.dict1, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            msg = f"merge.dict2: {json.dumps(merge.dict2, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            merge.commit()
            self._payloads_to_commit.append(copy.deepcopy(merge.dict_merged))
        msg = "self._payloads_to_commit: "
        msg += f"{json.dumps(self._payloads_to_commit, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def send_payloads(self):
        """
        ### Summary
        Send the payloads in self._payloads_to_commit to the controller

        ### Raises
        -   ``ValueError`` if any payload is not sent successfully.
        """
        method_name = inspect.stack()[0][3]
        self.rest_send.check_mode = self.params.get(  # pylint: disable=no-member
            "check_mode"
        )

        for payload in self._payloads_to_commit:
            try:
                self.send_payload(payload)
            except ValueError as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Error while sending payloads. "
                msg += f"Error detail: {error}"
                raise ValueError(msg) from error

    # pylint: disable=no-member
    def send_payload(self, payload):
        """
        ### Summary
        Send one payload to the controller

        ### Raises
        -   ``ValueError`` if the payload is not sent successfully.

        ### Notes
        -   pylint: disable=no-member is needed because the rest_send, results,
            and params properties are dynamically created by the
            @Properties class decorators.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"verb: {self.verb}, path: {self.path}, "
        msg += f"payload: {json.dumps(payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # We don't want RestSend to retry on errors since the likelihood of a
        # timeout error when updating image policies is low, and there are
        # many cases of permanent errors for which we don't want to retry.
        try:
            self.rest_send.timeout = 1
            self.rest_send.path = self.path
            self.rest_send.verb = self.verb
            self.rest_send.payload = payload
            self.rest_send.commit()
        except (TypeError, ValueError) as error:
            self.results.diff_current = {}
            self.results.action = self.action
            self.results.check_mode = self.params.get("check_mode")
            self.results.state = self.params.get("state")
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error while sending payload. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        if self.rest_send.result_current["success"] is False:
            self.results.diff_current = {}
        else:
            self.results.diff_current = copy.deepcopy(payload)

        self.results.action = self.action
        self.results.check_mode = self.params.get("check_mode")
        self.results.state = self.params.get("state")
        self.results.response_current = copy.deepcopy(self.rest_send.response_current)
        self.results.result_current = copy.deepcopy(self.rest_send.result_current)
        self.results.register_task_result()

    def commit(self):
        """
        ### Summary
        Commit the payloads to the controller.
        ### Raises
        -   ``ValueError`` if payloads, results, or rest_send are not set prior
            to calling commit.
        """
        method_name = inspect.stack()[0][3]
        if self.payloads is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"payloads must be set prior to calling {method_name}."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"results must be set prior to calling {method_name}."
            raise ValueError(msg)
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"rest_send must be set prior to calling {method_name}."
            raise ValueError(msg)

        self.build_payloads_to_commit()
        self.send_payloads()

    @property
    def payloads(self):
        """
        ### Summary
        Return the policy payloads

        ### Raises
        -   ``TypeError`` if payloads is not a list.
        """
        return self._payloads

    @payloads.setter
    def payloads(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be a list of dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        for item in value:
            self.verify_payload(item)
        self._payloads = value
