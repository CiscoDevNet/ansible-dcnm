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
"""
Update fabrics in bulk.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging
from typing import Any, Literal

from ..common.api.v1.lan_fabric.rest.control.fabrics.fabrics import EpFabricUpdate
from ..common.exceptions import ControllerResponseError
from ..common.operation_type import OperationType
from ..common.rest_send_v2 import RestSend
from ..common.results_v2 import Results
from .common_v2 import FabricCommon
from .fabric_details_v3 import FabricDetailsByName
from .fabric_summary_v2 import FabricSummary
from .fabric_types import FabricTypes


class FabricUpdateCommon(FabricCommon):
    """
    # Summary

    Common methods and properties for:

    - FabricUpdate
    - FabricUpdateBulk
    """

    def __init__(self) -> None:
        super().__init__()
        self.class_name: str = self.__class__.__name__
        self.action: str = "fabric_update"

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        self._ep_fabric_update: EpFabricUpdate = EpFabricUpdate()
        self._fabric_details_by_name: FabricDetailsByName = FabricDetailsByName()
        self._fabric_summary: FabricSummary = FabricSummary()
        self.fabric_types: FabricTypes = FabricTypes()

        msg = "ENTERED FabricUpdateCommon()"
        self.log.debug(msg)

    def _fabric_needs_update_for_merged_state(self, payload: dict[str, Any]) -> None:
        """
        -   Add True to self._fabric_update_required set() if the fabric needs
            to be updated for merged state.
        -   Populate self._fabric_changes_payload[fabric_name],
            a modified payload with key/values that differ from the fabric
            configuration on the controller.  This payload will be used to
            update the fabric.
        -   raise ``ValueError`` if any payload parameter would raise an
            error on the controller.

        The fabric needs to be updated if any of the following are true:
        -   A parameter in the payload has a different value than the
            corresponding parameter in fabric configuration on the controller.

        NOTES:
        -   We've already verified that the fabric exists on the
            controller in ``_build_payloads_for_merged_state()``.
        """
        method_name: str = inspect.stack()[0][3]

        fabric_name: str = payload.get("FABRIC_NAME", "")

        self._fabric_changes_payload[fabric_name] = {}
        nv_pairs: dict[str, Any] = self._fabric_details_by_name.all_data[fabric_name].get("nvPairs", {})

        key: str = ""
        payload_value: Any
        payload_key: str
        for payload_key, payload_value in payload.items():
            # Translate payload keys to equivilent keys on the controller
            # if necessary.  This handles cases where the controller key
            # is misspelled and we want our users to use the correct
            # spelling.
            if payload_key in self._key_translations:
                key = self._key_translations[payload_key]
            else:
                key = payload_key

            # Skip the FABRIC_TYPE key since the payload FABRIC_TYPE value
            # will be e.g. "VXLAN_EVPN", whereas the fabric configuration will
            # be something along the lines of "Switch_Fabric"
            if key == "FABRIC_TYPE":
                continue

            if not key:
                continue

            # If a key is in the payload that is not in the fabric
            # configuration on the controller:
            # - Update Results()
            # - raise ValueError
            if nv_pairs.get(key) is None:
                self._results.diff_current = {}
                self._results.result_current = {"success": False, "changed": False}
                self._results.add_failed(True)
                self._results.add_changed(False)
                self._results.failed_result["msg"] = (
                    f"Key {key} not found in fabric configuration for "
                    f"fabric {fabric_name}"
                )
                self._results.register_task_result()
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Invalid key: {key} found in payload for "
                msg += f"fabric {fabric_name}"
                self.log.debug(msg)
                raise ValueError(msg)
            msg = f"{self.class_name}.{method_name}: "
            msg += f"key: {key}, payload_value: {payload_value}, "
            msg += f"fabric_value: {nv_pairs.get(key)}"
            self.log.debug(msg)
            value = self._prepare_parameter_value_for_comparison(payload_value)

            if key == "ANYCAST_GW_MAC":
                try:
                    value = self.translate_anycast_gw_mac(fabric_name, value)
                except ValueError as error:
                    raise ValueError(error) from error

            if value != nv_pairs.get(key):
                msg = f"{self.class_name}.{method_name}: "
                msg += f"key {key}: "
                msg += f"payload_value [{value}] != "
                msg += f"fabric_value: [{nv_pairs.get(key)}]: "
                msg += "Fabric needs update."
                self.log.debug(msg)
                self._fabric_changes_payload[fabric_name][key] = value
                self._fabric_update_required.add(True)

        if len(self._fabric_changes_payload[fabric_name]) == 0:
            self._fabric_changes_payload[fabric_name] = payload
            return

        # Copy mandatory key/values DEPLOY, FABRIC_NAME, and FABRIC_TYPE
        # from the old payload to the new payload.
        deploy = payload.get("DEPLOY", None)
        fabric_type = payload.get("FABRIC_TYPE", None)
        self._fabric_changes_payload[fabric_name]["DEPLOY"] = deploy
        self._fabric_changes_payload[fabric_name]["FABRIC_NAME"] = fabric_name
        self._fabric_changes_payload[fabric_name]["FABRIC_TYPE"] = fabric_type

        msg = f"{self.class_name}.{method_name}: "
        msg += f"fabric_name: {fabric_name}, "
        msg += f"fabric_update_required: {self._fabric_update_required}, "
        msg += "fabric_changes_payload: "
        msg += f"{json.dumps(self._fabric_changes_payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _build_payloads_for_merged_state(self):
        """
        -   Populate self._payloads_to_commit. A list of dict of payloads to
            commit for merged state.
        -   Skip payloads for fabrics that do not exist on the controller.
        -   raise ``ValueError`` if ``_fabric_needs_update_for_merged_state``
            fails.
        -   Expects self.payloads to be a list of dict, with each dict
            being a payload for the fabric create API endpoint.

        NOTES:
        -   self._fabric_needs_update_for_merged_state() may remove payload
            key/values that would not change the controller configuration.
        """
        self._fabric_details_by_name.rest_send = self._rest_send
        self._fabric_details_by_name.refresh()
        self._payloads_to_commit = []

        for payload in self.payloads:
            fabric_name = payload.get("FABRIC_NAME", None)
            if fabric_name not in self._fabric_details_by_name.all_data:
                continue

            self._fabric_update_required = set()
            try:
                self._fabric_needs_update_for_merged_state(payload)
            except ValueError as error:
                raise ValueError(error) from error

            if True not in self._fabric_update_required:
                continue
            self._payloads_to_commit.append(
                copy.deepcopy(self._fabric_changes_payload[fabric_name])
            )

    def _send_payloads(self):
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
        try:
            self._fixup_payloads_to_commit()
        except ValueError as error:
            raise ValueError(error) from error

        for payload in self._payloads_to_commit:
            commit_payload = copy.deepcopy(payload)
            if "DEPLOY" in commit_payload:
                commit_payload.pop("DEPLOY")
            try:
                self._send_payload(commit_payload)
            except ValueError as error:
                raise ValueError(error) from error

        # Skip config-save if prior actions encountered errors.
        if True in self._results.failed:
            return

        for payload in self._payloads_to_commit:
            try:
                self._config_save(payload)
            except ValueError as error:
                raise ValueError(error) from error

        # Skip config-deploy if prior actions encountered errors.
        if True in self._results.failed:
            return

        for payload in self._payloads_to_commit:
            try:
                self._config_deploy(payload)
            except (ControllerResponseError, ValueError) as error:
                raise ValueError(error) from error

    def _set_fabric_update_endpoint(self, payload):
        """
        - Set the endpoint for the fabric create API call.
        - raise ``ValueError`` if the enpoint assignment fails
        """
        try:
            self._ep_fabric_update.fabric_name = payload.get("FABRIC_NAME")
        except ValueError as error:
            raise ValueError(error) from error

        # Used to convert fabric type to template name
        self.fabric_type = copy.copy(payload.get("FABRIC_TYPE"))
        try:
            self.fabric_types.fabric_type = self.fabric_type
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self._ep_fabric_update.template_name = self.fabric_types.template_name
        except ValueError as error:
            raise ValueError(error) from error

        payload.pop("FABRIC_TYPE", None)
        self.path = self._ep_fabric_update.path
        self.verb = self._ep_fabric_update.verb

    def _send_payload(self, payload):
        """
        - Send one fabric update payload
        - raise ``ValueError`` if the endpoint assignment fails
        """
        method_name: str = inspect.stack()[0][3]

        try:
            self._set_fabric_update_endpoint(payload)
        except ValueError as error:
            raise ValueError(error) from error

        msg = f"{self.class_name}.{method_name}: "
        msg += f"verb: {self.verb}, path: {self.path}, "
        msg += f"payload: {json.dumps(payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # We don't want RestSend to retry on errors since the likelihood of a
        # timeout error when updating a fabric is low, and there are many cases
        # of permanent errors for which we don't want to retry.
        self._rest_send.timeout = 1
        self._rest_send.path = self.path
        self._rest_send.verb = self.verb
        self._rest_send.payload = payload
        self._rest_send.commit()

        if self._rest_send.result_current["success"] is False:
            self._results.diff_current = {}
        else:
            self._results.diff_current = copy.deepcopy(payload)

        self.send_payload_result[payload["FABRIC_NAME"]] = (
            self._rest_send.result_current["success"]
        )
        self._results.action = self.action
        self._results.check_mode = self._rest_send.check_mode
        self._results.state = self._rest_send.state
        self._results.response_current = copy.deepcopy(self._rest_send.response_current)
        self._results.result_current = copy.deepcopy(self._rest_send.result_current)
        self._results.register_task_result()

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
    def payloads(self, value: list[dict[str, Any]]) -> None:
        method_name: str = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be a list of dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise ValueError(msg)
        for item in value:
            try:
                self._verify_payload(item)
            except ValueError as error:
                raise ValueError(error) from error
        self._payloads = value


class FabricUpdateBulk(FabricUpdateCommon):
    """
    # Summary

    Update fabrics in bulk.

    ##vUsage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.update import FabricUpdateBulk
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import Results

    payloads = [
        { "FABRIC_NAME": "fabric1", "BGP_AS": 65000, "DEPLOY": True },
        { "FABRIC_NAME": "fabric2", "BGP_AS": 65001, "DEPLOY: False }
    ]
    results = Results()
    instance = FabricUpdateBulk(ansible_module)
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
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.action: str = "fabric_update_bulk"

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        self._rest_send: RestSend = RestSend({})

        self._results: Results = Results()
        self._results.action = self.action
        self._results.operation_type = OperationType.UPDATE
        self._payloads: list[dict] = []

        msg = "ENTERED FabricUpdateBulk()"
        self.log.debug(msg)

    def commit(self):
        """
        # Summary

        - Update fabrics and register results.
        - Return if there are no fabrics to update for merged state.

        ## Raises

        ### ValueError

        - `payloads` is not set
        - `rest_send` is not set
        - `_build_payloads_for_merged_state` fails
        - `_send_payloads` fails
        """
        method_name: str = inspect.stack()[0][3]

        if not self.payloads:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            raise ValueError(msg)

        if not self._rest_send.params:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit."
            raise ValueError(msg)

        self._results.action = self.action
        self._results.check_mode = self._rest_send.check_mode
        self._results.state = self._rest_send.state

        try:
            self._build_payloads_for_merged_state()
        except ValueError as error:
            raise ValueError(error) from error

        if len(self._payloads_to_commit) == 0:
            self._results.diff_current = {}
            self._results.result_current = {"success": True, "changed": False}
            msg = "No fabrics to update for merged state."
            self._results.response_current = {"RETURN_CODE": 200, "MESSAGE": msg}
            self._results.register_task_result()
            return

        try:
            self._send_payloads()
        except ValueError as error:
            self._results.diff_current = {}
            self._results.result_current = {"success": False, "changed": False}
            return_code = self._rest_send.response_current.get("RETURN_CODE", None)
            msg = f"ValueError self._results.response: {self._results.response}"
            self.log.debug(msg)
            self._results.response_current = {
                "RETURN_CODE": f"{return_code}",
                "MESSAGE": f"{error}",
            }
            self._results.register_task_result()
            raise ValueError(error) from error

    @property
    def rest_send(self) -> RestSend:
        """
        # Summary

        An instance of the RestSend class.

        ## Raises

        -   setter: `TypeError` if the value is not an instance of RestSend.
        -   setter: `ValueError` if RestSend.params is not set.

        ## getter

        Return an instance of the RestSend class.

        ## setter

        Set an instance of the RestSend class.
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        method_name: str = inspect.stack()[0][3]
        _class_have: str = ""
        _class_need: Literal["RestSend"] = "RestSend"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        # Summary

        An instance of the Results class.

        ## Raises

        -   setter: `TypeError` if the value is not an instance of Results.

        ## getter

        Return an instance of the Results class.

        ## setter

        Set an instance of the Results class.
        """
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        method_name: str = inspect.stack()[0][3]
        _class_have: str = ""
        _class_need: Literal["Results"] = "Results"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._results = value
        self._results.action = self.action
        self._results.operation_type = OperationType.UPDATE
