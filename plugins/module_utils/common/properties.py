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


class Properties:
    """
    ### Summary
    Commonly-used properties and class decorator wrapper methods.

    ### Raises
    The following properties raise a ``TypeError`` if the value is not an
    instance of the expected class:
    -   ``rest_send``
    -   ``results``

    ### Properties
    -   ``rest_send``: Set and return nn instance of the ``RestSend`` class.
    -   ``results``: Set and return an instance of the ``Results`` class.
    """
    @property
    def params(self):
        """
        ### Summary
        Expects value to be a dictionary containing, at mimimum, the keys
        ``state`` and ``check_mode``.

        ### Raises
        -   setter: ``ValueError`` if value is not a dict.
        -   setter: ``ValueError`` if value["state"] is missing.
        -   setter: ``ValueError`` if value["state"] is not a valid state.
        -   setter: ``ValueError`` if value["check_mode"] is missing.

        ### Valid values

        #### ``state``
        -   deleted
        -   merged
        -   overridden
        -   query
        -   replaced

        #### ``check_mode``
        -   ``False`` - The Ansible module should make requested changes.
        -   ``True``  - The Ansible module should not make requested changed
            and should only report what changes it would make if ``check_mode``
            was ``False``.

        ### Details
        -   Example Valid params:
                -   ``{"state": "deleted", "check_mode": False}``
                -   ``{"state": "merged", "check_mode": False}``
                -   ``{"state": "overridden", "check_mode": False}``
                -   ``{"state": "query", "check_mode": False}``
                -   ``{"state": "replaced", "check_mode": False}``
        -   getter: return the params
        -   setter: set the params
        """
        return self._params

    @params.setter
    def params(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "params must be a dictionary. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        if value.get("state", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params.state is required but missing."
            raise ValueError(msg)
        if value.get("check_mode", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params.check_mode is required but missing."
            raise ValueError(msg)
        self._params = value

    @property
    def rest_send(self):
        """
        ### Summary
        An instance of the RestSend class.

        ### Raises
        -   setter: ``TypeError`` if the value is not an instance of RestSend.

        ### getter
        Return an instance of the RestSend class.

        ### setter
        Set an instance of the RestSend class.
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value):
        method_name = inspect.stack()[0][3]
        _class_have = None
        _class_need = "RestSend"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._rest_send = value

    @property
    def results(self):
        """
        ### Summary
        An instance of the Results class.

        ### Raises
        -   setter: ``TypeError`` if the value is not an instance of Results.

        ### getter
        Return an instance of the Results class.

        ### setter
        Set an instance of the Results class.
        """
        return self._results

    @results.setter
    def results(self, value):
        method_name = inspect.stack()[0][3]
        _class_have = None
        _class_need = "Results"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._results = value

    def add_params(self):
        """
        ### Summary
        Class decorator method to set the ``params`` property.
        """
        self.params = Properties.params
        return self

    def add_rest_send(self):
        """
        ### Summary
        Class decorator method to set the ``rest_send`` property.
        """
        self.rest_send = Properties.rest_send
        return self

    def add_results(self):
        """
        ### Summary
        Class decorator method to set the ``results`` property.
        """
        self.results = Properties.results
        return self
