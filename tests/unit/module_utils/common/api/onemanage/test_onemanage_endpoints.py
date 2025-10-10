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

"""Unit tests for api/onemanage/endpoints.py"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name

import pytest  # pylint: disable=unused-import,import-error
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.onemanage.endpoints import (
    EpOneManageFabricConfigDeploy,
    EpOneManageFabricConfigDeploySwitch,
    EpOneManageFabricConfigPreview,
    EpOneManageFabricConfigPreviewSwitch,
    EpOneManageFabricConfigSave,
    EpOneManageFabricCreate,
    EpOneManageFabricDelete,
    EpOneManageFabricDetails,
    EpOneManageFabricGroupMembersGet,
    EpOneManageFabricGroupUpdate,
    EpOneManageFabricsGet,
    EpOneManageFabricUpdate,
    EpOneManageLinkCreate,
    EpOneManageLinkGetByUuid,
    EpOneManageLinksDelete,
    EpOneManageLinksGetByFabric,
    EpOneManageLinkUpdate,
    EpOneManageNetworkCreate,
    EpOneManageNetworksDelete,
    EpOneManageNetworksGet,
    EpOneManageNetworkUpdate,
    EpOneManageVrfCreate,
    EpOneManageVrfsDelete,
    EpOneManageVrfsGet,
    EpOneManageVrfUpdate,
    FabricConfigDeployQueryParams,
    FabricConfigPreviewQueryParams,
    LinkByUuidQueryParams,
    NetworkNamesQueryParams,
    VrfNamesQueryParams,
)
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import does_not_raise
from pydantic import ValidationError

# =============================================================================
# Constants
# =============================================================================

ONEMANAGE_FABRICS_PATH = "/appcenter/cisco/ndfc/api/v1/onemanage/fabrics"
ONEMANAGE_LINKS_PATH = "/appcenter/cisco/ndfc/api/v1/onemanage/links"
ONEMANAGE_TOP_DOWN_FABRICS_PATH = "/appcenter/cisco/ndfc/api/v1/onemanage/top-down/fabrics"


# =============================================================================
# Test: NetworkNamesQueryParams
# =============================================================================


def test_onemanage_endpoints_00100():
    """
    ### Class
    - NetworkNamesQueryParams

    ### Summary
    - Verify to_query_string() with network_names set
    """
    with does_not_raise():
        params = NetworkNamesQueryParams()
        params.network_names = "Net1,Net2,Net3"
        result = params.to_query_string()
    assert result == "network-names=Net1,Net2,Net3"


def test_onemanage_endpoints_00110():
    """
    ### Class
    - NetworkNamesQueryParams

    ### Summary
    - Verify to_query_string() with no network_names set
    """
    with does_not_raise():
        params = NetworkNamesQueryParams()
        result = params.to_query_string()
    assert result == ""


def test_onemanage_endpoints_00120():
    """
    ### Class
    - NetworkNamesQueryParams

    ### Summary
    - Verify is_empty() returns True when no values set
    """
    with does_not_raise():
        params = NetworkNamesQueryParams()
        result = params.is_empty()
    assert result is True


def test_onemanage_endpoints_00130():
    """
    ### Class
    - NetworkNamesQueryParams

    ### Summary
    - Verify is_empty() returns False when network_names set
    """
    with does_not_raise():
        params = NetworkNamesQueryParams()
        params.network_names = "Net1"
        result = params.is_empty()
    assert result is False


def test_onemanage_endpoints_00140():
    """
    ### Class
    - NetworkNamesQueryParams

    ### Summary
    - Verify validation error with empty string during initialization
    """
    with pytest.raises(ValidationError):
        NetworkNamesQueryParams(network_names="")


def test_onemanage_endpoints_00150():
    """
    ### Class
    - NetworkNamesQueryParams

    ### Summary
    - Verify special characters in network names
    """
    with does_not_raise():
        params = NetworkNamesQueryParams()
        params.network_names = "Net_1,Net-2,Net.3"
        result = params.to_query_string()
    assert result == "network-names=Net_1,Net-2,Net.3"


# =============================================================================
# Test: VrfNamesQueryParams
# =============================================================================


def test_onemanage_endpoints_00200():
    """
    ### Class
    - VrfNamesQueryParams

    ### Summary
    - Verify to_query_string() with vrf_names set
    """
    with does_not_raise():
        params = VrfNamesQueryParams()
        params.vrf_names = "VRF1,VRF2,VRF3"
        result = params.to_query_string()
    assert result == "vrf-names=VRF1,VRF2,VRF3"


def test_onemanage_endpoints_00210():
    """
    ### Class
    - VrfNamesQueryParams

    ### Summary
    - Verify to_query_string() with no vrf_names set
    """
    with does_not_raise():
        params = VrfNamesQueryParams()
        result = params.to_query_string()
    assert result == ""


def test_onemanage_endpoints_00220():
    """
    ### Class
    - VrfNamesQueryParams

    ### Summary
    - Verify is_empty() returns True when no values set
    """
    with does_not_raise():
        params = VrfNamesQueryParams()
        result = params.is_empty()
    assert result is True


def test_onemanage_endpoints_00230():
    """
    ### Class
    - VrfNamesQueryParams

    ### Summary
    - Verify is_empty() returns False when vrf_names set
    """
    with does_not_raise():
        params = VrfNamesQueryParams()
        params.vrf_names = "VRF1"
        result = params.is_empty()
    assert result is False


def test_onemanage_endpoints_00240():
    """
    ### Class
    - VrfNamesQueryParams

    ### Summary
    - Verify validation error with empty string during initialization
    """
    with pytest.raises(ValidationError):
        VrfNamesQueryParams(vrf_names="")


def test_onemanage_endpoints_00250():
    """
    ### Class
    - VrfNamesQueryParams

    ### Summary
    - Verify special characters in VRF names
    """
    with does_not_raise():
        params = VrfNamesQueryParams()
        params.vrf_names = "VRF_1,VRF-2,VRF.3"
        result = params.to_query_string()
    assert result == "vrf-names=VRF_1,VRF-2,VRF.3"


# =============================================================================
# Test: EpOneManageFabricCreate
# =============================================================================


def test_onemanage_endpoints_00300():
    """
    ### Class
    - EpOneManageFabricCreate

    ### Summary
    - Verify path property returns correct endpoint
    """
    with does_not_raise():
        endpoint = EpOneManageFabricCreate()
        result = endpoint.path
    assert result == ONEMANAGE_FABRICS_PATH


def test_onemanage_endpoints_00310():
    """
    ### Class
    - EpOneManageFabricCreate

    ### Summary
    - Verify verb property returns POST
    """
    with does_not_raise():
        endpoint = EpOneManageFabricCreate()
        result = endpoint.verb
    assert result == "POST"


def test_onemanage_endpoints_00320():
    """
    ### Class
    - EpOneManageFabricCreate

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageFabricCreate()
        result = endpoint.class_name
    assert result == "EpOneManageFabricCreate"


# =============================================================================
# Test: EpOneManageFabricDetails
# =============================================================================


def test_onemanage_endpoints_00400():
    """
    ### Class
    - EpOneManageFabricDetails

    ### Summary
    - Verify path property with fabric_name set
    """
    with does_not_raise():
        endpoint = EpOneManageFabricDetails()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_FABRICS_PATH}/MyFabric"


def test_onemanage_endpoints_00410():
    """
    ### Class
    - EpOneManageFabricDetails

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageFabricDetails()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_00420():
    """
    ### Class
    - EpOneManageFabricDetails

    ### Summary
    - Verify verb property returns GET
    """
    with does_not_raise():
        endpoint = EpOneManageFabricDetails()
        result = endpoint.verb
    assert result == "GET"


def test_onemanage_endpoints_00430():
    """
    ### Class
    - EpOneManageFabricDetails

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageFabricDetails()
        result = endpoint.class_name
    assert result == "EpOneManageFabricDetails"


def test_onemanage_endpoints_00440():
    """
    ### Class
    - EpOneManageFabricDetails

    ### Summary
    - Verify path with special characters in fabric_name
    """
    with does_not_raise():
        endpoint = EpOneManageFabricDetails()
        endpoint.fabric_name = "My-Fabric_123"
        result = endpoint.path
    assert result == f"{ONEMANAGE_FABRICS_PATH}/My-Fabric_123"


def test_onemanage_endpoints_00450():
    """
    ### Class
    - EpOneManageFabricDetails

    ### Summary
    - Verify validation error with empty fabric_name during initialization
    """
    with pytest.raises(ValidationError):
        EpOneManageFabricDetails(fabric_name="")


# =============================================================================
# Test: EpOneManageNetworksDelete
# =============================================================================


def test_onemanage_endpoints_00500():
    """
    ### Class
    - EpOneManageNetworksDelete

    ### Summary
    - Verify path with fabric_name and network_names query param
    """
    with does_not_raise():
        endpoint = EpOneManageNetworksDelete()
        endpoint.fabric_name = "MyFabric"
        endpoint.query_params.network_names = "Net1,Net2,Net3"
        result = endpoint.path
    expected = f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/MyFabric/bulk-delete/networks?network-names=Net1,Net2,Net3"
    assert result == expected


def test_onemanage_endpoints_00510():
    """
    ### Class
    - EpOneManageNetworksDelete

    ### Summary
    - Verify path without query parameters
    """
    with does_not_raise():
        endpoint = EpOneManageNetworksDelete()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    expected = f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/MyFabric/bulk-delete/networks"
    assert result == expected


def test_onemanage_endpoints_00520():
    """
    ### Class
    - EpOneManageNetworksDelete

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageNetworksDelete()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_00530():
    """
    ### Class
    - EpOneManageNetworksDelete

    ### Summary
    - Verify verb property returns DELETE
    """
    with does_not_raise():
        endpoint = EpOneManageNetworksDelete()
        result = endpoint.verb
    assert result == "DELETE"


def test_onemanage_endpoints_00540():
    """
    ### Class
    - EpOneManageNetworksDelete

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageNetworksDelete()
        result = endpoint.class_name
    assert result == "EpOneManageNetworksDelete"


def test_onemanage_endpoints_00550():
    """
    ### Class
    - EpOneManageNetworksDelete

    ### Summary
    - Verify query_params initialized as NetworkNamesQueryParams
    """
    with does_not_raise():
        endpoint = EpOneManageNetworksDelete()
        result = isinstance(endpoint.query_params, NetworkNamesQueryParams)
    assert result is True


def test_onemanage_endpoints_00560():
    """
    ### Class
    - EpOneManageNetworksDelete

    ### Summary
    - Verify path with special characters in fabric and network names
    """
    with does_not_raise():
        endpoint = EpOneManageNetworksDelete()
        endpoint.fabric_name = "My-Fabric_123"
        endpoint.query_params.network_names = "Net_1,Net-2"
        result = endpoint.path
    expected = f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/My-Fabric_123/bulk-delete/networks?network-names=Net_1,Net-2"
    assert result == expected


# =============================================================================
# Test: EpOneManageNetworkUpdate
# =============================================================================


def test_onemanage_endpoints_00600():
    """
    ### Class
    - EpOneManageNetworkUpdate

    ### Summary
    - Verify path with fabric_name and network_name set
    """
    with does_not_raise():
        endpoint = EpOneManageNetworkUpdate()
        endpoint.fabric_name = "MyFabric"
        endpoint.network_name = "MyNetwork"
        result = endpoint.path
    expected = f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/MyFabric/networks/MyNetwork"
    assert result == expected


def test_onemanage_endpoints_00610():
    """
    ### Class
    - EpOneManageNetworkUpdate

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageNetworkUpdate()
        endpoint.network_name = "MyNetwork"
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_00620():
    """
    ### Class
    - EpOneManageNetworkUpdate

    ### Summary
    - Verify path raises ValueError when network_name not set
    """
    with pytest.raises(ValueError, match="network_name must be set"):
        endpoint = EpOneManageNetworkUpdate()
        endpoint.fabric_name = "MyFabric"
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_00630():
    """
    ### Class
    - EpOneManageNetworkUpdate

    ### Summary
    - Verify path raises ValueError when neither parameter set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageNetworkUpdate()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_00640():
    """
    ### Class
    - EpOneManageNetworkUpdate

    ### Summary
    - Verify verb property returns PUT
    """
    with does_not_raise():
        endpoint = EpOneManageNetworkUpdate()
        result = endpoint.verb
    assert result == "PUT"


def test_onemanage_endpoints_00650():
    """
    ### Class
    - EpOneManageNetworkUpdate

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageNetworkUpdate()
        result = endpoint.class_name
    assert result == "EpOneManageNetworkUpdate"


def test_onemanage_endpoints_00660():
    """
    ### Class
    - EpOneManageNetworkUpdate

    ### Summary
    - Verify path with special characters in names
    """
    with does_not_raise():
        endpoint = EpOneManageNetworkUpdate()
        endpoint.fabric_name = "My-Fabric_123"
        endpoint.network_name = "Net_1"
        result = endpoint.path
    expected = f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/My-Fabric_123/networks/Net_1"
    assert result == expected


def test_onemanage_endpoints_00670():
    """
    ### Class
    - EpOneManageNetworkUpdate

    ### Summary
    - Verify validation error with empty fabric_name during initialization
    """
    with pytest.raises(ValidationError):
        EpOneManageNetworkUpdate(fabric_name="")


def test_onemanage_endpoints_00680():
    """
    ### Class
    - EpOneManageNetworkUpdate

    ### Summary
    - Verify validation error with empty network_name during initialization
    """
    with pytest.raises(ValidationError):
        EpOneManageNetworkUpdate(network_name="")


# =============================================================================
# Test: EpOneManageVrfsDelete
# =============================================================================


def test_onemanage_endpoints_00700():
    """
    ### Class
    - EpOneManageVrfsDelete

    ### Summary
    - Verify path with fabric_name and vrf_names query param
    """
    with does_not_raise():
        endpoint = EpOneManageVrfsDelete()
        endpoint.fabric_name = "MyFabric"
        endpoint.query_params.vrf_names = "VRF1,VRF2,VRF3"
        result = endpoint.path
    expected = f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/MyFabric/bulk-delete/vrfs?vrf-names=VRF1,VRF2,VRF3"
    assert result == expected


def test_onemanage_endpoints_00710():
    """
    ### Class
    - EpOneManageVrfsDelete

    ### Summary
    - Verify path without query parameters
    """
    with does_not_raise():
        endpoint = EpOneManageVrfsDelete()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    expected = f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/MyFabric/bulk-delete/vrfs"
    assert result == expected


def test_onemanage_endpoints_00720():
    """
    ### Class
    - EpOneManageVrfsDelete

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageVrfsDelete()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_00730():
    """
    ### Class
    - EpOneManageVrfsDelete

    ### Summary
    - Verify verb property returns DELETE
    """
    with does_not_raise():
        endpoint = EpOneManageVrfsDelete()
        result = endpoint.verb
    assert result == "DELETE"


def test_onemanage_endpoints_00740():
    """
    ### Class
    - EpOneManageVrfsDelete

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageVrfsDelete()
        result = endpoint.class_name
    assert result == "EpOneManageVrfsDelete"


def test_onemanage_endpoints_00750():
    """
    ### Class
    - EpOneManageVrfsDelete

    ### Summary
    - Verify query_params initialized as VrfNamesQueryParams
    """
    with does_not_raise():
        endpoint = EpOneManageVrfsDelete()
        result = isinstance(endpoint.query_params, VrfNamesQueryParams)
    assert result is True


def test_onemanage_endpoints_00760():
    """
    ### Class
    - EpOneManageVrfsDelete

    ### Summary
    - Verify path with special characters in fabric and VRF names
    """
    with does_not_raise():
        endpoint = EpOneManageVrfsDelete()
        endpoint.fabric_name = "My-Fabric_123"
        endpoint.query_params.vrf_names = "VRF_1,VRF-2"
        result = endpoint.path
    expected = f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/My-Fabric_123/bulk-delete/vrfs?vrf-names=VRF_1,VRF-2"
    assert result == expected


# =============================================================================
# Test: EpOneManageVrfUpdate
# =============================================================================


def test_onemanage_endpoints_00800():
    """
    ### Class
    - EpOneManageVrfUpdate

    ### Summary
    - Verify path with fabric_name and vrf_name set
    """
    with does_not_raise():
        endpoint = EpOneManageVrfUpdate()
        endpoint.fabric_name = "MyFabric"
        endpoint.vrf_name = "MyVRF"
        result = endpoint.path
    expected = f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/MyFabric/vrfs/MyVRF"
    assert result == expected


def test_onemanage_endpoints_00810():
    """
    ### Class
    - EpOneManageVrfUpdate

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageVrfUpdate()
        endpoint.vrf_name = "MyVRF"
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_00820():
    """
    ### Class
    - EpOneManageVrfUpdate

    ### Summary
    - Verify path raises ValueError when vrf_name not set
    """
    with pytest.raises(ValueError, match="vrf_name must be set"):
        endpoint = EpOneManageVrfUpdate()
        endpoint.fabric_name = "MyFabric"
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_00830():
    """
    ### Class
    - EpOneManageVrfUpdate

    ### Summary
    - Verify path raises ValueError when neither parameter set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageVrfUpdate()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_00840():
    """
    ### Class
    - EpOneManageVrfUpdate

    ### Summary
    - Verify verb property returns PUT
    """
    with does_not_raise():
        endpoint = EpOneManageVrfUpdate()
        result = endpoint.verb
    assert result == "PUT"


def test_onemanage_endpoints_00850():
    """
    ### Class
    - EpOneManageVrfUpdate

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageVrfUpdate()
        result = endpoint.class_name
    assert result == "EpOneManageVrfUpdate"


def test_onemanage_endpoints_00860():
    """
    ### Class
    - EpOneManageVrfUpdate

    ### Summary
    - Verify path with special characters in names
    """
    with does_not_raise():
        endpoint = EpOneManageVrfUpdate()
        endpoint.fabric_name = "My-Fabric_123"
        endpoint.vrf_name = "VRF_1"
        result = endpoint.path
    expected = f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/My-Fabric_123/vrfs/VRF_1"
    assert result == expected


def test_onemanage_endpoints_00870():
    """
    ### Class
    - EpOneManageVrfUpdate

    ### Summary
    - Verify validation error with empty fabric_name during initialization
    """
    with pytest.raises(ValidationError):
        EpOneManageVrfUpdate(fabric_name="")


def test_onemanage_endpoints_00880():
    """
    ### Class
    - EpOneManageVrfUpdate

    ### Summary
    - Verify validation error with empty vrf_name during initialization
    """
    with pytest.raises(ValidationError):
        EpOneManageVrfUpdate(vrf_name="")


# =============================================================================
# Test: FabricConfigPreviewQueryParams
# =============================================================================


def test_onemanage_endpoints_00900():
    """
    ### Class
    - FabricConfigPreviewQueryParams

    ### Summary
    - Verify to_query_string() with both parameters set
    """
    with does_not_raise():
        params = FabricConfigPreviewQueryParams()
        params.force_show_run = "true"
        params.show_brief = "false"
        result = params.to_query_string()
    assert result == "forceShowRun=true&showBrief=false"


def test_onemanage_endpoints_00910():
    """
    ### Class
    - FabricConfigPreviewQueryParams

    ### Summary
    - Verify to_query_string() with defaults
    """
    with does_not_raise():
        params = FabricConfigPreviewQueryParams()
        result = params.to_query_string()
    assert result == "forceShowRun=false&showBrief=false"


def test_onemanage_endpoints_00920():
    """
    ### Class
    - FabricConfigPreviewQueryParams

    ### Summary
    - Verify validation error with invalid force_show_run value
    """
    with pytest.raises(ValidationError):
        FabricConfigPreviewQueryParams(force_show_run="yes")


def test_onemanage_endpoints_00930():
    """
    ### Class
    - FabricConfigPreviewQueryParams

    ### Summary
    - Verify validation error with invalid show_brief value
    """
    with pytest.raises(ValidationError):
        FabricConfigPreviewQueryParams(show_brief="invalid")


# =============================================================================
# Test: FabricConfigDeployQueryParams
# =============================================================================


def test_onemanage_endpoints_01000():
    """
    ### Class
    - FabricConfigDeployQueryParams

    ### Summary
    - Verify to_query_string() with both parameters set
    """
    with does_not_raise():
        params = FabricConfigDeployQueryParams()
        params.force_show_run = "true"
        params.incl_all_msd_switches = "true"
        result = params.to_query_string()
    assert result == "forceShowRun=true&inclAllMSDSwitches=true"


def test_onemanage_endpoints_01010():
    """
    ### Class
    - FabricConfigDeployQueryParams

    ### Summary
    - Verify to_query_string() with defaults
    """
    with does_not_raise():
        params = FabricConfigDeployQueryParams()
        result = params.to_query_string()
    assert result == "forceShowRun=false&inclAllMSDSwitches=false"


def test_onemanage_endpoints_01020():
    """
    ### Class
    - FabricConfigDeployQueryParams

    ### Summary
    - Verify validation error with invalid force_show_run value
    """
    with pytest.raises(ValidationError):
        FabricConfigDeployQueryParams(force_show_run="invalid")


def test_onemanage_endpoints_01030():
    """
    ### Class
    - FabricConfigDeployQueryParams

    ### Summary
    - Verify validation error with invalid incl_all_msd_switches value
    """
    with pytest.raises(ValidationError):
        FabricConfigDeployQueryParams(incl_all_msd_switches="yes")


# =============================================================================
# Test: LinkByUuidQueryParams
# =============================================================================


def test_onemanage_endpoints_01100():
    """
    ### Class
    - LinkByUuidQueryParams

    ### Summary
    - Verify to_query_string() with both cluster names set
    """
    with does_not_raise():
        params = LinkByUuidQueryParams()
        params.source_cluster_name = "nd-cluster-1"
        params.destination_cluster_name = "nd-cluster-2"
        result = params.to_query_string()
    assert result == "sourceClusterName=nd-cluster-1&destinationClusterName=nd-cluster-2"


def test_onemanage_endpoints_01110():
    """
    ### Class
    - LinkByUuidQueryParams

    ### Summary
    - Verify to_query_string() with no parameters set
    """
    with does_not_raise():
        params = LinkByUuidQueryParams()
        result = params.to_query_string()
    assert result == ""


def test_onemanage_endpoints_01120():
    """
    ### Class
    - LinkByUuidQueryParams

    ### Summary
    - Verify to_query_string() with only source cluster name
    """
    with does_not_raise():
        params = LinkByUuidQueryParams()
        params.source_cluster_name = "nd-cluster-1"
        result = params.to_query_string()
    assert result == "sourceClusterName=nd-cluster-1"


def test_onemanage_endpoints_01130():
    """
    ### Class
    - LinkByUuidQueryParams

    ### Summary
    - Verify validation error with empty source_cluster_name
    """
    with pytest.raises(ValidationError):
        LinkByUuidQueryParams(source_cluster_name="")


# =============================================================================
# Test: EpOneManageFabricConfigSave
# =============================================================================


def test_onemanage_endpoints_01200():
    """
    ### Class
    - EpOneManageFabricConfigSave

    ### Summary
    - Verify path with fabric_name set
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigSave()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_FABRICS_PATH}/MyFabric/config-save"


def test_onemanage_endpoints_01210():
    """
    ### Class
    - EpOneManageFabricConfigSave

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageFabricConfigSave()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_01220():
    """
    ### Class
    - EpOneManageFabricConfigSave

    ### Summary
    - Verify verb property returns POST
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigSave()
        result = endpoint.verb
    assert result == "POST"


def test_onemanage_endpoints_01230():
    """
    ### Class
    - EpOneManageFabricConfigSave

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigSave()
        result = endpoint.class_name
    assert result == "EpOneManageFabricConfigSave"


# =============================================================================
# Test: EpOneManageFabricConfigPreview
# =============================================================================


def test_onemanage_endpoints_01300():
    """
    ### Class
    - EpOneManageFabricConfigPreview

    ### Summary
    - Verify path with fabric_name and query parameters set
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigPreview()
        endpoint.fabric_name = "MyFabric"
        endpoint.query_params.force_show_run = "true"
        endpoint.query_params.show_brief = "false"
        result = endpoint.path
    assert result == f"{ONEMANAGE_FABRICS_PATH}/MyFabric/config-preview?forceShowRun=true&showBrief=false"


def test_onemanage_endpoints_01310():
    """
    ### Class
    - EpOneManageFabricConfigPreview

    ### Summary
    - Verify path without query parameters
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigPreview()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_FABRICS_PATH}/MyFabric/config-preview?forceShowRun=false&showBrief=false"


def test_onemanage_endpoints_01320():
    """
    ### Class
    - EpOneManageFabricConfigPreview

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageFabricConfigPreview()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_01330():
    """
    ### Class
    - EpOneManageFabricConfigPreview

    ### Summary
    - Verify verb property returns GET
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigPreview()
        result = endpoint.verb
    assert result == "GET"


def test_onemanage_endpoints_01340():
    """
    ### Class
    - EpOneManageFabricConfigPreview

    ### Summary
    - Verify query_params initialized as FabricConfigPreviewQueryParams
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigPreview()
        result = isinstance(endpoint.query_params, FabricConfigPreviewQueryParams)
    assert result is True


# =============================================================================
# Test: EpOneManageFabricConfigDeploy
# =============================================================================


def test_onemanage_endpoints_01400():
    """
    ### Class
    - EpOneManageFabricConfigDeploy

    ### Summary
    - Verify path with fabric_name and query parameters set
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigDeploy()
        endpoint.fabric_name = "MyFabric"
        endpoint.query_params.force_show_run = "true"
        endpoint.query_params.incl_all_msd_switches = "false"
        result = endpoint.path
    assert result == f"{ONEMANAGE_FABRICS_PATH}/MyFabric/config-deploy?forceShowRun=true&inclAllMSDSwitches=false"


def test_onemanage_endpoints_01410():
    """
    ### Class
    - EpOneManageFabricConfigDeploy

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageFabricConfigDeploy()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_01420():
    """
    ### Class
    - EpOneManageFabricConfigDeploy

    ### Summary
    - Verify verb property returns POST
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigDeploy()
        result = endpoint.verb
    assert result == "POST"


def test_onemanage_endpoints_01430():
    """
    ### Class
    - EpOneManageFabricConfigDeploy

    ### Summary
    - Verify query_params initialized as FabricConfigDeployQueryParams
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigDeploy()
        result = isinstance(endpoint.query_params, FabricConfigDeployQueryParams)
    assert result is True


# =============================================================================
# Test: EpOneManageLinksGetByFabric
# =============================================================================


def test_onemanage_endpoints_01500():
    """
    ### Class
    - EpOneManageLinksGetByFabric

    ### Summary
    - Verify path with fabric_name set
    """
    with does_not_raise():
        endpoint = EpOneManageLinksGetByFabric()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_LINKS_PATH}/fabrics/MyFabric"


def test_onemanage_endpoints_01510():
    """
    ### Class
    - EpOneManageLinksGetByFabric

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageLinksGetByFabric()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_01520():
    """
    ### Class
    - EpOneManageLinksGetByFabric

    ### Summary
    - Verify verb property returns GET
    """
    with does_not_raise():
        endpoint = EpOneManageLinksGetByFabric()
        result = endpoint.verb
    assert result == "GET"


def test_onemanage_endpoints_01530():
    """
    ### Class
    - EpOneManageLinksGetByFabric

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageLinksGetByFabric()
        result = endpoint.class_name
    assert result == "EpOneManageLinksGetByFabric"


# =============================================================================
# Test: EpOneManageFabricDelete
# =============================================================================


def test_onemanage_endpoints_01600():
    """
    ### Class
    - EpOneManageFabricDelete

    ### Summary
    - Verify path with fabric_name set
    """
    with does_not_raise():
        endpoint = EpOneManageFabricDelete()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_FABRICS_PATH}/MyFabric"


def test_onemanage_endpoints_01610():
    """
    ### Class
    - EpOneManageFabricDelete

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageFabricDelete()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_01620():
    """
    ### Class
    - EpOneManageFabricDelete

    ### Summary
    - Verify verb property returns DELETE
    """
    with does_not_raise():
        endpoint = EpOneManageFabricDelete()
        result = endpoint.verb
    assert result == "DELETE"


def test_onemanage_endpoints_01630():
    """
    ### Class
    - EpOneManageFabricDelete

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageFabricDelete()
        result = endpoint.class_name
    assert result == "EpOneManageFabricDelete"


# =============================================================================
# Test: EpOneManageNetworkCreate
# =============================================================================


def test_onemanage_endpoints_01700():
    """
    ### Class
    - EpOneManageNetworkCreate

    ### Summary
    - Verify path with fabric_name set
    """
    with does_not_raise():
        endpoint = EpOneManageNetworkCreate()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/MyFabric/networks"


def test_onemanage_endpoints_01710():
    """
    ### Class
    - EpOneManageNetworkCreate

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageNetworkCreate()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_01720():
    """
    ### Class
    - EpOneManageNetworkCreate

    ### Summary
    - Verify verb property returns POST
    """
    with does_not_raise():
        endpoint = EpOneManageNetworkCreate()
        result = endpoint.verb
    assert result == "POST"


def test_onemanage_endpoints_01730():
    """
    ### Class
    - EpOneManageNetworkCreate

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageNetworkCreate()
        result = endpoint.class_name
    assert result == "EpOneManageNetworkCreate"


# =============================================================================
# Test: EpOneManageLinkGetByUuid
# =============================================================================


def test_onemanage_endpoints_01800():
    """
    ### Class
    - EpOneManageLinkGetByUuid

    ### Summary
    - Verify path with link_uuid and query parameters
    """
    with does_not_raise():
        endpoint = EpOneManageLinkGetByUuid()
        endpoint.link_uuid = "63505f61-ce7b-40a6-a38c-ae9a355b2116"
        endpoint.query_params.source_cluster_name = "nd-cluster-1"
        endpoint.query_params.destination_cluster_name = "nd-cluster-2"
        result = endpoint.path
    expected = f"{ONEMANAGE_LINKS_PATH}/63505f61-ce7b-40a6-a38c-ae9a355b2116?sourceClusterName=nd-cluster-1&destinationClusterName=nd-cluster-2"
    assert result == expected


def test_onemanage_endpoints_01810():
    """
    ### Class
    - EpOneManageLinkGetByUuid

    ### Summary
    - Verify path without query parameters
    """
    with does_not_raise():
        endpoint = EpOneManageLinkGetByUuid()
        endpoint.link_uuid = "63505f61-ce7b-40a6-a38c-ae9a355b2116"
        result = endpoint.path
    assert result == f"{ONEMANAGE_LINKS_PATH}/63505f61-ce7b-40a6-a38c-ae9a355b2116"


def test_onemanage_endpoints_01820():
    """
    ### Class
    - EpOneManageLinkGetByUuid

    ### Summary
    - Verify path raises ValueError when link_uuid not set
    """
    with pytest.raises(ValueError, match="link_uuid must be set"):
        endpoint = EpOneManageLinkGetByUuid()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_01830():
    """
    ### Class
    - EpOneManageLinkGetByUuid

    ### Summary
    - Verify verb property returns GET
    """
    with does_not_raise():
        endpoint = EpOneManageLinkGetByUuid()
        result = endpoint.verb
    assert result == "GET"


def test_onemanage_endpoints_01840():
    """
    ### Class
    - EpOneManageLinkGetByUuid

    ### Summary
    - Verify query_params initialized as LinkByUuidQueryParams
    """
    with does_not_raise():
        endpoint = EpOneManageLinkGetByUuid()
        result = isinstance(endpoint.query_params, LinkByUuidQueryParams)
    assert result is True


# =============================================================================
# Test: EpOneManageFabricsGet
# =============================================================================


def test_onemanage_endpoints_01900():
    """
    ### Class
    - EpOneManageFabricsGet

    ### Summary
    - Verify path property returns correct endpoint
    """
    with does_not_raise():
        endpoint = EpOneManageFabricsGet()
        result = endpoint.path
    assert result == ONEMANAGE_FABRICS_PATH


def test_onemanage_endpoints_01910():
    """
    ### Class
    - EpOneManageFabricsGet

    ### Summary
    - Verify verb property returns GET
    """
    with does_not_raise():
        endpoint = EpOneManageFabricsGet()
        result = endpoint.verb
    assert result == "GET"


def test_onemanage_endpoints_01920():
    """
    ### Class
    - EpOneManageFabricsGet

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageFabricsGet()
        result = endpoint.class_name
    assert result == "EpOneManageFabricsGet"


# =============================================================================
# Test: EpOneManageFabricGroupMembersGet
# =============================================================================


def test_onemanage_endpoints_02000():
    """
    ### Class
    - EpOneManageFabricGroupMembersGet

    ### Summary
    - Verify path with fabric_name set
    """
    with does_not_raise():
        endpoint = EpOneManageFabricGroupMembersGet()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_FABRICS_PATH}/MyFabric/members"


def test_onemanage_endpoints_02010():
    """
    ### Class
    - EpOneManageFabricGroupMembersGet

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageFabricGroupMembersGet()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_02020():
    """
    ### Class
    - EpOneManageFabricGroupMembersGet

    ### Summary
    - Verify verb property returns GET
    """
    with does_not_raise():
        endpoint = EpOneManageFabricGroupMembersGet()
        result = endpoint.verb
    assert result == "GET"


def test_onemanage_endpoints_02030():
    """
    ### Class
    - EpOneManageFabricGroupMembersGet

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageFabricGroupMembersGet()
        result = endpoint.class_name
    assert result == "EpOneManageFabricGroupMembersGet"


# =============================================================================
# Test: EpOneManageFabricConfigPreviewSwitch
# =============================================================================


def test_onemanage_endpoints_02100():
    """
    ### Class
    - EpOneManageFabricConfigPreviewSwitch

    ### Summary
    - Verify path with fabric_name, switch_sn and query parameters
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigPreviewSwitch()
        endpoint.fabric_name = "MyFabric"
        endpoint.switch_sn = "92RZ2OMQCNC"
        endpoint.query_params.force_show_run = "true"
        endpoint.query_params.show_brief = "false"
        result = endpoint.path
    expected = f"{ONEMANAGE_FABRICS_PATH}/MyFabric/config-preview/92RZ2OMQCNC?forceShowRun=true&showBrief=false"
    assert result == expected


def test_onemanage_endpoints_02110():
    """
    ### Class
    - EpOneManageFabricConfigPreviewSwitch

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageFabricConfigPreviewSwitch()
        endpoint.switch_sn = "92RZ2OMQCNC"
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_02120():
    """
    ### Class
    - EpOneManageFabricConfigPreviewSwitch

    ### Summary
    - Verify path raises ValueError when switch_sn not set
    """
    with pytest.raises(ValueError, match="switch_sn must be set"):
        endpoint = EpOneManageFabricConfigPreviewSwitch()
        endpoint.fabric_name = "MyFabric"
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_02130():
    """
    ### Class
    - EpOneManageFabricConfigPreviewSwitch

    ### Summary
    - Verify verb property returns GET
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigPreviewSwitch()
        result = endpoint.verb
    assert result == "GET"


# =============================================================================
# Test: EpOneManageFabricConfigDeploySwitch
# =============================================================================


def test_onemanage_endpoints_02200():
    """
    ### Class
    - EpOneManageFabricConfigDeploySwitch

    ### Summary
    - Verify path with fabric_name, switch_sn and query parameters
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigDeploySwitch()
        endpoint.fabric_name = "MyFabric"
        endpoint.switch_sn = "92RZ2OMQCNC"
        endpoint.query_params.force_show_run = "true"
        endpoint.query_params.incl_all_msd_switches = "false"
        result = endpoint.path
    expected = f"{ONEMANAGE_FABRICS_PATH}/MyFabric/config-deploy/92RZ2OMQCNC?forceShowRun=true&inclAllMSDSwitches=false"
    assert result == expected


def test_onemanage_endpoints_02210():
    """
    ### Class
    - EpOneManageFabricConfigDeploySwitch

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageFabricConfigDeploySwitch()
        endpoint.switch_sn = "92RZ2OMQCNC"
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_02220():
    """
    ### Class
    - EpOneManageFabricConfigDeploySwitch

    ### Summary
    - Verify path raises ValueError when switch_sn not set
    """
    with pytest.raises(ValueError, match="switch_sn must be set"):
        endpoint = EpOneManageFabricConfigDeploySwitch()
        endpoint.fabric_name = "MyFabric"
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_02230():
    """
    ### Class
    - EpOneManageFabricConfigDeploySwitch

    ### Summary
    - Verify verb property returns POST
    """
    with does_not_raise():
        endpoint = EpOneManageFabricConfigDeploySwitch()
        result = endpoint.verb
    assert result == "POST"


# =============================================================================
# Test: EpOneManageFabricUpdate
# =============================================================================


def test_onemanage_endpoints_02300():
    """
    ### Class
    - EpOneManageFabricUpdate

    ### Summary
    - Verify path with fabric_name set
    """
    with does_not_raise():
        endpoint = EpOneManageFabricUpdate()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_FABRICS_PATH}/MyFabric"


def test_onemanage_endpoints_02310():
    """
    ### Class
    - EpOneManageFabricUpdate

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageFabricUpdate()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_02320():
    """
    ### Class
    - EpOneManageFabricUpdate

    ### Summary
    - Verify verb property returns PUT
    """
    with does_not_raise():
        endpoint = EpOneManageFabricUpdate()
        result = endpoint.verb
    assert result == "PUT"


def test_onemanage_endpoints_02330():
    """
    ### Class
    - EpOneManageFabricUpdate

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageFabricUpdate()
        result = endpoint.class_name
    assert result == "EpOneManageFabricUpdate"


# =============================================================================
# Test: EpOneManageVrfsGet
# =============================================================================


def test_onemanage_endpoints_02400():
    """
    ### Class
    - EpOneManageVrfsGet

    ### Summary
    - Verify path with fabric_name set
    """
    with does_not_raise():
        endpoint = EpOneManageVrfsGet()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/MyFabric/vrfs"


def test_onemanage_endpoints_02410():
    """
    ### Class
    - EpOneManageVrfsGet

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageVrfsGet()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_02420():
    """
    ### Class
    - EpOneManageVrfsGet

    ### Summary
    - Verify verb property returns GET
    """
    with does_not_raise():
        endpoint = EpOneManageVrfsGet()
        result = endpoint.verb
    assert result == "GET"


def test_onemanage_endpoints_02430():
    """
    ### Class
    - EpOneManageVrfsGet

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageVrfsGet()
        result = endpoint.class_name
    assert result == "EpOneManageVrfsGet"


# =============================================================================
# Test: EpOneManageVrfCreate
# =============================================================================


def test_onemanage_endpoints_02500():
    """
    ### Class
    - EpOneManageVrfCreate

    ### Summary
    - Verify path with fabric_name set
    """
    with does_not_raise():
        endpoint = EpOneManageVrfCreate()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/MyFabric/vrfs"


def test_onemanage_endpoints_02510():
    """
    ### Class
    - EpOneManageVrfCreate

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageVrfCreate()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_02520():
    """
    ### Class
    - EpOneManageVrfCreate

    ### Summary
    - Verify verb property returns POST
    """
    with does_not_raise():
        endpoint = EpOneManageVrfCreate()
        result = endpoint.verb
    assert result == "POST"


def test_onemanage_endpoints_02530():
    """
    ### Class
    - EpOneManageVrfCreate

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageVrfCreate()
        result = endpoint.class_name
    assert result == "EpOneManageVrfCreate"


# =============================================================================
# Test: EpOneManageNetworksGet
# =============================================================================


def test_onemanage_endpoints_02600():
    """
    ### Class
    - EpOneManageNetworksGet

    ### Summary
    - Verify path with fabric_name set
    """
    with does_not_raise():
        endpoint = EpOneManageNetworksGet()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_TOP_DOWN_FABRICS_PATH}/MyFabric/networks"


def test_onemanage_endpoints_02610():
    """
    ### Class
    - EpOneManageNetworksGet

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageNetworksGet()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_02620():
    """
    ### Class
    - EpOneManageNetworksGet

    ### Summary
    - Verify verb property returns GET
    """
    with does_not_raise():
        endpoint = EpOneManageNetworksGet()
        result = endpoint.verb
    assert result == "GET"


def test_onemanage_endpoints_02630():
    """
    ### Class
    - EpOneManageNetworksGet

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageNetworksGet()
        result = endpoint.class_name
    assert result == "EpOneManageNetworksGet"


# =============================================================================
# Test: EpOneManageLinkCreate
# =============================================================================


def test_onemanage_endpoints_02700():
    """
    ### Class
    - EpOneManageLinkCreate

    ### Summary
    - Verify path property returns correct endpoint
    """
    with does_not_raise():
        endpoint = EpOneManageLinkCreate()
        result = endpoint.path
    assert result == ONEMANAGE_LINKS_PATH


def test_onemanage_endpoints_02710():
    """
    ### Class
    - EpOneManageLinkCreate

    ### Summary
    - Verify verb property returns POST
    """
    with does_not_raise():
        endpoint = EpOneManageLinkCreate()
        result = endpoint.verb
    assert result == "POST"


def test_onemanage_endpoints_02720():
    """
    ### Class
    - EpOneManageLinkCreate

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageLinkCreate()
        result = endpoint.class_name
    assert result == "EpOneManageLinkCreate"


# =============================================================================
# Test: EpOneManageLinksDelete
# =============================================================================


def test_onemanage_endpoints_02800():
    """
    ### Class
    - EpOneManageLinksDelete

    ### Summary
    - Verify path property returns correct endpoint
    """
    with does_not_raise():
        endpoint = EpOneManageLinksDelete()
        result = endpoint.path
    assert result == ONEMANAGE_LINKS_PATH


def test_onemanage_endpoints_02810():
    """
    ### Class
    - EpOneManageLinksDelete

    ### Summary
    - Verify verb property returns PUT
    """
    with does_not_raise():
        endpoint = EpOneManageLinksDelete()
        result = endpoint.verb
    assert result == "PUT"


def test_onemanage_endpoints_02820():
    """
    ### Class
    - EpOneManageLinksDelete

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageLinksDelete()
        result = endpoint.class_name
    assert result == "EpOneManageLinksDelete"


# =============================================================================
# Test: EpOneManageLinkUpdate
# =============================================================================


def test_onemanage_endpoints_02900():
    """
    ### Class
    - EpOneManageLinkUpdate

    ### Summary
    - Verify path with link_uuid and query parameters
    """
    with does_not_raise():
        endpoint = EpOneManageLinkUpdate()
        endpoint.link_uuid = "63505f61-ce7b-40a6-a38c-ae9a355b2116"
        endpoint.query_params.source_cluster_name = "nd-cluster-2"
        endpoint.query_params.destination_cluster_name = "nd-cluster-1"
        result = endpoint.path
    expected = f"{ONEMANAGE_LINKS_PATH}/63505f61-ce7b-40a6-a38c-ae9a355b2116?sourceClusterName=nd-cluster-2&destinationClusterName=nd-cluster-1"
    assert result == expected


def test_onemanage_endpoints_02910():
    """
    ### Class
    - EpOneManageLinkUpdate

    ### Summary
    - Verify path raises ValueError when link_uuid not set
    """
    with pytest.raises(ValueError, match="link_uuid must be set"):
        endpoint = EpOneManageLinkUpdate()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_02920():
    """
    ### Class
    - EpOneManageLinkUpdate

    ### Summary
    - Verify verb property returns PUT
    """
    with does_not_raise():
        endpoint = EpOneManageLinkUpdate()
        result = endpoint.verb
    assert result == "PUT"


def test_onemanage_endpoints_02930():
    """
    ### Class
    - EpOneManageLinkUpdate

    ### Summary
    - Verify query_params initialized as LinkByUuidQueryParams
    """
    with does_not_raise():
        endpoint = EpOneManageLinkUpdate()
        result = isinstance(endpoint.query_params, LinkByUuidQueryParams)
    assert result is True


# =============================================================================
# Test: EpOneManageFabricGroupUpdate
# =============================================================================


def test_onemanage_endpoints_03000():
    """
    ### Class
    - EpOneManageFabricGroupUpdate

    ### Summary
    - Verify path with fabric_name set
    """
    with does_not_raise():
        endpoint = EpOneManageFabricGroupUpdate()
        endpoint.fabric_name = "MyFabric"
        result = endpoint.path
    assert result == f"{ONEMANAGE_FABRICS_PATH}/MyFabric/members"


def test_onemanage_endpoints_03010():
    """
    ### Class
    - EpOneManageFabricGroupUpdate

    ### Summary
    - Verify path raises ValueError when fabric_name not set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageFabricGroupUpdate()
        endpoint.path  # pylint: disable=pointless-statement


def test_onemanage_endpoints_03020():
    """
    ### Class
    - EpOneManageFabricGroupUpdate

    ### Summary
    - Verify verb property returns PUT
    """
    with does_not_raise():
        endpoint = EpOneManageFabricGroupUpdate()
        result = endpoint.verb
    assert result == "PUT"


def test_onemanage_endpoints_03030():
    """
    ### Class
    - EpOneManageFabricGroupUpdate

    ### Summary
    - Verify class_name attribute
    """
    with does_not_raise():
        endpoint = EpOneManageFabricGroupUpdate()
        result = endpoint.class_name
    assert result == "EpOneManageFabricGroupUpdate"
