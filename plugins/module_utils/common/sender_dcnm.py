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

from ..network.dcnm.dcnm import dcnm_send


class Sender:
    """
    ### Summary
    An injected dependency for ``RestSend`` which implements the
    ``sender`` interface.  Responses are retrieved using dcnm_send.

    ### Raises
    -   ``ValueError`` if:
            -   ``ansible_module`` is not set.
            -   ``path`` is not set.
            -   ``verb`` is not set.
    -   ``TypeError`` if:
            -   ``ansible_module`` is not an instance of AnsibleModule.
            -   ``payload`` is not a ``dict``.
            -   ``response`` is not a ``dict``.

    ### Usage
    ``ansible_module`` is an instance of ``AnsibleModule``.

    ```python
    sender = Sender()
    try:
        sender.ansible_module = ansible_module
        rest_send = RestSend()
        rest_send.sender = sender
    except (TypeError, ValueError) as error:
        handle_error(error)
    # etc...
    # See rest_send_v2.py for RestSend() usage.
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self._implements = "sender_v1"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.params = None
        self._ansible_module = None
        self._dcnm_send = dcnm_send
        self._path = None
        self._payload = None
        self._response = None
        self._verb = None

        self._valid_verbs = {"GET", "POST", "PUT", "DELETE"}

        msg = "ENTERED Sender(): "
        self.log.debug(msg)

    def _verify_commit_parameters(self):
        """
        ### Summary
        Verify that required parameters are set prior to calling ``commit()``

        ### Raises
        -   ``ValueError`` if ``verb`` is not set
        -   ``ValueError`` if ``path`` is not set
        """
        method_name = inspect.stack()[0][3]
        if self.ansible_module is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "ansible_module must be set before calling commit()."
            raise ValueError(msg)
        if self.path is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "path must be set before calling commit()."
            raise ValueError(msg)
        if self.verb is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "verb must be set before calling commit()."
            raise ValueError(msg)

    def commit(self):
        """
        Send the REST request to the controller

        ### Raises
            -   ``ValueError`` if:
                    -   ``ansible_module`` is not set.
                    -   ``path`` is not set.
                    -   ``verb`` is not set.

        ### Properties read
            -   ``verb``: HTTP verb e.g. GET, POST, PUT, DELETE
            -   ``path``: HTTP path e.g. http://controller_ip/path/to/endpoint
            -   ``payload`` Optional HTTP payload

        ## Properties written
            -   ``response``: raw response from the controller
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        try:
            self._verify_commit_parameters()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Not all mandatory parameters are set. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error
        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}.  "
        msg += f"Calling dcnm_send: verb {self.verb}, path {self.path}"
        if self.payload is None:
            self.log.debug(msg)
            response = self._dcnm_send(self.ansible_module, self.verb, self.path)
        else:
            msg += ", payload: "
            msg += f"{json.dumps(self.payload, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            response = self._dcnm_send(
                self.ansible_module,
                self.verb,
                self.path,
                data=json.dumps(self.payload),
            )
        self.response = copy.deepcopy(response)

    @property
    def ansible_module(self):
        """
        An AnsibleModule instance.

        ### Raises
        -   ``TypeError`` if value is not an instance of AnsibleModule.
        """
        return self._ansible_module

    @ansible_module.setter
    def ansible_module(self, value):
        method_name = inspect.stack()[0][3]
        try:
            self.params = value.params
        except AttributeError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be an instance of AnsibleModule. "
            msg += f"Got type {type(value).__name__}, value {value}. "
            msg += f"Error detail: {error}."
            raise TypeError(msg) from error
        self._ansible_module = value

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
        -   ``TypeError`` if value is not a ``dict``.
        """
        return self._payload

    @payload.setter
    def payload(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a dict. "
            msg += f"Got type {type(value).__name__}, "
            msg += f"value {value}."
            raise TypeError(msg)
        self._payload = value

    @property
    def response(self):
        """
        ### Summary
        The response from the controller.

        ### Raises
        -   ``TypeError`` if value is not a ``dict``.

        -   getter: Return a copy of ``response``
        -   setter: Set ``response``
        """
        return copy.deepcopy(self._response)

    @response.setter
    def response(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be a dict. "
            msg += f"Got type {type(value).__name__}, "
            msg += f"value {value}."
            raise TypeError(msg)
        self._response = value

    @property
    def verb(self):
        """
        Verb for the REST request.

        ### Raises
        -   ``ValueError`` if value is not a valid verb.

        ### Valid verbs
        ``GET``, ``POST``, ``PUT``, ``DELETE``
        """
        return self._verb

    @verb.setter
    def verb(self, value):
        method_name = inspect.stack()[0][3]
        if value not in self._valid_verbs:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{method_name} must be one of {sorted(self._valid_verbs)}. "
            msg += f"Got {value}."
            raise ValueError(msg)
        self._verb = value
