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
        # Standard python types
        self._types = {}
        self._types["bool"] = bool
        self._types["dict"] = dict
        self._types["float"] = float
        self._types["int"] = int
        self._types["list"] = list
        self._types["set"] = set
        self._types["str"] = str
        self._types["tuple"] = tuple
        self._ipaddress_types = set()
        self._ipaddress_types.add("ipv4")
        self._ipaddress_types.add("ipv6")
        self._ipaddress_types.add("ipv4_subnet")
        self._ipaddress_types.add("ipv6_subnet")
        self.valid_expected_types = set(self._types.keys()).union(self._ipaddress_types)

        self.validations = {}
        self.validations["bool"] = validation.check_type_bool
        self.validations["dict"] = validation.check_type_dict
        self.validations["float"] = validation.check_type_float
        self.validations["int"] = validation.check_type_int
        self.validations["list"] = validation.check_type_list
        self.validations["set"] = self._validate_set
        self.validations["str"] = validation.check_type_str
        self.validations["tuple"] = self._validate_tuple
        self.validations["ipv4"] = self._validate_ipv4_address
        self.validations["ipv6"] = self._validate_ipv6_address
        self.validations["ipv4_subnet"] = self._validate_ipv4_subnet
        self.validations["ipv6_subnet"] = self._validate_ipv6_subnet

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
                parameters[param] = self._verify_multitype(
                    spec[param], parameters, param
                )
            else:
                parameters[param] = self._verify_type(
                    spec[param]["type"], parameters, param
                )

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
        self._verify_expected_type(expected_type, param)

        value = params[param]
        if expected_type in self._ipaddress_types:
            try:
                self._ipaddress_guard(expected_type, value, param)
            except TypeError as err:
                self.invalid_type(expected_type, value, param, err)
                return value

        try:
            return self.validations[expected_type](value)
        except (ValueError, TypeError) as err:
            self.invalid_type(expected_type, value, param, err)
            return value

    def _ipaddress_guard(self, expected_type, value: Any, param: str) -> None:
        """
        Guard against int and bool types for ipv4, ipv6, ipv4_subnet,
        and ipv6_subnet type.

        Raise TypeError if value's type is int or bool and
        expected_type is one of self._ipaddress_types.

        The ipaddress module accepts int and bool types and converts
        them to IP addresses or networks.  E.g. True becomes 0.0.0.1,
        False becomes 0.0.0.0, 1 becomse 0.0.0.1, etc.  Because of
        this, we need to fail int and bool values if expected_type is
        one of ipv4, ipv6, ipv4_subnet, or ipv6_subnet.
        """
        method_name = inspect.stack()[0][3]
        if type(value) not in [int, bool]:
            return
        if expected_type not in self._ipaddress_types:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Expected type {expected_type}. "
        msg += f"Got type {type(value)} for "
        msg += f"param {param} with value {value}."
        raise TypeError(f"{msg}")

    def invalid_type(
        self, expected_type: str, value: Any, param: str, error: str = ""
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

    def _verify_multitype( # pylint: disable=inconsistent-return-statements
        self, spec: Any, params: Any, param: str
    ) -> Any:
        """
        Verify that value's type matches one of the types in expected_types

        NOTES:
        1.  We've disabled inconsistent-return-statements.  We're pretty
            sure this method is correct.
        """
        method_name = inspect.stack()[0][3]

        # preferred_type is mandatory for multitype
        self._verify_preferred_type(spec, param)

        # try to convert value to the preferred_type
        preferred_type = spec["preferred_type"]

        (result, value) = self._verify_preferred_type_for_standard_types(
            preferred_type, params[param]
        )
        if result is True:
            return value

        (result, value) = self._verify_preferred_type_for_ipaddress_types(
            preferred_type, params[param]
        )
        if result is True:
            return value

        # Couldn't convert value to the preferred_type. Try the other types.
        value = params[param]

        expected_types = spec.get("type", [])

        if preferred_type in expected_types:
            # We've already tried preferred_type, so remove it
            expected_types.remove(preferred_type)

        for expected_type in expected_types:
            if expected_type in self._ipaddress_types and type(value) in [int, bool]:
                # These are invalid, so skip them
                continue

            try:
                value = self.validations[expected_type](value)
                return value
            except (ValueError, TypeError):
                pass

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Invalid type for parameter '{param}'. "
        msg += f"Expected one of {expected_types}. "
        msg += f"Got '{value}'."
        self.ansible_module.fail_json(msg)

    def _verify_preferred_type(self, spec: Any, param: str) -> None:
        """
        verify that spec contains the key 'preferred_type'
        """
        method_name = inspect.stack()[0][3]
        if spec.get("preferred_type", None) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid param_spec for parameter '{param}'. "
            msg += "If type is a list, preferred_type must be specified."
            self.ansible_module.fail_json(msg)

    def _verify_preferred_type_for_standard_types(
        self, preferred_type: str, value: Any
    ) -> (bool, Any):
        """
        If preferred_type is one of the standard python types
        we use isinstance() to check if we are able to convert
        the value to preferred_type
        """
        standard_type_success = True
        if preferred_type not in self._types:
            return (False, value)
        try:
            value = self.validations[preferred_type](value)
        except (ValueError, TypeError):
            standard_type_success = False

        if standard_type_success is True:
            if isinstance(value, self._types[preferred_type]):
                return (True, value)
        return (False, value)

    def _verify_preferred_type_for_ipaddress_types(
        self, preferred_type: str, value: Any
    ) -> (bool, Any):
        """
        We can't use isinstance() to verify ipaddress types.
        Hence, we check these types separately.
        """
        ip_type_success = True
        if preferred_type not in self._ipaddress_types:
            return (False, value)
        try:
            value = self.validations[preferred_type](value)
        except (ValueError, TypeError):
            ip_type_success = False
        if ip_type_success is True:
            return (True, value)
        return (False, value)

    @staticmethod
    def _validate_ipv4_address(value: Any) -> Any:
        """
        verify that value is an IPv4 address
        """
        try:
            _ = ipaddress.IPv4Address(value)
            return value
        except ipaddress.AddressValueError as err:
            raise ValueError(f"invalid IPv4 address: {err}") from err

    @staticmethod
    def _validate_ipv4_subnet(value: Any) -> Any:
        """
        verify that value is an IPv4 network
        """
        try:
            _ = ipaddress.IPv4Network(value)
            return value
        except ipaddress.AddressValueError as err:
            raise ValueError(f"invalid IPv4 network: {err}") from err

    @staticmethod
    def _validate_ipv6_address(value: Any) -> Any:
        """
        verify that value is an IPv6 address
        """
        try:
            _ = ipaddress.IPv6Address(value)
            return value
        except ipaddress.AddressValueError as err:
            raise ValueError(f"invalid IPv6 address: {err}") from err

    @staticmethod
    def _validate_ipv6_subnet(value: Any) -> Any:
        """
        verify that value is an IPv6 network
        """
        try:
            _ = ipaddress.IPv6Network(value)
            return value
        except ipaddress.AddressValueError as err:
            raise ValueError(f"invalid IPv6 network: {err}") from err

    @staticmethod
    def _validate_set(value: Any) -> Any:
        """
        verify that value is a set
        """
        if not isinstance(value, set):
            raise TypeError(f"expected set, got {type(value)}")
        return value

    @staticmethod
    def _validate_tuple(value: Any) -> Any:
        """
        verify that value is a tuple
        """
        if not isinstance(value, tuple):
            raise TypeError(f"expected tuple, got {type(value)}")
        return value

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

    def _verify_expected_type(self, expected_type: str, param: str) -> None:
        """
        Verify that expected_type is valid
        """
        method_name = inspect.stack()[0][3]
        if expected_type in self.valid_expected_types:
            return
        msg = f"{self.class_name}.{method_name}: "
        msg += f"Invalid 'type' in params_spec for parameter '{param}'. "
        msg += "Expected one of "
        msg += f"'{','.join(sorted(self.valid_expected_types))}'. "
        msg += f"Got '{expected_type}'."
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
