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

from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_task_result import \
    FabricTaskResult

# Using only for its failed_result property
# pylint: disable=line-too-long


# pylint: enable=line-too-long


class FabricCommon:
    """
    Common methods used by the other classes supporting
    dcnm_fabric_* modules

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
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.params = ansible_module.params

        self.properties: Dict[str, Any] = {}
        self.properties["changed"] = False
        self.properties["diff"] = []
        # Default to VXLAN_EVPN
        self.properties["fabric_type"] = "VXLAN_EVPN"
        self.properties["failed"] = False
        self.properties["response"] = []
        self.properties["response_current"] = {}
        self.properties["response_data"] = []
        self.properties["result"] = []
        self.properties["result_current"] = {}

        self._valid_fabric_types = {"VXLAN_EVPN"}

        self.fabric_type_to_template_name_map = {}
        self.fabric_type_to_template_name_map["VXLAN_EVPN"] = "Easy_Fabric"

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
            return False
        return "".join((mac_addr[:4], ".", mac_addr[4:8], ".", mac_addr[8:]))

    def _handle_response(self, response, verb):
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

    def _handle_get_response(self, response):
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

    def _handle_post_put_delete_response(self, response):
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
            self.ansible_module.fail_json(msg, **self.failed_result)
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
    def changed(self):
        """
        bool = whether we changed anything
        """
        return self.properties["changed"]

    @changed.setter
    def changed(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.changed must be a bool. Got {value}"
            self.ansible_module.fail_json(msg)
        self.properties["changed"] = value

    @property
    def diff(self):
        """
        List of dicts representing the changes made
        """
        return self.properties["diff"]

    @diff.setter
    def diff(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.diff must be a dict. Got {value}"
            self.ansible_module.fail_json(msg)
        self.properties["diff"].append(value)

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
            msg += f"FABRIC_TYPE must be one of "
            msg += f"{sorted(self._valid_fabric_types)}. "
            msg += f"Got {value}"
            self.ansible_module.fail_json(msg, **self.failed_result)
        self.properties["fabric_type"] = value

    @property
    def failed(self):
        """
        bool = whether we failed or not
        If True, this means we failed to make a change
        If False, this means we succeeded in making a change
        """
        return self.properties["failed"]

    @failed.setter
    def failed(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.failed must be a bool. Got {value}"
            self.ansible_module.fail_json(msg)
        self.properties["failed"] = value

    @property
    def failed_result(self):
        """
        return a result for a failed task with no changes
        """
        return FabricTaskResult(self.ansible_module).failed_result

    @property
    def response_current(self):
        """
        Return the current POST response from the controller
        instance.commit() must be called first.

        This is a dict of the current response from the controller.
        """
        return self.properties.get("response_current")

    @response_current.setter
    def response_current(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.response_current must be a dict. "
            msg += f"Got {value}."
            self.ansible_module.fail_json(msg, **self.failed_result)
        self.properties["response_current"] = value

    @property
    def response(self):
        """
        Return the aggregated POST response from the controller
        instance.commit() must be called first.

        This is a list of responses from the controller.
        """
        return self.properties.get("response")

    @response.setter
    def response(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.response must be a dict. "
            msg += f"Got {value}."
            self.ansible_module.fail_json(msg, **self.failed_result)
        self.properties["response"].append(value)

    @property
    def response_data(self):
        """
        Return the contents of the DATA key within current_response.
        """
        return self.properties.get("response_data")

    @response_data.setter
    def response_data(self, value):
        self.properties["response_data"].append(value)

    @property
    def result(self):
        """
        Return the aggregated result from the controller
        instance.commit() must be called first.

        This is a list of results from the controller.
        """
        return self.properties.get("result")

    @result.setter
    def result(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.result must be a dict. "
            msg += f"Got {value}."
            self.ansible_module.fail_json(msg, **self.failed_result)
        self.properties["result"].append(value)

    @property
    def result_current(self):
        """
        Return the current result from the controller
        instance.commit() must be called first.

        This is a dict containing the current result.
        """
        return self.properties.get("result_current")

    @result_current.setter
    def result_current(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.result_current must be a dict. "
            msg += f"Got {value}."
            self.ansible_module.fail_json(msg, **self.failed_result)
        self.properties["result_current"] = value
