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

import inspect
from typing import Any, Dict

from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log


class ImagePolicyCommon:
    """
    Common methods used by the other classes supporting
    dcnm_image_policy module

    Usage (where ansible_module is an instance of
    AnsibleModule or MockAnsibleModule):

    class MyClass(ImagePolicyCommon):
        def __init__(self, module):
            super().__init__(module)
        ...
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.ansible_module = ansible_module
        self.params = ansible_module.params

        self.log = Log(ansible_module)
        self.log.debug = True
        self.log.logfile = "/tmp/dcnm_image_policy.log"

        self.properties: Dict[str, Any] = {}
        self.properties["changed"] = False
        self.properties["diff"] = []

        msg = f"{self.class_name}.{method_name}: DONE"
        self.log.log_msg(msg)

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

        Handle POST, PUT responses from the controller.

        Returns: dict() with the following keys:
        - changed:
            - True if changes were made to by the controller
            - False otherwise
        - success:
            - False if RETURN_CODE != 200 or MESSAGE != "OK"
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
    def failed_result(self):
        """
        return a result for a failed task with no changes
        """
        result = {}
        result["changed"] = False
        result["diff"] = []
        return result

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
            msg += f"changed must be a bool. Got {value}"
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
            msg += f"diff must be a dict. Got {value}"
            self.ansible_module.fail_json(msg)
        self.properties["diff"].append(value)

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
            msg += f"failed must be a bool. Got {value}"
            self.ansible_module.fail_json(msg)
        self.properties["failed"] = value
