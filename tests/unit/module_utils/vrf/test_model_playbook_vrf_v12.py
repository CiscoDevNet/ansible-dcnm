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
Test cases for PlaybookVrfModelV12 and PlaybookVrfConfigModelV12.
"""
from functools import partial
from typing import Union

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.enums.bgp import BgpPasswordEncrypt
from ansible_collections.cisco.dcnm.plugins.module_utils.vrf.model_playbook_vrf_v12 import (
    PlaybookVrfAttachModel,
    PlaybookVrfConfigModelV12,
    PlaybookVrfLiteModel,
    PlaybookVrfModelV12,
)

from ..common.common_utils import does_not_raise
from .fixtures.load_fixture import playbooks

bool_tests = [
    (True, True, True),  # OK, bool
    (False, False, True),  # OK, bool. TODO: This should not fail.
    (1, None, False),  # NOK, type is set to StrictBoolean in the model with allows only True or False
    (0, None, False),  # NOK, type is set to StrictBoolean in the model with allows only True or False
    ("abc", None, False),  # NOK, type is set to StrictBoolean in the model with allows only True or False
]
bool_tests_missing_default_true = bool_tests + [
    ("MISSING", True, True),  # OK, field can be missing. Default is True.
]
bool_tests_missing_default_false = bool_tests + [
    ("MISSING", False, True),  # OK, field can be missing. Default is False.
]

ipv4_addr_host_tests = [
    ("10.1.1.1", "10.1.1.1", True),
    ("168.1.1.1", "168.1.1.1", True),
    ("172.1.1.1", "172.1.1.1", True),
    # ("255.255.255.255/30", None, False), TODO: this should not be valid, but currently is
    ("10.1.1.1/24", "10.1.1.1/24", False),
    ("168.1.1.1/30", "168.1.1.1/30", False),
    ("172.1.1.1/30", "172.1.1.1/30", False),
    ("172.1.1.", None, False),
    ("2010::10:34:0:7", None, False),
    ("2010::10:34:0:7/64", None, False),
    (1, None, False),
    ("abc", None, False),
]

ipv4_addr_cidr_tests = [
    ("10.1.1.1/24", "10.1.1.1/24", True),
    ("168.1.1.1/30", "168.1.1.1/30", True),
    ("172.1.1.1/30", "172.1.1.1/30", True),
    ("MISSING", "", True),  # OK, field can be missing. Default is "".
    # ("255.255.255.255/30", None, False), TODO: this should not be valid, but currently is
    ("172.1.1.", None, False),
    ("255.255.255.255", None, False),
    ("2010::10:34:0:7", None, False),
    ("2010::10:34:0:7/64", None, False),
    (1, None, False),
    ("abc", None, False),
]

ipv4_multicast_group_tests = [
    ("224.1.1.1", "224.1.1.1", True),
    ("MISSING", "", True),  # OK, field can be missing. Default is "".
    ("10.1.1.1", None, False),
    (3, 3, False),  # NOK, int
    (None, None, False),  # NOK, None is not a valid value
]

ipv6_addr_host_tests = [
    ("2010::10:34:0:7", "2010::10:34:0:7", True),
    ("2010:10::7", "2010:10::7", True),
    ("2010::10:34:0:7/64", "2010::10:34:0:7/64", False),
    ("2010::10::7/128", "2010::10::7/128", False),
    ("172.1.1.1/30", None, False),
    ("172.1.1.1", None, False),
    ("255.255.255.255", None, False),
    (1, None, False),
    ("abc", None, False),
]

ipv6_addr_cidr_tests = [
    ("2010::10:34:0:7/64", "2010::10:34:0:7/64", True),
    ("2010::10::7/128", "2010::10::7/128", True),
    ("2010:10::7", None, False),
    ("172.1.1.1/30", None, False),
    ("172.1.1.1", None, False),
    ("255.255.255.255", None, False),
    (1, None, False),
    ("abc", None, False),
]


# pylint: disable=too-many-arguments
def base_test(value, expected, valid: bool, field: str, key: str, model):
    """
    Base test function called by other tests to validate the model.

    :param value: vrf_model value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    :param field: The field in the playbook to modify.
    :param key: The key in the playbooks fixture to use.
    :param model: The model class to instantiate.
    """
    playbook = playbooks(key)
    if value == "MISSING":
        playbook.pop(field, None)
    else:
        playbook[field] = value

    if valid:
        with does_not_raise():
            instance = model(**playbook)
            if value != "MISSING":
                assert getattr(instance, field) == expected
            else:
                assert expected == model.model_fields[field].default
    else:
        with pytest.raises(ValueError):
            model(**playbook)


# pylint: enable=too-many-arguments


def test_full_config_00000() -> None:
    """
    Test PlaybookVrfConfigModelV12 with JSON representing the structure passed to a playbook.

    The remaining tests will use partial structures (e.g. vrf_lite, attach) for simplicity.
    """
    playbook = playbooks("playbook_full_config")
    with does_not_raise():
        instance = PlaybookVrfConfigModelV12(**playbook)
    assert instance.config[0].vrf_name == "ansible-vrf-int1"


base_test_vrf_name = partial(base_test, field="vrf_name", key="playbook_as_dict", model=PlaybookVrfModelV12)
base_test_vrf_lite = partial(base_test, key="vrf_lite", model=PlaybookVrfLiteModel)
base_test_attach = partial(base_test, key="vrf_attach", model=PlaybookVrfAttachModel)
base_test_vrf = partial(base_test, key="playbook_as_dict", model=PlaybookVrfModelV12)


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("ansible-vrf-int1", "ansible-vrf-int1", True),
        ("vrf_5678901234567890123456789012", "vrf_5678901234567890123456789012", True),  # Valid, exactly 32 characters
        (123, None, False),  # Invalid, int
        ("vrf_56789012345678901234567890123", None, False),  # Invalid, longer than 32 characters
    ],
)
def test_vrf_name_00000(value: Union[str, int], expected, valid: bool) -> None:
    """
    vrf_name
    """
    base_test_vrf_name(value, expected, valid)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("1", "1", True),
        ("4094", "4094", True),
        (1, "1", True),
        (4094, "4094", True),
        ("0", "", True),
        (0, "", True),
        ("4095", None, False),
        (4095, None, False),
        ("-1", None, False),
        ("abc", None, False),
    ],
)
def test_vrf_lite_00000(value, expected, valid: bool) -> None:
    """
    dot1q
    """
    base_test_vrf_lite(value, expected, valid, field="dot1q")


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("Ethernet1/1", "Ethernet1/1", True),
        ("Eth2/1", "Eth2/1", True),
        ("MISSING", None, False),
    ],
)
def test_vrf_lite_00010(value, expected, valid: bool) -> None:
    """
    interface
    """
    base_test_vrf_lite(value, expected, valid, field="interface")


@pytest.mark.parametrize("value, expected, valid", ipv4_addr_cidr_tests)
def test_vrf_lite_00020(value, expected, valid: bool) -> None:
    """
    ipv4_addr
    """
    base_test_vrf_lite(value, expected, valid, field="ipv4_addr")


@pytest.mark.parametrize("value, expected, valid", ipv6_addr_cidr_tests)
def test_vrf_lite_00030(value, expected, valid: bool) -> None:
    """
    ipv6_addr
    """
    base_test_vrf_lite(value, expected, valid, field="ipv6_addr")


@pytest.mark.parametrize("value, expected, valid", ipv4_addr_host_tests)
def test_vrf_lite_00040(value, expected, valid: bool) -> None:
    """
    neighbor_ipv4
    """
    base_test_vrf_lite(value, expected, valid, field="neighbor_ipv4")


@pytest.mark.parametrize("value, expected, valid", ipv6_addr_host_tests)
def test_vrf_lite_00050(value, expected, valid: bool) -> None:
    """
    neighbor_ipv6
    """
    base_test_vrf_lite(value, expected, valid, field="neighbor_ipv6")


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("ansible-vrf-int1", "ansible-vrf-int1", True),  # OK, valid VRF name
        ("vrf_5678901234567890123456789012", "vrf_5678901234567890123456789012", True),  # OK, exactly 32 characters
        ("", "", False),  # NOK, at least one character is required
        (123, None, False),  # NOK, int
        ("vrf_56789012345678901234567890123", None, False),  # NOK, longer than 32 characters
    ],
)
def test_vrf_lite_00060(value, expected, valid: bool) -> None:
    """
    peer_vrf
    """
    base_test_vrf_lite(value, expected, valid, field="peer_vrf")


# VRF Attach Tests


@pytest.mark.parametrize("value, expected, valid", bool_tests_missing_default_true)
def test_vrf_attach_00000(value, expected, valid: bool) -> None:
    """
    deploy
    """
    base_test_attach(value, expected, valid, field="deploy")


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("", "", True),  # OK, empty string
        ("target:1:1", "target:1:1", True),  # OK, string
        (False, False, False),  # NOK, bool
        (123, None, False),  # NOK, int
    ],
)
def test_vrf_attach_00010(value, expected, valid: bool) -> None:
    """
    export_evpn_rt
    """
    base_test_attach(value, expected, valid, field="export_evpn_rt")


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("", "", True),  # OK, empty string
        ("target:1:2", "target:1:2", True),  # OK, string
        (False, False, False),  # NOK, bool
        (123, None, False),  # NOK, int
    ],
)
def test_vrf_attach_00020(value, expected, valid: bool) -> None:
    """
    import_evpn_rt
    """
    base_test_attach(value, expected, valid, field="import_evpn_rt")


@pytest.mark.parametrize("value, expected, valid", ipv4_addr_host_tests)
def test_vrf_attach_00030(value, expected, valid: bool) -> None:
    """
    ip_address
    """
    base_test_attach(value, expected, valid, field="ip_address")


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        (None, None, True),  # OK, vrf_lite null
        ("MISSING", None, True),  # OK, field can be missing
        (1, None, False),  # NOK, vrf_lite int
        ("abc", None, False),  # NOK, vrf_lite string
    ],
)
def test_vrf_attach_00040(value, expected, valid: bool) -> None:
    """
    vrf_lite
    """
    base_test_attach(value, expected, valid, field="vrf_lite")


@pytest.mark.parametrize("value,expected,valid", bool_tests_missing_default_true)
def test_vrf_model_00000(value, expected, valid: bool) -> None:
    """
    adv_default_routes
    """
    base_test_vrf(value, expected, valid, field="adv_default_routes")


@pytest.mark.parametrize("value,expected,valid", bool_tests_missing_default_false)
def test_vrf_model_00010(value, expected, valid: bool) -> None:
    """
    adv_host_routes
    """
    base_test_vrf(value, expected, valid, field="adv_host_routes")


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        (None, None, True),  # OK, attach can be null.
        ("MISSING", None, True),  # OK, field can be missing
        ([], [], True),  # OK, attach can be an empty list
        (0, None, False),
        ("abc", None, False),
    ],
)
def test_vrf_model_00020(value, expected, valid: bool) -> None:
    """
    attach
    """
    base_test_vrf(value, expected, valid, field="attach")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        (BgpPasswordEncrypt.MD5, BgpPasswordEncrypt.MD5.value, True),
        (BgpPasswordEncrypt.TYPE7, BgpPasswordEncrypt.TYPE7.value, True),
        (3, 3, True),  # OK, integer corresponding to MD5
        (7, 7, True),  # OK, integer corresponding to TYPE7
        (-1, -1, True),  # OK, integer corresponding to NONE
        (0, None, False),  # NOK, not a valid enum value
        ("md5", None, False),  # NOK, string not in enum
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00030(value, expected, valid):
    """
    bgp_passwd_encrypt
    """
    base_test_vrf(value, expected, valid, field="bgp_passwd_encrypt")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("MyPassword", "MyPassword", True),
        ("MISSING", "", True),  # OK, field can be missing
        (3, 3, False),  # NOK, int
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00040(value, expected, valid):
    """
    bgp_password
    """
    base_test_vrf(value, expected, valid, field="bgp_password")


@pytest.mark.parametrize("value,expected,valid", bool_tests_missing_default_true)
def test_vrf_model_00050(value, expected, valid):
    """
    deploy
    """
    base_test_vrf(value, expected, valid, field="deploy")


@pytest.mark.parametrize("value,expected,valid", bool_tests_missing_default_false)
def test_vrf_model_00060(value, expected, valid):
    """
    disable_rt_auto
    """
    base_test_vrf(value, expected, valid, field="disable_rt_auto")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("5000:1", "5000:1", True),
        ("MISSING", "", True),  # OK, field can be missing. Default is "".
        (3, 3, False),  # NOK, int
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00070(value, expected, valid):
    """
    export/import route-target tests
    """
    for field in ["export_evpn_rt", "import_evpn_rt", "export_mvpn_rt", "import_mvpn_rt", "export_vpn_rt", "import_vpn_rt"]:
        base_test_vrf(value, expected, valid, field=field)


@pytest.mark.parametrize("value,expected,valid", bool_tests_missing_default_true)
def test_vrf_model_00080(value, expected, valid):
    """
    ipv6_linklocal_enable
    """
    base_test_vrf(value, expected, valid, field="ipv6_linklocal_enable")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        (0, 0, True),  # OK, integer in range
        (4294967295, 4294967295, True),  # OK, integer in range
        ("MISSING", 12345, True),  # OK, field can be missing. Default is 12345.
        (-1, None, False),  # NOK, must be > 0
        (4294967296, None, False),  # NOK, must be <= 4294967295
        ("md5", None, False),  # NOK, string
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00090(value, expected, valid):
    """
    loopback_route_tag
    """
    base_test_vrf(value, expected, valid, field="loopback_route_tag")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        (1, 1, True),  # OK, integer in range
        (64, 64, True),  # OK, integer in range
        ("MISSING", 1, True),  # OK, field can be missing. Default is 1.
        (0, None, False),  # NOK, must be > 1
        (65, None, False),  # NOK, must be <= 64
        ("md5", None, False),  # NOK, string
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00100(value, expected, valid):
    """
    max_bgp_paths
    """
    base_test_vrf(value, expected, valid, field="max_bgp_paths")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        (1, 1, True),  # OK, integer in range
        (64, 64, True),  # OK, integer in range
        ("MISSING", 2, True),  # OK, field can be missing. Default is 2.
        (0, None, False),  # NOK, must be > 1
        (65, None, False),  # NOK, must be <= 64
        ("md5", None, False),  # NOK, string
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00110(value, expected, valid):
    """
    max_ibgp_paths
    """
    base_test_vrf(value, expected, valid, field="max_ibgp_paths")


@pytest.mark.parametrize("value,expected,valid", bool_tests_missing_default_false)
def test_vrf_model_00120(value, expected, valid):
    """
    netflow_enable
    """
    base_test_vrf(value, expected, valid, field="netflow_enable")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("5000:1", "5000:1", True),
        ("MISSING", "", True),  # OK, field can be missing. Default is "".
        (3, 3, False),  # NOK, int
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00130(value, expected, valid):
    """
    nf_monitor
    TODO: Revisit for actual values after testing against NDFC.
    """
    base_test_vrf(value, expected, valid, field="nf_monitor")


@pytest.mark.parametrize("value,expected,valid", bool_tests_missing_default_false)
def test_vrf_model_00140(value, expected, valid):
    """
    no_rp
    """
    base_test_vrf(value, expected, valid, field="no_rp")


@pytest.mark.parametrize("value,expected,valid", ipv4_multicast_group_tests)
def test_vrf_model_00150(value, expected, valid):
    """
    overlay_mcast_group
    """
    base_test_vrf(value, expected, valid, field="overlay_mcast_group")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("my-route-map", "my-route-map", True),
        ("MISSING", "FABRIC-RMAP-REDIST-SUBNET", True),  # OK, field can be missing. Default is "FABRIC-RMAP-REDIST-SUBNET".
        ("", "", True),  # OK, empty string
        (3, 3, False),  # NOK, int
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00160(value, expected, valid):
    """
    redist_direct_rmap
    """
    base_test_vrf(value, expected, valid, field="redist_direct_rmap")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("10.1.1.1", "10.1.1.1", True),
        ("MISSING", "", True),  # OK, field can be missing. Default is "".
        ("", "", True),  # OK, empty string
        ("10.1.1.1/24", "10.1.1.1/24", False),  # NOK, prefix is not allowed
        (3, 3, False),  # NOK, int
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00170(value, expected, valid):
    """
    rp_address
    """
    base_test_vrf(value, expected, valid, field="rp_address")


@pytest.mark.parametrize("value,expected,valid", bool_tests_missing_default_false)
def test_vrf_model_00180(value, expected, valid):
    """
    rp_external
    """
    base_test_vrf(value, expected, valid, field="rp_external")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        (0, 0, True),  # OK, integer in range
        (1023, 1023, True),  # OK, integer in range
        ("MISSING", "", True),  # OK, field can be missing. Default is "".
        (-1, None, False),  # NOK, must be >= 0
        (1024, None, False),  # NOK, must be <= 1023
        ("md5", None, False),  # NOK, string
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00190(value, expected, valid):
    """
    rp_loopback_id
    """
    base_test_vrf(value, expected, valid, field="rp_loopback_id")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("MY-SERVICE-VRF-TEMPLATE", "MY-SERVICE-VRF-TEMPLATE", True),  # OK, valid string
        ("MISSING", None, True),  # OK, field can be missing. Default is None.
        (None, None, True),  # OK, None is valid
        (-1, None, False),  # NOK, not a string
        (1024, None, False),  # NOK, not a string
    ],
)
def test_vrf_model_00200(value, expected, valid):
    """
    service_vrf_template
    """
    base_test_vrf(value, expected, valid, field="service_vrf_template")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("MISSING", None, True),  # OK, field is always hardcoded to None.
        (None, None, True),  # OK, field is always hardcoded to None.
        ("some-string", None, True),  # OK, field is always hardcoded to None.
        (-1, None, True),  # OK, field is always hardcoded to None.
        (1024, None, True),  # OK, field is always hardcoded to None.
    ],
)
def test_vrf_model_00210(value, expected, valid):
    """
    source
    """
    base_test_vrf(value, expected, valid, field="source")


@pytest.mark.parametrize("value,expected,valid", bool_tests_missing_default_true)
def test_vrf_model_00220(value, expected, valid):
    """
    static_default_route
    """
    base_test_vrf(value, expected, valid, field="static_default_route")


@pytest.mark.parametrize("value,expected,valid", bool_tests_missing_default_false)
def test_vrf_model_00230(value, expected, valid):
    """
    trm_bgw_msite
    """
    base_test_vrf(value, expected, valid, field="trm_bgw_msite")


@pytest.mark.parametrize("value,expected,valid", bool_tests_missing_default_false)
def test_vrf_model_00240(value, expected, valid):
    """
    trm_enable
    """
    base_test_vrf(value, expected, valid, field="trm_enable")


@pytest.mark.parametrize("value,expected,valid", ipv4_multicast_group_tests)
def test_vrf_model_00250(value, expected, valid):
    """
    underlay_mcast_ip
    """
    base_test_vrf(value, expected, valid, field="underlay_mcast_ip")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        (2, 2, True),  # OK, integer in range
        (4094, 4094, True),  # OK, integer in range
        ("2", 2, True),  # OK, str convertable to integer in range
        ("4094", 4094, True),  # OK, str convertable to integer in range
        ("MISSING", None, True),  # OK, field can be missing. Default is None.
        (-1, None, False),  # NOK, must be >= 2
        (4095, None, False),  # NOK, must be <= 4094
        ("1", None, False),  # NOK, str convertable to integer out of range
        ("4095", None, False),  # NOK, str convertable to integer out in range
        ("md5", None, False),  # NOK, string
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00260(value, expected, valid):
    """
    vlan_id
    """
    base_test_vrf(value, expected, valid, field="vlan_id")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("My vrf description", "My vrf description", True),
        ("MISSING", "", True),  # OK, field can be missing. Default is "".
        ("", "", True),  # OK, empty string
        (3, 3, False),  # NOK, int
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00270(value, expected, valid):
    """
    vrf_description
    """
    base_test_vrf(value, expected, valid, field="vrf_description")


@pytest.mark.parametrize(
    "value,expected,valid",
    [
        ("MY_VRF_EXT_TEMPLATE", "MY_VRF_EXT_TEMPLATE", True),
        ("MISSING", "Default_VRF_Extension_Universal", True),  # OK, field can be missing. Default is "Default_VRF_Extension_Universal".
        ("", "", True),  # OK, empty string
        (3, 3, False),  # NOK, int
        (None, None, False),  # NOK, None is not a valid value
    ],
)
def test_vrf_model_00280(value, expected, valid):
    """
    vrf_extension_template
    """
    base_test_vrf(value, expected, valid, field="vrf_extension_template")
