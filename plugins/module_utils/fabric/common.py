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
import re
from typing import Any, Dict


class FabricCommon:
    """
    Common methods used by the other classes supporting
    the dcnm_fabric module

    Usage (where ansible_module is an instance of
    AnsibleModule or MockAnsibleModule):

    class MyClass(FabricCommon):
        def __init__(self, module):
            super().__init__(module)
        ...
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module
        self.check_mode = self.ansible_module.check_mode
        self.state = ansible_module.params["state"]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED FabricCommon(): "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

        self.params = ansible_module.params

        self.properties: Dict[str, Any] = {}
        # Default to VXLAN_EVPN
        self.properties["fabric_type"] = "VXLAN_EVPN"
        self.properties["results"] = None

        self._valid_fabric_types = {"VXLAN_EVPN"}

        self.fabric_type_to_template_name_map = {}
        self.fabric_type_to_template_name_map["VXLAN_EVPN"] = "Easy_Fabric"

    def _fixup_payloads_to_commit(self) -> None:
        """
        Make any modifications to the payloads prior to sending them
        to the controller.

        Add any modifications to the list below.

        - Translate ANYCAST_GW_MAC to a format the controller understands
        """
        method_name = inspect.stack()[0][3]
        for payload in self._payloads_to_commit:
            if not "ANYCAST_GW_MAC" in payload:
                continue
            try:
                payload["ANYCAST_GW_MAC"] = self.translate_mac_address(
                    payload["ANYCAST_GW_MAC"]
                )
            except ValueError as error:
                fabric_name = payload.get("FABRIC_NAME", "UNKNOWN")
                anycast_gw_mac = payload.get("ANYCAST_GW_MAC", "UNKNOWN")

                self.results.failed = True
                self.results.changed = False
                self.results.register_task_result()

                msg = f"{self.class_name}.{method_name}: "
                msg += "Error translating ANYCAST_GW_MAC: "
                msg += f"for fabric {fabric_name}, "
                msg += f"ANYCAST_GW_MAC: {anycast_gw_mac}, "
                msg += f"Error detail: {error}"
                self.ansible_module.fail_json(msg, **self.results.failed_result)

    @staticmethod
    def translate_mac_address(mac_addr):
        """
        Accept mac address with any (or no) punctuation and convert it
        into the dotted-quad format that the controller expects.

        Return mac address formatted for the controller on success
        Return False on failure.
        """
        mac_addr = re.sub(r"[\W\s_]", "", mac_addr)
        if not re.search("^[A-Fa-f0-9]{12}$", mac_addr):
            raise ValueError(f"Invalid MAC address: {mac_addr}")
        return "".join((mac_addr[:4], ".", mac_addr[4:8], ".", mac_addr[8:]))

    def _handle_response(self, response, verb) -> Dict[str, Any]:
        """
        Call the appropriate handler for response based on verb
        """
        if verb == "GET":
            return self._handle_get_response(response)
        if verb in {"POST", "PUT", "DELETE"}:
            return self._handle_post_put_delete_response(response)
        return self._handle_unknown_request_verbs(response, verb)

    def _handle_unknown_request_verbs(self, response, verb):
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Unknown request verb ({verb}) for response {response}."
        self.ansible_module.fail_json(msg)

    def _handle_get_response(self, response) -> Dict[str, Any]:
        """
        Caller:
            - self._handle_response()
        Handle controller responses to GET requests
        Returns: dict() with the following keys:
        - found:
            - False, if request error was "Not found" and RETURN_CODE == 404
            - True otherwise
        - success:
            - False if RETURN_CODE != 200 or MESSAGE != "OK"
            - True otherwise
        """
        result = {}
        success_return_codes = {200, 404}
        if (
            response.get("RETURN_CODE") == 404
            and response.get("MESSAGE") == "Not Found"
        ):
            result["found"] = False
            result["success"] = True
            return result
        if (
            response.get("RETURN_CODE") not in success_return_codes
            or response.get("MESSAGE") != "OK"
        ):
            result["found"] = False
            result["success"] = False
            return result
        result["found"] = True
        result["success"] = True
        return result

    def _handle_post_put_delete_response(self, response) -> Dict[str, Any]:
        """
        Caller:
            - self.self._handle_response()

        Handle POST, PUT, DELETE responses from the controller.

        Returns: dict() with the following keys:
        - changed:
            - True if changes were made to by the controller
                - ERROR key is not present
                - MESSAGE == "OK"
            - False otherwise
        - success:
            - False if MESSAGE != "OK" or ERROR key is present
            - True otherwise
        """
        result = {}
        if response.get("ERROR") is not None:
            result["success"] = False
            result["changed"] = False
            return result
        if response.get("MESSAGE") != "OK" and response.get("MESSAGE") is not None:
            result["success"] = False
            result["changed"] = False
            return result
        result["success"] = True
        result["changed"] = True
        return result

    def fabric_type_to_template_name(self, value):
        """
        Return the template name for a given fabric type
        """
        method_name = inspect.stack()[0][3]
        if value not in self.fabric_type_to_template_name_map:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Unknown fabric type: {value}"
            self.ansible_module.fail_json(msg, **self.results.failed_result)
        return self.fabric_type_to_template_name_map[value]

    def make_boolean(self, value):
        """
        Return value converted to boolean, if possible.
        Return value, if value cannot be converted.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ["true", "yes"]:
                return True
            if value.lower() in ["false", "no"]:
                return False
        return value

    def make_none(self, value):
        """
        Return None if value is an empty string, or a string
        representation of a None type
        Return value otherwise
        """
        if value in ["", "none", "None", "NONE", "null", "Null", "NULL"]:
            return None
        return value

    @property
    def fabric_type(self):
        """
        The type of fabric to create/update.

        See self._valid_fabric_types for valid values
        """
        return self.properties["fabric_type"]

    @fabric_type.setter
    def fabric_type(self, value):
        method_name = inspect.stack()[0][3]
        if value not in self._valid_fabric_types:
            msg = f"{self.class_name}.{method_name}: "
            msg += "FABRIC_TYPE must be one of "
            msg += f"{sorted(self._valid_fabric_types)}. "
            msg += f"Got {value}"
            self.ansible_module.fail_json(msg, **self.results.failed_result)
        self.properties["fabric_type"] = value

    @property
    def results(self):
        """
        An instance of the Results class.
        """
        return self.properties["results"]

    @results.setter
    def results(self, value):
        self.properties["results"] = value
