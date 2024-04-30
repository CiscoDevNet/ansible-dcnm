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

import inspect
import logging
from typing import Any, Dict

from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.config_deploy import \
    FabricConfigDeploy
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.config_save import \
    FabricConfigSave
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_types import \
    FabricTypes


class FabricCommon:
    """
    Common methods used by the other classes supporting
    the dcnm_fabric module

    Usage (where params is AnsibleModule.params)

    class MyClass(FabricCommon):
        def __init__(self, params):
            super().__init__(params)
        ...
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        self.params = params

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.__init__(): "
            msg += "check_mode is required"
            raise ValueError(msg)

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.__init__(): "
            msg += "state is required"
            raise ValueError(msg)

        self.conversion = ConversionUtils()
        self.config_save = FabricConfigSave(params)
        self.config_deploy = FabricConfigDeploy(params)
        self.fabric_types = FabricTypes()

        msg = "ENTERED FabricCommon(): "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

        # Updated in _can_fabric_be_deployed()
        self.cannot_deploy_fabric_reason = ""

        # key: fabric_name, value: boolean
        # If True, the operation was successful
        # If False, the operation was not successful
        self.config_save_result = {}
        self.config_deploy_result = {}
        self.send_payload_result = {}

        # key: fabric_name, value: dict
        # Depending on state, updated in:
        # - self._fabric_needs_update_for_merged_state()
        # - self._fabric_needs_update_for_replaced_state()
        # Used to update the fabric configuration on the controller
        # with key/values that bring the controller to the intended
        # configuration.  This may include values not in the user
        # configuration that are needed to set the fabric to its
        # intended state.
        self._fabric_changes_payload = {}

        # List of fabrics that have the deploy flag set to True
        # and that are not empty.
        # Updated in _build_fabrics_to_config_deploy()
        self._fabrics_to_config_deploy = []

        # List of fabrics that have the deploy flag set to True
        # Updated in _build_fabrics_to_config_save()
        self._fabrics_to_config_save = []

        # Reset (depending on state) in:
        # - self._build_payloads_for_merged_state()
        # - self._build_payloads_for_replaced_state()
        # Updated (depending on state) in:
        # - self._fabric_needs_update_for_merged_state()
        # - self._fabric_needs_update_for_replaced_state()
        self._fabric_update_required = set()

        self._payloads_to_commit: list = []

        # path and verb cannot be defined here because endpoints.fabric name
        # must be set first.  Set these to None here and define them later in
        # the commit() method.
        self.path = None
        self.verb = None

        self._init_properties()
        self._init_key_translations()

    def _init_properties(self) -> None:
        """
        Initialize the properties dictionary.
        """
        self._properties: Dict[str, Any] = {}
        self._properties["fabric_details"] = None
        self._properties["fabric_summary"] = None
        self._properties["fabric_type"] = "VXLAN_EVPN"
        self._properties["rest_send"] = None
        self._properties["results"] = None

    def _init_key_translations(self):
        """
        Build a dictionary of fabric configuration key translations.

        The controller expects certain keys to be misspelled or otherwise
        different from the keys used in the payload this module sends.

        The dictionary is keyed on the payload key, and the value is either:
        -   The key the controller expects.
        -   None, if the key is not expected to be found in the controller
            fabric configuration.  This is useful for keys that are only
            used in the payload to the controller and later stripped before
            sending to the controller.
        """
        self._key_translations = {}
        self._key_translations["DEFAULT_QUEUING_POLICY_CLOUDSCALE"] = (
            "DEAFULT_QUEUING_POLICY_CLOUDSCALE"
        )
        self._key_translations["DEFAULT_QUEUING_POLICY_OTHER"] = (
            "DEAFULT_QUEUING_POLICY_OTHER"
        )
        self._key_translations["DEFAULT_QUEUING_POLICY_R_SERIES"] = (
            "DEAFULT_QUEUING_POLICY_R_SERIES"
        )
        self._key_translations["DEPLOY"] = None

    def _build_fabrics_to_config_deploy(self):
        """
        -   Build a list of fabrics to config-deploy and config-save
        -   This also removes the DEPLOY key from the payload
        -   raise ``ValueError`` if ``_can_fabric_be_deployed`` fails

        Skip:

        - payloads without FABRIC_NAME key (shouldn't happen, but just in case)
        - fabrics with DEPLOY key set to False
        - Empty fabrics (these cannot be config-deploy'ed or config-save'd)
        """
        for payload in self._payloads_to_commit:
            fabric_name = payload.get("FABRIC_NAME", None)
            if fabric_name is None:
                continue
            deploy = payload.pop("DEPLOY", None)
            if deploy is not True:
                continue

            can_deploy_fabric = False
            try:
                can_deploy_fabric = self._can_fabric_be_deployed(fabric_name)
            except ValueError as error:
                raise ValueError(error) from error

            if can_deploy_fabric is False:
                continue

            self._fabrics_to_config_deploy.append(fabric_name)
            self._fabrics_to_config_save.append(fabric_name)

    def _config_save(self):
        """
        -   Save the fabric configuration to the controller.
        -   Raise ``ValueError`` if the endpoint assignment fails.
        """
        method_name = inspect.stack()[0][3]

        for fabric_name in self._fabrics_to_config_save:
            if fabric_name not in self.send_payload_result:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"WARNING: fabric_name: {fabric_name}"
                msg += "not in send_payload_result."
                self.log.debug(msg)
                continue
            if self.send_payload_result[fabric_name] is False:
                # Skip config-save if send_payload failed
                # Set config_save_result to False so that config_deploy is skipped
                self.config_save_result[fabric_name] = False
                continue

            self.config_save.fabric_name = fabric_name
            self.config_save.rest_send = self.rest_send
            self.config_save.results = self.results
            try:
                self.config_save.commit()
            except ValueError as error:
                raise ValueError(error) from error
            result = self.rest_send.result_current["success"]
            self.config_save_result[fabric_name] = result

    def _config_deploy(self):
        """
        - Deploy the fabric configuration to the controller.
        - Raise ``ValueError`` if the endpoint assignment fails.
        """
        for fabric_name in self._fabrics_to_config_deploy:
            if self.config_save_result.get(fabric_name) is False:
                # Skip config-deploy if config-save failed
                continue

            self.config_deploy.fabric_name = fabric_name
            self.config_deploy.rest_send = self.rest_send
            self.config_deploy.results = self.results
            try:
                self.config_deploy.commit()
            except ValueError as error:
                raise ValueError(error) from error
            result = self.rest_send.result_current["success"]
            self.config_deploy_result[fabric_name] = result

    def _prepare_parameter_value_for_comparison(self, value):
        """
        convert payload values to controller formats

        Comparison order is important.
        bool needs to be checked before int since:
            isinstance(True, int) == True
            isinstance(False, int) == True
        """
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        return value

    def _prepare_anycast_gw_mac_for_comparison(self, fabric_name, mac_address):
        """
        Try to translate the ANYCAST_GW_MAC payload value to the format
        expected by the controller.

        - Return the translated mac_address if successful
        - Otherwise:
            -   Set results.failed to True
            -   Set results.changed to False
            -   Register the task result
            -   raise ``ValueError``
        """
        method_name = inspect.stack()[0][3]
        try:
            mac_address = self.conversion.translate_mac_address(mac_address)
        except ValueError as error:
            self.results.failed = True
            self.results.changed = False
            self.results.register_task_result()

            msg = f"{self.class_name}.{method_name}: "
            msg += "Error translating ANYCAST_GW_MAC: "
            msg += f"for fabric {fabric_name}, "
            msg += f"ANYCAST_GW_MAC: {mac_address}, "
            msg += f"Error detail: {error}"
            self.log.debug(msg)
            raise ValueError(msg) from error
        return mac_address

    def _fixup_payloads_to_commit(self) -> None:
        """
        -   Make any modifications to the payloads prior to sending them
            to the controller.
        -   raise ``ValueError`` if any modifications fail.

        NOTES:
        1. Add any modifications to the Modifications list below.

        Modifications:
        - Translate ANYCAST_GW_MAC to a format the controller understands
        - Validate BGP_AS
        """
        try:
            self._fixup_anycast_gw_mac()
            self._fixup_bgp_as()
        except ValueError as error:
            self.results.failed = True
            self.results.changed = False
            self.results.register_task_result()
            raise ValueError(error) from error

    def _fixup_bgp_as(self) -> None:
        """
        Raise ``ValueError`` if BGP_AS is not a valid BGP ASN.
        """
        method_name = inspect.stack()[0][3]
        for payload in self._payloads_to_commit:
            if "BGP_AS" not in payload:
                continue
            bgp_as = payload["BGP_AS"]
            if not self.conversion.bgp_as_is_valid(bgp_as):
                fabric_name = payload.get("FABRIC_NAME", "UNKNOWN")
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Invalid BGP_AS {bgp_as} "
                msg += f"for fabric {fabric_name}, "
                msg += f"Error detail: {self.conversion.bgp_as_invalid_reason}"
                raise ValueError(msg)

    def _verify_payload(self, payload) -> None:
        """
        - Verify that the payload is a dict and contains all mandatory keys
        - raise ``ValueError`` if the payload is not a dict
        - raise ``ValueError`` if the payload is missing mandatory keys
        """
        method_name = inspect.stack()[0][3]
        if self.state not in {"merged", "replaced"}:
            return
        msg = f"{self.class_name}.{method_name}: "
        msg += f"payload: {payload}"
        self.log.debug(msg)

        if not isinstance(payload, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Playbook configuration for fabrics must be a dict. "
            msg += f"Got type {type(payload).__name__}, "
            msg += f"value {payload}."
            raise ValueError(msg)

        sorted_payload = dict(sorted(payload.items(), key=lambda item: item[0]))
        fabric_type = payload.get("FABRIC_TYPE", None)
        fabric_name = payload.get("FABRIC_NAME", "UNKNOWN")

        if fabric_type is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Playbook configuration for fabric {fabric_name} "
            msg += "is missing mandatory parameter FABRIC_TYPE. "
            msg += "Valid values for FABRIC_TYPE: "
            msg += f"{self.fabric_types.valid_fabric_types}. "
            msg += f"Bad configuration: {sorted_payload}."
            raise ValueError(msg)

        if fabric_type not in self.fabric_types.valid_fabric_types:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Playbook configuration for fabric {fabric_name} "
            msg += f"contains an invalid FABRIC_TYPE ({fabric_type}). "
            msg += "Valid values for FABRIC_TYPE: "
            msg += f"{self.fabric_types.valid_fabric_types}. "
            msg += f"Bad configuration: {sorted_payload}."
            raise ValueError(msg)

        try:
            self.conversion.validate_fabric_name(fabric_name)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Playbook configuration for fabric {fabric_name} "
            msg += "contains an invalid FABRIC_NAME. "
            # error below already contains a period "." at the end
            msg += f"Error detail: {error} "
            msg += f"Bad configuration: {sorted_payload}."
            raise ValueError(msg) from error

        missing_parameters = []
        # FABRIC_TYPE is already validated above.
        # No need for try/except block here.
        self.fabric_types.fabric_type = fabric_type

        for parameter in self.fabric_types.mandatory_parameters:
            if parameter not in payload:
                missing_parameters.append(parameter)
        if len(missing_parameters) == 0:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Playbook configuration for fabric {fabric_name} "
        msg += "is missing mandatory parameters: "
        msg += f"{sorted(missing_parameters)}. "
        msg += f"Bad configuration: {sorted_payload}"
        raise ValueError(msg)

    def _fixup_anycast_gw_mac(self) -> None:
        """
        -   Translate the ANYCAST_GW_MAC address to the format the
            controller expects.
        -   Raise ``ValueError`` if the translation fails.
        """
        method_name = inspect.stack()[0][3]
        for payload in self._payloads_to_commit:
            if "ANYCAST_GW_MAC" not in payload:
                continue
            try:
                payload["ANYCAST_GW_MAC"] = self.conversion.translate_mac_address(
                    payload["ANYCAST_GW_MAC"]
                )
            except ValueError as error:
                fabric_name = payload.get("FABRIC_NAME", "UNKNOWN")
                anycast_gw_mac = payload.get("ANYCAST_GW_MAC", "UNKNOWN")

                msg = f"{self.class_name}.{method_name}: "
                msg += "Error translating ANYCAST_GW_MAC "
                msg += f"for fabric {fabric_name}, "
                msg += f"ANYCAST_GW_MAC: {anycast_gw_mac}, "
                msg += f"Error detail: {error}"
                raise ValueError(msg) from error

    def _can_fabric_be_deployed(self, fabric_name):
        """
        -   Return True if the fabric configuration can be saved and deployed.
        -   Return False otherwise.
        -   Re-raise ``ValueError`` if FabricSummary().fabric_name raises
            ``ValueError``
        -   Raise ``ValueError`` if a problem is encountered during
            FabricSummary().refresh()

        NOTES:
        -   If the fabric is empty, the controller will throw an error when
            attempting to deploy the fabric.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "ENTERED"
        self.log.debug(msg)

        try:
            self.fabric_summary.fabric_name = fabric_name
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.fabric_summary.refresh()
        except (ControllerResponseError, ValueError) as error:
            raise ValueError(error) from error

        if self.fabric_summary.fabric_is_empty is True:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Fabric {fabric_name} is empty. "
            msg += "Cannot deploy an empty fabric."
            self.log.debug(msg)
            self.cannot_deploy_fabric_reason = "Fabric is empty"
            return False
        return True

    @property
    def fabric_details(self):
        """
        An instance of the FabricDetails class.
        """
        return self._properties["fabric_details"]

    @fabric_details.setter
    def fabric_details(self, value):
        self._properties["fabric_details"] = value

    @property
    def fabric_summary(self):
        """
        An instance of the FabricSummary class.
        """
        return self._properties["fabric_summary"]

    @fabric_summary.setter
    def fabric_summary(self, value):
        self._properties["fabric_summary"] = value

    @property
    def fabric_type(self):
        """
        - getter: Return the type of fabric to create/update.
        - setter: Set the type of fabric to create/update.
        - setter: raise ``ValueError`` if ``value`` is not a valid fabric type

        See ``FabricTypes().valid_fabric_types`` for valid values
        """
        return self._properties["fabric_type"]

    @fabric_type.setter
    def fabric_type(self, value):
        method_name = inspect.stack()[0][3]
        if value not in self.fabric_types.valid_fabric_types:
            msg = f"{self.class_name}.{method_name}: "
            msg += "FABRIC_TYPE must be one of "
            msg += f"{self.fabric_types.valid_fabric_types}. "
            msg += f"Got {value}"
            raise ValueError(msg)
        self._properties["fabric_type"] = value

    @property
    def rest_send(self):
        """
        An instance of the RestSend class.
        """
        return self._properties["rest_send"]

    @rest_send.setter
    def rest_send(self, value):
        self._properties["rest_send"] = value

    @property
    def results(self):
        """
        An instance of the Results class.
        """
        return self._properties["results"]

    @results.setter
    def results(self, value):
        self._properties["results"] = value
