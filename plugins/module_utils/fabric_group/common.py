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
"""
Common methods used by the other classes supporting
the dcnm_fabric_group module
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import inspect
import logging

from ..common.conversion import ConversionUtils
from ..common.rest_send_v2 import RestSend
from ..common.results_v2 import Results
from ..fabric.fabric_summary_v2 import FabricSummary
from ..fabric_group.fabric_group_details import FabricGroupDetails
from .fabric_group_types import FabricGroupTypes

# pylint: disable=too-many-instance-attributes


class FabricGroupCommon:
    """
    ### Summary
    Common methods used by the other classes supporting the dcnm_fabric_group module

    ### Usage

    class MyClass(FabricGroupCommon):
        def __init__(self):
            super().__init__()
        ...
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.action = None

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = f"ENTERED {self.class_name}()"
        self.log.debug(msg)

        self.conversion: ConversionUtils = ConversionUtils()
        self.fabric_group_types: FabricGroupTypes = FabricGroupTypes()

        self._rest_send: RestSend = RestSend({})
        self._results: Results = Results()

        # key: fabric_name, value: boolean
        # If True, the operation was successful
        # If False, the operation was not successful
        self.send_payload_result: dict[str, bool] = {}

        # key: fabric_name, value: dict
        # Depending on state, updated in:
        # - self._fabric_group_needs_update_for_merged_state()
        # - self._fabric_group_needs_update_for_replaced_state()
        # Used to update the fabric configuration on the controller
        # with key/values that bring the controller to the intended
        # configuration.  This may include values not in the user
        # configuration that are needed to set the fabric to its
        # intended state.
        self._fabric_changes_payload: dict[str, dict] = {}

        # Reset (depending on state) in:
        # - self._build_payloads_for_merged_state()
        # - self._build_payloads_for_replaced_state()
        # Updated (depending on state) in:
        # - self._fabric_group_needs_update_for_merged_state()
        # - self._fabric_group_needs_update_for_replaced_state()
        self._fabric_group_update_required: set[bool] = set()

        self._payloads_to_commit: list = []

        self.path: str = ""
        self.verb: str = ""

        self._fabric_group_details: FabricGroupDetails = FabricGroupDetails()
        self._fabric_summary: FabricSummary = FabricSummary()
        self._fabric_type: str = "VXLAN_EVPN"

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
                payload["ANYCAST_GW_MAC"] = self.conversion.translate_mac_address(payload["ANYCAST_GW_MAC"])
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
        if self.action not in {"fabric_group_create", "fabric_group_replace", "fabric_group_update"}:
            return
        msg = f"{self.class_name}.{method_name}: "
        msg += f"payload: {payload}"
        self.log.debug(msg)

        if not isinstance(payload, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Playbook configuration for fabric groups must be a dict. "
            msg += f"Got type {type(payload).__name__}, value: {payload}."
            raise ValueError(msg)

        sorted_payload = dict(sorted(payload.items(), key=lambda item: item[0]))
        fabric_group_type = payload.get("FABRIC_TYPE", "MCFG")
        fabric_group_name = payload.get("FABRIC_NAME", "UNKNOWN")

        if fabric_group_type is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Playbook configuration for fabric group {fabric_group_name} "
            msg += "is missing mandatory parameter FABRIC_TYPE. "
            msg += "Valid values for FABRIC_TYPE: "
            msg += f"{self.fabric_group_types.valid_fabric_group_types}. "
            msg += f"Bad configuration: {sorted_payload}."
            raise ValueError(msg)

        if fabric_group_type not in self.fabric_group_types.valid_fabric_group_types:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Playbook configuration for fabric group {fabric_group_name} "
            msg += f"contains an invalid FABRIC_TYPE ({fabric_group_type}). "
            msg += "Valid values for FABRIC_TYPE: "
            msg += f"{self.fabric_group_types.valid_fabric_group_types}. "
            msg += f"Bad configuration: {sorted_payload}."
            raise ValueError(msg)

        try:
            self.conversion.validate_fabric_name(fabric_group_name)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Playbook configuration for fabric group {fabric_group_name} "
            msg += "contains an invalid FABRIC_NAME. "
            # error below already contains a period "." at the end
            msg += f"Error detail: {error} "
            msg += f"Bad configuration: {sorted_payload}."
            raise ValueError(msg) from error

        missing_parameters = []
        # FABRIC_TYPE is already validated above.
        # No need for try/except block here.
        self.fabric_group_types.fabric_group_type = fabric_group_type

        for parameter in self.fabric_group_types.mandatory_parameters:
            if parameter not in payload:
                missing_parameters.append(parameter)
        if len(missing_parameters) == 0:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Playbook configuration for fabric group {fabric_group_name} "
        msg += "is missing mandatory parameters: "
        msg += f"{sorted(missing_parameters)}. "
        msg += f"Bad configuration: {sorted_payload}"
        raise ValueError(msg)

    @property
    def fabric_group_details(self) -> FabricGroupDetails:
        """
        An instance of the FabricGroupDetails class.
        """
        return self._fabric_group_details

    @fabric_group_details.setter
    def fabric_group_details(self, value: FabricGroupDetails) -> None:
        self._fabric_group_details = value

    @property
    def fabric_summary(self) -> FabricSummary:
        """
        An instance of the FabricSummary class.
        """
        return self._fabric_summary

    @fabric_summary.setter
    def fabric_summary(self, value: FabricSummary) -> None:
        self._fabric_summary = value

    @property
    def fabric_group_type(self) -> str:
        """
        - getter: Return the type of fabric group to create/update.
        - setter: Set the type of fabric group to create/update.
        - setter: raise ``ValueError`` if ``value`` is not a valid fabric group type

        See ``FabricTypes().valid_fabric_types`` for valid values
        """
        return self._fabric_group_type

    @fabric_group_type.setter
    def fabric_group_type(self, value: str):
        method_name = inspect.stack()[0][3]
        if value not in self.fabric_group_types.valid_fabric_group_types:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_type must be one of "
            msg += f"{self.fabric_group_types.valid_fabric_group_types}. "
            msg += f"Got {value}"
            raise ValueError(msg)
        self._fabric_group_type = value

    @property
    def rest_send(self) -> RestSend:
        """
        An instance of the RestSend class.
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        if not value.params:
            method_name = inspect.stack()[0][3]
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must have params set."
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
