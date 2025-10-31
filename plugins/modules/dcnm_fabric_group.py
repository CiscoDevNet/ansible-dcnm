#!/usr/bin/python
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
"""
Manage creation, deletion, and update of fabric groups.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

DOCUMENTATION = """
---
module: dcnm_fabric_group
short_description: Manage creation, deletion, and update of fabric groups.
version_added: "3.8.0"
author: Allen Robel (@quantumonion)
description:
- Create, delete, update fabric groups.
options:
    state:
        choices:
        - deleted
        - merged
        - query
        - replaced
        default: merged
        description:
        - The state of the feature or object after module completion
        type: str
    skip_validation:
        default: false
        description:
        - Skip playbook parameter validation.  Useful for debugging.
        type: bool
    config:
        description:
        - A list of fabric configuration dictionaries
        type: list
        elements: dict
        suboptions:
            DEPLOY:
                default: False
                description:
                - Save and deploy the fabric configuration.
                required: false
                type: bool
            FABRIC_NAME:
                description:
                - The name of the fabric.
                required: true
                type: str
            FABRIC_TYPE:
                choices:
                - MCFG
                description:
                - The type of fabric group.
                required: true
                type: str
            MCFG_FABRIC_PARAMETERS:
                description:
                - Multi-cluster fabric-group specific parameters.
                - Domain that can contain multiple VXLAN EVPN Fabrics with Layer-2/Layer-3 Overlay Extensions and other Fabric Types.
                - The indentation of these parameters is meant only to logically group them.
                - They should be at the same YAML level as FABRIC_TYPE and FABRIC_NAME.
                suboptions:
                    ANYCAST_GW_MAC:
                        default: 2020.0000.00aa
                        description:
                        - Shared MAC address for all leaves
                        required: false
                        type: str
                    BGP_RP_ASN:
                        default: ''
                        description:
                        - 1-4294967295 | 1-65535.0-65535, e.g. 65000, 65001
                        required: false
                        type: str
                    BGW_ROUTING_TAG:
                        default: 54321
                        description:
                        - Routing tag associated with IP address of loopback and DCI interfaces
                        required: false
                        type: int
                    BORDER_GWY_CONNECTIONS:
                        choices:
                        - Manual
                        - Centralized_To_Route_Server
                        - Direct_To_BGWS
                        default: Manual
                        description:
                        - Manual, Auto Overlay EVPN Peering to Route Servers, Auto Overlay
                            EVPN Direct Peering to Border Gateways
                        required: false
                        type: str
                    CLOUDSEC_ALGORITHM:
                        default: AES_128_CMAC
                        description:
                        - AES_128_CMAC or AES_256_CMAC
                        required: false
                        type: str
                    CLOUDSEC_AUTOCONFIG:
                        default: false
                        description:
                        - Auto Config CloudSec on Border Gateways
                        required: false
                        type: bool
                    CLOUDSEC_ENFORCEMENT:
                        default: ''
                        description:
                        - If set to strict, data across site must be encrypted.
                        required: false
                        type: str
                    CLOUDSEC_KEY_STRING:
                        default: ''
                        description:
                        - Cisco Type 7 Encrypted Octet String
                        required: false
                        type: str
                    CLOUDSEC_REPORT_TIMER:
                        default: 5
                        description:
                        - CloudSec Operational Status periodic report timer in minutes
                        required: false
                        type: int
                    DCI_SUBNET_RANGE:
                        default: 10.10.1.0/24
                        description:
                        - Address range to assign P2P DCI Links
                        required: false
                        type: str
                    DCI_SUBNET_TARGET_MASK:
                        default: 30
                        description:
                        - 'Target Mask for Subnet Range '
                        required: false
                        type: int
                    DELAY_RESTORE:
                        default: 300
                        description:
                        - Multi-Site underlay and overlay control plane convergence time  in
                            seconds
                        required: false
                        type: int
                    ENABLE_BGP_BFD:
                        default: false
                        description:
                        - For auto-created Multi-Site Underlay IFCs
                        required: false
                        type: bool
                    ENABLE_BGP_LOG_NEIGHBOR_CHANGE:
                        default: false
                        description:
                        - For auto-created Multi-Site Underlay IFCs
                        required: false
                        type: bool
                    ENABLE_BGP_SEND_COMM:
                        default: false
                        description:
                        - For auto-created Multi-Site Underlay IFCs
                        required: false
                        type: bool
                    ENABLE_PVLAN:
                        default: false
                        description:
                        - Enable PVLAN on MSD and its child fabrics
                        required: false
                        type: bool
                    ENABLE_RS_REDIST_DIRECT:
                        default: false
                        description:
                        - For auto-created Multi-Site overlay IFCs in Route Servers. Applicable
                            only when Multi-Site Overlay IFC Deployment Method is Centralized_To_Route_Server.
                        required: false
                        type: bool
                    FABRIC_NAME:
                        default: ''
                        description:
                        - Please provide the fabric name to create it (Max Size 64)
                        required: false
                        type: str
                    L2_SEGMENT_ID_RANGE:
                        default: 30000-49000
                        description:
                        - 'Overlay Network Identifier Range '
                        required: false
                        type: str
                    L3_PARTITION_ID_RANGE:
                        default: 50000-59000
                        description:
                        - 'Overlay VRF Identifier Range '
                        required: false
                        type: str
                    LOOPBACK100_IP_RANGE:
                        default: 10.10.0.0/24
                        description:
                        - Typically Loopback100 IP Address Range
                        required: false
                        type: str
                    MS_IFC_BGP_AUTH_KEY_TYPE:
                        choices:
                        - 3
                        - 7
                        default: 3
                        description:
                        - 'BGP Key Encryption Type: 3 - 3DES, 7 - Cisco'
                        required: false
                        type: int
                    MS_IFC_BGP_PASSWORD:
                        default: ''
                        description:
                        - Encrypted eBGP Password Hex String
                        required: false
                        type: str
                    MS_IFC_BGP_PASSWORD_ENABLE:
                        default: false
                        description:
                        - eBGP password for Multi-Site underlay/overlay IFCs
                        required: false
                        type: bool
                    MS_LOOPBACK_ID:
                        default: 100
                        description:
                        - No description available
                        required: false
                        type: int
                    MS_UNDERLAY_AUTOCONFIG:
                        default: false
                        description:
                        - No description available
                        required: false
                        type: bool
                    RP_SERVER_IP:
                        default: ''
                        description:
                        - Multi-Site Route-Server peer list (typically loopback IP address
                            on Route-Server for Multi-Site EVPN peering with BGWs), e.g. 128.89.0.1,
                            128.89.0.2
                        required: false
                        type: str
                    RS_ROUTING_TAG:
                        default: 54321
                        description:
                        - Routing tag associated with Route Server IP for redistribute direct.
                            This is the IP used in eBGP EVPN peering.
                        required: false
                        type: int
                    TOR_AUTO_DEPLOY:
                        default: false
                        description:
                        - Enables Overlay VLANs on uplink between ToRs and Leafs
                        required: false
                        type: bool
                    default_network:
                        choices:
                        - Default_Network_Universal
                        - Service_Network_Universal
                        default: Default_Network_Universal
                        description:
                        - Default Overlay Network Template For Leafs
                        required: false
                        type: str
                    default_pvlan_sec_network:
                        choices:
                        - Pvlan_Secondary_Network
                        default: Pvlan_Secondary_Network
                        description:
                        - Default PVLAN Secondary Network Template
                        required: false
                        type: str
                    default_vrf:
                        choices:
                        - Default_VRF_Universal
                        default: Default_VRF_Universal
                        description:
                        - Default Overlay VRF Template For Leafs
                        required: false
                        type: str
                    enableScheduledBackup:
                        default: ''
                        description:
                        - 'Backup at the specified time. Note: Fabric Backup/Restore functionality
                            is being deprecated for MSD fabrics. Recommendation is to use
                            NDFC Backup & Restore'
                        required: false
                        type: bool
                    network_extension_template:
                        choices:
                        - Default_Network_Extension_Universal
                        default: Default_Network_Extension_Universal
                        description:
                        - Default Overlay Network Template For Borders
                        required: false
                        type: str
                    scheduledTime:
                        default: ''
                        description:
                        - Time (UTC) in 24hr format. (00:00 to 23:59)
                        required: false
                        type: str
                    vrf_extension_template:
                        choices:
                        - Default_VRF_Extension_Universal
                        default: Default_VRF_Extension_Universal
                        description:
                        - Default Overlay VRF Template For Borders
                        required: false
                        type: str

"""

EXAMPLES = """

# Create the following fabric groups with default configuration values
# if they don't already exist.  If they exist, the playbook will
# exit without doing anything.
# - 1. MCFG fabric

- name: Create fabric group
  cisco.dcnm.dcnm_fabric_group:
    state: merged
    config:
    -   FABRIC_NAME: MCFG
  register: result
- debug:
    var: result

# Update the above fabrics with additional configurations.

- name: Update fabric groups
  cisco.dcnm.dcnm_fabric_group:
    state: merged
    config:
    -   FABRIC_NAME: MCFG
        FABRIC_TYPE: MCFG
        ANYCAST_GW_MAC: 0001.aabb.ccdd
        BGP_RP_ASN: 65002
        BGW_ROUTING_TAG: 55555
        DEPLOY: true
  register: result
- debug:
    var: result

# Setting skip_validation to True to bypass parameter validation in the module.
# Note, this does not bypass parameter validation in NDFC.  skip_validation
# can be useful to verify that the dcnm_fabric module's parameter validation
# is disallowing parameter combinations that would also be disallowed by
# NDFC.

- name: Update fabrics
  cisco.dcnm.dcnm_fabric:
    state: merged
    skip_validation: True
    config:
    -   FABRIC_NAME: MCFG
        FABRIC_TYPE: MCFG
        ANYCAST_GW_MAC: 0001.aabb.ccdd
        DEPLOY: false

# Use replaced state to return the fabrics to their default configurations.

- name: Return fabrics to default configuration.
  cisco.dcnm.dcnm_fabric:
    state: replaced
    config:
    -   FABRIC_NAME: MCFG
        FABRIC_TYPE: MCFG
        DEPLOY: false
  register: result
- debug:
    var: result

# Query the fabrics to get their current configurations.

- name: Query the fabrics.
  cisco.dcnm.dcnm_fabric:
    state: query
    config:
    -   FABRIC_NAME: MCFG
  register: result
- debug:
    var: result

# Delete the fabric groups.

- name: Delete the fabric groups.
  cisco.dcnm.dcnm_fabric_group:
    state: deleted
    config:
    -   FABRIC_NAME: MCFG
  register: result
- debug:
    var: result

# When skip_validation is False (the default), some error messages might be
# misleading.  For example, with the playbook below, the error message
# that follows should be interpreted as "ENABLE_PVLAN is mutually-exclusive
# to ENABLE_SGT and should be removed from the playbook if ENABLE_SGT is set
# to True."  In the NDFC GUI, if Security Groups is enabled, NDFC disables
# the ability to modify the PVLAN option.  Hence, even a valid value for
# ENABLE_PVLAN in the playbook will generate an error.

-   name: merge fabric MyFabric
    cisco.dcnm.dcnm_fabric_group:
        state: merged
        skip_validation: false
        config:
        -   FABRIC_NAME: MCFG
            FABRIC_TYPE: MCFG
            ENABLE_SGT: true
            ENABLE_PVLAN: false

# Resulting error message (edited for brevity)
# "The following parameter(value) combination(s) are invalid and need to be reviewed: Fabric: f3, ENABLE_PVLAN(False) requires ENABLE_SGT != True."

"""
# pylint: disable=wrong-import-position, too-many-lines, too-many-instance-attributes
import copy
import inspect
import json
import logging
import traceback
from typing import Type, Union

from ansible.module_utils.basic import AnsibleModule  # type: ignore[import-untyped]

# Import guard for pydantic-dependent modules
try:
    from ..module_utils.common.controller_features_v2 import ControllerFeatures
    from ..module_utils.common.controller_version_v2 import ControllerVersion
    from ..module_utils.common.exceptions import ControllerResponseError
    from ..module_utils.common.log_v2 import Log
    from ..module_utils.common.response_handler import ResponseHandler
    from ..module_utils.common.rest_send_v2 import RestSend
    from ..module_utils.common.results_v2 import Results
    from ..module_utils.common.sender_dcnm import Sender
    from ..module_utils.common.template_get_v2 import TemplateGet
    from ..module_utils.fabric.verify_playbook_params import VerifyPlaybookParams
    from ..module_utils.fabric_group.common import FabricGroupCommon
    from ..module_utils.fabric_group.create import FabricGroupCreate
    from ..module_utils.fabric_group.delete import FabricGroupDelete
    from ..module_utils.fabric_group.fabric_group_types import FabricGroupTypes
    from ..module_utils.fabric_group.fabric_groups import FabricGroups
    from ..module_utils.fabric_group.query import FabricGroupQuery

    # from ..module_utils.fabric_group.replaced import FabricGroupReplaced
    from ..module_utils.fabric_group.update import FabricGroupUpdate

    HAS_PYDANTIC_DEPS = True
    PYDANTIC_DEPS_IMPORT_ERROR = None
except ImportError as imp_exc:
    HAS_PYDANTIC_DEPS = False
    PYDANTIC_DEPS_IMPORT_ERROR = traceback.format_exc()


def json_pretty(msg):
    """
    # Summary

    Return a pretty-printed JSON string for logging messages

    ## Raises

    None
    """
    return json.dumps(msg, indent=4, sort_keys=True)


# Use conditional base class to support import without pydantic
CommonBase: Type
if HAS_PYDANTIC_DEPS:
    CommonBase = FabricGroupCommon
else:
    CommonBase = object


class Common(CommonBase):
    """
    # Summary

    Common methods, properties, and resources for all states.

    ## Raises

    None
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        super().__init__()
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.params = params

        self.controller_features: ControllerFeatures = ControllerFeatures()
        self.controller_version: ControllerVersion = ControllerVersion()

        self.features = {}
        self._implemented_states = set()

        # populated in self.validate_input()
        self.payloads = {}

        self.populate_check_mode()
        self.populate_state()
        self.populate_config()

        self.rest_send: RestSend = RestSend(params=params)
        self.rest_send.response_handler = ResponseHandler()
        self.results: Results = Results()
        self.results.state = self.state
        self.results.check_mode = self.check_mode
        self._verify_playbook_params: VerifyPlaybookParams = VerifyPlaybookParams()

        self.have: FabricGroups = FabricGroups()
        self.query = []
        self.validated = []
        self.want: list[dict] = []

        msg = "ENTERED Common(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def populate_check_mode(self):
        """
        # Summary

        Populate ``check_mode`` with the playbook check_mode.

        ## Raises

        -   `ValueError` if check_mode is not provided.
        """
        method_name = inspect.stack()[0][3]
        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "check_mode is required."
            raise ValueError(msg)

    def populate_config(self):
        """
        # Summary

        Populate ``config`` with the playbook config.

        ## Raises

        -   `ValueError` if:
            -   ``state`` is "merged" or "replaced" and ``config`` is None.
            -   ``config`` is not a list.
        """
        method_name = inspect.stack()[0][3]
        states_requiring_config = {"merged", "replaced"}
        self.config: list[dict] = self.params.get("config", None)
        if self.state in states_requiring_config:
            if self.config is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += "params is missing config parameter."
                raise ValueError(msg)
            if not isinstance(self.config, list):
                msg = f"{self.class_name}.{method_name}: "
                msg += "expected list type for self.config. "
                msg += f"got {type(self.config).__name__}"
                raise ValueError(msg)

    def populate_state(self):
        """
        # Summary

        Populate ``state`` with the playbook state.

        ## Raises

        -   `ValueError` if:
            -   ``state`` is not provided.
            -   ``state`` is not a valid state.
        """
        method_name = inspect.stack()[0][3]

        valid_states = ["deleted", "merged", "query", "replaced"]

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params is missing state parameter."
            raise ValueError(msg)
        if self.state not in valid_states:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid state: {self.state}. "
            msg += f"Expected one of: {','.join(valid_states)}."
            raise ValueError(msg)

    def get_have(self):
        """
        # Summary

        Build `self.have`, which is the response from FabricGroupDetails containing the
        current controller fabric groups and their details.

        ## Raises

        - `ValueError` if the controller returns an error when attempting to
          retrieve the fabric details.

        ## have structure

        See FabricGroupDetails

        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        try:
            self.have.rest_send = self.rest_send
            self.have.results = Results()
            self.have.refresh()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Controller returned error when attempting to retrieve "
            msg += "fabric details. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def get_want(self) -> None:
        """
        # Summary

        -   Validate the playbook configs.
        -   Update self.want with the playbook configs.

        ## Raises

        -   `ValueError` if the playbook configs are invalid.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        merged_configs: list[dict] = []
        for config in self.config:
            try:
                self._verify_payload(config)
            except ValueError as error:
                raise ValueError(f"{error}") from error
            merged_configs.append(copy.deepcopy(config))

        self.want = []
        for config in merged_configs:
            self.want.append(copy.deepcopy(config))

    def get_controller_features(self) -> None:
        """
        # Summary

        -   Retrieve the state of relevant controller features
        -   Populate self.features
            -   key: FABRIC_TYPE
            -   value: True or False
                -   True if feature is started for this fabric type
                -   False otherwise

        ## Raises

        -   `ValueError` if the controller returns an error when attempting to
            retrieve the controller features.
        """
        method_name = inspect.stack()[0][3]
        self.features = {}
        self.controller_features.rest_send = self.rest_send
        try:
            self.controller_features.refresh()
        except ControllerResponseError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Controller returned error when attempting to retrieve "
            msg += "controller features. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        for fabric_group_type in self.fabric_group_types.valid_fabric_group_types:
            self.fabric_group_types.fabric_group_type = fabric_group_type
            self.controller_features.filter = self.fabric_group_types.feature_name
            self.features[fabric_group_type] = self.controller_features.started

    def get_controller_version(self):
        """
        # Summary

        Initialize and refresh self.controller_version.

        ## Raises

        -   `ValueError` if the controller returns an error when attempting
            to retrieve the controller version.
        """
        method_name = inspect.stack()[0][3]
        try:
            self.controller_version.rest_send = self.rest_send
            self.controller_version.refresh()
        except (ControllerResponseError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Controller returned error when attempting to retrieve "
            msg += "controller version. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error


class Deleted(Common):
    """
    # Summary

    Handle deleted state for fabric groups

    ## Raises

    None
    """

    def __init__(self, params) -> None:
        self.class_name: str = self.__class__.__name__
        super().__init__(params)

        self.action: str = "fabric_delete"
        self.delete: FabricGroupDelete = FabricGroupDelete()
        self._implemented_states.add("deleted")

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        msg = f"ENTERED {self.class_name}(): "
        msg += f"state: {self.results.state}, "
        msg += f"check_mode: {self.results.check_mode}"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        # Summary

        delete fabric groups in ``self.want`` that exist on the controller.

        ## Raises

        -   `ValueError` if the controller returns an error when attempting to
            delete the fabric groups.
        """
        self.get_want()
        method_name: str = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.delete.rest_send = self.rest_send
        self.delete.results = self.results

        fabric_group_names_to_delete: list = []
        for want in self.want:
            fabric_group_names_to_delete.append(want["FABRIC_NAME"])

        try:
            self.delete.fabric_group_names = fabric_group_names_to_delete
        except ValueError as error:
            raise ValueError(f"{error}") from error

        try:
            self.delete.commit()
        except ValueError as error:
            raise ValueError(f"{error}") from error


class Merged(Common):
    """
    # Summary

    Handle merged state.

    ## Raises

    -   `ValueError` if:
        -   The controller features required for the fabric type are not
            running on the controller.
        -   The playbook parameters are invalid.
        -   The controller returns an error when attempting to retrieve
            the template.
        -   The controller returns an error when attempting to retrieve
            the fabric details.
        -   The controller returns an error when attempting to create
            the fabric.
        -   The controller returns an error when attempting to update
            the fabric.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.action = "fabric_group_create"
        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        self.fabric_group_create: FabricGroupCreate = FabricGroupCreate()
        self.fabric_group_types: FabricGroupTypes = FabricGroupTypes()
        self.fabric_group_update: FabricGroupUpdate = FabricGroupUpdate()
        self.template: TemplateGet = TemplateGet()

        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.need_create: list = []
        self.need_update: list = []

        self._implemented_states.add("merged")

    def retrieve_template(self) -> None:
        """
        # Summary

        Retrieve the template for the fabric type in self.fabric_group_types.

        ## Raises

        -   `ValueError` if the controller returns an error when attempting to
            retrieve the template.
        """
        method_name = inspect.stack()[0][3]
        try:
            template_name = self.fabric_group_types.template_name
        except ValueError as error:
            raise ValueError(f"{error}") from error

        self.template.rest_send = self.rest_send
        self.template.template_name = template_name

        try:
            self.template.refresh()
        except ValueError as error:
            raise ValueError(f"{error}") from error
        except ControllerResponseError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Controller returned error when attempting to retrieve "
            msg += f"template: {template_name}. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def update_need_create(self, want) -> None:
        """
        # Summary

        -   Validate the playbook config in ``want`` for creation
        -   Append ``want`` to ``self.need_create``

        ## Raises

        -   `ValueError` if the playbook config in ``want`` is invalid.
        """
        method_name = inspect.stack()[0][3]
        try:
            self._verify_playbook_params.config_controller = None
        except TypeError as error:
            raise ValueError(f"{error}") from error

        if self.params.get("skip_validation") is False:
            try:
                self._verify_playbook_params.commit()
            except ValueError as error:
                raise ValueError(f"{error}") from error
        else:
            msg = f"{self.class_name}.{method_name}: "
            msg += "skip_validation: "
            msg += f"{self.params.get('skip_validation')}, "
            msg += "skipping parameter validation."
            self.log.debug(msg)

        self.need_create.append(want)

    def update_need_update(self, want) -> None:
        """
        # Summary

        -   Validate the playbook config in ``want`` for update
        -   Append ``want`` to ``self.need_update``

        ## Raises

        -   `ValueError` if the playbook config in ``want`` is invalid.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: ENTERED"
        self.log.debug(msg)
        fabric_name: str = want.get("FABRIC_NAME", "")
        if not fabric_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "FABRIC_NAME is required in config."
            raise ValueError(msg)
        nv_pairs = self.have.all_data[fabric_name]["nvPairs"]
        try:
            self._verify_playbook_params.config_controller = nv_pairs
        except TypeError as error:
            raise ValueError(f"{error}") from error
        if self.params.get("skip_validation") is False:
            try:
                self._verify_playbook_params.commit()
            except (ValueError, KeyError) as error:
                raise ValueError(f"{error}") from error
        else:
            msg = f"{self.class_name}.{method_name}: "
            msg += "skip_validation: "
            msg += f"{self.params.get('skip_validation')}, "
            msg += "skipping parameter validation."
            self.log.debug(msg)

        self.need_update.append(want)

    def get_need(self):
        """
        # Summary

        Build ``self.need`` for merged state.

        ## Raises

        -   `ValueError` if:
            -   The controller features required for the fabric type are not
                running on the controller.
            -   The playbook parameters are invalid.
            -   The controller returns an error when attempting to retrieve
                the template.
            -   The controller returns an error when attempting to retrieve
                the fabric group details.
        """
        method_name = inspect.stack()[0][3]
        self.payloads = {}
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        for want in self.want:

            fabric_name: str = want.get("FABRIC_NAME", "")
            fabric_type: str = want.get("FABRIC_TYPE", "")
            if not fabric_name:
                msg = f"{self.class_name}.{method_name}: "
                msg += "FABRIC_NAME is required in config."
                raise ValueError(msg)
            if not fabric_type:
                msg = f"{self.class_name}.{method_name}: "
                msg += "FABRIC_TYPE is required in config."
                raise ValueError(msg)

            is_4x = self.controller_version.is_controller_version_4x

            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_type: {fabric_type}, "
            msg += f"configurable: {self.features.get(fabric_type)}, "
            msg += f"is_4x: {is_4x}"
            self.log.debug(msg)

            if self.features.get(fabric_type) is False and is_4x is False:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Features required for fabric {fabric_name} "
                msg += f"of type {fabric_type} are not running on the "
                msg += "controller. Review controller settings at "
                msg += "Fabric Controller -> Admin -> System Settings -> "
                msg += "Feature Management"
                raise ValueError(msg)

            try:
                self._verify_playbook_params.config_playbook = want
            except TypeError as error:
                raise ValueError(f"{error}") from error

            try:
                self.fabric_group_types.fabric_group_type = fabric_type
            except ValueError as error:
                raise ValueError(f"{error}") from error

            self.retrieve_template()

            try:
                self._verify_playbook_params.template = self.template.template
            except TypeError as error:
                raise ValueError(f"{error}") from error

            # Append to need_create if the fabric does not exist.
            # Otherwise, append to need_update.
            if fabric_name not in self.have.fabric_group_names:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Fabric {fabric_name} does not exist on the controller. Will create."
                self.log.debug(msg)
                self.update_need_create(want)
            else:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Fabric {fabric_name} exists on the controller. Will update."
                self.log.debug(msg)
                self.update_need_update(want)

    def commit(self):
        """
        # Summary

        Commit the merged state request.

        ## Raises

        -   `ValueError` if:
            -   The controller features required for the fabric type are not
                running on the controller.
            -   The playbook parameters are invalid.
            -   The controller returns an error when attempting to retrieve
                the template.
            -   The controller returns an error when attempting to retrieve
                the fabric details.
            -   The controller returns an error when attempting to create
                the fabric.
            -   The controller returns an error when attempting to update
                the fabric.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        self.get_controller_version()

        self.get_controller_features()
        self.get_want()
        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.want: {json_pretty(self.want)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += "Calling get_have()"
        self.log.debug(msg)
        self.get_have()
        self.get_need()
        self.send_need_create()
        self.send_need_update()

    def send_need_create(self) -> None:
        """
        # Summary

        Build and send the payload to create fabrics specified in the playbook.

        ## Raises

        -   `ValueError` if:
            -   Any payload is invalid.
            -   The controller returns an error when attempting to create
                the fabric.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: entered. "
        msg += f"self.need_create: {json_pretty(self.need_create)}"
        self.log.debug(msg)

        if len(self.need_create) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No fabrics to create."
            self.log.debug(msg)
            return

        self.fabric_group_create.rest_send = self.rest_send
        self.fabric_group_create.results = self.results

        try:
            self.fabric_group_create.payloads = self.need_create
        except ValueError as error:
            raise ValueError(f"{error}") from error

        try:
            self.fabric_group_create.commit()
        except ValueError as error:
            raise ValueError(f"{error}") from error

    def send_need_update(self) -> None:
        """
        # Summary

        Build and send the payload to update fabric_groups specified in the playbook.

        ## Raises

        -   `ValueError` if:
            -   Any payload is invalid.
            -   The controller returns an error when attempting to update
                the fabric.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        msg = f"{self.class_name}.{method_name}: ENTERED. "
        msg += "self.need_update: "
        msg += f"{json_pretty(self.need_update)}"
        self.log.debug(msg)

        if len(self.need_update) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "No fabric_groups to update for merged state."
            self.log.debug(msg)
            return

        self.fabric_group_update.rest_send = self.rest_send
        self.fabric_group_update.results = self.results

        try:
            self.fabric_group_update.payloads = self.need_update
        except ValueError as error:
            raise ValueError(f"{error}") from error

        msg = f"{self.class_name}.{method_name}: "
        msg += "Calling self.fabric_group_update.commit()"
        self.log.debug(msg)

        try:
            self.fabric_group_update.commit()
        except ValueError as error:
            raise ValueError(f"{error}") from error


class Query(Common):
    """
    # Summary

    Handle query state.

    ## Raises

    -   `ValueError` if:
        -   The playbook parameters are invalid.
        -   The controller returns an error when attempting to retrieve
            the fabric group details.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)

        self.action = "fabric_group_query"
        self._implemented_states.add("query")

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED Query(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        # Summary

        Query the fabrics in `self.want` that exist on the controller.

        ## Raises

        -   `ValueError` if:
            -   Any fabric names are invalid.
            -   The controller returns an error when attempting to query the fabrics.
        """
        self.get_want()

        fabric_group_query = FabricGroupQuery()
        fabric_group_query.rest_send = self.rest_send
        fabric_group_query.results = self.results

        fabric_names_to_query = []
        for want in self.want:
            fabric_names_to_query.append(want["FABRIC_NAME"])
        try:
            fabric_group_query.fabric_group_names = copy.copy(fabric_names_to_query)
        except ValueError as error:
            raise ValueError(f"{error}") from error

        try:
            fabric_group_query.commit()
        except ValueError as error:
            raise ValueError(f"{error}") from error


def main():
    """
    # Summary

    main entry point for module execution.

    -   In the event that ``ValueError`` is raised, ``AnsibleModule.fail_json``
        is called with the error message.
    -   Else, ``AnsibleModule.exit_json`` is called with the final result.

    ## Raises

    -   `ValueError` if:
        -   The playbook parameters are invalid.
        -   The controller returns an error when attempting to
            delete, create, query, or update the fabrics.
    """

    argument_spec = {}
    argument_spec["config"] = {"required": False, "type": "list", "elements": "dict"}
    argument_spec["skip_validation"] = {
        "required": False,
        "type": "bool",
        "default": False,
    }
    argument_spec["state"] = {
        "default": "merged",
        "choices": ["deleted", "merged", "query", "replaced"],
    }

    ansible_module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    # Check for pydantic dependency before proceeding
    if not HAS_PYDANTIC_DEPS:
        ansible_module.fail_json(
            msg="The pydantic library is required to use this module. " "Install it with: pip install pydantic", exception=PYDANTIC_DEPS_IMPORT_ERROR
        )

    params = copy.deepcopy(ansible_module.params)
    params["check_mode"] = ansible_module.check_mode

    # Logging setup
    try:
        log = Log()
        log.commit()
    except ValueError as error:
        ansible_module.fail_json(str(error))

    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    if params.get("state") not in ["deleted", "merged", "query", "replaced"]:
        ansible_module.fail_json(f"Invalid state: {params['state']}")
    # task: Union[Deleted, Merged, Query, Replaced, None] = None
    task: Union[Deleted, Merged, Query, None] = None
    try:
        if params["state"] == "merged":
            task = Merged(params)
        elif params["state"] == "deleted":
            task = Deleted(params)
        elif params["state"] == "query":
            task = Query(params)
        # elif params["state"] == "replaced":
        #     task = Replaced(params)
    except ValueError as error:
        ansible_module.fail_json(f"Failed to initialize task: {error}")

    if task is None:
        ansible_module.fail_json("Task is None. Exiting.")
    else:
        # else is needed here since pylint doesn't understand fail_json
        # and thinks task can be None below.
        try:
            task.rest_send = rest_send
            task.commit()
            task.results.build_final_result()
        except ValueError as error:
            ansible_module.fail_json(f"{error}", **task.results.failed_result)

        # Results().failed is a property that returns a set()
        # of boolean values.  pylint doesn't seem to understand this so we've
        # disabled the unsupported-membership-test warning.
        if True in task.results.failed:  # pylint: disable=unsupported-membership-test
            msg = "Module failed."
            ansible_module.fail_json(msg, **task.results.final_result)
        ansible_module.exit_json(**task.results.final_result)


if __name__ == "__main__":
    main()
