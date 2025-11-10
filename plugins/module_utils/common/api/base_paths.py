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
Centralized base paths for ND API endpoints.

This module provides a single location to manage all API base paths,
allowing easy modification when API paths change. All endpoint classes
should use these path builders for consistency.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

from typing import Final


class BasePath:
    """
    ## Centralized API Base Paths

    ### Description
    Provides centralized base path definitions for all ND API endpoints.
    This allows API path changes to be managed in a single location.

    ### Usage

    ```python
    # Get a complete base path
    path = BasePath.control_fabrics("MyFabric", "config-deploy")
    # Returns: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/MyFabric/config-deploy

    # Build custom paths
    path = BasePath.v1("custom", "endpoint")
    # Returns: /appcenter/cisco/ndfc/api/v1/custom/endpoint
    ```

    ### Design Notes
    - All base paths are defined as class constants for easy modification
    - Helper methods compose paths from base constants
    - Use these methods in Pydantic endpoint models to ensure consistency
    - If NDFC changes base API paths, only this class needs updating
    """

    # Root API paths
    NDFC_API: Final = "/appcenter/cisco/ndfc/api"
    ONEMANAGE: Final = "/onemanage"
    LOGIN: Final = "/login"

    @classmethod
    def api(cls, *segments: str) -> str:
        """
        Build path from NDFC API root.

        ### Parameters
        - segments: Path segments to append

        ### Returns
        - Complete path string

        ### Example
        ```python
        path = BasePath.api("custom", "endpoint")
        # Returns: /appcenter/cisco/ndfc/api/custom/endpoint
        ```
        """
        if not segments:
            return cls.NDFC_API
        return f"{cls.NDFC_API}/{'/'.join(segments)}"

    @classmethod
    def v1(cls, *segments: str) -> str:
        """
        Build v1 API path.

        ### Parameters
        - segments: Path segments to append after v1

        ### Returns
        - Complete v1 API path

        ### Example
        ```python
        path = BasePath.v1("lan-fabric", "rest")
        # Returns: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest
        ```
        """
        return cls.api("v1", *segments)

    @classmethod
    def lan_fabric(cls, *segments: str) -> str:
        """
        Build lan-fabric API path.

        ### Parameters
        - segments: Path segments to append after lan-fabric

        ### Returns
        - Complete lan-fabric path

        ### Example
        ```python
        path = BasePath.lan_fabric("rest", "control")
        # Returns: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control
        ```
        """
        return cls.v1("lan-fabric", *segments)

    @classmethod
    def lan_fabric_rest(cls, *segments: str) -> str:
        """
        Build lan-fabric/rest API path.

        ### Parameters
        - segments: Path segments to append after rest

        ### Returns
        - Complete lan-fabric/rest path
        """
        return cls.lan_fabric("rest", *segments)

    @classmethod
    def control(cls, *segments: str) -> str:
        """
        Build lan-fabric/rest/control API path.

        ### Parameters
        - segments: Path segments to append after control

        ### Returns
        - Complete control path
        """
        return cls.lan_fabric_rest("control", *segments)

    @classmethod
    def control_fabrics(cls, *segments: str) -> str:
        """
        Build control/fabrics API path.

        ### Parameters
        - segments: Path segments to append after fabrics (e.g., fabric_name, operations)

        ### Returns
        - Complete control/fabrics path

        ### Example
        ```python
        path = BasePath.control_fabrics("MyFabric", "config-deploy")
        # Returns: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/MyFabric/config-deploy
        ```
        """
        return cls.control("fabrics", *segments)

    @classmethod
    def control_switches(cls, *segments: str) -> str:
        """
        Build control/switches API path.

        ### Parameters
        - segments: Path segments to append after switches

        ### Returns
        - Complete control/switches path
        """
        return cls.control("switches", *segments)

    @classmethod
    def inventory(cls, *segments: str) -> str:
        """
        Build lan-fabric/rest/inventory API path.

        ### Parameters
        - segments: Path segments to append after inventory

        ### Returns
        - Complete inventory path
        """
        return cls.lan_fabric_rest("inventory", *segments)

    @classmethod
    def configtemplate(cls, *segments: str) -> str:
        """
        Build configtemplate API path.

        ### Parameters
        - segments: Path segments to append after configtemplate

        ### Returns
        - Complete configtemplate path

        ### Example
        ```python
        path = BasePath.configtemplate("rest", "config", "templates")
        # Returns: /appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates
        ```
        """
        return cls.v1("configtemplate", *segments)

    @classmethod
    def onemanage(cls, *segments: str) -> str:
        """
        Build onemanage API path.

        ### Parameters
        - segments: Path segments to append after onemanage

        ### Returns
        - Complete onemanage path

        ### Example
        ```python
        path = BasePath.onemanage("fabrics", "MyFabric")
        # Returns: /appcenter/cisco/ndfc/api/v1/onemanage/fabrics/MyFabric
        ```
        """
        return cls.v1("onemanage", *segments)

    @classmethod
    def onemanage_fabrics(cls, *segments: str) -> str:
        """
        Build onemanage/fabrics API path.

        ### Parameters
        - segments: Path segments to append after fabrics (e.g., fabric_name)

        ### Returns
        - Complete onemanage/fabrics path

        ### Example
        ```python
        path = BasePath.onemanage_fabrics("MyFabric")
        # Returns: /appcenter/cisco/ndfc/api/v1/onemanage/fabrics/MyFabric
        ```
        """
        return cls.onemanage("fabrics", *segments)

    @classmethod
    def onemanage_links(cls, *segments: str) -> str:
        """
        Build onemanage/links API path.

        ### Parameters
        - segments: Path segments to append after links (e.g., link_uuid)

        ### Returns
        - Complete onemanage/links path

        ### Example
        ```python
        path = BasePath.onemanage_links("63505f61-ce7b-40a6-a38c-ae9a355b2116")
        # Returns: /appcenter/cisco/ndfc/api/v1/onemanage/links/63505f61-ce7b-40a6-a38c-ae9a355b2116
        ```
        """
        return cls.onemanage("links", *segments)

    @classmethod
    def onemanage_links_fabrics(cls, *segments: str) -> str:
        """
        Build onemanage/links/fabrics API path.

        ### Parameters
        - segments: Path segments to append after links/fabrics (e.g., fabric_name)

        ### Returns
        - Complete onemanage/links/fabrics path

        ### Example
        ```python
        path = BasePath.onemanage_links_fabrics("MyFabric")
        # Returns: /appcenter/cisco/ndfc/api/v1/onemanage/links/fabrics/MyFabric
        ```
        """
        return cls.onemanage("links", "fabrics", *segments)

    @classmethod
    def onemanage_top_down(cls, *segments: str) -> str:
        """
        Build onemanage/top-down API path.

        ### Parameters
        - segments: Path segments to append after top-down (e.g., fabric_name)

        ### Returns
        - Complete onemanage/top-down path

        ### Example
        ```python
        path = BasePath.onemanage_top_down("fabrics", "MyFabric")
        # Returns: /appcenter/cisco/ndfc/api/v1/onemanage/top-down/fabrics/MyFabric
        ```
        """
        return cls.onemanage("top-down", *segments)

    @classmethod
    def onemanage_top_down_fabrics(cls, *segments: str) -> str:
        """
        Build onemanage/top-down/fabrics API path.

        ### Parameters
        - segments: Path segments to append after top-down/fabrics (e.g., fabric_name)

        ### Returns
        - Complete onemanage/top-down/fabrics path

        ### Example
        ```python
        path = BasePath.onemanage_top_down_fabrics("MyFabric")
        # Returns: /appcenter/cisco/ndfc/api/v1/onemanage/top-down/fabrics/MyFabric
        ```
        """
        return cls.onemanage_top_down("fabrics", *segments)
