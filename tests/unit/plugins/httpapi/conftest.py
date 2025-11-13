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
Fixtures for HttpApi tests
"""

import pytest
from unittest.mock import Mock


@pytest.fixture
def mock_connection():
    """Create a mock connection object."""
    connection = Mock()
    connection._url = "https://test.nd.com"
    connection._auth = None
    connection.get_option.return_value = 10
    return connection


@pytest.fixture
def mock_response_success():
    """Create a mock successful HTTP response."""
    response = Mock()
    response.getcode.return_value = 200
    response.geturl.return_value = "/api/test"
    response.msg = "OK"
    return response


@pytest.fixture
def mock_response_failure():
    """Create a mock failed HTTP response."""
    response = Mock()
    response.getcode.return_value = 401
    response.geturl.return_value = "/api/test"
    response.msg = "Unauthorized"
    return response


@pytest.fixture
def mock_response_data_json():
    """Create mock response data with JSON."""
    rdata = Mock()
    rdata.getvalue.return_value = b'{"result": "success", "token": "test123"}'
    return rdata


@pytest.fixture
def mock_response_data_nd_token():
    """Create mock response data with DCNM token."""
    rdata = Mock()
    rdata.getvalue.return_value = b'{"Dcnm-Token": "nd-token-123"}'
    return rdata


@pytest.fixture
def mock_response_data_ndfc_token():
    """Create mock response data with NDFC token."""
    rdata = Mock()
    rdata.getvalue.return_value = b'{"token": "ndfc-token-456"}'
    return rdata


@pytest.fixture
def nd_login_config():
    """Standard DCNM login configuration."""
    return {"controller_type": "DCNM", "version": 11, "path": "/rest/logon", "data": "{'expirationTime': 10000}", "force_basic_auth": True}


@pytest.fixture
def ndfc_login_config():
    """Standard NDFC login configuration."""
    return {
        "controller_type": "NDFC",
        "version": 12,
        "path": "/login",
        "data": '{"userName": "admin", "userPasswd": "password", "domain": "local"}',
        "force_basic_auth": False,
    }


@pytest.fixture
def nd_logout_config():
    """Standard DCNM logout configuration."""
    return {"controller_type": "DCNM", "path": "/rest/logout", "data": "test-token", "force_basic_auth": True}


@pytest.fixture
def ndfc_logout_config():
    """Standard NDFC logout configuration."""
    return {"controller_type": "NDFC", "path": "/logout", "data": {}, "force_basic_auth": False}
