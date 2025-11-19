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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

# Standard Library Imports
import copy
import time

# Ansible Imports
from ansible_collections.ansible.netcommon.plugins.action.network import (
    ActionModule as ActionNetworkModule,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.action_error_handler import (
    ActionErrorHandler as ErrorHandler,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.action_logger import (
    ActionLogger as Logger,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    get_nd_version, obtain_federated_fabric_associations, obtain_fabric_associations
)
from ansible.utils.display import Display

# Module Constants
WAIT_TIME_FOR_DELETE_LOOP = 5
VALID_VRF_STATES = ["DEPLOYED", "PENDING", "NA"]
MAX_RETRY_COUNT = 50


class ActionModule(ActionNetworkModule):
    """
    NDFC VRF Action Plugin supporting Multisite (Multi-Site Domain) workflows

    This action plugin extends the base dcnm_vrf module with Multisite fabric support,
    handling Multisite Parent, Child Multisite, and Standalone fabric types.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display = Display()
        self.logger = Logger("NDFC_VRF_ActionPlugin", self.display)
        self.error_handler = ErrorHandler(self.logger)
        self.logger.info("NDFC VRF Action Plugin initialized")
        # Default NDFC version
        self.ndfc_version = 12.2

    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================

    def run(self, tmp=None, task_vars=None):
        """
        Main entry point for NDFC VRF action plugin execution.

        This method orchestrates the complete VRF operation workflow, handling fabric
        type detection, validation, and appropriate workflow routing. It serves as the
        central coordinator for all VRF operations across different fabric types.

        Execution Flow:
        - Performs initial validation of module parameters
        - Discovers fabric associations from NDFC controller
        - Detects fabric type (Multisite Parent, Multisite Child, Standalone)
        - Routes to appropriate workflow handler based on fabric type
        - Returns structured results with operation outcomes

        Fabric Type Workflows:
        - Multisite Parent: Handles parent VRF config and child fabric coordination
        - Multisite Child: Restricts direct access, requires parent fabric routing
        - Standalone: Standard VRF operations without Multisite considerations

        Error Handling:
        - Comprehensive exception handling with structured error responses
        - Detailed logging for debugging and monitoring
        - Fail-fast approach with immediate error returns

        Args:
            tmp (str, optional): Temporary directory path for module operations
            task_vars (dict, optional): Ansible task variables and context

        Returns:
            dict: Structured result dictionary containing:
                - failed (bool): True if operation failed
                - changed (bool): True if fabric state was modified
                - msg (str): Success/failure message
                - fabric_type (str): Detected fabric type
                - workflow (str): Executed workflow description
                - Additional workflow-specific result data
        """
        # Log workflow initiation
        self.logger.info("Starting NDFC VRF action plugin execution")

        # Perform initial parameter validation
        result = self.run_pre_validation()
        if result is False:
            return self.error_handler.handle_failure("Pre-validation failed")

        # Extract module arguments and fabric name
        module_args = self._task.args.copy()
        fabric_name = module_args.get("fabric")

        self.ndfc_version = get_nd_version(self, task_vars, tmp)

        self.logger.info(f"ND version: {self.ndfc_version}", fabric=fabric_name)

        # Discover fabric associations from NDFC
        fabric_association_data = obtain_federated_fabric_associations(self, task_vars, tmp)

        # Validate required fabric parameter
        if not fabric_name:
            return self.error_handler.handle_failure("Parameter 'fabric' is required")

        # Log fabric processing initiation
        self.logger.info(f"Processing fabric: {fabric_name}", fabric=fabric_name)

        # Detect fabric type for workflow routing
        fabric_type, fabric_data = self.detect_fabric_type(fabric_name, fabric_association_data, "mcfg")
        if not fabric_type:
            fabric_association_data = obtain_fabric_associations(self, task_vars, tmp)
            fabric_type, fabric_data = self.detect_fabric_type(fabric_name, fabric_association_data, "msd")
            if not fabric_type:
                return self.error_handler.handle_failure(f"Fabric '{fabric_name}' not found in NDFC.")

        self.logger.info(f"Detected fabric type: {fabric_type}", fabric=fabric_name)

        # Route to appropriate workflow based on fabric type
        if fabric_type in ["multisite_parent", "multicluster_parent"]:
            result = self.handle_parent_msd_workflow(module_args, fabric_data, fabric_type, task_vars, tmp)
        elif fabric_type in ["multisite_child", "multicluster_child"]:
            result = self.handle_child_msd_workflow(module_args, fabric_data, task_vars, tmp)
        else:
            result = self.handle_standalone_workflow(module_args, task_vars, tmp)

        return result

    # =========================================================================
    # VALIDATION METHODS
    # =========================================================================

    def run_pre_validation(self):
        """
        Perform comprehensive input validation for VRF module parameters.

        This method validates the input configuration to ensure proper parameter
        usage and catch common configuration errors early in the execution flow.
        It checks for parameter placement, structure validation, and state-specific
        restrictions to prevent invalid operations.

        Validation Checks:
        - vlan_id placement validation (must be in config, not attach block)
        - vrf_lite structure validation (must contain interface parameter)
        - child_fabric_config restrictions for delete operations
        - Parameter structure and format validation

        State-Specific Validations:
        - merged/overridden/replaced: Full parameter validation
        - deleted: Restricted child_fabric_config usage

        Args:
            None (uses self._task.args for validation input)

        Returns:
            bool: True if validation passes, False if any validation fails

        Raises:
            AnsibleError: On validation failures with detailed error info
        """
        # Log validation initiation
        self.logger.debug("Starting input validation", operation="validation")

        try:
            # Extract state and configuration from task arguments
            state = self._task.args.get("state")
            config = self._task.args.get("config")

            # Validate configurations for create/update states
            if state in ["merged", "overridden", "replaced", "query"] or not state:
                if config:
                    # Iterate through each VRF configuration
                    for con_idx, con in enumerate(config):
                        # Validate attach block parameters if present
                        if "attach" in con:
                            for at_idx, at in enumerate(con["attach"]):
                                # Check for vlan_id misplacement
                                if "vlan_id" in at:
                                    msg = (
                                        f"Config[{con_idx}].attach[{at_idx}]: vlan_id should not be "
                                        "specified under attach block. Please specify under config block instead"
                                    )
                                    self.logger.error(msg, operation="validation")
                                    return False

                                # Validate vrf_lite structure
                                if "vrf_lite" in at:
                                    try:
                                        # Attempt to iterate vrf_lite to check structure
                                        for vl in at["vrf_lite"]:
                                            continue
                                    except TypeError:
                                        # vrf_lite is not iterable - missing interface parameter
                                        msg = (
                                            f"Config[{con_idx}].attach[{at_idx}]: Please specify interface "
                                            "parameter under vrf_lite section in the playbook"
                                        )
                                        self.logger.error(msg, operation="validation")
                                        return False

            # Log successful validation completion
            self.logger.debug(
                "Input pre-validation completed successfully", operation="validation"
            )
            return True

        except Exception as e:
            # Handle validation exceptions
            return self.error_handler.handle_exception(e, "validation")

    # =========================================================================
    # FABRIC DISCOVERY & TYPE DETECTION
    # =========================================================================

    def detect_fabric_type(self, fabric_name, fabric_associations, fabric_data_type):
        """
        Analyze fabric data to determine fabric type for workflow routing.

        This method examines fabric properties from NDFC to classify the fabric
        into one of three types that determine the appropriate VRF workflow.
        The classification drives the execution path and operation restrictions.

        Fabric Type Classification:
        - Multisite Parent: fabricType="MSD" - Can orchestrate child fabrics
        - Multisite Child: fabricState="member" - Restricted to parent-driven operations
        - Standalone: All others - Standard VRF operations without Multisite features

        Detection Logic:
        1. Check if fabric exists in NDFC fabric associations
        2. Examine fabricType field for Multisite Parent identification
        3. Examine fabricState field for child fabric identification
        4. Default to standalone for all other configurations

        Args:
            fabric_name (str): Name of fabric to classify
            fabric_data (dict): Fabric associations data from NDFC
            fabric_data_type (str): Type of fabric data (e.g., "mcfg", "msd")

        Returns:
            None|str: Detected fabric type:
                - "multicluster_parent"
                - "multicluster_child"
                - "multisite_parent"
                - "multisite_child"
                - "standalone"
                - None if fabric not found
            None|dict: Fabric data for the specified fabric
        """
        # Log fabric type detection initiation
        self.logger.debug(
            f"Detecting fabric type for: {fabric_name}",
            fabric=fabric_name,
            operation="type_detection"
        )

        # Validate fabric exists in NDFC associations
        if fabric_name not in fabric_associations:
            return None, None

        fabric_data = fabric_associations.get(fabric_name)
        detected_type = None
        # Extract fabric properties for classification
        fabric_type = fabric_data.get("fabricType")
        fabric_state = fabric_data.get("fabricState")

        if fabric_data_type == "mcfg":
            # Classify fabric based on properties for multicluster fabric data
            if fabric_type == "MFD":
                # Multicluster type indicates parent fabric
                detected_type = "multicluster_parent"
            elif fabric_state == "member":
                # Member state indicates child fabric
                detected_type = "multicluster_child"

        elif fabric_data_type == "msd":
            # Classify fabric based on msd properties
            if fabric_type == "MSD":
                # Multisite type indicates parent fabric
                detected_type = "multisite_parent"
            elif fabric_state == "member":
                # Member state indicates child fabric
                detected_type = "multisite_child"
            else:
                # All others are standalone fabrics
                detected_type = "standalone"

        # Log classification result with details
        self.logger.debug(
            f"Fabric type detected: {detected_type} "
            f"(fabricType={fabric_type}, fabricState={fabric_state})",
            fabric=fabric_name,
            operation="type_detection"
        )
        return detected_type, fabric_data

    def validate_child_parent_fabric(self, child_fabric, parent_fabric, fabric_associations):
        """
        Validate the relationship between child and Multisite Parent fabrics.

        This method ensures that child fabrics are properly associated with their
        Multisite Parent fabric and validates the hierarchical relationship integrity.
        It prevents misconfigurations that could lead to operational issues in
        multi-site domain environments.

        Validation Checks:
        - Child fabric exists in Parent Fabric's NDFC fabric associations

        Args:
            child_fabric (str): Name of child fabric to validate
            parent_fabric (str): Name of expected parent fabric
            fabric_associations (list): Child fabric associations data from NDFC

        Returns:
            bool: True if child-parent relationship is valid, False otherwise
        """
        # Log validation initiation with context
        self.logger.debug(
            f"Validating child-parent fabric relationship: {child_fabric} <-> {parent_fabric}, {fabric_associations}",
            fabric=child_fabric,
            operation="child_parent_validation"
        )

        if fabric_associations is None:
            error_msg = (
                f"Fabric associations data is None while validating child-parent "
                f"relationship: {child_fabric} -> {parent_fabric}"
            )
            self.logger.error(
                error_msg, fabric=child_fabric, operation="child_parent_validation"
            )
            return False

        # Validate child fabrics present in parent hierarchy
        if child_fabric not in fabric_associations:
            error_msg = (
                f"Fabric '{child_fabric}' not associated with {parent_fabric}. "
                f"Associated child fabrics: {fabric_associations}"
            )
            self.logger.error(
                error_msg, fabric=child_fabric, operation="child_parent_validation"
            )
            return False

        # Validation passed
        return True

    # =========================================================================
    # WORKFLOW HANDLERS
    # =========================================================================

    def handle_parent_msd_workflow(self, module_args, fabric_data, fabric_type, task_vars, tmp):
        """
        Execute comprehensive Multisite Parent fabric workflow with child fabric orchestration.
        This method implements the complete Multisite Parent workflow that coordinates VRF
        operations across parent and child fabrics in the correct sequence. It handles
        configuration splitting, validation, execution coordination, and result aggregation
        for complex multi-site domain scenarios.

        Workflow Sequence:
        1. Configuration Validation and Splitting
           - Validates child fabric configurations and relationships
           - Splits parent and child configurations into separate tasks
           - Ensures proper Multisite hierarchy and parameter usage

        2. Parent Fabric Operations
           - Executes VRF creation, configuration, and attachment on parent
           - Handles parent-specific parameters and templates
           - Validates parent operation completion before child processing
        3. Child Fabric Coordination
           - Waits for VRF readiness on child fabrics
           - Executes child fabric tasks sequentially
           - Applies child-specific VRF parameters and configurations

        4. Result Aggregation
           - Combines parent and child operation results
           - Creates structured response with fabric-specific outcomes
           - Handles error propagation and rollback scenarios

        Configuration Processing:
        - Extracts child_fabric_config from parent VRF definitions
        - Creates clean parent configurations without child parameters
        - Generates child tasks grouped by fabric with VRF lists
        - Validates child fabric relationships and capabilities

        Error Handling:
        - Fail-fast on validation errors with detailed messages
        - Child task failures abort workflow with context preservation
        - Comprehensive logging for debugging complex multi-fabric scenarios
        Args:
            module_args (dict): Original module arguments from playbook
            fabric_data (dict): Fabric associations data from NDFC
            fabric_type (str): Detected fabric type ("multisite_parent, multicluster_parent")
            task_vars (dict): Ansible task variables for execution context
            tmp (str): Temporary directory path for operations

        Returns:
            dict: Comprehensive workflow result containing:
                - failed (bool): True if any operation failed
                - changed (bool): True if any fabric was modified
                - fabric_type (str): "multisite_parent"
                - workflow (str): Workflow description
                - parent_fabric (dict): Parent fabric operation results
                - child_fabrics (list): Child fabric operation results
                - Error details and context if failures occurred
        """
        # Extract parent fabric name for context
        parent_fabric = module_args.get("fabric")
        # Log workflow initiation
        self.logger.info(
            "Starting Multisite Parent workflow",
            fabric=parent_fabric,
            operation="parent_multisite_workflow"
        )

        try:
            # Step 1: Validate and split parent/child configurations
            config = module_args.get("config")
            state = module_args.get("state")
            parent_config = []
            child_tasks_dict = {}
            # Extract associated child fabrics from NDFC data
            child_fabric_associations = [
                child_fabric.get("fabricName") for child_fabric in fabric_data.get("members", [])]

            if config:
                # Process each VRF configuration for parent/child splitting
                for vrf_idx, vrf in enumerate(config):
                    child_fabric_configs = vrf.get("child_fabric_config")
                    if "child_fabric_config" in vrf:
                        if state != "deleted":

                            child_fabric_configs = vrf.get("child_fabric_config")
                            if not child_fabric_configs:
                                error_msg = (
                                    f"Config[{vrf_idx+1}]: child_fabric_config is required for "
                                    "Multisite Parent fabrics. It can be optionally removed when state is query/deleted."
                                )
                                return self.error_handler.handle_failure(error_msg)

                            # Validate each child fabric configuration
                            for child_idx, child_config in enumerate(child_fabric_configs):
                                fabric_name = child_config.get("fabric")
                                if not fabric_name:
                                    error_msg = (
                                        f"Config[{vrf_idx+1}].child_fabric_config[{child_idx+1}]: "
                                        "fabric is required"
                                    )
                                    return self.error_handler.handle_failure(error_msg)
                                # Validate child fabric type and child-parent relationship
                                if not self.validate_child_parent_fabric(
                                    fabric_name, parent_fabric, child_fabric_associations
                                ):
                                    error_msg = (
                                        f"Multisite Child-Parent fabric validation failed: {fabric_name} -> {parent_fabric}"
                                    )
                                    return self.error_handler.handle_failure(error_msg)

                                # Create child tasks and group by child fabric name
                                child_tasks_dict = self.create_child_task(
                                    vrf, child_config, child_tasks_dict, fabric_name, module_args
                                )

                        # Create parent VRF without child_fabric_config
                        parent_vrf = copy.deepcopy(vrf)
                        del parent_vrf["child_fabric_config"]
                        parent_config.append(parent_vrf)
                    else:
                        # Handle VRFs without child fabric configurations
                        parent_vrf = copy.deepcopy(vrf)
                        parent_config.append(parent_vrf)

            # Step 2: Execute parent VRF operations
            self.logger.info(
                f"Executing parent operations for {len(parent_config)} VRF configurations",
                fabric=parent_fabric,
                operation="parent_execution"
            )
            parent_module_args = copy.deepcopy(module_args)
            parent_module_args["config"] = parent_config
            fabric_details = {}
            fabric_details["nd_version"] = self.ndfc_version
            fabric_details["fabric_type"] = fabric_type
            fabric_details["members"] = fabric_data.get("members", [])
            parent_module_args["fabric_details"] = fabric_details

            # Execute parent fabric VRF operations
            parent_result = self.execute_module_with_args(parent_module_args, task_vars, tmp)

            # Step 3: Execute child fabric tasks if parent succeeded
            child_results = []
            if not parent_result.get("failed", False) and child_tasks_dict:
                self.logger.info(f"Processing {len(child_tasks_dict)} child fabrics",
                                 fabric=parent_fabric, operation="child_execution")

                for child_task in child_tasks_dict.values():
                    if state != "query":
                        # Wait for VRF readiness on child fabric before processing
                        all_vrf_ready, vrf_not_ready = self.wait_for_vrf_ready(
                            child_task["vrf_list"],
                            child_task["fabric"],
                            child_task["fabric_details"],
                            task_vars,
                            tmp
                        )
                        if not all_vrf_ready:
                            error_msg = (
                                f"VRF(s) {', '.join(vrf_not_ready)} not in a deployable state on fabric "
                                f"{child_task['fabric']}. Please ensure VRF(s) are in DEPLOYED/PENDING/NA "
                                "state before proceeding."
                            )
                            return self.error_handler.handle_failure(error_msg, changed=True)

                    # Execute child fabric task
                    self.logger.info("Executing child task", fabric=child_task["fabric"], operation="child_execution")
                    child_result = self.execute_child_task(child_task, task_vars, tmp)
                    child_results.append(child_result)

                    # Handle child task failures with immediate abort
                    if child_result.get("failed", False):
                        error_msg = f"Child fabric task failed for {child_task['fabric']}: {child_result.get('msg', 'Unknown error')}"
                        self.logger.error(error_msg, fabric=child_task["fabric"], operation="child_execution")
                        break

            # Step 4: Create structured results
            result = self.create_structured_results(parent_result, child_results, parent_fabric)
            self.logger.info("Multisite Parent workflow completed successfully", fabric=parent_fabric, operation="parent_multisite_workflow")
            return result

        except Exception as e:
            # Handle workflow-level exceptions
            return self.error_handler.handle_exception(e, "parent_multisite_workflow", parent_fabric)

    def handle_child_msd_workflow(self, module_args, fabric_type, task_vars, tmp):
        """
        Handle restricted access attempts to Child Multisite fabrics.
        This method enforces the Multisite operational model by preventing direct
        access to child fabrics. In Multisite architectures, all VRF operations
        must be coordinated through the parent fabric to maintain consistency
        and proper orchestration across the multi-site domain.

        Operational Restrictions:
        - Direct VRF operations on child fabrics are not permitted
        - All child fabric changes must be initiated from parent fabric
        - Prevents configuration drift and maintains Multisite integrity
        - Enforces proper Multisite workflow patterns

        Security Model:
        - Child fabrics should only be modified through parent orchestration
        - Direct access could bypass Multisite coordination mechanisms
        - Prevents unauthorized or uncoordinated fabric modifications

        Args:
            module_args (dict): Original module arguments from playbook
            fabric_type (str): Detected fabric type ("multisite_child", "multicluster_child")
            task_vars (dict): Ansible task variables for module execution

        Returns:
            dict: Result indicating operation:
                - failed (bool): True or False based on operation
                - changed (bool): False (no changes allowed)
                - msg (str): Operation specific data message
                - fabric_type (str): "multisite_child"
                - workflow (str): "Child Multisite Workflow"
        """
        # Extract fabric name for logging
        fabric_name = module_args.get("fabric")
        state = module_args.get("state")
        self.logger.info("Starting Multisite Child workflow", operation="multisite_child_workflow")
        if state == "query":
            child_module_args = {
                "fabric": module_args["fabric"],
                "state": "query",
                "config": module_args.get("config"),
                "_fabric_type": "standalone"
            }

            # Execute base dcnm_vrf module functionality
            result = self.execute_module_with_args(child_module_args, task_vars, tmp)

            # Add workflow identification to result if not present
            if "fabric_type" not in result:
                result["fabric_type"] = fabric_type
                result["workflow"] = "Multisite Child VRF Processing"

            # Log successful completion
            self.logger.info("Multisite Child workflow completed successfully", operation="multisite_child_workflow")
        else:
            # Log attempted direct child fabric access for other states
            error_msg = f"Attempted task on Child Multisite fabric '{fabric_name}'. State 'query' is only allowed."
            return self.error_handler.handle_failure(error_msg)

        return result

    def handle_standalone_workflow(self, module_args, task_vars, tmp):
        """
        Execute standard VRF operations for non-Multisite (standalone) fabrics.

        This method handles VRF operations for fabrics that are not part of
        Multi-Site Domain (Multisite) configurations. It provides a direct pass-through
        to the base dcnm_vrf module functionality without Multisite-specific processing.

        Workflow Characteristics:
        - Direct pass-through to base module functionality
        - No child fabric considerations or orchestration
        - Standard VRF operations (create, update, delete, attach)
        - No additional Multisite-specific validation or processing

        Operation Types Supported:
        - VRF creation and configuration
        - VRF attachments to switches
        - VRF updates and modifications
        - VRF deletion and cleanup

        Args:
            module_args (dict): Original module arguments from playbook
            task_vars (dict): Ansible task variables for module execution
        Returns:
            dict: Module execution result containing:
                - changed (bool): True if fabric state was modified
                - failed (bool): True if operation failed
                - fabric_type (str): Set to "standalone"
                - workflow (str): Workflow description
                - Additional standard dcnm_vrf module results
        """
        # Log standalone workflow initiation
        self.logger.info("Starting standalone Non-Multisite workflow", operation="standalone_workflow")

        fabric_details = {}
        fabric_details["nd_version"] = self.ndfc_version
        fabric_details["fabric_type"] = "standalone"

        parent_module_args = {
            "fabric": module_args["fabric"],
            "config": module_args.get("config"),
            "fabric_details": fabric_details
        }

        if module_args.get("state"):
            parent_module_args["state"] = module_args["state"]

        # Execute base dcnm_vrf module functionality
        result = self.execute_module_with_args(parent_module_args, task_vars, tmp)

        # Add workflow identification to result if not present
        if "fabric_type" not in result:
            result["fabric_type"] = "standalone"
            result["workflow"] = "Standalone Fabric VRF Processing"

        # Log successful completion
        self.logger.info("Standalone workflow completed successfully", operation="standalone_workflow")
        return result

    # =========================================================================
    # CHILD FABRIC TASK MANAGEMENT
    # =========================================================================

    def create_child_task(self, parent_vrf, child_config, child_tasks_dict, child_fabric_data, parent_module_args):
        """
        Create and organize child fabric tasks from parent VRF and child configurations.

        This method processes child fabric configurations and creates structured tasks
        that can be executed independently on child fabrics. It handles task grouping
        by fabric name to optimize execution and maintains VRF context from parent
        configurations while applying child-specific parameters.

        Task Creation Process:
        - Extracts fabric name from child configuration
        - Removes fabric name from config (used as task key)
        - Inherits VRF name and deploy settings from parent VRF
        - Groups multiple VRFs by child fabric for batch processing
        - Maintains VRF list for readiness checking

        Task Grouping Logic:
        - Child tasks are grouped by fabric name for efficiency
        - Multiple VRFs for same child fabric are batched together
        - Each child fabric gets one task with multiple VRF configurations
        - VRF names tracked separately for status monitoring

        Configuration Inheritance:
        - VRF name: Inherited from parent VRF configuration
        - Deploy flag: Inherited from parent if specified
        - State: Inherited from parent module arguments
        - Child-specific parameters: From child_config block

        Args:
            parent_vrf (dict): Parent VRF configuration containing VRF name and settings
            child_config (dict): Child fabric configuration with fabric name and parameters
            child_tasks_dict (dict): Existing child tasks dictionary for accumulation
            child_fabric_data (dict): Child fabric properties from NDFC
            parent_module_args (dict): Original module arguments for state inheritance

        Returns:
            dict: Updated child tasks dictionary with structure:
                {
                    "child_fabric_name": {
                        "fabric": "child_fabric_name",
                        "state": "merged|replaced|overridden",
                        "config": [list of VRF configs for this fabric],
                        "vrf_list": [list of VRF names for readiness checking]
                    }
                }

        Raises:
            Exception: On task creation failures with context preservation
        """
        try:
            child_config = copy.deepcopy(child_config)
            # Extract and remove fabric name from child configuration
            child_fabric_name = child_config["fabric"]
            del child_config["fabric"]

            # Inherit VRF context from parent configuration
            child_config["vrf_name"] = parent_vrf["vrf_name"]

            # Inherit deploy setting from parent only
            if "deploy" in child_config:
                del child_config["deploy"]
            if "deploy" in parent_vrf:
                child_config["deploy"] = parent_vrf["deploy"]

            # Check if child fabric already has tasks (for grouping multiple VRFs)
            if child_tasks_dict.get(child_fabric_name):
                # Append to existing child fabric task
                child_tasks_dict[child_fabric_name]["config"].append(child_config)
                child_tasks_dict[child_fabric_name]["vrf_list"].append(child_config["vrf_name"])
            else:
                # Create new child fabric task
                child_task = {
                    "fabric": child_fabric_name,
                    "state": parent_module_args.get("state"),
                    "config": [child_config],
                    "vrf_list": [child_config["vrf_name"]]
                }
                child_tasks_dict[child_fabric_name] = child_task

            fabric_details = {}
            fabric_details["nd_version"] = self.ndfc_version
            if "clusterName" in child_fabric_data:
                fabric_details["fabric_type"] = "multicluster_child"
                fabric_details["cluster_name"] = child_fabric_data.get("clusterName")
            else:
                fabric_details["fabric_type"] = "multisite_child"
            child_tasks_dict[child_fabric_name]["fabric_details"] = fabric_details

            # Log task creation progress
            self.logger.debug(f"Created child task for VRF: {child_config['vrf_name']}", fabric=child_fabric_name,
                              operation="create_child_task")
            return child_tasks_dict
        except Exception as e:
            raise e

    def execute_child_task(self, child_task, task_vars, tmp):
        """
        Execute child fabric VRF operations using specialized Child Multisite workflow.

        This method handles the execution of VRF operations on child fabrics within
        an Multisite environment. It adapts parent module arguments for child fabric
        execution, applies state transformations, and maintains proper context
        for child fabric operations while ensuring Multisite operational consistency.

        Child Multisite Execution Model:
        - Child fabrics operate with restricted parameter sets
        - State transformations applied (overridden -> replaced)
        - Child-specific VRF parameters applied from parent orchestration
        - Independent execution context with parent-derived configurations

        State Handling:
        - overridden: Transformed to 'replaced' for child fabric compatibility
        - merged/replaced: Passed through unchanged
        - deleted: Should be prevented at validation stage

        Module Argument Adaptation:
        - fabric: Set to child fabric name
        - config: Child-specific VRF configurations
        - state: Transformed as needed for child fabric
        - _fabric_type: Set to "multisite_child" for module behavior

        Result Enhancement:
        - Adds child_fabric identifier to result
        - Includes invocation details for debugging
        - Preserves all standard dcnm_vrf result data
        - Maintains error context for troubleshooting

        Args:
            child_task (dict): Child fabric task containing:
                - fabric (str): Child fabric name
                - config (list): VRF configurations for child fabric
                - state (str): Operation state
                - vrf_list (list): VRF names for tracking
            task_vars (dict): Ansible task variables for execution context

        Returns:
            dict: Child fabric execution result containing:
                - Standard dcnm_vrf module results (changed, failed, diff, response)
                - child_fabric (str): Child fabric identifier
                - invocation (dict): Module arguments used for execution
                - Error details if execution failed
        """
        # Extract fabric name for logging and result context
        fabric_name = child_task["fabric"]

        # Log child task execution initiation
        self.logger.info(f"Executing child task for fabric: {fabric_name}", fabric=fabric_name, operation="execute_child_task")

        # Build child fabric module arguments
        child_module_args = {
            "fabric": fabric_name,
            "config": child_task["config"],
        }

        # Handle state transformations for child fabric compatibility
        state = child_task.get("state")
        if state:
            if state == "overridden":
                # Transform overridden to replaced for child fabrics
                child_module_args["state"] = "replaced"
            else:
                # Pass through other states unchanged
                child_module_args["state"] = state

        child_module_args["fabric_details"] = child_task.get("fabric_details")

        # Execute child fabric operations using base module
        child_result = self.execute_module_with_args(child_module_args, task_vars, tmp)

        # Enhance result with child fabric context
        child_result["child_fabric"] = fabric_name
        child_result["invocation"] = {
            "module_args": copy.deepcopy(child_module_args)
        }

        # Log execution outcome
        success = not child_result.get("failed", False)
        self.logger.info(f"Child task execution completed: {'Success' if success else 'Failed'}",
                         fabric=fabric_name, operation="execute_child_task")
        return child_result

    # =========================================================================
    # UTILITY & HELPER METHODS
    # =========================================================================

    def execute_module_with_args(self, module_args, task_vars, tmp):
        """
        Execute the dcnm_vrf module with specified arguments and context.

        This method provides a wrapper for executing the base dcnm_vrf module
        with custom arguments while preserving the original task context.
        It temporarily replaces task arguments, executes the module, and
        restores the original arguments to maintain task state integrity.

        Execution Flow:
        - Preserves original task arguments
        - Temporarily replaces with custom module arguments
        - Executes base dcnm_vrf module functionality
        - Adds invocation details to result for debugging
        - Restores original task arguments

        Use Cases:
        - Parent fabric VRF operations with modified configurations
        - Child fabric VRF operations with derived configurations
        - Module execution with dynamically generated parameters
        Args:
            module_args (dict): Custom module arguments to execute with
            task_vars (dict): Ansible task variables for execution context

        Returns:
            dict: Module execution result containing:
                - Standard dcnm_vrf module results
                - invocation: Module arguments used for execution
                - Additional execution context and debugging information
        """
        # Extract fabric name for logging context
        fabric_name = module_args.get("fabric", "Unknown")
        # Preserve original task arguments
        original_args = self._task.args

        try:
            # Log module execution initiation
            self.logger.debug("Executing NDFC VRF module", fabric=fabric_name, operation="execute_module")
            # Temporarily replace task arguments with custom ones
            self._task.args = module_args
            # Execute base dcnm_vrf module with custom arguments
            result = self._execute_module(
                module_name="cisco.dcnm.dcnm_vrf",
                module_args=module_args,
                task_vars=task_vars,
                tmp=tmp
            )

            # Add invocation details for debugging and audit trail
            result["invocation"] = {
                "module_args": copy.deepcopy(module_args)
            }

            # Log execution outcome
            success = not result.get("failed", False)
            self.logger.debug(f"Module execution completed: {'Success' if success else 'Failed'}",
                              fabric=fabric_name, operation="execute_module")
            return result

        except Exception as e:
            # Handle module execution failures
            raise e
        finally:
            # Always restore original task arguments
            self._task.args = original_args

    def wait_for_vrf_ready(self, vrf_list, fabric_name, fabric_details, task_vars, tmp):
        """
        Wait for VRFs to reach a deployable state on the specified fabric.

        This method monitors VRF status on child fabrics to ensure they are in
        appropriate states before child fabric operations proceed. It implements
        a polling mechanism with configurable retry logic and handles various
        VRF states that may occur during parent-to-child fabric propagation.
        VRF State Monitoring:
        - DEPLOYED: VRF is fully deployed and ready for operations
        - PENDING: VRF deployment is in progress, acceptable for operations
        - NA: VRF state not applicable, typically ready for operations
        - OUT-OF-SYNC: VRF configuration drift, handled with retry logic

        Polling Algorithm:
        - Queries NDFC REST API for current VRF status on fabric
        - Removes VRFs from wait list as they reach ready states
        - Implements exponential backoff with configurable wait times
        - Handles persistent OUT-OF-SYNC states with tolerance logic

        Retry Logic:
        - Maximum retry count based on MAX_RETRY_COUNT and WAIT_TIME_FOR_DELETE_LOOP
        - OUT-OF-SYNC VRFs get additional chances before removal
        - Persistent wait list items eventually timeout and fail
        - Progressive logging of wait status and remaining retries

        State Transition Handling:
        - Newly created VRFs may initially show as non-existent
        - Parent fabric changes propagate to child fabrics over time
        - Configuration drift scenarios handled with retry tolerance
        - Network connectivity issues accommodated with retry logic

        Args:
            vrf_list (list): List of VRF names to monitor for readiness
            fabric_name (str): Child fabric name where VRFs should be ready
            task_vars (dict): Ansible task variables for API calls
            tmp (str): Temporary directory path for operations

        Returns:
            tuple: (all_ready, remaining_vrfs)
                - all_ready (bool): True if all VRFs reached ready state
                - remaining_vrfs (list): VRF names still not ready (if any)

        Raises:
            Exception: On API failures or critical polling errors
        """
        # Handle empty VRF list case
        if not vrf_list:
            return True, None

        # Initialize retry tracking and OUT-OF-SYNC handling
        vrf_oos_list = []
        retry_count = max(MAX_RETRY_COUNT // WAIT_TIME_FOR_DELETE_LOOP, 1)

        # Log readiness monitoring initiation
        self.logger.info(f"Waiting for VRF(s) to be ready: {', '.join(vrf_list)}",
                         fabric=fabric_name, operation="wait_for_vrf_ready")

        path = f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs"
        proxy = ""
        if fabric_details.get("fabric_type") == "multicluster_child":
            if self.ndfc_version >= 12.4:
                proxy = "/fedproxy"
            else:
                proxy = "/onepath"
            path = proxy + fabric_details.get("cluster_name") + path
        # Continue polling while VRFs remain and retries available
        while retry_count > 0 and vrf_list:
            try:
                # Query NDFC for current VRF status on fabric
                resp = self._execute_module(
                    module_name="cisco.dcnm.dcnm_rest",
                    module_args={
                        "method": "GET",
                        "path": path,
                    },
                    task_vars=task_vars,
                    tmp=tmp
                )

                # Validate API response and extract VRF data
                response_data = self.error_handler.validate_api_response(resp, "VRF status check", fabric_name)
                vrf_data = response_data.get("DATA", [])

                # Process each VRF in the fabric response
                for vrf in vrf_data:
                    vrf_name = vrf.get("vrfName")
                    if vrf_name in vrf_list:
                        vrf_status = vrf.get("vrfStatus")

                        # Check if VRF is in ready state
                        if vrf_status in VALID_VRF_STATES:
                            # VRF is ready, remove from wait list
                            vrf_list.remove(vrf_name)
                            self.logger.debug(f"VRF {vrf_name} is ready (status: {vrf_status})",
                                              fabric=fabric_name, operation="wait_for_vrf_ready")
                        elif vrf_status == "OUT-OF-SYNC":
                            # Handle OUT-OF-SYNC state with tolerance
                            if vrf not in vrf_oos_list:
                                # First time seeing this VRF as OUT-OF-SYNC
                                vrf_oos_list.append(vrf)
                                self.logger.debug(f"VRF {vrf_name} is OUT-OF-SYNC",
                                                  fabric=fabric_name, operation="wait_for_vrf_ready")
                            else:
                                # VRF has been OUT-OF-SYNC before, remove from wait list
                                vrf_list.remove(vrf_name)
                                self.logger.debug(f"VRF {vrf_name} removed after persistent OUT-OF-SYNC",
                                                  fabric=fabric_name, operation="wait_for_vrf_ready")

                # If VRFs still waiting, sleep and retry
                if vrf_list:
                    time.sleep(WAIT_TIME_FOR_DELETE_LOOP)
                    retry_count -= 1
                    self.logger.debug(f"VRF(s) still not ready: {', '.join(vrf_list)}, retries left: {retry_count}",
                                      fabric=fabric_name, operation="wait_for_vrf_ready")

            except Exception as e:
                # Log API or processing errors
                self.logger.error(f"VRF readiness check failed: {str(e)}",
                                  fabric=fabric_name, operation="wait_for_vrf_ready")
                raise e

        # Determine final outcome
        if vrf_list:
            # Some VRFs never reached ready state
            self.logger.warning(f"VRF(s) not ready after maximum retries: {', '.join(vrf_list)}",
                                fabric=fabric_name, operation="wait_for_vrf_ready")
            return False, vrf_list
        else:
            # All VRFs reached ready state
            self.logger.info("All VRFs are ready", fabric=fabric_name, operation="wait_for_vrf_ready")
            return True, None

    def create_structured_results(self, parent_result, child_results, parent_fabric):
        """
        Create structured results combining parent and child fabric operations.

        This method aggregates execution results from Multi-Site Domain (Multisite)
        operations to create a unified response structure that clearly separates
        parent fabric outcomes from child fabric orchestration results. It
        provides consistent output format for both simple parent-only operations
        and complex parent-with-children workflows.

        Result Structure Design:
        - Multisite Parent operations: Primary fabric configuration changes
        - Child fabric operations: Secondary orchestrated operations
        - Combined status: Overall operation success/failure indicators
        - Workflow metadata: Operation type and fabric relationship context

        Parent-Only Workflow:
        - Simple augmentation of parent result with workflow metadata
        - Fabric type marked as "multisite_parent" for identification
        - Workflow description indicates no child processing occurred
        - All original parent result data preserved unchanged

        Parent-with-Children Workflow:
        - Comprehensive structure separating parent and child results
        - Parent fabric section with original operation outcomes
        - Child fabrics array with individual fabric results
        - Aggregated changed/failed status across all fabrics
        - Detailed failure messaging for child fabric issues

        Status Aggregation Logic:
        - changed: True if parent OR any child fabric changed
        - failed: True if parent OR any child fabric failed
        - Child failures include detailed error messaging
        - Parent failures preserved from original result

        Args:
            parent_result (dict): Result from parent fabric operations
                Expected keys: changed, failed, diff, response, msg
            child_results (list): List of child fabric operation results
                Each item expected keys: child_fabric, changed, failed, diff, response, msg
            parent_fabric (str): Name of the Multisite Parent fabric for context

        Returns:
            dict: Structured result with parent/child separation
                For parent-only operations:
                {
                    'changed': bool,
                    'failed': bool,
                    'fabric_type': 'multisite_parent',
                    'workflow': 'Multisite Parent without Child Fabric Processing',
                    ... (original parent_result fields)
                }

                For parent-with-children operations:
                {
                    'changed': bool,      # Aggregated across all fabrics
                    'failed': bool,       # Aggregated across all fabrics
                    'fabric_type': 'multisite_parent',
                    'workflow': 'Multisite Parent with Child Fabric Processing',
                    'parent_fabric': {
                        'fabric': str,
                        'changed': bool,
                        'diff': list,
                        'response': list
                    },
                    'child_fabrics': [
                        {
                            'fabric': str,
                            'changed': bool,
                            'failed': bool,
                            'diff': list,
                            'response': list
                        }, ...
                    ],
                    'msg': str  # Present if any child fabric failed
                }

        Raises:
            Exception: On critical result processing errors (handled internally)
        """
        # Log structured result creation initiation
        self.logger.debug("Creating structured results", fabric=parent_fabric, operation="create_structured_results")

        try:
            # Determine workflow type based on child results presence
            if child_results:
                # Parent-with-children workflow: Create comprehensive structure
                structured_result = {
                    "changed": parent_result.get("changed", False),
                    "failed": parent_result.get("failed", False),
                    "fabric_type": "multisite_parent",
                    "workflow": "Multisite Parent with Child Fabric Processing",
                    "parent_fabric": {
                        "fabric": parent_fabric,
                        "invocation": parent_result.get("invocation"),
                        "changed": parent_result.get("changed", False),
                        "diff": parent_result.get("diff", []),
                        "response": parent_result.get("response", [])
                    },
                    "child_fabrics": []
                }

                # Process each child fabric result
                for child_result in child_results:
                    # Create child fabric entry with all relevant data
                    child_entry = {
                        "fabric": child_result.get("child_fabric"),
                        "invocation": child_result.get("invocation"),
                        "changed": child_result.get("changed", False),
                        "failed": child_result.get("failed", False),
                        "diff": child_result.get("diff", []),
                        "response": child_result.get("response", [])
                    }
                    structured_result["child_fabrics"].append(child_entry)

                    # Aggregate child changed status into overall result
                    if child_result.get("changed", False):
                        structured_result["changed"] = True

                    # Aggregate child failed status and capture error details
                    if child_result.get("failed", False):
                        structured_result["failed"] = True
                        structured_result["msg"] = (
                            f"Child fabric task failed for {child_result.get('child_fabric')}: "
                            f"{child_result.get('msg', 'Unknown error')}"
                        )

                return structured_result
            else:
                # Parent-only workflow: Augment original result with metadata
                parent_result["workflow"] = "Multisite Parent without Child Fabric Processing"
                return parent_result

        except Exception as e:
            # Handle result structuring errors
            self.logger.error(f"Failed to create structured results: {str(e)}",
                              fabric=parent_fabric, operation="create_structured_results")
            raise e
