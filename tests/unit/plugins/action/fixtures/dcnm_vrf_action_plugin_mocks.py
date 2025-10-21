"""
Mock classes and utilities for DCNM VRF Action Plugin testing
"""

from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
from .dcnm_vrf_action_plugin_fixtures import DCNMVRFActionPluginFixtures


class MockDCNMRestResponse:
    """Mock class for DCNM REST API responses."""

    def __init__(self, data: Dict[str, Any], failed: bool = False):
        self.data = data
        self.failed = failed

    def get_response(self) -> Dict[str, Any]:
        """Return mock response in DCNM format."""
        return {
            "failed": self.failed,
            "response": {
                "RETURN_CODE": 400 if self.failed else 200,
                "MESSAGE": "Bad Request" if self.failed else "OK",
                "DATA": self.data if not self.failed else {"Error": "Mock error"}
            }
        }


class MockActionBase:
    """Mock base class for action modules."""

    def __init__(self):
        self.task = MagicMock()
        self.connection = MagicMock()
        self.play_context = MagicMock()
        self.loader = MagicMock()
        self.templar = MagicMock()
        self.shared_loader_obj = MagicMock()

    def execute_module(self, module_name=None, module_args=None, task_vars=None, tmp=None):
        """Mock module execution with predefined responses."""
        fixtures = DCNMVRFActionPluginFixtures()

        # Determine response based on module args
        if module_args:
            fabric = module_args.get("fabric", "")
            state = module_args.get("state", "")
            config = module_args.get("config", [])

            # Query operation
            if state == "query":
                return fixtures.get_fabric_associations_query_response()

            # Child fabric direct access
            if fabric == DCNMVRFActionPluginFixtures.CHILD_FABRIC:
                return fixtures.get_fabric_related_failures()["child_direct_merged"]

            # Invalid VRF ID
            if config and config[0].get("vrf_id") == 99999999:
                return fixtures.get_configuration_validation_failures()["invalid_vrf_id"]

            # Success case
            return fixtures.get_merged_parent_with_child_failure()

        # Default success response
        return {"changed": False, "failed": False}


class MockDCNMVRFModule:
    """Mock DCNM VRF module for testing."""

    @staticmethod
    def get_mock_fabric_details():
        """Returns mock fabric details data."""
        return {
            DCNMVRFActionPluginFixtures.PARENT_FABRIC: {
                "fabricType": "MSD",
                "fabricState": "msd",
                "id": 12345
            },
            DCNMVRFActionPluginFixtures.CHILD_FABRIC: {
                "fabricType": "Switch_Fabric",
                "fabricState": "member",
                "id": 12346
            },
            "STANDALONE_FABRIC": {
                "fabricType": "Switch_Fabric",
                "fabricState": "standalone",
                "id": 12347
            }
        }

    @staticmethod
    def get_mock_switch_details():
        """Returns mock switch details data."""
        return {
            DCNMVRFActionPluginFixtures.SWITCH_IP: {
                "serialNumber": DCNMVRFActionPluginFixtures.SWITCH_SERIAL,
                "switchName": DCNMVRFActionPluginFixtures.SWITCH_NAME,
                "fabricName": DCNMVRFActionPluginFixtures.PARENT_FABRIC,
                "role": "leaf"
            }
        }


class MockLogger:
    """Mock logger for testing."""

    def __init__(self, name="Mock_Logger"):
        self.name = name
        self.logged_messages = []

    def log(self, level, message, fabric=None, operation=None):
        """Mock log method that captures messages."""
        self.logged_messages.append({
            "level": level,
            "message": message,
            "fabric": fabric,
            "operation": operation
        })

    def debug(self, message, fabric=None, operation=None):
        self.log("debug", message, fabric, operation)

    def info(self, message, fabric=None, operation=None):
        self.log("info", message, fabric, operation)

    def warning(self, message, fabric=None, operation=None):
        self.log("warning", message, fabric, operation)

    def error(self, message, fabric=None, operation=None):
        self.log("error", message, fabric, operation)


class MockErrorHandler:
    """Mock error handler for testing."""

    def __init__(self, logger):
        self.logger = logger
        self.handled_exceptions = []

    def handle_exception(self, e, operation="unknown", fabric=None, include_traceback=False):
        """Mock exception handler that captures exceptions."""
        self.handled_exceptions.append({
            "exception": e,
            "operation": operation,
            "fabric": fabric,
            "include_traceback": include_traceback
        })

        # Return mock error response instead of raising
        error_response = {
            "failed": True,
            "msg": str(e),
            "error_type": type(e).__name__,
            "operation": operation
        }

        if fabric:
            error_response["fabric"] = fabric

        return error_response

    def validate_api_response(self, response, operation="API call", fabric=None):
        """Mock API response validation."""
        if not response or response.get("failed"):
            raise ValueError("Mock API response validation failed")

        return response.get("response", {})


# Mock patch decorators for common test scenarios
def mock_fabric_associations(fabric_data=None):
    """Decorator to mock fabric associations API call."""
    if fabric_data is None:
        fabric_data = DCNMVRFActionPluginFixtures.get_fabric_associations_data()

    def mock_rest_call(*args, **kwargs):
        return MockDCNMRestResponse(fabric_data).get_response()

    return patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations',
                 return_value=fabric_data)


def mock_module_execution(response_data=None):
    """Decorator to mock module execution."""
    if response_data is None:
        response_data = {"changed": False, "failed": False}

    return patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.execute_module_with_args',
                 return_value=response_data)


def mock_logger():
    """Decorator to mock logger."""
    return patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.Logger',
                 return_value=MockLogger())


def mock_error_handler():
    """Decorator to mock error handler."""
    mock_logger_instance = MockLogger()
    return patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ErrorHandler',
                 return_value=MockErrorHandler(mock_logger_instance))
