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
import json
import logging
import re

from ..common.conversion import ConversionUtils


class ParamInfo:
    """
    Given a parameter, return a python dict containing parameter info.
    Parameter info is culled from the provided template.

    Raise ``ValueError`` during refresh() if:
    - template is not set
    - template has no parameters
    - template[parameters] is not a list

    Raise ``KeyError`` during parameter() call if:
    - parameter is not found

    Usage:

    ```python
    instance = ParamInfo()
    instance.template = template

    try:
        instance.refresh()
    except ValueError as error:
        print(error)
        exit(1)

    try:
        my_parameter_info = instance.parameter("my_parameter")
    except KeyError as error:
        print(error)
        exit(1)

    parameter_type = my_parameter_info["type"] # python type: bool, str, int, dict, set, list, None
    parameter_choices = my_parameter_info["choices"] # python list, or None
    parameter_min = my_parameter_info["min"] # int, or None
    parameter_max = my_parameter_info["max"] # int, or None
    parameter_default = my_parameter_info["default"] # Any, or None
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.conversion = ConversionUtils()

        self.info = {}
        self._init_properties()

    def _init_properties(self):
        """
        Initialize the properties dict containing properties used by the class.
        """
        self.properties = {}
        self.properties["template"] = None

    @property
    def template(self):
        """
        - getter : return the template used to cull parameter info.
        - setter : set the template used to cull parameter info.
        - setter : raise ``TypeError`` if template is not a dict
        """
        return self.properties["template"]

    @template.setter
    def template(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "template must be a dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        self.properties["template"] = value

    def refresh(self):
        """
        # Refresh the parameter information based on the template

        - raise ValueError if template is not set
        - raise ValueError if template has no parameters key
        - raise ValueError if template[parameters] is not a list
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        if self.template is None:
            msg += "Call instance.template before calling instance.refresh()."
            raise ValueError(msg)
        if self.template.get("parameters") is None:
            msg += "No parameters in template."
            raise ValueError(msg)
        if isinstance(self.template["parameters"], list) is False:
            msg += "template['parameters'] is not a list."
            raise ValueError(msg)

        self._build_info()

    def parameter(self, value):
        """
        -   Return parameter information based on the template.
        -   Raise ``KeyError`` if parameter is not found

        Usage:

        ```python
        try:
            parameter_info = instance.parameter("my_parameter")
        except KeyError as error:
            print(error)
            exit(1)
        ```

        ``parameter_info`` is returned as a python dict:

        ```json
        {
            "type": str,
            "choices": ["Ingress", "Multicast"],
            "min": None,
            "max": None,
            "default": "Multicast"
        }
        ```

        - type: (``bool, str, int, dict, set, list, None``),
        - choices: (``list``, or ``None``)
        - min: (``int``, or ``None``)
        - max: (``int``, or ``None``)
        - default: (``str``, ``int``, etc, or ``None``)

        """
        method_name = inspect.stack()[0][3]
        try:
            return self.info[value]
        except KeyError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Parameter {value} not found in fabric template. "
            msg += f"This likely means that the parameter {value} is not "
            msg += "appropriate for the fabric type."
            raise KeyError(msg) from error

    def _get_choices(self, parameter):
        """
        -   Return a python list of valid parameter choices, if specified
            in the template.
        -   Return None otherwise.

        Example conversions:

        ```
        "\\"Multicast,Ingress\\"" -> ["Ingress", "Multicast"]
        "\\"1,2\\"" -> [1,2]
        "\\"true,false\\"" -> [False, True]
        ```

        """
        parameter_type = self._get_type(parameter)
        if parameter_type == "boolean":
            return [False, True]
        choices = parameter.get("annotations", {}).get("Enum", None)
        if choices is None:
            return None
        choices = re.sub(r"\"", "", choices)
        choices = choices.split(",")
        choices = [self.conversion.make_int(choice) for choice in choices]
        return sorted(choices)

    def _get_default(self, parameter):
        """
        - Return the parameter's default value, if specified in the template.
        - Return None otherwise.

        NOTES:
        -  The default value can be in two places. Check both places.:
            - metaProperties.defaultValue
            - defaultValue
        -  Conversion to int must preceed conversion to boolean.
        """
        value = parameter.get("metaProperties", {}).get("defaultValue", None)
        if value is None:
            value = parameter.get("defaultValue", None)
        if value is None:
            return None
        value = re.sub('"', "", value)
        value_type = self._get_type(parameter)
        if value_type == "string":
            # This prevents things like MPLS_ISIS_AREA_NUM
            # from being converted from "0001" to 1
            return value
        if value_type == "integer":
            value = self.conversion.make_int(value)
        if isinstance(value, int):
            return value
        return self.conversion.make_boolean(value)

    def _get_internal(self, parameter):
        """
        -   Return the parameter's annotations.IsInternal value,
            if specified in the template.
        -   Return None otherwise.
        """
        value = parameter.get("annotations", {}).get("IsInternal", None)
        if value is None:
            return None
        return self.conversion.make_boolean(value)

    def _get_min(self, parameter):
        """
        - Return the parameter's minimum value, if specified in the template.
        - Return None otherwise.
        """
        value = parameter.get("metaProperties", {}).get("min", None)
        if value is None:
            return None
        return self.conversion.make_int(value)

    def _get_max(self, parameter):
        """
        - Return the parameter's maximum value, if specified in the template.
        - Return None otherwise.
        """
        value = parameter.get("metaProperties", {}).get("max", None)
        if value is None:
            return None
        return self.conversion.make_int(value)

    def _get_param_name(self, parameter):
        """
        -   Return the ``name`` key from the parameter dict.
        -   Raise ``KeyError`` if ``name`` key is missing
        """
        method_name = inspect.stack()[0][3]

        param_name = parameter.get("name", None)
        if param_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Parameter is missing name key: "
            msg += f"parameter={parameter}"
            raise KeyError(msg)
        return param_name

    def _get_type(self, parameter):
        """
        - Return the parameter's type, if specified in the template.
        - Return None otherwise.
        """
        return parameter.get("parameterType", None)

    def _build_info(self) -> None:
        """
        # Build a ``dict`` of parameter information, keyed on parameter name.

        ## Parameter information is culled from the template.

        - choices: (``list``, or ``None``)
        - default: (``str``, ``int``, etc, or ``None``)
        - internal: (``bool``, or ``None``)
        - max: (``int``, or ``None``)
        - min: (``int``, or ``None``)
        - type:
            -   boolean
            -   enum
            -   integer
            -   integerRange
            -   interface
            -   interfaceRange
            -   ipAddressList
            -   ipV4Address
            -   ipV4AddressWithSubnet
            -   ipV6AddressWithSubnet
            -   macAddress
            -   string
            -   string[]
            -   structureArray
            -   None

        Example:

        ```python
        self.info[parameter] = {
            "choices": ["Ingress", "Multicast"],
            "default": "Multicast",
            "internal": False,
            "max": None,
            "min": None,
            "type": "string"
        }
        ```

        """
        method_name = inspect.stack()[0][3]
        self.info = {}
        for parameter in self.template.get("parameters", []):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"parameter: {json.dumps(parameter, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            param_name = self._get_param_name(parameter)
            if param_name not in self.info:
                self.info[param_name] = {}
            self.info[param_name]["choices"] = self._get_choices(parameter)
            self.info[param_name]["default"] = self._get_default(parameter)
            self.info[param_name]["max"] = self._get_max(parameter)
            self.info[param_name]["min"] = self._get_min(parameter)
            self.info[param_name]["type"] = self._get_type(parameter)
            self.info[param_name]["internal"] = self._get_internal(parameter)
            self.info[param_name]["type"] = self._get_type(parameter)
