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

__metaclass__ = type
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging

from ..common.api.v1.lan_fabric.rest.control.fabrics.fabrics import \
    EpFabricUpdate
from ..common.exceptions import ControllerResponseError
from .common import FabricCommon
from .fabric_types import FabricTypes
from .param_info import ParamInfo
from .ruleset import RuleSet
from .template_get import TemplateGet
from .verify_playbook_params import VerifyPlaybookParams


class FabricReplacedCommon(FabricCommon):
    """
    Common methods and properties for:
    - FabricReplacedBulk
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.action = "fabric_replace"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.ep_fabric_update = EpFabricUpdate()
        self.fabric_types = FabricTypes()
        self.param_info = ParamInfo()
        self.ruleset = RuleSet()
        self.template_get = TemplateGet()
        self.verify_playbook_params = VerifyPlaybookParams()

        # key: fabric_type, value: dict
        # Updated in _build_fabric_templates()
        # Stores the fabric template, pulled from the controller,
        # for each fabric type in the user's payload.
        self.fabric_templates = {}

        # key: fabric_name, value: dict containing the current
        # controller fabric configuration for fabric_name.
        # Populated in _fabric_needs_update_for_replaced_state()
        self._controller_config = {}

        msg = "ENTERED FabricReplacedCommon()"
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
        translated_payload = {}
        fabric_name = payload.get("FABRIC_NAME", None)
        for payload_key, payload_value in payload.items():
            # Translate payload keys to equivilent keys on the controller
            # if necessary.  This handles cases where the controller key
            # is misspelled and we want our users to use the correct
            # spelling.
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
                    user_value = self.translate_anycast_gw_mac(fabric_name, user_value)
                except ValueError as error:
                    raise ValueError(error) from error

            translated_payload[user_parameter] = user_value
        return copy.deepcopy(translated_payload)

    def update_site_id(self, playbook, controller):
        """
        ### Summary
        Special-case handling for fabric SITE_ID parameter update.

        ### Raises
        None

        ### Discussion
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

    def update_replaced_payload(self, parameter, playbook, controller, default):
        """
        ### Summary
        Given a parameter, and the parameter's values from:

        -   playbook config
        -   controller fabric config
        -   default value from the template

        Return either:

        -   None if the parameter does not need to be updated.
        -   A dict with the parameter and playbook value if the parameter
            needs to be updated.

        ### Usage:
        ```python
        payload_to_send_to_controller = {}
        for parameter, controller in _controller_config.items():
            playbook = playbook_config.get(parameter, None)
            default = default_config.get(parameter, None)
            result = self.update_replaced_payload(parameter, playbook, controller, default)
            if result is None:
                continue
            payload_to_send_to_controller.update(result)
        ```

        ### NOTES
        -   Special-case SITE_ID.
            -   The template default value is "", but the actual default value
                is BGP_AS.
        -   Explicitely skip ANYCAST_RP_IP_RANGE_INTERNAL.
            -   It is an internal parameter, but is not specified as such in
                the fabric template.
        """
        if parameter == "ANYCAST_RP_IP_RANGE_INTERNAL":
            return None
        if parameter == "SITE_ID":
            return self.update_site_id(playbook, controller)
        if playbook is None:
            if controller not in {default, ""}:
                if default is None:
                    # The controller prefers empty string over null.
                    return {parameter: ""}
                return {parameter: default}
            return None
        if playbook == controller:
            return None
        return {parameter: playbook}

    def _verify_value_types_for_comparison(
        self, fabric_name, parameter, user_value, controller_value, default_value
    ) -> None:
        """
        -   Raise ``ValueError`` if the value types differ between:
            playbook, controller, and default values.
        """
        method_name = inspect.stack()[0][3]
        type_set = set()
        value_source_set = set()
        if user_value is not None:
            type_set.add(type(user_value))
            value_source_set.add("playbook")
        if controller_value is not None:
            type_set.add(type(controller_value))
            value_source_set.add("controller")
        if default_value is not None:
            type_set.add(type(default_value))
            value_source_set.add("default")
        if len(type_set) > 1:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"parameter: {parameter}, "
            msg += f"fabric: {fabric_name}, "
            msg += f"conflicting value types {type_set} between "
            msg += f"the following sources: {sorted(value_source_set)}."
            raise ValueError(msg)

    def _fabric_needs_update_for_replaced_state(self, payload):
        """
        -   Add True to self._fabric_update_required set() if the fabric needs
            to be updated for replaced state.
        -   Populate self._fabric_changes_payload[fabric_name],
            with key/values that are required to:
            -   Bring the fabric configuration to a default state
            -   Apply the user's non-default parameters onto this
                default configuration
        -   This payload will be used to update the fabric.
        -   Raise ``ValueError`` if the fabric template is not found.
        -   Raise ``ValueError`` if ParamInfo().refresh() fails.
        -   Raise ``ValueError`` if the value types differ between the
            playbook, controller, and default values.

        The fabric needs to be updated if all of the following are true:
        -   A fabric configuration parameter (on the controller) differs
            from the default value for that parameter.  This needs to be
            set to either 1) the default value, or 2) the value in the
            caller's playbook configuration.
        -   A parameter in the payload has a different value than the
            corresponding default parameter in fabric configuration on
            the controller (case 2 above).

        NOTES:
        -   The fabric has already been verified to exist on the
            controller in ``_build_payloads_for_replaced_state()``.
        -   self.fabric_templates has already been populated in
            ``_build_payloads_for_replaced_state()``.
        """
        method_name = inspect.stack()[0][3]

        fabric_name = payload.get("FABRIC_NAME", None)
        fabric_type = payload.get("FABRIC_TYPE", None)

        self._fabric_changes_payload[fabric_name] = {}
        self._controller_config = self.fabric_details.all_data[fabric_name].get(
            "nvPairs", {}
        )

        # Refresh ParamInfo() with the fabric template
        try:
            self.param_info.template = self.fabric_templates.get(fabric_type)
        except TypeError as error:
            raise ValueError(error) from error
        try:
            self.param_info.refresh()
        except ValueError as error:
            raise ValueError(error) from error

        # Translate user payload for comparison against the controller
        # fabric configuration and default values in the fabric template.
        translated_payload = self._translate_payload_for_comparison(payload)

        # For each of the parameters in the controller fabric configuration,
        # compare against the user's payload and the default value in the
        # template.  Update _fabric_changes_payload with the result of
        # the comparison.
        for parameter, controller_value in self._controller_config.items():

            msg = f"parameter: {parameter}, "
            msg += f"controller_value: {controller_value}, "
            msg += f"type: {type(controller_value)}"
            self.log.debug(msg)

            try:
                parameter_info = self.param_info.parameter(parameter)
            except KeyError as error:
                msg = f"SKIP parameter: {parameter} in fabric {fabric_name}. "
                msg += "parameter not found in template."
                self.log.debug(msg)
                continue

            if parameter_info.get("internal", True) is True:
                msg = f"SKIP parameter: {parameter} in fabric {fabric_name}. "
                msg += "parameter is internal."
                self.log.debug(msg)
                continue

            user_value = translated_payload.get(parameter, None)
            default_value = parameter_info.get("default", None)
            default_value = self._prepare_parameter_value_for_comparison(default_value)

            msg = f"parameter: {parameter}, "
            msg += f"user_value: {user_value}, "
            msg += f"type: {type(user_value)}"
            self.log.debug(msg)

            msg = f"parameter: {parameter}, "
            msg += f"default_value: {default_value}, "
            msg += f"type: {type(default_value)}"
            self.log.debug(msg)

            self._verify_value_types_for_comparison(
                fabric_name, parameter, user_value, controller_value, default_value
            )

            result = self.update_replaced_payload(
                parameter, user_value, controller_value, default_value
            )
            if result is None:
                continue
            msg = f"UPDATE _fabric_changes_payload with result: {result}"
            self.log.debug(msg)
            self._fabric_changes_payload[fabric_name].update(result)
            self._fabric_update_required.add(True)

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

    def _build_fabric_templates(self):
        """
        -   Build a dictionary, keyed on fabric_type, whose value is the
            template for that fabric_type.
        -   Re-raise ``ValueError`` if ``fabric_types`` raises ``ValueError``
        -   To minimize requests to the controller, only the templates
            associated with fabric_types present in the user's payload are
            retrieved.
        """
        for payload in self.payloads:
            fabric_type = payload.get("FABRIC_TYPE", None)
            if fabric_type in self.fabric_templates:
                continue
            try:
                self.fabric_types.fabric_type = fabric_type
            except ValueError as error:
                raise ValueError(error) from error

            self.template_get.template_name = self.fabric_types.template_name
            self.template_get.refresh()
            self.fabric_templates[fabric_type] = self.template_get.template

    def _build_payloads_for_replaced_state(self):
        """
        -   Build a list of dict of payloads to commit for replaced state.
            Skip payloads for fabrics that do not exist on the controller.
        -   raise ``ValueError`` if ``_fabric_needs_update_for_replaced_state``
            fails.
        -   Expects self.payloads to be a list of dict, with each dict
            being a payload for the fabric create API endpoint.
        -   Populates self._payloads_to_commit with a list of payloads to
            commit.

        NOTES:
        -   self._fabric_needs_update_for_replaced_state() may remove
            payload key/values that would not change the controller
            configuration.
        """
        self.fabric_details.refresh()
        self._payloads_to_commit = []
        # Builds self.fabric_templates dictionary, keyed on fabric type.
        # Value is the fabric template associated with each fabric_type.
        self._build_fabric_templates()

        for payload in self.payloads:
            fabric_name = payload.get("FABRIC_NAME", None)
            if fabric_name not in self.fabric_details.all_data:
                continue

            # Validate explicitly-set user parameters and inter-parameter
            # dependencies.  The user must provide a complete valid
            # non-default config since replaced-state defaults everything else.
            try:
                self._initial_payload_validation(payload)
            except ValueError as error:
                raise ValueError(error) from error

            self._fabric_update_required = set()
            try:
                self._fabric_needs_update_for_replaced_state(payload)
            except ValueError as error:
                raise ValueError(error) from error

            if True not in self._fabric_update_required:
                continue
            self._payloads_to_commit.append(
                copy.deepcopy(self._fabric_changes_payload[fabric_name])
            )

    def _initial_payload_validation(self, payload) -> None:
        """
        -   Perform parameter validation and inter-parameter dependency
            checks on parameters the user is explicitely setting.
        -   Raise ``ValueError`` if a payload validation fails.
        """
        fabric_type = payload.get("FABRIC_TYPE", None)
        fabric_name = payload.get("FABRIC_NAME", None)
        try:
            self.verify_playbook_params.config_playbook = payload
        except TypeError as error:
            raise ValueError(error) from error

        try:
            self.fabric_types.fabric_type = fabric_type
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.verify_playbook_params.template = self.fabric_templates[fabric_type]
        except TypeError as error:
            raise ValueError(error) from error
        config_controller = self.fabric_details.all_data.get(fabric_name, {}).get(
            "nvPairs", {}
        )

        try:
            self.verify_playbook_params.config_controller = config_controller
        except TypeError as error:
            raise ValueError(error) from error

        try:
            self.verify_playbook_params.commit()
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
            if commit_payload.get("DEPLOY", None) is not None:
                commit_payload.pop("DEPLOY")
            try:
                self._send_payload(commit_payload)
            except ValueError as error:
                raise ValueError(error) from error

        # pylint: disable=no-member
        # Skip config-save if prior actions encountered errors.
        if True in self.results.failed:
            return

        for payload in self._payloads_to_commit:
            try:
                self._config_save(payload)
            except ValueError as error:
                raise ValueError(error) from error

        # Skip config-deploy if prior actions encountered errors.
        if True in self.results.failed:
            return

        for payload in self._payloads_to_commit:
            try:
                self._config_deploy(payload)
            except (ControllerResponseError, ValueError) as error:
                raise ValueError(error) from error

    def _set_fabric_update_endpoint(self, payload):
        """
        - Set the endpoint for the fabric update API call.
        - raise ``ValueError`` if the enpoint assignment fails
        """
        try:
            self.ep_fabric_update.fabric_name = payload.get("FABRIC_NAME")
        except ValueError as error:
            raise ValueError(error) from error

        self.fabric_type = copy.copy(payload.get("FABRIC_TYPE"))
        try:
            self.fabric_types.fabric_type = self.fabric_type
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.ep_fabric_update.template_name = self.fabric_types.template_name
        except ValueError as error:
            raise ValueError(error) from error

        payload.pop("FABRIC_TYPE", None)
        self.path = self.ep_fabric_update.path
        self.verb = self.ep_fabric_update.verb

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

        self.send_payload_result[payload["FABRIC_NAME"]] = (
            self.rest_send.result_current["success"]
        )
        self.results.action = self.action
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


class FabricReplacedBulk(FabricReplacedCommon):
    """
    Update fabrics in bulk for replaced state.

    Usage (where params is an AnsibleModule.params dictionary):
    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.update import \
        FabricReplacedBulk
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
        Results

    payloads = [
        { "FABRIC_NAME": "fabric1", "FABRIC_TYPE": "VXLAN_EVPN", "BGP_AS": 65000, "DEPLOY": True },
        { "FABRIC_NAME": "fabric2", "FABRIC_TYPE": "LAN_CLASSIC", "DEPLOY: False }
    ]
    results = Results()
    instance = FabricReplacedBulk(params)
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

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self._payloads = None

        self.log.debug("ENTERED FabricReplacedBulk()")

    def commit(self):
        """
        - Update fabrics and register results.
        - Return if there are no fabrics to update for replaced state.
        - raise ``ValueError`` if ``fabric_details`` is not set
        - raise ``ValueError`` if ``fabric_summary`` is not set
        - raise ``ValueError`` if ``payloads`` is not set
        - raise ``ValueError`` if ``rest_send`` is not set
        - raise ``ValueError`` if ``_build_payloads_for_replaced_state`` fails
        - raise ``ValueError`` if ``_send_payloads`` fails
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_details is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_details must be set prior to calling commit."
            raise ValueError(msg)

        if self.fabric_summary is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_summary must be set prior to calling commit."
            raise ValueError(msg)

        if self.payloads is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            raise ValueError(msg)

        # pylint: disable=no-member
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit."
            raise ValueError(msg)

        self.results.action = self.action
        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state

        self.template_get.rest_send = self.rest_send
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
