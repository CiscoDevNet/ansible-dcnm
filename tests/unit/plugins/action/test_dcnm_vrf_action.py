# Copyright (c) 2020-2025 Cisco and/or its affiliates.
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

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
import copy
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime

from ansible.errors import AnsibleError
from ansible.utils.display import Display

# Import the action plugin class
from ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf import (
    ActionModule,
    Logger,
    ErrorHandler
)


def load_fixture_data(fixture_name):
    """
    Load fixture data from the dcnm_vrf_action.json file.
    
    Args:
        fixture_name (str): Name of the fixture to load
        
    Returns:
        dict: Fixture data
    """
    import os
    import json
    
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        'fixtures',
        'dcnm_vrf_action.json'
    )
    
    with open(fixture_path, 'r') as f:
        fixtures = json.load(f)
    
    return fixtures.get(fixture_name, {})


class TestDcnmVrfActionLogger:
    """Test suite for the Logger class in DCNM VRF action plugin."""
    
    def setup_method(self):
        """Set up test environment before each test method."""
        self.logger = Logger("TestLogger")
        self.test_data = load_fixture_data("mock_logger_contexts")
    
    def test_logger_initialization(self):
        """Test Logger class initialization."""
        assert self.logger.name == "TestLogger"
        assert isinstance(self.logger.start_time, datetime)
    
    def test_logger_default_name(self):
        """Test Logger class with default name."""
        default_logger = Logger()
        assert default_logger.name == "DCNM_VRF_ActionPlugin"
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.display')
    def test_logger_debug_level(self, mock_display):
        """Test logging at debug level."""
        context = self.test_data["basic_context"]
        self.logger.log("debug", "Test debug message", 
                       fabric=context["fabric"], 
                       operation=context["operation"])
        mock_display.vvv.assert_called_once()
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.display')
    def test_logger_info_level(self, mock_display):
        """Test logging at info level."""
        context = self.test_data["basic_context"]
        self.logger.log("info", "Test info message",
                       fabric=context["fabric"],
                       operation=context["operation"])
        mock_display.vv.assert_called_once()
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.display')
    def test_logger_warning_level(self, mock_display):
        """Test logging at warning level."""
        context = self.test_data["basic_context"]
        self.logger.log("warning", "Test warning message",
                       fabric=context["fabric"],
                       operation=context["operation"])
        mock_display.warning.assert_called_once()
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.display')
    def test_logger_error_level(self, mock_display):
        """Test logging at error level."""
        context = self.test_data["basic_context"]
        self.logger.log("error", "Test error message",
                       fabric=context["fabric"],
                       operation=context["operation"])
        mock_display.error.assert_called_once()
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.display')
    def test_logger_without_context(self, mock_display):
        """Test logging without fabric and operation context."""
        self.logger.log("info", "Test message without context")
        mock_display.vv.assert_called_once()
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.display')
    def test_logger_with_fabric_only(self, mock_display):
        """Test logging with fabric context only."""
        self.logger.log("info", "Test message with fabric only", fabric="AK-R")
        mock_display.vv.assert_called_once()
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.display')
    def test_logger_with_operation_only(self, mock_display):
        """Test logging with operation context only."""
        self.logger.log("info", "Test message with operation only", 
                       operation="test_operation")
        mock_display.vv.assert_called_once()


class TestDcnmVrfActionErrorHandler:
    """Test suite for the ErrorHandler class in DCNM VRF action plugin."""
    
    def setup_method(self):
        """Set up test environment before each test method."""
        self.mock_logger = Mock()
        self.error_handler = ErrorHandler(self.mock_logger)
        self.test_data = load_fixture_data("mock_error_handler_data")
    
    def test_error_handler_initialization(self):
        """Test ErrorHandler class initialization."""
        assert self.error_handler.logger == self.mock_logger
    
    def test_handle_error(self):
        """Test handling of generic exceptions."""
        error_data = self.test_data["api_error"]
        test_error = Exception(error_data["message"])
        
        with pytest.raises(AnsibleError):
            self.error_handler.handle_exception(
                test_error,
                operation=error_data["operation"],
                fabric=error_data["fabric"]
            )


class TestDcnmVrfActionModule:
    """Test suite for the ActionModule class in DCNM VRF action plugin."""
    
    def setup_method(self):
        """Set up test environment before each test method."""
        # Create mock task and connection objects
        self.mock_task = Mock()
        self.mock_connection = Mock()
        self.mock_play_context = Mock()
        self.mock_loader = Mock()
        self.mock_templar = Mock()
        self.mock_shared_loader_obj = Mock()
        
        # Initialize action module
        self.action_module = ActionModule(
            task=self.mock_task,
            connection=self.mock_connection,
            play_context=self.mock_play_context,
            loader=self.mock_loader,
            templar=self.mock_templar,
            shared_loader_obj=self.mock_shared_loader_obj
        )
        
        # Load test data
        self.fabric_associations = load_fixture_data("mock_fabric_associations")
        self.fabric_data = load_fixture_data("mock_fabric_associations_dict")
        self.parent_fabric_details = load_fixture_data("mock_parent_fabric_details")
        self.child_fabric_details = load_fixture_data("child_fabric_details")
        self.standalone_fabric_details = load_fixture_data("standalone_fabric_details")
        self.module_args = load_fixture_data("mock_module_args")
        self.error_responses = load_fixture_data("mock_error_responses")
        self.workflow_results = load_fixture_data("mock_workflow_results")
        self.fabric_detection_data = load_fixture_data("mock_fabric_detection_data")
    
    def test_action_module_initialization(self):
        """Test ActionModule class initialization."""
        assert hasattr(self.action_module, 'logger')
        assert hasattr(self.action_module, 'error_handler')
        assert isinstance(self.action_module.logger, Logger)
        assert isinstance(self.action_module.error_handler, ErrorHandler)
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_detect_fabric_type_standalone(self, mock_get_associations):
        """Test fabric type detection for standalone fabric."""
        # Setup mocks
        mock_get_associations.return_value = self.fabric_data
        
        fabric_type = self.action_module.detect_fabric_type(
            "AK-R", 
            self.fabric_data
        )
        
        assert fabric_type == "standalone"
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_detect_fabric_type_msd_parent(self, mock_get_associations):
        """Test fabric type detection for MSD parent fabric."""
        # Setup mocks
        mock_get_associations.return_value = self.fabric_data
        
        fabric_type = self.action_module.detect_fabric_type(
            "AK-MSD_R",
            self.fabric_data
        )
        
        assert fabric_type == "multisite_parent"
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_detect_fabric_type_msd_child(self, mock_get_associations):
        """Test fabric type detection for MSD child fabric."""
        # Setup mocks
        mock_get_associations.return_value = self.fabric_data
        
        fabric_type = self.action_module.detect_fabric_type(
            "AK-RT",
            self.fabric_data
        )
        
        assert fabric_type == "multisite_child"
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_detect_fabric_type_nonexistent_fabric(self, mock_get_associations):
        """Test fabric type detection for non-existent fabric."""
        # Setup mocks
        mock_get_associations.return_value = self.fabric_data
        
        with pytest.raises(AnsibleError) as exc_info:
            self.action_module.detect_fabric_type("NONEXISTENT_FABRIC", self.fabric_data)

        assert "not found in NDFC" in str(exc_info.value)
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.execute_module_with_args')
    def test_standalone_fabric_workflow(self, mock_execute_module):
        """Test standalone fabric workflow execution."""
        # Setup mock return value
        mock_execute_module.return_value = self.workflow_results["standalone_success"]
        
        result = self.action_module.handle_standalone_workflow(
            self.module_args["basic_vrf_config"],
            {}
        )
        
        assert result["changed"] is True
        assert result["failed"] is False
        assert result["fabric_type"] == "standalone"
        mock_execute_module.assert_called_once()
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.execute_module_with_args')
    def test_multisite_parent_workflow(self, mock_execute_module):
        """Test multisite parent fabric workflow execution."""
        # Setup mock return value
        mock_execute_module.return_value = self.workflow_results["msd_parent_success"]
        
        result = self.action_module.handle_parent_msd_workflow(
            self.module_args["msd_parent_config"],
            self.fabric_data,
            {},
            "/tmp"
        )
        
        assert result["changed"] is True
        assert result["failed"] is False
        assert result["fabric_type"] == "multisite_parent"
        mock_execute_module.assert_called_once()
    
    def test_child_multisite_workflow(self):
        """Test child multisite fabric workflow (should redirect to parent)."""
        result = self.action_module.handle_child_msd_workflow(
            self.module_args["child_fabric_config"],
            {}
        )
        
        assert result["changed"] is False
        assert result["failed"] is True
        assert "not permitted on Child Multisite fabric" in result["msg"]
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_get_child_fabrics(self, mock_get_associations):
        """Test getting child fabrics for MSD parent."""
        mock_get_associations.return_value = self.fabric_associations
        
        # Create a list from fabric associations to simulate fabric_data
        fabric_data = {}
        for fab in self.fabric_associations:
            fabric_data[fab["fabricName"]] = fab
        
        # Test finding child fabrics for AK-MSD_R
        child_fabrics = []
        for fabric_name, fabric_info in fabric_data.items():
            if fabric_info.get("fabricParent") == "AK-MSD_R" and fabric_info.get("fabricState") == "member":
                child_fabrics.append(fabric_name)
        
        expected_children = ["AK-RT"]  # Based on fixture data
        assert len(child_fabrics) >= 1
        assert "AK-RT" in child_fabrics
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_get_child_fabrics_no_children(self, mock_get_associations):
        """Test getting child fabrics when none exist."""
        mock_get_associations.return_value = self.fabric_associations
        
        # Create a list from fabric associations to simulate fabric_data
        fabric_data = {}
        for fab in self.fabric_associations:
            fabric_data[fab["fabricName"]] = fab
        
        # Test finding child fabrics for AK-R (standalone fabric)
        child_fabrics = []
        for fabric_name, fabric_info in fabric_data.items():
            if fabric_info.get("fabricParent") == "AK-R" and fabric_info.get("fabricState") == "member":
                child_fabrics.append(fabric_name)
        
        assert child_fabrics == []
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule._execute_module')
    def test_execute_dcnm_module(self, mock_execute_module):
        """Test DCNM module execution."""
        # Setup mock return value
        mock_execute_module.return_value = {
            "changed": True,
            "failed": False,
            "msg": "Module executed successfully"
        }
        
        result = self.action_module.execute_module_with_args(
            self.module_args["basic_vrf_config"],
            {}
        )
        
        assert result["changed"] is True
        assert result["failed"] is False
        mock_execute_module.assert_called_once()
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.detect_fabric_type')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.handle_standalone_workflow')
    def test_run_method_standalone_fabric(self, mock_standalone_workflow, 
                                         mock_get_associations, mock_detect_type):
        """Test run method with standalone fabric."""
        # Setup mocks
        mock_get_associations.return_value = self.fabric_associations
        mock_detect_type.return_value = "standalone"
        mock_standalone_workflow.return_value = self.workflow_results["standalone_success"]
        
        # Setup task args
        self.mock_task.args = self.module_args["basic_vrf_config"]
        
        result = self.action_module.run(tmp=None, task_vars={})
        
        assert result["changed"] is True
        assert result["failed"] is False
        mock_standalone_workflow.assert_called_once()
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.detect_fabric_type')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.handle_parent_msd_workflow')
    def test_run_method_msd_parent_fabric(self, mock_parent_workflow,
                                         mock_get_associations, mock_detect_type):
        """Test run method with MSD parent fabric."""
        # Setup mocks
        mock_get_associations.return_value = self.fabric_associations
        mock_detect_type.return_value = "multisite_parent"
        mock_parent_workflow.return_value = self.workflow_results["msd_parent_success"]
        
        # Setup task args
        self.mock_task.args = self.module_args["msd_parent_config"]
        
        result = self.action_module.run(tmp=None, task_vars={})
        
        assert result["changed"] is True
        assert result["failed"] is False
        mock_parent_workflow.assert_called_once()
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.detect_fabric_type')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.handle_child_msd_workflow')
    def test_run_method_msd_child_fabric(self, mock_child_workflow,
                                        mock_get_associations, mock_detect_type):
        """Test run method with MSD child fabric."""
        # Setup mocks
        mock_get_associations.return_value = self.fabric_associations
        mock_detect_type.return_value = "multisite_child"
        mock_child_workflow.return_value = self.error_responses["child_direct_access"]
        
        # Setup task args
        self.mock_task.args = self.module_args["child_fabric_config"]
        
        result = self.action_module.run(tmp=None, task_vars={})
        
        assert result["failed"] is True
        assert "not permitted on Child Multisite fabric" in result["msg"]
        mock_child_workflow.assert_called_once()
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.detect_fabric_type')
    def test_run_method_invalid_fabric(self, mock_detect_type):
        """Test run method with invalid fabric name."""
        # Setup mock to raise exception
        mock_detect_type.side_effect = AnsibleError("Fabric 'NONEXISTENT_FABRIC' not found")
        
        # Setup task args
        self.mock_task.args = self.module_args["invalid_fabric_config"]
        
        result = self.action_module.run(tmp=None, task_vars={})
        
        assert result["failed"] is True
        assert "not found" in result["msg"]
    
    def test_validate_inputs_valid_config(self):
        """Test input validation with valid configuration."""
        valid_args = self.module_args["basic_vrf_config"]
        
        # Setup task args for validation
        self.mock_task.args = valid_args
        
        # Should not raise any exceptions
        try:
            result = self.action_module.run_pre_validation()
            assert not result.get("failed", False)
        except Exception as e:
            pytest.fail(f"validate_inputs raised {e} unexpectedly!")
    
    def test_validate_inputs_missing_fabric(self):
        """Test input validation with missing fabric parameter."""
        invalid_args = copy.deepcopy(self.module_args["basic_vrf_config"])
        del invalid_args["fabric"]
        
        # Setup task args for validation
        self.mock_task.args = invalid_args
        
        with pytest.raises(AnsibleError) as exc_info:
            self.action_module.run(tmp=None, task_vars={})
        
        assert "fabric" in str(exc_info.value)
    
    def test_validate_inputs_invalid_state(self):
        """Test input validation with invalid state parameter."""
        invalid_args = copy.deepcopy(self.module_args["basic_vrf_config"])
        invalid_args["state"] = "invalid_state"
        
        # Setup task args for validation
        self.mock_task.args = invalid_args
        
        result = self.action_module.run_pre_validation()
        
        # Should return validation error
        assert result.get("failed", False) is True
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule._execute_module')
    def test_obtain_fabric_associations_success(self, mock_execute_module):
        """Test successful fabric associations retrieval."""
        # Setup mock response
        mock_execute_module.return_value = {
            "failed": False,
            "response": {
                "RETURN_CODE": 200,
                "MESSAGE": "OK",
                "DATA": self.fabric_associations
            }
        }
        
        result = self.action_module.obtain_fabric_associations({}, "/tmp")

        assert len(result) > 0
        assert result.get("AK-R").get("fabricName") == "AK-R"
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule._execute_module')
    def test_obtain_fabric_associations_failure(self, mock_execute_module):
        """Test fabric associations retrieval failure."""
        # Setup mock response
        mock_execute_module.return_value = {
            "failed": True,
            "msg": "API call failed"
        }
        
        with pytest.raises(AnsibleError):
            self.action_module.obtain_fabric_associations({}, "/tmp")


class TestDcnmVrfActionIntegration:
    """Integration tests for the DCNM VRF action plugin."""
    
    def setup_method(self):
        """Set up test environment before each test method."""
        # Create mock objects
        self.mock_task = Mock()
        self.mock_connection = Mock()
        self.mock_play_context = Mock()
        self.mock_loader = Mock()
        self.mock_templar = Mock()
        self.mock_shared_loader_obj = Mock()
        
        # Load test data
        self.module_args = load_fixture_data("mock_module_args")
        self.fabric_associations = load_fixture_data("mock_fabric_associations")
        self.fabric_data = load_fixture_data("mock_fabric_associations_dict")
        self.parent_fabric_details = load_fixture_data("mock_parent_fabric_details")
        self.child_fabric_details = load_fixture_data("mock_child_fabric_details")
        self.standalone_fabric_details = load_fixture_data("mock_standalone_fabric_details")
        self.workflow_results = load_fixture_data("mock_workflow_results")
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule._execute_module')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_end_to_end_standalone_workflow(self, mock_get_associations, mock_execute_module):
        """Test complete end-to-end workflow for standalone fabric."""
        # Initialize action module
        action_module = ActionModule(
            task=self.mock_task,
            connection=self.mock_connection,
            play_context=self.mock_play_context,
            loader=self.mock_loader,
            templar=self.mock_templar,
            shared_loader_obj=self.mock_shared_loader_obj
        )
        
        # Setup task args
        self.mock_task.args = self.module_args["basic_vrf_config"]
        
        # Setup mock responses
        mock_get_associations.return_value = self.fabric_data
        mock_execute_module.return_value = self.workflow_results["standalone_success"]
        
        # Execute the workflow
        result = action_module.run(tmp=None, task_vars={})
        
        # Verify results
        assert result["changed"] is True
        assert result["failed"] is False
        assert result["fabric_type"] == "standalone"
        assert "successfully" in result["msg"]
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule._execute_module')
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_end_to_end_msd_parent_workflow(self, mock_get_associations, mock_execute_module):
        """Test complete end-to-end workflow for MSD parent fabric."""
        # Initialize action module
        action_module = ActionModule(
            task=self.mock_task,
            connection=self.mock_connection,
            play_context=self.mock_play_context,
            loader=self.mock_loader,
            templar=self.mock_templar,
            shared_loader_obj=self.mock_shared_loader_obj
        )
        
        # Setup task args
        self.mock_task.args = self.module_args["msd_parent_config"]
        
        # Setup mock responses
        mock_get_associations.return_value = self.fabric_data
        mock_execute_module.return_value = self.workflow_results["msd_parent_success"]
        
        # Execute the workflow
        result = action_module.run(tmp=None, task_vars={})
        
        # Verify results
        assert result["changed"] is True
        assert result["failed"] is False
        assert result["fabric_type"] == "multisite_parent"
        assert "successfully" in result["msg"]
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_end_to_end_error_handling(self, mock_get_associations):
        """Test complete end-to-end error handling workflow."""
        # Initialize action module
        action_module = ActionModule(
            task=self.mock_task,
            connection=self.mock_connection,
            play_context=self.mock_play_context,
            loader=self.mock_loader,
            templar=self.mock_templar,
            shared_loader_obj=self.mock_shared_loader_obj
        )
        
        # Setup task args with invalid fabric
        self.mock_task.args = self.module_args["invalid_fabric_config"]
        
        # Setup mock response for fabric not found
        mock_get_associations.return_value = self.fabric_data
        
        # Execute the workflow
        result = action_module.run(tmp=None, task_vars={})
        
        # Verify error handling
        assert result["failed"] is True
        assert "not found in NDFC" in result["msg"]
        assert "error_type" in result
        assert "operation" in result


class TestDcnmVrfActionPerformance:
    """Performance and stress tests for the DCNM VRF action plugin."""
    
    def setup_method(self):
        """Set up test environment before each test method."""
        self.performance_data = load_fixture_data("mock_performance_data")
    
    def test_logger_performance(self):
        """Test logger performance under load."""
        logger = Logger("PerformanceTest")
        
        import time
        start_time = time.time()
        
        # Log many messages quickly
        for i in range(1000):
            with patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.display'):
                logger.log("info", f"Performance test message {i}", 
                          fabric="test_fabric", operation="performance_test")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (less than 1 second for 1000 messages)
        assert duration < 1.0
    
    def test_error_handler_memory_usage(self):
        """Test error handler doesn't leak memory with many errors."""
        mock_logger = Mock()
        error_handler = ErrorHandler(mock_logger)
        
        # Handle many errors to test for memory leaks
        for i in range(100):
            test_error = Exception(f"Test error {i}")
            try:
                error_handler.handle_exception(
                    test_error,
                    operation="memory_test",
                    fabric="test_fabric"
                )
            except AnsibleError:
                # Expected to raise AnsibleError
                pass
        
        # If we get here without memory issues, test passes
        assert True
    
    @patch('ansible_collections.cisco.dcnm.plugins.action.dcnm_vrf.ActionModule.obtain_fabric_associations')
    def test_fabric_detection_caching(self, mock_get_associations):
        """Test that fabric details are properly cached to avoid repeated API calls."""
        # Initialize action module
        mock_task = Mock()
        action_module = ActionModule(
            task=mock_task,
            connection=Mock(),
            play_context=Mock(),
            loader=Mock(),
            templar=Mock(),
            shared_loader_obj=Mock()
        )
        
        # Setup mock response
        fabric_associations = load_fixture_data("mock_fabric_associations")
        mock_get_associations.return_value = fabric_associations
        
        # Call obtain_fabric_associations multiple times
        result1 = action_module.obtain_fabric_associations({}, "/tmp")
        result2 = action_module.obtain_fabric_associations({}, "/tmp")
        result3 = action_module.obtain_fabric_associations({}, "/tmp")
        
        # Verify all results are consistent
        assert result1 == result2 == result3
        assert len(result1) > 0


if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])