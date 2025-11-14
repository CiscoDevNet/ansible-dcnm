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
# pylint: disable=protected-access
# pylint: disable=invalid-name

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import pytest
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    does_not_raise, fabric_types_fixture)


def test_fabric_types_00010(fabric_types) -> None:
    """
    Classes and Methods
    - FabricTypes
        - __init__()

    Summary
    -   Verify class attributes are initialized to expected values.
    -   Verify exception is not raised.
    """
    with does_not_raise():
        instance = fabric_types
    assert instance.class_name == "FabricTypes"
    assert instance._properties["fabric_type"] is None
    assert instance._properties["template_name"] is None
    for fabric_type in ["IPFM", "ISN", "LAN_CLASSIC", "VXLAN_EVPN", "VXLAN_EVPN_MSD"]:
        assert fabric_type in instance.valid_fabric_types
    for mandatory_parameter in ["FABRIC_NAME", "FABRIC_TYPE"]:
        assert mandatory_parameter in instance._mandatory_parameters_all_fabrics
    for fabric_type in instance.valid_fabric_types:
        assert fabric_type in instance._mandatory_parameters
    assert "BGP_AS" in instance._mandatory_parameters["ISN"]
    assert "BGP_AS" in instance._mandatory_parameters["VXLAN_EVPN"]


MATCH_00020 = r"FabricTypes\.fabric_type.setter:\s+"
MATCH_00020 += r"Invalid fabric type: INVALID_FABRIC_TYPE.\s+"
MATCH_00020 += r"Expected one of:\s+.*\."


@pytest.mark.parametrize(
    "fabric_type, template_name, does_raise, expected",
    [
        ("ISN", "External_Fabric", False, does_not_raise()),
        ("IPFM", "Easy_Fabric_IPFM", False, does_not_raise()),
        ("LAN_CLASSIC", "LAN_Classic", False, does_not_raise()),
        ("VXLAN_EVPN", "Easy_Fabric", False, does_not_raise()),
        ("VXLAN_EVPN_MSD", "MSD_Fabric", False, does_not_raise()),
        (
            "INVALID_FABRIC_TYPE",
            None,
            True,
            pytest.raises(ValueError, match=MATCH_00020),
        ),
    ],
)
def test_fabric_types_00020(
    fabric_types, fabric_type, template_name, does_raise, expected
) -> None:
    """
    Classes and Methods
    - FabricTypes
        - __init__()
        - fabric_type.setter
        - template_name.getter

    Summary
    -   Verify FabricTypes().template returns the expected template name,
        given a valid fabric_type.
    -   Verify ``ValueError`` is raised if user tries to set an invalid
        fabric_type.
    """
    with does_not_raise():
        instance = fabric_types
    with expected:
        instance.fabric_type = fabric_type
    if not does_raise:
        assert instance.template_name == template_name


def test_fabric_types_00030(fabric_types) -> None:
    """
    Classes and Methods
    - FabricTypes
        - __init__()
        - template_name.getter

    Summary
    -   Verify ``ValueError`` is raised if FabricTypes().fabric_type
        is not set prior to accessing FabricTypes().template_name.
    """
    with does_not_raise():
        instance = fabric_types
    match = r"FabricTypes\.template_name:\s+"
    match += r"Set FabricTypes\.fabric_type before accessing\s+"
    match += r"FabricTypes\.template_name"
    with pytest.raises(ValueError, match=match):
        instance.template_name  # pylint: disable=pointless-statement


ISN_PARAMETERS = ["BGP_AS", "FABRIC_NAME", "FABRIC_TYPE"]
IPFM_PARAMETERS = ["FABRIC_NAME", "FABRIC_TYPE"]
LAN_CLASSIC_PARAMETERS = ["FABRIC_NAME", "FABRIC_TYPE"]
VXLAN_EVPN_PARAMETERS = ["BGP_AS", "FABRIC_NAME", "FABRIC_TYPE"]
VXLAN_EVPN_MSD_PARAMETERS = ["FABRIC_NAME", "FABRIC_TYPE"]
MATCH_00040 = r"FabricTypes\.fabric_type.setter:\s+"
MATCH_00040 += r"Invalid fabric type: INVALID_FABRIC_TYPE.\s+"


@pytest.mark.parametrize(
    "fabric_type, parameters, does_raise, expected",
    [
        ("ISN", ISN_PARAMETERS, False, does_not_raise()),
        ("IPFM", IPFM_PARAMETERS, False, does_not_raise()),
        ("LAN_CLASSIC", LAN_CLASSIC_PARAMETERS, False, does_not_raise()),
        ("VXLAN_EVPN", VXLAN_EVPN_PARAMETERS, False, does_not_raise()),
        ("VXLAN_EVPN_MSD", VXLAN_EVPN_MSD_PARAMETERS, False, does_not_raise()),
        (
            "INVALID_FABRIC_TYPE",
            None,
            True,
            pytest.raises(ValueError, match=MATCH_00040),
        ),
    ],
)
def test_fabric_types_00040(
    fabric_types, fabric_type, parameters, does_raise, expected
) -> None:
    """
    Classes and Methods
    - FabricTypes
        - __init__()
        - fabric_type.setter
        - mandatory_parameters.getter

    Summary
    -   Verify FabricTypes().mandatory_parameters returns the expected
        mandatory parameters, given a valid fabric_type.
    -   Verify ``ValueError`` is raised if user tries to set an invalid
        fabric_type.
    """
    with does_not_raise():
        instance = fabric_types
    with expected:
        instance.fabric_type = fabric_type
    if not does_raise:
        assert instance.mandatory_parameters == parameters


def test_fabric_types_00050(fabric_types) -> None:
    """
    Classes and Methods
    - FabricTypes
        - __init__()
        - mandatory_parameters.getter

    Summary
    -   Verify that ``ValueError`` is raised if FabricTypes().fabric_type
        is not set prior to accessing FabricTypes().mandatory_parameters.
    """
    with does_not_raise():
        instance = fabric_types
    match = r"FabricTypes\.mandatory_parameters:\s+"
    match += r"Set FabricTypes\.fabric_type before accessing\s+"
    match += r"FabricTypes\.mandatory_parameters"
    with pytest.raises(ValueError, match=match):
        instance.mandatory_parameters  # pylint: disable=pointless-statement
