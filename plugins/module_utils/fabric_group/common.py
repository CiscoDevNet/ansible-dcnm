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
from typing import Any

from ..common.conversion import ConversionUtils
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

    def __init__(self) -> None:
        self.class_name: str = self.__class__.__name__
        self.action = "fabric_group_common"

        self.conversion: ConversionUtils = ConversionUtils()
        self.fabric_group_types: FabricGroupTypes = FabricGroupTypes()

        # self._payloads_to_commit
        # Already added to all subclasses
        self._payloads_to_commit: list[dict[str, Any]] = []

        self.path: str = ""
        self.verb: str = ""

        self._fabric_type: str = "VXLAN_EVPN"

    def _fixup_payloads_to_commit(self) -> None:
        """
        # Summary

        -   Make any modifications to the payloads prior to sending them
            to the controller.
        -   raise ``ValueError`` if any modifications fail.

        ## Raises

        -   ``ValueError``: if any modifications fail.

        ## Notes

        1. Used in

        - FabricGroupCreate
        - FabricGroupUpdate

        2. Add any modifications to the Modifications list below.

        Modifications:
        - Translate ANYCAST_GW_MAC to a format the controller understands
        - Validate BGP_AS
        - Remove DEPLOY key if present
        """
        try:
            self._fixup_anycast_gw_mac()
            self._fixup_bgp_as()
            self._fixup_deploy()
        except ValueError as error:
            raise ValueError(error) from error

    def _fixup_anycast_gw_mac(self) -> None:
        """
        -   Translate the ANYCAST_GW_MAC address to the format the
            controller expects.
        -   Raise ``ValueError`` if the translation fails.
        """
        method_name: str = inspect.stack()[0][3]
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
        method_name: str = inspect.stack()[0][3]
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

    def _fixup_deploy(self) -> None:
        """
        -   Remove DEPLOY key from payloads prior to sending them
            to the controller.
        """
        for payload in self._payloads_to_commit:
            payload.pop("DEPLOY", None)

    def _verify_payload(self, payload: dict[str, Any]) -> None:
        """
        - Verify that the payload is a dict and contains all mandatory keys
        - raise ``ValueError`` if the payload is not a dict
        - raise ``ValueError`` if the payload is missing mandatory keys
        """
        method_name: str = inspect.stack()[0][3]
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
    def fabric_group_type(self) -> str:
        """
        - getter: Return the type of fabric group to create/update.
        - setter: Set the type of fabric group to create/update.
        - setter: raise ``ValueError`` if ``value`` is not a valid fabric group type

        See ``FabricTypes().valid_fabric_types`` for valid values
        """
        return self._fabric_group_type

    @fabric_group_type.setter
    def fabric_group_type(self, value: str) -> None:
        method_name: str = inspect.stack()[0][3]
        if value not in self.fabric_group_types.valid_fabric_group_types:
            msg: str = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_type must be one of "
            msg += f"{self.fabric_group_types.valid_fabric_group_types}. "
            msg += f"Got {value}"
            raise ValueError(msg)
        self._fabric_group_type = value
