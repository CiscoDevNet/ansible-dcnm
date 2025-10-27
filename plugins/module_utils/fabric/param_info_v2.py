# Copyright (c) 2024-2025 Cisco and/or its affiliates.
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
"""
Exposes public class ParamInfo which contains methods and properties for
parsing parameter information from fabric templates.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import inspect
import json
import logging
import re
from typing import Any, Union

from ..common.conversion import ConversionUtils


class ParamInfo:
    """
    # Summary

    Methods and properties for parsing and accessing parameter information
    from fabric templates.

    ## Raises

    `ValueError` during refresh() if:

        - template is not set
        - template has no parameters
        - template[parameters] is not a list

    `ValueError` during property access if:
        - template is not set
        - parameter_name is not set
        - parameter_name is not found in the template

    Usage:

    ```python
    instance = ParamInfo()
    instance.template = template

    try:
        instance.refresh()
    except ValueError as error:
        print(error)
        exit(1)

    for param_name in instance.parameter_names:
        instance.parameter_name = param_name
        print(f"{param_name}.choices: {instance.parameter_choices}")
        print(f"{param_name}.default: {instance.parameter_default}")
        print(f"{param_name}.max: {instance.parameter_max}")
        print(f"{param_name}.min: {instance.parameter_min}")
        print(f"{param_name}.type: {instance.parameter_type}")
    ```

    """

    def __init__(self) -> None:
        self.class_name: str = self.__class__.__name__

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")
        self.conversion: ConversionUtils = ConversionUtils()

        self.info: dict[str, Any] = {}
        self._parameter_name: str = ""
        self._template: dict[str, Any] = {}

    def refresh(self) -> None:
        """
        # Summary

        Refresh the parameter information based on the template

        ## Raises

        `ValueError` if:

            - template is not set
            - template has no parameters key
            - template[parameters] is not a list
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

    def parameter(self, value: str) -> dict[str, Any]:
        """
        # Summary

        Return parameter information from the template for value (parameter name).

        Deprecated: Use properties instead:
            - parameter_choices
            - parameter_default
            - parameter_max
            - parameter_min
            - parameter_type

        ## Raises

        `KeyError` if:
            - parameter is not found

        ## Usage

        ```python
        try:
            parameter_info = instance.parameter("my_parameter")
        except KeyError as error:
            print(error)
            exit(1)
        ```

        ## Returns

        `parameter_info` is returned as a python dict:

        ```json
        {
            "type": str,
            "choices": ["Ingress", "Multicast"],
            "min": None,
            "max": None,
            "default": "Multicast"
        }
        ```

        - type: (`bool, str, int, dict, set, list, None`),
        - choices: (`list`, or `None`)
        - min: (`int`, or `None`)
        - max: (`int`, or `None`)
        - default: (`str`, `int`, etc, or "")

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

    def _get_choices(self, parameter: dict[str, Any]) -> Union[list[Any], None]:
        """
        # Summary

        -   Return a python list of valid parameter choices, if specified
            in the template.
        -   Return None otherwise.

        ## Raises

        None

        ## Example conversions

        Conversions are performed so the values are more useful.
            -   boolean parameters return [False, True]
            -   integer parameters return a list of integers
            -   comma-separated strings are converted to lists of strings

        Examples

        - `"\\"Multicast,Ingress\\""` -> ["Ingress", "Multicast"]
        - `"\\"1,2\\""` -> [1,2]
        - `"\\"true,false\\""` -> [False, True]

        """
        parameter_type = self._get_type(parameter)
        if parameter_type == "boolean":
            return [False, True]
        choices = parameter.get("annotations", {}).get("Enum", None)
        if choices is None:
            choices = parameter.get("choices", None)
        if choices is None:
            choices = parameter.get("metaProperties", {}).get("validValues", None)
        if choices is None:
            return None
        if isinstance(choices, str):
            choices = re.sub(r'^\\"|\\$"', "", choices)
            choices = choices.split(",")
            choices = [re.sub(r"\"", "", choice) for choice in choices]
        choices = [self.conversion.make_int(choice) for choice in choices]
        return choices

    def _get_default(self, parameter: dict[str, Any]) -> Union[Any, None]:
        """
        # Summary

        - Return the parameter's default value, if specified in the template.
        - Return "" for parameters with no default value.

        ## Raises

        None

        ## Notes

        -  The default value can be in two places. Check both places.:
            - metaProperties.defaultValue
            - defaultValue
        -  Conversion to int must preceed conversion to boolean.
        """
        value = parameter.get("metaProperties", {}).get("defaultValue", None)
        if value is None:
            value = parameter.get("defaultValue", None)
        if value is None:
            return ""
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

    def _get_internal(self, parameter: dict[str, Any]) -> Union[bool, None]:
        """
        # Summary

        -   Return the parameter's annotations.IsInternal value,
            if specified in the template.
        -   Return None otherwise.

        ## Raises

        None
        """
        value = parameter.get("annotations", {}).get("IsInternal", None)
        if value is None:
            return None
        return self.conversion.make_boolean(value)

    def _get_min(self, parameter: dict[str, Any]) -> Union[int, None]:
        """
        # Summary

        - Return the parameter's minimum value, if specified in the template.
        - Return None otherwise.

        ## Raises

        None
        """
        value = parameter.get("metaProperties", {}).get("min", None)
        if value is None:
            return None
        return self.conversion.make_int(value)

    def _get_max(self, parameter: dict[str, Any]) -> Union[int, None]:
        """
        # Summary

        - Return the parameter's maximum value, if specified in the template.
        - Return None otherwise.

        ## Raises

        None
        """
        value = parameter.get("metaProperties", {}).get("max", None)
        if value is None:
            return None
        return self.conversion.make_int(value)

    def _get_param_name(self, parameter: dict[str, Any]) -> str:
        """
        # Summary

        -   Return the `name` key from the parameter dict.
        -   Return "" if `name` key is not found.

        ## Raises

        None
        """
        param_name = parameter.get("name", None)
        if param_name is None:
            return ""
        return param_name

    def _get_type(self, parameter: dict[str, Any]) -> Union[str, None]:
        """
        # Summary

        - Return the parameter's type, if specified in the template.
        - Return None otherwise.

        ## Raises

        None
        """
        parameter_type = parameter.get("parameterType", None)
        if parameter_type is None:
            parameter_type = parameter.get("type", None)
        return parameter_type

    def _build_info(self) -> None:
        """
        # Summary

        Build a `dict` of parameter information, keyed on parameter name.

        ## Raises

        None

        ## Notes

        The `self.info` dict, keyed on parameter name, will have the following
        structure for each parameter:

        - choices: (`list`, or `None`)
        - default: (`str`, `int`, etc, or `None`)
        - internal: (`bool`, or `None`)
        - max: (`int`, or `None`)
        - min: (`int`, or `None`)
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

    def _validate_property_prerequisites(self) -> None:
        """
        # Summary

        Validate that prerequisites are met for getter properties.

        ## Raises

        `ValueError` if:
            - template is not set
            - parameter_name is not set
            - parameter_name is not found in self.info
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        if not self.template:
            msg += "Call instance.template before accessing getter properties."
            raise ValueError(msg)
        if not self.parameter_name:
            msg += "Call instance.parameter_name before accessing getter properties."
            raise ValueError(msg)
        if self.parameter_name not in self.info:
            msg += f"Parameter {self.parameter_name} not found in fabric template. "
            msg += f"This likely means that the parameter {self.parameter_name} is not "
            msg += "appropriate for the fabric type."
            raise ValueError(msg)

    @property
    def parameter_choices(self) -> Union[list[Any], None]:
        """
        # Summary

        Return the parameter choices for parameter name.

        ## Raises

        `ValueError` if:
            - template is not set
            - parameter_name is not set
            - parameter_name is not found in the template
        """
        method_name = inspect.stack()[0][3]
        try:
            self._validate_property_prerequisites()
            return self.info[self.parameter_name]["choices"]
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: {error}"
            self.log.debug(msg)
            raise ValueError(msg) from error

    @property
    def parameter_default(self) -> Any:
        """
        # Summary

        Return the parameter default for parameter name.

        ## Raises

        `ValueError` if:
            - template is not set
            - parameter_name is not set
            - parameter_name is not found in the template
        """
        method_name = inspect.stack()[0][3]
        try:
            self._validate_property_prerequisites()
            return self.info[self.parameter_name]["default"]
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: {error}"
            self.log.debug(msg)
            raise ValueError(msg) from error

    @property
    def parameter_max(self) -> Union[int, None]:
        """
        # Summary

        Return the parameter max for parameter name.

        ## Raises

        `ValueError` if:
            - template is not set
            - parameter_name is not set
            - parameter_name is not found in the template
        """
        method_name = inspect.stack()[0][3]
        try:
            self._validate_property_prerequisites()
            return self.info[self.parameter_name]["max"]
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: {error}"
            self.log.debug(msg)
            raise ValueError(msg) from error

    @property
    def parameter_min(self) -> Union[int, None]:
        """
        # Summary

        Return the parameter min for parameter name.

        ## Raises

        `ValueError` if:
            - template is not set
            - parameter_name is not set
            - parameter_name is not found in the template
        """
        method_name = inspect.stack()[0][3]
        try:
            self._validate_property_prerequisites()
            return self.info[self.parameter_name]["min"]
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: {error}"
            self.log.debug(msg)
            raise ValueError(msg) from error

    @property
    def parameter_names(self) -> list[str]:
        """
        # Summary

        Return a list of parameter names found in the template.

        ## Raises

        `ValueError` if:
            - template is not set
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        if not self.template:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Call {self.class_name}.template before accessing parameter_names."
            raise ValueError(msg)
        return sorted(list(self.info.keys()))

    @property
    def parameter_type(self) -> Union[str, None]:
        """
        # Summary

        Return the parameter type for parameter name.

        ## Raises

        `ValueError` if:
            - template is not set
            - parameter_name is not set
            - parameter_name is not found in the template
        """
        method_name = inspect.stack()[0][3]
        try:
            self._validate_property_prerequisites()
            return self.info[self.parameter_name]["type"]
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: {error}"
            self.log.debug(msg)
            raise ValueError(msg) from error

    @property
    def parameter_name(self) -> str:
        """
        Return the parameter name.
        """
        return self._parameter_name

    @parameter_name.setter
    def parameter_name(self, value: str) -> None:
        self._parameter_name = value

    @property
    def template(self) -> dict[str, Any]:
        """
        - getter : return the template used to cull parameter info.
        - setter : set the template used to cull parameter info.
        - setter : raise ``TypeError`` if template is not a dict
        """
        return self._template

    @template.setter
    def template(self, value: dict[str, Any]) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "template must be a dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        self._template = value
