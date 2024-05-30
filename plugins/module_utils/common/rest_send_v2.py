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
import re
from time import sleep

# Using only for its failed_result property
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results


class RestSend:
    """
    ### Summary
    Send REST requests to the controller with retries, and handle responses.

    ### Usage
    Below we are using a Sender() class that requires an instance of
    AnsibleModule, and uses dcnm_send() to send requests to the controller.
    See dcnm_sender.py for details about implementing Sender() classes.

    ```python
    sender = Sender() # class that implements the sender interface
    sender.ansible_module = ansible_module

    rest_send = RestSend()
    rest_send.unit_test = True # optional, use in unit tests for speed
    rest_send.sender = sender
    rest_send.path = "/rest/top-down/fabrics"
    rest_send.verb = "GET"
    rest_send.payload = my_payload # optional
    rest_send.save_settings() # save current check_mode and timeout
    rest_send.timeout = 300 # optional
    rest_send.check_mode = True
    # Do things with rest_send...
    rest_send.commit()
    rest_send.restore_settings() # restore check_mode and timeout
    rest_send.commit()

    # list of responses from the controller for this session
    response = rest_send.response
    # dict containing the current controller response
    response_current = rest_send.response_current
    # list of results from the controller for this session
    result = rest_send.result
    # dict containing the current controller result
    result_current = rest_send.result_current
    ```
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.params = params
        msg = "ENTERED RestSend(): "
        msg += f"params: {self.params}"
        self.log.debug(msg)

        self.properties = {}
        self.properties["check_mode"] = False
        self.properties["path"] = None
        self.properties["payload"] = None
        self.properties["response"] = []
        self.properties["response_current"] = {}
        self.properties["result"] = []
        self.properties["result_current"] = {}
        self.properties["send_interval"] = 5
        self.properties["sender"] = None
        self.properties["timeout"] = 300
        self.properties["unit_test"] = False
        self.properties["verb"] = None

        # See save_settings() and restore_settings()
        self.saved_timeout = None
        self.saved_check_mode = None

        self._valid_verbs = {"GET", "POST", "PUT", "DELETE"}

        self.check_mode = self.params.get("check_mode", False)
        self.state = self.params.get("state")

        msg = "ENTERED RestSend(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def _verify_commit_parameters(self):
        """
        ### Summary
        Verify that required parameters are set prior to calling ``commit()``

        ### Raises
        -   ``ValueError`` if:
                -   ``path`` is not set
                -   ``sender`` is not set
                -   ``verb`` is not set
        """
        if self.path is None:
            msg = f"{self.class_name}._verify_commit_parameters: "
            msg += "path must be set before calling commit()."
            raise ValueError(msg)
        if self.sender is None:
            msg = f"{self.class_name}._verify_commit_parameters: "
            msg += "sender must be set before calling commit()."
            raise ValueError(msg)
        if self.verb is None:
            msg = f"{self.class_name}._verify_commit_parameters: "
            msg += "verb must be set before calling commit()."
            raise ValueError(msg)

    def restore_settings(self):
        """
        ### Summary
        Restore ``check_mode`` and ``timeout`` to their saved values.

        ### Raises
        None

        ### See also
        -   ``save_settings()``

        ### Discussion
        This is useful when a task needs to temporarily set ``check_mode``
        to False, (or change the timeout value) and then restore them to
        their original values.

        -   ``check_mode`` is not restored if ``save_setting()`` has not
            previously been called.
        -   ``timeout`` is not restored if ``save_setting()`` has not
            previously been called.
        """
        if self.saved_check_mode is not None:
            self.check_mode = self.saved_check_mode
        if self.saved_timeout is not None:
            self.timeout = self.saved_timeout

    def save_settings(self):
        """
        Save the current values of ``check_mode`` and ``timeout`` for later
        restoration.

        ### Raises
        None

        ### See also
        -   ``restore_settings()``


        -   ``check_mode`` is not saved if it has not yet been initialized.
        -   ``timeout`` is not save if it has not yet been initialized.
        """
        if self.check_mode is not None:
            self.saved_check_mode = self.check_mode
        if self.timeout is not None:
            self.saved_timeout = self.timeout

    def commit(self):
        """
        Send the REST request to the controller
        """
        msg = f"{self.class_name}.commit: "
        msg += f"check_mode: {self.check_mode}."
        self.log.debug(msg)
        if self.check_mode is True:
            self.commit_check_mode()
        else:
            self.commit_normal_mode()

    def commit_check_mode(self):
        """
        ### Summary
        Simulate a controller request for check_mode.

        ### Raises
        None

        ### Properties read:
            -   ``verb``: HTTP verb e.g. DELETE, GET, POST, PUT
            -   ``path``: HTTP path e.g. http://controller_ip/path/to/endpoint
            -   ``payload``: Optional HTTP payload

        ### Properties written:
            -   ``response_current``: raw simulated response
            -   ``result_current``: result from self._handle_response() method
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
        self.response_current["CHECK_MODE"] = True
        self.response_current["DATA"] = "[simulated-check-mode-response:Success]"
        self.result_current = self._handle_response(
            copy.deepcopy(self.response_current)
        )

        self.response = copy.deepcopy(self.response_current)
        self.result = copy.deepcopy(self.result_current)

    def commit_normal_mode(self):
        """
        Call dcnm_send() with retries until successful response or timeout is exceeded.

        ### Raises
            -   AnsibleModule.fail_json() if the response is not a dict
        ### Properties read
            -   ``send_interval``: interval between retries (set in ImageUpgradeCommon)
            -   ``timeout``: timeout in seconds (set in ImageUpgradeCommon)
            -   ``verb``: HTTP verb e.g. GET, POST, PUT, DELETE
            -   ``path``: HTTP path e.g. http://controller_ip/path/to/endpoint
            -   ``payload`` Optional HTTP payload

        ## Properties written
            -   ``response``: raw response from the controller
            -   ``result``: result from self._handle_response() method
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        self._verify_commit_parameters()
        try:
            timeout = self.timeout
        except AttributeError:
            timeout = 300

        success = False
        msg = f"{caller}: Entering commit loop. "
        msg += f"timeout: {timeout}, unit_test: {self.unit_test}."
        self.log.debug(msg)

        self.sender.path = self.path
        self.sender.verb = self.verb
        if self.payload is not None:
            self.sender.payload = self.payload
        while timeout > 0 and success is False:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}.  "
            msg += f"Calling sender.commit(): verb {self.verb}, path {self.path}"

            self.sender.commit()

            self.response_current = self.sender.response
            self.result_current = self._handle_response(self.response_current)

            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}.  "
            msg += f"result_current: {json.dumps(self.result_current, indent=4, sort_keys=True)}."
            self.log.debug(msg)

            success = self.result_current["success"]
            if success is False and self.unit_test is False:
                sleep(self.send_interval)
            timeout -= self.send_interval

            self.response_current = self._strip_invalid_json_from_response_data(
                self.response_current
            )
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}.  "
            msg += "response_current: "
            msg += f"{json.dumps(self.response_current, indent=4, sort_keys=True)}."
            self.log.debug(msg)

        self.response = copy.deepcopy(self.response_current)
        self.result = copy.deepcopy(self.result_current)

    def _strip_invalid_json_from_response_data(self, response):
        """
        Strip "Invalid JSON response:" from response["DATA"] if present

        This just clutters up the output and is not useful to the user.
        """
        if "DATA" not in response:
            return response
        if not isinstance(response["DATA"], str):
            return response
        response["DATA"] = re.sub(r"Invalid JSON response:\s*", "", response["DATA"])
        return response

    def _handle_response(self, response):
        """
        ### Summary
        Call the appropriate handler for response based on verb

        ### Raises
        -   ``ValueError`` if verb is not a valid verb

        ### Valid verbs
        -   GET, POST, PUT, DELETE
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
        raise ValueError(msg)

    def _handle_get_response(self, response):
        """
        ### Summary
        Handle GET responses from the controller.

        ### Caller
        ``self._handle_response()``

        ### Returns
        ``dict`` with the following keys:
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
        ### Summary
        Handle POST, PUT responses from the controller.

        ### Caller
        ``self.self._handle_response()``


        ### Returns
        ``dict`` with the following keys:
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
        ### Summary
        Determines if dcnm_send should be called.

        ### Raises
        -   ``TypeError`` if value is not a ``bool``

        ### Default
        ``False``

        -   If ``False``, dcnm_send is called. Real controller responses
            are returned by RestSend()
        -   If ``True``, dcnm_send is not called. Simulated controller
            responses are returned by RestSend()

        ### Discussion
        We want to be able to read data from the controller for read-only
        operations (i.e. to set check_mode to False temporarily, even when
        the user has set check_mode to True).  For example, SwitchIssuDetails
        is a read-only operation, and we want to be able to read this data to
        provide a real controller response to stage, validate, and upgrade
        tasks.
        """
        return self.properties.get("check_mode")

    @check_mode.setter
    def check_mode(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a bool(). Got {value}."
            raise TypeError(msg)
        self.properties["check_mode"] = value

    @property
    def failed_result(self):
        """
        Return a result for a failed task with no changes
        """
        return Results().failed_result

    @property
    def path(self):
        """
        Endpoint path for the REST request.

        ### Raises
        None

        ### Example
        ``/appcenter/cisco/ndfc/api/v1/...etc...``
        """
        return self.properties.get("path")

    @path.setter
    def path(self, value):
        self.properties["path"] = value

    @property
    def payload(self):
        """
        Return the payload to send to the controller

        ### Raises
        None
        """
        return self.properties["payload"]

    @payload.setter
    def payload(self, value):
        self.properties["payload"] = value

    @property
    def response_current(self):
        """
        ### Summary
        Return the current response from the controller
        as a ``dict``. ``commit()`` must be called first.

        ### Raises
        -   setter: ``TypeError`` if value is not a ``dict``

        ### getter
        Return a copy of ``response_current``

        ### setter
        Set ``response_current``
        """
        return copy.deepcopy(self.properties.get("response_current"))

    @response_current.setter
    def response_current(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.response_current must be a dict. "
            msg += f"Got type {type(value).__name__}, "
            msg += f"Value: {value}."
            raise TypeError(msg)
        self.properties["response_current"] = value

    @property
    def response(self):
        """
        ### Summary
        The aggregated list of responses from the controller.

        ``commit()`` must be called first.

        ### Raises
        -   setter: ``TypeError`` if value is not a ``dict``

        ### getter
        Return a copy of ``response``

        ### setter
        Append value to ``response``
        """
        return copy.deepcopy(self.properties.get("response"))

    @response.setter
    def response(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.response must be a dict. "
            msg += f"Got type {type(value).__name__}, "
            msg += f"Value: {value}."
            raise TypeError(msg)
        self.properties["response"].append(value)

    @property
    def result(self):
        """
        ### Summary
        The aggregated list of results from the controller.

        ``commit()`` must be called first.

        ### Raises
        -   setter: ``TypeError`` if value is not a ``dict``

        ### getter
        Return a copy of ``result``

        ### setter
        Append value to ``result``
        """
        return copy.deepcopy(self.properties.get("result"))

    @result.setter
    def result(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.result must be a dict. "
            msg += f"Got {value}."
            raise TypeError(msg)
        self.properties["result"].append(value)

    @property
    def result_current(self):
        """
        ### Summary
        The current result from the controller

        ``commit()`` must be called first.

        This is a dict containing the current result.

        ### Raises
        -   setter: ``TypeError`` if value is not a ``dict``

        ### getter
        Return a copy of ``current_result``

        ### setter
        Set ``current_result``
        """
        return copy.deepcopy(self.properties.get("result_current"))

    @result_current.setter
    def result_current(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.result_current must be a dict. "
            msg += f"Got {value}."
            raise TypeError(msg)
        self.properties["result_current"] = value

    @property
    def send_interval(self):
        """
        ### Summary
        Send interval, in seconds, for retrying responses from the controller.

        ### Valid values
        ``int``
        ### Default
        ``5``

        ### Raises
        -   setter: ``TypeError`` if value is not an ``int``

        ### getter
        Returns ``send_interval``

        ### setter
        Sets ``send_interval``
        """
        return self.properties.get("send_interval")

    @send_interval.setter
    def send_interval(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, int):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be an int(). Got {value}."
            raise TypeError(msg)
        self.properties["send_interval"] = value

    @property
    def sender(self):
        """
        A class implementing functionality to send requests to the controller.

        The class must implement the following:

        1. Class().class_name: str: property
            -   Returns the name of the class
            -   The class name must be "Sender"
        2. Class().verb: str: property setter
            -   Set the HTTP verb to use in the request.
            -   One of {"GET", "POST", "PUT", "DELETE"}
        3. Class().path: str: property setter
            -   Set the path to the controller endpoint.
        4. Class().payload: dict: property
            -   Set the payload to send to the controller.
            -   Must be Optional
        5. Class().commit(): method
            -   Initiate the request to the controller.
        6. Class().response: dict: property
            -   Return the response from the controller.

        ### Raises
        -   ``TypeError`` if value is not an instance of ``Sender``
        """
        return self.properties.get("sender")

    @sender.setter
    def sender(self, value):
        method_name = inspect.stack()[0][3]
        _class_have = None
        _class_need = "Sender"
        msg = f"ZZZ: {self.class_name}.{method_name}: "
        msg += f"Entered with value: {value}."
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f"Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self.properties["sender"] = value

    @property
    def timeout(self):
        """
        ### Summary
        Timeout, in seconds, for retrieving responses from the controller.

        ### Raises
        -   setter: ``TypeError`` if value is not an ``int``

        ### Valid values
        ``int``

        ### Default
        ``300``

        ### getter
        Returns ``timeout``

        ### setter
        Sets ``timeout``
        """
        return self.properties.get("timeout")

    @timeout.setter
    def timeout(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, int):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be an int(). Got {value}."
            raise TypeError(msg)
        self.properties["timeout"] = value

    @property
    def unit_test(self):
        """
        ### Summary
        Is RestSend being called from a unit test.
        Set this to True in unit tests to speed the test up.

        ### Raises
        -   setter: ``TypeError`` if value is not a ``bool``

        ### Default
        ``False``

        ### getter
        Returns ``unit_test``

        ### setter
        Sets ``unit_test``
        """
        return self.properties.get("unit_test")

    @unit_test.setter
    def unit_test(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a bool(). Got {value}."
            raise TypeError(msg)
        self.properties["unit_test"] = value

    @property
    def verb(self):
        """
        Verb for the REST request.

        ### Raises
        -   setter: ``ValueError`` if value is not a valid verb.

        ### Valid verbs
        ``GET``, ``POST``, ``PUT``, ``DELETE``
        """
        return self.properties.get("verb")

    @verb.setter
    def verb(self, value):
        method_name = inspect.stack()[0][3]
        if value not in self._valid_verbs:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be one of {sorted(self._valid_verbs)}. "
            msg += f"Got {value}."
            raise ValueError(msg)
        self.properties["verb"] = value
