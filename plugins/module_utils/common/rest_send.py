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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_upgrade_task_result import \
    ImageUpgradeTaskResult
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send


class RestSend:
    """
    Send REST requests to the controller with retries, and handle responses.

    Usage (where ansible_module is an instance of AnsibleModule):

    rest_send = RestSend(ansible_module)
    rest_send.path = "/rest/top-down/fabrics"
    rest_send.verb = "GET"
    rest_send.payload = my_payload # Optional
    rest_send.commit()

    # list of responses from the controller for this session
    response = rest_send.response
    # dict with current controller response
    response_current = rest_send.response_current
    # list of results from the controller for this session
    result = rest_send.result
    # dict with current controller result
    result_current = rest_send.result_current
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.ansible_module = ansible_module

        msg = "ENTERED RestSend(): "
        self.log.debug(msg)

        self.params = ansible_module.params

        self._valid_verbs = {"GET", "POST", "PUT", "DELETE"}
        self.properties = {}
        self.properties["check_mode"] = False
        self.properties["response"] = []
        self.properties["response_current"] = {}
        self.properties["result"] = []
        self.properties["result_current"] = {}
        self.properties["send_interval"] = 5
        self.properties["timeout"] = 300
        self.properties["unit_test"] = False
        self.properties["verb"] = None
        self.properties["path"] = None
        self.properties["payload"] = None

    def _verify_commit_parameters(self):
        if self.verb is None:
            msg = f"{self.class_name}._verify_commit_parameters: "
            msg += "verb must be set before calling commit()."
            self.ansible_module.fail_json(msg, **self.failed_result)
        if self.path is None:
            msg = f"{self.class_name}._verify_commit_parameters: "
            msg += "path must be set before calling commit()."
            self.ansible_module.fail_json(msg, **self.failed_result)

    def commit(self):
        if self.check_mode is True:
            self.commit_check_mode()
        else:
            self.commit_normal_mode()

    def commit_check_mode(self):
        """
        Simulate a dcnm_send() call for check_mode

        Properties read:
            self.verb: HTTP verb e.g. GET, POST, PUT, DELETE
            self.path: HTTP path e.g. http://controller_ip/path/to/endpoint
            self.payload: Optional HTTP payload

        Properties written:
            self.properties["response_current"]: raw simulated response
            self.properties["result_current"]: result from self._handle_response() method
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}.  "
        msg += f"verb {self.verb}, path {self.path}."
        self.log.debug(msg)

        self._verify_commit_parameters()

        self.response_current = {}
        self.response_current["RETURN_CODE"] = 200
        self.response_current["METHOD"] = self.verb
        self.response_current["REQUEST_PATH"] = self.path
        self.response_current["MESSAGE"] = "OK"
        self.response_current["DATA"] = "[simulated-check-mode-response:Success] "
        self.result_current = self._handle_response(self.response_current)

        self.response = copy.deepcopy(self.response_current)
        self.result = copy.deepcopy(self.result_current)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}.  "
        msg += f"self.response_current: "
        msg += f"{json.dumps(self.response_current, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}.  "
        msg += f"self.response: "
        msg += f"{json.dumps(self.response, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}.  "
        msg += f"self.result_current: "
        msg += f"{json.dumps(self.result_current, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}.  "
        msg += f"self.result: "
        msg += f"{json.dumps(self.result, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def commit_normal_mode(self):
        """
        Call dcnm_send() with retries until successful response or timeout is exceeded.

        Properties read:
            self.send_interval: interval between retries (set in ImageUpgradeCommon)
            self.timeout: timeout in seconds (set in ImageUpgradeCommon)
            self.verb: HTTP verb e.g. GET, POST, PUT, DELETE
            self.path: HTTP path e.g. http://controller_ip/path/to/endpoint
            self.payload: Optional HTTP payload

        Properties written:
            self.properties["response"]: raw response from the controller
            self.properties["result"]: result from self._handle_response() method
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}.  "
        msg += f"verb {self.verb}, path {self.path}."
        self.log.debug(msg)

        self._verify_commit_parameters()
        try:
            timeout = self.timeout
        except AttributeError:
            timeout = 300

        success = False
        msg = f"{caller}: Entering commit loop. "
        self.log.debug(msg)

        while timeout > 0 and success is False:
            if self.payload is None:
                msg = f"{caller}: Calling dcnm_send: verb {self.verb}, path {self.path}"
                self.log.debug(msg)
                response = dcnm_send(self.ansible_module, self.verb, self.path)
            else:
                msg = f"{caller}: Calling dcnm_send: verb {self.verb}, path {self.path}, payload: "
                msg += f"{json.dumps(self.payload, indent=4, sort_keys=True)}"
                self.log.debug(msg)
                response = dcnm_send(
                    self.ansible_module,
                    self.verb,
                    self.path,
                    data=json.dumps(self.payload),
                )

            self.response_current = copy.deepcopy(response)
            self.result_current = self._handle_response(response)

            success = self.result_current["success"]
            if success is False and self.unit_test is False:
                sleep(self.send_interval)
            timeout -= self.send_interval

        msg = f"{caller}: Exiting dcnm_send_with_retry loop."
        msg += f"success {success}. verb {self.verb}, path {self.path}."
        self.log.debug(msg)

        self.response = copy.deepcopy(self.response_current)
        self.result = copy.deepcopy(self.result_current)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}.  "
        msg += f"self.response_current: "
        msg += f"{json.dumps(self.response_current, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}.  "
        msg += f"self.response: "
        msg += f"{json.dumps(self.response, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}.  "
        msg += f"self.result_current: "
        msg += f"{json.dumps(self.result_current, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}.  "
        msg += f"self.result: "
        msg += f"{json.dumps(self.result, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _handle_response(self, response):
        """
        Call the appropriate handler for response based on verb
        """
        if self.verb == "GET":
            return self._handle_get_response(response)
        if self.verb in {"POST", "PUT", "DELETE"}:
            return self._handle_post_put_delete_response(response)
        return self._handle_unknown_request_verbs(response)

    def _handle_unknown_request_verbs(self, response):
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Unknown request verb ({self.verb}) for response {response}."
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

    @property
    def check_mode(self):
        """
        Determines if dcnm_send should be called.

        Default: False

        If False, dcnm_send is called. Real controller responses
        are returned by RestSend()

        If True, dcnm_send is not called. Simulated controller responses
        are returned by RestSend()

        Discussion:
        We don't set check_mode from the value of self.ansible_module.check_mode
        because we want to be able to read data from the controller even when
        self.ansible_module.check_mode is True. For example, SwitchIssuDetails
        is a read-only operation, and we want to be able to read this data
        to provide a realistic simulation of stage, validate, and upgrade
        tasks.
        """
        return self.properties.get("check_mode")

    @check_mode.setter
    def check_mode(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a bool(). Got {value}."
            self.ansible_module.fail_json(msg, **self.failed_result)
        self.properties["check_mode"] = value

    @property
    def failed_result(self):
        """
        Return a result for a failed task with no changes
        """
        return ImageUpgradeTaskResult(self.ansible_module).failed_result

    @property
    def path(self):
        """
        Endpoint path for the REST request.
        e.g. "/appcenter/cisco/ndfc/api/v1/...etc..."
        """
        return self.properties.get("path")

    @path.setter
    def path(self, value):
        self.properties["path"] = value

    @property
    def payload(self):
        """
        Return the payload to send to the controller
        """
        return self.properties["payload"]

    @payload.setter
    def payload(self, value):
        self.properties["payload"] = value

    @property
    def response_current(self):
        """
        Return the current POST response from the controller
        instance.commit() must be called first.

        This is a dict of the current response from the controller.
        """
        return copy.deepcopy(self.properties.get("response_current"))

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
        return copy.deepcopy(self.properties.get("response"))

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
    def result(self):
        """
        Return the aggregated result from the controller
        instance.commit() must be called first.

        This is a list of results from the controller.
        """
        return copy.deepcopy(self.properties.get("result"))

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
        return copy.deepcopy(self.properties.get("result_current"))

    @result_current.setter
    def result_current(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.result_current must be a dict. "
            msg += f"Got {value}."
            self.ansible_module.fail_json(msg, **self.failed_result)
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
            self.ansible_module.fail_json(msg, **self.failed_result)
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
            self.ansible_module.fail_json(msg, **self.failed_result)
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
            self.ansible_module.fail_json(msg, **self.failed_result)
        self.properties["unit_test"] = value

    @property
    def verb(self):
        """
        Verb for the REST request.
        One of "GET", "POST", "PUT", "DELETE"
        """
        return self.properties.get("verb")

    @verb.setter
    def verb(self, value):
        method_name = inspect.stack()[0][3]
        if value not in self._valid_verbs:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be one of {sorted(self._valid_verbs)}. "
            msg += f"Got {value}."
            self.ansible_module.fail_json(msg, **self.failed_result)
        self.properties["verb"] = value
