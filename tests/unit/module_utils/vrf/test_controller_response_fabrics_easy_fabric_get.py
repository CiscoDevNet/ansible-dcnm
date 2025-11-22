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
"""
Test cases for ControllerResponseFabricsEasyFabricGet.
"""
from functools import partial

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.vrf.model_controller_response_fabrics_easy_fabric_get import ControllerResponseFabricsEasyFabricGet

from ..common.common_utils import does_not_raise
from .fixtures.load_fixture import controller_response_fabrics_easy_fabric_get


# pylint: disable=too-many-arguments
def base_test_fabric(value, expected, valid: bool, field: str):
    """
    Base test function called by other tests to validate the model.

    :param value: Field value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    :param field: The field in the response to modify.
    """
    response = controller_response_fabrics_easy_fabric_get("fabric_get")
    if value == "MISSING":
        response.pop(field, None)
    else:
        response[field] = value

    if valid:
        with does_not_raise():
            instance = ControllerResponseFabricsEasyFabricGet(**response)
            if value != "MISSING":
                assert getattr(instance, field) == expected
            else:
                # Check if field has a default value
                field_info = ControllerResponseFabricsEasyFabricGet.model_fields.get(field)
                if field_info and field_info.default is not None:
                    assert getattr(instance, field) == field_info.default
    else:
        with pytest.raises(ValueError):
            ControllerResponseFabricsEasyFabricGet(**response)


# pylint: enable=too-many-arguments

# Create partial functions for common test patterns
base_test_string_field = partial(base_test_fabric)
base_test_int_field = partial(base_test_fabric)


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("65001", "65001", True),  # OK, string
        ("12345", "12345", True),  # OK, string
        ("", "", False),  # NOK, min_length=1
        ("MISSING", None, False),  # NOK, required field
        (123, 123, False),  # NOK, int (should be string)
    ],
)
def test_fabrics_easy_fabric_get_asn(value, expected, valid: bool) -> None:
    """
    asn field validation
    """
    base_test_string_field(value, expected, valid, field="asn")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        (1750784465087, 1750784465087, True),  # OK, int
        (0, 0, True),  # OK, int
        ("123", 123, True),  # OK, string is coerced to int
        ("MISSING", None, False),  # NOK, required field
        (None, None, False),  # NOK, None not allowed
    ],
)
def test_fabrics_easy_fabric_get_created_on(value, expected, valid: bool) -> None:
    """
    createdOn field validation
    """
    base_test_int_field(value, expected, valid, field="createdOn")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("n9k", "n9k", True),  # OK, string
        ("n7k", "n7k", True),  # OK, string
        ("MISSING", None, False),  # NOK, required field
        ("", "", True),  # OK, empty string
        (123, 123, False),  # NOK, int (should be string)
    ],
)
def test_fabrics_easy_fabric_get_device_type(value, expected, valid: bool) -> None:
    """
    deviceType field validation
    """
    base_test_string_field(value, expected, valid, field="deviceType")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("FABRIC-2", "FABRIC-2", True),  # OK, string
        ("FABRIC-1", "FABRIC-1", True),  # OK, string
        ("MISSING", None, False),  # NOK, required field
        ("", "", True),  # OK, empty string
        (123, 123, False),  # NOK, int (should be string)
    ],
)
def test_fabrics_easy_fabric_get_fabric_id(value, expected, valid: bool) -> None:
    """
    fabricId field validation
    """
    base_test_string_field(value, expected, valid, field="fabricId")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("f1", "f1", True),  # OK, string
        ("my-fabric", "my-fabric", True),  # OK, string
        ("MISSING", None, False),  # NOK, required field
        ("", "", True),  # OK, empty string
        (123, 123, False),  # NOK, int (should be string)
    ],
)
def test_fabrics_easy_fabric_get_fabric_name(value, expected, valid: bool) -> None:
    """
    fabricName field validation
    """
    base_test_string_field(value, expected, valid, field="fabricName")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("VXLANFabric", "VXLANFabric", True),  # OK, string
        ("LANClassic", "LANClassic", True),  # OK, string
        ("MISSING", None, False),  # NOK, required field
        ("", "", True),  # OK, empty string
        (123, 123, False),  # NOK, int (should be string)
    ],
)
def test_fabrics_easy_fabric_get_fabric_technology(value, expected, valid: bool) -> None:
    """
    fabricTechnology field validation
    """
    base_test_string_field(value, expected, valid, field="fabricTechnology")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        (2, 2, True),  # OK, int
        (100, 100, True),  # OK, int
        ("2", 2, True),  # OK, string is coerced to int
        ("MISSING", None, False),  # NOK, required field
        (None, None, False),  # NOK, None not allowed
    ],
)
def test_fabrics_easy_fabric_get_id(value, expected, valid: bool) -> None:
    """
    id field validation
    """
    base_test_int_field(value, expected, valid, field="id")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("Default_Network_Extension_Universal", "Default_Network_Extension_Universal", True),  # OK, default value
        ("Custom_Network_Extension", "Custom_Network_Extension", True),  # OK, custom value
        ("MISSING", "Default_Network_Extension_Universal", True),  # OK, uses default
        ("", "", True),  # OK, empty string
    ],
)
def test_fabrics_easy_fabric_get_network_extension_template(value, expected, valid: bool) -> None:
    """
    networkExtensionTemplate field validation
    """
    base_test_string_field(value, expected, valid, field="networkExtensionTemplate")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("Default_Network_Universal", "Default_Network_Universal", True),  # OK, default value
        ("Custom_Network", "Custom_Network", True),  # OK, custom value
        ("MISSING", "Default_Network_Universal", True),  # OK, uses default
        ("", "", True),  # OK, empty string
    ],
)
def test_fabrics_easy_fabric_get_network_template(value, expected, valid: bool) -> None:
    """
    networkTemplate field validation
    """
    base_test_string_field(value, expected, valid, field="networkTemplate")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("MINOR", "MINOR", True),  # OK, string
        ("MAJOR", "MAJOR", True),  # OK, string
        ("MISSING", None, False),  # NOK, required field
        ("", "", True),  # OK, empty string
        (123, 123, False),  # NOK, int (should be string)
    ],
)
def test_fabrics_easy_fabric_get_oper_status(value, expected, valid: bool) -> None:
    """
    operStatus field validation
    """
    base_test_string_field(value, expected, valid, field="operStatus")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("DCNMTopDown", "DCNMTopDown", True),  # OK, string
        ("External", "External", True),  # OK, string
        ("MISSING", None, False),  # NOK, required field
        ("", "", True),  # OK, empty string
        (123, 123, False),  # NOK, int (should be string)
    ],
)
def test_fabrics_easy_fabric_get_provision_mode(value, expected, valid: bool) -> None:
    """
    provisionMode field validation
    """
    base_test_string_field(value, expected, valid, field="provisionMode")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("Default_VRF_Extension_Universal", "Default_VRF_Extension_Universal", True),  # OK, default value
        ("Custom_VRF_Extension", "Custom_VRF_Extension", True),  # OK, custom value
        ("MISSING", "Default_VRF_Extension_Universal", True),  # OK, uses default
        ("", "", False),  # NOK, min_length=1
    ],
)
def test_fabrics_easy_fabric_get_vrf_extension_template(value, expected, valid: bool) -> None:
    """
    vrfExtensionTemplate field validation
    """
    base_test_string_field(value, expected, valid, field="vrfExtensionTemplate")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("Default_VRF_Universal", "Default_VRF_Universal", True),  # OK, default value
        ("Custom_VRF", "Custom_VRF", True),  # OK, custom value
        ("MISSING", "Default_VRF_Universal", True),  # OK, uses default
        ("", "", False),  # NOK, min_length=1
    ],
)
def test_fabrics_easy_fabric_get_vrf_template(value, expected, valid: bool) -> None:
    """
    vrfTemplate field validation
    """
    base_test_string_field(value, expected, valid, field="vrfTemplate")


def test_fabrics_easy_fabric_get_full_response() -> None:
    """
    Test ControllerResponseFabricsEasyFabricGet with full controller response.
    """
    response = controller_response_fabrics_easy_fabric_get("fabric_get")
    with does_not_raise():
        instance: ControllerResponseFabricsEasyFabricGet = ControllerResponseFabricsEasyFabricGet(**response)
    # Verify some key fields are populated correctly
    assert instance.asn == "65001"
    assert instance.fabricName == "f1"
    assert instance.deviceType == "n9k"
    assert instance.id == 2
    assert instance.operStatus == "MINOR"
    assert instance.nvPairs is not None
    assert instance.nvPairs.BGP_AS == "65001"  # pylint: disable=no-member


def test_fabrics_easy_fabric_get_missing_nvpairs() -> None:
    """
    Test ControllerResponseFabricsEasyFabricGet fails when nvPairs is missing.
    """
    response = controller_response_fabrics_easy_fabric_get("fabric_get")
    response.pop("nvPairs", None)

    with pytest.raises(ValueError):
        ControllerResponseFabricsEasyFabricGet(**response)


def test_fabrics_easy_fabric_get_invalid_nvpairs() -> None:
    """
    Test ControllerResponseFabricsEasyFabricGet fails when nvPairs is invalid.
    """
    response = controller_response_fabrics_easy_fabric_get("fabric_get")
    response["nvPairs"] = "invalid"

    with pytest.raises(ValueError):
        ControllerResponseFabricsEasyFabricGet(**response)
