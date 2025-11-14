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
from .results import Results


class RestSend:
    """
    ### Summary
    -   Send REST requests to the controller with retries.
    -   Accepts a ``Sender()`` class that implements the sender interface.
            -   The sender interface is defined in
                ``module_utils/common/sender_dcnm.py``
    -   Accepts a ``ResponseHandler()`` class that implements the response
        handler interface.
            -   The response handler interface is defined in
                ``module_utils/common/response_handler.py``

    ### Raises
    -   ``ValueError`` if:
            -   self._verify_commit_parameters() raises
                ``ValueError``
            -   ResponseHandler() raises ``TypeError`` or ``ValueError``
            -   Sender().commit() raises ``ValueError``
            -   ``verb`` is not a valid verb (GET, POST, PUT, DELETE)
    -  ``TypeError`` if:
            -   ``check_mode`` is not a ``bool``
            -   ``path`` is not a ``str``
            -   ``payload`` is not a ``dict``
            -   ``response`` is not a ``dict``
            -   ``response_current`` is not a ``dict``
            -   ``response_handler`` is not an instance of
                ``ResponseHandler()``
            -   ``result`` is not a ``dict``
            -   ``result_current`` is not a ``dict``
            -   ``send_interval`` is not an ``int``
            -   ``sender`` is not an instance of ``Sender()``
            -   ``timeout`` is not an ``int``
            -   ``unit_test`` is not a ``bool``

    ### Usage discussion
    -   A Sender() class is used in the usage example below that requires an
        instance of ``AnsibleModule``, and uses ``dcnm_send()`` to send
        requests to the controller.
        -   See ``module_utils/common/sender_dcnm.py`` for details about
            implementing ``Sender()`` classes.
    -   A ResponseHandler() class is used in the usage example below that
        abstracts controller response handling.  It accepts a controller
        response dict and returns a result dict.
        -   See ``module_utils/common/response_handler.py`` for details
            about implementing ``ResponseHandler()`` classes.

    ### Usage example
    ```python
    params = {"check_mode": False, "state": "merged"}
    sender = Sender() # class that implements the sender interface
    sender.ansible_module = ansible_module

    try:
        rest_send = RestSend(params)
        rest_send.sender = sender
        rest_send.response_handler = ResponseHandler()
        rest_send.unit_test = True # optional, use in unit tests for speed
        rest_send.path = "/rest/top-down/fabrics"
        rest_send.verb = "GET"
        rest_send.payload = my_payload # optional
        rest_send.save_settings() # save current check_mode and timeout
        rest_send.timeout = 300 # optional
        rest_send.check_mode = True
        # Do things with rest_send...
        rest_send.commit()
        rest_send.restore_settings() # restore check_mode and timeout
    except (TypeError, ValueError) as error:
        # Handle error

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

        self._implements = "rest_send_v2"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.params = params
        msg = "ENTERED RestSend(): "
        msg += f"params: {self.params}"
        self.log.debug(msg)

        self._check_mode = False
        self._path = None
        self._payload = None
        self._response = []
        self._response_current = {}
        self._response_handler = None
        self._result = []
        self._result_current = {}
        self._send_interval = 5
        self._sender = None
        self._timeout = 300
        self._unit_test = False
        self._verb = None

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
                -   ``response_handler`` is not set
                -   ``sender`` is not set
                -   ``verb`` is not set
        """
        if self.path is None:
            msg = f"{self.class_name}._verify_commit_parameters: "
            msg += "path must be set before calling commit()."
            raise ValueError(msg)
        if self.response_handler is None:
            msg = f"{self.class_name}._verify_commit_parameters: "
            msg += "response_handler must be set before calling commit()."
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

        ### NOTES
        -   ``check_mode`` is not saved if it has not yet been initialized.
        -   ``timeout`` is not saved if it has not yet been initialized.
        """
        if self.check_mode is not None:
            self.saved_check_mode = self.check_mode
        if self.timeout is not None:
            self.saved_timeout = self.timeout

    def commit(self):
        """
        ### Summary
        Send the REST request to the controller

        ### Raises
        -   ``ValueError`` if:
                -   RestSend()._verify_commit_parameters() raises
                    ``ValueError``
                -   ResponseHandler() raises ``TypeError`` or ``ValueError``
                -   Sender().commit() raises ``ValueError``
                -   ``verb`` is not a valid verb (GET, POST, PUT, DELETE)
        -  ``TypeError`` if:
                -   ``check_mode`` is not a ``bool``
                -   ``path`` is not a ``str``
                -   ``payload`` is not a ``dict``
                -   ``response`` is not a ``dict``
                -   ``response_current`` is not a ``dict``
                -   ``response_handler`` is not an instance of
                    ``ResponseHandler()``
                -   ``result`` is not a ``dict``
                -   ``result_current`` is not a ``dict``
                -   ``send_interval`` is not an ``int``
                -   ``sender`` is not an instance of ``Sender()``
                -   ``timeout`` is not an ``int``
                -   ``unit_test`` is not a ``bool``

        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"verb: {self.verb}, "
        msg += f"path: {self.path}."
        self.log.debug(msg)

        try:
            if self.check_mode is True:
                self.commit_check_mode()
            else:
                self.commit_normal_mode()
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during commit. "
            msg += f"Error details: {error}"
            raise ValueError(msg) from error

    def commit_check_mode(self):
        """
        ### Summary
        Simulate a controller request for check_mode.

        ### Raises
        -   ``ValueError`` if:
            -   ResponseHandler() raises ``TypeError`` or ``ValueError``
            -   self.response_current raises ``TypeError``
            -   self.result_current raises ``TypeError``
            -   self.response raises ``TypeError``
            -   self.result raises ``TypeError``


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

        response_current = {}
        response_current["RETURN_CODE"] = 200
        response_current["METHOD"] = self.verb
        response_current["REQUEST_PATH"] = self.path
        response_current["MESSAGE"] = "OK"
        response_current["CHECK_MODE"] = True
        response_current["DATA"] = "[simulated-check-mode-response:Success]"

        try:
            self.response_current = response_current
            self.response_handler.response = self.response_current
            self.response_handler.verb = self.verb
            self.response_handler.commit()
            self.result_current = self.response_handler.result
            self.response = copy.deepcopy(self.response_current)
            self.result = copy.deepcopy(self.result_current)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error building response/result. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def commit_normal_mode(self):
        """
        Call dcnm_send() with retries until successful response or timeout is exceeded.

        ### Raises
            -   ``ValueError`` if:
                -   HandleResponse() raises ``ValueError``
                -   Sender().commit() raises ``ValueError``
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

        try:
            self._verify_commit_parameters()
        except ValueError as error:
            raise ValueError(error) from error

        timeout = copy.copy(self.timeout)

        msg = f"{caller}: Entering commit loop. "
        msg += f"timeout: {timeout}, unit_test: {self.unit_test}."
        self.log.debug(msg)

        self.sender.path = self.path
        self.sender.verb = self.verb
        if self.payload is not None:
            self.sender.payload = self.payload
        success = False
        while timeout > 0 and success is False:
            timeout -= self.send_interval
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += f"unit_test: {self.unit_test}. "
            msg += f"Subtracted {self.send_interval} from timeout. "
            msg += f"timeout: {timeout}, "
            msg += f"success: {success}."
            self.log.debug(msg)

            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}.  "
            msg += "Calling sender.commit(): "
            msg += f"timeout {timeout}, success {success}, verb {self.verb}, path {self.path}."
            self.log.debug(msg)

            try:
                self.sender.commit()
            except ValueError as error:
                raise ValueError(error) from error

            self.response_current = self.sender.response
            # Handle controller response and derive result
            try:
                self.response_handler.response = self.response_current
                self.response_handler.verb = self.verb
                self.response_handler.commit()
                self.result_current = self.response_handler.result
            except (TypeError, ValueError) as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Error building response/result. "
                msg += f"Error detail: {error}"
                self.log.debug(msg)
                raise ValueError(msg) from error

            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += f"timeout: {timeout}. "
            msg += f"result_current: {json.dumps(self.result_current, indent=4, sort_keys=True)}."
            self.log.debug(msg)

            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += f"timeout: {timeout}. "
            msg += "response_current: "
            msg += f"{json.dumps(self.response_current, indent=4, sort_keys=True)}."
            self.log.debug(msg)

            success = self.result_current["success"]
            if success is False and self.unit_test is False:
                sleep(self.send_interval)

        self.response = copy.deepcopy(self.response_current)
        self.result = copy.deepcopy(self.result_current)
        self._payload = None

    @property
    def check_mode(self):
        """
        ### Summary
        Determines if changes should be made on the controller.

        ### Raises
        -   ``TypeError`` if value is not a ``bool``

        ### Default
        ``False``

        -   If ``False``, write operations, if any, are made on the controller.
        -   If ``True``, write operations are not made on the controller.
            Instead, controller responses for write operations are simulated
            to be successful (200 response code) and these simulated responses
            are returned by RestSend().  Read operations are not affected
            and are sent to the controller and real responses are returned.

        ### Discussion
        We want to be able to read data from the controller for read-only
        operations (i.e. to set check_mode to False temporarily, even when
        the user has set check_mode to True).  For example, SwitchDetails
        is a read-only operation, and we want to be able to read this data to
        provide a real controller response to the user.
        """
        return self._check_mode

    @check_mode.setter
    def check_mode(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a boolean. Got {value}."
            raise TypeError(msg)
        self._check_mode = value

    @property
    def failed_result(self):
        """
        Return a result for a failed task with no changes
        """
        return Results().failed_result

    @property
    def implements(self):
        """
        ### Summary
        The interface implemented by this class.

        ### Raises
        None
        """
        return self._implements

    @property
    def path(self):
        """
        Endpoint path for the REST request.

        ### Raises
        None

        ### Example
        ``/appcenter/cisco/ndfc/api/v1/...etc...``
        """
        return self._path

    @path.setter
    def path(self, value):
        self._path = value

    @property
    def payload(self):
        """
        Return the payload to send to the controller

        ### Raises
        None
        """
        return self._payload

    @payload.setter
    def payload(self, value):
        self._payload = value

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
        return copy.deepcopy(self._response_current)

    @response_current.setter
    def response_current(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a dict. "
            msg += f"Got type {type(value).__name__}, "
            msg += f"Value: {value}."
            raise TypeError(msg)
        self._response_current = value

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
        return copy.deepcopy(self._response)

    @response.setter
    def response(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a dict. "
            msg += f"Got type {type(value).__name__}, "
            msg += f"Value: {value}."
            raise TypeError(msg)
        self._response.append(value)

    @property
    def response_handler(self):
        """
        ### Summary
        A class that implements the response handler interface.  This
        handles responses from the controller and returns results.

        ### Raises
        -   ``TypeError`` if:
                -   ``value`` is not an instance of ``ResponseHandler``

        ### getter
        Return a the ``response_handler`` instance.

        ### setter
        Set the ``response_handler`` instance.

        ### NOTES
        -   See module_utils/common/response_handler.py for details about
            implementing a ``ResponseHandler`` class.
        """
        return self._response_handler

    @response_handler.setter
    def response_handler(self, value):
        method_name = inspect.stack()[0][3]
        _implements_need = "response_handler_v1"
        _implements_have = None
        msg = f"{self.class_name}.{method_name}: "
        msg += f"{method_name} must implement {_implements_need}. "
        msg += f"Got type {type(value).__name__}, "
        msg += f"implementing {_implements_have}. "
        try:
            _implements_have = value.implements
        except AttributeError as error:
            msg += f"Error detail: {error}."
            raise TypeError(msg) from error
        if _implements_have != _implements_need:
            raise TypeError(msg)
        self._response_handler = value

    @property
    def result(self):
        """
        ### Summary
        The aggregated list of results from the controller.

        ``commit()`` must be called first.

        ### Raises
        -   setter: ``TypeError`` if:
                -   value is not a ``dict``.

        ### getter
        Return a copy of ``result``

        ### setter
        Append value to ``result``
        """
        return copy.deepcopy(self._result)

    @result.setter
    def result(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a dict. "
            msg += f"Got type {type(value).__name__}, "
            msg += f"Value: {value}."
            raise TypeError(msg)
        self._result.append(value)

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
        return copy.deepcopy(self._result_current)

    @result_current.setter
    def result_current(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a dict. "
            msg += f"Got {value}."
            raise TypeError(msg)
        self._result_current = value

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
        return self._send_interval

    @send_interval.setter
    def send_interval(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"{method_name} must be an integer. "
        msg += f"Got type {type(value).__name__}, "
        msg += f"value {value}."
        if isinstance(value, bool):
            raise TypeError(msg)
        if not isinstance(value, int):
            raise TypeError(msg)
        self._send_interval = value

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
        return self._sender

    @sender.setter
    def sender(self, value):
        method_name = inspect.stack()[0][3]
        _implements_have = None
        _implements_need = "sender_v1"

        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be a class that implements {_implements_need}. "
        msg += f"Got type {type(value).__name__}, "
        msg += f"value {value}. "
        try:
            _implements_have = value.implements
        except AttributeError as error:
            msg += f"Error detail: {error}."
            raise TypeError(msg) from error
        if _implements_have != _implements_need:
            raise TypeError(msg)
        self._sender = value

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
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"{method_name} must be an integer. "
        msg += f"Got type {type(value).__name__}, "
        msg += f"value {value}."
        if isinstance(value, bool):
            raise TypeError(msg)
        if not isinstance(value, int):
            raise TypeError(msg)
        self._timeout = value

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
        return self._unit_test

    @unit_test.setter
    def unit_test(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a boolean. "
            msg += f"Got type {type(value).__name__}, "
            msg += f"value {value}."
            raise TypeError(msg)
        self._unit_test = value

    @property
    def verb(self):
        """
        Verb for the REST request.

        ### Raises
        -   setter: ``TypeError`` if value is not a string.
        -   setter: ``ValueError`` if value is not a valid verb.

        ### Valid verbs
        ``GET``, ``POST``, ``PUT``, ``DELETE``
        """
        return self._verb

    @verb.setter
    def verb(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"{method_name} must be one of {sorted(self._valid_verbs)}. "
        msg += f"Got {value}."
        if not isinstance(value, str):
            raise TypeError(msg)
        if value not in self._valid_verbs:
            raise ValueError(msg)
        self._verb = value
