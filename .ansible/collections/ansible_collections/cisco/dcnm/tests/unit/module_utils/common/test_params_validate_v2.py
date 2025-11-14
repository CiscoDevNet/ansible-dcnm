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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# pylint: disable=unused-import
# Some fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-argument
# Some tests require calling protected methods
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.params_validate_v2 import \
    ParamsValidate
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    does_not_raise, params_validate_v2_fixture)


def test_params_validate_v2_00000(params_validate_v2) -> None:
    """
    ### Method
    -   ``__init__``

    ## Test
    -   Class attributes are initialized to expected values.
    """
    with does_not_raise():
        instance = params_validate_v2
    assert isinstance(instance, ParamsValidate)
    assert isinstance(instance.properties, dict)
    assert isinstance(instance.reserved_params, set)
    assert instance.reserved_params == {
        "choices",
        "default",
        "length_max",
        "no_log",
        "preferred_type",
        "range_max",
        "range_min",
        "required",
        "type",
    }
    assert instance.mandatory_param_spec_keys == {"required", "type"}
    assert instance.class_name == "ParamsValidate"
    assert instance.properties.get("parameters", "foo") is None
    assert instance.properties.get("params_spec", "foo") is None


def test_params_validate_v2_00100(params_validate_v2) -> None:
    """
    ### Property
    -   ``params_spec``

    ### Test
    -   ``params_spec`` accepts a valid minimum specification
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = "str"
    params_spec["foo"]["required"] = True

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec


def test_params_validate_v2_00110(params_validate_v2) -> None:
    """
    ### Property
    -   ``params_spec``

    ### Test
    -   ``params_spec`` raises ``TypeError`` when passed a value
        that is not a dict.
    """
    match = "ParamsValidate.params_spec: "
    match += "Invalid params_spec. Expected type dict. Got type "
    match += r"\<class 'str'\>\."

    with pytest.raises(TypeError, match=match):
        instance = params_validate_v2
        instance.params_spec = "foo"


@pytest.mark.parametrize(
    "present_key, present_key_value, missing_key",
    [
        ("required", True, "type"),
        ("type", "int", "required"),
    ],
)
def test_params_validate_v2_00120(
    params_validate_v2, present_key, present_key_value, missing_key
) -> None:
    """
    ### Property
    -   ``params_spec``

    ### Test
    -   ``params_spec`` calls ``ValueError`` when specification is missing
        a mandatory key.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"][f"{present_key}"] = present_key_value

    match = "ParamsValidate._verify_mandatory_param_spec_keys: "
    match += "Invalid params_spec. "
    match += f"Missing mandatory key '{missing_key}' for param 'foo'."

    with pytest.raises(ValueError, match=match):
        instance = params_validate_v2
        instance.params_spec = params_spec


def test_params_validate_v2_00200(params_validate_v2) -> None:
    """
    ### Property
    -   ``parameters``

    ### Test
    -   ``parameters`` accepts a valid dict.
    """
    with does_not_raise():
        instance = params_validate_v2
        instance.parameters = {"foo": "bar"}


def test_params_validate_v2_00210(params_validate_v2) -> None:
    """
    ### Property
    -   ``parameters``

    ### Test
    -   ``parameters`` raises ``TypeError`` when passed a value that
        is not a dict.
    """
    match = "ParamsValidate.parameters: "
    match += "Invalid parameters. Expected type dict. Got type "
    match += r"list\."

    with pytest.raises(TypeError, match=match):
        instance = params_validate_v2
        instance.parameters = [1, 2, 3]


def test_params_validate_v2_00300(params_validate_v2) -> None:
    """
    ### Method
    -   ``commit``

    ### Test
    -   ``commit`` raises ``ValueError`` if ``parameters`` has not
        been set.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = "str"
    params_spec["foo"]["required"] = True

    match = "ParamsValidate.commit: "
    match += "instance.parameters needs to be set prior to calling "
    match += r"instance.commit\(\)\."

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_params_validate_v2_00310(params_validate_v2) -> None:
    """
    ### Method
    -   ``commit``

    ### Test
    -   ``commit`` raises ``ValueError`` if ``params_spec`` has not
        been set.
    """
    parameters = {}
    parameters["foo"] = "bar"

    match = "ParamsValidate.commit: "
    match += "instance.params_spec needs to be set prior to calling "
    match += r"instance.commit\(\)\."

    with does_not_raise():
        instance = params_validate_v2
        instance.parameters = parameters
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_params_validate_v2_00320(params_validate_v2) -> None:
    """
    ### Method
    -   ``commit``
    -   ``validate_parameters``
    -   ``verify_choices``

    ### Test
    -   happy path for ``params_spec`` and ``parameters``
    """
    with does_not_raise():
        instance = params_validate_v2
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = "str"
    params_spec["foo"]["required"] = True
    params_spec["foo"]["choices"] = ["bar", "baz"]

    parameters = {}
    parameters["foo"] = "bar"

    with does_not_raise():
        instance.params_spec = params_spec
        instance.parameters = parameters
        instance.commit()


def test_params_validate_v2_00400(params_validate_v2) -> None:
    """
    ### Method
    -   ``commit``
    -   ``validate_parameters``

    ### Test
    -   ``validate_parameters`` raises ``ValueError`` if parameters
        is missing a required parameter.
    """
    with does_not_raise():
        instance = params_validate_v2
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = "str"
    params_spec["foo"]["required"] = True
    params_spec["foo"]["choices"] = ["bar", "baz"]

    parameters = {}
    parameters["bar"] = "baz"

    with does_not_raise():
        instance.params_spec = params_spec
        instance.parameters = parameters

    match = "ParamsValidate._validate_parameters: "
    match += "Playbook is missing mandatory parameter: foo."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_params_validate_v2_00500(params_validate_v2) -> None:
    """
    ### Method
    -   ``commit``
    -   ``verify_choices``

    ### Test
    -   Exception is not raised when ``parameter`` value is
        a valid choice.
    """
    with does_not_raise():
        instance = params_validate_v2
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = "str"
    params_spec["foo"]["required"] = True
    params_spec["foo"]["choices"] = ["bar", "baz"]

    parameters = {}
    parameters["foo"] = "baz"

    with does_not_raise():
        instance.params_spec = params_spec
        instance.parameters = parameters
        instance.commit()


def test_params_validate_v2_00510(params_validate_v2) -> None:
    """
    ### Method
    -   ``commit``
    -   ``verify_choices``

    ### Test
    -   ``ValueError`` is raised when ``parameter`` value is
        not a valid choice.
    """
    with does_not_raise():
        instance = params_validate_v2
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = "str"
    params_spec["foo"]["required"] = True
    params_spec["foo"]["choices"] = ["bar", "baz"]

    parameters = {}
    parameters["foo"] = "bing"

    with does_not_raise():
        instance.params_spec = params_spec
        instance.parameters = parameters

    match = "ParamsValidate._verify_choices: "
    match += "Invalid value for parameter 'foo'. "
    match += r"Expected one of \['bar', 'baz'\]. Got bing"

    with pytest.raises(ValueError, match=match):
        instance.commit()


@pytest.mark.parametrize(
    "value, expected_type",
    [("bing", "int"), ("1", "ipv4"), (False, "set"), (True, "tuple"), ("bar", "bool")],
)
def test_params_validate_v2_00600(params_validate_v2, value, expected_type) -> None:
    """
    ### Method
    -   ``commit``
    -   ``verify_type``

    ### Test
    -   Behavior when parameter value's type is not convertable to expected_type.

    ### NOTES
    1.  value == bool and type in [ipv4, ipv6, ipv4_subnet, ipv6_subnet]
        is tested separately (see ipaddress_guard test)
    2.  If expected_type is "str" ANY value (dict, tuple, float, int, etc)
        will succeed.  Hence, for expected_type == "str" there are no invalid
        values.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = expected_type
    params_spec["foo"]["required"] = True

    parameters = {}
    parameters["foo"] = value

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters

    match = "ParamsValidate._invalid_type: "
    match += "Invalid type for parameter 'foo'. "
    match += f"Expected {expected_type}. Got '{value}'. "

    with pytest.raises(ValueError, match=match):
        instance.commit()


@pytest.mark.parametrize(
    "value, expected_type",
    [
        (1, "int"),
        ("1", "int"),
        (1.0, "float"),
        ("1.0", "float"),
        ("foo", "str"),
        (1, "str"),
        ([1, 2, "3"], "list"),
        (1, "list"),
        ((1, 2, 3), "tuple"),
        ({"foo": "bar"}, "dict"),
        ("foo=1, bar=2", "dict"),
        ({"foo", "bar"}, "set"),
        ("1.1.1.1", "ipv4"),
        ("1.1.1.0/24", "ipv4_subnet"),
        ("2001:1:1::fe", "ipv6"),
        ("2001:1:1::/64", "ipv6_subnet"),
    ],
)
def test_params_validate_v2_00610(params_validate_v2, value, expected_type) -> None:
    """
    ### Method
    -   ``commit``
    -   ``verify_type``

    ### Test
    -   Verify exception is not raised if parameter type is valid.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = expected_type
    params_spec["foo"]["required"] = True

    parameters = {}
    parameters["foo"] = value

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters
        instance.commit()


def test_params_validate_v2_00620(params_validate_v2) -> None:
    """
    ### Method
    -   ``commit``
    -   ``verify_type``

    ### Test
    -   Verify that ``verify_type`` raises ``ValueError`` if type is not a valid type.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["required"] = True
    params_spec["foo"]["type"] = "bad_type"

    parameters = {}
    parameters["foo"] = "bar"

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters

    match = "ParamsValidate._verify_expected_type: "
    match += "Invalid 'type' in params_spec for parameter 'foo'. "
    match += "Expected one of "
    match += f"'{','.join(sorted(instance.valid_expected_types))}'. "
    match += "Got 'bad_type'."

    with pytest.raises(ValueError, match=match):
        instance.commit()


@pytest.mark.parametrize(
    "value, expected_type, preferred_type",
    [
        # preferred type != value's "native" type
        ("1", ["int", "str"], "int"),
        (1, ["int", "str", "list"], "list"),
        ("1", ["int", "str", "list"], "list"),
        (1.145, ["int", "list", "float"], "list"),
        # preferred_type == value's "native" type
        ("1", ["int", "str"], "str"),
        (1, ["int", "str"], "int"),
        ([1, 2, 3], ["int", "str", "list"], "list"),
        (1.456, ["int", "str", "float"], "float"),
        (False, ["int", "str", "bool"], "bool"),
        ("1.1.1.1", ["int", "str", "ipv4"], "ipv4"),
        # any type is convertable to str
        (1, ["int", "str"], "str"),
        ([1, 2, 3], ["int", "str", "list"], "str"),
        ((1, 2, 3), ["int", "str", "list"], "str"),
        ({1, 2, 3}, ["int", "str", "list"], "str"),
        ({"foo": "bar"}, ["int", "str", "dict"], "str"),
        (False, ["int", "str", "bool"], "str"),
        (1.456, ["int", "str", "float"], "str"),
    ],
)
def test_params_validate_v2_00700(
    params_validate_v2, value, expected_type, preferred_type
) -> None:
    """
    ### Method
    -   ``commit``
    -   ``_verify_multitype``

    ### Test
    -   Verify ``_verify_multitype`` converts parameter value to
        preferred_type.

    NOTES:
    1.  ansible.module_utils.common.validation can/will convert
        any type to type str.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = expected_type
    params_spec["foo"]["preferred_type"] = preferred_type
    params_spec["foo"]["required"] = True

    parameters = {}
    parameters["foo"] = value

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters
        instance.commit()
    if preferred_type in instance._ipaddress_types:  # pylint: disable=protected-access
        assert isinstance(instance.parameters["foo"], str)
    else:
        assert isinstance(
            instance.parameters["foo"], instance._standard_types[preferred_type]
        )  # pylint: disable=protected-access


@pytest.mark.parametrize(
    "value, type_to_verify, preferred_type",
    [
        ("1", ["dict", "ipv4"], "dict"),
        ("1", ["dict", "ipv4"], "ipv4"),
    ],
)
def test_params_validate_v2_00710(
    params_validate_v2, value, type_to_verify, preferred_type
) -> None:
    """
    ### Method
    -   ``commit``
    -   ``verify_type``
    -   ``_verify_multitype``

    ### Test
    -   Verify behavior when parameter type is invalid.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = type_to_verify
    params_spec["foo"]["preferred_type"] = preferred_type
    params_spec["foo"]["required"] = True

    parameters = {}
    parameters["foo"] = value

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters

    match = "ParamsValidate._verify_multitype: "
    match += "Invalid type for parameter 'foo'. "
    match += r"Expected one of .*?. "
    match += f"Got '{value}'."

    with pytest.raises(ValueError, match=match):
        instance.commit()


@pytest.mark.parametrize(
    "value, type_to_verify, preferred_type",
    [
        ("1", ["dict", "ipv4"], "dict"),
        ("1", ["dict", "ipv4"], "ipv4"),
    ],
)
def test_params_validate_v2_00720(
    params_validate_v2, value, type_to_verify, preferred_type
) -> None:
    """
    ### Method
    -   ``commit``
    -   ``verify_type``
    -   ``_verify_multitype``

    ### Test
    -   Verify behavior when parameter type is invalid in multi-level
        parameters.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = ["int", "str"]
    params_spec["foo"]["preferred_type"] = "int"
    params_spec["foo"]["required"] = True
    params_spec["bar"] = {}
    params_spec["bar"]["type"] = "dict"
    params_spec["bar"]["required"] = False
    params_spec["bar"]["baz"] = {}
    params_spec["bar"]["baz"]["type"] = type_to_verify
    params_spec["bar"]["baz"]["preferred_type"] = preferred_type
    params_spec["bar"]["baz"]["required"] = True

    parameters = {}
    parameters["foo"] = 1
    parameters["bar"] = {}
    parameters["bar"]["baz"] = value

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters

    match = "ParamsValidate._verify_multitype: "
    match += "Invalid type for parameter 'baz'. "
    match += r"Expected one of .*?. "
    match += f"Got '{value}'."

    with pytest.raises(ValueError, match=match):
        instance.commit()


@pytest.mark.parametrize(
    "value, type_to_verify, preferred_type",
    [
        ("1", ["dict", "tuple", "list"], "dict"),
    ],
)
def test_params_validate_v2_00730(
    params_validate_v2, value, type_to_verify, preferred_type
) -> None:
    """
    ### Method
    -   ``commit``
    -   ``verify_type``
    -   ``_verify_multitype``

    ### Test
    -   Verify behavior when parameter value cannot be converted to the
        preferred_type, but can be converted to another type in
        ``_verify_multitype``
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = type_to_verify
    params_spec["foo"]["preferred_type"] = preferred_type
    params_spec["foo"]["required"] = True

    parameters = {}
    parameters["foo"] = value

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters
        instance.commit()


def test_params_validate_v2_00740(params_validate_v2) -> None:
    """
    ### Method
    -   ``commit``
    -   ``_verify_multitype``
    -   ``_verify_preferred_type``

    ### Test
    -   Verify behavior when the preferred_type key is missing from spec
        when spec.type is a list of types.

    NOTES:
    1.  preferred_type is mandatory when spec.type is a list of types.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = ["int", "str"]
    params_spec["foo"]["required"] = True

    parameters = {}
    parameters["foo"] = 1

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters
    match = "ParamsValidate._verify_preferred_type_param_spec_is_present: "
    match += "Invalid param_spec for parameter 'foo'. "
    match += "If type is a list, preferred_type must be specified."
    with pytest.raises(ValueError, match=match):
        instance.commit()


@pytest.mark.parametrize(
    "value, type_to_verify",
    [
        (1, "ipv4"),
        (1, "ipv6"),
        (1, "ipv4_subnet"),
        (1, "ipv6_subnet"),
        (True, "ipv4"),
        (True, "ipv6"),
        (True, "ipv4_subnet"),
        (True, "ipv6_subnet"),
    ],
)
def test_params_validate_v2_00800(params_validate_v2, value, type_to_verify) -> None:
    """
    ### Method
    -   ``commit``
    -  ``verify_type``
    -   ``ipaddress_guard``

    ### Test
    -   Verify that ``ValueError`` is raised if type is in
        [ipv4, ipv6, ipv4_subnet, ipv6_subnet] and value is bool or int.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = type_to_verify
    params_spec["foo"]["required"] = True

    parameters = {}
    parameters["foo"] = value

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters

    match = "ParamsValidate._ipaddress_guard: "
    match += f"Expected type {type_to_verify}. "
    match += f"Got type {type(value).__name__} for param foo with value {value}."
    with pytest.raises(ValueError, match=match):
        instance.commit()


@pytest.mark.parametrize(
    "value, range_min, range_max",
    [
        (1, 1, 10),
        (5, 1, 10),
        (10, 1, 10),
    ],
)
def test_params_validate_v2_00900(
    params_validate_v2, value, range_min, range_max
) -> None:
    """
    ### Method
    -   ``commit``
    -   ``_verify_integer_range``

    ### Test
    -   Verify exception is not raised when parameter (int) is within
        range_min and range_max.
    """
    with does_not_raise():
        instance = params_validate_v2
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = "int"
    params_spec["foo"]["required"] = True
    params_spec["foo"]["range_min"] = range_min
    params_spec["foo"]["range_max"] = range_max

    parameters = {}
    parameters["foo"] = value

    with does_not_raise():
        instance.params_spec = params_spec
        instance.parameters = parameters
        instance.commit()


@pytest.mark.parametrize(
    "value, range_min, range_max",
    [
        (-1, 1, 10),
        (0, 1, 10),
        (11, 1, 10),
    ],
)
def test_params_validate_v2_00910(
    params_validate_v2, value, range_min, range_max
) -> None:
    """
    ### Method
    -   ``commit``
    -   ``_verify_integer_range``

    ### Test
    -   Verify ``ValueError`` is raised if parameter (int) is not within
        range_min and range_max
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = "int"
    params_spec["foo"]["required"] = True
    params_spec["foo"]["range_min"] = range_min
    params_spec["foo"]["range_max"] = range_max

    parameters = {}
    parameters["foo"] = value

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters

    match = "ParamsValidate._verify_integer_range: "
    match += "Invalid value for parameter 'foo'. "
    match += f"Expected value between 1 and 10. Got {value}"

    with pytest.raises(ValueError, match=match):
        instance.commit()


@pytest.mark.parametrize(
    "value, range_min, range_max",
    [
        (-1, "foo", 10),
        (0, 1, "bar"),
        (11, [], {}),
    ],
)
def test_params_validate_v2_00920(
    params_validate_v2, value, range_min, range_max
) -> None:
    """
    ### Method
    -   ``commit``
    -   ``_verify_integer_range``

    ### Test
    -   Negative. Verify ``ValueError`` is raised if range_min or range_max
        is not an integer.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = "int"
    params_spec["foo"]["required"] = True
    params_spec["foo"]["range_min"] = range_min
    params_spec["foo"]["range_max"] = range_max

    parameters = {}
    parameters["foo"] = value

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters

    match = "ParamsValidate._verify_integer_range: "
    match += "Invalid specification for parameter 'foo'. "
    match += "range_min and range_max must be integers. Got "
    match += rf"range_min '.*?' type {type(range_min)}, "
    match += rf"range_max '.*?' type {type(range_max)}."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_params_validate_v2_00930(params_validate_v2) -> None:
    """
    ### Method
    -   ``commit``
    -   ``_verify_integer_range``

    ### Test
    -   Negative: Verify ``ValueError`` is raised if specification for non-int parameter
        contains range_min and range_max.
    """
    params_spec = {}
    params_spec["foo"] = {}
    params_spec["foo"]["type"] = "str"
    params_spec["foo"]["required"] = True
    params_spec["foo"]["range_min"] = 1
    params_spec["foo"]["range_max"] = 10

    parameters = {}
    parameters["foo"] = "bar"

    with does_not_raise():
        instance = params_validate_v2
        instance.params_spec = params_spec
        instance.parameters = parameters

    match = "ParamsValidate._validate_parameters: "
    match += "Invalid param_spec for parameter 'foo'. "
    match += "range_min and range_max are only valid for "
    match += "parameters of type int. Got type str for param foo."

    with pytest.raises(ValueError, match=match):
        instance.commit()
