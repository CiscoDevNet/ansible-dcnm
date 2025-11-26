# Copyright (c) 2020-2022 Cisco and/or its affiliates.
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
Action plugin for dcnm_network module with Multi-Site Domain (MSD) support.

This action plugin provides intelligent processing of network configurations across
MSD fabric hierarchies. It automatically detects fabric types and handles the complex
workflow of configuring networks on both parent and child fabrics in MSD environments.

Key Features:
- Automatic fabric type detection using NDFC fabric associations API
- MSD parent/child configuration validation and processing
- Intelligent config splitting for parent and child fabric operations
- Structured result aggregation for MSD workflows
- Fail-fast error handling with detailed error messages

Workflow Overview:
1. Detect fabric type (standalone, msd_parent, msd_child) via API
2. Validate MSD hierarchy rules and configuration constraints
3. Split unified config into separate parent/child configurations
4. Execute dcnm_network module for each fabric with appropriate parameters
5. Aggregate results into structured format for MSD operations

Supported Fabric Types:
- standalone: Regular fabric not part of MSD/MFD hierarchy
- multicluster_parent: Parent fabric in MFD domain (from OneManage API, fabricType='MFD')
- multicluster_child: Child/member fabric in MFD domain (from OneManage API)
- multisite_parent: Parent fabric in MSD domain (from fabric associations API, fabricState='msd', fabricParent='None')
- multisite_child: Child/member fabric in MSD domain (from fabric associations API, fabricState='member')

Author: Neil John
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
from ansible_collections.cisco.dcnm.plugins.module_utils.common.action_error_handler import (
    ActionErrorHandler as ErrorHandler,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.action_logger import (
    ActionLogger as Logger,
)
import json
import traceback

# Import new utility functions from dcnm module_utils

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    get_nd_version,
    obtain_federated_fabric_associations,
    obtain_fabric_associations
)

display = Display()


class ActionModule(ActionBase):
    """
    Action plugin for dcnm_network module with comprehensive MSD fabric support.

    This plugin extends the standard dcnm_network module to intelligently handle
    Multi-Site Domain (MSD) fabric configurations. It provides automatic fabric
    type detection, configuration validation, and orchestrated execution across
    parent and child fabrics.

    Core Responsibilities:
    1. Fabric Type Detection: Uses NDFC OneManage API (preferred) and fabric associations API
       to classify fabrics as standalone, multicluster_parent/child (MFD), or multisite_parent/child (MSD)

    2. Configuration Validation: Enforces MSD hierarchy rules and validates
       child_fabric_config parameters for correctness

    3. Configuration Processing: Transforms unified network configurations into
       separate parent and child fabric configurations with proper inheritance

    4. Execution Orchestration: Coordinates dcnm_network module execution across
       multiple fabrics with appropriate state transformations

    5. Result Aggregation: Structures execution results for both standalone and
       MSD workflows with comprehensive error handling

    MSD Configuration Features:
    - Automatic deploy flag inheritance from parent to child (no override allowed)
    - VRF and L2-only settings propagation to child fabrics
    - State transformation (parent 'overridden' becomes child 'replaced')
    - Attachment restriction enforcement (parent-only configuration)
    - Deploy flag restriction enforcement (parent-only configuration)
    - Comprehensive validation of fabric hierarchy relationships

    Error Handling:
    - Fail-fast execution with detailed error messages
    - Comprehensive validation before any execution begins
    - Structured error reporting with fabric context information
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display = Display()
        self.logger = Logger("NDFC_Network_ActionPlugin", self.display)
        self.error_handler = ErrorHandler(self.logger)
        self.logger.info("NDFC Network Action Plugin initialized")
        # Default NDFC version
        self.ndfc_version = 12.2

    def run(self, tmp=None, task_vars=None):
        """
        Main entry point for the action plugin.

        This method orchestrates the MSD fabric detection and processing workflow:
        1. Validates required parameters (fabric, state, config)
        2. Collects all fabrics needed from user config (parent + child fabrics)
        3. Attempts to get fabric info from OneManage API first (preferred)
        4. Falls back to fabric associations API for any missing fabrics
        5. Builds unified fabric info dictionary with only needed fabrics
        6. Validates and splits MSD parent/child configurations
        7. Executes network operations on parent and child fabrics

        Fabric Detection Strategy:
        - OneManage API is checked first for all fabrics (handles MFD parent/child)
        - Fabric associations API is only called if fabrics are missing from OneManage
        - Both APIs are normalized to same format: {type, fabricParent, cluster_name}

        Args:
            tmp (str, optional): Temporary directory path for file operations
            task_vars (dict, optional): Ansible task variables and context

        Returns:
            dict: Ansible result dictionary containing:
                - changed (bool): Whether any changes were made
                - failed (bool): Whether the operation failed
                - msg (str): Error message if failed
                - workflow (str): Type of workflow executed
                - parent_fabric (dict): Parent fabric results for MSD
                - child_fabrics (list): Child fabric results for MSD
        """
        if task_vars is None:
            task_vars = dict()

        result = dict(
            changed=False
        )

        # Get module arguments
        module_args = self._task.args.copy()
        fabric_name = module_args.get('fabric')

        if not fabric_name:
            result['failed'] = True
            result['msg'] = "fabric parameter is required"
            return result

        # Get ND version for API path selection (similar to dcnm_vrf)
        ndfc_version = get_nd_version(self, task_vars, tmp)
        display.vvv(f"ND version: {ndfc_version}")
        
        if ndfc_version is None:
            result['failed'] = True
            result['msg'] = (
                "Failed to get ND version from NDFC controller. "
                "The get_nd_version() function returned None. "
                "This could be due to: "
                "1) NDFC controller is unreachable, "
                "2) Authentication failure, "
                "3) API endpoints /fm/fmrest/about/version or /appcenter/cisco/ndfc/api/about/version are not responding with 200 status code, "
                "4) Version information in response is malformed. "
                "Please check your NDFC connectivity and credentials."
            )
            return result

        state = module_args.get('state')  # Get the state parameter
        if not state:
            result['failed'] = True
            result['msg'] = "The 'state' parameter is required"
            return result

        config = module_args.get('config')

        if not isinstance(config, list) or not config:
            # For 'query' and 'deleted', allow empty config (interpreted as all networks)
            if state in ['query', 'deleted']:
                config = []
            else:
                result['failed'] = True
                result['msg'] = f"The 'config' parameter must be a non-empty list for state '{state}'."
                return result

        # Collect all fabrics we need to check from the user config
        fabrics_needed = set([fabric_name])
        for net_config in config:
            child_fabric_configs = net_config.get('child_fabric_config', [])
            for child_config in child_fabric_configs:
                child_fabric_name = child_config.get('fabric')
                if child_fabric_name:
                    fabrics_needed.add(child_fabric_name)

        # Step 1: Get MFD fabrics from OneManage API (federated fabrics)
        display.vvv("="*80)
        display.vvv("Getting MFD fabrics from OneManage API")
        display.vvv("="*80)
        
        federated_fabrics = obtain_federated_fabric_associations(self, task_vars, tmp)
        if federated_fabrics is None:
            result['failed'] = True
            result['msg'] = "Failed to get federated fabric associations from OneManage API"
            return result

        display.vvv(f"Found {len(federated_fabrics)} MFD fabrics from OneManage API")

        # Build initial fabrics dict from MFD data
        fabrics = {}
        for fabric_name_key, fabric_data in federated_fabrics.items():
            fabric_type = fabric_data.get('fabricType')
            fabric_state = fabric_data.get('fabricState')
            
            # Determine fabric type based on fabricType and fabricState
            if fabric_type == 'MFD':
                # MFD parent fabric
                fabrics[fabric_name_key] = {
                    'type': 'multicluster_parent',
                    'fabricParent': 'None',
                    'cluster_name': ''
                }
            elif fabric_state == 'member':
                # MFD child/member fabric - need to find parent
                parent_fabric = None
                for parent_name, parent_data in federated_fabrics.items():
                    if parent_data.get('fabricType') == 'MFD':
                        members = parent_data.get('members', [])
                        for member in members:
                            if member.get('fabricName') == fabric_name_key:
                                parent_fabric = parent_name
                                break
                    if parent_fabric:
                        break
                
                fabrics[fabric_name_key] = {
                    'type': 'multicluster_child',
                    'fabricParent': parent_fabric if parent_fabric else 'None',
                    'cluster_name': fabric_data.get('clusterName', '')
                }
            else:
                # Other fabric types (standalone, etc.)
                fabrics[fabric_name_key] = {
                    'type': 'standalone',
                    'fabricParent': 'None',
                    'cluster_name': fabric_data.get('clusterName', '')
                }

        # Check which fabrics we need are missing from MFD data
        fabrics_found = set(fabrics.keys())
        missing_fabrics = fabrics_needed - fabrics_found

        # Step 2: If any fabrics are missing, check MSD fabric associations API
        if missing_fabrics:
            display.vvv("="*80)
            display.vvv(f"Missing {len(missing_fabrics)} fabrics from MFD: {missing_fabrics}")
            display.vvv("Checking MSD fabric associations API")
            display.vvv("="*80)
            
            msd_fabrics = obtain_fabric_associations(self, task_vars, tmp)
            if msd_fabrics is None:
                result['failed'] = True
                result['msg'] = "Failed to get MSD fabric associations"
                return result

            display.vvv(f"Found {len(msd_fabrics)} MSD fabrics from fabric associations API")

            # Process MSD fabrics and add missing ones
            for fabric_name_key, fabric_data in msd_fabrics.items():
                if fabric_name_key in missing_fabrics:
                    fabric_type = fabric_data.get('fabricType')
                    fabric_state = fabric_data.get('fabricState')
                    
                    # Determine fabric type based on fabricType and fabricState
                    if fabric_type == 'MSD' and fabric_state == 'msd':
                        # MSD parent fabric
                        fabrics[fabric_name_key] = {
                            'type': 'multisite_parent',
                            'fabricParent': 'None',
                            'cluster_name': ''
                        }
                    elif fabric_state == 'member':
                        # MSD child/member fabric - need to find parent
                        parent_fabric = None
                        for parent_name, parent_data in msd_fabrics.items():
                            if parent_data.get('fabricType') == 'MSD' and parent_data.get('fabricState') == 'msd':
                                members = parent_data.get('members', [])
                                for member in members:
                                    if member.get('fabricName') == fabric_name_key:
                                        parent_fabric = parent_name
                                        break
                            if parent_fabric:
                                break
                        
                        fabrics[fabric_name_key] = {
                            'type': 'multisite_child',
                            'fabricParent': parent_fabric if parent_fabric else 'None',
                            'cluster_name': ''
                        }
                    else:
                        # Unknown or other fabric types - mark as standalone
                        fabrics[fabric_name_key] = {
                            'type': 'standalone',
                            'fabricParent': 'None',
                            'cluster_name': ''
                        }

            # Check if there are still missing fabrics after MSD check
            fabrics_found = set(fabrics.keys())
            still_missing = fabrics_needed - fabrics_found

            # Step 3: Mark any remaining missing fabrics as standalone
            if still_missing:
                display.vvv("="*80)
                display.vvv(f"Fabrics not found in MFD or MSD APIs: {still_missing}")
                display.vvv("Marking them as standalone fabrics")
                display.vvv("="*80)
                
                for missing_fabric in still_missing:
                    fabrics[missing_fabric] = {
                        'type': 'standalone',
                        'fabricParent': 'None',
                        'cluster_name': ''
                    }

        # Log final fabric mapping
        display.vvv("="*80)
        display.vvv("Final fabric mapping:")
        display.vvv(json.dumps(fabrics, indent=2))
        display.vvv("="*80)

        # Validate fabric hierarchy before processing
        configs, error_msg = self._split_config(fabrics, fabric_name, config, state, result, ndfc_version)

        if configs is None:
            result['failed'] = True
            result['msg'] = error_msg
            return result

        # Execute fabric configurations
        execution_result = self._execute_fabric_configs(configs, module_args, result, task_vars, tmp)
        if execution_result:
            return execution_result

        return result

    def _get_fabric_details(self, fabric_name, fabrics):
        """
        Get fabric details from the unified fabric information dictionary.

        This method retrieves the fabric details (type and cluster_name) from the combined 
        fabric info dictionary which may contain data from OneManage API or fabric associations API.

        Classification Types:
        - multicluster_parent: MFD parent fabric (from OneManage API)
        - multicluster_child: MFD child/member fabric (from OneManage API)
        - multisite_parent: MSD parent fabric (from fabric associations API)
        - multisite_child: MSD child/member fabric (from fabric associations API)
        - standalone: Standalone fabric (not part of MSD/MFD)
        - unknown: Fabric not found or unrecognized type

        Args:
            fabric_name (str): Name of the fabric to get details for
            fabrics (dict): Combined fabric information dictionary

        Returns:
            dict: Fabric details dictionary containing:
                {
                    'fabric_type': 'multicluster_parent'|'multicluster_child'|'multisite_parent'|'multisite_child'|'standalone'|'unknown',
                    'cluster_name': 'cluster_name' or ''
                }
        """
        fabric_info = fabrics.get(fabric_name)
        if not fabric_info:
            return {
                'fabric_type': 'unknown',
                'cluster_name': ''
            }

        return {
            'fabric_type': fabric_info.get('type', 'unknown'),
            'cluster_name': fabric_info.get('cluster_name', '')
        }

    def _split_config(self, fabrics, fabric_name, config, state, result, ndfc_version):
        """
        Validate MSD fabric hierarchy and split network configurations for parent/child processing.

        This method performs comprehensive validation of MSD fabric relationships and transforms
        the unified network configuration into separate configurations for parent and child fabrics.
        It enforces MSD hierarchy rules and handles configuration inheritance.

        Validation Rules:
        1. Top-level fabric must not be a child (fabricParent is 'None')
        2. Child fabric configs must be members with correct parent relationship
        3. Child fabrics cannot contain 'attach' configurations (parent-only)
        4. Child fabrics cannot contain 'deploy' flag (must inherit from parent)
        5. Child fabric configurations must reference valid MSD member fabrics

        Configuration Processing:
        1. Split config into parent fabric config (without child_fabric_config) and
           separate child fabric configs (with only net_name and child-specific settings)
        2. State handling: If parent state is 'overridden', child state is set to 'replaced'.
           Child state is never 'overridden'.
        3. Deploy handling: Child fabrics always inherit the deploy flag from parent level.
           Users cannot specify deploy at child level (validation error thrown).
           Default to deploy=True if not specified at parent level.
        4. Automatic copying of is_l2only and vrf_name from parent to child

        Args:
            fabrics (dict): Fabric association information from _get_fabric_associations
            fabric_name (str): Top-level fabric name from playbook
            config (list): Network configuration list from playbook
            state (str): Ansible state parameter (merged, replaced, deleted, etc.)
            result (dict): Result dictionary to update with workflow information

        Returns:
            tuple: (list_of_fabric_configs, error_message)
                - list_of_fabric_configs (list): List of fabric configurations for execution
                - error_message (str): Error description if validation fails, None if successful

                Each fabric config has structure:
                {
                    'fabric': fabric_name,
                    '_fabric_details': {
                        'fabric_type': 'multisite_parent'|'multisite_child'|'standalone'|'unknown',
                        'cluster_name': 'cluster_name' or ''
                    },
                    'state': state,  # For parent: original state; For child: 'replaced' if parent state is 'overridden', otherwise original state
                    'config': [network_configs...]  # deploy defaults to True, child always inherits from parent
                }
        """
        # Check if top-level fabric exists in fabrics dict
        if fabric_name not in fabrics:
            return None, f"Top-level fabric '{fabric_name}' not found in fabric associations"

        top_level_fabric = fabrics[fabric_name]

        # Rule 1: Top-level fabric must not be a child (fabricParent is 'None')
        # Skip this check for query state since queries are read-only and should work on any fabric
        if state != 'query' and top_level_fabric['fabricParent'] != 'None':
            return None, f"Top-level fabric '{fabric_name}' cannot be a child fabric. " \
                f"It has parent '{top_level_fabric['fabricParent']}' but must have parent 'None'"

        # Rule 2: Validate child fabric configs and build child fabric configs
        child_fabric_configs_by_fabric = {}

        for net_config in config:
            # If parent state is 'deleted', discard child_fabric_config and continue
            if state == 'deleted':
                if 'child_fabric_config' in net_config:
                    del net_config['child_fabric_config']
                continue

            child_fabric_configs = net_config.get('child_fabric_config', [])

            # Check if child_fabric_config key is present but empty or has no value
            if 'child_fabric_config' in net_config and not child_fabric_configs:
                return None, (
                    f"Network '{net_config.get('net_name', 'unknown')}' has 'child_fabric_config' key "
                    "but no child fabric configurations provided. Either remove the key or provide "
                    "child fabric configurations."
                )

            if not child_fabric_configs:
                continue

            for child_config in child_fabric_configs:
                child_fabric_name = child_config.get('fabric')

                if not child_fabric_name:
                    return None, f"Child fabric config missing 'fabric' name in network '{net_config.get('net_name', 'unknown')}'"

                # Check if attach configuration is present in child fabric config
                if 'attach' in child_config:
                    return None, f"Child fabric config for '{child_fabric_name}' in network '{net_config.get('net_name', 'unknown')}' " \
                        "cannot contain 'attach' configuration. Attachments should only be configured on the parent fabric."

                # Check if deploy flag is present in child fabric config
                if 'deploy' in child_config:
                    return None, f"Child fabric config for '{child_fabric_name}' in network '{net_config.get('net_name', 'unknown')}' " \
                        "cannot contain 'deploy' flag. The deploy flag is automatically inherited from the parent fabric configuration."

                # Check if child fabric exists in fabrics dict
                if child_fabric_name not in fabrics:
                    return None, f"Child fabric '{child_fabric_name}' not found in fabric associations"

                child_fabric = fabrics[child_fabric_name]

                # Child fabric must be of type 'multisite_child' or 'multicluster_child'
                if child_fabric['type'] not in ['multisite_child', 'multicluster_child']:
                    return None, f"Child fabric '{child_fabric_name}' must be of type 'multisite_child' or 'multicluster_child' " \
                        f"but has type '{child_fabric['type']}'"

                # Child fabric's parent must be the top-level fabric
                if child_fabric['fabricParent'] != fabric_name:
                    return None, f"Child fabric '{child_fabric_name}' must have parent '{fabric_name}' " \
                        f"but has parent '{child_fabric['fabricParent']}'"

                # Build child fabric configs while validating
                if child_fabric_name not in child_fabric_configs_by_fabric:
                    child_fabric_configs_by_fabric[child_fabric_name] = []

                # Create child network config with only net_name and child-specific settings
                child_net_config = {
                    'net_name': net_config['net_name']
                }

                # Always copy is_l2only and vrf_name from parent to child
                if 'is_l2only' in net_config:
                    child_net_config['is_l2only'] = net_config['is_l2only']
                if 'vrf_name' in net_config:
                    child_net_config['vrf_name'] = net_config['vrf_name']

                # Always inherit deploy flag from parent level (default to True if not specified)
                if 'deploy' in net_config:
                    child_net_config['deploy'] = net_config['deploy']
                else:
                    child_net_config['deploy'] = True

                # Add all child-specific settings except 'fabric' and 'deploy'
                for key, value in child_config.items():
                    if key not in ['fabric', 'deploy']:
                        child_net_config[key] = value

                # Log the child network config with deploy attribute
                display.vvv(f"Child network config for '{child_fabric_name}' - Network '{net_config['net_name']}': deploy={child_net_config.get('deploy', 'NOT SET')}")

                child_fabric_configs_by_fabric[child_fabric_name].append(child_net_config)

        # Set default workflow to standalone
        result['workflow'] = 'Standalone'

        # Split configuration into separate fabric configs
        fabric_configs = []

        # 1. Create parent fabric config (remove child_fabric_config from each network)
        parent_config = []
        for net_config in config:
            parent_net = net_config.copy()

            # Set default deploy to True if not specified
            if 'deploy' not in parent_net:
                parent_net['deploy'] = True

            if 'child_fabric_config' in parent_net:
                del parent_net['child_fabric_config']
            parent_config.append(parent_net)

        parent_fabric_details = self._get_fabric_details(fabric_name, fabrics)
        # Add nd_version to fabric_details for module consumption (similar to dcnm_vrf)
        parent_fabric_details['nd_version'] = ndfc_version
        parent_fabric_config = {
            'fabric': fabric_name,
            '_fabric_details': parent_fabric_details,
            'state': state,
            'config': parent_config
        }
        fabric_configs.append(parent_fabric_config)

        # Update workflow if parent is MSD or MFD
        if parent_fabric_details['fabric_type'] in ['multisite_parent', 'multicluster_parent']:
            result['workflow'] = 'Parent MSD Processing without child fabric'

        # 2. Create fabric config for each child fabric
        for child_fabric_name, child_net_configs in child_fabric_configs_by_fabric.items():
            child_fabric_details = self._get_fabric_details(child_fabric_name, fabrics)
            # Add nd_version to child fabric_details for module consumption (similar to dcnm_vrf)
            child_fabric_details['nd_version'] = ndfc_version

            # Determine child fabric state: if parent state is 'overridden', child state should be 'replaced'
            # Child state should never be 'overridden'
            if state == 'overridden':
                child_state = 'replaced'
            else:
                child_state = state

            child_fabric_config = {
                'fabric': child_fabric_name,
                '_fabric_details': child_fabric_details,
                'state': child_state,
                'config': child_net_configs
            }
            fabric_configs.append(child_fabric_config)

            # Update workflow when child is detected
            if parent_fabric_details['fabric_type'] in ['multisite_parent', 'multicluster_parent']:
                result['workflow'] = 'Parent MSD with Child Fabric Processing'
            else:
                result['workflow'] = 'Child Fabric Processing'

        return fabric_configs, None

    def _execute_fabric_configs(self, configs, module_args, result, task_vars, tmp):
        """
        Execute dcnm_network module for each fabric configuration and aggregate results.

        This method orchestrates the execution of network operations across parent and child
        fabrics in the correct order. It handles different fabric types appropriately and
        aggregates results into a structured format for MSD operations.

        Execution Behavior:
        - Standalone fabrics: Returns module result exactly as-is (pass-through)
        - MSD fabrics: Executes parent first, then children, with aggregated results
        - Fail-fast: Stops on first error and returns failure immediately
        - Verbose logging: Displays detailed execution information in vvv mode

        Result Aggregation:
        - Standalone: Direct pass-through of module result
        - MSD: Structured output with separate parent_fabric and child_fabrics sections
        - Changed flag: Set if any fabric execution results in changes

        Args:
            configs (list): List of fabric configurations from _split_config
                Each config dict contains: fabric, _fabric_details (with fabric_type and cluster_name), state, config
            module_args (dict): Original Ansible module arguments from playbook
            result (dict): Base result dictionary to update with execution results
            task_vars (dict): Ansible task variables for module execution context
            tmp (str): Temporary directory path for module execution

        Returns:
            dict or None:
                - dict: Error result if execution fails (with failed=True, msg=error)
                - None: Successful execution (result dict is updated in-place)

        Side Effects:
            - Updates result['changed'] if any fabric execution changes
            - Updates result['parent_fabric'] for MSD parent results
            - Updates result['child_fabrics'] for MSD child results
            - Logs verbose execution details in vvv mode
        """

        # Track fabric results for new output structure
        parent_fabric_result = None
        child_fabric_results = []

        # Process each fabric config by calling the dcnm_network module
        for fabric_config in configs:
            fabric_details = fabric_config['_fabric_details']
            fabric_type = fabric_details['fabric_type']
            
            # Prepare module arguments for this fabric
            fabric_module_args = module_args.copy()
            fabric_module_args['fabric'] = fabric_config['fabric']
            fabric_module_args['state'] = fabric_config['state']
            fabric_module_args['config'] = fabric_config['config']
            fabric_module_args['_fabric_details'] = fabric_details  # Pass full fabric_details to module

            # Call the dcnm_network module for this fabric
            display.vvv(f"Processing fabric '{fabric_config['fabric']}' with {len(fabric_config['config'])} network(s)")

            # In vvv mode, display fabric and key attributes being pushed to module
            if display.verbosity >= 3:
                display.vvv(f"Fabric: {fabric_module_args['fabric']}")
                display.vvv(f"Fabric Type: {fabric_type}")
                display.vvv(f"Cluster Name: {fabric_details['cluster_name']}")
                display.vvv(f"State: {fabric_module_args['state']}")
                display.vvv("Networks being processed:")
                for i, net_config in enumerate(fabric_module_args['config'], 1):
                    net_name = net_config.get('net_name', 'unknown')
                    vrf_name = net_config.get('vrf_name', 'N/A')
                    net_id = net_config.get('net_id', 'auto')
                    vlan_id = net_config.get('vlan_id', 'auto')
                    deploy = net_config.get('deploy', True)
                    display.vvv(f"  {i}. {net_name} (VRF: {vrf_name}, Net ID: {net_id}, VLAN: {vlan_id}, Deploy: {deploy})")

            fabric_result = self._execute_module(
                module_name="cisco.dcnm.dcnm_network",
                module_args=fabric_module_args,
                task_vars=task_vars,
                tmp=tmp
            )

            # Show raw output in vvv mode
            if display.verbosity >= 3:
                display.vvv(f"Raw execution result for fabric '{fabric_config['fabric']}':")
                display.vvv(json.dumps(fabric_result, indent=2))

            # For standalone fabrics, return the module result exactly as-is
            if fabric_type == 'standalone':
                return fabric_result

            # FAIL FAST on first error
            if fabric_result.get('failed'):
                result['failed'] = True
                result['msg'] = (
                    f"Failed processing fabric '{fabric_config['fabric']}' "
                    f"({fabric_type}): {fabric_result.get('msg', 'Unknown error')}"
                )
                return result

            # Set overall changed flag if any fabric changed
            if fabric_result.get('changed'):
                result['changed'] = True
                display.vvv(f"Fabric '{fabric_config['fabric']}' execution resulted in changes")

            # Store results based on fabric type for new output structure
            if fabric_type in ['multisite_parent', 'multicluster_parent']:
                parent_fabric_result = {
                    'fabric_name': fabric_config['fabric'],
                    'changed': fabric_result.get('changed', False),
                    'failed': fabric_result.get('failed', False),
                    'response': fabric_result.get('response', []),
                    'diff': fabric_result.get('diff', [])
                }
            elif fabric_type in ['multisite_child', 'multicluster_child']:
                child_fabric_results.append({
                    'fabric_name': fabric_config['fabric'],
                    'changed': fabric_result.get('changed', False),
                    'failed': fabric_result.get('failed', False),
                    'response': fabric_result.get('response', []),
                    'diff': fabric_result.get('diff', [])
                })

        # Structure the final result based on what we processed
        if parent_fabric_result:
            result['parent_fabric'] = parent_fabric_result

        if child_fabric_results:
            result['child_fabrics'] = child_fabric_results

        return None
