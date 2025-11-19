"""
Class to provide logging capabilities for Ansible action plugins
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
from datetime import datetime

__metaclass__ = type
__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Akshayanat Chengam Saravanan"


class ActionLogger:
    """
    Centralized logging system for NDFC VRF action plugin operations.

    This class provides structured logging with context awareness for fabric operations.
    It formats log messages with timestamps, fabric context, and operation context to
    facilitate debugging and monitoring of VRF operations across different fabric types.

    Features:
    - Contextual logging with fabric and operation information
    - Multiple log levels mapped to Ansible display verbosity
    - Consistent message formatting across all operations
    - Timestamp tracking for performance analysis

    Args:
        name (str): Logger instance name for identification

    Attributes:
        name (str): Logger identifier used in message formatting
        start_time (datetime): Initialization timestamp for duration calculations
    """

    def __init__(self, name="NDFC_VRF_ActionPlugin", display=None):
        # Set logger identification name
        self.name = name
        # Record initialization time for performance tracking
        self.start_time = datetime.now()
        self.display = display

    def log(self, level, message, fabric=None, operation=None):
        """
        Core logging method that formats and outputs messages with context.

        This method creates structured log messages with timestamps and contextual
        information, then routes them to appropriate Ansible display methods based
        on log level severity.

        Message Format:
        - YYYY-MM-DD HH:MM:SS [Logger][Fabric][Operation] LEVEL: message

        Args:
            level (str): Log level (debug, info, warning, error)
            message (str): Log message content
            fabric (str, optional): Fabric context for the log message
            operation (str, optional): Operation context for the log message

        Display Routing:
        - debug: display.vvv() - Most verbose, debug information
        - info: display.vv() - Informational messages
        - warning: display.warning() - Warning messages
        - error: display.error() - Error messages
        - default: display.v() - Standard verbosity
        """
        # Generate timestamp for log entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Build context string starting with logger name
        context = f"[{self.name}]"

        # Add fabric context if provided
        if fabric:
            context += f"[{fabric}]"
        # Add operation context if provided
        if operation:
            context += f"[{operation}]"

        # Format complete log message
        log_msg = f"{timestamp} {context} {level.upper()}: {message}"

        # Route to appropriate Ansible display method based on level
        if level == "debug":
            self.display.vvv(log_msg)  # Highest verbosity for debugging
        elif level == "info":
            self.display.vv(log_msg)   # Medium verbosity for information
        elif level == "warning":
            self.display.warning(log_msg)  # Warning level
        elif level == "error":
            self.display.error(log_msg)    # Error level
        else:
            self.display.v(log_msg)    # Default verbosity

    def debug(self, message, fabric=None, operation=None):
        """Log debug level message with optional context."""
        self.log("debug", message, fabric, operation)

    def info(self, message, fabric=None, operation=None):
        """Log info level message with optional context."""
        self.log("info", message, fabric, operation)

    def warning(self, message, fabric=None, operation=None):
        """Log warning level message with optional context."""
        self.log("warning", message, fabric, operation)

    def error(self, message, fabric=None, operation=None):
        """Log error level message with optional context."""
        self.log("error", message, fabric, operation)
