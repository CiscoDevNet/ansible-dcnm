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
# TODO: needs_testing

from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging
from typing import Any, Dict

from ansible_collections.cisco.dcnm.plugins.module_utils.common.merge_dicts import \
    MergeDicts
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send

class ImagePolicyUpdateCommon(ImagePolicyCommon):
    """
    Common methods and properties for:
    - ImagePolicyUpdate
    - ImagePolicyUpdateBulk
    """
    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug(f"ENTERED ImagePolicyUpdateCommon()")

        self.endpoints = ApiEndpoints()

        self.path = self.endpoints.policy_edit.get("path")
        self.verb = self.endpoints.policy_edit.get("verb")

        self._mandatory_payload_keys = set()
        self._mandatory_payload_keys.add("nxosVersion")
        self._mandatory_payload_keys.add("policyName")
        self._mandatory_payload_keys.add("policyType")


    def _verify_payload(self, payload):
        """
        Verify that the payload is a dict and contains all mandatory keys
        """
        method_name = inspect.stack()[0][3]
        if not isinstance(payload, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be a dict. "
            msg += f"gpt type {type(payload).__name__}, "
            msg += f"value {payload}"
            self.ansible_module.fail_json(msg, **self.failed_result)

        missing_keys = []
        for key in self._mandatory_payload_keys:
            if key not in payload:
                missing_keys.append(key)
        if len(missing_keys) == 0:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += f"payload is missing mandatory keys: "
        msg += f"{sorted(missing_keys)}"
        self.ansible_module.fail_json(msg, **self.failed_result)


    def _build_payloads_to_commit(self):
        """
        Build a list of payloads to commit.  Skip any payloads that
        already exist on the controller.

        Expects self.payloads to be a list of dict, with each dict
        being a payload for the image policy edit API endpoint.

        Populates self._payloads_to_commit with a list of payloads
        to commit.
        """
        self.image_policies = ImagePolicies(self.ansible_module)
        self.image_policies.refresh()

        _payloads = []
        for payload in self.payloads:
            if payload.get("policyName", None) not in self.image_policies.all_policies:
                continue
            _payloads.append(payload)

        # build self._payloads_to_commit by merging _payloads with the policies
        # on the controller.  The parameters in _payloads take precedence.
        self._payloads_to_commit = []
        for payload in _payloads:
            merge = MergeDicts(self.ansible_module)
            merge.dict1 = self.image_policies.all_policies.get(payload["policyName"])
            merge.dict2 = payload
            merge.commit()
            self._payloads_to_commit.append(copy.deepcopy(merge.dict_merged))


    def _send_payloads(self):
        """
        Send the payloads to the controller and populate the following lists:

        - self.result_ok   : list of controller responses that succeeded
        - self.diff_ok     : list of payloads that succeeded
        - self.result_nok  : list of controller responses that failed
        - self.diff_nok    : list of payloads that failed
        """
        self.result_ok = []
        self.diff_ok = []
        self.result_nok = []
        self.diff_nok = []
        for payload in self._payloads_to_commit:
            response = dcnm_send(
                self.ansible_module, self.verb, self.path, data=json.dumps(payload)
            )
            result = self._handle_response(response, self.verb)

            if result["success"]:
                self.result_ok.append(response)
                self.diff_ok.append(payload)
            else:
                self.result_nok.append(response)
                self.diff_nok.append(payload)

    def _process_responses(self):
        method_name = inspect.stack()[0][3]

        if len(self.result_ok) == len(self._payloads_to_commit):
            self.changed = True
            for diff in self.diff_ok:
                self.diff = diff
            return

        self.changed = False
        # at least one request succeeded, so set changed to True
        if len(self.result_nok) != len(self._payloads_to_commit):
            self.changed = True

        result = {}
        result["changed"] = self.changed
        # When failing, provide the diff(s) for the request(s) that succeeded
        # Since these represent the change(s) that were made.
        result["diff"] = self.diff_ok
        result["failed"] = True
        msg = f"{self.class_name}.{method_name}: "
        msg += "Bad response(s) during policy create. "
        msg += f"response(s): {self.result_nok}"
        self.ansible_module.fail_json(msg, **result)

class ImagePolicyUpdateBulk(ImagePolicyUpdateCommon):
    """
    Given a list of payloads, bulk-update the image policies therein.
    The payload format is given below.

    agnostic        bool(), optional. true or false
    epldImgName     str(), optional. name of an EPLD image to install.
    nxosVersion     str(), required. NX-OS version as version_type_arch
    packageName:    str(), optional, A comma-separated list of packages
    platform:       str(), optional, one of N9K, N6K, N5K, N3K
    policyDesc      str(), optional, description for the image policy
    policyName:     str(), required.  Name of the image policy.
    policyType      str(), required. PLATFORM or UMBRELLA
    rpmimages:      str(), optional. A comma-separated list of packages to uninstall

    Example (updating two policies)):

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
    bulk_update = ImagePolicyUpdateBulk(ansible_module)
    bulk_update.payloads = policies
    bulk_update.commit()
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug(f"ENTERED ImagePolicyUpdateBulk()")

        self._build_properties()
        self.endpoints = ApiEndpoints()

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        # self.properties is already set in the parent class
        self.properties["payloads"] = None

    @property
    def payloads(self):
        """
        Return the image policy payloads

        Payloads must be a list of dict. Each dict is a
        payload for the image policy update API endpoint.
        """
        return self.properties["payloads"]

    @payloads.setter
    def payloads(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be a list of dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg)
        for item in value:
            self._verify_payload(item)
        self.properties["payloads"] = value

    def commit(self):
        """
        Update policies.  Skip any policies that do not exist
        on the controller.
        """
        method_name = inspect.stack()[0][3]
        if self.payloads is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            self.ansible_module.fail_json(msg)

        self._build_payloads_to_commit()
        if len(self._payloads_to_commit) == 0:
            return
        self._send_payloads()
        self._process_responses()


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

    policy = {
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
    update.payload = policy
    update.commit()
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ImagePolicyUpdate()")

        self._mandatory_keys = set()
        self._mandatory_keys.add("policyName")

        self._build_properties()
        self.endpoints = ApiEndpoints()

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        # properties is already initialized in the parent class
        self.properties["payload"] = None

    @property
    def payload(self):
        """
        This class expects a properly-defined image policy payload.
        See class docstring for the payload structure and example usage.
        """
        return self.properties["payload"]

    @payload.setter
    def payload(self, value):
        self._verify_payload(value)
        self.properties["payload"] = value

    def commit(self):
        """
        Update policy.  If policy does not exist on the controller, do nothing.
        """
        method_name = inspect.stack()[0][3]
        if self.payload is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.failed_result)

        # ImagePolicyUpdateCommon expects a list of payloads
        self.payloads = [self.payload]
        self._build_payloads_to_commit()

        if self._payloads_to_commit == []:
            return
        self._send_payloads()
        self._process_responses()
