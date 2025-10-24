#!/usr/bin/python
# -*- coding: utf-8 -*-

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
- standalone: Regular fabric not part of MSD hierarchy
- multisite_parent: Parent fabric in MSD domain (fabricState='msd', fabricParent='None')
- multisite_child: Child/member fabric in MSD domain (fabricState='member')

Author: Neil John
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
import json

display = Display()


class ActionModule(ActionBase):
    """
    Action plugin for dcnm_network module with comprehensive MSD fabric support.
    
    This plugin extends the standard dcnm_network module to intelligently handle
    Multi-Site Domain (MSD) fabric configurations. It provides automatic fabric
    type detection, configuration validation, and orchestrated execution across
    parent and child fabrics.
    
    Core Responsibilities:
    1. Fabric Type Detection: Uses NDFC fabric associations API to automatically
       classify fabrics as standalone, multisite_parent, or multisite_child
       
    2. Configuration Validation: Enforces MSD hierarchy rules and validates
       child_fabric_config parameters for correctness
       
    3. Configuration Processing: Transforms unified network configurations into
       separate parent and child fabric configurations with proper inheritance
       
    4. Execution Orchestration: Coordinates dcnm_network module execution across
       multiple fabrics with appropriate state transformations
       
    5. Result Aggregation: Structures execution results for both standalone and
       MSD workflows with comprehensive error handling
    
    MSD Configuration Features:
    - Automatic deploy flag inheritance from parent to child (with override)
    - VRF and L2-only settings propagation to child fabrics
    - State transformation (parent 'overridden' becomes child 'replaced')
    - Attachment restriction enforcement (parent-only configuration)
    - Comprehensive validation of fabric hierarchy relationships
    
    Error Handling:
    - Fail-fast execution with detailed error messages
    - Comprehensive validation before any execution begins
    - Structured error reporting with fabric context information
    """

    def run(self, tmp=None, task_vars=None):
        """
        Main entry point for the action plugin.
        
        This method orchestrates the MSD fabric detection and processing workflow:
        1. Validates required parameters
        2. Detects fabric type using NDFC fabric associations API
        3. Validates and splits MSD parent/child configurations
        4. Executes network operations on parent and child fabrics
        
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

        # Detect fabric type using fabric associations API
        fabrics = self._get_fabric_associations(task_vars)
        
        if fabrics is None:
            result['failed'] = True
            result['msg'] = f"Failed to get fabric associations"
            return result

        # Validate fabric hierarchy before processing

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
        
        configs, error_msg = self._split_config(fabrics, fabric_name, config, state, result)
        
        if configs is None:
            result['failed'] = True
            result['msg'] = error_msg
            return result
        
        # Execute fabric configurations
        execution_result = self._execute_fabric_configs(configs, module_args, result, task_vars, tmp)
        if execution_result:
            return execution_result
        
        return result

    def _get_fabric_associations(self, task_vars):
        """
        Retrieve fabric association information from NDFC using the MSD fabric associations API.
        
        This method calls the NDFC REST API to get information about all fabrics and their
        MSD (Multi-Site Domain) relationships. The API returns fabric state and parent
        information needed to determine fabric type classification.
        
        Args:
            task_vars (dict): Ansible task variables for API authentication and context
            
        Returns:
            dict or None: Dictionary mapping fabric names to their association info:
                {
                    'fabric_name': {
                        'fabricState': 'msd'|'member'|'standalone',
                        'fabricParent': 'parent_name' or 'None'
                    }
                }
                Returns None if API call fails.
                
        API Endpoint:
            GET /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/msd/fabric-associations
        """

        # Use the fabric associations API to get MSD fabric information
        msd_fabric_associations = self._execute_module(
            module_name="cisco.dcnm.dcnm_rest",
            module_args={
                "method": "GET",
                "path": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/msd/fabric-associations",
            },
            task_vars=task_vars
        )
        # Check if the API call was successful
        if msd_fabric_associations.get('failed'):
            display.error(f"Fabric associations API call failed")
            return
        
        msd_fabric_associations = msd_fabric_associations.get('response', {}).get('DATA', {})
        fabrics = {}
        for fabric in msd_fabric_associations:
            fabrics[fabric['fabricName']] = {
                'fabricState': fabric['fabricState'],
                'fabricParent': fabric['fabricParent']
            }

        return fabrics

    def _get_fabric_type(self, fabric_name, fabrics):
        """
        Classify fabric type based on MSD fabric association information.
        
        This method analyzes the fabric state and parent relationship to determine
        the correct fabric classification for MSD processing logic.
        
        Classification Rules:
        - multisite_child: fabricState='member' (child fabric in MSD)
        - multisite_parent: fabricState='msd' AND fabricParent='None' (parent fabric in MSD)
        - standalone: fabricState='standalone' (not part of MSD)
        - unknown: fabric not found or unrecognized state
        
        Args:
            fabric_name (str): Name of the fabric to classify
            fabrics (dict): Fabric association information from _get_fabric_associations
            
        Returns:
            str: Fabric type classification:
                - 'multisite_parent': MSD parent fabric
                - 'multisite_child': MSD child/member fabric
                - 'standalone': Standalone fabric (not MSD)
                - 'unknown': Fabric not found or unrecognized state
        """
        fabric_info = fabrics.get(fabric_name)
        if not fabric_info:
            return 'unknown'
        
        fabric_state = fabric_info.get('fabricState')
        fabric_parent = fabric_info.get('fabricParent')
        
        if fabric_state == 'member':
            return 'multisite_child'
        elif fabric_state == 'msd' and fabric_parent == 'None':
            return 'multisite_parent'
        elif fabric_state == 'standalone':
            return 'standalone'
        else:
            return 'unknown'

    def _split_config(self, fabrics, fabric_name, config, state, result):
        """
        Validate MSD fabric hierarchy and split network configurations for parent/child processing.
        
        This method performs comprehensive validation of MSD fabric relationships and transforms
        the unified network configuration into separate configurations for parent and child fabrics.
        It enforces MSD hierarchy rules and handles configuration inheritance.
        
        Validation Rules:
        1. Top-level fabric must not be a child (fabricParent is 'None')
        2. Child fabric configs must be members with correct parent relationship
        3. Child fabrics cannot contain 'attach' configurations (parent-only)
        4. Child fabric configurations must reference valid MSD member fabrics
        
        Configuration Processing:
        1. Split config into parent fabric config (without child_fabric_config) and
           separate child fabric configs (with only net_name and child-specific settings)
        2. State handling: If parent state is 'overridden', child state is set to 'replaced'.
           Child state is never 'overridden'.
        3. Deploy handling: Both parent and child default to deploy=True. Child-level config
           takes priority over parent-level config.
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
                    '_fabric_type': fabric_type,  # 'multisite_parent', 'multisite_child', 'standalone', or 'unknown'
                    'state': state,  # For parent: original state; For child: 'replaced' if parent state is 'overridden', otherwise original state
                    'config': [network_configs...]  # deploy defaults to True, child-level takes priority
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
                return None, f"Network '{net_config.get('net_name', 'unknown')}' has 'child_fabric_config' key but no child fabric configurations provided. Either remove the key or provide child fabric configurations."
            
            if not child_fabric_configs:
                continue
                
            for child_config in child_fabric_configs:
                child_fabric_name = child_config.get('fabric')
                
                if not child_fabric_name:
                    return None, f"Child fabric config missing 'fabric' name in network '{net_config.get('net_name', 'unknown')}'"
                
                # Check if attach configuration is present in child fabric config
                if 'attach' in child_config:
                    return None, f"Child fabric config for '{child_fabric_name}' in network '{net_config.get('net_name', 'unknown')}' " \
                                 f"cannot contain 'attach' configuration. Attachments should only be configured on the parent fabric."
                
                # Check if child fabric exists in fabrics dict
                if child_fabric_name not in fabrics:
                    return None, f"Child fabric '{child_fabric_name}' not found in fabric associations"
                
                child_fabric = fabrics[child_fabric_name]
                
                # Child fabric must be in 'member' state
                if child_fabric['fabricState'] != 'member':
                    return None, f"Child fabric '{child_fabric_name}' must have fabricState 'member' " \
                                 f"but has '{child_fabric['fabricState']}'"
                
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
                
                # Handle deploy flag: child-level takes priority, default to True
                if 'deploy' in child_config:
                    child_net_config['deploy'] = child_config['deploy']
                elif 'deploy' in net_config:
                    child_net_config['deploy'] = net_config['deploy']
                else:
                    child_net_config['deploy'] = True
                
                # Add all child-specific settings except 'fabric'
                for key, value in child_config.items():
                    if key != 'fabric':
                        child_net_config[key] = value
                
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
        
        parent_fabric_type = self._get_fabric_type(fabric_name, fabrics)
        parent_fabric_config = {
            'fabric': fabric_name,
            '_fabric_type': parent_fabric_type,
            'state': state,
            'config': parent_config
        }
        fabric_configs.append(parent_fabric_config)
        
        # Update workflow if parent is MSD
        if parent_fabric_type == 'multisite_parent':
            result['workflow'] = 'Parent MSD Processing without child fabric'
        
        # 2. Create fabric config for each child fabric
        for child_fabric_name, child_net_configs in child_fabric_configs_by_fabric.items():
            child_fabric_type = self._get_fabric_type(child_fabric_name, fabrics)
            
            # Determine child fabric state: if parent state is 'overridden', child state should be 'replaced'
            # Child state should never be 'overridden'
            if state == 'overridden':
                child_state = 'replaced'
            else:
                child_state = state
            
            child_fabric_config = {
                'fabric': child_fabric_name,
                '_fabric_type': child_fabric_type,
                'state': child_state,
                'config': child_net_configs
            }
            fabric_configs.append(child_fabric_config)
            
            # Update workflow when child is detected
            if parent_fabric_type == 'multisite_parent':
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
                Each config dict contains: fabric, _fabric_type, state, config
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
            # Prepare module arguments for this fabric
            fabric_module_args = module_args.copy()
            fabric_module_args['fabric'] = fabric_config['fabric']
            fabric_module_args['state'] = fabric_config['state']
            fabric_module_args['config'] = fabric_config['config']
            fabric_module_args['_fabric_type'] = fabric_config['_fabric_type']
            
            # Call the dcnm_network module for this fabric
            display.vvv(f"Processing fabric '{fabric_config['fabric']}' with {len(fabric_config['config'])} network(s)")
            
            # In vvv mode, display fabric and key attributes being pushed to module
            if display.verbosity >= 3:
                display.vvv(f"Fabric: {fabric_module_args['fabric']}")
                display.vvv(f"Fabric Type: {fabric_module_args['_fabric_type']}")
                display.vvv(f"State: {fabric_module_args['state']}")
                display.vvv(f"Networks being processed:")
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
            if fabric_config['_fabric_type'] == 'standalone':
                return fabric_result

            # FAIL FAST on first error
            if fabric_result.get('failed'):
                result['failed'] = True
                result['msg'] = f"Failed processing fabric '{fabric_config['fabric']}' ({fabric_config['_fabric_type']}): {fabric_result.get('msg', 'Unknown error')}"
                return result
            
            # Set overall changed flag if any fabric changed
            if fabric_result.get('changed'):
                result['changed'] = True
                display.vvv(f"Fabric '{fabric_config['fabric']}' execution resulted in changes")
            
            # Store results based on fabric type for new output structure
            if fabric_config['_fabric_type'] == 'multisite_parent':
                parent_fabric_result = {
                    'fabric_name': fabric_config['fabric'],
                    'changed': fabric_result.get('changed', False),
                    'failed': fabric_result.get('failed', False),
                    'response': fabric_result.get('response', []),
                    'diff': fabric_result.get('diff', [])
                }
            elif fabric_config['_fabric_type'] == 'multisite_child':
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