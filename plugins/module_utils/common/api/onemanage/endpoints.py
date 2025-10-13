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

import traceback
from typing import Literal, Optional, Union

try:
    from pydantic import BaseModel, Field
except ImportError:
    HAS_PYDANTIC = False
    PYDANTIC_IMPORT_ERROR: Union[str, None] = traceback.format_exc()
else:
    HAS_PYDANTIC = True
    PYDANTIC_IMPORT_ERROR = None

from ..base_paths import BasePath
from ..query_params import EndpointQueryParams

# ============================================================================
# Endpoint-Specific Query Parameter Classes
# ============================================================================


class FabricConfigDeployQueryParams(EndpointQueryParams):
    """
    Query parameters for fabric config deploy endpoints.

    ### Parameters
    - force_show_run: If true, fetch latest running config from device; if false, use cached version (default: "false")
    - incl_all_msd_switches: If true and MSD fabric, deploy all child fabric changes; if false, skip child fabrics (default: "false")
    """

    force_show_run: Literal["false", "true"] = Field("false", description="Fetch latest running config from device")
    incl_all_msd_switches: Literal["false", "true"] = Field("false", description="Deploy all MSD child fabric changes")

    def to_query_string(self) -> str:
        """Build query string with forceShowRun and inclAllMSDSwitches parameters."""
        params = []
        if self.force_show_run:
            params.append(f"forceShowRun={self.force_show_run}")
        if self.incl_all_msd_switches:
            params.append(f"inclAllMSDSwitches={self.incl_all_msd_switches}")
        return "&".join(params)


class FabricConfigPreviewQueryParams(EndpointQueryParams):
    """
    Query parameters for fabric config preview endpoints.

    ### Parameters
    - force_show_run: Force show running config (default: "false")
    - show_brief: Show brief output (default: "false")
    """

    force_show_run: Literal["false", "true"] = Field("false", description="Force show running config")
    show_brief: Literal["false", "true"] = Field("false", description="Show brief output")

    def to_query_string(self) -> str:
        """Build query string with forceShowRun and showBrief parameters."""
        params = []
        if self.force_show_run:
            params.append(f"forceShowRun={self.force_show_run}")
        if self.show_brief:
            params.append(f"showBrief={self.show_brief}")
        return "&".join(params)


class LinkByUuidQueryParams(EndpointQueryParams):
    """
    Query parameters for link by UUID endpoints.

    ### Parameters
    - source_cluster_name: Source cluster name (e.g., "nd-cluster-1")
    - destination_cluster_name: Destination cluster name (e.g., "nd-cluster-2")
    """

    source_cluster_name: Optional[str] = Field(None, min_length=1, description="Source cluster name")
    destination_cluster_name: Optional[str] = Field(None, min_length=1, description="Destination cluster name")

    def to_query_string(self) -> str:
        """Build query string with sourceClusterName and destinationClusterName parameters."""
        params = []
        if self.source_cluster_name:
            params.append(f"sourceClusterName={self.source_cluster_name}")
        if self.destination_cluster_name:
            params.append(f"destinationClusterName={self.destination_cluster_name}")
        return "&".join(params)


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


class EpOneManageFabricConfigDeploy(BaseModel):
    """
    ## Fabric Config-Deploy Endpoint (OneManage)

    ### Description
    Endpoint to deploy the configuration for a specific multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/fabrics/{fabricName}/config-deploy

    ### Verb

    - POST

    ### Usage
    ```python
    request = EpOneManageFabricConfigDeploy()
    request.fabric_name = "MyFabric"
    request.query_params.force_show_run = "true"
    request.query_params.incl_all_msd_switches = "false"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: Optional[str] = Field(default="EpOneManageFabricConfigDeploy", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")
    query_params: FabricConfigDeployQueryParams = Field(default_factory=FabricConfigDeployQueryParams)

    def __init__(self, **data):
        """Initialize with default query parameter objects."""
        super().__init__(**data)
        if not isinstance(self.query_params, FabricConfigDeployQueryParams):
            self.query_params = FabricConfigDeployQueryParams()

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

        base_path = BasePath.onemanage_fabrics(self.fabric_name, "config-deploy")

        query_string = self.query_params.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> Literal["POST"]:
        """Return the HTTP verb for this endpoint."""
        return "POST"


class EpOneManageFabricConfigDeploySwitch(BaseModel):
    """
    ## Fabric Config-Deploy Switch Endpoint (OneManage)

    ### Description
    Endpoint to deploy the configuration for a specific switch in a multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/fabrics/{fabricName}/config-deploy/{switchSN}

    ### Verb

    - POST

    ### Usage
    ```python
    request = EpOneManageFabricConfigDeploySwitch()
    request.fabric_name = "MyFabric"
    request.switch_sn = "92RZ2OMQCNC"
    request.query_params.force_show_run = "true"
    request.query_params.incl_all_msd_switches = "false"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: Optional[str] = Field(default="EpOneManageFabricConfigDeploySwitch", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")
    switch_sn: Optional[str] = Field(None, min_length=1, description="Switch serial number")
    query_params: FabricConfigDeployQueryParams = Field(default_factory=FabricConfigDeployQueryParams)

    def __init__(self, **data):
        """Initialize with default query parameter objects."""
        super().__init__(**data)
        if not isinstance(self.query_params, FabricConfigDeployQueryParams):
            self.query_params = FabricConfigDeployQueryParams()

    @property
    def path(self) -> str:
        """
        Build the endpoint path with query parameters.

        ### Raises
        - ValueError: If fabric_name or switch_sn is not set

        ### Returns
        - Complete endpoint path string with query parameters
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")
        if self.switch_sn is None:
            raise ValueError("switch_sn must be set before accessing path")

        base_path = BasePath.onemanage_fabrics(self.fabric_name, "config-deploy", self.switch_sn)

        query_string = self.query_params.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> Literal["POST"]:
        """Return the HTTP verb for this endpoint."""
        return "POST"


class EpOneManageFabricConfigPreview(BaseModel):
    """
    ## Fabric Config-Preview Endpoint (OneManage)

    ### Description
    Endpoint to preview the configuration for a specific multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/fabrics/{fabricName}/config-preview

    ### Verb

    - GET

    ### Usage
    ```python
    request = EpOneManageFabricConfigPreview()
    request.fabric_name = "MyFabric"
    request.query_params.force_show_run = "true"
    request.query_params.show_brief = "false"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: Optional[str] = Field(default="EpOneManageFabricConfigPreview", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")
    query_params: FabricConfigPreviewQueryParams = Field(default_factory=FabricConfigPreviewQueryParams)

    def __init__(self, **data):
        """Initialize with default query parameter objects."""
        super().__init__(**data)
        if not isinstance(self.query_params, FabricConfigPreviewQueryParams):
            self.query_params = FabricConfigPreviewQueryParams()

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

        base_path = BasePath.onemanage_fabrics(self.fabric_name, "config-preview")

        query_string = self.query_params.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> Literal["GET"]:
        """Return the HTTP verb for this endpoint."""
        return "GET"


class EpOneManageFabricConfigPreviewSwitch(BaseModel):
    """
    ## Fabric Config-Preview Switch Endpoint (OneManage)

    ### Description
    Endpoint to preview the configuration for a specific switch in a multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/fabrics/{fabricName}/config-preview/{switchSN}

    ### Verb

    - GET

    ### Usage
    ```python
    request = EpOneManageFabricConfigPreviewSwitch()
    request.fabric_name = "MyFabric"
    request.switch_sn = "92RZ2OMQCNC"
    request.query_params.force_show_run = "true"
    request.query_params.show_brief = "false"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: Optional[str] = Field(default="EpOneManageFabricConfigPreviewSwitch", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")
    switch_sn: Optional[str] = Field(None, min_length=1, description="Switch serial number")
    query_params: FabricConfigPreviewQueryParams = Field(default_factory=FabricConfigPreviewQueryParams)

    def __init__(self, **data):
        """Initialize with default query parameter objects."""
        super().__init__(**data)
        if not isinstance(self.query_params, FabricConfigPreviewQueryParams):
            self.query_params = FabricConfigPreviewQueryParams()

    @property
    def path(self) -> str:
        """
        Build the endpoint path with query parameters.

        ### Raises
        - ValueError: If fabric_name or switch_sn is not set

        ### Returns
        - Complete endpoint path string with query parameters
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")
        if self.switch_sn is None:
            raise ValueError("switch_sn must be set before accessing path")

        base_path = BasePath.onemanage_fabrics(self.fabric_name, "config-preview", self.switch_sn)

        query_string = self.query_params.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> Literal["GET"]:
        """Return the HTTP verb for this endpoint."""
        return "GET"


class EpOneManageFabricConfigSave(BaseModel):
    """
    ## Fabric Config-Save Endpoint (OneManage)

    ### Description
    Endpoint to save the configuration for a specific multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/fabrics/{fabricName}/config-save

    ### Verb

    - POST

    ### Usage
    ```python
    request = EpOneManageFabricConfigSave()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: Optional[str] = Field(default="EpOneManageFabricConfigSave", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        return BasePath.onemanage_fabrics(self.fabric_name, "config-save")

    @property
    def verb(self) -> Literal["POST"]:
        """Return the HTTP verb for this endpoint."""
        return "POST"


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

    class_name: Optional[str] = Field(default="EpOneManageFabricCreate", description="Class name for backward compatibility")

    @property
    def path(self) -> str:
        """Build the endpoint path."""

        return BasePath.onemanage_fabrics()

    @property
    def verb(self) -> Literal["POST"]:
        """Return the HTTP verb for this endpoint."""
        return "POST"


class EpOneManageFabricDelete(BaseModel):
    """
    ## Fabric Delete Endpoint (OneManage)

    ### Description
    Endpoint to delete a specific multi-cluster fabric.

    ### Path

    - /onemanage/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabricName}

    ### Verb

    - DELETE

    ### Usage
    ```python
    request = EpOneManageFabricDelete()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```

    ### Note
    The delete endpoint uses the regular LAN fabric control API with /onemanage prefix,
    not the onemanage-specific API endpoint. This is required for multi-cluster fabrics.
    """

    class_name: Optional[str] = Field(default="EpOneManageFabricDelete", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string with /onemanage prefix
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        # Use the regular LAN fabric control API with /onemanage prefix
        # This is the correct endpoint for deleting multi-cluster fabrics
        return f"/onemanage{BasePath.control_fabrics(self.fabric_name)}"

    @property
    def verb(self) -> Literal["DELETE"]:
        """Return the HTTP verb for this endpoint."""
        return "DELETE"


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

    class_name: Optional[str] = Field(default="EpOneManageFabricDetails", description="Class name for backward compatibility")
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


class EpOneManageFabricGroupMembersGet(BaseModel):
    """
    ## Fabric Group Members Get Endpoint (OneManage)

    ### Description
    Endpoint to retrieve members of a specific multi-cluster fabric group.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/fabrics/{fabricName}/members

    ### Verb

    - GET

    ### Usage
    ```python
    request = EpOneManageFabricGroupMembersGet()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: Optional[str] = Field(default="EpOneManageFabricGroupMembersGet", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric group name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        return BasePath.onemanage_fabrics(self.fabric_name, "members")

    @property
    def verb(self) -> Literal["GET"]:
        """Return the HTTP verb for this endpoint."""
        return "GET"


class EpOneManageFabricGroupUpdate(BaseModel):
    """
    ## Fabric Group Update Endpoint (OneManage)

    ### Description
    Endpoint to add or remove a fabric from a multi-cluster fabric group.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/fabrics/{fabricName}/members

    ### Verb

    - PUT

    ### Usage
    ```python
    request = EpOneManageFabricGroupUpdate()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```

    ### Request Body

    The request body should contain fabric group update parameters:
    - clusterName: str - Name of the cluster
    - fabricName: str - Name of the fabric
    - operation: str - Operation type ("add" or "remove")
      - "add": Add fabricName to clusterName
      - "remove": Remove fabricName from clusterName
    """

    class_name: Optional[str] = Field(default="EpOneManageFabricGroupUpdate", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric group name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        return BasePath.onemanage_fabrics(self.fabric_name, "members")

    @property
    def verb(self) -> Literal["PUT"]:
        """Return the HTTP verb for this endpoint."""
        return "PUT"


class EpOneManageFabricUpdate(BaseModel):
    """
    ## Fabric Update Endpoint (OneManage)

    ### Description
    Endpoint to update a specific multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/fabrics/{fabricName}

    ### Verb

    - PUT

    ### Usage
    ```python
    request = EpOneManageFabricUpdate()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```

    ### Request Body

    The request body should contain fabric update parameters:
    - fabricName: str - Name of the Fabric
    - fabricType: str - Type of the fabric
    - fabricTechnology: str - Fabric technology
    - nvPairs: dict - Key value pairs describing the fabric configuration

    nvPairs dictionary keys (all string values unless noted):
    - ANYCAST_GW_MAC
    - BGP_RP_ASN
    - BGW_ROUTING_TAG
    - BGW_ROUTING_TAG_PREV
    - BORDER_GWY_CONNECTIONS
    - DCI_SUBNET_RANGE
    - DCI_SUBNET_TARGET_MASK
    - DELAY_RESTORE
    - ENABLE_BGP_BFD
    - ENABLE_BGP_LOG_NEIGHBOR_CHANGE (boolean)
    - ENABLE_BGP_SEND_COMM (boolean)
    - ENABLE_PVLAN
    - ENABLE_PVLAN_PREV
    - ENABLE_RS_REDIST_DIRECT (boolean)
    - ENABLE_TRM_TRMv6
    - ENABLE_TRM_TRMv6_PREV
    - EXT_FABRIC_TYPE
    - FABRIC_NAME
    - FABRIC_TYPE
    - FF
    - L2_SEGMENT_ID_RANGE
    - L3_PARTITION_ID_RANGE
    - LOOPBACK100_IPV6_RANGE
    - LOOPBACK100_IP_RANGE
    - MSO_CONTROLER_ID
    - MSO_SITE_GROUP_NAME
    - MS_IFC_BGP_AUTH_KEY_TYPE
    - MS_IFC_BGP_AUTH_KEY_TYPE_PREV
    - MS_IFC_BGP_PASSWORD
    - MS_IFC_BGP_PASSWORD_ENABLE
    - MS_IFC_BGP_PASSWORD_ENABLE_PREV
    - MS_IFC_BGP_PASSWORD_PREV
    - MS_LOOPBACK_ID
    - MS_UNDERLAY_AUTOCONFIG (boolean)
    - PARENT_ONEMANAGE_FABRIC
    - PREMSO_PARENT_FABRIC
    - RP_SERVER_IP
    - RS_ROUTING_TAG
    - TOR_AUTO_DEPLOY
    - V6_DCI_SUBNET_RANGE
    - V6_DCI_SUBNET_TARGET_MASK
    - VXLAN_UNDERLAY_IS_V6
    - default_network
    - default_pvlan_sec_network
    - default_vrf
    - network_extension_template
    - vrf_extension_template
    """

    class_name: Optional[str] = Field(default="EpOneManageFabricUpdate", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        return BasePath.onemanage_fabrics(self.fabric_name)

    @property
    def verb(self) -> Literal["PUT"]:
        """Return the HTTP verb for this endpoint."""
        return "PUT"


class EpOneManageFabricsGet(BaseModel):
    """
    ## Fabrics Get Endpoint (OneManage)

    ### Description
    Endpoint to retrieve all multi-cluster fabrics.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/fabrics

    ### Verb

    - GET

    ### Usage
    ```python
    request = EpOneManageFabricsGet()

    path = request.path
    verb = request.verb
    ```
    """

    class_name: Optional[str] = Field(default="EpOneManageFabricsGet", description="Class name for backward compatibility")

    @property
    def path(self) -> str:
        """Build the endpoint path."""
        return BasePath.onemanage_fabrics()

    @property
    def verb(self) -> Literal["GET"]:
        """Return the HTTP verb for this endpoint."""
        return "GET"


class EpOneManageLinkCreate(BaseModel):
    """
    ## Link Create Endpoint (OneManage)

    ### Description
    Endpoint to create a link between fabrics in multi-cluster setup.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/links

    ### Verb

    - POST

    ### Usage
    ```python
    request = EpOneManageLinkCreate()

    path = request.path
    verb = request.verb
    ```

    ### Request Body

    The request body should contain link creation parameters:
    - sourceClusterName: str - Source cluster name
    - destinationClusterName: str - Destination cluster name
    - sourceFabric: str - Source fabric name
    - destinationFabric: str - Destination fabric name
    - sourceDevice: str - Source switch serial number
    - destinationDevice: str - Destination switch serial number
    - sourceSwitchName: str - Source switch name
    - destinationSwitchName: str - Destination switch name
    - sourceInterface: str - Source switch interface
    - destinationInterface: str - Destination switch interface
    - templateName: str - Link template name
    - nvPairs: dict - Key/value pairs of configuration items

    nvPairs dictionary keys (all string values unless noted):
    - IP_MASK
    - NEIGHBOR_IP
    - IPV6_MASK
    - IPV6_NEIGHBOR
    - MAX_PATHS
    - ROUTING_TAG
    - MTU
    - SPEED
    - DEPLOY_DCI_TRACKING (boolean)
    - BGP_PASSWORD_ENABLE
    - BGP_PASSWORD
    - ENABLE_BGP_LOG_NEIGHBOR_CHANGE
    - ENABLE_BGP_SEND_COMM
    - BGP_PASSWORD_INHERIT_FROM_MSD
    - BGP_AUTH_KEY_TYPE
    - asn
    - NEIGHBOR_ASNL
    - ENABLE_BGP_BFD
    """

    class_name: Optional[str] = Field(default="EpOneManageLinkCreate", description="Class name for backward compatibility")

    @property
    def path(self) -> str:
        """Build the endpoint path."""
        return BasePath.onemanage_links()

    @property
    def verb(self) -> Literal["POST"]:
        """Return the HTTP verb for this endpoint."""
        return "POST"


class EpOneManageLinkGetByUuid(BaseModel):
    """
    ## Link Get By UUID Endpoint (OneManage)

    ### Description
    Endpoint to retrieve a specific link by its UUID.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/links/{linkUUID}

    ### Verb

    - GET

    ### Usage
    ```python
    request = EpOneManageLinkGetByUuid()
    request.link_uuid = "63505f61-ce7b-40a6-a38c-ae9a355b2116"
    request.query_params.source_cluster_name = "nd-cluster-1"
    request.query_params.destination_cluster_name = "nd-cluster-2"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: Optional[str] = Field(default="EpOneManageLinkGetByUuid", description="Class name for backward compatibility")
    link_uuid: Optional[str] = Field(None, min_length=1, description="Link UUID")
    query_params: LinkByUuidQueryParams = Field(default_factory=LinkByUuidQueryParams)

    def __init__(self, **data):
        """Initialize with default query parameter objects."""
        super().__init__(**data)
        if not isinstance(self.query_params, LinkByUuidQueryParams):
            self.query_params = LinkByUuidQueryParams()

    @property
    def path(self) -> str:
        """
        Build the endpoint path with query parameters.

        ### Raises
        - ValueError: If link_uuid is not set

        ### Returns
        - Complete endpoint path string with query parameters
        """
        if self.link_uuid is None:
            raise ValueError("link_uuid must be set before accessing path")

        base_path = BasePath.onemanage_links(self.link_uuid)

        query_string = self.query_params.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> Literal["GET"]:
        """Return the HTTP verb for this endpoint."""
        return "GET"


class EpOneManageLinkUpdate(BaseModel):
    """
    ## Link Update Endpoint (OneManage)

    ### Description
    Endpoint to update a specific link by its UUID.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/links/{linkUUID}

    ### Verb

    - PUT

    ### Usage
    ```python
    request = EpOneManageLinkUpdate()
    request.link_uuid = "63505f61-ce7b-40a6-a38c-ae9a355b2116"
    request.query_params.source_cluster_name = "nd-cluster-2"
    request.query_params.destination_cluster_name = "nd-cluster-1"

    path = request.path
    verb = request.verb
    ```

    ### Request Body

    The request body should contain link update parameters:
    - sourceClusterName: str - Source cluster name
    - destinationClusterName: str - Destination cluster name
    - sourceFabric: str - Source fabric name
    - destinationFabric: str - Destination fabric name
    - sourceDevice: str - Source switch serial number
    - destinationDevice: str - Destination switch serial number
    - sourceSwitchName: str - Source switch name
    - destinationSwitchName: str - Destination switch name
    - sourceInterface: str - Source switch interface
    - destinationInterface: str - Destination switch interface
    - templateName: str - Link template name
    - nvPairs: dict - Key/value pairs of configuration items

    nvPairs dictionary keys (all string values unless noted):
    - IP_MASK
    - NEIGHBOR_IP
    - IPV6_MASK
    - IPV6_NEIGHBOR
    - MAX_PATHS
    - ROUTING_TAG
    - MTU
    - SPEED
    - DEPLOY_DCI_TRACKING (boolean)
    - BGP_PASSWORD_ENABLE
    - BGP_PASSWORD
    - ENABLE_BGP_LOG_NEIGHBOR_CHANGE
    - ENABLE_BGP_SEND_COMM
    - BGP_PASSWORD_INHERIT_FROM_MSD
    - BGP_AUTH_KEY_TYPE
    - asn
    - NEIGHBOR_ASNL
    - ENABLE_BGP_BFD
    """

    class_name: Optional[str] = Field(default="EpOneManageLinkUpdate", description="Class name for backward compatibility")
    link_uuid: Optional[str] = Field(None, min_length=1, description="Link UUID")
    query_params: LinkByUuidQueryParams = Field(default_factory=LinkByUuidQueryParams)

    def __init__(self, **data):
        """Initialize with default query parameter objects."""
        super().__init__(**data)
        if not isinstance(self.query_params, LinkByUuidQueryParams):
            self.query_params = LinkByUuidQueryParams()

    @property
    def path(self) -> str:
        """
        Build the endpoint path with query parameters.

        ### Raises
        - ValueError: If link_uuid is not set

        ### Returns
        - Complete endpoint path string with query parameters
        """
        if self.link_uuid is None:
            raise ValueError("link_uuid must be set before accessing path")

        base_path = BasePath.onemanage_links(self.link_uuid)

        query_string = self.query_params.to_query_string()
        if query_string:
            return f"{base_path}?{query_string}"
        return base_path

    @property
    def verb(self) -> Literal["PUT"]:
        """Return the HTTP verb for this endpoint."""
        return "PUT"


class EpOneManageLinksDelete(BaseModel):
    """
    ## Links Delete Endpoint (OneManage)

    ### Description
    Endpoint to delete links in multi-cluster setup.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/links

    ### Verb

    - PUT

    ### Usage
    ```python
    request = EpOneManageLinksDelete()

    path = request.path
    verb = request.verb
    ```

    ### Request Body

    The request body should contain link deletion parameters:
    - linkUUID: str - Link UUID (e.g., "63505f61-ce7b-40a6-a38c-ae9a355b2116")
    - destinationClusterName: str - Destination cluster name (e.g., "nd-cluster-1")
    - sourceClusterName: str - Source cluster name (e.g., "nd-cluster-2")
    """

    class_name: Optional[str] = Field(default="EpOneManageLinksDelete", description="Class name for backward compatibility")

    @property
    def path(self) -> str:
        """Build the endpoint path."""
        return BasePath.onemanage_links()

    @property
    def verb(self) -> Literal["PUT"]:
        """Return the HTTP verb for this endpoint."""
        return "PUT"


class EpOneManageLinksGetByFabric(BaseModel):
    """
    ## Links Get By Fabric Endpoint (OneManage)

    ### Description
    Endpoint to retrieve links for a specific multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/links/fabrics/{fabricName}

    ### Verb

    - GET

    ### Usage
    ```python
    request = EpOneManageLinksGetByFabric()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: Optional[str] = Field(default="EpOneManageLinksGetByFabric", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        return BasePath.onemanage_links_fabrics(self.fabric_name)

    @property
    def verb(self) -> Literal["GET"]:
        """Return the HTTP verb for this endpoint."""
        return "GET"


class EpOneManageNetworkCreate(BaseModel):
    """
    ## Network Create Endpoint (OneManage)

    ### Description

    Endpoint to create a network in a multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/top-down/fabrics/{fabricName}/networks

    ### Verb

    - POST

    ### Usage

    ```python
    request = EpOneManageNetworkCreate()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```

    ### Request Body

    The request body should contain network creation parameters:
    - id: int - Link ID
    - vrfId: int - VRF ID
    - networkId: int - Network ID
    - vrf: str - Name of the VRF
    - fabric: str - Name of the Fabric
    - networkTemplate: str - Network template name
    - networkTemplateConfig: str - Network extension template config
    """

    class_name: Optional[str] = Field(default="EpOneManageNetworkCreate", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        return BasePath.onemanage_top_down_fabrics(self.fabric_name, "networks")

    @property
    def verb(self) -> Literal["POST"]:
        """Return the HTTP verb for this endpoint."""
        return "POST"


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

    class_name: Optional[str] = Field(default="EpOneManageNetworkUpdate", description="Class name for backward compatibility")
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

    class_name: Optional[str] = Field(default="EpOneManageNetworksDelete", description="Class name for backward compatibility")
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


class EpOneManageNetworksGet(BaseModel):
    """
    ## Networks Get Endpoint (OneManage)

    ### Description

    Endpoint to retrieve all networks from a multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/top-down/fabrics/{fabricName}/networks

    ### Verb

    - GET

    ### Usage

    ```python
    request = EpOneManageNetworksGet()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: Optional[str] = Field(default="EpOneManageNetworksGet", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        return BasePath.onemanage_top_down_fabrics(self.fabric_name, "networks")

    @property
    def verb(self) -> Literal["GET"]:
        """Return the HTTP verb for this endpoint."""
        return "GET"


class EpOneManageVrfCreate(BaseModel):
    """
    ## VRF Create Endpoint (OneManage)

    ### Description

    Endpoint to create a VRF in a multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/top-down/fabrics/{fabricName}/vrfs

    ### Verb

    - POST

    ### Usage

    ```python
    request = EpOneManageVrfCreate()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```

    ### Request Body

    The request body should contain VRF creation parameters:
    - id: int - Link ID
    - vrfId: int - VRF ID
    - vrfName: str - Name of the VRF
    - fabric: str - Name of the fabric
    - vrfTemplate: str - VRF template name
    - vrfExtensionTemplate: str - VRF extension template name
    - vrfTemplateConfig: str - JSON string representing the VRF configuration
    """

    class_name: Optional[str] = Field(default="EpOneManageVrfCreate", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        return BasePath.onemanage_top_down_fabrics(self.fabric_name, "vrfs")

    @property
    def verb(self) -> Literal["POST"]:
        """Return the HTTP verb for this endpoint."""
        return "POST"


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

    class_name: Optional[str] = Field(default="EpOneManageVrfUpdate", description="Class name for backward compatibility")
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

    class_name: Optional[str] = Field(default="EpOneManageVrfsDelete", description="Class name for backward compatibility")
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


class EpOneManageVrfsGet(BaseModel):
    """
    ## VRFs Get Endpoint (OneManage)

    ### Description

    Endpoint to retrieve all VRFs from a multi-cluster fabric.

    ### Path

    - /appcenter/cisco/ndfc/api/v1/onemanage/top-down/fabrics/{fabricName}/vrfs

    ### Verb

    - GET

    ### Usage

    ```python
    request = EpOneManageVrfsGet()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: Optional[str] = Field(default="EpOneManageVrfsGet", description="Class name for backward compatibility")
    fabric_name: Optional[str] = Field(None, min_length=1, description="Fabric name")

    @property
    def path(self) -> str:
        """
        Build the endpoint path.

        ### Raises
        - ValueError: If fabric_name is not set

        ### Returns
        - Complete endpoint path string
        """
        if self.fabric_name is None:
            raise ValueError("fabric_name must be set before accessing path")

        return BasePath.onemanage_top_down_fabrics(self.fabric_name, "vrfs")

    @property
    def verb(self) -> Literal["GET"]:
        """Return the HTTP verb for this endpoint."""
        return "GET"
