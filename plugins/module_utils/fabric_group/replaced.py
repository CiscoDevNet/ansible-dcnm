#
# Copyright (c) 2025 Cisco and/or its affiliates.
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
Update fabric groups in bulk for replaced state
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging
from typing import Any, Union

from ..common.api.onemanage.endpoints import EpOneManageFabricGroupUpdate
from ..common.conversion import ConversionUtils
from ..common.exceptions import ControllerResponseError
from ..common.operation_type import OperationType
from ..common.rest_send_v2 import RestSend
from ..common.results_v2 import Results
from ..common.template_get_v2 import TemplateGet
from ..fabric.config_deploy_v2 import FabricConfigDeploy
from ..fabric.config_save_v2 import FabricConfigSave
from ..fabric.param_info import ParamInfo
from ..fabric.ruleset import RuleSet
from .common import FabricGroupCommon
from .fabric_group_default import FabricGroupDefault
from .fabric_group_types import FabricGroupTypes
from .fabric_groups import FabricGroups
from .verify_playbook_params import VerifyPlaybookParams


class FabricGroupReplaced(FabricGroupCommon):
    """
    # Summary

    Update fabric groups in bulk for replaced state.

    This class is not used currently due to ND 3.2 controller limitations.

    ## Raises

    -   `ValueError` if:
        -   `fabric_group_details` is not set.
        -   `fabric_groups` is not set.
        -   `payloads` is not set.
        -   `rest_send` is not set.
        -   `_build_payloads_for_replaced_state` fails.
        -   `_send_payloads` fails.

    ## Usage

    - params is an AnsibleModule.params dictionary

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.replaced import FabricGroupReplaced
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import Results

    payloads = [
        { "FABRIC_NAME": "fabric1", "FABRIC_TYPE": "VXLAN_EVPN", "BGP_AS": 65000, "DEPLOY": True },
        { "FABRIC_NAME": "fabric2", "FABRIC_TYPE": "LAN_CLASSIC", "DEPLOY": False }
    ]
    results = Results()
    instance = FabricGroupReplaced()
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

    def __init__(self) -> None:
        super().__init__()
        self.class_name: str = self.__class__.__name__
        self.action: str = "fabric_group_replace"
        self.operation_type: OperationType = OperationType.UPDATE

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        self.config_save: FabricConfigSave = FabricConfigSave()
        self.config_deploy: FabricConfigDeploy = FabricConfigDeploy()
        self.conversion: ConversionUtils = ConversionUtils()
        self._ep_fabric_group_update: EpOneManageFabricGroupUpdate = EpOneManageFabricGroupUpdate()
        self._fabric_group_default: FabricGroupDefault = FabricGroupDefault()
        self._fabric_group_types: FabricGroupTypes = FabricGroupTypes()
        self._fabric_group_type: str = ""
        self._fabric_groups: FabricGroups = FabricGroups()
        self._param_info: ParamInfo = ParamInfo()
        self._ruleset: RuleSet = RuleSet()
        self._template_get: TemplateGet = TemplateGet()
        self._verify_playbook_params: VerifyPlaybookParams = VerifyPlaybookParams()
        self._fabric_group_changes_payload: dict[str, dict] = {}
        self._fabric_group_update_required: set[bool] = set()
        # key: fabric_type, value: dict
        # Updated in _build_fabric_templates()
        # Stores the fabric template, pulled from the controller,
        # for each fabric type in the user's payload.
        self._fabric_templates: dict[str, dict] = {}

        # key: fabric_name, value: dict containing the current
        # controller fabric configuration for fabric_name.
        # Populated in _fabric_group_needs_update_for_replaced_state()
        self._controller_config: dict[str, dict] = {}

        self._key_translations: dict[str, str] = {}
        self._payloads: list[dict] = []
        self._payloads_to_commit: list[dict] = []

        # Properties to be set by caller
        self._rest_send: RestSend = RestSend({})
        self._results: Results = Results()

        msg = f"ENTERED {self.class_name}()"
        self.log.debug(msg)

    def _translate_payload_for_comparison(self, payload: dict) -> dict:
        """
        Translate user payload keys to controller keys if necessary.
        This handles the following:

        -   Translate correctly-spelled user keys to incorrectly-spelled
            controller keys.
        -   Translate the format of user values to the format expected by
            the controller.
        """
        translated_payload: dict[str, Any] = {}
        for payload_key, payload_value in payload.items():
            # Translate payload keys to equivilent keys on the controller
            # if necessary.  This handles cases where the controller key
            # is misspelled and we want our users to use the correct
            # spelling.
            user_parameter: Union[str, None] = ""
            if payload_key in self._key_translations:
                user_parameter = self._key_translations[payload_key]
            else:
                user_parameter = payload_key

            user_value = copy.copy(payload_value)

            # Skip the FABRIC_TYPE key since the payload FABRIC_TYPE value
            # will be e.g. "VXLAN_EVPN", whereas the fabric configuration will
            # be something along the lines of "Switch_Fabric"
            if user_parameter == "FABRIC_TYPE":
                continue

            # self._key_translations returns None for any keys that would not
            # be found in the controller configuration (e.g. DEPLOY).
            # Skip these keys.
            if user_parameter is None:
                continue

            user_value = self._prepare_parameter_value_for_comparison(user_value)
            if user_parameter == "ANYCAST_GW_MAC":
                try:
                    user_value = self.conversion.translate_mac_address(user_value)
                except ValueError as error:
                    raise ValueError(error) from error

            translated_payload[user_parameter] = user_value
        return copy.deepcopy(translated_payload)

    def update_site_id(self, playbook, controller) -> Union[dict, None]:
        """
        # Summary

        Special-case handling for fabric SITE_ID parameter update.

        ## Raises

        None

        ## Discussion

        -   If playbook.SITE_ID == controller.SITE_ID, no change is needed.
            Return None.
        -   If playbook.SITE_ID == controller.BGP_AS, no change is needed.
            Return None.
        -   If playbook.SITE_ID is not None and playbook.SITE_ID != BGP_AS,
            update payload with playbook.SITE_ID.
        -   If playbook.SITE_ID is None, and controller.SITE_ID != controller.BGP_AS,
            update the payload with controller.BGP_AS.
        -   Default return is None (don't add SITE_ID to payload).
        """
        bgp_as = self._controller_config.get("BGP_AS", None)
        if playbook == controller:
            return None
        if playbook == bgp_as:
            return None
        if playbook is not None and playbook != bgp_as:
            return {"SITE_ID": playbook}
        if playbook is None and controller != bgp_as:
            return {"SITE_ID": bgp_as}
        return None

    def _fabric_group_needs_update_for_replaced_state(self, payload):
        """
        # Summary

        TODO: This method currently does NOT add True to self._fabric_group_update_required

        Add True to self._fabric_group_update_required set() if the fabric group needs
        to be updated for replaced state.

        1. Generate a default fabric-group configuration based on the fabric-group template.
        2. Merge the user's playbook configuration onto the default configuration.
        3. Compare the resulting configuration against the controller's current fabric-group configuration.
        4. If there are any differences, add True to self._fabric_group_update_required set(),
           and populate self._fabric_group_changes_payload[fabric_name] with the merged configuration.

        ## Raises

        -   `ValueError` if:
            -   `_fabric_group_default.commit()` fails.
            -   `_fabric_group_details.refresh()` fails.
        """
        method_name = inspect.stack()[0][3]
        fabric_group_default = FabricGroupDefault()
        fabric_group_default.fabric_group_name = payload.get("FABRIC_NAME", "")
        fabric_group_default.rest_send = self._rest_send
        fabric_group_default.commit()

        msg = f"{self.class_name}.{method_name}: "
        msg += f"config_user for fabric {fabric_group_default.fabric_group_name}: "
        msg += f"{json.dumps(payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        config_default = fabric_group_default.config.get("nvPairs", {})
        msg = f"{self.class_name}.{method_name}: "
        msg += f"config_default for fabric {fabric_group_default.fabric_group_name}: "
        msg += f"{json.dumps(config_default, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        config_merged = copy.deepcopy(config_default)
        for key, value in payload.items():
            if key in {"FABRIC_NAME", "FABRIC_TYPE", "DEPLOY"}:
                continue
            config_merged[key] = value

        self._fabric_group_details.rest_send = self._rest_send
        self._fabric_group_details.fabric_group_name = payload.get("FABRIC_NAME", "")
        self._fabric_group_details.refresh()

        config_controller = self._fabric_group_details.all_data.get(self._fabric_group_details.fabric_group_name, {}).get("nvPairs", {})
        msg = f"{self.class_name}.{method_name}: "
        msg += f"config_controller for fabric {self._fabric_group_details.fabric_group_name}: "
        msg += f"{json.dumps(config_controller, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _build_fabric_templates(self):
        """
        # Summary

        -   Build a dictionary, keyed on fabric_group_type, whose value is the
            template for that fabric_group_type.
        -   To minimize requests to the controller, only the templates
            associated with fabric_group_types present in the user's payload are
            retrieved.

        ## Raises

        -   `ValueError` if
            -   setting `fabric_group_type` on `FabricGroupTypes` fails.
            -   setting `template_name` on `TemplateGet` fails.
            -   `TemplateGet.refresh()` fails.
        """
        method_name = inspect.stack()[0][3]

        for payload in self.payloads:
            fabric_group_type: str = payload.get("FABRIC_TYPE", "")
            if fabric_group_type in self._fabric_templates:
                continue
            if not fabric_group_type:
                continue
            try:
                self._fabric_group_types.fabric_group_type = fabric_group_type
            except ValueError as error:
                raise ValueError(error) from error

            try:
                self._template_get.template_name = self._fabric_group_types.template_name
            except TypeError as error:
                raise ValueError(error) from error

            try:
                self._template_get.refresh()
            except (ControllerResponseError, ValueError) as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Failed to retrieve template for fabric type {fabric_group_type}. "
                msg += f"Error detail: {error}"
                self.log.error(msg)
                raise ValueError(msg) from error
            self._fabric_templates[fabric_group_type] = self._template_get.template

    def _build_payloads_for_replaced_state(self):
        """
        # Summary

        -   Build a list of dict of payloads to commit for replaced state.
        -   Skip payloads for fabric groups that do not exist on the controller.
        -   Expects self.payloads to be a list of dict, with each dict
            being a payload for the fabric create API endpoint.
        -   Populates self._payloads_to_commit with a list of payloads to commit.

        ## Raises

        -   `ValueError` if
            -   `_fabric_groups.refresh()` fails.
            -   `_build_fabric_templates` fails.
            -   `_initial_payload_validation` fails.
            -   `_fabric_group_needs_update_for_replaced_state` fails.

        """
        self._fabric_groups.rest_send = self._rest_send
        self._fabric_groups.refresh()
        self._payloads_to_commit = []
        # Builds self._fabric_templates dictionary, keyed on fabric type.
        # Value is the fabric template associated with each fabric_type.
        self._build_fabric_templates()

        for payload in self.payloads:
            fabric_name = payload.get("FABRIC_NAME", "")
            if fabric_name not in self._fabric_groups.fabric_group_names:
                continue

            # Validate explicitly-set user parameters and inter-parameter
            # dependencies.  The user must provide a complete valid
            # non-default config since replaced-state defaults everything else.
            self._initial_payload_validation(payload)
            self._fabric_group_update_required = set()
            try:
                self._fabric_group_needs_update_for_replaced_state(payload)
            except ValueError as error:
                raise ValueError(error) from error

            if True not in self._fabric_group_update_required:
                continue
            self._payloads_to_commit.append(copy.deepcopy(self._fabric_group_changes_payload[fabric_name]))

    def _initial_payload_validation(self, payload) -> None:
        """
        -   Perform parameter validation and inter-parameter dependency
            checks on parameters the user is explicitely setting.
        -   Raise ``ValueError`` if a payload validation fails.
        """
        fabric_group_type = payload.get("FABRIC_TYPE", None)
        fabric_name = payload.get("FABRIC_NAME", None)
        try:
            self._verify_playbook_params.config_playbook = payload
        except TypeError as error:
            raise ValueError(error) from error

        try:
            self._fabric_group_types.fabric_group_type = fabric_group_type
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self._verify_playbook_params.template = self._fabric_templates[fabric_group_type]
        except TypeError as error:
            raise ValueError(error) from error
        config_controller = self.fabric_group_details.all_data.get(fabric_name, {}).get("nvPairs", {})

        try:
            self._verify_playbook_params.config_controller = config_controller
        except TypeError as error:
            raise ValueError(error) from error

        try:
            self._verify_playbook_params.commit()
        except ValueError as error:
            raise ValueError(error) from error

    def _send_payloads(self):
        """
        -   If ``check_mode`` is ``False``, send the payloads
            to the controller.
        -   If ``check_mode`` is ``True``, do not send the payloads
            to the controller.
        -   In both cases, register results.
        -   Re-raise ``ValueError`` if any of the following fail:
            -   ``FabricCommon()._fixup_payloads_to_commit()``
            -   ``FabricReplacedCommon()._send_payload()``
            -   ``FabricReplacedCommon()._config_save()``
            -   ``FabricReplacedCommon()._config_deploy()``
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
        if True in self.results.failed:
            return

        for payload in self._payloads_to_commit:
            try:
                self.config_save.payload = payload
            except ValueError as error:
                raise ValueError(error) from error

        # Skip config-deploy if prior actions encountered errors.
        if True in self.results.failed:
            return

        for payload in self._payloads_to_commit:
            try:
                self.config_deploy.payload = payload
            except (ControllerResponseError, ValueError) as error:
                raise ValueError(error) from error

    def _set_fabric_update_endpoint(self, payload):
        """
        - Set the endpoint for the fabric update API call.
        - raise ``ValueError`` if the enpoint assignment fails
        """
        try:
            self._ep_fabric_group_update.fabric_name = payload.get("FABRIC_NAME")
        except ValueError as error:
            raise ValueError(error) from error

        self._fabric_group_type = copy.copy(payload.get("FABRIC_TYPE"))
        try:
            self._fabric_group_types.fabric_group_type = self._fabric_group_type
        except ValueError as error:
            raise ValueError(error) from error

        payload.pop("FABRIC_TYPE", None)
        self.path = self._ep_fabric_group_update.path
        self.verb = self._ep_fabric_group_update.verb

    def _send_payload(self, payload):
        """
        - Send one fabric update payload
        - raise ``ValueError`` if the endpoint assignment fails
        """
        method_name = inspect.stack()[0][3]

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
        self.rest_send.timeout = 1
        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.payload = payload
        self.rest_send.commit()

        if self.rest_send.result_current["success"] is False:
            self.results.diff_current = {}
        else:
            self.results.diff_current = copy.deepcopy(payload)

        self.send_payload_result[payload["FABRIC_NAME"]] = self.rest_send.result_current["success"]
        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state
        self.results.response_current = copy.deepcopy(self.rest_send.response_current)
        self.results.result_current = copy.deepcopy(self.rest_send.result_current)
        self.results.register_task_result()

    @property
    def payloads(self):
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
    def payloads(self, value):
        method_name = inspect.stack()[0][3]
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

    def commit(self):
        """
        - Update fabric groups and register results.
        - Return if there are no fabric groups to update for replaced state.
        - raise ``ValueError`` if ``fabric_details`` is not set
        - raise ``ValueError`` if ``fabric_summary`` is not set
        - raise ``ValueError`` if ``payloads`` is not set
        - raise ``ValueError`` if ``rest_send`` is not set
        - raise ``ValueError`` if ``_build_payloads_for_replaced_state`` fails
        - raise ``ValueError`` if ``_send_payloads`` fails
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_group_details is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_details must be set prior to calling commit."
            raise ValueError(msg)

        if self._fabric_groups is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_groups must be set prior to calling commit."
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

        self._template_get.rest_send = self.rest_send
        try:
            self._build_payloads_for_replaced_state()
        except ValueError as error:
            raise ValueError(error) from error

        if len(self._payloads_to_commit) == 0:
            self.results.diff_current = {}
            self.results.result_current = {"success": True, "changed": False}
            msg = "No fabrics to update for replaced state."
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
        self._results.add_changed(False)
        self._results.operation_type = self.operation_type
