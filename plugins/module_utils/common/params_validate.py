"""
Validate that parameters conform to specification params_spec
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import inspect
import ipaddress
from collections.abc import MutableMapping as Map
from typing import Any, List

from ansible.module_utils.common import validation


class ParamsValidate:
    """
    Validate playbook parameters.

    This expects the following:
        1.  parameters: fully-merged dictionary of parameters
        2.  params_spec: Dictionary that describes each parameter
            in parameters

    Usage (where ansible_module is an instance of AnsibleModule):

    Assume the following params_spec describing parameters
    ip_address and foo.
    ip_address is a required parameter of type ipv4.
    foo is an optional parameter of type dict.
    foo contains a parameter named bar that is an optional
    parameter of type str with a default value of bingo.
    bar can be assigned one of three values: bingo, bango, or bongo.

    params_spec: Dict[str, Any] = {}
    params_spec["ip_address"] = {}
    params_spec["ip_address"]["required"] = False
    params_spec["ip_address"]["type"] = "ipv4"
    params_spec["foo"] = {}
    params_spec["foo"]["required"] = False
    params_spec["foo"]["type"] = "dict"
    params_spec["foo"]["default"] = {}
    params_spec["foo"]["bar"] = {}
    params_spec["foo"]["bar"]["required"] = False
    params_spec["foo"]["bar"]["type"] = "str"
    params_spec["foo"]["bar"]["default"] = "bingo"
    params_spec["foo"]["bar"]["choices"] = ["bingo", "bango", "bongo"]

    Which describes the following YAML:

    ip_address: 1.2.3.4
    foo:
        bar: bingo

    validator = ParamsValidator(ansible_module)
    validator.parameters = ansible_module.params
    validator.params_spec = params_spec
    """

    def __init__(self, ansible_module):
        self.class_name = __class__.__name__
        self.ansible_module = ansible_module
        self.validation = validation
        self.debug = False
        self.file_handle = None
        self.logfile = "/tmp/ansible_dcnm.log"
        self.properties = {}
        self.properties["parameters"] = None
        self.properties["params_spec"] = None
        self.reserved_params = set()
        self.reserved_params.add("choices")
        self.reserved_params.add("default")
        self.reserved_params.add("range_max")
        self.reserved_params.add("range_min")
        self.reserved_params.add("required")
        self.reserved_params.add("type")

    def log_msg(self, msg):
        """
        used for debugging. disable this when committing to main
        by setting self.debug to False in __init__()
        """
        if self.debug is False:
            return
        if self.file_handle is None:
            try:
                # since we need self.file_handle open throughout this class
                # we are disabling pylint R1732
                self.file_handle = open(  # pylint: disable=consider-using-with
                    f"{self.logfile}", "a+", encoding="UTF-8"
                )
            except IOError as err:
                msg = f"error opening logfile {self.logfile}. "
                msg += f"detail: {err}"
                self.ansible_module.fail_json(msg)

        self.file_handle.write(msg)
        self.file_handle.write("\n")
        self.file_handle.flush()

    def validate(self) -> None:
        """
        Verify that parameters in self.parameters conform to self.params_spec
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.validate_parameters(self.params_spec, self.parameters)

    def validate_parameters(self, spec, parameters):
        """
        Recursively traverse parameters and verify conformity with spec
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        for param in spec:
            if param in self.reserved_params:
                continue

            if isinstance(spec[param], Map):
                self.validate_parameters(spec[param], parameters.get(param, {}))

            # We shouldn't hit this since defaults are merged for all
            # missing parameters, but just in case...
            if (
                parameters.get(param, None) is None
                and spec[param].get("required", False) is True
            ):
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Playbook is missing mandatory parameter: {param}."
                self.ansible_module.fail_json(msg)

            self.verify_type(spec[param]["type"], parameters[param], param)
            self.verify_choices(
                spec[param].get("choices", None), parameters[param], param
            )
            if (
                spec[param].get("type", None) == "int"
                and spec[param].get("range_min", None) is not None
                and spec[param].get("range_max", None) is not None
            ):
                self.verify_integer_range(
                    spec[param].get("range_min", None),
                    spec[param].get("range_max", None),
                    parameters[param],
                    param,
                )

    def verify_choices(self, choices: List[Any], value: Any, param: str) -> None:
        """
        Verify that value is one of the choices
        """
        method_name = inspect.stack()[0][3]
        if choices is None:
            return

        if value not in choices:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid value for parameter '{param}'. "
            msg += f"Expected one of {choices}. "
            msg += f"Got {value}"
            self.ansible_module.fail_json(msg)

    def verify_integer_range(
        self, range_min: int, range_max: int, value: int, param: str
    ) -> None:
        """
        Verify that value is within the range range_min to range_max
        """
        method_name = inspect.stack()[0][3]
        if value < range_min or value > range_max:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid value for parameter '{param}'. "
            msg += f"Expected value between {range_min} and {range_max}. "
            msg += f"Got {value}"
            self.ansible_module.fail_json(msg)

    def verify_type(self, expected_type: str, value: Any, param: str) -> None:
        """
        Verify that value's type matches the expected type
        """
        method_name = inspect.stack()[0][3]
        if isinstance(expected_type, list):
            self.verify_multitype(expected_type, value, param)
            return
        invalid = False
        if expected_type == "str":
            try:
                value = self.validation.check_type_str(value)
            except TypeError as error:  # pylint: disable=unused-variable
                invalid = True
        elif expected_type == "bool":
            try:
                value = self.validation.check_type_bool(value)
            except TypeError as error:
                invalid = True
        elif expected_type == "int":
            try:
                value = self.validation.check_type_int(value)
            except TypeError as error:
                invalid = True
        if expected_type == "float":
            try:
                value = self.validation.check_type_float(value)
            except TypeError as error:
                invalid = True
        elif expected_type == "dict":
            # check_type_dict() converts strings with format "k1=v1, k2=v2"
            # to dict.
            try:
                value = self.validation.check_type_dict(value)
            except TypeError as error:
                invalid = True
        elif expected_type == "list":
            # check_type_list() converts int, str, float to a single-element
            # list. It also converts comma-separated strings to lists.
            try:
                value = self.validation.check_type_list(value)
            except TypeError as error:
                invalid = True
        elif expected_type == "set":
            # validate does not have a check_type_set() method
            if not isinstance(value, set):
                error = f"Expected type set. Got type {type(value)} for "
                error += f"param {param} with value {value}."
                invalid = True
        if expected_type == "tuple":
            # validate does not have a check_type_tuple() method
            if not isinstance(value, tuple):
                error = f"Expected type tuple. Got type {type(value)} for "
                error += f"param {param} with value {value}."
                invalid = True
        if expected_type == "ipv4":
            try:
                ipaddress.IPv4Address(value)
            except ipaddress.AddressValueError as error:
                invalid = True
        if expected_type == "ipv6":
            try:
                ipaddress.IPv6Address(value)
            except ipaddress.AddressValueError as error:
                invalid = True
        if expected_type == "ipv4_subnet":
            try:
                ipaddress.IPv4Network(value)
            except ValueError as error:
                invalid = True
        if expected_type == "ipv6_subnet":
            try:
                ipaddress.IPv6Network(value)
            except ValueError as error:
                invalid = True

        if invalid is True:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid type for parameter '{param}'. "
            msg += f"Expected {expected_type}. "
            msg += f"Got '{value}'. "
            msg += f"More info: {error}"
            self.ansible_module.fail_json(msg)

    def verify_multitype(
        self, expected_types: List[str], value: Any, param: str
    ) -> None:
        """
        Verify that value's type matches one of the types in expected_types
        """
        method_name = inspect.stack()[0][3]
        invalid = True
        error = ""
        for expected_type in expected_types:
            if expected_type == "str":
                try:
                    value = self.validation.check_type_str(value)
                    invalid = False
                except TypeError as error:  # pylint: disable=unused-variable
                    pass
            elif expected_type == "bool":
                try:
                    value = self.validation.check_type_bool(value)
                    invalid = False
                except TypeError as error:
                    pass
            elif expected_type == "int":
                try:
                    value = self.validation.check_type_int(value)
                    invalid = False
                except TypeError as error:
                    pass
            elif expected_type == "dict":
                try:
                    value = self.validation.check_type_dict(value)
                    invalid = False
                except TypeError as error:
                    pass
            elif expected_type == "list":
                try:
                    value = self.validation.check_type_list(value)
                    invalid = False
                except TypeError as error:
                    pass
            elif expected_type == "set":
                # validate does not have a check_type_set() method
                if isinstance(value, set):
                    invalid = False
                error = f"Expected type set. Got type {type(value)} for "
                error += f"param {param} with value {value}."
            elif expected_type == "tuple":
                # validate does not have a check_type_tuple() method
                if isinstance(value, tuple):
                    invalid = False
                error = f"Expected type tuple. Got type {type(value)} for "
                error += f"param {param} with value {value}."
            elif expected_type == "float":
                try:
                    value = self.validation.check_type_float(value)
                    invalid = False
                except TypeError as error:
                    pass
            elif expected_type == "ipv4":
                try:
                    ipaddress.IPv4Address(value)
                    invalid = False
                except ipaddress.AddressValueError as error:
                    pass
            elif expected_type == "ipv6":
                try:
                    ipaddress.IPv6Address(value)
                    invalid = False
                except ipaddress.AddressValueError:
                    pass
            elif expected_type == "ipv4_subnet":
                try:
                    ipaddress.IPv4Network(value)
                    invalid = False
                except ValueError:
                    pass
            elif expected_type == "ipv6_subnet":
                try:
                    ipaddress.IPv6Network(value)
                    invalid = False
                except ValueError:
                    pass
            else:
                error = f"Unknown type {expected_type} for param {param} "
                error += f"with value {value}."
                invalid = True

        if invalid is True:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid type for parameter '{param}'. "
            msg += f"Expected one of {expected_types}. "
            msg += f"Got '{value}'. "
            msg += f"More info: {error}"
            self.ansible_module.fail_json(msg)

    @property
    def parameters(self):
        """
        The parameters to validate.
        parameters have the same structure as params_spec.
        """
        return self.properties["parameters"]

    @parameters.setter
    def parameters(self, value):
        self.properties["parameters"] = value

    @property
    def params_spec(self):
        """
        The param specification used to validate the parameters
        """
        return self.properties["params_spec"]

    @params_spec.setter
    def params_spec(self, value):
        self.properties["params_spec"] = value
