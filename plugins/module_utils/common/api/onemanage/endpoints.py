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
Pydantic-based endpoint models with property-style interface for ALL parameters.

This module demonstrates a fully property-based approach where path parameters,
endpoint-specific query parameters, and Lucene-style filtering query parameters
are all set using the same consistent interface.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

from typing import Literal, Optional

from pydantic import BaseModel, Field

from ..base_paths import BasePath
from ..query_params import EndpointQueryParams

# ============================================================================
# Endpoint-Specific Query Parameter Classes
# ============================================================================


class NetworkNamesQueryParams(EndpointQueryParams):
    """
    Query parameters for network deletion endpoints.

    ### Parameters
    - network_names: Comma-separated list of network names to delete e.g. "Net1,Net2,Net3"
    """

    network_names: Optional[str] = Field(None, min_length=1, description="Comma-separated network names")

    def to_query_string(self) -> str:
        """Build query string with network-names parameter."""
        if self.network_names:
            return f"network-names={self.network_names}"
        return ""


class VrfNamesQueryParams(EndpointQueryParams):
    """
    Query parameters for VRF deletion endpoints.

    ### Parameters
    - vrf_names: Comma-separated list of VRF names to delete e.g. "VRF1,VRF2,VRF3"
    """

    vrf_names: Optional[str] = Field(None, min_length=1, description="Comma-separated VRF names")

    def to_query_string(self) -> str:
        """Build query string with vrf-names parameter."""
        if self.vrf_names:
            return f"vrf-names={self.vrf_names}"
        return ""


class EpOneManageFabricCreate(BaseModel):
    """
    ## Fabric Create Endpoint (OneManage)

    ### Description
    Endpoint to create a new multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/fabrics

    ### Verb

    - POST

    ### Usage
    ```python
    request = EpOneManageFabricCreate()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: str = "EpOneManageFabricCreate"  # For backward compatibility

    @property
    def path(self) -> str:
        """Build the endpoint path."""

        return BasePath.onemanage_fabrics()

    @property
    def verb(self) -> Literal["POST"]:
        """Return the HTTP verb for this endpoint."""
        return "POST"


class EpOneManageFabricDetails(BaseModel):
    """
    ## Fabric Details Endpoint (OneManage)

    ### Description
    Endpoint to query details for a specific multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/fabrics/MyFabric

    ### Verb

    - GET

    ### Usage
    ```python
    request = EpOneManageFabricDetails()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: str = "EpOneManageFabricDetails"  # For backward compatibility
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")

    @property
    def path(self) -> str:
        """Build the endpoint path."""
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        return BasePath.onemanage_fabrics(self.fabric_name)

    @property
    def verb(self) -> Literal["GET"]:
        """Return the HTTP verb for this endpoint."""
        return "GET"


class EpOneManageNetworksDelete(BaseModel):
    """
    ## Networks Delete Endpoint (OneManage)

    ### Description

    Endpoint to bulk-delete networks from a multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/top-down/fabrics/{fabric_name}/bulk-delete/networks

    ### Verb

    - DELETE

    ### Usage

    ```python
    request = EpOneManageNetworksDelete()
    request.fabric_name = "MyFabric"
    request.query_params.network_names = "MyNetwork1,MyNetwork2,MyNetwork3"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: str = "EpOneManageNetworksDelete"  # For backward compatibility
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")
    query_params: NetworkNamesQueryParams = Field(default_factory=NetworkNamesQueryParams)

    def __init__(self, **data):
        """Initialize with default query parameter objects."""
        super().__init__(**data)
        if not isinstance(self.query_params, NetworkNamesQueryParams):
            self.query_params = NetworkNamesQueryParams()

    @property
    def path(self) -> str:
        """
        Build the endpoint path with query parameters.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string with query parameters
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        base_path = BasePath.onemanage_top_down_fabrics(self.fabric_name, "bulk-delete", "networks")

        query_string = self.query_params.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> Literal["DELETE"]:
        """Return the HTTP verb for this endpoint."""
        return "DELETE"


class EpOneManageNetworkUpdate(BaseModel):
    """
    ## Network Update Endpoint (OneManage)

    ### Description

    Endpoint to update single Network in a multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/top-down/fabrics/{fabric_name}/networks/{network_name}

    ### Verb

    - PUT

    ### Usage

    ```python
    request = EpOneManageNetworkUpdate()
    request.fabric_name = "MyFabric"
    request.network_name = "MyNetwork1"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: str = "EpOneManageNetworkUpdate"  # For backward compatibility
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")
    network_name: Optional[str] = Field(None, min_length=1, description="Network name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises

        - ValueError: If fabric_name or vrf_name is not set

        ### Returns

        - Complete endpoint path string
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")
        if self.network_name is None:
            raise ValueError("network_name must be set before accessing path")

        return BasePath.onemanage_top_down_fabrics(self.fabric_name, "networks", self.network_name)

    @property
    def verb(self) -> Literal["PUT"]:
        """Return the HTTP verb for this endpoint."""
        return "PUT"


class EpOneManageVrfsDelete(BaseModel):
    """
    ## VRFs Delete Endpoint (OneManage)

    ### Description

    Endpoint to bulk-delete VRFs from a multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/top-down/fabrics/{fabric_name}/bulk-delete/vrfs

    ### Verb

    - DELETE

    ### Usage

    ```python
    request = EpOneManageVrfsDelete()
    request.fabric_name = "MyFabric"
    request.query_params.vrf_names = "MyVRF1,MyVRF2,MyVRF3"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: str = "EpOneManageVrfsDelete"  # For backward compatibility
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")
    query_params: VrfNamesQueryParams = Field(default_factory=VrfNamesQueryParams)

    def __init__(self, **data):
        """Initialize with default query parameter objects."""
        super().__init__(**data)
        if not isinstance(self.query_params, VrfNamesQueryParams):
            self.query_params = VrfNamesQueryParams()

    @property
    def path(self) -> str:
        """
        Build the endpoint path with query parameters.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string with query parameters
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        base_path = BasePath.onemanage_top_down_fabrics(self.fabric_name, "bulk-delete", "vrfs")

        query_string = self.query_params.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> Literal["DELETE"]:
        """Return the HTTP verb for this endpoint."""
        return "DELETE"


class EpOneManageVrfUpdate(BaseModel):
    """
    ## VRF Update Endpoint (OneManage)

    ### Description

    Endpoint to update single VRF in a multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/top-down/fabrics/{fabric_name}/vrfs/{vrf_name}

    ### Verb

    - PUT

    ### Usage

    ```python
    request = EpOneManageVrfUpdate()
    request.fabric_name = "MyFabric"
    request.vrf_name = "MyVRF1"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: str = "EpOneManageVrfUpdate"  # For backward compatibility
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")
    vrf_name: Optional[str] = Field(None, min_length=1, description="VRF name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises
        - ValueError: If fabric_name or vrf_name is not set

        ### Returns
        - Complete endpoint path string
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")
        if self.vrf_name is None:
            raise ValueError("vrf_name must be set before accessing path")

        return BasePath.onemanage_top_down_fabrics(self.fabric_name, "vrfs", self.vrf_name)

    @property
    def verb(self) -> Literal["PUT"]:
        """Return the HTTP verb for this endpoint."""
        return "PUT"
