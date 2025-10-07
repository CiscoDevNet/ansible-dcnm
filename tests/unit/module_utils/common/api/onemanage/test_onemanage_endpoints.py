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
    EpOneManageFabricCreate,
    EpOneManageFabricDetails,
    EpOneManageNetworksDelete,
    EpOneManageNetworkUpdate,
    EpOneManageVrfsDelete,
    EpOneManageVrfUpdate,
    NetworkNamesQueryParams,
    VrfNamesQueryParams,
)
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import does_not_raise
from pydantic import ValidationError

# =============================================================================
# Constants
# =============================================================================

ONEMANAGE_FABRICS_PATH = "/appcenter/cisco/ndfc/api/v1/onemanage/fabrics"
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
        _ = endpoint.path


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
        _ = endpoint.path


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
        _ = endpoint.path


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
        _ = endpoint.path


def test_onemanage_endpoints_00630():
    """
    ### Class
    - EpOneManageNetworkUpdate

    ### Summary
    - Verify path raises ValueError when neither parameter set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageNetworkUpdate()
        _ = endpoint.path


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
        _ = endpoint.path


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
        _ = endpoint.path


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
        _ = endpoint.path


def test_onemanage_endpoints_00830():
    """
    ### Class
    - EpOneManageVrfUpdate

    ### Summary
    - Verify path raises ValueError when neither parameter set
    """
    with pytest.raises(ValueError, match="fabric_name must be set"):
        endpoint = EpOneManageVrfUpdate()
        _ = endpoint.path


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
