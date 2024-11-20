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

# Required for class decorators
# pylint: disable=no-member

import inspect
import logging

from ..api.login import EpLogin
from ..conversion import ConversionUtils
from ..properties import Properties


@Properties.add_rest_send
@Properties.add_results
class EppLogin:
    """
    ### Summary
    Login to Nexus Dashboard

    ### Raises
    None

    ### Data Structure
    ```json
    {
        "domain": "local",
        "userName": "admin",
        "userPasswd": "password"
    }
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.action = "login"
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED EppLogin()"
        self.log.debug(msg)

        self.data = {}
        self.conversion = ConversionUtils()
        self.ep_login = EpLogin()

        self._domain = None
        self._password = None
        self._rest_send = None
        self._results = None
        self._result_code = None
        self._result_message = None
        self._username = None

    def register_result(self):
        """
        ### Summary
        Update the results object with the current state of the endpoint
        and register the result.

        ### Raises
        -   ``ValueError``if:
                -    ``Results()`` raises ``TypeError``
        """
        method_name = inspect.stack()[0][3]
        try:
            self.results.action = self.action
            self.results.response_current = self.rest_send.response_current
            self.results.result_current = self.rest_send.result_current
            if self.results.response_current.get("RETURN_CODE") in [200, 400]:
                self.results.failed = False
            else:
                self.results.failed = True
            # endpoint never changes the controller state
            self.results.changed = False
            self.results.register_task_result()
        except TypeError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Failed to register result. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def validate_commit_parameters(self) -> None:
        """
        ### Summary
        Validate that mandatory parameters are set before calling refresh().

        ### Raises
        -   ``ValueError``if:
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
        """
        method_name = inspect.stack()[0][3]
        if self.domain is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.domain must be set before calling "
            msg += f"{self.class_name}.commit()."
            raise ValueError(msg)
        if self.password is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.password must be set before calling "
            msg += f"{self.class_name}.commit()."
            raise ValueError(msg)
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.rest_send must be set before calling "
            msg += f"{self.class_name}.commit()."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.results must be set before calling "
            msg += f"{self.class_name}.commit()."
            raise ValueError(msg)
        if self.username is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.username must be set before calling "
            msg += f"{self.class_name}.commit()."
            raise ValueError(msg)

    @property
    def domain(self):
        return self._domain

    @domain.setter
    def domain(self, value):
        self._domain = value

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = value

    @property
    def result_code(self):
        return self._result_code

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = value

    def commit(self):
        """
        ### Summary
        Call the controller endpoint, refresh the endpoint response, and
        populate self.data with the results.

        ### Raises
        -   ``ValueError`` if:
                -   ``validate_commit_parameters()`` raises ``ValueError``.
                -   ``RestSend`` raises ``TypeError`` or ``ValueError``.
                -   ``register_result()`` raises ``ValueError``.

        ### Notes
        -   ``self.data`` is a dictionary of endpoint response elements, keyed on
            fabric name.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            self.validate_commit_parameters()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.rest_send.path = self.ep_login.path
            self.rest_send.verb = self.ep_login.verb

            # We always want to login to the controller,
            # regardless of the current value of check_mode.
            # We save the current check_mode and timeout settings, set
            # rest_send.check_mode to False so the request will be sent
            # to the controller, and then restore the original settings.

            payload = dict()
            payload["userName"] = self.username
            payload["userPasswd"] = self.password
            payload["domain"] = self.domain

            self.rest_send.save_settings()
            self.rest_send.payload = payload
            self.rest_send.check_mode = False
            self.rest_send.timeout = 1
            self.rest_send.commit()
            self.rest_send.restore_settings()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

        self.data = {}
        response_data = self.rest_send.response_current.get("DATA")
        self._result_code = self.rest_send.response_current.get("RETURN_CODE")
        if self.result_code in [400, 401]:
            # TODO: Verify 400 response
            self._result_message = response_data.get("message")
            msg = f"Received result_code {self.result_code}. "
            msg += f"Message: {self._result_message}"
            self.log.debug(msg)
            self.data = {}
        elif self.result_code == 200:
            self.data = self.rest_send.response_current.get("DATA", {})
        else:
            message = self.rest_send.response_current.get("MESSAGE")
            msg = f"Got RETURN_CODE {self.result_code} with message {message}"
            raise ValueError(msg)

        msg = f"{self.class_name}.{method_name}: calling self.rest_send.commit() DONE"
        self.log.debug(msg)
