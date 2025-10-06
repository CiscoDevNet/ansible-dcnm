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
import json
import time
import traceback
from datetime import datetime

# Ansible Imports
from ansible_collections.ansible.netcommon.plugins.action.network import (
    ActionModule as ActionNetworkModule,
)
from ansible.utils.display import Display
from ansible.errors import AnsibleError

# Module Constants
WAIT_TIME_FOR_DELETE_LOOP = 5
VALID_VRF_STATES = ["DEPLOYED", "PENDING", "NA"]
MAX_RETRY_COUNT = 50

display = Display()


class Logger:
    """Logger for action plugin operations"""

    def __init__(self, name="DCNM_VRF_ActionPlugin"):
        self.name = name
        self.start_time = datetime.now()

    def log(self, level, message, fabric=None, operation=None):
        """Log message with timestamp and context"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        context = f"[{self.name}]"

        if fabric:
            context += f"[{fabric}]"
        if operation:
            context += f"[{operation}]"

        log_msg = f"{timestamp} {context} {level.upper()}: {message}"

        if level == "debug":
            display.vvv(log_msg)
        elif level == "info":
            display.vv(log_msg)
        elif level == "warning":
            display.warning(log_msg)
        elif level == "error":
            display.error(log_msg)
        else:
            display.v(log_msg)

    def debug(self, message, fabric=None, operation=None):
        self.log("debug", message, fabric, operation)

    def info(self, message, fabric=None, operation=None):
        self.log("info", message, fabric, operation)

    def warning(self, message, fabric=None, operation=None):
        self.log("warning", message, fabric, operation)

    def error(self, message, fabric=None, operation=None):
        self.log("error", message, fabric, operation)


class ErrorHandler:
    """Centralized error handling for action plugin"""

    def __init__(self, logger):
        self.logger = logger

    def handle_exception(self, e, operation="unknown", fabric=None, include_traceback=False):
        """Handle exceptions with logging and structured error response"""
        error_type = type(e).__name__
        error_msg = str(e)

        context = f"Operation: {operation}"
        if fabric:
            context += f", Fabric: {fabric}"

        self.logger.error(f"{error_type} in {context}: {error_msg}")

        error_response = {
            "failed": True,
            "msg": error_msg,
            "error_type": error_type,
            "operation": operation
        }

        if fabric:
            error_response["fabric"] = fabric

        if include_traceback:
            error_response["traceback"] = traceback.format_exc()
            self.logger.debug(f"Traceback: {traceback.format_exc()}")

        return error_response

    def validate_api_response(self, response, operation="API call", fabric=None):
        """Validate API response and handle errors"""
        if not response:
            raise AnsibleError(f"No response received for {operation}")

        if not response.get("response"):
            self.logger.error(f"Empty response for {operation}: {json.dumps(response, indent=2)}")
            raise AnsibleError(f"Empty response received for {operation}")

        resp = response.get("response")
        return_code = resp.get("RETURN_CODE", 500)

        if return_code != 200:
            error_msg = resp.get("MESSAGE", f"HTTP {return_code} error")
            self.logger.error(f"API error for {operation}: {json.dumps(resp, indent=2)}")
            raise AnsibleError(f"{operation} failed: {error_msg}")

        return resp


class ActionModule(ActionNetworkModule):
    """
    DCNM VRF Action Plugin supporting MSD (Multi-Site Domain) workflows

    This action plugin extends the base dcnm_vrf module with MSD fabric support,
    handling Parent MSD, Child MSD, and Standard fabric types.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = Logger("DCNM_VRF_ActionPlugin")
        self.error_handler = ErrorHandler(self.logger)
        self.logger.info("DCNM VRF Action Plugin initialized")

    # =========================================================================
    # MAIN ENTRY POINT
    # =========================================================================

    def run(self, tmp=None, task_vars=None):
        """Main entry point for the action plugin"""
        self.logger.info("Starting DCNM VRF action plugin execution")

        try:
            result = self.run_pre_validation()
            if result.get("failed", False):
                self.logger.error("Validation failed", operation="validation")
                return result

            fabric_data = self.obtain_fabric_associations(task_vars, tmp)
            module_args = self._task.args.copy()
            fabric_name = module_args.get("fabric")

            if not fabric_name:
                raise AnsibleError("Parameter 'fabric' is required")

            self.logger.info(f"Processing fabric: {fabric_name}", fabric=fabric_name)
            fabric_type = self.detect_fabric_type(fabric_name, fabric_data)
            self.logger.info(f"Detected fabric type: {fabric_type}", fabric=fabric_name)

            if fabric_type == "Parent MSD":
                result = self.handle_parent_msd_workflow(module_args, fabric_data, task_vars, tmp)
            elif fabric_type == "Child MSD":
                result = self.handle_child_msd_workflow(module_args, task_vars)
            else:
                result = self.handle_standard_workflow(task_vars)

            return result

        except Exception as e:
            return self.error_handler.handle_exception(e, "main_execution", include_traceback=True)

    # =========================================================================
    # VALIDATION METHODS
    # =========================================================================

    def run_pre_validation(self):
        """Run the existing validation logic"""
        self.logger.debug("Starting input validation", operation="validation")

        try:
            state = self._task.args.get("state")
            config = self._task.args.get("config", [])

            if state in ["merged", "overridden", "replaced"]:
                for con_idx, con in enumerate(config):
                    if "attach" in con:
                        for at_idx, at in enumerate(con["attach"]):
                            if "vlan_id" in at:
                                msg = f"Config[{con_idx}].attach[{at_idx}]: vlan_id should not be specified under attach block. Please specify under config block instead"
                                self.logger.error(msg, operation="validation")
                                return {"failed": True, "msg": msg}

                            if "vrf_lite" in at:
                                try:
                                    for vl in at["vrf_lite"]:
                                        continue
                                except TypeError:
                                    msg = f"Config[{con_idx}].attach[{at_idx}]: Please specify interface parameter under vrf_lite section in the playbook"
                                    self.logger.error(msg, operation="validation")
                                    return {"failed": True, "msg": msg}

            elif state == "deleted":
                for vrf_idx, vrf in enumerate(config):
                    if vrf.get("child_fabric_config"):
                        msg = f"Config[{vrf_idx}]: child_fabric_config is not supported with state 'deleted'"
                        self.logger.error(msg, operation="validation")
                        return {"failed": True, "msg": msg}

            self.logger.debug("Input validation completed successfully", operation="validation")
            return {"failed": False}

        except Exception as e:
            return self.error_handler.handle_exception(e, "validation")

    # =========================================================================
    # FABRIC DISCOVERY & TYPE DETECTION
    # =========================================================================

    def obtain_fabric_associations(self, task_vars, tmp):
        """Obtain fabric associations from DCNM"""
        self.logger.debug("Fetching fabric associations from DCNM", operation="fabric_discovery")

        try:
            msd_fabric_associations = self._execute_module(
                module_name="cisco.dcnm.dcnm_rest",
                module_args={
                    "method": "GET",
                    "path": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/msd/fabric-associations",
                },
                task_vars=task_vars,
                tmp=tmp
            )

            # Validate API response
            response_data = self.error_handler.validate_api_response(
                msd_fabric_associations,
                "fabric associations retrieval"
            )

            fabric_data = {}
            for fabric in response_data.get("DATA", []):
                fabric_name = fabric.get("fabricName")
                if fabric_name:
                    fabric_data[fabric_name] = fabric

            self.logger.info(f"Retrieved {len(fabric_data)} fabric associations", operation="fabric_discovery")
            return fabric_data

        except Exception as e:
            raise AnsibleError(f"Failed to obtain fabric associations: {str(e)}")

    def detect_fabric_type(self, fabric_name, fabric_data):
        """Detect fabric type from fabric name or DCNM API"""
        self.logger.debug(f"Detecting fabric type for: {fabric_name}", fabric=fabric_name, operation="type_detection")

        try:
            if fabric_name not in fabric_data:
                available_fabrics = list(fabric_data.keys())
                error_msg = f"Fabric '{fabric_name}' not found in NDFC. Available fabrics: {available_fabrics}"
                self.logger.error(error_msg, fabric=fabric_name, operation="type_detection")
                raise AnsibleError(error_msg)

            fabric_info = fabric_data.get(fabric_name)
            fabric_type = fabric_info.get("fabricType")
            fabric_state = fabric_info.get("fabricState")

            if fabric_type == "MSD":
                detected_type = "Parent MSD"
            elif fabric_state == "member":
                detected_type = "Child MSD"
            else:
                detected_type = "Standard"

            self.logger.debug(f"Fabric type detected: {detected_type} (fabricType={fabric_type}, fabricState={fabric_state})",
                            fabric=fabric_name, operation="type_detection")
            return detected_type

        except Exception as e:
            self.logger.error(f"Failed to detect fabric type: {str(e)}", fabric=fabric_name, operation="type_detection")
            raise

    # =========================================================================
    # WORKFLOW HANDLERS
    # =========================================================================

    def handle_parent_msd_workflow(self, module_args, fabric_data, task_vars, tmp):
        """Handle Parent MSD fabric workflow with child fabric processing"""
        parent_fabric = module_args.get("fabric")
        self.logger.info("Starting Parent MSD workflow", fabric=parent_fabric, operation="parent_msd_workflow")

        try:
            # Step 1: Validate and split parent/child configurations
            config = module_args.get("config", [])
            parent_config = []
            child_tasks_dict = {}

            for vrf_idx, vrf in enumerate(config):
                child_fabric_configs = vrf.get("child_fabric_config")

                if child_fabric_configs:
                    # Validate child fabrics
                    for child_idx, child_config in enumerate(child_fabric_configs):
                        fabric_name = child_config.get("fabric_name")
                        if not fabric_name:
                            error_msg = f"Config[{vrf_idx}].child_fabric_config[{child_idx}]: fabric_name is required"
                            self.logger.error(error_msg, fabric=parent_fabric, operation="config_validation")
                            return {"failed": True, "msg": error_msg}

                        # Validate child fabric type
                        try:
                            child_fabric_type = self.detect_fabric_type(fabric_name, fabric_data)
                            if child_fabric_type != "Child MSD":
                                error_msg = f"Fabric {fabric_name} is not a valid Child MSD fabric (detected: {child_fabric_type})"
                                self.logger.error(error_msg, fabric=parent_fabric, operation="config_validation")
                                return {"failed": True, "msg": error_msg}
                        except Exception as e:
                            error_msg = f"Config[{vrf_idx}].child_fabric_config[{child_idx}]: {str(e)}"
                            return {"failed": True, "msg": error_msg}

                        # Create child tasks and group by child fabric name
                        child_tasks_dict = self.create_child_task(vrf, child_config, module_args, child_tasks_dict)

                    # Create parent VRF without child_fabric_config
                    parent_vrf = copy.deepcopy(vrf)
                    if "child_fabric_config" in parent_vrf:
                        del parent_vrf["child_fabric_config"]
                    parent_config.append(parent_vrf)
                else:
                    parent_config.append(vrf)

            # Step 2: Execute parent VRF operations
            self.logger.info(f"Executing parent operations for {len(parent_config)} VRF configurations",
                           fabric=parent_fabric, operation="parent_execution")
            parent_module_args = copy.deepcopy(module_args)
            parent_module_args["config"] = parent_config
            parent_module_args["_fabric_type"] = "Parent MSD"

            parent_result = self.execute_module_with_args(parent_module_args, task_vars)

            # Step 3: Execute child fabric tasks if parent succeeded
            child_results = []
            if not parent_result.get("failed", False) and child_tasks_dict:
                self.logger.info(f"Processing {len(child_tasks_dict)} child fabrics",
                               fabric=parent_fabric, operation="child_execution")

                for child_task in child_tasks_dict.values():
                    all_vrf_ready, vrf_not_ready = self.wait_for_vrf_ready(
                        child_task["vrf_list"],
                        child_task["fabric"],
                        task_vars,
                        tmp
                    )
                    if not all_vrf_ready:
                        error_msg = f"VRF(s) {', '.join(vrf_not_ready)} not in a deployable state on fabric {child_task['fabric']}. Please ensure VRF(s) are in DEPLOYED/PENDING/NA state before proceeding."
                        self.logger.error(error_msg, fabric=child_task['fabric'], operation="vrf_readiness")
                        return {"failed": True, "msg": error_msg}

                    self.logger.info("Executing child task", fabric=child_task["fabric"], operation="child_execution")
                    child_result = self.execute_child_task(child_task, task_vars)
                    child_results.append(child_result)

                    if child_result.get("failed", False):
                        error_msg = f"Child fabric task failed for {child_task['fabric']}: {child_result.get('msg', 'Unknown error')}"
                        self.logger.error(error_msg, fabric=child_task["fabric"], operation="child_execution")
                        parent_result["failed"] = True
                        parent_result["msg"] = error_msg
                        parent_result["child_fabric_results"] = child_results
                        return parent_result

            # Step 4: Create structured results
            result = self.create_structured_results(parent_result, child_results, parent_fabric)
            self.logger.info("Parent MSD workflow completed successfully", fabric=parent_fabric, operation="parent_msd_workflow")
            return result

        except Exception as e:
            return self.error_handler.handle_exception(e, "parent_msd_workflow", parent_fabric)

    def handle_child_msd_workflow(self, module_args, task_vars):
        """Handle Child MSD fabric workflow with restrictions"""
        fabric_name = module_args.get("fabric", "Unknown")
        self.logger.warning("Attempted direct access to Child MSD fabric", fabric=fabric_name, operation="child_msd_workflow")

        result = {
            "failed": True,
            "msg": f"Task not permitted on Child MSD fabric '{fabric_name}'. Please perform operations through the Parent MSD fabric.",
            "fabric_type": "Child MSD",
            "workflow": "Child MSD Workflow"
        }
        return result

    def handle_standard_workflow(self, task_vars):
        """Handle standard Non-MSD fabric workflow using existing logic"""
        self.logger.info("Starting standard Non-MSD workflow", operation="standard_workflow")

        try:
            result = super(ActionModule, self).run(task_vars=task_vars)

            if "fabric_type" not in result:
                result["fabric_type"] = "Standard"
                result["workflow"] = "Standard Non-MSD VRF Processing"

            self.logger.info("Standard workflow completed successfully", operation="standard_workflow")
            return result

        except Exception as e:
            return self.error_handler.handle_exception(e, "standard_workflow")

    # =========================================================================
    # CHILD FABRIC TASK MANAGEMENT
    # =========================================================================

    def create_child_task(self, parent_vrf, child_config, parent_module_args, child_tasks_dict):
        """Create child fabric task from parent VRF and child config"""
        try:
            child_fabric_name = child_config["fabric_name"]
            del child_config["fabric_name"]
            child_config["vrf_name"] = parent_vrf["vrf_name"]
            if "deploy" in parent_vrf:
                child_config["deploy"] = parent_vrf["deploy"]

            if child_tasks_dict.get(child_fabric_name):
                child_tasks_dict[child_fabric_name]["config"].append(child_config)
                child_tasks_dict[child_fabric_name]["vrf_list"].append(child_config["vrf_name"])
            else:
                child_task = {
                    "fabric": child_fabric_name,
                    "state": parent_module_args.get("state"),
                    "config": [child_config],
                    "vrf_list": [child_config["vrf_name"]]
                }
                child_tasks_dict[child_fabric_name] = child_task

            self.logger.debug(f"Created child task for VRF: {child_config['vrf_name']}",
                            fabric=child_fabric_name, operation="create_child_task")
            return child_tasks_dict

        except Exception as e:
            self.logger.error(f"Failed to create child task: {str(e)}", operation="create_child_task")
            raise

    def execute_child_task(self, child_task, task_vars):
        """Execute child fabric task using Child MSD flow"""
        fabric_name = child_task["fabric"]

        try:
            self.logger.info(f"Executing child task for fabric: {fabric_name}", fabric=fabric_name, operation="execute_child_task")

            child_module_args = {
                "fabric": fabric_name,
                "config": child_task["config"],
                "_fabric_type": "Child MSD"
            }

            state = child_task.get("state")
            if state:
                if state == "overridden":
                    child_module_args["state"] = "replaced"
                else:
                    child_module_args["state"] = state

            child_result = self.execute_module_with_args(child_module_args, task_vars)

            child_result["child_fabric"] = fabric_name
            child_result["invocation"] = {
                "module_args": copy.deepcopy(child_module_args)
            }

            success = not child_result.get("failed", False)
            self.logger.info(f"Child task execution completed: {'Success' if success else 'Failed'}",
                           fabric=fabric_name, operation="execute_child_task")
            return child_result

        except Exception as e:
            return self.error_handler.handle_exception(e, "execute_child_task", fabric_name)

    # =========================================================================
    # UTILITY & HELPER METHODS
    # =========================================================================

    def execute_module_with_args(self, module_args, task_vars):
        """Execute the dcnm_vrf module with given arguments"""
        fabric_name = module_args.get("fabric", "Unknown")
        original_args = self._task.args

        try:
            self.logger.debug("Executing DCNM VRF module", fabric=fabric_name, operation="execute_module")
            self._task.args = module_args
            result = super(ActionModule, self).run(task_vars=task_vars)

            result["invocation"] = {
                "module_args": copy.deepcopy(module_args)
            }

            success = not result.get("failed", False)
            self.logger.debug(f"Module execution completed: {'Success' if success else 'Failed'}",
                            fabric=fabric_name, operation="execute_module")
            return result

        except Exception as e:
            return self.error_handler.handle_exception(e, "execute_module", fabric_name)
        finally:
            self._task.args = original_args

    def wait_for_vrf_ready(self, vrf_list, fabric_name, task_vars, tmp):
        """Wait for VRFs to be in a deployable state"""
        if not vrf_list:
            return True, None

        vrf_oos_list = []
        retry_count = max(MAX_RETRY_COUNT // WAIT_TIME_FOR_DELETE_LOOP, 1)

        self.logger.info(f"Waiting for VRF(s) to be ready: {', '.join(vrf_list)}",
                        fabric=fabric_name, operation="wait_for_vrf_ready")

        while retry_count > 0 and vrf_list:
            try:
                resp = self._execute_module(
                    module_name="cisco.dcnm.dcnm_rest",
                    module_args={
                        "method": "GET",
                        "path": f"/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{fabric_name}/vrfs",
                    },
                    task_vars=task_vars,
                    tmp=tmp
                )

                response_data = self.error_handler.validate_api_response(resp, "VRF status check", fabric_name)
                vrf_data = response_data.get("DATA", [])

                for vrf in vrf_data:
                    vrf_name = vrf.get("vrfName")
                    if vrf_name in vrf_list:
                        vrf_status = vrf.get("vrfStatus")
                        if vrf_status in VALID_VRF_STATES:
                            vrf_list.remove(vrf_name)
                            self.logger.debug(f"VRF {vrf_name} is ready (status: {vrf_status})",
                                            fabric=fabric_name, operation="wait_for_vrf_ready")
                        elif vrf_status == "OUT-OF-SYNC":
                            if vrf not in vrf_oos_list:
                                vrf_oos_list.append(vrf)
                                self.logger.debug(f"VRF {vrf_name} is OUT-OF-SYNC",
                                                fabric=fabric_name, operation="wait_for_vrf_ready")
                            else:
                                vrf_list.remove(vrf_name)
                                self.logger.debug(f"VRF {vrf_name} removed after persistent OUT-OF-SYNC",
                                                fabric=fabric_name, operation="wait_for_vrf_ready")

                if vrf_list:
                    time.sleep(WAIT_TIME_FOR_DELETE_LOOP)
                    retry_count -= 1
                    self.logger.debug(f"VRF(s) still not ready: {', '.join(vrf_list)}, retries left: {retry_count}",
                                    fabric=fabric_name, operation="wait_for_vrf_ready")

            except Exception as e:
                self.logger.error(f"VRF readiness check failed: {str(e)}",
                                fabric=fabric_name, operation="wait_for_vrf_ready")
                return False, vrf_list

        if vrf_list:
            self.logger.warning(f"VRF(s) not ready after maximum retries: {', '.join(vrf_list)}",
                              fabric=fabric_name, operation="wait_for_vrf_ready")
            return False, vrf_list
        else:
            self.logger.info("All VRFs are ready", fabric=fabric_name, operation="wait_for_vrf_ready")
            return True, None

    def create_structured_results(self, parent_result, child_results, parent_fabric):
        """Create structured results combining parent and child fabric operations"""
        self.logger.debug("Creating structured results", fabric=parent_fabric, operation="create_structured_results")

        try:
            if child_results:
                structured_result = {
                    "changed": parent_result.get("changed", False),
                    "failed": parent_result.get("failed", False),
                    "fabric_type": "Parent MSD",
                    "workflow": "Parent MSD with Child Fabric Processing",
                    "parent_fabric": {
                        "fabric_name": parent_fabric,
                        "changed": parent_result.get("changed", False),
                        "diff": parent_result.get("diff", []),
                        "response": parent_result.get("response", [])
                    },
                    "child_fabrics": []
                }

                for child_result in child_results:
                    child_entry = {
                        "fabric_name": child_result.get("child_fabric"),
                        "changed": child_result.get("changed", False),
                        "failed": child_result.get("failed", False),
                        "diff": child_result.get("diff", []),
                        "response": child_result.get("response", [])
                    }
                    structured_result["child_fabrics"].append(child_entry)

                    if child_result.get("changed", False):
                        structured_result["changed"] = True

                    if child_result.get("failed", False):
                        structured_result["failed"] = True
                        structured_result["msg"] = f"Child fabric task failed for {child_result.get('child_fabric')}: {child_result.get('msg', 'Unknown error')}"

                return structured_result
            else:
                parent_result["fabric_type"] = "Parent MSD"
                parent_result["workflow"] = "Parent MSD without Child Fabric Processing"
                return parent_result

        except Exception as e:
            self.logger.error(f"Failed to create structured results: {str(e)}",
                            fabric=parent_fabric, operation="create_structured_results")
            return self.error_handler.handle_exception(e, "create_structured_results", parent_fabric)
