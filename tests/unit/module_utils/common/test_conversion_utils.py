# Copyright (c) 2025 Cisco and/or its affiliates.
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

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import re

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import ConversionUtils
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import does_not_raise

RE_ASN_STR = "^(((\\+)?[1-9]{1}[0-9]{0,8}|(\\+)?[1-3]{1}[0-9]{1,9}|(\\+)?[4]"
RE_ASN_STR += "{1}([0-1]{1}[0-9]{8}|[2]{1}([0-8]{1}[0-9]{7}|[9]{1}([0-3]{1}"
RE_ASN_STR += "[0-9]{6}|[4]{1}([0-8]{1}[0-9]{5}|[9]{1}([0-5]{1}[0-9]{4}|[6]"
RE_ASN_STR += "{1}([0-6]{1}[0-9]{3}|[7]{1}([0-1]{1}[0-9]{2}|[2]{1}([0-8]{1}"
RE_ASN_STR += "[0-9]{1}|[9]{1}[0-5]{1})))))))))|([1-5]\\d{4}|[1-9]\\d{0,3}|6"
RE_ASN_STR += "[0-4]\\d{3}|65[0-4]\\d{2}|655[0-2]\\d|6553[0-5])"
RE_ASN_STR += "(\\.([1-5]\\d{4}|[1-9]\\d{0,3}|6[0-4]\\d{3}|65[0-4]"
RE_ASN_STR += "\\d{2}|655[0-2]\\d|6553[0-5]|0))?)$"
re_asn = re.compile(RE_ASN_STR)
re_valid_fabric_name = re.compile(r"[a-zA-Z]+[a-zA-Z0-9_-]*")


def test_conversion_utils_00000() -> None:
    """
    Classes and Methods
    - ConversionUtils
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = ConversionUtils()
    assert instance.class_name == "ConversionUtils"
    assert instance.bgp_as_invalid_reason is None
    assert instance.re_asn == re_asn
    assert instance.re_valid_fabric_name == re_valid_fabric_name


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, False),  # 2-byte and 4-byte ASN minimum exceeded
        (1, True),  # 2-byte and 4-byte ASN minimum
        ("65535", True),  # 2-byte ASN maximum
        ("65536", True),  # 4-byte ASN within range
        ("1.0", True),  # dotted notation,same as 65536
        ("65535.65535", True),  # dotted notation, maximum
        ("65535.65536", False),  # dotted notation, maximum exceeded
        ("4200000000", True),  # 4-byte ASN private use minimum
        ("4294967294", True),  # 4-byte ASN private use maximum
        ("4294967295", True),  # 4-byte ASN maximum
        ("4294967296", False),  # 4-byte ASN maximum exceeded
        ("asdf", False),  # fails regex
        (None, False),  # fails regex
    ],
)
def test_conversion_utils_00010(value, expected) -> None:
    """
    ### Classes and Methods

    - ConversionUtils()
        - __init__()
        - bgp_as_is_valid()

    ### Summary
    Verify valid BGP AS is accepted and invalid BGP AS is rejected.

    ### Setup

    -   ConversionUtils() is instantiated

    ### Test

    -   ``bgp_as_is_valid`` is called with various valid and invalid values.

    ### Expected Result
    -   Exceptions are never raised
    -   Appropriate return value (True or False) for each value.
    """
    with does_not_raise():
        instance = ConversionUtils()
    assert instance.bgp_as_is_valid(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, 0),  # Not a boolean
        (1, 1),  # Not a boolean
        ("foo", "foo"),  # Not a boolean
        (True, True),  # boolean
        (False, False),  # boolean
        ("True", True),  # boolean string representation
        ("False", False),  # boolean string representation
        ("true", True),  # boolean string representation
        ("false", False),  # boolean string representation
        ("yes", True),  # boolean string representation
        ("no", False),  # boolean string representation
        ("YES", True),  # boolean string representation
        ("NO", False),  # boolean string representation
        (None, None),  # Not a boolean
    ],
)
def test_conversion_utils_00020(value, expected) -> None:
    """
    ### Classes and Methods

    - ConversionUtils()
        - __init__()
        - make_boolean()

    ### Summary
    Verify expected values are returned.

    ### Setup

    -   ConversionUtils() is instantiated

    ### Test

    -   ``make_boolean`` is called with various values.

    ### Expected Result
    -   Exceptions are never raised
    -   Appropriate return value (True, False, or value) for each value.
    """
    with does_not_raise():
        instance = ConversionUtils()
    assert instance.make_boolean(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, 0),  # int
        (999.1, 999),  # float converted to int
        ("foo", "foo"),  # Not an int
        (True, True),  # Not an int
        (False, False),  # Not an int
        ("True", "True"),  # Not an int
        ("False", "False"),  # Not an int
        (None, None),  # Not an int
    ],
)
def test_conversion_utils_00030(value, expected) -> None:
    """
    ### Classes and Methods

    - ConversionUtils()
        - __init__()
        - make_int()

    ### Summary
    Verify expected values are returned.

    ### Setup

    -   ConversionUtils() is instantiated

    ### Test

    -   ``make_int`` is called with various values.

    ### Expected Result
    -   Exceptions are never raised
    -   Appropriate return value for each input value.
    """
    with does_not_raise():
        instance = ConversionUtils()
    assert instance.make_int(value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, 0),  # int
        (999.1, 999.1),  # float
        ("foo", "foo"),  # str, not representation of None
        (True, True),  # bool, not representation of None
        (False, False),  # bool, not representation of None
        ("", None),  # str, empty string converted to None
        ("none", None),  # str, representation of None
        ("null", None),  # str, representation of None
        (None, None),  # None
    ],
)
def test_conversion_utils_00040(value, expected) -> None:
    """
    ### Classes and Methods

    - ConversionUtils()
        - __init__()
        - make_none()

    ### Summary
    Verify expected values are returned.

    ### Setup

    -   ConversionUtils() is instantiated

    ### Test

    -   `make_none` is called with various values.

    ### Expected Result
    -   Exceptions are never raised
    -   Appropriate return value for each input value.
    """
    with does_not_raise():
        instance = ConversionUtils()
    assert instance.make_none(value) == expected


@pytest.mark.parametrize(
    "value, expected, raises",
    [
        ("aaaa.bbbb.cccc", "aaaa.bbbb.cccc", False),  # valid mac
        ("aaaabbbbcccc", "aaaa.bbbb.cccc", False),  # valid mac
        ("aa:aa:bb:bb:cc:cc", "aaaa.bbbb.cccc", False),  # valid mac
        ("aa-aa-bb-bb-cc-cc", "aaaa.bbbb.cccc", False),  # valid mac
        ("Aa-AA-BB-bb-cC-cc", "aaaa.bbbb.cccc", False),  # valid mac
        ("zaaabbbbcccc", None, True),  # invalid mac
        ("notamac", None, True),  # invalid mac
        (0, None, True),  # invalid mac
        (999.1, None, True),  # invalid mac
        ("", None, True),  # invalid mac
        (True, None, True),  # invalid mac
        (False, None, True),  # invalid mac
        (None, None, True),  # invalid mac
    ],
)
def test_conversion_utils_00050(value, expected, raises) -> None:
    """
    ### Classes and Methods

    - ConversionUtils()
        - __init__()
        - translate_mac_address()

    ### Summary

    - Verify expected values are returned for valid mac
    - Verify ValueError is raised for invalid mac

    ### Setup

    -   ConversionUtils() is instantiated

    ### Test

    -   `translate_mac_address` is called with various values.

    ### Expected Result

    -   dotted-quad mac address returned for valid mac
    -   ValueError raised for invalid mac
    """
    with does_not_raise():
        instance = ConversionUtils()
    if not raises:
        with does_not_raise():
            assert instance.translate_mac_address(value) == expected
    else:
        match = f"Invalid MAC address: {value}"
        with pytest.raises(ValueError, match=re.escape(match)):
            instance.translate_mac_address(value)
