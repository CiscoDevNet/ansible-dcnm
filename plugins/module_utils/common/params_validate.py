"""
Validate that parameters conform to specification params_spec
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name

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
    params_spec["foo"]["bar"] = {}
    params_spec["foo"]["bar"]["required"] = False
    params_spec["foo"]["bar"]["type"] = "str"
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
        self.reserved_params.add("preferred_type")
        self.mandatory_param_spec_keys = set()
        self.mandatory_param_spec_keys.add("required")
        self.mandatory_param_spec_keys.add("type")
        self.types = dict()
        self.types["str"] = str
        self.types['int'] = int
        self.types['float'] = float
        self.types['bool'] = bool
        self.types['dict'] = dict
        self.types['list'] = list
        self.types['set'] = set
        self.types['tuple'] = tuple


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
        self._validate_parameters(self.params_spec, self.parameters)

    def _validate_parameters(self, spec, parameters):
        """
        Recursively traverse parameters and verify conformity with spec
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        for param in spec:
            if param in self.reserved_params:
                continue

            if isinstance(spec[param], Map):
                self._validate_parameters(spec[param], parameters.get(param, {}))

            # We shouldn't hit this since defaults are merged for all
            # missing parameters, but just in case...
            if (
                parameters.get(param, None) is None
                and spec[param].get("required", False) is True
            ):
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Playbook is missing mandatory parameter: {param}."
                self.ansible_module.fail_json(msg)

            if isinstance(spec[param]["type"], list):
                parameters[param] = self._verify_multitype(spec[param], parameters, param)
            else:
                parameters[param] = self._verify_type(spec[param]["type"], parameters, param)

            self._verify_choices(
                spec[param].get("choices", None), parameters[param], param
            )

            if spec[param].get("type", None) != "int" and (
                spec[param].get("range_min", None) is not None
                or spec[param].get("range_max", None) is not None
            ):
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Invalid param_spec for parameter '{param}'. "
                msg += "range_min and range_max are only valid for "
                msg += "parameters of type int. "
                msg += f"Got type {spec[param]['type']} for param {param}."
                self.ansible_module.fail_json(msg)

            if (
                spec[param].get("type", None) == "int"
                and spec[param].get("range_min", None) is not None
                and spec[param].get("range_max", None) is not None
            ):
                self._verify_integer_range(
                    spec[param].get("range_min", None),
                    spec[param].get("range_max", None),
                    parameters[param],
                    param,
                )

    def _verify_choices(self, choices: List[Any], value: Any, param: str) -> None:
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

    def _verify_integer_range(
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

    def _verify_type(self, expected_type: str, params: Any, param: str) -> Any:
        """
        Verify that value's type matches the expected type
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        value = params[param]
        value = self._verify_str(expected_type, value, param)
        value = self._verify_bool(expected_type, value, param)
        value = self._verify_int(expected_type, value, param)
        value = self._verify_float(expected_type, value, param)
        value = self._verify_dict(expected_type, value, param)
        value = self._verify_list(expected_type, value, param)
        value = self._verify_set(expected_type, value, param)
        value = self._verify_tuple(expected_type, value, param)
        value = self._verify_ipv4(expected_type, value, param)
        value = self._verify_ipv6(expected_type, value, param)
        value = self._verify_ipv4_subnet(expected_type, value, param)
        value = self._verify_ipv6_subnet(expected_type, value, param)
        return value

    def _verify_str(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is a str, or convert to str if possible
        If value is not a str, and conversion fails,
        call invalid_type() to fail the playbook
        """
        if expected_type != "str":
            return value
        try:
            return self.validation.check_type_str(value)
        except TypeError as err:
            self.invalid_type(expected_type, value, param, err)
            return value  # never reached, but it makes pylint happy

    def _verify_bool(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is a bool, or convert to bool if possible
        If value is not a bool, and conversion fails,
        call invalid_type() to fail the playbook
        """
        if expected_type != "bool":
            return value
        try:
            return self.validation.check_type_bool(value)
        except TypeError as err:
            self.invalid_type(expected_type, value, param, err)
            return value  # never reached, but it makes pylint happy

    def _verify_int(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is an int, or convert to int if possible
        If value is not an int, and conversion fails,
        call invalid_type() to fail the playbook
        """
        if expected_type != "int":
            return value
        try:
            return self.validation.check_type_int(value)
        except TypeError as err:
            self.invalid_type(expected_type, value, param, err)
            return value  # never reached, but it makes pylint happy

    def _verify_float(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is a float, or convert to float if possible
        If value is not a float, and conversion fails,
        call invalid_type() to fail the playbook
        """
        if expected_type != "float":
            return value
        try:
            return self.validation.check_type_float(value)
        except TypeError as err:
            self.invalid_type(expected_type, value, param, err)
            return value  # never reached, but it makes pylint happy

    def _verify_dict(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is a dict
        check_type_dict() also converts strings with format
        "k1=v1, k2=v2" to dict.

        If value is not a dict, and conversion fails,
        call invalid_type() to fail the playbook
        """
        if expected_type != "dict":
            return value
        try:
            return self.validation.check_type_dict(value)
        except TypeError as err:
            self.invalid_type(expected_type, value, param, err)
            return value  # never reached, but it makes pylint happy

    def _verify_list(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is a list
        check_type_list() converts int, str, float to a single-element list.
        It also converts comma-separated strings to lists.

        If value is not a list, and conversion fails,
        call invalid_type() to fail the playbook
        """
        if expected_type != "list":
            return value
        try:
            return self.validation.check_type_list(value)
        except TypeError as err:
            self.invalid_type(expected_type, value, param, err)
            return value  # never reached, but it makes pylint happy

    def _verify_set(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is a set
        validate does not have a check_type_set() method so
        we use isinstance() instead.

        If value is not a set, call invalid_type() to fail the playbook
        """
        if expected_type != "set":
            return value
        if isinstance(value, set):
            return value
        error = f"Expected type set. Got type {type(value)} for "
        error += f"param {param} with value {value}."
        self.invalid_type(expected_type, value, param, error)
        return value  # never reached, but it makes pylint happy

    def _verify_tuple(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is a tuple
        validate does not have a check_type_tuple() method so
        we use isinstance() instead.

        If value is not a tuple, call invalid_type() to fail the playbook
        """
        if expected_type != "tuple":
            return value
        if isinstance(value, tuple):
            return value
        error = f"Expected type tuple. Got type {type(value)} for "
        error += f"param {param} with value {value}."
        self.invalid_type(expected_type, value, param, error)
        return value  # never reached, but it makes pylint happy

    def _verify_ipv4(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is an IPv4 address
        If value is not an IPv4 address, call invalid_type()
        to fail the playbook
        """
        if expected_type != "ipv4":
            return value
        self.ipaddress_guard(expected_type, value, param)
        try:
            _ = ipaddress.IPv4Address(value)
            return value
        except ipaddress.AddressValueError as err:
            self.invalid_type(expected_type, value, param, err)
            return value  # never reached, but it makes pylint happy

    def _verify_ipv6(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is an IPv6 address
        If value is not an IPv6 address, call invalid_type()
        to fail the playbook
        """
        if expected_type != "ipv6":
            return value
        self.ipaddress_guard(expected_type, value, param)
        try:
            _ = ipaddress.IPv6Address(value)
            return value
        except ipaddress.AddressValueError as err:
            self.invalid_type(expected_type, value, param, err)
            return value  # never reached, but it makes pylint happy

    def _verify_ipv4_subnet(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is an IPv4 subnet
        If value is not an IPv4 subnet, call invalid_type()
        to fail the playbook
        """
        if expected_type != "ipv4_subnet":
            return value
        self.ipaddress_guard(expected_type, value, param)
        try:
            _ = ipaddress.IPv4Network(value)
            return value
        except ValueError as err:
            self.invalid_type(expected_type, value, param, err)
            return value  # never reached, but it makes pylint happy

    def _verify_ipv6_subnet(self, expected_type: str, value: Any, param: str) -> Any:
        """
        verify that value is an IPv6 subnet
        If value is not an IPv6 subnet, call invalid_type()
        to fail the playbook
        """
        if expected_type != "ipv6_subnet":
            return value
        self.ipaddress_guard(expected_type, value, param)
        try:
            _ = ipaddress.IPv6Network(value)
            return value
        except ValueError as err:
            self.invalid_type(expected_type, value, param, err)
            return value  # never reached, but it makes pylint happy

    def ipaddress_guard(self, expected_type, value: Any, param: str) -> None:
        """
        Guard against int and bool types for ipv4, ipv6, ipv4_subnet,
        and ipv6_subnet type.

        The ipaddress module accepts int and bool types and converts
        them to IP addresses or networks.  E.g. True becomes 0.0.0.1,
        False becomes 0.0.0.0, 1 becomse 0.0.0.1, etc.  Because of
        this, we need to fail int and bool values if expected_type is
        one of ipv4, ipv6, ipv4_subnet, or ipv6_subnet.
        """
        if isinstance(value, int):
            error = f"Expected type ipv4. Got type {type(value)} for "
            error += f"param {param} with value {value}."
            self.invalid_type(expected_type, value, param, error)
        if isinstance(value, bool):
            error = f"Expected type ipv4. Got type {type(value)} for "
            error += f"param {param} with value {value}."
            self.invalid_type(expected_type, value, param, error)

    def invalid_type(
        self, expected_type: str, value: Any, param: str, error: str
    ) -> None:
        """
        Calls fail_json when value's type does not match expected_type
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"Invalid type for parameter '{param}'. "
        msg += f"Expected {expected_type}. "
        msg += f"Got '{value}'. "
        msg += f"More info: {error}"
        self.ansible_module.fail_json(msg)

    def _verify_multitype(
        self, spec: Any, params: Any, param: str
    ) -> Any:
        """
        Verify that value's type matches one of the types in expected_types
        """
        method_name = inspect.stack()[0][3]

        # preferred_type is mandatory for multitype
        if spec.get("preferred_type", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid param_spec for parameter '{param}'. "
            msg += "If type is a list, preferred_type must be specified."
            self.ansible_module.fail_json(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"spec: {spec}"
        self.log_msg(msg)
        # try to convert to preferred_type
        preferred_type = spec["preferred_type"]
        self.log_msg(f"{self.class_name}.{method_name}: preferred_type: {preferred_type}")
        value = self._verify_type(preferred_type, params, param)
        if isinstance(value, self.types[preferred_type]):
            return value

        invalid = True
        error = ""
        value = params[param]
        expected_types = spec.get("type", [])

        for expected_type in expected_types:
            if expected_type == "str":
                try:
                    value = self.validation.check_type_str(value)
                    invalid = False
                except TypeError:
                    pass
            elif expected_type == "bool":
                try:
                    value = self.validation.check_type_bool(value)
                    invalid = False
                except TypeError:
                    pass
            elif expected_type == "int":
                try:
                    value = self.validation.check_type_int(value)
                    invalid = False
                except TypeError:
                    pass
            elif expected_type == "dict":
                try:
                    value = self.validation.check_type_dict(value)
                    invalid = False
                except TypeError:
                    pass
            elif expected_type == "list":
                try:
                    value = self.validation.check_type_list(value)
                    invalid = False
                except TypeError:
                    pass
            elif expected_type == "set":
                # validate does not have a check_type_set() method
                if isinstance(value, set):
                    invalid = False
            elif expected_type == "tuple":
                # validate does not have a check_type_tuple() method
                if isinstance(value, tuple):
                    invalid = False
            elif expected_type == "float":
                try:
                    value = self.validation.check_type_float(value)
                    invalid = False
                except TypeError:
                    pass
            elif expected_type == "ipv4":
                try:
                    ipaddress.IPv4Address(value)
                    invalid = False
                except ipaddress.AddressValueError:
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

        if invalid is False:
            return value
        msg = f"{self.class_name}.{method_name}: "
        msg += f"Invalid type for parameter '{param}'. "
        msg += f"Expected one of {expected_types}. "
        msg += f"Got '{value}'."
        if error:
            msg += f"More info: {error}"
        self.ansible_module.fail_json(msg)

    def verify_mandatory_param_spec_keys(self, params_spec: dict) -> None:
        """
        Recurse over params_spec dictionary and verify that the
        specification for each param contains the mandatory keys
        defined in self.mandatory_param_spec_keys
        """
        method_name = inspect.stack()[0][3]
        for param in params_spec:
            if not isinstance(params_spec[param], Map):
                continue
            if param in self.reserved_params:
                continue
            self.verify_mandatory_param_spec_keys(params_spec[param])
            for key in self.mandatory_param_spec_keys:
                if key in params_spec[param]:
                    continue
                msg = f"{self.class_name}.{method_name}: "
                msg += "Invalid params_spec. Missing mandatory key "
                msg += f"'{key}' for param '{param}'."
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
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Invalid parameters. Expected type dict. "
            msg += f"Got type {type(value)}."
            self.ansible_module.fail_json(msg)
        self.properties["parameters"] = value

    @property
    def params_spec(self):
        """
        The param specification used to validate the parameters
        """
        return self.properties["params_spec"]

    @params_spec.setter
    def params_spec(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Invalid params_spec. Expected type dict. "
            msg += f"Got type {type(value)}."
            self.ansible_module.fail_json(msg)
        self.verify_mandatory_param_spec_keys(value)
        self.properties["params_spec"] = value
