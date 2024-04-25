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

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_types
    assert instance.class_name == "FabricTypes"
    assert instance._properties["fabric_type"] is None
    assert instance._properties["template_name"] is None
    for fabric_type in ["LAN_CLASSIC", "VXLAN_EVPN", "VXLAN_EVPN_MSD"]:
        assert fabric_type in instance.valid_fabric_types
    for mandatory_parameter in ["FABRIC_NAME", "FABRIC_TYPE"]:
        assert mandatory_parameter in instance._mandatory_parameters_all_fabrics
    for fabric_type in instance.valid_fabric_types:
        assert fabric_type in instance._mandatory_parameters
    assert "BGP_AS" in instance._mandatory_parameters["VXLAN_EVPN"]


MATCH_00020 = r"FabricTypes\.fabric_type.setter:\s+"
MATCH_00020 += r"Invalid fabric type: INVALID_FABRIC_TYPE.\s+"
MATCH_00020 += r"Expected one of: LAN_CLASSIC, VXLAN_EVPN, VXLAN_EVPN_MSD\."


@pytest.mark.parametrize(
    "fabric_type, template_name, does_raise, expected",
    [
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

    Summary
    -    FabricTypes().template returns the expected template name, given
        a valid fabric_type.
    -   ``ValueError`` is raised user tries to set an invalid fabric_type.
    """
    with does_not_raise():
        instance = fabric_types
    with expected:
        instance.fabric_type = fabric_type
    if not does_raise:
        assert instance.template_name == template_name


VXLAN_EVPN_PARAMETERS = ["BGP_AS", "FABRIC_NAME", "FABRIC_TYPE"]
LAN_CLASSIC_PARAMETERS = ["FABRIC_NAME", "FABRIC_TYPE"]
VXLAN_EVPN_MSD_PARAMETERS = ["FABRIC_NAME", "FABRIC_TYPE"]
MATCH_00030 = r"FabricTypes\.fabric_type.setter:\s+"
MATCH_00030 += r"Invalid fabric type: INVALID_FABRIC_TYPE.\s+"


@pytest.mark.parametrize(
    "fabric_type, parameters, does_raise, expected",
    [
        ("LAN_CLASSIC", LAN_CLASSIC_PARAMETERS, False, does_not_raise()),
        ("VXLAN_EVPN", VXLAN_EVPN_PARAMETERS, False, does_not_raise()),
        ("VXLAN_EVPN_MSD", VXLAN_EVPN_MSD_PARAMETERS, False, does_not_raise()),
        (
            "INVALID_FABRIC_TYPE",
            None,
            True,
            pytest.raises(ValueError, match=MATCH_00030),
        ),
    ],
)
def test_fabric_types_00030(
    fabric_types, fabric_type, parameters, does_raise, expected
) -> None:
    """
    Classes and Methods
    - FabricTypes
        - __init__()
        - fabric_type.setter

    Summary
    -    FabricTypes().template returns the expected template name, given
        a valid fabric_type.
    -   ``ValueError`` is raised user tries to set an invalid fabric_type.
    """
    with does_not_raise():
        instance = fabric_types
    with expected:
        instance.fabric_type = fabric_type
    if not does_raise:
        assert instance.mandatory_parameters == parameters
