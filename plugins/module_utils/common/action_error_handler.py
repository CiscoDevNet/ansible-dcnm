"""
Class to provide error handling capabilities for Ansible action plugins
"""

#
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

from __future__ import absolute_import, division, print_function
from .exceptions import ActionError
import traceback
import json

__metaclass__ = type
__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Akshayanat Chengam Saravanan"


class ActionErrorHandler:
    """
    Centralized error handling and API response validation for NDFC operations.

    This class provides standardized error handling, exception management, and API
    response validation for all NDFC VRF operations. It ensures consistent error
    reporting and helps maintain robust operation flows across fabric types.

    Features:
    - Structured exception handling with context preservation
    - API response validation with detailed error reporting
    - Traceback management for debugging complex failures
    - Integration with logging system for error tracking
    - Consistent error response formatting for Ansible

    Args:
        logger (Logger): Logger instance for error reporting

    Attributes:
        logger (Logger): Associated logger for error message output
    """

    def __init__(self, logger):
        # Store logger reference for error reporting
        self.logger = logger

    def handle_failure(
        self, msg, changed=False
    ):
        """
        Handle failure scenarios with error logging and structured error responses.

        This method processes failure conditions by logging the error with message context,
        creating structured error responses suitable for Ansible module returns

        Failure Processing:
        - Logs error
        - Creates structured error response dictionary

        Args:
            msg (str): Failure message to report
            changed (bool): Whether any changes were made before failure

        Returns:
            dict: Structured error response with failed=True and error details

        """

        # Log the failure with full context
        self.logger.error(msg)

        # Create structured error response
        error_response = {
            "failed": True,
            "changed": changed,
            "msg": msg,
        }

        return error_response

    def handle_exception(
        self, e, operation="unknown", fabric=None, include_traceback=False
    ):
        """
        Handle exceptions with comprehensive logging and structured error responses.

        This method processes exceptions by extracting relevant information, logging
        the error with context, and creating structured error responses suitable for
        Ansible module returns. It supports optional traceback inclusion for debugging.

        Exception Processing:
        - Extracts exception type and message
        - Logs error with operation and fabric context
        - Creates structured error response dictionary
        - Optionally includes Python traceback for debugging
        - Raises ActionError with structured information

        Args:
            e (Exception): Exception object to handle
            operation (str): Operation context where exception occurred
            fabric (str, optional): Fabric context for the exception
            include_traceback (bool): Whether to include Python traceback

        Returns:
            dict: Structured error response with failed=True and error details

        Raises:
            ActionError: Always raises with structured error information
        """
        # Extract exception type and message for structured reporting
        error_type = type(e).__name__
        error_msg = str(e)

        # Build context string for error reporting
        context = f"Operation: {operation}"
        if fabric:
            context += f", Fabric: {fabric}"

        # Log the error with full context
        self.logger.error(f"{error_type} in {context}: {error_msg}")

        # Create structured error response for Ansible
        error_response = {
            "failed": True,
            "msg": error_msg,
            "error_type": error_type,
            "operation": operation
        }

        # Add fabric context if provided
        if fabric:
            error_response["fabric"] = fabric

        # Include traceback for debugging if requested
        if include_traceback:
            error_response["traceback"] = traceback.format_exc()
            self.logger.debug(f"Traceback: {traceback.format_exc()}")

        # Raise structured Ansible error
        raise ActionError(error_response)

    def validate_api_response(
        self, response, operation="API call", fabric=None
    ):
        """
        Validate NDFC API responses and handle various error conditions.

        This method performs comprehensive validation of NDFC API responses,
        checking for proper structure, success indicators, and data presence.
        It handles the common NDFC API response format and provides detailed
        error reporting for debugging failed API calls.

        Validation Checks:
        - Response existence and basic structure
        - Response format validation (dict expected)
        - Failed flag checking for operation failures
        - Response data structure validation
        - HTTP return code validation (expects 200)
        - Data payload presence validation

        NDFC API Response Format:
        {
            "failed": false,
            "response": {
                "RETURN_CODE": 200,
                "MESSAGE": "OK",
                "DATA": [...]
            }
        }

        Args:
            response (dict): NDFC API response to validate
            operation (str): Operation description for error reporting
            fabric (str, optional): Fabric context for error reporting

        Returns:
            dict: Validated response['response'] section with DATA
        """
        # Check for response existence
        if not response:
            raise ActionError(f"No response received for {operation}")

        # Validate response format
        if not isinstance(response, dict):
            raise ActionError(f"Invalid response format for {operation}: {response}")

        # Check for operation failure flag
        if response.get("failed"):
            error_msg = response.get("msg", "Unknown error")
            self.logger.error(f"API failure for {operation}: {json.dumps(response, indent=2)}")
            raise ActionError(f"{operation} failed: {error_msg}")

        # Validate response structure
        if not response.get("response"):
            self.logger.error(f"Empty response msg for {operation}: {json.dumps(response, indent=2)}")
            raise ActionError(f"Empty response msg received for {operation}")

        # Extract response data section
        resp = response.get("response")
        if not isinstance(resp, dict):
            raise ActionError(f"Invalid response format for {operation}: {resp}")

        # Validate HTTP return code
        return_code = resp.get("RETURN_CODE")
        if not return_code or return_code != 200:
            error_msg = response.get("MESSAGE", f"HTTP {return_code} error")
            self.logger.error(f"API error for {operation}: {json.dumps(resp, indent=2)}")
            raise ActionError(f"{operation} failed: {error_msg}")

        # Validate data payload presence
        if not resp.get("DATA"):
            self.logger.error(f"Empty response DATA for {operation}: {json.dumps(resp, indent=2)}")
            raise ActionError(f"Empty response DATA received for {operation}")

        # Return validated response data
        return resp
