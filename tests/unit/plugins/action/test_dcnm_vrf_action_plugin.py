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
Unit tests for DCNM VRF Action Plugin with Multisite Domain (MSD) support
"""

import pytest
import json
from unittest.mock import MagicMock, patch, Mock
from ansible.errors import AnsibleError
from ansible.utils.display import Display

# Import the action plugin
from ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf import ActionModule

# Import test fixtures and mocks
from .fixtures.dcnm_vrf_action_plugin_fixtures import DCNMVRFActionPluginFixtures
from .fixtures.dcnm_vrf_action_plugin_mocks import (
    MockActionBase, MockLogger, MockErrorHandler, MockDCNMVRFModule,
    mock_fabric_associations, mock_module_execution, mock_logger
)


class TestDCNMVRFActionPlugin:
    """Test class for DCNM VRF Action Plugin."""

    def setup_method(self):
        """Setup method run before each test."""
        self.fixtures = DCNMVRFActionPluginFixtures()
        self.action_base = MockActionBase()

        # Mock task and connection setup
        self.task_vars = {"inventory_hostname": "test_controller"}
        self.tmp = "/tmp/test"

        # Create action module instance with mocked base
        with patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionNetworkModule.__init__'):
            self.action_module = ActionModule(self.action_base.task, self.action_base.connection,
                                              self.action_base.play_context, self.action_base.loader,
                                              self.action_base.templar, self.action_base.shared_loader_obj)

        # Setup basic attributes
        self.action_module._task = MagicMock()
        self.action_module._task.args = {}
        self.action_module._connection = MagicMock()

    @pytest.fixture
    def mock_task_args_successful_merged(self):
        """Fixture for successful merged operation task args."""
        return self.fixtures.get_module_args_successful_merged()

    @pytest.fixture
    def mock_task_args_query(self):
        """Fixture for query operation task args."""
        return self.fixtures.get_module_args_query()

    @pytest.fixture
    def mock_task_args_invalid_vrf_id(self):
        """Fixture for invalid VRF ID task args."""
        return self.fixtures.get_module_args_invalid_vrf_id()

    @pytest.fixture
    def mock_task_args_child_fabric_direct(self):
        """Fixture for direct child fabric access task args."""
        return self.fixtures.get_module_args_child_fabric_direct()


class TestDCNMVRFActionPluginInitialization(TestDCNMVRFActionPlugin):
    """Test action plugin initialization."""

    def test_action_plugin_initialization(self):
        """Test that action plugin initializes correctly."""
        with patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionNetworkModule.__init__'):
            with patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.Logger') as mock_logger_class:
                with patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ErrorHandler') as mock_error_handler_class:
                    mock_logger_instance = MockLogger()
                    mock_logger_class.return_value = mock_logger_instance
                    mock_error_handler_class.return_value = MockErrorHandler(mock_logger_instance)

                    action_module = ActionModule(self.action_base.task, self.action_base.connection,
                                                 self.action_base.play_context, self.action_base.loader,
                                                 self.action_base.templar, self.action_base.shared_loader_obj)

                    # Verify initialization
                    assert action_module.logger is not None
                    assert action_module.error_handler is not None

                    # Verify logger was called with initialization message
                    mock_logger_class.assert_called_once_with("DCNM_VRF_ActionPlugin")


class TestDCNMVRFActionPluginFabricDetection(TestDCNMVRFActionPlugin):
    """Test fabric type detection functionality."""

    def test_detect_multisite_parent_fabric_type(self):
        """Test detection of Multisite Parent fabric type."""
        fabric_data = {
            self.fixtures.PARENT_FABRIC: {
                "fabricType": "MSD",
                "fabricState": "msd"
            }
        }

        result = self.action_module.detect_fabric_type(self.fixtures.PARENT_FABRIC, fabric_data)
        assert result == "multisite_parent"

    def test_detect_multisite_child_fabric_type(self):
        """Test detection of Multisite Child fabric type."""
        fabric_data = {
            self.fixtures.CHILD_FABRIC: {
                "fabricType": "Switch_Fabric",
                "fabricState": "member"
            }
        }

        result = self.action_module.detect_fabric_type(self.fixtures.CHILD_FABRIC, fabric_data)
        assert result == "multisite_child"

    def test_detect_standalone_fabric_type(self):
        """Test detection of Standalone fabric type."""
        fabric_data = {
            "STANDALONE_FABRIC": {
                "fabricType": "Switch_Fabric",
                "fabricState": "standalone"
            }
        }

        result = self.action_module.detect_fabric_type("STANDALONE_FABRIC", fabric_data)
        assert result == "standalone"

    def test_detect_fabric_type_nonexistent_fabric(self):
        """Test fabric type detection with nonexistent fabric."""
        fabric_data = {
            self.fixtures.PARENT_FABRIC: {
                "fabricType": "MSD",
                "fabricState": "msd"
            }
        }

        with pytest.raises(AnsibleError) as exc_info:
            self.action_module.detect_fabric_type("NONEXISTENT_FABRIC", fabric_data)

        assert "not found in NDFC" in str(exc_info.value)


class TestDCNMVRFActionPluginValidation(TestDCNMVRFActionPlugin):
    """Test validation functionality."""

    def test_validate_child_parent_fabric_relationship_valid(self):
        """Test valid child-parent fabric relationship validation."""
        fabric_data = self.fixtures.get_fabric_associations_data()
        fabric_dict = {fab["fabricName"]: fab for fab in fabric_data}

        result = self.action_module.validate_child_parent_fabric(
            self.fixtures.CHILD_FABRIC,
            self.fixtures.PARENT_FABRIC,
            fabric_dict
        )

        assert result is True

    def test_validate_child_parent_fabric_relationship_invalid_child(self):
        """Test validation with invalid child fabric."""
        fabric_data = self.fixtures.get_fabric_associations_data()
        fabric_dict = {fab["fabricName"]: fab for fab in fabric_data}

        with pytest.raises(AnsibleError) as exc_info:
            self.action_module.validate_child_parent_fabric(
                "NONEXISTENT_CHILD",
                self.fixtures.PARENT_FABRIC,
                fabric_dict
            )

        assert "not found in NDFC" in str(exc_info.value)

    def test_validate_child_parent_fabric_relationship_not_child_type(self):
        """Test validation with fabric that is not child type."""
        fabric_data = self.fixtures.get_fabric_associations_data()
        fabric_dict = {fab["fabricName"]: fab for fab in fabric_data}

        result = self.action_module.validate_child_parent_fabric(
            "STANDALONE_FABRIC",
            self.fixtures.PARENT_FABRIC,
            fabric_dict
        )

        assert result is False


class TestDCNMVRFActionPluginWorkflows(TestDCNMVRFActionPlugin):
    """Test workflow execution."""

    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.execute_module_with_args')
    def test_query_workflow_success(self, mock_execute_module, mock_fabric_associations, mock_task_args_query):
        """Test successful query workflow."""
        # Setup mocks
        mock_fabric_associations.return_value = {fab["fabricName"]: fab for fab in self.fixtures.get_fabric_associations_data()}
        mock_execute_module.return_value = self.fixtures.get_fabric_associations_query_response()

        # Setup task args
        self.action_module._task.args = mock_task_args_query

        # Execute
        result = self.action_module.run(self.tmp, self.task_vars)

        # Verify
        assert result["changed"] is False
        assert result["failed"] is False
        assert "workflow" in result
        assert "response" in result

    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.execute_module_with_args')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.wait_for_vrf_ready')
    def test_merged_workflow_multisite_parent_success(self, mock_wait_vrf, mock_execute_module,
                                                      mock_fabric_associations, mock_task_args_successful_merged):
        """Test successful merged workflow on multisite parent."""
        # Setup mocks
        mock_fabric_associations.return_value = {fab["fabricName"]: fab for fab in self.fixtures.get_fabric_associations_data()}
        mock_execute_module.return_value = self.fixtures.get_merged_parent_with_child_failure()
        mock_wait_vrf.return_value = None

        # Setup task args
        self.action_module._task.args = mock_task_args_successful_merged

        # Execute
        result = self.action_module.run(self.tmp, self.task_vars)

        # Verify
        assert result["fabric_type"] == "multisite_parent"
        assert "parent_fabric" in result
        assert "child_fabrics" in result

    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_child_fabric_direct_access_blocked(self, mock_fabric_associations, mock_task_args_child_fabric_direct):
        """Test that direct access to child fabric is properly blocked."""
        # Setup mocks
        mock_fabric_associations.return_value = {fab["fabricName"]: fab for fab in self.fixtures.get_fabric_associations_data()}

        # Setup task args for child fabric direct access
        self.action_module._task.args = mock_task_args_child_fabric_direct

        # Execute
        result = self.action_module.run(self.tmp, self.task_vars)

        # Verify
        assert result["failed"] is True
        assert result["fabric_type"] == "multisite_child"
        assert "not permitted" in result["msg"]
        assert "Parent fabric" in result["msg"]


class TestDCNMVRFActionPluginErrorHandling(TestDCNMVRFActionPlugin):
    """Test error handling scenarios."""

    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.execute_module_with_args')
    def test_invalid_vrf_id_validation_error(self, mock_execute_module, mock_fabric_associations,
                                            mock_task_args_invalid_vrf_id):
        """Test validation error for invalid VRF ID."""
        # Setup mocks
        mock_fabric_associations.return_value = {fab["fabricName"]: fab for fab in self.fixtures.get_fabric_associations_data()}
        mock_execute_module.return_value = self.fixtures.get_configuration_validation_failures()["invalid_vrf_id"]

        # Setup task args
        self.action_module._task.args = mock_task_args_invalid_vrf_id

        # Execute
        result = self.action_module.run(self.tmp, self.task_vars)

        # Verify
        assert result["failed"] is True
        assert "exceeds the allowed range" in result["msg"]

    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_nonexistent_fabric_error(self, mock_fabric_associations):
        """Test error handling for nonexistent fabric."""
        # Setup mocks
        mock_fabric_associations.return_value = {fab["fabricName"]: fab for fab in self.fixtures.get_fabric_associations_data()}

        # Setup task args with nonexistent fabric
        self.action_module._task.args = {
            "fabric": "NONEXISTENT_FABRIC",
            "state": "query",
            "config": []
        }

        # Execute and verify error
        with pytest.raises(AnsibleError) as exc_info:
            self.action_module.run(self.tmp, self.task_vars)

        assert "not found in NDFC" in str(exc_info.value)

    def test_empty_vrf_name_validation_error(self):
        """Test validation error for empty VRF name."""
        # This would be caught during module parameter validation
        # Test the error pattern from fixtures
        error_response = self.fixtures.get_configuration_validation_failures()["empty_vrf_name"]

        assert error_response["failed"] is True
        assert "missing mandatory key vrf_name" in error_response["msg"]

    def test_duplicate_vrf_id_api_error(self):
        """Test API error handling for duplicate VRF ID."""
        error_response = self.fixtures.get_configuration_validation_failures()["duplicate_vrf_id"]

        assert error_response["failed"] is True
        assert error_response["msg"]["RETURN_CODE"] == 400
        assert "already exists" in error_response["msg"]["DATA"]["message"]


class TestDCNMVRFActionPluginHelperMethods(TestDCNMVRFActionPlugin):
    """Test helper methods and utilities."""

    def test_create_child_task(self):
        """Test child task creation."""
        parent_vrf = {
            "vrf_name": "TestVRF_Parent",
            "vrf_id": 50001,
            "vlan_id": 2001
        }

        child_config = {"fabric": self.fixtures.CHILD_FABRIC}
        parent_module_args = self.fixtures.get_module_args_successful_merged()
        child_tasks_dict = {}

        # Execute
        self.action_module.create_child_task(parent_vrf, child_config, parent_module_args, child_tasks_dict)

        # Verify child task was created
        assert self.fixtures.CHILD_FABRIC in child_tasks_dict
        child_task = child_tasks_dict[self.fixtures.CHILD_FABRIC]
        assert child_task["fabric"] == self.fixtures.CHILD_FABRIC
        assert child_task["config"][0]["vrf_name"] == "TestVRF_Parent"

    def test_create_structured_results(self):
        """Test structured results creation."""
        parent_result = {"changed": True, "response": []}
        child_results = [{
            "fabric": self.fixtures.CHILD_FABRIC,
            "changed": False,
            "failed": True
        }]

        result = self.action_module.create_structured_results(
            parent_result, child_results, self.fixtures.PARENT_FABRIC
        )

        # Verify structure
        assert "parent_fabric" in result
        assert "child_fabrics" in result
        assert "fabric_type" in result
        assert result["fabric_type"] == "multisite_parent"


class TestDCNMVRFActionPluginLogger(TestDCNMVRFActionPlugin):
    """Test logging functionality."""

    def test_logger_creation_and_usage(self):
        """Test logger creation and message logging."""
        mock_logger = MockLogger("Test_Logger")

        # Test different log levels
        mock_logger.debug("Debug message", "TEST_FABRIC", "test_operation")
        mock_logger.info("Info message", "TEST_FABRIC", "test_operation")
        mock_logger.warning("Warning message", "TEST_FABRIC", "test_operation")
        mock_logger.error("Error message", "TEST_FABRIC", "test_operation")

        # Verify messages were logged
        assert len(mock_logger.logged_messages) == 4

        # Verify message structure
        debug_msg = mock_logger.logged_messages[0]
        assert debug_msg["level"] == "debug"
        assert debug_msg["message"] == "Debug message"
        assert debug_msg["fabric"] == "TEST_FABRIC"
        assert debug_msg["operation"] == "test_operation"


class TestDCNMVRFActionPluginErrorHandler(TestDCNMVRFActionPlugin):
    """Test error handler functionality."""

    def test_error_handler_exception_handling(self):
        """Test error handler exception processing."""
        mock_logger = MockLogger()
        error_handler = MockErrorHandler(mock_logger)

        test_exception = ValueError("Test error message")
        result = error_handler.handle_exception(
            test_exception,
            operation="test_operation",
        )

        # Verify error response structure
        assert result["failed"] is True
        assert result["msg"] == "Test error message"
        assert result["error_type"] == "ValueError"
        assert result["operation"] == "test_operation"
        assert result["fabric"] == "TEST_FABRIC"

        # Verify exception was captured
        assert len(error_handler.handled_exceptions) == 1
        handled_exc = error_handler.handled_exceptions[0]
        assert handled_exc["exception"] == test_exception
        assert handled_exc["operation"] == "test_operation"
        assert handled_exc["fabric"] == "TEST_FABRIC"

    def test_error_handler_api_response_validation_success(self):
        """Test successful API response validation."""
        mock_logger = MockLogger()
        error_handler = MockErrorHandler(mock_logger)

        valid_response = {
            "failed": False,
            "response": {
                "RETURN_CODE": 200,
                "MESSAGE": "OK",
                "DATA": {"result": "success"}
            }
        }

        result = error_handler.validate_api_response(valid_response)
        assert result == valid_response["response"]

    def test_error_handler_api_response_validation_failure(self):
        """Test API response validation with invalid response."""
        mock_logger = MockLogger()
        error_handler = MockErrorHandler(mock_logger)

        invalid_response = {"failed": True}

        with pytest.raises(ValueError):
            error_handler.validate_api_response(invalid_response)


# Integration tests combining multiple components
class TestDCNMVRFActionPluginIntegration(TestDCNMVRFActionPlugin):
    """Integration tests for complete workflows."""

    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.execute_module_with_args')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.wait_for_vrf_ready')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.execute_child_task')
    def test_full_multisite_workflow_with_child_processing(self, mock_execute_child_task, mock_wait_vrf,
                                                           mock_execute_module, mock_fabric_associations):
        """Test complete multisite workflow with child fabric processing."""
        # Setup mocks
        mock_fabric_associations.return_value = {fab["fabricName"]: fab for fab in self.fixtures.get_fabric_associations_data()}

        # Mock successful parent execution
        parent_response = {
            "changed": True,
            "failed": False,
            "fabric_type": "multisite_parent",
            "parent_fabric": {
                "changed": True,
                "response": [{"DATA": {"VRF Id": 50101, "VRF Name": "TestVRF_Success"}}]
            },
            "child_fabrics": [
                {
                    "changed": True,
                    "fabric": self.fixtures.CHILD_FABRIC,
                    "response": [{"DATA": {"result": "success"}}]
                }
            ],
            "response": [{"DATA": {"VRF Id": 50101, "VRF Name": "TestVRF_Success"}}]
        }
        mock_execute_module.return_value = parent_response

        # Mock child task execution
        child_response = {
            "changed": True,
            "fabric": self.fixtures.CHILD_FABRIC,
            "response": [{"DATA": {"result": "success"}}]
        }
        mock_execute_child_task.return_value = child_response

        mock_wait_vrf.return_value = None

        # Setup task args with child fabric configuration
        task_args = self.fixtures.get_module_args_successful_merged()
        task_args["config"][0]["child_fabrics"] = [{"fabric": self.fixtures.CHILD_FABRIC}]
        self.action_module._task.args = task_args

        # Execute
        result = self.action_module.run(self.tmp, self.task_vars)

        # Verify complete workflow
        assert result["fabric_type"] == "multisite_parent"
        assert "parent_fabric" in result
        assert "child_fabrics" in result
        assert len(result["child_fabrics"]) == 1
        assert result["child_fabrics"][0]["fabric"] == self.fixtures.CHILD_FABRIC


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
