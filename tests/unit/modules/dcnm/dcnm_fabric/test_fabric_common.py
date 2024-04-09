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

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary
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
    assert instance.state == "merged"
    assert instance.check_mode is False
    assert len(instance._valid_fabric_types) == 1
    assert "VXLAN_EVPN" in instance._valid_fabric_types
    assert instance.fabric_type_to_template_name_map["VXLAN_EVPN"] == "Easy_Fabric"
    assert instance._properties["fabric_details"] is None
    assert instance._properties["fabric_summary"] is None
    assert instance._properties["fabric_type"] == "VXLAN_EVPN"
    assert instance._properties["rest_send"] is None
    assert instance._properties["results"] is None


def test_fabric_common_00011() -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()

    Summary
    - Verify ``ValueError`` is raised when check_mode is missing from params
    """
    params_test = copy.deepcopy(params)
    params_test.pop("check_mode", None)
    match = r"FabricCommon\.__init__\(\): check_mode is required"
    with pytest.raises(ValueError, match=match):
        FabricCommon(params_test)


def test_fabric_common_00012() -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()

    Summary
    - Verify ``ValueError`` is raised when state is missing from params
    """
    params_test = copy.deepcopy(params)
    params_test.pop("state", None)
    match = r"FabricCommon\.__init__\(\): state is required"
    with pytest.raises(ValueError, match=match):
        FabricCommon(params_test)


def test_fabric_common_00020(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _fixup_payloads_to_commit()

    Summary
    - Verify ``ValueError`` is raised when ANYCAST_GW_MAC is malformed.
    """
    key = "test_fabric_create_bulk_00020a"
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
        instance._payloads_to_commit = payloads_fabric_common(key)
    match = r"FabricCommon\._fixup_payloads_to_commit: "
    match += "Error translating ANYCAST_GW_MAC for fabric f1, "
    match += r"ANYCAST_GW_MAC: 00\.54, Error detail: Invalid MAC address"
    with pytest.raises(ValueError, match=match):
        instance._fixup_payloads_to_commit()


def test_fabric_common_00030(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _handle_response()
        - _handle_unknown_request_verbs()

    Summary
    - Verify ``ValueError`` is raised when request verb is unknown.
    """
    key = "test_fabric_common_00030a"
    response = responses_fabric_common(key)
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
    match = r"FabricCommon\._handle_unknown_request_verbs: "
    match += r"Unknown request verb \(FOO\) for response"
    with pytest.raises(ValueError, match=match):
        instance._handle_response(response, response.get("METHOD", None))


def test_fabric_common_00040(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _handle_response()
        - _handle_get_response()

    Summary
    -   Verify _handle_get_response() for:
        -   MESSAGE: "Not Found"
        -   METHOD: GET
        -   RETURN_CODE: 404

    Test
    - Verify ``ValueError`` is not raised
    - Verify ``result`` values are as expected
    """
    key = "test_fabric_common_00040a"
    response = responses_fabric_common(key)
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
        result = instance._handle_response(response, response.get("METHOD", None))
    assert result.get("found") is False
    assert result.get("success") is True


def test_fabric_common_00041(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _handle_response()
        - _handle_get_response()

    Summary
    -   Verify _handle_get_response() for:
        -   MESSAGE: don't care
        -   METHOD: GET
        -   RETURN_CODE: 500 (not in {200, 404})

    Test
    - Verify ``ValueError`` is not raised
    - Verify ``result`` values are as expected
    """
    key = "test_fabric_common_00041a"
    response = responses_fabric_common(key)
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
        result = instance._handle_response(response, response.get("METHOD", None))
    assert result.get("found") is False
    assert result.get("success") is False


def test_fabric_common_00042(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _handle_response()
        - _handle_get_response()

    Summary
    -   Verify _handle_get_response() for:
        -   MESSAGE: "ERROR" (!= "OK")
        -   METHOD: GET
        -   RETURN_CODE: 200 (don't care)

    Test
    - Verify ``ValueError`` is not raised
    - Verify ``result`` values are as expected
    """
    key = "test_fabric_common_00042a"
    response = responses_fabric_common(key)
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
        result = instance._handle_response(response, response.get("METHOD", None))
    assert result.get("found") is False
    assert result.get("success") is False


def test_fabric_common_00043(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _handle_response()
        - _handle_get_response()

    Summary
    -   Verify _handle_get_response() for:
        -   MESSAGE: "OK"
        -   METHOD: GET
        -   RETURN_CODE: 200

    Test
    - Verify ``ValueError`` is not raised
    - Verify ``result`` values are as expected
    """
    key = "test_fabric_common_00043a"
    response = responses_fabric_common(key)
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
        result = instance._handle_response(response, response.get("METHOD", None))
    assert result.get("found") is True
    assert result.get("success") is True


def test_fabric_common_00050(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _handle_response()
        - _handle_post_put_delete_response()

    Summary
    -   Verify _handle_post_put_delete_response() for:
        -   ERROR: key is present
        -   MESSAGE: "OK" (don't care)
        -   METHOD: POST
        -   RETURN_CODE: 200 (don't care)

    Test
    - Verify ``ValueError`` is not raised
    - Verify ``result`` values are as expected
    """
    key = "test_fabric_common_00050a"
    response = responses_fabric_common(key)
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
        result = instance._handle_response(response, response.get("METHOD", None))
    assert result.get("changed") is False
    assert result.get("success") is False


def test_fabric_common_00051(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _handle_response()
        - _handle_post_put_delete_response()

    Summary
    -   Verify _handle_post_put_delete_response() for:
        -   ERROR: not present (don't care)
        -   MESSAGE: "NOK" (!= OK)
        -   METHOD: POST
        -   RETURN_CODE: 200 (don't care)

    Test
    - Verify ``ValueError`` is not raised
    - Verify ``result`` values are as expected
    """
    key = "test_fabric_common_00051a"
    response = responses_fabric_common(key)
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
        result = instance._handle_response(response, response.get("METHOD", None))
    assert result.get("changed") is False
    assert result.get("success") is False


def test_fabric_common_00052(fabric_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - _handle_response()
        - _handle_post_put_delete_response()

    Summary
    -   Verify _handle_post_put_delete_response() for:
        -   ERROR: not present
        -   MESSAGE: "OK"
        -   METHOD: POST
        -   RETURN_CODE: don't care

    Test
    - Verify ``ValueError`` is not raised
    - Verify ``result`` values are as expected
    """
    key = "test_fabric_common_00052a"
    response = responses_fabric_common(key)
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
        result = instance._handle_response(response, response.get("METHOD", None))
    assert result.get("changed") is True
    assert result.get("success") is True


MATCH_00060a = r"FabricCommon\.fabric_type_to_template_name: "
MATCH_00060a += "Unknown fabric type:"


@pytest.mark.parametrize(
    "fabric_type, expected_template_name, result",
    [
        ("VXLAN_EVPN", "Easy_Fabric", does_not_raise()),
        ("UNKNOWN", None, pytest.raises(ValueError, match=MATCH_00060a)),
    ],
)
def test_fabric_common_00060(
    fabric_common, fabric_type, expected_template_name, result
) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - fabric_type_to_template_name()

    Summary
    -   Verify fabric_type_to_template_name() behavior for:
        -   Valid fabric_type
        -   Invalid fabric_type

    Test
    - Verify ``ValueError`` is not raised given valid fabric_type
    - Verify expected template name is returned given valid fabric_type
    - Verify ``ValueError`` is raised given invalid fabric_type
    """
    with does_not_raise():
        instance = fabric_common
        instance.results = Results()
    template_name = None
    with result:
        template_name = instance.fabric_type_to_template_name(fabric_type)
    assert template_name == expected_template_name


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
def test_fabric_common_00070(
    fabric_common, value, expected_return_value) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - make_none()

    Summary
    -   Verify expected values are returned:
    """
    with does_not_raise():
        instance = fabric_common
        return_value = instance.make_none(value)
    assert return_value == expected_return_value

