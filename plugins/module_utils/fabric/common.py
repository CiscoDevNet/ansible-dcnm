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

from ..common.conversion import ConversionUtils
from ..common.properties import Properties
from .config_deploy import FabricConfigDeploy
from .config_save import FabricConfigSave
from .fabric_types import FabricTypes


@Properties.add_rest_send
@Properties.add_results
class FabricCommon:
    """
    ### Summary
    Common methods used by the other classes supporting
    the dcnm_fabric module

    ### Usage

    class MyClass(FabricCommon):
        def __init__(self):
            super().__init__()
        ...
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.action = None

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.conversion = ConversionUtils()
        self.config_save = FabricConfigSave()
        self.config_deploy = FabricConfigDeploy()
        self.fabric_types = FabricTypes()

        msg = "ENTERED FabricCommon()"
        self.log.debug(msg)

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

        self._fabric_details = None
        self._fabric_summary = None
        self._fabric_type = "VXLAN_EVPN"
        self._rest_send = None
        self._results = None

        self._init_key_translations()

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

    def _config_save(self, payload):
        """
        -   Save the fabric configuration to the controller.
            Raise ``ValueError`` if payload is missing FABRIC_NAME.
        -   Raise ``ValueError`` if the endpoint assignment fails.
        """
        method_name = inspect.stack()[0][3]

        fabric_name = payload.get("FABRIC_NAME", None)
        if fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload is missing mandatory parameter: FABRIC_NAME."
            raise ValueError(msg)

        if self.send_payload_result[fabric_name] is False:
            # Skip config-save if send_payload failed
            # Set config_save_result to False so that config_deploy is skipped
            self.config_save_result[fabric_name] = False
            return

        self.config_save.payload = payload
        # pylint: disable=no-member
        self.config_save.rest_send = self.rest_send
        self.config_save.results = self.results
        try:
            self.config_save.commit()
        except ValueError as error:
            raise ValueError(error) from error
        result = self.rest_send.result_current["success"]
        self.config_save_result[fabric_name] = result

    def _config_deploy(self, payload):
        """
        -   Deploy the fabric configuration to the controller.
        -   Skip config-deploy if config-save failed
        -   Re-raise ``ValueError`` from FabricConfigDeploy(), if any.
        -   Raise ``ValueError`` if the payload is missing the FABRIC_NAME key.
        """
        method_name = inspect.stack()[0][3]
        fabric_name = payload.get("FABRIC_NAME")
        if fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload is missing mandatory parameter: FABRIC_NAME."
            raise ValueError(msg)
        if self.config_save_result.get(fabric_name) is False:
            # Skip config-deploy if config-save failed
            return

        try:
            self.config_deploy.fabric_details = self.fabric_details
            self.config_deploy.payload = payload
            self.config_deploy.fabric_summary = self.fabric_summary
            # pylint: disable=no-member
            self.config_deploy.rest_send = self.rest_send
            self.config_deploy.results = self.results
        except TypeError as error:
            raise ValueError(error) from error
        try:
            self.config_deploy.commit()
        except ValueError as error:
            raise ValueError(error) from error
        result = self.config_deploy.results.result_current["success"]
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

    def translate_anycast_gw_mac(self, fabric_name, mac_address):
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
            # pylint: disable=no-member
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
            # pylint: disable=no-member
            self.results.failed = True
            self.results.changed = False
            self.results.register_task_result()
            raise ValueError(error) from error

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
        if self.action not in {"fabric_create", "fabric_replace", "fabric_update"}:
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

    @property
    def fabric_details(self):
        """
        An instance of the FabricDetails class.
        """
        return self._fabric_details

    @fabric_details.setter
    def fabric_details(self, value):
        self._fabric_details = value

    @property
    def fabric_summary(self):
        """
        An instance of the FabricSummary class.
        """
        return self._fabric_summary

    @fabric_summary.setter
    def fabric_summary(self, value):
        self._fabric_summary = value

    @property
    def fabric_type(self):
        """
        - getter: Return the type of fabric to create/update.
        - setter: Set the type of fabric to create/update.
        - setter: raise ``ValueError`` if ``value`` is not a valid fabric type

        See ``FabricTypes().valid_fabric_types`` for valid values
        """
        return self._fabric_type

    @fabric_type.setter
    def fabric_type(self, value):
        method_name = inspect.stack()[0][3]
        if value not in self.fabric_types.valid_fabric_types:
            msg = f"{self.class_name}.{method_name}: "
            msg += "FABRIC_TYPE must be one of "
            msg += f"{self.fabric_types.valid_fabric_types}. "
            msg += f"Got {value}"
            raise ValueError(msg)
        self._fabric_type = value
