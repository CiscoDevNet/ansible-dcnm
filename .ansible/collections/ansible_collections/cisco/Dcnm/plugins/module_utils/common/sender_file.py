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
import logging


class Sender:
    """
    ### Summary
    An injected dependency for ``RestSend`` which implements the
    ``sender`` interface.  Responses are read from JSON files.

    ### Raises
    -   ``ValueError`` if:
            -   ``gen`` is not set.
    -   ``TypeError`` if:
            -   ``gen`` is not an instance of ResponseGenerator()

    ### Usage
    ``responses()`` is a coroutine that yields controller responses.
    In the example below, it yields to dictionaries.  However, in
    practice, it would yield responses read from JSON files.

    ```python
    def responses():
        yield {"key1": "value1"}
        yield {"key2": "value2"}

    sender = Sender()
    sender.gen = ResponseGenerator(responses())

    try:
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

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._ansible_module = None
        self._gen = None
        self._implements = "sender_v1"
        self._path = None
        self._payload = None
        self._response = None
        self._verb = None

        self._raise_method = None
        self._raise_exception = None

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
        if self.gen is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "gen must be set before calling commit()."
            raise ValueError(msg)

    def commit(self):
        """
        ### Summary
        Dummy commit

        ### Raises
        -   ``ValueError`` if ``gen`` is not set.
        -   ``self.raise_exception`` if set and
            ``self.raise_method`` == "commit"
        """
        method_name = inspect.stack()[0][3]

        if self.raise_method == method_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Simulated {self.raise_exception.__name__}."
            raise self.raise_exception(msg)  # pylint: disable=not-callable

        try:
            self._verify_commit_parameters()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Not all mandatory parameters are set. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller {caller}"
        self.log.debug(msg)

    @property
    def ansible_module(self):
        """
        ### Summary
        Dummy ansible_module
        """
        return self._ansible_module

    @ansible_module.setter
    def ansible_module(self, value):
        self._ansible_module = value

    @property
    def gen(self):
        """
        ### Summary
        -   getter: Return the ``ResponseGenerator()`` instance.
        -   setter: Set the ``ResponseGenerator()`` instance that provides
            simulated responses.

        ### Raises
        ``TypeError`` if value is not a class implementing the
        response_generator interface.
        """
        return self._gen

    @gen.setter
    def gen(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "Expected a class implementing the "
        msg += "response_generator interface. "
        msg += f"Got {value}."
        try:
            implements = value.implements
        except AttributeError as error:
            raise TypeError(msg) from error
        if implements != "response_generator":
            raise TypeError(msg)
        self._gen = value

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
        ### Summary
        Dummy path.

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
        ### Summary
        Dummy payload.

        ### Raises
        -   ``TypeError`` if value is not a ``dict``.
        """
        return self._payload

    @payload.setter
    def payload(self, value):
        self._payload = value

    @property
    def raise_exception(self):
        """
        ### Summary
        The exception to raise.

        ### Raises
        -   ``TypeError`` if value is not a subclass of
            ``BaseException``.

        ### Usage
        ```python
        instance = Sender()
        instance.raise_method = "commit"
        instance.raise_exception = ValueError
        instance.commit() # will raise a simulated ValueError
        ```

        ### NOTES
        -   No error checking is done on the input to this property.
        """
        return self._raise_exception

    @raise_exception.setter
    def raise_exception(self, value):
        self._raise_exception = value

    @property
    def raise_method(self):
        """
        ### Summary
        The method in which to raise ``raise_exception``.

        ### Raises
        None

        ### Usage
        See ``raise_exception``.
        """
        return self._raise_method

    @raise_method.setter
    def raise_method(self, value):
        self._raise_method = value

    @property
    def response(self):
        """
        ### Summary
        The simulated response from a file.

        ### Raises
        None

        -   getter: Return a copy of ``response``
        -   setter: Set ``response``
        """
        return self.gen.next

    @property
    def verb(self):
        """
        ### Summary
        Dummy Verb.

        ### Raises
        None
        """
        return self._verb

    @verb.setter
    def verb(self, value):
        self._verb = value
