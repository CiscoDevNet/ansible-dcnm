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
Query parameter classes for API endpoints.

This module provides composable query parameter classes for building
URL query strings. Supports endpoint-specific parameters and Lucene-style
filtering with type safety via Pydantic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

from abc import ABC, abstractmethod
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator


class QueryParams(ABC):
    """
    ## Abstract Base Class for Query Parameters

    ### Description
    Base class for all query parameter types. Subclasses implement
    `to_query_string()` to convert their parameters to URL query string format.

    ### Design
    This allows composition of different query parameter types:
    - Endpoint-specific parameters (e.g., forceShowRun, ticketId)
    - Generic Lucene-style filtering (e.g., filter, max, sort)
    - Future parameter types can be added without changing existing code
    """

    @abstractmethod
    def to_query_string(self) -> str:
        """
        Convert parameters to URL query string format.

        ### Returns
        - Query string (without leading '?')
        - Empty string if no parameters are set

        ### Example
        ```python
        "forceShowRun=true&ticketId=12345"
        ```
        """

    def is_empty(self) -> bool:
        """
        Check if any parameters are set.

        ### Returns
        - True if no parameters are set
        - False if at least one parameter is set
        """
        return len(self.to_query_string()) == 0


class EndpointQueryParams(BaseModel):
    """
    ## Endpoint-Specific Query Parameters

    ### Description
    Query parameters specific to a particular endpoint.
    These are typed and validated by Pydantic.

    ### Usage
    Subclass this for each endpoint that needs custom query parameters:

    ```python
    class ConfigDeployQueryParams(EndpointQueryParams):
        force_show_run: bool = False
        include_all_msd_switches: bool = False

        def to_query_string(self) -> str:
            params = [f"forceShowRun={str(self.force_show_run).lower()}"]
            params.append(f"inclAllMSDSwitches={str(self.include_all_msd_switches).lower()}")
            return "&".join(params)
    ```
    """

    def to_query_string(self) -> str:
        """
        Default implementation: convert all fields to key=value pairs.
        Override this method for custom formatting.
        """
        params = []
        for field_name, field_value in self.model_dump(exclude_none=True).items():
            # Convert snake_case to camelCase for API compatibility
            api_key = self._to_camel_case(field_name)
            api_value = str(field_value).lower() if isinstance(field_value, bool) else str(field_value)
            params.append(f"{api_key}={api_value}")
        return "&".join(params)

    @staticmethod
    def _to_camel_case(snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    def is_empty(self) -> bool:
        """Check if any parameters are set."""
        return len(self.model_dump(exclude_none=True, exclude_defaults=True)) == 0


class LuceneQueryParams(BaseModel):
    """
    ## Lucene-Style Query Parameters

    ### Description
    Generic Lucene-style filtering query parameters for ND API.
    Supports filtering, pagination, and sorting.

    ### Parameters
    - filter: Lucene filter expression (e.g., "name:MyFabric AND state:deployed")
    - max: Maximum number of results to return
    - offset: Offset for pagination
    - sort: Sort field and direction (e.g., "name:asc", "created:desc")
    - fields: Comma-separated list of fields to return

    ### Usage
    ```python
    lucene = LuceneQueryParams(
        filter="name:Fabric*",
        max=100,
        sort="name:asc"
    )
    query_string = lucene.to_query_string()
    # Returns: "filter=name:Fabric*&max=100&sort=name:asc"
    ```

    ### Lucene Filter Examples
    - Single field: `name:MyFabric`
    - Wildcard: `name:Fabric*`
    - Multiple conditions: `name:MyFabric AND state:deployed`
    - Range: `created:[2024-01-01 TO 2024-12-31]`
    - OR conditions: `state:deployed OR state:pending`
    - NOT conditions: `NOT state:deleted`
    """

    filter: Optional[str] = Field(None, description="Lucene filter expression")
    max: Optional[int] = Field(None, ge=1, le=10000, description="Maximum results")
    offset: Optional[int] = Field(None, ge=0, description="Pagination offset")
    sort: Optional[str] = Field(None, description="Sort field and direction (e.g., 'name:asc')")
    fields: Optional[str] = Field(None, description="Comma-separated list of fields to return")

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, value):
        """Validate sort format: field:direction."""
        if value is not None and ":" in value:
            parts = value.split(":")
            if len(parts) == 2 and parts[1].lower() not in ["asc", "desc"]:
                raise ValueError("Sort direction must be 'asc' or 'desc'")
        return value

    def to_query_string(self) -> str:
        """Convert to URL query string format."""
        params = []
        for field_name, field_value in self.model_dump(exclude_none=True).items():
            if field_value is not None:
                params.append(f"{field_name}={field_value}")
        return "&".join(params)

    def is_empty(self) -> bool:
        """Check if any filter parameters are set."""
        return all(v is None for v in self.model_dump().values())


class CompositeQueryParams:
    """
    ## Composite Query Parameters

    ### Description
    Composes multiple query parameter types into a single query string.
    This allows combining endpoint-specific parameters with Lucene filtering.

    ### Design Pattern
    Uses composition to combine different query parameter types without
    inheritance. Each parameter type can be independently configured and tested.

    ### Usage
    ```python
    # Endpoint-specific params
    endpoint_params = ConfigDeployQueryParams(
        force_show_run=True,
        include_all_msd_switches=False
    )

    # Lucene filtering params
    lucene_params = LuceneQueryParams(
        filter="name:MySwitch*",
        max=50,
        sort="name:asc"
    )

    # Compose them together
    composite = CompositeQueryParams()
    composite.add(endpoint_params)
    composite.add(lucene_params)

    query_string = composite.to_query_string()
    # Returns: "forceShowRun=true&inclAllMSDSwitches=false&filter=name:MySwitch*&max=50&sort=name:asc"
    ```
    """

    def __init__(self) -> None:
        self._param_groups: list[Union[EndpointQueryParams, LuceneQueryParams]] = []

    def add(self, params: Union[EndpointQueryParams, LuceneQueryParams]) -> "CompositeQueryParams":
        """
        Add a query parameter group to the composite.

        ### Parameters
        - params: EndpointQueryParams or LuceneQueryParams instance

        ### Returns
        - Self (for method chaining)

        ### Example
        ```python
        composite = CompositeQueryParams()
        composite.add(endpoint_params).add(lucene_params)
        ```
        """
        self._param_groups.append(params)
        return self

    def to_query_string(self) -> str:
        """
        Build complete query string from all parameter groups.

        ### Returns
        - Complete query string (without leading '?')
        - Empty string if no parameters are set
        """
        parts = []
        for param_group in self._param_groups:
            if not param_group.is_empty():
                parts.append(param_group.to_query_string())
        return "&".join(parts)

    def is_empty(self) -> bool:
        """Check if any parameters are set across all groups."""
        return all(param_group.is_empty() for param_group in self._param_groups)

    def clear(self) -> None:
        """Remove all parameter groups."""
        self._param_groups.clear()
