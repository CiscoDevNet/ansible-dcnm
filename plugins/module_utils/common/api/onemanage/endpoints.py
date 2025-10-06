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

from typing import Literal

from pydantic import BaseModel, Field  # field_validator

from ..base_paths import BasePath

# Import query parameter models as needed
# from ..query_params import (
#     CompositeQueryParams,
#     EndpointQueryParams,
#     LuceneQueryParams,
# )


class EpOneManageFabricCreate(BaseModel):
    """
    ## Fabric Create Endpoint (OneManage)

    ### Description
    Endpoint to create a new multi-cluster fabric.

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

    ### Usage
    ```python
    request = EpOneManageFabricDetails()
    request.fabric_name = "MyFabric"

    path = request.path
    verb = request.verb
    ```
    """

    class_name: str = "EpOneManageFabricDetails"  # For backward compatibility
    fabric_name: str | None = Field(None, min_length=1, description="Fabric name")

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
