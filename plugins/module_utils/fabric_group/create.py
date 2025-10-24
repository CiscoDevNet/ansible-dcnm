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
# pylint: disable=too-many-instance-attributes
"""
Exposes one public class to create fabric-groups on the controller:
- FabricGroupCreate
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging
from typing import Any, Union

from ..common.api.onemanage.endpoints import EpOneManageFabricCreate
from .common import FabricGroupCommon
from .fabric_group_types import FabricGroupTypes
from .fabric_groups import FabricGroups


class FabricGroupCreate(FabricGroupCommon):
    """
    Create fabric-groups in bulk.  Skip any fabric-groups that already exist.

    Usage:

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.create import FabricGroupCreate
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.fabric_group_details import FabricGroupDetails
    payloads = [
        { "FABRIC_NAME": "fabric1", "BGP_AS": 65000 },
        { "FABRIC_NAME": "fabric2", "BGP_AS": 65001 }
    ]
    results = Results()
    fabric_group_details = FabricGroupDetails()
    fabric_group_details.rest_send = rest_send_instance
    fabric_group_details.results = results
    instance = FabricGroupCreate()
    instance.rest_send = rest_send_instance
    instance.results = results
    instance.payloads = payloads
    instance.fabric_group_details = fabric_group_details
    instance.commit()
    results.build_final_result()

    # diff contains a dictionary of payloads that succeeded and/or failed
    diff = results.diff
    # result contains the result(s) of the fabric create request
    result = results.result
    # response contains the response(s) from the controller
    response = results.response

    # results.final_result contains all of the above info, and can be passed
    # to the exit_json and fail_json methods of AnsibleModule:

    if True in results.failed:
        msg = "Fabric create failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.action = "fabric_group_create"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.endpoint = EpOneManageFabricCreate()
        self.fabric_groups = FabricGroups()
        self.fabric_group_types = FabricGroupTypes()

        self.path: str = self.endpoint.path
        self.verb: str = self.endpoint.verb

        self._payloads: list[dict] = []
        self._payloads_to_commit: list[dict[str, Any]] = []

        msg = f"ENTERED {self.class_name}()"
        self.log.debug(msg)

    def _build_payload_top_level_keys(self, fabric_name: str) -> dict[str, str]:
        """
        # Summary

        Add top-level keys to the payload.  Remove seed_member from the
        passed `payload` and add it as a top-level key seedMember in the
        returned dict.

        - fabricName
        - fabricTechnology
        - fabricType
        - templateName
        - seedMember

        ## Assumptions

        - fabricType is always MFD
        - fabricTechnology is always VXLANFabric
        - templateName is always MSD_Fabric

        ## Raises

        -   `ValueError` if
            - payload is missing ``FABRIC_NAME``.
            - seed_member update fails.

        """
        commit_payload = {}
        commit_payload["fabricName"] = fabric_name
        commit_payload["fabricTechnology"] = "VXLANFabric"
        commit_payload["fabricType"] = "MFD"
        commit_payload["templateName"] = "MSD_Fabric"
        return commit_payload

    def _build_payload_seed_member(self, commit_payload: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        """
        Build the commit_payload seedMember contents from payload.

        - Update commit_payload with seedMember key set to the updated seed_member contents.
        - Pop seed_member from payload.

        ## Raises

        -   `ValueError` if seed_member update fails.

        """
        try:
            seed_member = self._update_seed_member(payload.get("seed_member", {}))
        except ValueError as error:
            raise ValueError(error) from error
        payload.pop("seed_member", None)
        commit_payload["seedMember"] = copy.deepcopy(seed_member)
        return commit_payload

    def _build_payload_nv_pairs(self, commit_payload: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        """
        # Summary

        Add nvPairs to commit_payload.

        - Add mandatory nvPairs with default values if not present in payload.
          - Else, use values from payload.
        - Copy all other keys from payload to nvPairs.

        ## Assumptions

        - nvPairs.FABRIC_TYPE is always MFD.

        ## Raises

        None
        """
        commit_payload["nvPairs"] = copy.deepcopy(payload)
        commit_payload["nvPairs"]["FABRIC_TYPE"] = "MFD"
        commit_payload["nvPairs"]["default_network"] = payload.get("default_network", "Default_Network_Universal")
        commit_payload["nvPairs"]["default_vrf"] = payload.get("default_vrf", "Default_VRF_Universal")
        commit_payload["nvPairs"]["network_extension_template"] = payload.get("network_extension_template", "Default_Network_Extension_Universal")
        commit_payload["nvPairs"]["scheduledTime"] = payload.get("scheduledTime", "")
        commit_payload["nvPairs"]["vrf_extension_template"] = payload.get("vrf_extension_template", "Default_VRF_Extension_Universal")
        commit_payload["nvPairs"]["CLOUDSEC_ALGORITHM"] = payload.get("CLOUDSEC_ALGORITHM", "")
        commit_payload["nvPairs"]["CLOUDSEC_ENFORCEMENT"] = payload.get("CLOUDSEC_ENFORCEMENT", "")
        commit_payload["nvPairs"]["CLOUDSEC_KEY_STRING"] = payload.get("CLOUDSEC_KEY_STRING", "")
        commit_payload["nvPairs"]["CLOUDSEC_REPORT_TIMER"] = payload.get("CLOUDSEC_REPORT_TIMER", "")
        commit_payload["nvPairs"]["LOOPBACK100_IPV6_RANGE"] = payload.get("LOOPBACK100_IPV6_RANGE", "")
        commit_payload["nvPairs"]["MS_IFC_BGP_AUTH_KEY_TYPE"] = payload.get("MS_IFC_BGP_AUTH_KEY_TYPE", "")
        commit_payload["nvPairs"]["MS_IFC_BGP_PASSWORD"] = payload.get("MS_IFC_BGP_PASSWORD", "")
        commit_payload["nvPairs"]["V6_DCI_SUBNET_RANGE"] = payload.get("V6_DCI_SUBNET_RANGE", "")
        commit_payload["nvPairs"]["V6_DCI_SUBNET_TARGET_MASK"] = payload.get("V6_DCI_SUBNET_TARGET_MASK", "")
        return commit_payload

    def _build_payloads_to_commit(self) -> None:
        """
        # Summary

        Build a list of payloads to commit.  Skip any payloads that
        already exist on the controller.

        Expects self.payloads to be a list of dict, with each dict
        being a payload for the fabric group create API endpoint.

        Populates self._payloads_to_commit with a list of payloads
        to commit.

        ## Raises

        -   `ValueError` if
            - `_build_payload_top_level` raises `ValueError`.
            - `FABRIC_NAME` is missing from any payload.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.fabric_groups.rest_send = self.rest_send
        self.fabric_groups.results = self.results
        self.fabric_groups.refresh()

        self._payloads_to_commit = []
        payload: dict[str, Any] = {}
        for payload in self.payloads:
            fabric_name: Union[str, None] = payload.get("FABRIC_NAME", None)
            if fabric_name is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += "FABRIC_NAME is missing from fabric_group config, but is mandatory."
                raise ValueError(msg)
            # Skip any fabric-groups that already exist
            if fabric_name in self.fabric_groups.fabric_group_names:
                continue
            # Order is important here
            commit_payload = self._build_payload_top_level_keys(fabric_name)
            commit_payload = self._build_payload_seed_member(commit_payload, payload)
            commit_payload = self._build_payload_nv_pairs(commit_payload, payload)
            self._payloads_to_commit.append(commit_payload)

    def _send_payloads(self):
        """
        # Summary

        -   If ``check_mode`` is ``False``, send the payloads
            to the controller.
        -   If ``check_mode`` is ``True``, do not send the payloads
            to the controller.
        -   In both cases, register results.
        -   raise ``ValueError`` if the fabric_group_create endpoint assignment fails
        """
        for payload in self._payloads_to_commit:

            # We don't want RestSend to retry on errors since the likelihood of a
            # timeout error when creating a fabric-group is low, and there are many cases
            # of permanent errors for which we don't want to retry.
            # pylint: disable=no-member
            self.rest_send.timeout = 1

            self.rest_send.path = self.path
            self.rest_send.verb = self.verb
            self.rest_send.payload = payload
            self.rest_send.commit()

            if self.rest_send.result_current["success"] is False:
                self.results.diff_current = {}
            else:
                self.results.diff_current = copy.deepcopy(payload)
            self.results.action = self.action
            self.results.state = self.rest_send.state
            self.results.check_mode = self.rest_send.check_mode
            self.results.response_current = copy.deepcopy(self.rest_send.response_current)
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()

            msg = f"self.results.diff: {json.dumps(self.results.diff, indent=4, sort_keys=True)}"
            self.log.debug(msg)

    def commit(self):
        """
        # Summary

        Commit the fabric_group create payloads to the controller to
        create fabric_groups.

        - Skip any fabric_groups that already exist on the controller.
        - raise ``ValueError`` if ``payloads`` is not set.
        - raise ``ValueError`` if payload fixup fails.
        - raise ``ValueError`` if sending the payloads fails.
        """
        method_name = inspect.stack()[0][3]

        # pylint: disable=no-member
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit. "
            raise ValueError(msg)

        if not self.payloads:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            raise ValueError(msg)

        self._build_payloads_to_commit()

        msg = "self._payloads_to_commit: "
        msg += f"{json.dumps(self._payloads_to_commit, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if len(self._payloads_to_commit) == 0:
            return
        try:
            self._fixup_payloads_to_commit()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self._send_payloads()
        except ValueError as error:
            raise ValueError(error) from error

    @property
    def payloads(self):
        """
        Payloads must be a ``list`` of ``dict`` of payloads for the
        ``fabric_create`` endpoint.

        - getter: Return the fabric create payloads
        - setter: Set the fabric create payloads
        - setter: raise ``ValueError`` if ``payloads`` is not a ``list`` of ``dict``
        - setter: raise ``ValueError`` if any payload is missing mandatory keys
        """
        return self._payloads

    @payloads.setter
    def payloads(self, value: list[dict[str, Any]]):
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"value: {value}"
        self.log.debug(msg)

        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be a list of dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise ValueError(msg)
        for item in value:
            if not isinstance(item, dict):
                msg = f"{self.class_name}.{method_name}: "
                msg += "Each payload must be a dict. "
                msg += f"got {type(item).__name__} for "
                msg += f"item {item}"
                raise ValueError(msg)
            try:
                self._verify_payload(item)
            except ValueError as error:
                raise ValueError(error) from error
        self._payloads = value
