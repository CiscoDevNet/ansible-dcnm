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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# Also, fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-import
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=unused-argument
# pylint: disable=unused-variable
# pylint: disable=invalid-name
# pylint: disable=line-too-long
# pylint: disable=too-many-lines
"""
Unit tests for FabricGroupTypes class in module_utils/fabric_group/fabric_group_types.py
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.fabric_group_types import FabricGroupTypes
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric_group.utils import does_not_raise


@pytest.fixture(name="fabric_group_types")
def fabric_group_types_fixture():
    """
    Return FabricGroupTypes() instance.
    """
    return FabricGroupTypes()


def test_fabric_group_types_00000(fabric_group_types) -> None:
    """
    # Summary

    Verify class initialization

    ## Classes and Methods

    - FabricGroupTypes.__init__()

    ## Test

    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_group_types
    assert instance.class_name == "FabricGroupTypes"
    assert instance._template_name == ""
    assert instance._fabric_group_type == ""
    assert instance._fabric_group_type_to_template_name_map is not None
    assert instance._fabric_group_type_to_feature_name_map is not None
    assert instance._fabric_group_type_to_fabric_type_map is not None
    assert instance._valid_fabric_group_types is not None
    assert instance._mandatory_parameters_all_fabric_groups is not None
    assert instance._mandatory_parameters is not None


def test_fabric_group_types_00010(fabric_group_types) -> None:
    """
    # Summary

    Verify valid_fabric_group_types property returns correct list

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.valid_fabric_group_types (property)

    ## Test

    - valid_fabric_group_types returns sorted list containing "MCFG"
    """
    with does_not_raise():
        instance = fabric_group_types

    assert isinstance(instance.valid_fabric_group_types, list)
    assert "MCFG" in instance.valid_fabric_group_types
    assert len(instance.valid_fabric_group_types) >= 1


def test_fabric_group_types_00020(fabric_group_types) -> None:
    """
    # Summary

    Verify valid_fabric_group_template_names property returns correct list

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.valid_fabric_group_template_names (property)

    ## Test

    - valid_fabric_group_template_names returns sorted list containing "MSD_Fabric"
    """
    with does_not_raise():
        instance = fabric_group_types

    assert isinstance(instance.valid_fabric_group_template_names, list)
    assert "MSD_Fabric" in instance.valid_fabric_group_template_names
    assert len(instance.valid_fabric_group_template_names) >= 1


def test_fabric_group_types_00030(fabric_group_types) -> None:
    """
    # Summary

    Verify fabric_group_type property setter and getter

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.fabric_group_type (setter/getter)

    ## Test

    - fabric_group_type is set to "MCFG"
    - fabric_group_type returns "MCFG"
    """
    with does_not_raise():
        instance = fabric_group_types
        instance.fabric_group_type = "MCFG"
    assert instance.fabric_group_type == "MCFG"


def test_fabric_group_types_00031(fabric_group_types) -> None:
    """
    # Summary

    Verify ValueError is raised when fabric_group_type is set to invalid value

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.fabric_group_type (setter)

    ## Test

    - ValueError is raised with expected message
    """
    match = r"FabricGroupTypes\.fabric_group_type\.setter: "
    match += r"Invalid fabric group type: INVALID\. "
    match += r"Expected one of: MCFG\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_types
        instance.fabric_group_type = "INVALID"


def test_fabric_group_types_00040(fabric_group_types) -> None:
    """
    # Summary

    Verify template_name property returns correct value for MCFG

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.template_name (property)

    ## Test

    - template_name returns "MSD_Fabric" for MCFG fabric group type
    """
    with does_not_raise():
        instance = fabric_group_types
        instance.fabric_group_type = "MCFG"

    assert instance.template_name == "MSD_Fabric"


def test_fabric_group_types_00041(fabric_group_types) -> None:
    """
    # Summary

    Verify ValueError is raised when template_name is accessed without setting fabric_group_type

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.template_name (property)

    ## Test

    - ValueError is raised with expected message
    """
    match = r"FabricGroupTypes\.template_name: "
    match += r"Set FabricGroupTypes\.fabric_group_type before accessing "
    match += r"FabricGroupTypes\.template_name"

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_types
        result = instance.template_name  # pylint: disable=pointless-statement


def test_fabric_group_types_00050(fabric_group_types) -> None:
    """
    # Summary

    Verify fabric_type property returns correct value for MCFG

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.fabric_type (property)

    ## Test

    - fabric_type returns "MFD" for MCFG fabric group type
    """
    with does_not_raise():
        instance = fabric_group_types
        instance.fabric_group_type = "MCFG"

    assert instance.fabric_type == "MFD"


def test_fabric_group_types_00051(fabric_group_types) -> None:
    """
    # Summary

    Verify ValueError is raised when fabric_type is accessed without setting fabric_group_type

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.fabric_type (property)

    ## Test

    - ValueError is raised with expected message
    """
    match = r"FabricGroupTypes\.fabric_type: "
    match += r"Set FabricGroupTypes\.fabric_group_type before accessing "
    match += r"FabricGroupTypes\.fabric_type"

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_types
        result = instance.fabric_type  # pylint: disable=pointless-statement


def test_fabric_group_types_00060(fabric_group_types) -> None:
    """
    # Summary

    Verify feature_name property returns correct value for MCFG

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.feature_name (property)

    ## Test

    - feature_name returns "vxlan" for MCFG fabric group type
    """
    with does_not_raise():
        instance = fabric_group_types
        instance.fabric_group_type = "MCFG"

    assert instance.feature_name == "vxlan"


def test_fabric_group_types_00061(fabric_group_types) -> None:
    """
    # Summary

    Verify ValueError is raised when feature_name is accessed without setting fabric_group_type

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.feature_name (property)

    ## Test

    - ValueError is raised with expected message
    """
    match = r"FabricGroupTypes\.feature_name: "
    match += r"Set FabricGroupTypes\.fabric_group_type before accessing "
    match += r"FabricGroupTypes\.feature_name"

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_types
        result = instance.feature_name  # pylint: disable=pointless-statement


def test_fabric_group_types_00070(fabric_group_types) -> None:
    """
    # Summary

    Verify mandatory_parameters property returns correct list for MCFG

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.mandatory_parameters (property)

    ## Test

    - mandatory_parameters returns sorted list containing "FABRIC_NAME" and "FABRIC_TYPE"
    """
    with does_not_raise():
        instance = fabric_group_types
        instance.fabric_group_type = "MCFG"

    assert isinstance(instance.mandatory_parameters, list)
    assert "FABRIC_NAME" in instance.mandatory_parameters
    assert "FABRIC_TYPE" in instance.mandatory_parameters
    # Verify list is sorted
    assert instance.mandatory_parameters == sorted(instance.mandatory_parameters)


def test_fabric_group_types_00071(fabric_group_types) -> None:
    """
    # Summary

    Verify ValueError is raised when mandatory_parameters is accessed without setting fabric_group_type

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.mandatory_parameters (property)

    ## Test

    - ValueError is raised with expected message
    """
    match = r"FabricGroupTypes\.mandatory_parameters: "
    match += r"Set FabricGroupTypes\.fabric_group_type before accessing "
    match += r"FabricGroupTypes\.mandatory_parameters"

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_types
        result = instance.mandatory_parameters  # pylint: disable=pointless-statement


def test_fabric_group_types_00080(fabric_group_types) -> None:
    """
    # Summary

    Verify _init_fabric_group_types initializes all mappings correctly

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes._init_fabric_group_types()

    ## Test

    - All mapping dictionaries contain MCFG entries
    - Valid fabric group types set contains MCFG
    - Mandatory parameters lists are populated
    """
    with does_not_raise():
        instance = fabric_group_types

    # Verify template name mapping
    assert "MCFG" in instance._fabric_group_type_to_template_name_map
    assert instance._fabric_group_type_to_template_name_map["MCFG"] == "MSD_Fabric"

    # Verify feature name mapping
    assert "MCFG" in instance._fabric_group_type_to_feature_name_map
    assert instance._fabric_group_type_to_feature_name_map["MCFG"] == "vxlan"

    # Verify fabric type mapping
    assert "MCFG" in instance._fabric_group_type_to_fabric_type_map
    assert instance._fabric_group_type_to_fabric_type_map["MCFG"] == "MFD"

    # Verify valid fabric group types
    assert "MCFG" in instance._valid_fabric_group_types

    # Verify mandatory parameters
    assert "FABRIC_NAME" in instance._mandatory_parameters_all_fabric_groups
    assert "FABRIC_TYPE" in instance._mandatory_parameters_all_fabric_groups
    assert "MCFG" in instance._mandatory_parameters
    assert instance._mandatory_parameters["MCFG"] == sorted(instance._mandatory_parameters["MCFG"])


def test_fabric_group_types_00090(fabric_group_types) -> None:
    """
    # Summary

    Verify all properties work together correctly

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.fabric_group_type (setter)
    - FabricGroupTypes.template_name (property)
    - FabricGroupTypes.fabric_type (property)
    - FabricGroupTypes.feature_name (property)
    - FabricGroupTypes.mandatory_parameters (property)

    ## Test

    - All properties return expected values when fabric_group_type is set to MCFG
    """
    with does_not_raise():
        instance = fabric_group_types
        instance.fabric_group_type = "MCFG"

    # Verify all properties return expected values
    assert instance.fabric_group_type == "MCFG"
    assert instance.template_name == "MSD_Fabric"
    assert instance.fabric_type == "MFD"
    assert instance.feature_name == "vxlan"
    assert isinstance(instance.mandatory_parameters, list)
    assert len(instance.mandatory_parameters) >= 2


def test_fabric_group_types_00100(fabric_group_types) -> None:
    """
    # Summary

    Verify valid_fabric_group_types returns a sorted list

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.valid_fabric_group_types (property)

    ## Test

    - valid_fabric_group_types returns a sorted list
    """
    with does_not_raise():
        instance = fabric_group_types
        valid_types = instance.valid_fabric_group_types

    # Verify list is sorted
    assert valid_types == sorted(valid_types)


def test_fabric_group_types_00110(fabric_group_types) -> None:
    """
    # Summary

    Verify valid_fabric_group_template_names returns a sorted list

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.valid_fabric_group_template_names (property)

    ## Test

    - valid_fabric_group_template_names returns a sorted list
    """
    with does_not_raise():
        instance = fabric_group_types
        template_names = instance.valid_fabric_group_template_names

    # Verify list is sorted
    assert template_names == sorted(template_names)


def test_fabric_group_types_00120(fabric_group_types) -> None:
    """
    # Summary

    Verify fabric_group_type can be changed after initial setting

    ## Classes and Methods

    - FabricGroupTypes.__init__()
    - FabricGroupTypes.fabric_group_type (setter/getter)

    ## Test

    - fabric_group_type can be set multiple times
    - Properties reflect the currently set fabric_group_type
    """
    with does_not_raise():
        instance = fabric_group_types
        instance.fabric_group_type = "MCFG"

    assert instance.fabric_group_type == "MCFG"
    assert instance.template_name == "MSD_Fabric"

    # Can set to the same value again
    with does_not_raise():
        instance.fabric_group_type = "MCFG"

    assert instance.fabric_group_type == "MCFG"
    assert instance.template_name == "MSD_Fabric"
