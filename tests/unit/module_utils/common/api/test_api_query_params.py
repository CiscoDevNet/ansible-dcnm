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

"""Unit tests for query_params.py"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name

from typing import Optional

import pytest  # pylint: disable=unused-import,import-error
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.query_params import (
    CompositeQueryParams,
    EndpointQueryParams,
    LuceneQueryParams,
)
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import does_not_raise
from pydantic import ValidationError

# =============================================================================
# Helper Classes for Testing
# =============================================================================


class MockEndpointParams(EndpointQueryParams):
    """Mock endpoint-specific query parameters."""

    force_show_run: bool = False
    include_all_msd_switches: bool = False


class MockTicketParams(EndpointQueryParams):
    """Mock ticket ID query parameters."""

    ticket_id: Optional[str] = None

    def to_query_string(self) -> str:
        """Custom query string with ticketId."""
        if self.ticket_id:
            return f"ticketId={self.ticket_id}"
        return ""


# =============================================================================
# Test: EndpointQueryParams
# =============================================================================


def test_query_params_00100():
    """
    ### Class
    - EndpointQueryParams

    ### Summary
    - Verify default to_query_string() with default values
    """
    with does_not_raise():
        params = MockEndpointParams()
        result = params.to_query_string()
    assert result == "forceShowRun=false&includeAllMsdSwitches=false"


def test_query_params_00110():
    """
    ### Class
    - EndpointQueryParams

    ### Summary
    - Verify to_query_string() with parameters set
    """
    with does_not_raise():
        params = MockEndpointParams(force_show_run=True, include_all_msd_switches=True)
        result = params.to_query_string()
    assert result == "forceShowRun=true&includeAllMsdSwitches=true"


def test_query_params_00120():
    """
    ### Class
    - EndpointQueryParams

    ### Summary
    - Verify to_query_string() with mixed boolean values
    """
    with does_not_raise():
        params = MockEndpointParams(force_show_run=True, include_all_msd_switches=False)
        result = params.to_query_string()
    assert result == "forceShowRun=true&includeAllMsdSwitches=false"


def test_query_params_00130():
    """
    ### Class
    - EndpointQueryParams

    ### Summary
    - Verify is_empty() returns True when only defaults are set
    """
    with does_not_raise():
        params = MockEndpointParams()
        result = params.is_empty()
    assert result is True  # Defaults don't count as "set"


def test_query_params_00140():
    """
    ### Class
    - EndpointQueryParams

    ### Summary
    - Verify is_empty() returns False when parameters are set
    """
    with does_not_raise():
        params = MockEndpointParams(force_show_run=True)
        result = params.is_empty()
    assert result is False


def test_query_params_00150():
    """
    ### Class
    - EndpointQueryParams

    ### Summary
    - Verify custom to_query_string() implementation
    """
    with does_not_raise():
        params = MockTicketParams(ticket_id="CHG0012345")
        result = params.to_query_string()
    assert result == "ticketId=CHG0012345"


def test_query_params_00160():
    """
    ### Class
    - EndpointQueryParams

    ### Summary
    - Verify custom to_query_string() with None value
    """
    with does_not_raise():
        params = MockTicketParams()
        result = params.to_query_string()
    assert result == ""


def test_query_params_00170():
    """
    ### Class
    - EndpointQueryParams

    ### Summary
    - Verify _to_camel_case() helper method
    """
    with does_not_raise():
        result1 = EndpointQueryParams._to_camel_case("force_show_run")  # pylint: disable=protected-access
        result2 = EndpointQueryParams._to_camel_case("include_all_msd_switches")  # pylint: disable=protected-access
        result3 = EndpointQueryParams._to_camel_case("ticket_id")  # pylint: disable=protected-access
    assert result1 == "forceShowRun"
    assert result2 == "includeAllMsdSwitches"
    assert result3 == "ticketId"


# =============================================================================
# Test: LuceneQueryParams
# =============================================================================


def test_query_params_00200():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify empty LuceneQueryParams
    """
    with does_not_raise():
        params = LuceneQueryParams()
        result = params.to_query_string()
    assert result == ""
    assert params.is_empty() is True


def test_query_params_00210():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify LuceneQueryParams with filter only
    """
    with does_not_raise():
        params = LuceneQueryParams(filter="name:MyFabric")
        result = params.to_query_string()
    assert result == "filter=name:MyFabric"
    assert params.is_empty() is False


def test_query_params_00220():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify LuceneQueryParams with max only
    """
    with does_not_raise():
        params = LuceneQueryParams(max=100)
        result = params.to_query_string()
    assert result == "max=100"
    assert params.is_empty() is False


def test_query_params_00230():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify LuceneQueryParams with offset only
    """
    with does_not_raise():
        params = LuceneQueryParams(offset=50)
        result = params.to_query_string()
    assert result == "offset=50"


def test_query_params_00240():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify LuceneQueryParams with sort only
    """
    with does_not_raise():
        params = LuceneQueryParams(sort="name:asc")
        result = params.to_query_string()
    assert result == "sort=name:asc"


def test_query_params_00250():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify LuceneQueryParams with fields only
    """
    with does_not_raise():
        params = LuceneQueryParams(fields="name,state,created")
        result = params.to_query_string()
    assert result == "fields=name,state,created"


def test_query_params_00260():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify LuceneQueryParams with all parameters
    """
    with does_not_raise():
        params = LuceneQueryParams(filter="name:Fabric* AND state:deployed", max=100, offset=0, sort="name:asc", fields="name,state")
        result = params.to_query_string()
    assert "filter=name:Fabric* AND state:deployed" in result
    assert "max=100" in result
    assert "offset=0" in result
    assert "sort=name:asc" in result
    assert "fields=name,state" in result


def test_query_params_00270():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify LuceneQueryParams with wildcard filter
    """
    with does_not_raise():
        params = LuceneQueryParams(filter="name:Fabric*")
        result = params.to_query_string()
    assert result == "filter=name:Fabric*"


def test_query_params_00280():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify LuceneQueryParams with AND condition
    """
    with does_not_raise():
        params = LuceneQueryParams(filter="name:MyFabric AND state:deployed")
        result = params.to_query_string()
    assert result == "filter=name:MyFabric AND state:deployed"


def test_query_params_00290():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify LuceneQueryParams with OR condition
    """
    with does_not_raise():
        params = LuceneQueryParams(filter="state:deployed OR state:pending")
        result = params.to_query_string()
    assert result == "filter=state:deployed OR state:pending"


def test_query_params_00300():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify LuceneQueryParams with NOT condition
    """
    with does_not_raise():
        params = LuceneQueryParams(filter="NOT state:deleted")
        result = params.to_query_string()
    assert result == "filter=NOT state:deleted"


# =============================================================================
# Test: LuceneQueryParams Validation
# =============================================================================


def test_query_params_00400():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify sort validation with valid 'asc' direction
    """
    with does_not_raise():
        params = LuceneQueryParams(sort="name:asc")
    assert params.sort == "name:asc"


def test_query_params_00410():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify sort validation with valid 'desc' direction
    """
    with does_not_raise():
        params = LuceneQueryParams(sort="created:desc")
    assert params.sort == "created:desc"


def test_query_params_00420():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify sort validation with invalid direction raises ValueError
    """
    match = r"Sort direction must be 'asc' or 'desc'"
    with pytest.raises(ValidationError, match=match):
        LuceneQueryParams(sort="name:invalid")


def test_query_params_00430():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify sort validation without colon (no direction)
    """
    with does_not_raise():
        params = LuceneQueryParams(sort="name")
    assert params.sort == "name"


def test_query_params_00440():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify max validation with valid value
    """
    with does_not_raise():
        params = LuceneQueryParams(max=100)
    assert params.max == 100


def test_query_params_00450():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify max validation with minimum value (1)
    """
    with does_not_raise():
        params = LuceneQueryParams(max=1)
    assert params.max == 1


def test_query_params_00460():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify max validation with maximum value (10000)
    """
    with does_not_raise():
        params = LuceneQueryParams(max=10000)
    assert params.max == 10000


def test_query_params_00470():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify max validation with value less than 1 raises ValidationError
    """
    with pytest.raises(ValidationError):
        LuceneQueryParams(max=0)


def test_query_params_00480():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify max validation with value greater than 10000 raises ValidationError
    """
    with pytest.raises(ValidationError):
        LuceneQueryParams(max=10001)


def test_query_params_00490():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify offset validation with valid value
    """
    with does_not_raise():
        params = LuceneQueryParams(offset=50)
    assert params.offset == 50


def test_query_params_00500():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify offset validation with minimum value (0)
    """
    with does_not_raise():
        params = LuceneQueryParams(offset=0)
    assert params.offset == 0


def test_query_params_00510():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify offset validation with negative value raises ValidationError
    """
    with pytest.raises(ValidationError):
        LuceneQueryParams(offset=-1)


# =============================================================================
# Test: CompositeQueryParams
# =============================================================================


def test_query_params_00600():
    """
    ### Class
    - CompositeQueryParams

    ### Summary
    - Verify empty CompositeQueryParams
    """
    with does_not_raise():
        composite = CompositeQueryParams()
        result = composite.to_query_string()
    assert result == ""
    assert composite.is_empty() is True


def test_query_params_00610():
    """
    ### Class
    - CompositeQueryParams

    ### Summary
    - Verify CompositeQueryParams with single endpoint params
    """
    with does_not_raise():
        endpoint_params = MockEndpointParams(force_show_run=True)
        composite = CompositeQueryParams()
        composite.add(endpoint_params)
        result = composite.to_query_string()
    assert result == "forceShowRun=true&includeAllMsdSwitches=false"
    assert composite.is_empty() is False


def test_query_params_00620():
    """
    ### Class
    - CompositeQueryParams

    ### Summary
    - Verify CompositeQueryParams with single Lucene params
    """
    with does_not_raise():
        lucene_params = LuceneQueryParams(filter="name:MyFabric", max=100)
        composite = CompositeQueryParams()
        composite.add(lucene_params)
        result = composite.to_query_string()
    assert result == "filter=name:MyFabric&max=100"


def test_query_params_00630():
    """
    ### Class
    - CompositeQueryParams

    ### Summary
    - Verify CompositeQueryParams with endpoint and Lucene params
    """
    with does_not_raise():
        endpoint_params = MockEndpointParams(force_show_run=True, include_all_msd_switches=False)
        lucene_params = LuceneQueryParams(filter="name:Fabric*", max=50, sort="name:asc")
        composite = CompositeQueryParams()
        composite.add(endpoint_params)
        composite.add(lucene_params)
        result = composite.to_query_string()
    # Verify all parts are present
    assert "forceShowRun=true" in result
    assert "includeAllMsdSwitches=false" in result
    assert "filter=name:Fabric*" in result
    assert "max=50" in result
    assert "sort=name:asc" in result


def test_query_params_00640():
    """
    ### Class
    - CompositeQueryParams

    ### Summary
    - Verify CompositeQueryParams with method chaining
    """
    with does_not_raise():
        endpoint_params = MockEndpointParams(force_show_run=True)
        lucene_params = LuceneQueryParams(filter="name:Test*")
        composite = CompositeQueryParams()
        result_composite = composite.add(endpoint_params).add(lucene_params)
        result = result_composite.to_query_string()
    # Verify method chaining returns self
    assert result_composite is composite
    # Verify query string contains both
    assert "forceShowRun=true" in result
    assert "filter=name:Test*" in result


def test_query_params_00650():
    """
    ### Class
    - CompositeQueryParams

    ### Summary
    - Verify CompositeQueryParams with empty endpoint params
    """
    with does_not_raise():
        endpoint_params = MockTicketParams()  # No ticket_id set
        lucene_params = LuceneQueryParams(filter="name:MyFabric")
        composite = CompositeQueryParams()
        composite.add(endpoint_params)
        composite.add(lucene_params)
        result = composite.to_query_string()
    # Empty endpoint params should not appear
    assert result == "filter=name:MyFabric"


def test_query_params_00660():
    """
    ### Class
    - CompositeQueryParams

    ### Summary
    - Verify CompositeQueryParams with empty Lucene params
    """
    with does_not_raise():
        endpoint_params = MockEndpointParams(force_show_run=True)
        lucene_params = LuceneQueryParams()  # No parameters set
        composite = CompositeQueryParams()
        composite.add(endpoint_params)
        composite.add(lucene_params)
        result = composite.to_query_string()
    # Empty Lucene params should not appear
    assert "forceShowRun=true" in result
    assert "filter=" not in result


def test_query_params_00670():
    """
    ### Class
    - CompositeQueryParams

    ### Summary
    - Verify CompositeQueryParams clear() method
    """
    with does_not_raise():
        endpoint_params = MockEndpointParams(force_show_run=True)
        composite = CompositeQueryParams()
        composite.add(endpoint_params)
        assert composite.is_empty() is False
        composite.clear()
        result = composite.to_query_string()
    assert result == ""
    assert composite.is_empty() is True


def test_query_params_00680():
    """
    ### Class
    - CompositeQueryParams

    ### Summary
    - Verify CompositeQueryParams with multiple endpoint param groups
    """
    with does_not_raise():
        params1 = MockEndpointParams(force_show_run=True)
        params2 = MockTicketParams(ticket_id="CHG12345")
        composite = CompositeQueryParams()
        composite.add(params1).add(params2)
        result = composite.to_query_string()
    assert "forceShowRun=true" in result
    assert "ticketId=CHG12345" in result


def test_query_params_00690():
    """
    ### Class
    - CompositeQueryParams

    ### Summary
    - Verify CompositeQueryParams is_empty() with all empty params
    """
    with does_not_raise():
        params1 = MockTicketParams()  # Empty
        params2 = LuceneQueryParams()  # Empty
        composite = CompositeQueryParams()
        composite.add(params1).add(params2)
        result = composite.is_empty()
    assert result is True


# =============================================================================
# Test: Edge Cases and Special Scenarios
# =============================================================================


def test_query_params_00800():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify Lucene filter with special characters
    """
    with does_not_raise():
        params = LuceneQueryParams(filter="name:My-Fabric_123")
        result = params.to_query_string()
    assert result == "filter=name:My-Fabric_123"


def test_query_params_00810():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify Lucene filter with spaces
    """
    with does_not_raise():
        params = LuceneQueryParams(filter="name:My Fabric")
        result = params.to_query_string()
    assert result == "filter=name:My Fabric"


def test_query_params_00820():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify Lucene filter with range query
    """
    with does_not_raise():
        params = LuceneQueryParams(filter="created:[2024-01-01 TO 2024-12-31]")
        result = params.to_query_string()
    assert result == "filter=created:[2024-01-01 TO 2024-12-31]"


def test_query_params_00830():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify Lucene filter with parentheses
    """
    with does_not_raise():
        params = LuceneQueryParams(filter="(name:Fabric1 OR name:Fabric2) AND state:deployed")
        result = params.to_query_string()
    assert result == "filter=(name:Fabric1 OR name:Fabric2) AND state:deployed"


def test_query_params_00840():
    """
    ### Class
    - EndpointQueryParams

    ### Summary
    - Verify parameter order is consistent
    """
    with does_not_raise():
        params1 = MockEndpointParams(force_show_run=True, include_all_msd_switches=False)
        params2 = MockEndpointParams(force_show_run=True, include_all_msd_switches=False)
        result1 = params1.to_query_string()
        result2 = params2.to_query_string()
    assert result1 == result2


def test_query_params_00850():
    """
    ### Class
    - CompositeQueryParams

    ### Summary
    - Verify order of parameter groups in composite
    """
    with does_not_raise():
        endpoint_params = MockEndpointParams(force_show_run=True)
        lucene_params = LuceneQueryParams(filter="name:Test")
        composite = CompositeQueryParams()
        composite.add(endpoint_params).add(lucene_params)
        result = composite.to_query_string()
    # Endpoint params should come before Lucene params
    assert result.index("forceShowRun") < result.index("filter")


def test_query_params_00860():
    """
    ### Class
    - LuceneQueryParams

    ### Summary
    - Verify fields parameter with multiple fields
    """
    with does_not_raise():
        params = LuceneQueryParams(fields="name,state,created,modified")
        result = params.to_query_string()
    assert result == "fields=name,state,created,modified"
