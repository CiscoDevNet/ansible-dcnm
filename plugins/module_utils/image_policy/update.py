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
class ImagePolicyUpdateCommon:
    """
    Common methods and properties for:
    - ImagePolicyUpdate
    - ImagePolicyUpdateBulk
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.action = "update"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

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
        self._payload = None
        self._payloads = None
        self._rest_send = None
        self._results = None

        msg = "ENTERED ImagePolicyUpdateCommon(): "
        msg += f"action: {self.action}, "
        self.log.debug(msg)

    def verify_payload(self, payload):
        """
        Verify that the payload is a dict and contains all mandatory keys
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

    def build_payloads_to_commit(self):
        """
        ### Summary
        Build a list of payloads to commit.  Skip any payloads that do not
        exist on the controller.

        Expects self.payloads to be a list of dict, with each dict
        being a payload for the image policy edit API endpoint.

        Populates self._payloads_to_commit with a list of payloads
        to commit.
        """
        method_name = inspect.stack()[0][3]
        if self.payloads is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            raise ValueError(msg)

        self._image_policies.rest_send = self.rest_send  # pylint: disable=no-member
        self._image_policies.refresh()

        _payloads = []
        _policy_names = []
        for payload in self.payloads:
            if payload.get("policyName", None) not in self._image_policies.all_policies:
                continue
            _payloads.append(payload)
            _policy_names.append(payload["policyName"])

        self._verify_image_policy_ref_count(self._image_policies, _policy_names)

        # build self._payloads_to_commit by merging each _payload with the
        # corresponding policy payload on the controller.  The parameters
        # in _payloads take precedence.
        self._payloads_to_commit = []
        for payload in _payloads:
            try:
                merge = MergeDicts()
                merge.dict1 = self._image_policies.all_policies.get(
                    payload["policyName"]
                )
                merge.dict2 = payload
                merge.commit()
                updated_payload = copy.deepcopy(merge.dict_merged)
            except (TypeError, ValueError) as error:
                msg = f"{self.class_name}.build_payloads_to_commit: "
                msg += "Error merging payload and policy. "
                msg += f"Error detail: {error}."
                raise ValueError(msg) from error
            # ref_count, imageName, and platformPolicies are returned
            # by the controller, but are not valid parameters for the
            # edit-policy endpoint.
            updated_payload.pop("ref_count", None)
            updated_payload.pop("imageName", None)
            updated_payload.pop("platformPolicies", None)
            self._payloads_to_commit.append(copy.deepcopy(updated_payload))
        msg = f"{self.class_name}.{method_name}: "
        msg += "self._payloads_to_commit: "
        msg += f"{json.dumps(self._payloads_to_commit, indent=4, sort_keys=True)}"
        self.log.debug(msg)

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
        msg += "the dcnm_image_upgrade module with state == deleted."
        for policy_name, ref_count in _non_zero_ref_counts.items():
            msg += f"policy_name: {policy_name}, "
            msg += f"ref_count: {ref_count}. "
        raise ValueError(msg)

    def send_payloads(self):
        """
        If check_mode is False, send the payloads to the controller
        If check_mode is True, do not send the payloads to the controller

        In both cases, update results
        """
        self.rest_send.check_mode = self.params.get(  # pylint: disable=no-member
            "check_mode"
        )

        for payload in self._payloads_to_commit:
            self.send_payload(payload)

    # pylint: disable=no-member
    def send_payload(self, payload):
        """
        ### Summary
        Send one image policy update payload

        ### Raises

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
        # timeout error when updating an image policy is low, and there are
        # cases of permanent errors for which we don't want to retry.
        self.rest_send.save_settings()
        self.rest_send.timeout = 1
        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.payload = payload
        self.rest_send.commit()
        self.rest_send.restore_settings()

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

    @property
    def payloads(self):
        """
        Return the image policy payloads

        Payloads must be a list of dict. Each dict is a
        payload for the image policy update API endpoint.
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


class ImagePolicyUpdateBulk(ImagePolicyUpdateCommon):
    """
    ### Summary
    Given a list of payloads, bulk-update the image policies therein.
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

    ### Usage example (updating two policies)

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
            "policyName": "BAR,
        },
    ]
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    bulk_update = ImagePolicyUpdateBulk()
    bulk_update.payloads = policies
    bulk_update.results = Results()
    bulk_update.rest_send = rest_send
    bulk_update.params = rest_send.params
    bulk_update.commit()
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED ImagePolicyUpdateBulk(): "
        self.log.debug(msg)

    # pylint: disable=no-member
    def commit(self):
        """
        ### Summary
        Update policies.  Skip any policies that do not exist
        on the controller.

        ### Raises
        -   ``ValueError`` if:
                -   payloads is None
                -   results is None
                -   rest_send is None

        ### Notes
        -   pylint: disable=no-member is needed becase the rest_send, results,
            and params properties are dynamically created by the
            @Properties class decorators.
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

        if len(self._payloads_to_commit) == 0:
            return
        self.send_payloads()


class ImagePolicyUpdate(ImagePolicyUpdateCommon):
    """
    Given a properly-constructed image policy payload (python dict),
    send an image policy update request to the controller.  The payload
    format is given below.

    agnostic        bool(), optional. true or false
    epldImgName     str(), optional. name of an EPLD image to install.
    nxosVersion     str(), required. NX-OS version as version_type_arch
    packageName:    str(), optional, A comma-separated list of packages
    platform:       str(), optional, one of N9K, N6K, N5K, N3K
    policyDesc      str(), optional, description for the image policy
    policyName:     str(), required.  Name of the image policy.
    policyType      str(), required. PLATFORM or UMBRELLA
    rpmimages:      str(), optional. A comma-separated list of packages to uninstall

    Example (update one policy):

    image_policy_payload = {
        "agnostic": false,
        "epldImgName": "n9000-epld.10.3.2.F.img",
        "nxosVersion": "10.3.1_nxos64-cs_64bit",
        "packageName": "mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm",
        "platform": "N9K",
        "policyDescr": "image policy of 10.3(3)F",
        "policyName": "FOO",
        "policyType": "PLATFORM",
        "rpmimages": "mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000"
    }
    update = ImagePolicyUpdate(ansible_module)
    update.payload = image_policy_payload
    update.commit()
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED ImagePolicyUpdate(): "
        self.log.debug(msg)

        self._mandatory_keys = set()
        self._mandatory_keys.add("policyName")

    @property
    def payload(self):
        """
        This class expects a properly-defined image policy payload.
        See class docstring for the payload structure and example usage.
        """
        return self._payload

    @payload.setter
    def payload(self, value):
        self.verify_payload(value)
        self._payload = value
        # ImagePolicyUpdateCommon expects a list of payloads
        self._payloads = [value]

    def commit(self):
        """
        Update policy.
        If policy does not exist on the controller, do nothing.
        """
        method_name = inspect.stack()[0][3]
        if self.payload is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"payload must be set prior to calling {method_name}."
            raise ValueError(msg)
        if self.results is None:  # pylint: disable=no-member
            msg = f"{self.class_name}.{method_name}: "
            msg += f"results must be set prior to calling {method_name}."
            raise ValueError(msg)
        if self.rest_send is None:  # pylint: disable=no-member
            msg = f"{self.class_name}.{method_name}: "
            msg += f"rest_send must be set prior to calling {method_name}."
            raise ValueError(msg)

        try:
            self.build_payloads_to_commit()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error building payloads to commit. "
            msg += f"Error detail: {error}."
            raise ValueError(msg) from error

        if len(self._payloads_to_commit) == 0:
            return
        self.send_payloads()
