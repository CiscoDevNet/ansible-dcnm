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
from time import sleep

# Using only for its failed_result property
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_task_result import \
    ImageUpgradeTaskResult
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send


class ImageUpgradeCommon:
    """
    Common methods used by the other image upgrade classes

    Usage (where module is an instance of AnsibleModule):

    class MyClass(ImageUpgradeCommon):
        def __init__(self, module):
            super().__init__(module)
        ...
    """

    def __init__(self, module):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED ImageUpgradeCommon()"
        self.log.debug(msg)

        self.module = module
        self.params = module.params

        self.properties = {}
        self.properties["changed"] = False
        self.properties["diff"] = []
        self.properties["failed"] = False
        self.properties["response"] = []
        self.properties["response_current"] = {}
        self.properties["result"] = []
        self.properties["result_current"] = {}
        self.properties["send_interval"] = 5
        self.properties["timeout"] = 300
        self.properties["unit_test"] = False

    def dcnm_send_with_retry(self, payload=None):
        """
        Call dcnm_send() with retries until successful response or timeout is exceeded.

        Properties read:
            self.send_interval: interval between retries (set in ImageUpgradeCommon)
            self.timeout: timeout in seconds (set in ImageUpgradeCommon)
            self.verb: HTTP verb (set in the calling class's commit() method)
            self.path: HTTP path (set in the calling class's commit() method)
            payload:
                - (optionally) passed directly to this function.
                - Normally only used when verb is POST or PUT.

        Properties written:
            self.properties["response"]: raw response from the controller
            self.properties["result"]: result from self._handle_response() method
        """
        caller = inspect.stack()[1][3]
        try:
            timeout = self.timeout
        except AttributeError:
            timeout = 300

        success = False
        msg = f"{caller}: Entering dcnm_send_with_retry loop. timeout {timeout}, send_interval {self.send_interval}"
        self.log.debug(msg)

        while timeout > 0 and success is False:
            if payload is None:
                msg = f"{caller}: Calling dcnm_send with no payload"
                self.log.debug(msg)
                response = dcnm_send(self.module, self.verb, self.path)
            else:
                msg = f"{caller}: Calling dcnm_send with payload: "
                msg += f"{json.dumps(payload, indent=4, sort_keys=True)}"
                self.log.debug(msg)
                response = dcnm_send(
                    self.module, self.verb, self.path, data=json.dumps(payload)
                )

            self.response_current = copy.deepcopy(response)
            self.response = copy.deepcopy(response)

            self.result_current = self._handle_response(response, self.verb)
            self.result = copy.deepcopy(self.result_current)

            success = self.result_current["success"]

            if success is False and self.unit_test is False:
                sleep(self.send_interval)
            timeout -= self.send_interval

        msg = f"{caller}: Exiting dcnm_send_with_retry loop. success {success}. "
        self.log.debug(msg)

        msg = f"{caller}: self.response_current {json.dumps(self.response_current, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{caller}: self.response {json.dumps(self.response, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{caller}: self.result_current {json.dumps(self.result_current, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = (
            f"{caller}: self.result {json.dumps(self.result, indent=4, sort_keys=True)}"
        )
        self.log.debug(msg)

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
        self.module.fail_json(msg)

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
        Return a result for a failed task with no changes
        """
        return ImageUpgradeTaskResult(None).failed_result

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
            self.module.fail_json(msg)
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
            self.module.fail_json(msg)
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
            self.module.fail_json(msg)
        self.properties["failed"] = value

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
            self.module.fail_json(msg, **self.failed_result)
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
            self.module.fail_json(msg, **self.failed_result)
        self.properties["response"].append(value)

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
            self.module.fail_json(msg, **self.failed_result)
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
            self.module.fail_json(msg, **self.failed_result)
        self.properties["result_current"] = value

    @property
    def send_interval(self):
        """
        Send interval, in seconds, for retrying responses from the controller.
        Valid values: int()
        Default: 5
        """
        return self.properties.get("send_interval")

    @send_interval.setter
    def send_interval(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, int):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be an int(). Got {value}."
            self.module.fail_json(msg, **self.failed_result)
        self.properties["send_interval"] = value

    @property
    def timeout(self):
        """
        Timeout, in seconds, for retrieving responses from the controller.
        Valid values: int()
        Default: 300
        """
        return self.properties.get("timeout")

    @timeout.setter
    def timeout(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, int):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be an int(). Got {value}."
            self.module.fail_json(msg, **self.failed_result)
        self.properties["timeout"] = value

    @property
    def unit_test(self):
        """
        Is the class running under a unit test.
        Set this to True in unit tests to speed the test up.
        Default: False
        """
        return self.properties.get("unit_test")

    @unit_test.setter
    def unit_test(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a bool(). Got {value}."
            self.module.fail_json(msg, **self.failed_result)
        self.properties["unit_test"] = value
