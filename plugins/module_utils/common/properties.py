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
            msg += f"Error detail: {error}."
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
