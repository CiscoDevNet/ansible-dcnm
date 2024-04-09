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

    Usage (where params is AnsibleModule.params)

    class MyClass(FabricCommon):
        def __init__(self, params):
            super().__init__(params)
        ...
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.params = params

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

        msg = "ENTERED FabricCommon(): "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

        self._valid_fabric_types = {"VXLAN_EVPN"}

        self.fabric_type_to_template_name_map = {}
        self.fabric_type_to_template_name_map["VXLAN_EVPN"] = "Easy_Fabric"

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

    def _fixup_payloads_to_commit(self) -> None:
        """
        -   Make any modifications to the payloads prior to sending them
            to the controller.
        -   raise ``ValueError`` if any modifications fail.

        NOTES:
        1. Add any modifications to the Modifications list below.

        Modifications:
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
                msg += "Error translating ANYCAST_GW_MAC "
                msg += f"for fabric {fabric_name}, "
                msg += f"ANYCAST_GW_MAC: {anycast_gw_mac}, "
                msg += f"Error detail: {error}"
                raise ValueError(msg) from error

    @staticmethod
    def translate_mac_address(mac_addr):
        """
        Accept mac address with any (or no) punctuation and convert it
        into the dotted-quad format that the controller expects.

        Return mac address formatted for the controller on success
        Raise ValueError on failure.
        """
        mac_addr = re.sub(r"[\W\s_]", "", mac_addr)
        if not re.search("^[A-Fa-f0-9]{12}$", mac_addr):
            raise ValueError(f"Invalid MAC address: {mac_addr}")
        return "".join((mac_addr[:4], ".", mac_addr[4:8], ".", mac_addr[8:]))

    def _handle_response(self, response, verb) -> Dict[str, Any]:
        """
        - Call the appropriate handler for response based on verb
        - Raise ``ValueError`` if verb is unknown
        """
        if verb == "GET":
            return self._handle_get_response(response)
        if verb in {"POST", "PUT", "DELETE"}:
            return self._handle_post_put_delete_response(response)
        try:
            return self._handle_unknown_request_verbs(response, verb)
        except ValueError as error:
            raise ValueError(error) from error

    def _handle_unknown_request_verbs(self, response, verb):
        """
        Raise ``ValueError`` if verb is unknown
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Unknown request verb ({verb}) for response {response}."
        raise ValueError(msg)

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
        - Return the template name for a given fabric type
        - raise ``ValueError`` if value is not a valid fabric type
        """
        method_name = inspect.stack()[0][3]
        if value not in self.fabric_type_to_template_name_map:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Unknown fabric type: {value}"
            raise ValueError(msg)
        return self.fabric_type_to_template_name_map[value]

    @staticmethod
    def make_boolean(value):
        """
        Return value converted to boolean, if possible.
        Otherwise, return value.

        TODO: This method is duplicated in several other classes.
        TODO: Would be good to move this to a Utility() class.
        """
        if str(value).lower() in ["true", "yes"]:
            return True
        if str(value).lower() in ["false", "no"]:
            return False
        return value

    @staticmethod
    def make_none(value):
        """
        Return None if value is a string representation of a None type
        Otherwise, return value

        TODO: This method is duplicated in several other classes.
        TODO: Would be good to move this to a Utility() class.
        """
        if str(value).lower in ["", "none", "null"]:
            return None
        return value

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

        See ``self._valid_fabric_types`` for valid values
        """
        return self._properties["fabric_type"]

    @fabric_type.setter
    def fabric_type(self, value):
        method_name = inspect.stack()[0][3]
        if value not in self._valid_fabric_types:
            msg = f"{self.class_name}.{method_name}: "
            msg += "FABRIC_TYPE must be one of "
            msg += f"{sorted(self._valid_fabric_types)}. "
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
