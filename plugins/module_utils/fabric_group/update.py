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
Exposes one public class to update fabric-groups on the controller:

- FabricGroupUpdate
"""
from __future__ import absolute_import, division, print_function

from typing import Any, Union

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging

from ..common.api.onemanage.endpoints import EpOneManageFabricGroupUpdate
from ..common.conversion import ConversionUtils
from ..common.operation_type import OperationType
from .common import FabricGroupCommon
from .config_deploy import FabricGroupConfigDeploy
from .config_save import FabricGroupConfigSave
from ..common.rest_send_v2 import RestSend
from ..common.results_v2 import Results
from .fabric_group_types import FabricGroupTypes
from .fabric_groups import FabricGroups


class FabricGroupUpdate(FabricGroupCommon):
    """
    Update fabrics in bulk.

    Usage:
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.update import \
        FabricGroupUpdate
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import \
        Results

    payloads = [
        { "FABRIC_NAME": "fabric1", "BGP_AS": 65000, "DEPLOY": True },
        { "FABRIC_NAME": "fabric2", "BGP_AS": 65001, "DEPLOY": False }
    ]
    results = Results()
    instance = FabricGroupUpdate(ansible_module)
    instance.payloads = payloads
    instance.results = results
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
        msg = "Fabric update(s) failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)
    """

    def __init__(self) -> None:
        super().__init__()
        self.class_name: str = self.__class__.__name__
        self.action: str = "fabric_group_update"
        self.operation_type: OperationType = OperationType.UPDATE

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        self._config_deploy: FabricGroupConfigDeploy = FabricGroupConfigDeploy()
        self._config_save: FabricGroupConfigSave = FabricGroupConfigSave()
        self.conversion: ConversionUtils = ConversionUtils()
        self._fabric_group_update_required: set = set()
        self._key_translations: dict = {}
        self._key_translations["DEPLOY"] = ""
        self.endpoint: EpOneManageFabricGroupUpdate = EpOneManageFabricGroupUpdate()
        self.fabric_group_types: FabricGroupTypes = FabricGroupTypes()
        self.fabric_group_type: str = "MCFG"
        self.fabric_groups: FabricGroups = FabricGroups()
        self._payloads: list[dict] = []

        # Properties to be set by caller
        self._rest_send: RestSend = RestSend({})
        self._results: Results = Results()

        msg = f"ENTERED {self.class_name}"
        self.log.debug(msg)

    def _string_to_bool(self, value: str) -> Any:
        """
        # Summary

        Convert string "true" or "false" to boolean True or False.
        If value is not a string, or is a string that's not "true"/"false",
        return it unchanged.

        ## Raises

        None
        """
        if not isinstance(value, str):
            return value
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        return value

    def _merge_nv_pairs(self, controller_nv_pairs: dict, payload: dict) -> dict:
        """
        # Summary

        Merge user and controller nvPairs.  User nvPairs overwrite controller nvPairs.

        -  Translate payload keys to equivilent keys on the controller if necessary.
        -  Skip FABRIC_TYPE key since we add the correct value later.

        ## Raises

        -   ``ValueError`` if ANYCAST_GW_MAC translation fails.
        """
        method_name: str = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        for payload_key, payload_value in payload.items():
            # Translate payload keys to equivilent keys on the controller
            # if necessary.  This handles cases where the controller key
            # is misspelled and we want our users to use the correct
            # spelling.
            if payload_key in self._key_translations:
                key = self._key_translations[payload_key]
            else:
                key = payload_key
            # Skip the FABRIC_TYPE key since the user payload FABRIC_TYPE value
            # will be e.g. "MCFG", whereas the fabric configuration will
            # be "MFD".  We later add the correct FABRIC_TYPE value in
            # self._add_mandatory_keys_to_payload().
            if key == "FABRIC_TYPE":
                continue
            if key == "ANYCAST_GW_MAC":
                try:
                    payload_value = self.conversion.translate_mac_address(payload_value)
                except ValueError as error:
                    raise ValueError(error) from error
            if key in controller_nv_pairs:
                if isinstance(controller_nv_pairs.get(key), bool):
                    payload_value = self._string_to_bool(payload_value)
                controller_nv_pairs[key] = payload_value
        return controller_nv_pairs

    def _log_changed_keys(self, controller_values: dict, updated_values: dict) -> None:
        """
        # Summary

        Log the keys that have changed between controller_values and updated_values.

        ## Raises

        None
        """
        method_name: str = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        all_keys = set(controller_values) | set(updated_values)
        changed = {k for k in all_keys if controller_values.get(k) != updated_values.get(k)}
        msg = f"{self.class_name}.{method_name}: "
        msg += "Changed keys: "
        msg += f"{','.join(list(changed))}"
        self.log.debug(msg)

    def _add_mandatory_keys_to_payload(self, fabric_name: str) -> None:
        """
        # Summary

        Add mandatory key/values to the fabric update payload.

        - fabricName
        - fabricTechnology
        - fabricType
        - templateName
        - nvPairs.FABRIC_NAME
        - nvPairs.FABRIC_TYPE

        ## Raises

        None

        ## Notes

        1. For now, we assume all fabric groups are VXLAN MFD fabrics
        """
        method_name: str = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        self._fabric_changes_payload[fabric_name]["fabricName"] = fabric_name
        self._fabric_changes_payload[fabric_name]["fabricTechnology"] = "VXLANFabric"
        self._fabric_changes_payload[fabric_name]["fabricType"] = "MFD"
        self._fabric_changes_payload[fabric_name]["templateName"] = "MSD_Fabric"
        if "nvPairs" not in self._fabric_changes_payload[fabric_name]:
            self._fabric_changes_payload[fabric_name]["nvPairs"] = {}
        self._fabric_changes_payload[fabric_name]["nvPairs"]["FABRIC_NAME"] = fabric_name
        self._fabric_changes_payload[fabric_name]["nvPairs"]["FABRIC_TYPE"] = "MFD"

    def _merge_payload(self, payload: dict) -> None:
        """
        # Summary

        Merge user payload into existing fabric configuration on the controller.
        If the resulting merged payload differs from the existing fabric configuration
        on the controller, prepare the merged payload for update.

        Add True to self._fabric_group_update_required set() if the updated payload
        needs to be sent to the controller.

        The controller needs to be updated if a parameter in the merged user/controller
        payload has a different value than the corresponding parameter in fabric
        configuration on the controller.

        ## Raises

        None

        """
        method_name: str = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        fabric_name: Union[str, None] = payload.get("FABRIC_NAME", None)
        if not fabric_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "FABRIC_NAME missing from payload.  Skipping payload."
            self.log.error(msg)
            return

        controller_config: dict = self.fabric_groups.data.get(fabric_name, {})
        if not controller_config:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Fabric {fabric_name} not found on controller.  Skipping payload."
            self.log.debug(msg)
            return

        self._fabric_changes_payload[fabric_name] = {}

        controller_nv_pairs = copy.deepcopy(controller_config.get("nvPairs", {}))
        controller_nv_pairs_original = copy.deepcopy(controller_nv_pairs)
        controller_nv_pairs_updated = self._merge_nv_pairs(controller_nv_pairs, payload)
        if controller_nv_pairs_updated != controller_nv_pairs_original:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Controller needs to be updated for fabric {fabric_name}. "
            self.log.debug(msg)
            self._log_changed_keys(controller_nv_pairs_original, controller_nv_pairs_updated)
            self._fabric_changes_payload[fabric_name]["nvPairs"] = controller_nv_pairs_updated
            self._fabric_group_update_required.add(True)

        if True not in self._fabric_group_update_required:
            self._fabric_changes_payload[fabric_name] = payload
            msg = f"{self.class_name}.{method_name}: "
            msg += f"No changes detected for fabric {fabric_name}. "
            msg += "Skipping controller update."
            self.log.debug(msg)
            return

        self._add_mandatory_keys_to_payload(fabric_name)

    def _build_payloads(self) -> None:
        """
        # Summary

        Build the list of payloads to commit for merged (update) state.

        -   Populate self._payloads_to_commit. A list of dict of payloads to
            commit for merged state.
        -   Skip payloads for fabrics that do not exist on the controller.
        -   raise ``ValueError`` if ``_merge_payload``
            fails.
        -   Expects self.payloads to be a list of dict, with each dict
            being a payload for the fabric create API endpoint.

        ## Raises

        -   ``ValueError`` if ``_merge_payload`` fails.
        """
        method_name: str = inspect.stack()[0][3]
        self.fabric_groups.rest_send = self.rest_send
        self.fabric_groups.results = self.results
        self.fabric_groups.refresh()
        self._payloads_to_commit = []

        for payload in self.payloads:
            fabric_name = payload.get("FABRIC_NAME", "")
            if not fabric_name:
                msg = f"{self.class_name}.{method_name}: "
                msg += "FABRIC_NAME missing from payload. Skipping payload."
                self.log.debug(msg)
                continue

            if fabric_name not in self.fabric_groups.fabric_group_names:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Fabric {fabric_name} not found on controller. "
                msg += "Skipping payload."
                self.log.debug(msg)
                continue

            self._fabric_group_update_required = set()
            try:
                self._merge_payload(payload)
            except ValueError as error:
                raise ValueError(error) from error

            if True not in self._fabric_group_update_required:
                continue
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Adding fabric group {fabric_name} to payloads_to_commit. "
            self.log.debug(msg)
            self._payloads_to_commit.append(copy.deepcopy(self._fabric_changes_payload[fabric_name]))

    def _send_payloads(self) -> None:
        """
        -   If ``check_mode`` is ``False``, send the payloads
            to the controller.
        -   If ``check_mode`` is ``True``, do not send the payloads
            to the controller.
        -   In both cases, register results.
        -   Re-raise ``ValueError`` if any of the following fail:
            -   ``FabricCommon()._fixup_payloads_to_commit()``
            -   ``FabricUpdateCommon()._send_payload()``
            -   ``FabricUpdateCommon()._config_save()``
            -   ``FabricUpdateCommon()._config_deploy()``
        """
        method_name: str = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)

        try:
            self._fixup_payloads_to_commit()
        except ValueError as error:
            raise ValueError(error) from error

        for payload in self._payloads_to_commit:
            commit_payload: dict = copy.deepcopy(payload)
            try:
                self._send_payload(commit_payload)
            except ValueError as error:
                raise ValueError(error) from error

        # Skip config-save if prior actions encountered errors.
        # if True in self.results.failed:
        #     return

        # TODO: Ask Mike/Matt if we need to do config-save and config-deploy
        # for fabric group updates.
        # for payload in self._payloads_to_commit:
        #     try:
        #         self._config_save.payload = payload
        #     except ValueError as error:
        #         raise ValueError(error) from error

        # # Skip config-deploy if prior actions encountered errors.
        # if True in self.results.failed:
        #     return

        # for payload in self._payloads_to_commit:
        #     try:
        #         self._config_deploy.payload = payload
        #     except (ControllerResponseError, ValueError) as error:
        #         raise ValueError(error) from error

    def _send_payload(self, payload: dict) -> None:
        """
        - Send one fabric update payload
        - raise ``ValueError`` if the endpoint assignment fails
        """
        method_name: str = inspect.stack()[0][3]

        fabric_name: Union[str, None] = payload.get("nvPairs", {}).get("FABRIC_NAME", None)
        if not fabric_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "FABRIC_NAME missing from payload nvPairs."
            self.log.error(msg)
            raise ValueError(msg)

        try:
            self.endpoint.fabric_name = fabric_name
        except ValueError as error:
            raise ValueError(error) from error

        self.path = self.endpoint.path
        self.verb = self.endpoint.verb

        msg = f"{self.class_name}.{method_name}: "
        msg += f"verb: {self.verb}, path: {self.path}, "
        msg += f"payload: {json.dumps(payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # We don't want RestSend to retry on errors since the likelihood of a
        # timeout error when updating a fabric is low, and there are many cases
        # of permanent errors for which we don't want to retry.
        self.rest_send.timeout = 1
        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.payload = payload
        self.rest_send.commit()

        if self.rest_send.result_current["success"] is False:
            self.results.diff_current = {}
        else:
            self.results.diff_current = copy.deepcopy(payload)

        self.send_payload_result[fabric_name] = self.rest_send.result_current["success"]
        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state
        self.results.response_current = copy.deepcopy(self.rest_send.response_current)
        self.results.result_current = copy.deepcopy(self.rest_send.result_current)
        self.results.register_task_result()

    @property
    def payloads(self) -> list[dict[str, Any]]:
        """
        Payloads must be a ``list`` of ``dict`` of payloads for the
        ``fabric_update`` endpoint.

        - getter: Return the fabric update payloads
        - setter: Set the fabric update payloads
        - setter: raise ``ValueError`` if ``payloads`` is not a ``list`` of ``dict``
        - setter: raise ``ValueError`` if any payload is missing mandatory keys
        """
        return self._payloads

    @payloads.setter
    def payloads(self, value: list[dict[str, Any]]):
        method_name = inspect.stack()[0][3]
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

    def commit(self) -> None:
        """
        - Update fabrics and register results.
        - Return if there are no fabrics to update for merged state.
        - raise ``ValueError`` if ``fabric_group_details`` is not set
        - raise ``ValueError`` if ``fabric_summary`` is not set
        - raise ``ValueError`` if ``payloads`` is not set
        - raise ``ValueError`` if ``rest_send`` is not set
        - raise ``ValueError`` if ``_build_payloads`` fails
        - raise ``ValueError`` if ``_send_payloads`` fails
        """
        method_name: str = inspect.stack()[0][3]
        msg: str = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)
        if self.fabric_group_details is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_details must be set prior to calling commit."
            raise ValueError(msg)

        if self.fabric_summary is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_summary must be set prior to calling commit."
            raise ValueError(msg)

        if not self.payloads:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            raise ValueError(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit."
            raise ValueError(msg)

        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state

        try:
            self._build_payloads()
        except ValueError as error:
            raise ValueError(error) from error

        if len(self._payloads_to_commit) == 0:
            self.results.diff_current = {}
            self.results.result_current = {"success": True, "changed": False}
            msg = "No fabrics to update for merged state."
            self.results.response_current = {"RETURN_CODE": 200, "MESSAGE": msg}
            self.results.register_task_result()
            return

        try:
            self._send_payloads()
        except ValueError as error:
            self.results.diff_current = {}
            self.results.result_current = {"success": False, "changed": False}
            return_code = self.rest_send.response_current.get("RETURN_CODE", None)
            msg = f"ValueError self.results.response: {self.results.response}"
            self.log.debug(msg)
            self.results.response_current = {
                "RETURN_CODE": f"{return_code}",
                "MESSAGE": f"{error}",
            }
            self.results.register_task_result()
            raise ValueError(error) from error

    @property
    def rest_send(self) -> RestSend:
        """
        An instance of the RestSend class.
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        if not value.params:
            msg = f"{self.class_name}.rest_send must be set to an "
            msg += "instance of RestSend with params set."
            raise ValueError(msg)
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        An instance of the Results class.
        """
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        self._results = value
        self._results.action = self.action
        self._results.changed = False
        self._results.operation_type = self.operation_type
