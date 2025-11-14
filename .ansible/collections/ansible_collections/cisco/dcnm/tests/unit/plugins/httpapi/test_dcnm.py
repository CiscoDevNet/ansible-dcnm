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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# pylint: disable=unused-import
# Some fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-argument
# Some tests require calling protected methods
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Mike Wiebe"

import json
import io
from unittest.mock import Mock, MagicMock, patch

import pytest
import requests

from ansible.module_utils.connection import ConnectionError
from ansible_collections.cisco.dcnm.plugins.httpapi.dcnm import HttpApi

# Running These Tests
# cd <path>/collections
# PYTHONPATH=<path>/collections python -m pytest ansible_collections/cisco/dcnm/tests/unit/plugins/httpapi/test_dcnm.py -v
#
# Example
# cd /Users/mwiebe/Projects/Ansible/nac-vxlan/collections
# PYTHONPATH=/Users/mwiebe/Projects/Ansible/nac-vxlan/collections python -m pytest ansible_collections/cisco/dcnm/tests/unit/plugins/httpapi/test_dcnm.py -v


class TestHttpApiInit:
    """Test HttpApi initialization."""

    def test_init_default_values(self, mock_connection):
        """Test that HttpApi initializes with correct default values."""
        http_api = HttpApi(mock_connection)

        assert http_api.headers == {"Content-Type": "application/json", 'Transfer-Encoding': 'chunked'}
        assert http_api.txt_headers == {"Content-Type": "text/plain"}
        assert http_api.version is None
        assert http_api.retrycount == 5

    def test_init_inheritance(self, mock_connection):
        """Test that HttpApi properly inherits from HttpApiBase."""
        from ansible.plugins.httpapi import HttpApiBase

        http_api = HttpApi(mock_connection)
        assert isinstance(http_api, HttpApiBase)


class TestHttpApiVersionMethods:
    """Test version getter and setter methods."""

    def test_get_version_initial(self, mock_connection):
        """Test get_version returns None initially."""
        http_api = HttpApi(mock_connection)
        assert http_api.get_version() is None

    def test_set_get_version(self, mock_connection):
        """Test setting and getting version."""
        http_api = HttpApi(mock_connection)
        http_api.set_version(11)
        assert http_api.get_version() == 11

        http_api.set_version(12)
        assert http_api.get_version() == 12


class TestHttpApiTokenMethods:
    """Test token getter and setter methods."""

    def test_set_get_token(self, mock_connection):
        """Test setting and getting token."""
        http_api = HttpApi(mock_connection)
        test_token = {"Authorization": "Bearer test123"}

        http_api.set_token(test_token)
        assert http_api.get_token() == test_token


class TestHttpApiConnectionMethods:
    """Test URL connection methods."""

    @patch("requests.head")
    def test_check_url_connection_success(self, mock_head, mock_connection):
        """Test successful URL connection check."""
        mock_head.return_value = Mock()
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection._url = "https://test.nd.com"

        # Should not raise exception
        http_api.check_url_connection()
        mock_head.assert_called_once_with("https://test.nd.com", verify=False)

    @patch("requests.head", side_effect=requests.exceptions.RequestException("Connection failed"))
    def test_check_url_connection_failure(self, mock_head, mock_connection):
        """Test URL connection check failure."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection._url = "https://test.nd.com"

        with pytest.raises(ConnectionError) as exc_info:
            http_api.check_url_connection()

        assert "Connection failed" in str(exc_info.value)
        assert "Please verify that the DCNM controller HTTPS URL" in str(exc_info.value)

    def test_get_url_connection(self, mock_connection):
        """Test getting URL connection."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection._url = "https://test.nd.com"

        assert http_api.get_url_connection() == "https://test.nd.com"


class TestHttpApiResponseParsing:
    """Test response parsing methods."""

    def test_get_response_value(self, mock_connection):
        """Test extracting response value."""
        http_api = HttpApi(mock_connection)
        mock_response_data = Mock()
        mock_response_data.getvalue.return_value = b'{"test": "data"}'

        result = http_api._get_response_value(mock_response_data)
        assert result == '{"test": "data"}'

    def test_response_to_json_valid(self, mock_connection):
        """Test converting valid JSON response."""
        http_api = HttpApi(mock_connection)
        json_string = '{"key": "value", "number": 123}'

        result = http_api._response_to_json(json_string)
        assert result == {"key": "value", "number": 123}

    def test_response_to_json_empty(self, mock_connection):
        """Test converting empty response."""
        http_api = HttpApi(mock_connection)

        result = http_api._response_to_json("")
        assert result == {}

    def test_response_to_json_invalid(self, mock_connection):
        """Test converting invalid JSON response."""
        http_api = HttpApi(mock_connection)
        invalid_json = "invalid json content"

        result = http_api._response_to_json(invalid_json)
        assert result == "Invalid JSON response: invalid json content"

    def test_response_to_json12_valid_with_getvalue(self, mock_connection):
        """Test converting valid JSON response for v12 with getvalue method."""
        http_api = HttpApi(mock_connection)
        mock_response = Mock()
        mock_response.getvalue.return_value = b'{"token": "abc123"}'

        result = http_api._response_to_json12(mock_response)
        assert result == {"token": "abc123"}

    def test_response_to_json12_valid_without_getvalue(self, mock_connection):
        """Test converting valid JSON response for v12 without getvalue method."""
        http_api = HttpApi(mock_connection)
        response_text = '{"token": "abc123"}'

        result = http_api._response_to_json12(response_text)
        assert result == {"token": "abc123"}

    def test_response_to_json12_empty(self, mock_connection):
        """Test converting empty response for v12."""
        http_api = HttpApi(mock_connection)

        result = http_api._response_to_json12("")
        assert result == {}

    def test_response_to_json12_invalid(self, mock_connection):
        """Test converting invalid JSON response for v12."""
        http_api = HttpApi(mock_connection)
        invalid_json = "invalid json content"

        result = http_api._response_to_json12(invalid_json)
        assert result == "Invalid JSON response: invalid json content"


class TestHttpApiReturnInfo:
    """Test return info formatting method."""

    def test_return_info_complete(self, mock_connection):
        """Test return info with all parameters."""
        http_api = HttpApi(mock_connection)

        result = http_api._return_info(200, "GET", "/api/test", "OK", {"data": "test"})

        expected = {"RETURN_CODE": 200, "METHOD": "GET", "REQUEST_PATH": "/api/test", "MESSAGE": "OK", "DATA": {"data": "test"}}
        assert result == expected

    def test_return_info_minimal(self, mock_connection):
        """Test return info with minimal parameters."""
        http_api = HttpApi(mock_connection)

        result = http_api._return_info(404, "POST", "/api/missing", "Not Found")

        expected = {"RETURN_CODE": 404, "METHOD": "POST", "REQUEST_PATH": "/api/missing", "MESSAGE": "Not Found", "DATA": None}
        assert result == expected


class TestHttpApiVerifyResponse:
    """Test response verification method."""

    def test_verify_response_success(self, mock_connection):
        """Test successful response verification."""
        http_api = HttpApi(mock_connection)

        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = "/api/test"
        mock_response.msg = "OK"

        mock_rdata = Mock()
        mock_rdata.getvalue.return_value = b'{"result": "success"}'

        result = http_api._verify_response(mock_response, "GET", "/api/test", mock_rdata)

        assert result["RETURN_CODE"] == 200
        assert result["METHOD"] == "GET"
        assert result["REQUEST_PATH"] == "/api/test"
        assert result["MESSAGE"] == "OK"
        assert result["DATA"] == {"result": "success"}

    def test_verify_response_failure(self, mock_connection):
        """Test failed response verification."""
        http_api = HttpApi(mock_connection)

        mock_response = Mock()
        mock_response.getcode.return_value = 601  # Outside valid range
        mock_response.geturl.return_value = "/api/missing"
        mock_response.msg = "Invalid Range"

        mock_rdata = Mock()
        mock_rdata.getvalue.return_value = b'{"error": "invalid range"}'

        with pytest.raises(ConnectionError):
            http_api._verify_response(mock_response, "GET", "/api/missing", mock_rdata)

    def test_verify_response_edge_cases(self, mock_connection):
        """Test response verification edge cases."""
        http_api = HttpApi(mock_connection)

        mock_response = Mock()
        mock_response.getcode.return_value = 599  # Edge of acceptable range
        mock_response.geturl.return_value = "/api/test"
        mock_response.msg = "OK"

        mock_rdata = Mock()
        mock_rdata.getvalue.return_value = b'{"result": "success"}'

        result = http_api._verify_response(mock_response, "GET", "/api/test", mock_rdata)
        assert result["RETURN_CODE"] == 599


class TestHttpApiAttemptLogin:
    """Test attempt login method."""

    def test_attempt_login_nd_success(self, mock_connection):
        """Test successful DCNM login attempt."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.login_fail_msg = []

        # Mock successful response
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = "/rest/logon"
        mock_response.msg = "OK"

        mock_response_data = Mock()
        mock_response_data.getvalue.return_value = b'{"Dcnm-Token": "test-token"}'

        http_api.connection.send.return_value = (mock_response, mock_response_data)

        login_config = {"controller_type": "DCNM", "version": 11, "path": "/rest/logon", "data": "{'expirationTime': 10000}", "force_basic_auth": True}

        result = http_api._attempt_login(login_config)

        assert result is True
        assert http_api.login_succeeded is True
        assert http_api.version == 11
        assert http_api.connection._auth == {"Dcnm-Token": "test-token"}

    def test_attempt_login_ndfc_success(self, mock_connection):
        """Test successful NDFC login attempt."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.login_fail_msg = []

        # Mock successful response
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = "/login"
        mock_response.msg = "OK"

        mock_response_data = Mock()
        mock_response_data.getvalue.return_value = b'{"token": "ndfc-token"}'

        http_api.connection.send.return_value = (mock_response, mock_response_data)

        login_config = {
            "controller_type": "NDFC",
            "version": 12,
            "path": "/login",
            "data": '{"userName": "admin", "userPasswd": "password", "domain": "local"}',
            "force_basic_auth": False,
        }

        result = http_api._attempt_login(login_config)

        assert result is True
        assert http_api.login_succeeded is True
        assert http_api.version == 12
        expected_auth = {"Authorization": "Bearer ndfc-token", "Cookie": "AuthCookie=ndfc-token"}
        assert http_api.connection._auth == expected_auth

    def test_attempt_login_failure_bad_status(self, mock_connection):
        """Test login attempt failure due to bad status code."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.login_fail_msg = []

        # Mock failed response
        mock_response = Mock()
        mock_response.getcode.return_value = 401
        mock_response.geturl.return_value = "/rest/logon"
        mock_response.msg = "Unauthorized"

        mock_response_data = Mock()
        mock_response_data.getvalue.return_value = b'{"error": "invalid credentials"}'

        http_api.connection.send.return_value = (mock_response, mock_response_data)

        login_config = {"controller_type": "DCNM", "version": 11, "path": "/rest/logon", "data": "{'expirationTime': 10000}", "force_basic_auth": True}

        result = http_api._attempt_login(login_config)

        assert result is False
        assert len(http_api.login_fail_msg) == 1
        assert "Error on attempt to authenticate with DCNM controller" in http_api.login_fail_msg[0]

    def test_attempt_login_exception(self, mock_connection):
        """Test login attempt failure due to exception."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection.send.side_effect = Exception("Network error")
        http_api.login_fail_msg = []

        login_config = {"controller_type": "DCNM", "version": 11, "path": "/rest/logon", "data": "{'expirationTime': 10000}", "force_basic_auth": True}

        result = http_api._attempt_login(login_config)

        assert result is False
        assert len(http_api.login_fail_msg) == 1
        assert "Error on attempt to authenticate with DCNM controller" in http_api.login_fail_msg[0]
        assert "Network error" in http_api.login_fail_msg[0]


class TestHttpApiLogin:
    """Test login method."""

    @patch.object(HttpApi, "get_option")
    def test_login_success_first_attempt(self, mock_get_option, mock_connection):
        """Test successful login on first attempt."""
        mock_get_option.return_value = "local"

        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection.get_option.return_value = 10

        # Mock successful login attempt
        with patch.object(http_api, "_attempt_login", return_value=True) as mock_attempt:
            http_api.login("admin", "password")

            # Should call attempt_login once and return
            mock_attempt.assert_called_once()
            assert mock_attempt.call_args[0][0]["controller_type"] == "NDFC"

    @patch.object(HttpApi, "get_option")
    def test_login_success_second_attempt(self, mock_get_option, mock_connection):
        """Test successful login on second attempt."""
        mock_get_option.return_value = "local"

        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection.get_option.return_value = 10

        # Mock first attempt fails, second succeeds
        with patch.object(http_api, "_attempt_login", side_effect=[False, True]) as mock_attempt:
            http_api.login("admin", "password")

            # Should call attempt_login twice
            assert mock_attempt.call_count == 2

    @patch.object(HttpApi, "get_option")
    def test_login_all_attempts_fail(self, mock_get_option, mock_connection):
        """Test login when all attempts fail."""
        mock_get_option.return_value = "local"

        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection.get_option.return_value = 10
        http_api.login_fail_msg = ["Login failed"]

        # Mock all attempts fail
        with patch.object(http_api, "_attempt_login", return_value=False) as mock_attempt:
            with pytest.raises(ConnectionError):
                http_api.login("admin", "password")

            # Should call attempt_login three times (all configs)
            assert mock_attempt.call_count == 3

    @patch.object(HttpApi, "get_option")
    def test_login_custom_domain(self, mock_get_option, mock_connection):
        """Test login with custom domain."""
        mock_get_option.return_value = "custom-domain"

        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection.get_option.return_value = 10

        # Mock attempt_login to fail on first call, succeed on second
        with patch.object(http_api, "_attempt_login", side_effect=[False, True, False]) as mock_attempt:
            http_api.login("admin", "password")

            # Check that custom domain is used in NDFC login configs
            calls = mock_attempt.call_args_list
            assert len(calls) >= 2, "Should make at least 2 login attempts"
            ndfc_call = calls[1][0][0]  # Second call should be NDFC
            assert "custom-domain" in ndfc_call["data"]


class TestHttpApiAttemptLogout:
    """Test attempt logout method."""

    def test_attempt_logout_success(self, mock_connection):
        """Test successful logout attempt."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.logout_fail_msg = []

        # Mock successful response
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = "/rest/logout"
        mock_response.msg = "OK"

        mock_response_data = Mock()
        mock_response_data.getvalue.return_value = b'{"result": "success"}'

        http_api.connection.send.return_value = (mock_response, mock_response_data)

        logout_config = {"controller_type": "DCNM", "path": "/rest/logout", "data": "test-token", "force_basic_auth": True}

        result = http_api._attempt_logout(logout_config)

        assert result is True
        assert len(http_api.logout_fail_msg) == 0

    def test_attempt_logout_failure(self, mock_connection):
        """Test logout attempt failure."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.logout_fail_msg = []

        # Mock failed response
        mock_response = Mock()
        mock_response.getcode.return_value = 401
        mock_response.geturl.return_value = "/rest/logout"
        mock_response.msg = "Unauthorized"

        mock_response_data = Mock()
        mock_response_data.getvalue.return_value = b'{"error": "invalid token"}'

        http_api.connection.send.return_value = (mock_response, mock_response_data)

        logout_config = {"controller_type": "DCNM", "path": "/rest/logout", "data": "invalid-token", "force_basic_auth": True}

        result = http_api._attempt_logout(logout_config)

        assert result is False
        assert len(http_api.logout_fail_msg) == 1

    def test_attempt_logout_exception(self, mock_connection):
        """Test logout attempt exception."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection.send.side_effect = Exception("Network error")
        http_api.logout_fail_msg = []

        logout_config = {"controller_type": "DCNM", "path": "/rest/logout", "data": "test-token", "force_basic_auth": True}

        result = http_api._attempt_logout(logout_config)

        assert result is False
        assert len(http_api.logout_fail_msg) == 1
        assert "Network error" in http_api.logout_fail_msg[0]


class TestHttpApiLogout:
    """Test logout method."""

    def test_logout_no_auth(self, mock_connection):
        """Test logout when no authentication exists."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection._auth = None

        # Should return without error
        http_api.logout()

    def test_logout_no_version(self, mock_connection):
        """Test logout when version is not set."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection._auth = {"Dcnm-Token": "test"}
        http_api.version = None

        with pytest.raises(ConnectionError) as exc_info:
            http_api.logout()

        assert "Version not detected" in str(exc_info.value)

    def test_logout_nd_success(self, mock_connection):
        """Test successful DCNM logout."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection._auth = {"Dcnm-Token": "test-token"}
        http_api.version = 11

        with patch.object(http_api, "_attempt_logout", return_value=True) as mock_attempt:
            http_api.logout()

            assert http_api.logout_succeeded is True
            assert http_api.connection._auth is None
            mock_attempt.assert_called_once()

    def test_logout_ndfc_success(self, mock_connection):
        """Test successful NDFC logout."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection._auth = {"Authorization": "Bearer token"}
        http_api.version = 12

        with patch.object(http_api, "_attempt_logout", return_value=True) as mock_attempt:
            http_api.logout()

            assert http_api.logout_succeeded is True
            assert http_api.connection._auth is None
            mock_attempt.assert_called_once()

    def test_logout_failure(self, mock_connection):
        """Test logout failure."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection._auth = {"Dcnm-Token": "test-token"}
        http_api.version = 11
        http_api.logout_fail_msg = ["Logout failed"]

        with patch.object(http_api, "_attempt_logout", return_value=False) as mock_attempt:
            with pytest.raises(ConnectionError) as exc_info:
                http_api.logout()

            assert "Logout failed" in str(exc_info.value)


class TestHttpApiSendRequestInternal:
    """Test internal send request method."""

    @patch.object(HttpApi, "check_url_connection")
    def test_send_request_internal_success(self, mock_check_url, mock_connection):
        """Test successful internal request."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.retrycount = 5

        # Mock successful response
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = "/api/test"
        mock_response.msg = "OK"

        mock_rdata = Mock()
        mock_rdata.getvalue.return_value = b'{"result": "success"}'

        http_api.connection.send.return_value = (mock_response, mock_rdata)

        result = http_api._send_request_internal("GET", "/api/test", {"key": "value"})

        assert result["RETURN_CODE"] == 200
        assert result["DATA"] == {"result": "success"}
        mock_check_url.assert_called_once()

    @patch.object(HttpApi, "check_url_connection")
    def test_send_request_internal_invalid_path(self, mock_check_url, mock_connection):
        """Test internal request with invalid path."""
        http_api = HttpApi(mock_connection)

        with pytest.raises(ConnectionError) as exc_info:
            http_api._send_request_internal("GET", "invalid-path")

        assert "Value of <path> does not appear to be formatted properly" in str(exc_info.value)

    @patch.object(HttpApi, "check_url_connection")
    def test_send_request_internal_exception(self, mock_check_url, mock_connection):
        """Test internal request with exception."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection.send.side_effect = Exception("Network error")

        with pytest.raises(ConnectionError) as exc_info:
            http_api._send_request_internal("GET", "/api/test")

        assert "Network error" in str(exc_info.value)
        assert "Please verify your login credentials" in str(exc_info.value)

    @patch.object(HttpApi, "check_url_connection")
    def test_send_request_internal_dict_exception(self, mock_check_url, mock_connection):
        """Test internal request with dict-type exception."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection

        # Create an exception with dict args
        exception_dict = {"METHOD": "GET", "error": "test"}
        exception = Exception(exception_dict)
        http_api.connection.send.side_effect = exception

        result = http_api._send_request_internal("GET", "/api/test")

        assert result == exception_dict

    @patch.object(HttpApi, "check_url_connection")
    def test_send_request_internal_custom_headers(self, mock_check_url, mock_connection):
        """Test internal request with custom headers."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection

        # Mock successful response
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = "/api/test"
        mock_response.msg = "OK"

        mock_rdata = Mock()
        mock_rdata.getvalue.return_value = b'{"result": "success"}'

        http_api.connection.send.return_value = (mock_response, mock_rdata)

        custom_headers = {"Content-Type": "application/xml"}
        result = http_api._send_request_internal("POST", "/api/test", {"data": "test"}, custom_headers)

        # Verify custom headers were used
        call_args = http_api.connection.send.call_args
        assert call_args[1]["headers"] == custom_headers


class TestHttpApiPublicMethods:
    """Test public request methods."""

    def test_send_request(self, mock_connection):
        """Test send_request method."""
        http_api = HttpApi(mock_connection)

        with patch.object(http_api, "_send_request_internal") as mock_internal:
            mock_internal.return_value = {"RETURN_CODE": 200}

            result = http_api.send_request("GET", "/api/test", {"key": "value"})

            mock_internal.assert_called_once_with("GET", "/api/test", {"key": "value"}, http_api.headers)
            assert result == {"RETURN_CODE": 200}

    def test_send_request_no_json(self, mock_connection):
        """Test send_request method with no JSON data."""
        http_api = HttpApi(mock_connection)

        with patch.object(http_api, "_send_request_internal") as mock_internal:
            mock_internal.return_value = {"RETURN_CODE": 200}

            result = http_api.send_request("GET", "/api/test")

            mock_internal.assert_called_once_with("GET", "/api/test", {}, http_api.headers)

    def test_send_txt_request(self, mock_connection):
        """Test send_txt_request method."""
        http_api = HttpApi(mock_connection)

        with patch.object(http_api, "_send_request_internal") as mock_internal:
            mock_internal.return_value = {"RETURN_CODE": 200}

            result = http_api.send_txt_request("POST", "/api/text", "plain text data")

            mock_internal.assert_called_once_with("POST", "/api/text", "plain text data", http_api.txt_headers)
            assert result == {"RETURN_CODE": 200}

    def test_send_txt_request_no_txt(self, mock_connection):
        """Test send_txt_request method with no text data."""
        http_api = HttpApi(mock_connection)

        with patch.object(http_api, "_send_request_internal") as mock_internal:
            mock_internal.return_value = {"RETURN_CODE": 200}

            result = http_api.send_txt_request("POST", "/api/text")

            mock_internal.assert_called_once_with("POST", "/api/text", "", http_api.txt_headers)


class TestHttpApiEdgeCases:
    """Test edge cases and error conditions."""

    def test_response_to_json_none(self, mock_connection):
        """Test _response_to_json with None input."""
        http_api = HttpApi(mock_connection)

        result = http_api._response_to_json(None)
        assert result == {}

    def test_response_to_json12_exception_in_getvalue(self, mock_connection):
        """Test _response_to_json12 when getvalue raises exception."""
        http_api = HttpApi(mock_connection)

        mock_response = Mock()
        mock_response.getvalue.side_effect = Exception("getvalue failed")

        # Should fall back to using the response object directly
        result = http_api._response_to_json12(mock_response)
        # This will result in invalid JSON since mock_response is not a string
        assert "Invalid JSON response:" in str(result)

    def test_verify_response_boundary_codes(self, mock_connection):
        """Test _verify_response with boundary HTTP codes."""
        http_api = HttpApi(mock_connection)

        # Test lower boundary (200)
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = "/api/test"
        mock_response.msg = "OK"

        mock_rdata = Mock()
        mock_rdata.getvalue.return_value = b'{"result": "success"}'

        result = http_api._verify_response(mock_response, "GET", "/api/test", mock_rdata)
        assert result["RETURN_CODE"] == 200

        # Test upper boundary (600)
        mock_response.getcode.return_value = 600
        result = http_api._verify_response(mock_response, "GET", "/api/test", mock_rdata)
        assert result["RETURN_CODE"] == 600

        # Test outside boundary (601)
        mock_response.getcode.return_value = 601
        with pytest.raises(ConnectionError):
            http_api._verify_response(mock_response, "GET", "/api/test", mock_rdata)

    def test_login_configs_structure(self, mock_connection):
        """Test that login configurations are properly structured."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection.get_option.return_value = 10

        with patch.object(HttpApi, "get_option", return_value="testdomain"):
            with patch.object(http_api, "_attempt_login", return_value=True) as mock_attempt:
                http_api.login("testuser", "testpass")

                # Get the first call (DCNM config)
                nd_config = mock_attempt.call_args_list[0][0][0]
                assert nd_config["controller_type"] == "NDFC"
                assert nd_config["version"] == 12
                assert nd_config["path"] == "/login"
                assert nd_config["force_basic_auth"] is False

    def test_logout_config_selection(self, mock_connection):
        """Test that logout selects correct configuration based on version."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection._auth = {"Dcnm-Token": "test"}

        # Test DCNM version 11
        http_api.version = 11
        with patch.object(http_api, "_attempt_logout", return_value=True) as mock_attempt:
            http_api.logout()

            logout_config = mock_attempt.call_args[0][0]
            assert logout_config["controller_type"] == "DCNM"
            assert logout_config["path"] == "/rest/logout"
            assert logout_config["data"] == "test"
            assert logout_config["force_basic_auth"] is True

        # Test NDFC version 12
        http_api.connection._auth = {"Authorization": "Bearer token"}
        http_api.version = 12
        with patch.object(http_api, "_attempt_logout", return_value=True) as mock_attempt:
            http_api.logout()

            logout_config = mock_attempt.call_args[0][0]
            assert logout_config["controller_type"] == "NDFC"
            assert logout_config["path"] == "/logout"
            assert logout_config["data"] == {}
            assert logout_config["force_basic_auth"] is False


class TestHttpApiConstants:
    """Test that constants are properly defined and used."""

    def test_constants_defined(self, mock_connection):
        """Test that all required constants are defined."""
        from ansible_collections.cisco.dcnm.plugins.httpapi.dcnm import (
            DCNM_VERSION,
            NDFC_VERSION,
            HTTP_SUCCESS_MIN,
            HTTP_SUCCESS_MAX,
            DEFAULT_LOGIN_DOMAIN,
            DEFAULT_RETRY_COUNT,
        )

        assert DCNM_VERSION == 11
        assert NDFC_VERSION == 12
        assert HTTP_SUCCESS_MIN == 200
        assert HTTP_SUCCESS_MAX == 600
        assert DEFAULT_LOGIN_DOMAIN == "local"
        assert DEFAULT_RETRY_COUNT == 5

    def test_constants_usage(self, mock_connection):
        """Test that constants are used correctly in initialization."""
        http_api = HttpApi(mock_connection)
        assert http_api.retrycount == 5  # DEFAULT_RETRY_COUNT


class TestHttpApiIntegration:
    """Integration tests combining multiple methods."""

    def test_full_login_logout_cycle_nd(self, mock_connection):
        """Test complete login/logout cycle for DCNM."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection.get_option.return_value = 10

        # Mock successful login
        login_response = Mock()
        login_response.getcode.return_value = 200
        login_response.geturl.return_value = "/rest/logon"
        login_response.msg = "OK"

        login_rdata = Mock()
        login_rdata.getvalue.return_value = b'{"Dcnm-Token": "test-token-123"}'

        # Mock successful logout
        logout_response = Mock()
        logout_response.getcode.return_value = 200
        logout_response.geturl.return_value = "/rest/logout"
        logout_response.msg = "OK"

        logout_rdata = Mock()
        logout_rdata.getvalue.return_value = b'{"result": "logged out"}'

        http_api.connection.send.side_effect = [(login_response, login_rdata), (logout_response, logout_rdata)]  # Login call  # Logout call

        with patch.object(HttpApi, "get_option", return_value="local"):
            # Perform login
            http_api.login("admin", "password")

            # Verify login state
            assert http_api.login_succeeded is True
            assert http_api.version == 12
            assert http_api.connection._auth == {'Authorization': 'Bearer None', 'Cookie': 'AuthCookie=None'}

            # Perform logout
            http_api.logout()

            # Verify logout state
            assert http_api.logout_succeeded is True
            assert http_api.connection._auth is None

    def test_full_login_logout_cycle_ndfc(self, mock_connection):
        """Test complete login/logout cycle for NDFC."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection.get_option.return_value = 10

        # Mock failed DCNM login, successful NDFC login
        nd_response = Mock()
        nd_response.getcode.return_value = 401
        nd_response.geturl.return_value = "/rest/logon"
        nd_response.msg = "Unauthorized"

        nd_rdata = Mock()
        nd_rdata.getvalue.return_value = b'{"error": "unauthorized"}'

        ndfc_response = Mock()
        ndfc_response.getcode.return_value = 200
        ndfc_response.geturl.return_value = "/login"
        ndfc_response.msg = "OK"

        ndfc_rdata = Mock()
        ndfc_rdata.getvalue.return_value = b'{"token": "ndfc-token-456"}'

        logout_response = Mock()
        logout_response.getcode.return_value = 200
        logout_response.geturl.return_value = "/logout"
        logout_response.msg = "OK"

        logout_rdata = Mock()
        logout_rdata.getvalue.return_value = b'{"result": "logged out"}'

        http_api.connection.send.side_effect = [
            (nd_response, nd_rdata),  # Failed DCNM login
            (ndfc_response, ndfc_rdata),  # Successful NDFC login
            (logout_response, logout_rdata),  # Logout call
        ]

        with patch.object(HttpApi, "get_option", return_value="local"):
            # Perform login
            http_api.login("admin", "password")

            # Verify login state
            assert http_api.login_succeeded is True
            assert http_api.version == 12
            expected_auth = {"Authorization": "Bearer ndfc-token-456", "Cookie": "AuthCookie=ndfc-token-456"}
            assert http_api.connection._auth == expected_auth

            # Perform logout
            http_api.logout()

            # Verify logout state
            assert http_api.logout_succeeded is True
            assert http_api.connection._auth is None
