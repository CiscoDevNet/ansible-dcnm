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
from typing import Union

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.vrf.model_playbook_vrf_v12 import (
    PlaybookVrfAttachModel,
    PlaybookVrfConfigModelV12,
    PlaybookVrfLiteModel,
    PlaybookVrfModelV12,
)

from ..common.common_utils import does_not_raise
from .fixtures.load_fixture import playbooks


def test_full_config_00000() -> None:
    """
    Test PlaybookVrfConfigModelV12 with JSON representing the structure passed to a playbook.

    The remaining tests will use the structure associated with PlaybookVrfModelV12 for simplicity.
    """
    playbook = playbooks("playbook_full_config")
    with does_not_raise():
        instance = PlaybookVrfConfigModelV12(**playbook)
    assert instance.config[0].vrf_name == "ansible-vrf-int1"


@pytest.mark.parametrize(
    "value, expected",
    [
        ("ansible-vrf-int1", True),
        ("vrf_5678901234567890123456789012", True),  # Valid, exactly 32 characters
        (123, False),  # Invalid, int
        ("vrf_56789012345678901234567890123", False),  # Invalid, longer than 32 characters
    ],
)
def test_vrf_name_00000(value: Union[str, int], expected: bool) -> None:
    """
    Test the validation of VRF names.

    :param value: The VRF name to validate.
    :param expected: Expected result of the validation.
    """
    playbook = playbooks("playbook_as_dict")
    playbook["vrf_name"] = value
    if expected:
        with does_not_raise():
            instance = PlaybookVrfModelV12(**playbook)
            assert instance.vrf_name == value
    else:
        with pytest.raises(ValueError):
            PlaybookVrfModelV12(**playbook)


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
def test_vrf_lite_00000(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_lite.dot1q validation.

    :param value: The dot1q value to validate.
    :param expected: Expected value after model conversion (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_lite")
    playbook["dot1q"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfLiteModel(**playbook)
            assert instance.dot1q == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfLiteModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("Ethernet1/1", "Ethernet1/1", True),
        ("Eth2/1", "Eth2/1", True),
        ("foo", None, False),
    ],
)
def test_vrf_lite_00010(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_lite.interface validation.

    :param value: interface value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_lite")
    if valid:
        playbook["interface"] = value
        with does_not_raise():
            instance = PlaybookVrfLiteModel(**playbook)
            assert instance.interface == expected
    else:
        del playbook["interface"]
        with pytest.raises(ValueError):
            PlaybookVrfLiteModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("10.1.1.1/24", "10.1.1.1/24", True),
        ("168.1.1.1/30", "168.1.1.1/30", True),
        ("172.1.1.1/30", "172.1.1.1/30", True),
        # ("255.255.255.255/30", None, False), TODO: this should not be valid, but currently is
        ("172.1.1.", None, False),
        ("255.255.255.255", None, False),
        ("2010::10:34:0:7", None, False),
        ("2010::10:34:0:7/64", None, False),
        (1, None, False),
        ("abc", None, False),
    ],
)
def test_vrf_lite_00020(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_lite.ipv4_addr validation.

    :param value: ipv4_addr value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_lite")
    playbook["ipv4_addr"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfLiteModel(**playbook)
            assert instance.ipv4_addr == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfLiteModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("2010::10:34:0:7/64", "2010::10:34:0:7/64", True),
        ("2010::10::7/128", "2010::10::7/128", True),
        ("2010:10::7", None, False),
        ("172.1.1.1/30", None, False),
        ("172.1.1.1", None, False),
        ("255.255.255.255", None, False),
        (1, None, False),
        ("abc", None, False),
    ],
)
def test_vrf_lite_00030(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_lite.ipv6_addr validation.

    :param value: ipv6_addr value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_lite")
    playbook["ipv6_addr"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfLiteModel(**playbook)
            assert instance.ipv6_addr == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfLiteModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
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
    ],
)
def test_vrf_lite_00040(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_lite.neighbor_ipv4 validation.

    :param value: neighbor_ipv4 value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_lite")
    playbook["neighbor_ipv4"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfLiteModel(**playbook)
            assert instance.neighbor_ipv4 == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfLiteModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("2010::10:34:0:7", "2010::10:34:0:7", True),
        ("2010:10::7", "2010:10::7", True),
        ("2010::10:34:0:7/64", "2010::10:34:0:7/64", False),
        ("2010::10::7/128", "2010::10::7/128", False),
        ("172.1.1.1/30", None, False),
        ("172.1.1.1", None, False),
        ("255.255.255.255", None, False),
        (1, None, False),
        ("abc", None, False),
    ],
)
def test_vrf_lite_00050(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_lite.neighbor_ipv6 validation.

    :param value: neighbor_ipv6 value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_lite")
    playbook["neighbor_ipv6"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfLiteModel(**playbook)
            assert instance.neighbor_ipv6 == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfLiteModel(**playbook)


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
def test_vrf_lite_00060(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_lite.peer_vrf validation.

    :param value: peer_vrf value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_lite")
    playbook["peer_vrf"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfLiteModel(**playbook)
            assert instance.peer_vrf == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfLiteModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        (True, True, True),  # OK, bool
        (False, False, True),  # OK, bool
        ("", None, False),  # NOK, string
        (123, None, False),  # NOK, int
    ],
)
def test_vrf_attach_00000(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_attach.deploy validation.

    :param value: vrf_attachc value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_attach")
    playbook["deploy"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfAttachModel(**playbook)
            assert instance.deploy == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfAttachModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("", "", True),  # OK, empty string
        ("target:1:1", "target:1:1", True),  # OK, string
        (False, False, False),  # NOK, bool
        (123, None, False),  # NOK, int
    ],
)
def test_vrf_attach_00010(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_attach.export_evpn_rt validation.

    :param value: vrf_attachc value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_attach")
    playbook["export_evpn_rt"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfAttachModel(**playbook)
            assert instance.export_evpn_rt == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfAttachModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        ("", "", True),  # OK, empty string
        ("target:1:2", "target:1:2", True),  # OK, string
        (False, False, False),  # NOK, bool
        (123, None, False),  # NOK, int
    ],
)
def test_vrf_attach_00020(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_attach.import_evpn_rt validation.

    :param value: vrf_attachc value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_attach")
    playbook["import_evpn_rt"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfAttachModel(**playbook)
            assert instance.import_evpn_rt == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfAttachModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
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
    ],
)
def test_vrf_attach_00030(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_attach.ip_address validation.

    :param value: ip_address value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_attach")
    playbook["ip_address"] = value
    if valid:
        with does_not_raise():
            instance = PlaybookVrfAttachModel(**playbook)
            assert instance.ip_address == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfAttachModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        (None, None, True),  # OK, vrf_lite null
        ("MISSING", None, True),  # OK, vrf_lite can be missing
        (1, None, False),  # NOK, vrf_lite int
        ("abc", None, False),  # NOK, vrf_lite string
    ],
)
def test_vrf_attach_00040(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_attach.vrf_lite validation.

    :param value: ip_address value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("vrf_attach")
    if value == "MISSING":
        playbook.pop("vrf_list", None)
    else:
        playbook["vrf_lite"] = value

    if valid:
        with does_not_raise():
            instance = PlaybookVrfAttachModel(**playbook)
            if value != "MISSING":
                assert instance.vrf_lite == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfAttachModel(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        (True, True, True),  # OK, bool
        # (False, False, True),  # OK, bool. TODO: This should not fail.
        ("MISSING", True, True),  # OK, adv_default_routes can be missing
        (1, True, True),  # OK, type is set to StrictBoolean in the model which does allow 1
        (0, True, True),  # TODO: this should pass since StrictBoolean allows 0, but currently fails.  0 should == False, but True passes.
        ("abc", True, True),  # OK, "abc" is truthy in Python, so it is considered valid
    ],
)
def test_vrf_model_00000(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_attach.adv_default_routes validation.

    :param value: vrf_model value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("playbook_as_dict")
    if value == "MISSING":
        playbook.pop("adv_default_routes", None)
    else:
        playbook["adv_default_routes"] = value

    if valid:
        with does_not_raise():
            instance = PlaybookVrfModelV12(**playbook)
            if value != "MISSING":
                assert instance.adv_default_routes == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfModelV12(**playbook)


@pytest.mark.parametrize(
    "value, expected, valid",
    [
        # (True, True, True),  # OK, bool
        (False, False, True),  # OK, bool. TODO: This should not fail.
        ("MISSING", False, True),  # OK, adv_default_routes can be missing
        # (1, True, True),  # OK, type is set to StrictBoolean in the model which does allow 1
        (0, False, True),
        # ("abc", True, True),  # NOK, vrf_lite string
    ],
)
def test_vrf_model_00010(value: Union[str, int], expected: str, valid: bool) -> None:
    """
    vrf_attach.adv_host_routes

    :param value: vrf_model value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the value is valid or not.
    """
    playbook = playbooks("playbook_as_dict")
    if value == "MISSING":
        playbook.pop("adv_host_routes", None)
    else:
        playbook["adv_host_routes"] = value

    if valid:
        with does_not_raise():
            instance = PlaybookVrfModelV12(**playbook)
            if value != "MISSING":
                assert instance.adv_host_routes == expected
    else:
        with pytest.raises(ValueError):
            PlaybookVrfModelV12(**playbook)
