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
Test cases for ControllerResponseFabricsEasyFabricGetNvPairs.
"""
from functools import partial

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.vrf.model_controller_response_fabrics_easy_fabric_get import (
    ControllerResponseFabricsEasyFabricGetNvPairs,
)

from ..common.common_utils import does_not_raise
from .fixtures.load_fixture import controller_response_fabrics_easy_fabric_get


# pylint: disable=too-many-arguments
def base_test_nvpairs(value, expected, valid: bool, field: str):
    """
    Base test function called by other tests to validate the model.

    :param value: Field value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    :param field: The field in the response to modify.
    """
    response = controller_response_fabrics_easy_fabric_get("fabric_get_nvpairs")
    if value == "MISSING":
        response.pop(field, None)
    else:
        response[field] = value

    if valid:
        with does_not_raise():
            instance = ControllerResponseFabricsEasyFabricGetNvPairs(**response)
            if value != "MISSING":
                assert getattr(instance, field) == expected
            else:
                # All fields except BGP_AS and FABRIC_NAME are Optional[str] with default None
                if field in ["BGP_AS", "FABRIC_NAME"]:
                    # These are required fields, so test should fail if missing
                    assert False, f"Required field {field} should not be missing"
                else:
                    assert getattr(instance, field) is None
    else:
        with pytest.raises(ValueError):
            ControllerResponseFabricsEasyFabricGetNvPairs(**response)


# pylint: enable=too-many-arguments

# Create partial functions for common test patterns
base_test_string_field = partial(base_test_nvpairs)


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
def test_fabrics_easy_fabric_get_nv_pairs_bgp_as(value, expected, valid: bool) -> None:
    """
    BGP_AS field validation (required field with min_length=1)
    """
    base_test_string_field(value, expected, valid, field="BGP_AS")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("f1", "f1", True),  # OK, string
        ("my-fabric", "my-fabric", True),  # OK, string
        ("", "", True),  # OK, empty string
        ("MISSING", None, False),  # NOK, required field
        (123, 123, False),  # NOK, int (should be string)
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_fabric_name(value, expected, valid: bool) -> None:
    """
    FABRIC_NAME field validation (required field)
    """
    base_test_string_field(value, expected, valid, field="FABRIC_NAME")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("true", "true", True),  # OK, string
        ("false", "false", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (True, True, False),  # NOK, bool (should be string)
        (False, False, False),  # NOK, bool (should be string)
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_enable_evpn(value, expected, valid: bool) -> None:
    """
    ENABLE_EVPN field validation
    """
    base_test_string_field(value, expected, valid, field="ENABLE_EVPN")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("9216", "9216", True),  # OK, string
        ("1500", "1500", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (9216, 9216, False),  # NOK, int (should be string)
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_fabric_mtu(value, expected, valid: bool) -> None:
    """
    FABRIC_MTU field validation
    """
    base_test_string_field(value, expected, valid, field="FABRIC_MTU")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("10.2.0.0/22", "10.2.0.0/22", True),  # OK, string
        ("192.168.1.0/24", "192.168.1.0/24", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_loopback0_ip_range(value, expected, valid: bool) -> None:
    """
    LOOPBACK0_IP_RANGE field validation
    """
    base_test_string_field(value, expected, valid, field="LOOPBACK0_IP_RANGE")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("ospf", "ospf", True),  # OK, string
        ("isis", "isis", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_link_state_routing(value, expected, valid: bool) -> None:
    """
    LINK_STATE_ROUTING field validation
    """
    base_test_string_field(value, expected, valid, field="LINK_STATE_ROUTING")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("2020.0000.00aa", "2020.0000.00aa", True),  # OK, string
        ("0000.1111.2222", "0000.1111.2222", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_anycast_gw_mac(value, expected, valid: bool) -> None:
    """
    ANYCAST_GW_MAC field validation
    """
    base_test_string_field(value, expected, valid, field="ANYCAST_GW_MAC")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("2000-2299", "2000-2299", True),  # OK, string
        ("100-200", "100-200", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_vrf_vlan_range(value, expected, valid: bool) -> None:
    """
    VRF_VLAN_RANGE field validation
    """
    base_test_string_field(value, expected, valid, field="VRF_VLAN_RANGE")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("Default_VRF_Universal", "Default_VRF_Universal", True),  # OK, string
        ("Custom_VRF_Template", "Custom_VRF_Template", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_default_vrf(value, expected, valid: bool) -> None:
    """
    default_vrf field validation
    """
    base_test_string_field(value, expected, valid, field="default_vrf")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("admin", "admin", True),  # OK, string
        ("operator", "operator", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_dcnm_user(value, expected, valid: bool) -> None:
    """
    dcnmUser field validation
    """
    base_test_string_field(value, expected, valid, field="dcnmUser")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("0.0.0.0", "0.0.0.0", True),  # OK, string
        ("192.168.1.0", "192.168.1.0", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_ospf_area_id(value, expected, valid: bool) -> None:
    """
    OSPF_AREA_ID field validation
    """
    base_test_string_field(value, expected, valid, field="OSPF_AREA_ID")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("Ingress", "Ingress", True),  # OK, string
        ("Multicast", "Multicast", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_replication_mode(value, expected, valid: bool) -> None:
    """
    REPLICATION_MODE field validation
    """
    base_test_string_field(value, expected, valid, field="REPLICATION_MODE")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("65001", "65001", True),  # OK, string
        ("65002", "65002", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_site_id(value, expected, valid: bool) -> None:
    """
    SITE_ID field validation
    """
    base_test_string_field(value, expected, valid, field="SITE_ID")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("10.4.0.0/16", "10.4.0.0/16", True),  # OK, string
        ("192.168.0.0/24", "192.168.0.0/24", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_subnet_range(value, expected, valid: bool) -> None:
    """
    SUBNET_RANGE field validation
    """
    base_test_string_field(value, expected, valid, field="SUBNET_RANGE")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("30", "30", True),  # OK, string
        ("24", "24", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_subnet_target_mask(value, expected, valid: bool) -> None:
    """
    SUBNET_TARGET_MASK field validation
    """
    base_test_string_field(value, expected, valid, field="SUBNET_TARGET_MASK")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("Default_Network_Extension_Universal", "Default_Network_Extension_Universal", True),  # OK, string
        ("Custom_Network_Extension", "Custom_Network_Extension", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_network_extension_template(value, expected, valid: bool) -> None:
    """
    network_extension_template field validation
    """
    base_test_string_field(value, expected, valid, field="network_extension_template")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("Default_VRF_Extension_Universal", "Default_VRF_Extension_Universal", True),  # OK, string
        ("Custom_VRF_Extension", "Custom_VRF_Extension", True),  # OK, string
        ("MISSING", None, True),  # OK, field can be missing
        ("", "", True),  # OK, empty string
        (None, None, True),  # OK, None is valid for optional field
    ],
)
def test_fabrics_easy_fabric_get_nv_pairs_vrf_extension_template(value, expected, valid: bool) -> None:
    """
    vrf_extension_template field validation
    """
    base_test_string_field(value, expected, valid, field="vrf_extension_template")


def test_fabrics_easy_fabric_get_nv_pairs_full_response() -> None:
    """
    Test ControllerResponseFabricsEasyFabricGetNvPairs with full controller response.
    """
    response = controller_response_fabrics_easy_fabric_get("fabric_get_nvpairs")
    with does_not_raise():
        instance = ControllerResponseFabricsEasyFabricGetNvPairs(**response)
    # Verify some key fields are populated correctly
    assert instance.BGP_AS == "65001"
    assert instance.FABRIC_NAME == "f1"
    assert instance.ENABLE_EVPN == "true"
    assert instance.FABRIC_MTU == "9216"
    assert instance.LOOPBACK0_IP_RANGE == "10.2.0.0/22"
    assert instance.LINK_STATE_ROUTING == "ospf"
    assert instance.ANYCAST_GW_MAC == "2020.0000.00aa"
    assert instance.VRF_VLAN_RANGE == "2000-2299"
    assert instance.default_vrf == "Default_VRF_Universal"
    assert instance.dcnmUser == "admin"


def test_fabrics_easy_fabric_get_nv_pairs_missing_required_bgp_as() -> None:
    """
    Test ControllerResponseFabricsEasyFabricGetNvPairs fails when BGP_AS is missing.
    """
    response = controller_response_fabrics_easy_fabric_get("fabric_get_nvpairs")
    response.pop("BGP_AS", None)

    with pytest.raises(ValueError):
        ControllerResponseFabricsEasyFabricGetNvPairs(**response)


def test_fabrics_easy_fabric_get_nv_pairs_missing_required_fabric_name() -> None:
    """
    Test ControllerResponseFabricsEasyFabricGetNvPairs fails when FABRIC_NAME is missing.
    """
    response = controller_response_fabrics_easy_fabric_get("fabric_get_nvpairs")
    response.pop("FABRIC_NAME", None)

    with pytest.raises(ValueError):
        ControllerResponseFabricsEasyFabricGetNvPairs(**response)


def test_fabrics_easy_fabric_get_nv_pairs_invalid_bgp_as_empty() -> None:
    """
    Test ControllerResponseFabricsEasyFabricGetNvPairs fails when BGP_AS is empty (violates min_length=1).
    """
    response = controller_response_fabrics_easy_fabric_get("fabric_get_nvpairs")
    response["BGP_AS"] = ""

    with pytest.raises(ValueError):
        ControllerResponseFabricsEasyFabricGetNvPairs(**response)


def test_fabrics_easy_fabric_get_nv_pairs_optional_fields_can_be_none() -> None:
    """
    Test that optional fields can be None or missing without causing validation errors.
    """
    response = controller_response_fabrics_easy_fabric_get("fabric_get_nvpairs")

    # Remove some optional fields
    optional_fields = ["ENABLE_EVPN", "FABRIC_MTU", "LOOPBACK0_IP_RANGE", "LINK_STATE_ROUTING", "ANYCAST_GW_MAC", "VRF_VLAN_RANGE", "default_vrf", "dcnmUser"]

    for field in optional_fields:
        response.pop(field, None)

    with does_not_raise():
        instance = ControllerResponseFabricsEasyFabricGetNvPairs(**response)
        # Verify optional fields default to None
        for field in optional_fields:
            assert getattr(instance, field) is None


def test_fabrics_easy_fabric_get_nv_pairs_with_minimal_data() -> None:
    """
    Test ControllerResponseFabricsEasyFabricGetNvPairs with only required fields.
    """
    minimal_response = {"BGP_AS": "65001", "FABRIC_NAME": "test-fabric"}

    with does_not_raise():
        instance = ControllerResponseFabricsEasyFabricGetNvPairs(**minimal_response)
        assert instance.BGP_AS == "65001"
        assert instance.FABRIC_NAME == "test-fabric"
        # All other fields should be None
        assert instance.ENABLE_EVPN is None
        assert instance.FABRIC_MTU is None
        assert instance.dcnmUser is None
