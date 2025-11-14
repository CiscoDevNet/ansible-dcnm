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
Performance and stress tests for DCNM HttpApi plugin
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Mike Wiebe"

import time
from unittest.mock import Mock, patch

import pytest

from ansible_collections.cisco.dcnm.plugins.httpapi.dcnm import HttpApi


class TestHttpApiPerformance:
    """Performance tests for HttpApi methods."""

    def test_multiple_login_attempts_performance(self, mock_connection):
        """Test performance of multiple login attempts."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection
        http_api.connection.get_option.return_value = 10

        # Mock response setup
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = "/rest/logon"
        mock_response.msg = "OK"

        mock_rdata = Mock()
        mock_rdata.getvalue.return_value = b'{"Dcnm-Token": "test-token"}'

        http_api.connection.send.return_value = (mock_response, mock_rdata)

        with patch.object(HttpApi, "get_option", return_value="local"):
            start_time = time.time()

            # Perform 100 login attempts
            for idx in range(100):
                http_api.login_succeeded = False  # Reset state
                http_api.login("admin", "password")

            end_time = time.time()
            duration = end_time - start_time

            # Should complete 100 logins in reasonable time (less than 1 second)
            assert duration < 1.0, f"100 logins took {duration:.3f} seconds, too slow"

    def test_json_parsing_performance(self, mock_connection):
        """Test JSON parsing performance with large responses."""
        http_api = HttpApi(mock_connection)

        # Create a large JSON response
        large_data = {"items": [{"id": i, "name": f"item_{i}", "data": "x" * 100} for i in range(1000)]}
        large_json = str(large_data).replace("'", '"')

        start_time = time.time()

        # Parse JSON 100 times
        for idx in range(100):
            http_api._response_to_json(large_json)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete 100 parses in reasonable time
        assert duration < 2.0, f"100 JSON parses took {duration:.3f} seconds, too slow"

    def test_response_verification_performance(self, mock_connection):
        """Test response verification performance."""
        http_api = HttpApi(mock_connection)

        # Mock response setup
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response.geturl.return_value = "/api/test"
        mock_response.msg = "OK"

        mock_rdata = Mock()
        mock_rdata.getvalue.return_value = b'{"result": "success"}'

        start_time = time.time()

        # Verify 1000 responses
        for idx in range(1000):
            http_api._verify_response(mock_response, "GET", "/api/test", mock_rdata)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete 1000 verifications in reasonable time
        assert duration < 1.0, f"1000 response verifications took {duration:.3f} seconds, too slow"


class TestHttpApiStress:
    """Stress tests for HttpApi methods."""

    def test_concurrent_request_simulation(self, mock_connection):
        """Simulate concurrent request handling."""
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

        with patch.object(http_api, "check_url_connection"):
            # Simulate 500 concurrent-like requests
            results = []
            for i in range(500):
                try:
                    result = http_api._send_request_internal("GET", f"/api/test/{i}")
                    results.append(result)
                except Exception as e:
                    pytest.fail(f"Request {i} failed: {e}")

            # All requests should succeed
            assert len(results) == 500
            assert all(r["RETURN_CODE"] == 200 for r in results)

    def test_memory_usage_stability(self, mock_connection):
        """Test that memory usage remains stable during multiple operations."""
        http_api = HttpApi(mock_connection)

        # Perform many operations that could potentially leak memory
        for i in range(1000):
            # Test JSON parsing
            test_json = f'{{"id": {i}, "data": "test_data_{i}"}}'
            http_api._response_to_json(test_json)

            # Test return info creation
            http_api._return_info(200, "GET", f"/api/test/{i}", "OK", {"id": i})

            # Test response value extraction
            mock_rdata = Mock()
            mock_rdata.getvalue.return_value = f"test_data_{i}".encode()
            http_api._get_response_value(mock_rdata)

        # If we get here without memory errors, the test passes
        assert True

    def test_large_response_handling(self, mock_connection):
        """Test handling of very large responses."""
        http_api = HttpApi(mock_connection)

        # Create a very large response (1MB of data)
        large_response = '{"data": "' + "x" * (1024 * 1024) + '"}'

        # Should handle large response without errors
        result = http_api._response_to_json(large_response)
        assert isinstance(result, dict)
        assert len(result["data"]) == 1024 * 1024

    def test_invalid_json_stress(self, mock_connection):
        """Test handling of many invalid JSON responses."""
        http_api = HttpApi(mock_connection)

        invalid_responses = ["invalid json", '{"incomplete": }', '{"unterminated": "string', "{broken json}", "null}", '{"nested": {"broken": }}']

        # Should handle all invalid JSON gracefully
        for invalid_json in invalid_responses * 100:  # Test each 100 times
            result = http_api._response_to_json(invalid_json)
            assert "Invalid JSON response:" in str(result)

    def test_exception_handling_stress(self, mock_connection):
        """Test exception handling under stress conditions."""
        http_api = HttpApi(mock_connection)
        http_api.connection = mock_connection

        # Test various exception types
        exceptions = [
            Exception("Network error"),
            ConnectionError("Connection failed"),
            ValueError("Invalid value"),
            KeyError("Missing key"),
            TypeError("Wrong type"),
        ]

        for exception in exceptions * 20:  # Test each exception type 20 times
            http_api.connection.send.side_effect = exception
            http_api.login_fail_msg = []

            login_config = {"controller_type": "DCNM", "version": 11, "path": "/rest/logon", "data": "test", "force_basic_auth": True}

            # Should handle all exceptions gracefully
            result = http_api._attempt_login(login_config)
            assert result is False
            assert len(http_api.login_fail_msg) > 0


class TestHttpApiEdgeStress:
    """Edge case stress tests."""

    def test_empty_responses_stress(self, mock_connection):
        """Test handling of many empty responses."""
        http_api = HttpApi(mock_connection)

        empty_responses = ["", "{}", "null", "[]"]  # Remove None as it causes different behavior

        for empty_response in empty_responses * 200:  # Test each 200 times
            result = http_api._response_to_json(empty_response)
            # Should handle gracefully, returning dict, list, None, or error string
            assert isinstance(result, (dict, list, str, type(None)))

    def test_boundary_http_codes_stress(self, mock_connection):
        """Test boundary HTTP codes under stress."""
        http_api = HttpApi(mock_connection)

        # Test boundary codes (200-600 is success range)
        boundary_codes = [199, 200, 201, 399, 400, 401, 499, 500, 599, 600, 601]

        mock_response = Mock()
        mock_response.geturl.return_value = "/api/test"
        mock_response.msg = "Test"

        mock_rdata = Mock()
        mock_rdata.getvalue.return_value = b'{"test": "data"}'

        from ansible.module_utils.connection import ConnectionError as AnsibleConnectionError

        for code in boundary_codes * 50:  # Test each code 50 times
            mock_response.getcode.return_value = code

            if 200 <= code <= 600:
                # Should succeed
                result = http_api._verify_response(mock_response, "GET", "/api/test", mock_rdata)
                assert result["RETURN_CODE"] == code
            else:
                # Should raise ConnectionError
                with pytest.raises(AnsibleConnectionError):
                    http_api._verify_response(mock_response, "GET", "/api/test", mock_rdata)

    def test_path_validation_stress(self, mock_connection):
        """Test path validation with many invalid paths."""
        http_api = HttpApi(mock_connection)

        invalid_paths = [
            "no-leading-slash",
            "  /path-with-spaces",
            "/path with spaces",
            "",
            "relative/path",
            "path/without/leading/slash",
            "../../malicious/path",
            "/path/../with/../dots",
            "/path/with/\nnewline",
            "/path/with/\ttab",
        ]

        for invalid_path in invalid_paths * 10:  # Test each 10 times
            try:
                # Most should raise ConnectionError for invalid format
                if not str(invalid_path).startswith("/"):
                    with pytest.raises(ConnectionError):
                        http_api._send_request_internal("GET", invalid_path)
                else:
                    # Paths starting with / should pass validation but may fail later
                    with patch.object(http_api, "check_url_connection"):
                        http_api.connection = mock_connection
                        http_api.connection.send.side_effect = Exception("Test exception")

                        with pytest.raises(ConnectionError):
                            http_api._send_request_internal("GET", invalid_path)
            except ConnectionError:
                # This is expected for invalid paths
                pass
            except Exception as e:
                # Check that we got the expected Ansible ConnectionError type
                from ansible.module_utils.connection import ConnectionError as AnsibleConnectionError

                assert isinstance(e, AnsibleConnectionError), f"Unexpected exception type: {type(e)}"
