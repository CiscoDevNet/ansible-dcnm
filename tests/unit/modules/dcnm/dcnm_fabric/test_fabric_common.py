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
# Also, fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-import
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=unused-argument
# pylint: disable=invalid-name

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy
import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    does_not_raise, fabric_common_fixture, params, payloads_fabric_common,
    responses_fabric_common)


def test_fabric_common_00010(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricUpdateBulk
        - __init__()

    Summary
    - Verify the class attributes are initialized to expected values.

    Test
    - Class attributes are initialized to expected values
    - ``ValueError`` is not called
    """
    with does_not_raise():
        instance = fabric_common
    assert instance.class_name == "FabricCommon"

    assert instance._fabric_details is None
    assert instance._fabric_summary is None
    assert instance._fabric_type == "VXLAN_EVPN"
    assert instance._rest_send is None
    assert instance._results is None


def test_fabric_common_00020(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _fixup_payloads_to_commit()
        - _fixup_anycast_gw_mac()

    Summary
    - Verify ``ValueError`` is raised when ANYCAST_GW_MAC is malformed.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
        instance._payloads_to_commit = payloads_fabric_common(key)
    match = r"FabricCommon\._fixup_anycast_gw_mac: "
    match += "Error translating ANYCAST_GW_MAC for fabric f1, "
    match += r"ANYCAST_GW_MAC: 00\.54, Error detail: Invalid MAC address"
    with pytest.raises(ValueError, match=match):
        instance._fixup_payloads_to_commit()


MATCH_00021a = r"FabricCommon\._fixup_bgp_as:\s+"
MATCH_00021a += r"Invalid BGP_AS .* for fabric f1,\s+"
MATCH_00021a += r"Error detail: BGP ASN .* failed regex validation\."

MATCH_00021b = r"FabricCommon\._fixup_bgp_as:\s+"
MATCH_00021b += r"Invalid BGP_AS .* for fabric f1,\s+"
MATCH_00021b += r"Error detail: BGP ASN \(.*\) cannot be type float\(\)\s+"
MATCH_00021b += r"due to loss of trailing zeros\.\s+"
MATCH_00021b += r"Use a string or integer instead\."


@pytest.mark.parametrize(
    "bgp_as, expected",
    [
        ("65001.65535", does_not_raise()),
        ("65001.0", does_not_raise()),
        ("65001", does_not_raise()),
        (65001, does_not_raise()),
        (4294967295, does_not_raise()),
        (0, pytest.raises(ValueError, match=MATCH_00021a)),
        (4294967296, pytest.raises(ValueError, match=MATCH_00021a)),
        ("FOOBAR", pytest.raises(ValueError, match=MATCH_00021a)),
        ("65001.65536", pytest.raises(ValueError, match=MATCH_00021a)),
        ("65001:65000", pytest.raises(ValueError, match=MATCH_00021a)),
        (65001.65000, pytest.raises(ValueError, match=MATCH_00021b)),
    ],
)
def test_fabric_common_00021(fabric_common, bgp_as, expected) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _fixup_payloads_to_commit()
        - _fixup_bgp_as()

    Summary
    - Verify ``ValueError`` is raised when BGP_AS fails regex validation.
    """
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
        instance._payloads_to_commit = [
            {"BGP_AS": bgp_as, "FABRIC_NAME": "f1", "FABRIC_TYPE": "VXLAN_EVPN"}
        ]
    with expected:
        instance._fixup_payloads_to_commit()


@pytest.mark.parametrize(
    "value, expected_return_value",
    [
        ("", None),
        ("null", None),
        ("Null", None),
        ("NULL", None),
        ("none", None),
        ("None", None),
        ("NONE", None),
        (None, None),
        (10, 10),
        ({"foo": "bar"}, {"foo": "bar"}),
        (["foo", "bar"], ["foo", "bar"]),
        (101.4, 101.4),
    ],
)
def test_fabric_common_00070(fabric_common, value, expected_return_value) -> None:
    """
    Classes and Methods
    - ConversionUtils
        - make_none()
    - FabricCommon
        - __init__()

    Summary
    -   Verify FabricCommon().conversion.make_none returns expected values.
    """
    with does_not_raise():
        instance = fabric_common
        return_value = instance.conversion.make_none(value)
    assert return_value == expected_return_value


@pytest.mark.parametrize(
    "value, expected_return_value",
    [
        (True, True),
        ("true", True),
        ("TRUE", True),
        ("yes", True),
        ("YES", True),
        (False, False),
        ("false", False),
        ("FALSE", False),
        ("no", False),
        ("NO", False),
        (10, 10),
        ({"foo": "bar"}, {"foo": "bar"}),
        (["foo", "bar"], ["foo", "bar"]),
        (101.4, 101.4),
    ],
)
def test_fabric_common_00080(fabric_common, value, expected_return_value) -> None:
    """
    Classes and Methods
    - ConversionUtils
        - make_boolean()
    - FabricCommon
        - __init__()
        - conversion.make_boolean()

    Summary
    -   Verify FabricCommon().conversion.make_boolean returns expected values.
    """
    with does_not_raise():
        instance = fabric_common
        return_value = instance.conversion.make_boolean(value)
    assert return_value == expected_return_value


def test_fabric_common_00100(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _verify_payload()

    Summary
    -   Verify ``ValueError`` is raised when payload is not a `dict``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_common(key)

    with does_not_raise():
        instance = fabric_common

    match = r"FabricCommon\._verify_payload:\s+"
    match += r"Playbook configuration for fabrics must be a dict\.\s+"
    match += r"Got type str, value NOT_A_DICT\."
    with pytest.raises(ValueError, match=match):
        instance.action = "fabric_create"
        instance._verify_payload(payload)


@pytest.mark.parametrize(
    "mandatory_key",
    [
        "BGP_AS",
        "FABRIC_NAME",
        "FABRIC_TYPE",
    ],
)
def test_fabric_common_00110(fabric_common, mandatory_key) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _verify_payload()

    Summary
    -   Verify ``ValueError`` is raised when payload is missing
        mandatory parameters.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_common(key)

    payload.pop(mandatory_key, None)

    with does_not_raise():
        instance = fabric_common
        instance.action = "fabric_create"

    match = r"FabricCommon\._verify_payload:\s+"
    match += r"Playbook configuration for fabric .* is missing mandatory\s+"
    match += r"parameter.*\."
    with pytest.raises(ValueError, match=match):
        instance._verify_payload(payload)


def test_fabric_common_00111(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _verify_payload()

    Summary
    -   Verify FabricCommon()_verify_payload() returns if action
        is not one of "fabric_create" or "fabric_replace".

    NOTES:
    -   Since action == "foo", FabricCommon()._verify_payload() does not
        reach its validation checks and so does not raise ``ValueError``
        when its input parameter is the wrong type (str vs dict).
    """
    with does_not_raise():
        instance = fabric_common
        instance.action = "foo"
        instance._verify_payload("NOT_A_DICT")


MATCH_00112a = r"FabricCommon\._verify_payload:\s+"
MATCH_00112a += r"Playbook configuration for fabric .* contains an invalid\s+"
MATCH_00112a += r"FABRIC_NAME\.\s+"
MATCH_00112a += r"Error detail: ConversionUtils\.validate_fabric_name:\s+"
MATCH_00112a += r"Invalid fabric name:\s+.*\.\s+"
MATCH_00112a += r"Fabric name must start with a letter A-Z or a-z and\s+"
MATCH_00112a += r"contain only the characters in: \[A-Z,a-z,0-9,-,_\]\.\s+"
MATCH_00112a += r"Bad configuration:.*"


MATCH_00112b = r"FabricCommon\._verify_payload:\s+"
MATCH_00112b += r"Playbook configuration for fabric .* contains an invalid\s+"
MATCH_00112b += r"FABRIC_NAME\.\s+"
MATCH_00112b += r"Error detail: ConversionUtils\.validate_fabric_name:\s+"
MATCH_00112b += r"Invalid fabric name\. Expected string. Got .*\.\s+"
MATCH_00112b += r"Bad configuration:.*"


@pytest.mark.parametrize(
    "fabric_name, expected",
    [
        ("MyFabric", does_not_raise()),
        ("My_Fabric", does_not_raise()),
        ("My-Fabric-66", does_not_raise()),
        (0, pytest.raises(ValueError, match=MATCH_00112b)),
        (100.100, pytest.raises(ValueError, match=MATCH_00112b)),
        ("10_MyFabric", pytest.raises(ValueError, match=MATCH_00112a)),
        ("My:Fabric", pytest.raises(ValueError, match=MATCH_00112a)),
        ("My,Fabric", pytest.raises(ValueError, match=MATCH_00112a)),
        ("@MyFabric", pytest.raises(ValueError, match=MATCH_00112a)),
    ],
)
def test_fabric_common_00112(fabric_common, fabric_name, expected) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _verify_payload()

    Summary
    - Verify ``ValueError`` is raised when FABRIC_NAME fails regex validation.
    """
    payload = {
        "BGP_AS": "65000.100",
        "FABRIC_NAME": fabric_name,
        "FABRIC_TYPE": "VXLAN_EVPN",
    }

    with does_not_raise():
        instance = fabric_common
        instance.action = "fabric_create"
        instance.results = Results()
    with expected:
        instance._verify_payload(payload)


MATCH_00113a = r"FabricCommon\._verify_payload:\s+"
MATCH_00113a += r"Playbook configuration for fabric .* contains an invalid\s+"
MATCH_00113a += r"FABRIC_TYPE\s+\(.*\)\.\s+"
MATCH_00113a += r"Valid values for FABRIC_TYPE:\s+"
MATCH_00113a += r"\[.*]\.\s+"
MATCH_00113a += r"Bad configuration:\s+"


@pytest.mark.parametrize(
    "fabric_type, expected",
    [
        ("LAN_CLASSIC", does_not_raise()),
        ("VXLAN_EVPN", does_not_raise()),
        ("VXLAN_EVPN_MSD", does_not_raise()),
        (0, pytest.raises(ValueError, match=MATCH_00113a)),
        ("FOOBAR", pytest.raises(ValueError, match=MATCH_00113a)),
    ],
)
def test_fabric_common_00113(fabric_common, fabric_type, expected) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _verify_payload()

    Summary
    - Verify ``ValueError`` is raised when FABRIC_TYPE is invalid.
    """
    payload = {
        "BGP_AS": "65000.100",
        "FABRIC_NAME": "MyFabric",
        "FABRIC_TYPE": fabric_type,
    }

    with does_not_raise():
        instance = fabric_common
        instance.action = "fabric_create"
        instance.results = Results()
    with expected:
        instance._verify_payload(payload)


MATCH_00120a = r"FabricCommon\.translate_anycast_gw_mac:\s+"
MATCH_00120a += r"Error translating ANYCAST_GW_MAC: for fabric MyFabric,\s+"
MATCH_00120a += r"ANYCAST_GW_MAC: .*, Error detail: Invalid MAC address:\s+.*"


@pytest.mark.parametrize(
    "mac_in, mac_out, raises, expected",
    [
        ("0001aabbccdd", "0001.aabb.ccdd", False, does_not_raise()),
        ("00:01:aa:bb:cc:dd", "0001.aabb.ccdd", False, does_not_raise()),
        ("00:---01:***aa:b//b:cc:dd", "0001.aabb.ccdd", False, does_not_raise()),
        ("00zz.aabb.ccdd", None, True, pytest.raises(ValueError, match=MATCH_00120a)),
        ("0001", None, True, pytest.raises(ValueError, match=MATCH_00120a)),
    ],
)
def test_fabric_common_00120(fabric_common, mac_in, mac_out, raises, expected) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
        - translate_anycast_gw_mac()

    Summary
    -   Verify FabricCommon().translate_anycast_gw_mac()
        raises ``ValueError`` if mac_in cannot be translated into a format
        expected by the controller.
    -   Verify the error message when ``ValueError`` is raised.
    -   Verify ``ValueError`` is not raised when ANYCAST_GW_MAC can be
        translated.
    """
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
    with expected:
        result = instance.translate_anycast_gw_mac("MyFabric", mac_in)
    if raises is False:
        assert result == mac_out
