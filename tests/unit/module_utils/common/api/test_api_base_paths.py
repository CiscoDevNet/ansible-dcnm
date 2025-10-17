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

"""Unit tests for base_paths.py"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name


import pytest  # pylint: disable=unused-import,import-error
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.base_paths import BasePath
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import does_not_raise

# =============================================================================
# Constants
# =============================================================================

NDFC_API_PREFIX = "/appcenter/cisco/ndfc/api"
V1_PREFIX = f"{NDFC_API_PREFIX}/v1"
LAN_FABRIC_PREFIX = f"{V1_PREFIX}/lan-fabric"
LAN_FABRIC_REST_PREFIX = f"{LAN_FABRIC_PREFIX}/rest"
CONTROL_PREFIX = f"{LAN_FABRIC_REST_PREFIX}/control"
CONTROL_FABRICS_PREFIX = f"{CONTROL_PREFIX}/fabrics"
CONTROL_SWITCHES_PREFIX = f"{CONTROL_PREFIX}/switches"
INVENTORY_PREFIX = f"{LAN_FABRIC_REST_PREFIX}/inventory"
CONFIGTEMPLATE_PREFIX = f"{V1_PREFIX}/configtemplate"
ONEMANAGE_PREFIX = f"{V1_PREFIX}/onemanage"
ONEMANAGE_FABRICS_PREFIX = f"{ONEMANAGE_PREFIX}/fabrics"
ONEMANAGE_TOP_DOWN_PREFIX = f"{ONEMANAGE_PREFIX}/top-down"
ONEMANAGE_TOP_DOWN_FABRICS_PREFIX = f"{ONEMANAGE_TOP_DOWN_PREFIX}/fabrics"


# =============================================================================
# Test: Class Constants
# =============================================================================


def test_base_paths_00010():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify NDFC_API constant value
    """
    with does_not_raise():
        result = BasePath.NDFC_API
    assert result == NDFC_API_PREFIX


def test_base_paths_00020():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify ONEMANAGE constant value
    """
    with does_not_raise():
        result = BasePath.ONEMANAGE
    assert result == "/onemanage"


def test_base_paths_00030():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify LOGIN constant value
    """
    with does_not_raise():
        result = BasePath.LOGIN
    assert result == "/login"


# =============================================================================
# Test: api() method
# =============================================================================


def test_base_paths_00100():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify api() with no segments returns NDFC_API root
    """
    with does_not_raise():
        result = BasePath.api()
    assert result == NDFC_API_PREFIX


def test_base_paths_00110():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify api() with single segment
    """
    with does_not_raise():
        result = BasePath.api("custom")
    assert result == f"{NDFC_API_PREFIX}/custom"


def test_base_paths_00120():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify api() with multiple segments
    """
    with does_not_raise():
        result = BasePath.api("custom", "endpoint", "path")
    assert result == f"{NDFC_API_PREFIX}/custom/endpoint/path"


# =============================================================================
# Test: v1() method
# =============================================================================


def test_base_paths_00200():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify v1() with no segments returns v1 prefix
    """
    with does_not_raise():
        result = BasePath.v1()
    assert result == V1_PREFIX


def test_base_paths_00210():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify v1() with single segment
    """
    with does_not_raise():
        result = BasePath.v1("custom")
    assert result == f"{V1_PREFIX}/custom"


def test_base_paths_00220():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify v1() with multiple segments
    """
    with does_not_raise():
        result = BasePath.v1("lan-fabric", "rest")
    assert result == f"{V1_PREFIX}/lan-fabric/rest"


# =============================================================================
# Test: lan_fabric() method
# =============================================================================


def test_base_paths_00300():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify lan_fabric() with no segments
    """
    with does_not_raise():
        result = BasePath.lan_fabric()
    assert result == LAN_FABRIC_PREFIX


def test_base_paths_00310():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify lan_fabric() with segments
    """
    with does_not_raise():
        result = BasePath.lan_fabric("rest", "control")
    assert result == f"{LAN_FABRIC_PREFIX}/rest/control"


# =============================================================================
# Test: lan_fabric_rest() method
# =============================================================================


def test_base_paths_00400():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify lan_fabric_rest() with no segments
    """
    with does_not_raise():
        result = BasePath.lan_fabric_rest()
    assert result == LAN_FABRIC_REST_PREFIX


def test_base_paths_00410():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify lan_fabric_rest() with segments
    """
    with does_not_raise():
        result = BasePath.lan_fabric_rest("control", "fabrics")
    assert result == f"{LAN_FABRIC_REST_PREFIX}/control/fabrics"


# =============================================================================
# Test: control() method
# =============================================================================


def test_base_paths_00500():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify control() with no segments
    """
    with does_not_raise():
        result = BasePath.control()
    assert result == CONTROL_PREFIX


def test_base_paths_00510():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify control() with segments
    """
    with does_not_raise():
        result = BasePath.control("fabrics", "MyFabric")
    assert result == f"{CONTROL_PREFIX}/fabrics/MyFabric"


# =============================================================================
# Test: control_fabrics() method
# =============================================================================


def test_base_paths_00600():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify control_fabrics() with no segments
    """
    with does_not_raise():
        result = BasePath.control_fabrics()
    assert result == CONTROL_FABRICS_PREFIX


def test_base_paths_00610():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify control_fabrics() with fabric_name
    """
    with does_not_raise():
        result = BasePath.control_fabrics("MyFabric")
    assert result == f"{CONTROL_FABRICS_PREFIX}/MyFabric"


def test_base_paths_00620():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify control_fabrics() with fabric_name and operation
    """
    with does_not_raise():
        result = BasePath.control_fabrics("MyFabric", "config-deploy")
    assert result == f"{CONTROL_FABRICS_PREFIX}/MyFabric/config-deploy"


def test_base_paths_00630():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify control_fabrics() with fabric_name, operation, and switch_id
    """
    with does_not_raise():
        result = BasePath.control_fabrics("MyFabric", "config-deploy", "CHM1234567")
    assert result == f"{CONTROL_FABRICS_PREFIX}/MyFabric/config-deploy/CHM1234567"


def test_base_paths_00640():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify control_fabrics() with maintenance mode path
    """
    with does_not_raise():
        result = BasePath.control_fabrics("MyFabric", "maintenance-mode", "FDO12345678", "deploy")
    assert result == f"{CONTROL_FABRICS_PREFIX}/MyFabric/maintenance-mode/FDO12345678/deploy"


# =============================================================================
# Test: control_switches() method
# =============================================================================


def test_base_paths_00700():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify control_switches() with no segments
    """
    with does_not_raise():
        result = BasePath.control_switches()
    assert result == CONTROL_SWITCHES_PREFIX


def test_base_paths_00710():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify control_switches() with fabric_name
    """
    with does_not_raise():
        result = BasePath.control_switches("MyFabric")
    assert result == f"{CONTROL_SWITCHES_PREFIX}/MyFabric"


def test_base_paths_00720():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify control_switches() with fabric_name and operation
    """
    with does_not_raise():
        result = BasePath.control_switches("MyFabric", "overview")
    assert result == f"{CONTROL_SWITCHES_PREFIX}/MyFabric/overview"


# =============================================================================
# Test: inventory() method
# =============================================================================


def test_base_paths_00800():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify inventory() with no segments
    """
    with does_not_raise():
        result = BasePath.inventory()
    assert result == INVENTORY_PREFIX


def test_base_paths_00810():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify inventory() with segments
    """
    with does_not_raise():
        result = BasePath.inventory("discover", "switches")
    assert result == f"{INVENTORY_PREFIX}/discover/switches"


# =============================================================================
# Test: configtemplate() method
# =============================================================================


def test_base_paths_00900():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify configtemplate() with no segments
    """
    with does_not_raise():
        result = BasePath.configtemplate()
    assert result == CONFIGTEMPLATE_PREFIX


def test_base_paths_00910():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify configtemplate() with segments
    """
    with does_not_raise():
        result = BasePath.configtemplate("rest", "config", "templates")
    assert result == f"{CONFIGTEMPLATE_PREFIX}/rest/config/templates"


# =============================================================================
# Test: onemanage() method
# =============================================================================


def test_base_paths_01000():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage() with no segments
    """
    with does_not_raise():
        result = BasePath.onemanage()
    assert result == ONEMANAGE_PREFIX


def test_base_paths_01010():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage() with single segment
    """
    with does_not_raise():
        result = BasePath.onemanage("fabrics")
    assert result == f"{ONEMANAGE_PREFIX}/fabrics"


def test_base_paths_01020():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage() with multiple segments
    """
    with does_not_raise():
        result = BasePath.onemanage("fabrics", "MyFabric")
    assert result == f"{ONEMANAGE_PREFIX}/fabrics/MyFabric"


# =============================================================================
# Test: onemanage_fabrics() method
# =============================================================================


def test_base_paths_01100():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_fabrics() with no segments
    """
    with does_not_raise():
        result = BasePath.onemanage_fabrics()
    assert result == ONEMANAGE_FABRICS_PREFIX


def test_base_paths_01110():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_fabrics() with fabric_name
    """
    with does_not_raise():
        result = BasePath.onemanage_fabrics("MyFabric")
    assert result == f"{ONEMANAGE_FABRICS_PREFIX}/MyFabric"


def test_base_paths_01120():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_fabrics() with multiple segments
    """
    with does_not_raise():
        result = BasePath.onemanage_fabrics("MyFabric", "details")
    assert result == f"{ONEMANAGE_FABRICS_PREFIX}/MyFabric/details"


# =============================================================================
# Test: onemanage_top_down() method
# =============================================================================


def test_base_paths_01200():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_top_down() with no segments
    """
    with does_not_raise():
        result = BasePath.onemanage_top_down()
    assert result == ONEMANAGE_TOP_DOWN_PREFIX


def test_base_paths_01210():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_top_down() with single segment
    """
    with does_not_raise():
        result = BasePath.onemanage_top_down("fabrics")
    assert result == f"{ONEMANAGE_TOP_DOWN_PREFIX}/fabrics"


def test_base_paths_01220():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_top_down() with multiple segments
    """
    with does_not_raise():
        result = BasePath.onemanage_top_down("fabrics", "MyFabric")
    assert result == f"{ONEMANAGE_TOP_DOWN_PREFIX}/fabrics/MyFabric"


# =============================================================================
# Test: onemanage_top_down_fabrics() method
# =============================================================================


def test_base_paths_01300():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_top_down_fabrics() with no segments
    """
    with does_not_raise():
        result = BasePath.onemanage_top_down_fabrics()
    assert result == ONEMANAGE_TOP_DOWN_FABRICS_PREFIX


def test_base_paths_01310():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_top_down_fabrics() with fabric_name
    """
    with does_not_raise():
        result = BasePath.onemanage_top_down_fabrics("MyFabric")
    assert result == f"{ONEMANAGE_TOP_DOWN_FABRICS_PREFIX}/MyFabric"


def test_base_paths_01320():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_top_down_fabrics() with bulk-delete vrfs
    """
    with does_not_raise():
        result = BasePath.onemanage_top_down_fabrics("MyFabric", "bulk-delete", "vrfs")
    assert result == f"{ONEMANAGE_TOP_DOWN_FABRICS_PREFIX}/MyFabric/bulk-delete/vrfs"


def test_base_paths_01330():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_top_down_fabrics() with bulk-delete networks
    """
    with does_not_raise():
        result = BasePath.onemanage_top_down_fabrics("MyFabric", "bulk-delete", "networks")
    assert result == f"{ONEMANAGE_TOP_DOWN_FABRICS_PREFIX}/MyFabric/bulk-delete/networks"


def test_base_paths_01340():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_top_down_fabrics() with vrf update path
    """
    with does_not_raise():
        result = BasePath.onemanage_top_down_fabrics("MyFabric", "vrfs", "VRF-1")
    assert result == f"{ONEMANAGE_TOP_DOWN_FABRICS_PREFIX}/MyFabric/vrfs/VRF-1"


def test_base_paths_01350():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify onemanage_top_down_fabrics() with network update path
    """
    with does_not_raise():
        result = BasePath.onemanage_top_down_fabrics("MyFabric", "networks", "Network-1")
    assert result == f"{ONEMANAGE_TOP_DOWN_FABRICS_PREFIX}/MyFabric/networks/Network-1"


# =============================================================================
# Test: Method Chaining and Composition
# =============================================================================


def test_base_paths_02000():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify method composition: control_fabrics() uses control()
    """
    with does_not_raise():
        direct_result = BasePath.control_fabrics("TestFabric")
        composed_result = BasePath.control("fabrics", "TestFabric")
    assert direct_result == composed_result


def test_base_paths_02010():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify method composition: lan_fabric() uses v1()
    """
    with does_not_raise():
        direct_result = BasePath.lan_fabric("rest")
        composed_result = BasePath.v1("lan-fabric", "rest")
    assert direct_result == composed_result


def test_base_paths_02020():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify method composition: onemanage_fabrics() uses onemanage()
    """
    with does_not_raise():
        direct_result = BasePath.onemanage_fabrics("TestFabric")
        composed_result = BasePath.onemanage("fabrics", "TestFabric")
    assert direct_result == composed_result


def test_base_paths_02030():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify method composition: onemanage_top_down_fabrics() uses onemanage_top_down()
    """
    with does_not_raise():
        direct_result = BasePath.onemanage_top_down_fabrics("TestFabric")
        composed_result = BasePath.onemanage_top_down("fabrics", "TestFabric")
    assert direct_result == composed_result


# =============================================================================
# Test: Edge Cases
# =============================================================================


def test_base_paths_03000():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify empty string segment is handled correctly
    """
    with does_not_raise():
        result = BasePath.control_fabrics("MyFabric", "", "config-deploy")
    assert result == f"{CONTROL_FABRICS_PREFIX}/MyFabric//config-deploy"
    # Note: Empty strings create double slashes - this is expected behavior


def test_base_paths_03010():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify path with special characters in fabric name
    """
    with does_not_raise():
        result = BasePath.control_fabrics("My-Fabric_123")
    assert result == f"{CONTROL_FABRICS_PREFIX}/My-Fabric_123"


def test_base_paths_03020():
    """
    ### Class
    - BasePath

    ### Summary
    - Verify path with spaces (should not URL-encode)
    """
    with does_not_raise():
        result = BasePath.control_fabrics("My Fabric")
    assert result == f"{CONTROL_FABRICS_PREFIX}/My Fabric"
    # Note: BasePath doesn't URL-encode - that's the caller's responsibility
