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
from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Prabahal"

DOCUMENTATION = """
---
module: dcnm_fabric_member
short_description: Manage addition and deletion of NDFC fabrics to MSD.
version_added: "3.5.0"
author: Prabahal (@prabahal)
description:
- Create, Delete, Query NDFC child fabrics.
options:
    state:
        choices:
        - deleted
        - merged
        - query
        default: merged
        description:
        - The state of the feature or object after module completion
        type: str
    config:
        description:
        - A list of fabric configuration dictionaries
        type: list
        elements: dict
        suboptions:
            DEPLOY:
                default: False
                description:
                - Save the member fabric configuration.
                required: false
                type: bool
            FABRIC_NAME:
                description:
                - The name of the MSD fabric.
                required: true
                type: str
            CHILD_FABRIC_NAME:
                description:
                - The child fabric of MSD fabric.
                required: true
                type: str
"""

EXAMPLES = """

- name: add child fabrics to MSD
  cisco.dcnm.dcnm_fabric_member:
    state: merged
    config:
    -   FABRIC_NAME: MSD_Parent1
        CHILD_FABRIC_NAME: child1
    -   FABRIC_NAME: MSD_Parent2
        CHILD_FABRIC_NAME: child2
    -   FABRIC_NAME: MSD_Parent2
        CHILD_FABRIC_NAME: child3
  register: result
- debug:
    var: result

# Query the child fabrics of a MSD Fabric.

- name: Query the child fabrics of MSD fabrics.
  cisco.dcnm.dcnm_fabric_member:
    state: query
    config:
    -   FABRIC_NAME: MSD_Fabric1
    -   FABRIC_NAME: MSD_Fabric2
    -   FABRIC_NAME: MSD_Fabric3
  register: result
- debug:
    var: result

# Delete the fabrics.

- name: Delete the fabrics.
  cisco.dcnm.dcnm_fabric:
    state: deleted
    config:
    -   FABRIC_NAME: MSD_Parent1
        CHILD_FABRIC_NAME: child1
    -   FABRIC_NAME: MSD_Parent2
        CHILD_FABRIC_NAME: child2
  register: result
- debug:
    var: result

"""
# pylint: disable=wrong-import-position
import copy
import inspect
import logging

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.common.controller_version import ControllerVersion
from ..module_utils.common.exceptions import ControllerResponseError
from ..module_utils.common.log_v2 import Log
from ..module_utils.common.properties import Properties
from ..module_utils.common.response_handler import ResponseHandler
from ..module_utils.common.rest_send_v2 import RestSend
from ..module_utils.common.results import Results
from ..module_utils.common.sender_dcnm import Sender
from ..module_utils.common.conversion import ConversionUtils
from ..module_utils.msd.query_child_fab import childFabricQuery
from ..module_utils.msd.delete_child_fab import childFabricDelete
from ..module_utils.msd.add_child_fab import childFabricAdd
from ..module_utils.msd.fabric_associations import FabricAssociations
from ..module_utils.network.dcnm.dcnm import validate_list_of_dicts


@Properties.add_rest_send
class childCommon():
    """
    Common methods, properties, and resources for all states.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.controller_version = ControllerVersion()
        self.features = {}
        self._implemented_states = set()

        self.params = params

        self.populate_check_mode()
        self.populate_state()
        self.populate_config()

        self.results = Results()
        self.results.state = self.state
        self.results.check_mode = self.check_mode
        self.conversion = ConversionUtils()
        self.payloads = []
        self.want = []

        msg = "ENTERED Common(): "
        msg += f"{method_name}: state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def verify_msd_fab_exists_in_controller(self):
        method_name = inspect.stack()[0][3]
        for item in self.payloads:
            for fabric in self.data:
                if fabric == item["destFabric"]:
                    break
            else:
                invalid_fab = item["destFabric"]
                msg = f"{self.class_name}: {method_name}: "
                msg += f"Playbook configuration for FABRIC_NAME {invalid_fab} "
                msg += "is not found in Controller. Please create and try again"
                raise ValueError(msg)

    def verify_msd_fab_type(self):
        method_name = inspect.stack()[0][3]
        for item in self.payloads:
            for fabric in self.data:
                if fabric == item["destFabric"]:
                    if (self.data[fabric]['fabricType'] != "MSD"):
                        invalid_fab = item["destFabric"]
                        msg = f"{self.class_name}: {method_name}: "
                        msg += f"Playbook configuration for FABRIC_NAME {invalid_fab} "
                        msg += "is not of type MSD"
                        raise ValueError(msg)

    def verify_child_fab_exists_in_controller(self):
        method_name = inspect.stack()[0][3]
        for item in self.payloads:
            for fabric in self.data:
                if fabric == item["sourceFabric"]:
                    break
            else:
                invalid_fab = item["sourceFabric"]
                msg = f"{self.class_name}: {method_name}: "
                msg += f"Playbook configuration for CHILD_FABRIC_NAME {invalid_fab} "
                msg += "is not found in Controller. Please create and try again"
                raise ValueError(msg)

    def verify_child_fabric_is_member_of_another_fabric(self):
        for item in self.payloads:
            for fabric in self.data:
                if fabric == item["sourceFabric"]:
                    if (self.data[fabric]['fabricParent'] != item["destFabric"]) \
                            and (self.data[fabric]['fabricParent'] != "None"):
                        inv_child_fab = item["sourceFabric"]
                        another_fab = self.data[fabric]['fabricParent']
                        msg = f"Invalid Operation: Child fabric {inv_child_fab} "
                        msg += f"is member of another Fabric {another_fab}."
                        self.log.debug(msg)
                        raise ValueError(msg)

    def verify_child_fabric_is_already_member(self, item) -> bool:
        for fabric in self.data:
            if fabric == item["sourceFabric"]:
                if (self.data[fabric]['fabricParent'] == item["destFabric"]):
                    return True
        return False

    def validate_input(self):
        method_name = inspect.stack()[0][3]
        fab_member_spec = dict(
            FABRIC_NAME=dict(required=True, type="str"),
            CHILD_FABRIC_NAME=dict(required=True, type="str"),
            DEPLOY=dict(type="bool", default=False),
        )
        fab_mem_info, invalid_params = validate_list_of_dicts(self.config, fab_member_spec, None)
        if invalid_params:
            msg = "Invalid parameters in playbook: {invalid_params}"
            msg += "while processing config \n"
            raise ValueError(msg)
        for config in self.config:
            if not isinstance(config, dict):
                msg = f"{self.class_name}.{method_name}: "
                msg += "Playbook configuration for fabric_member must be a dict. "
                msg += f"Got type {type(config).__name__}, "
                msg += f"value {config}."
                raise ValueError(msg)
            msd_fabric = config.get("FABRIC_NAME", None)
            child_fabric = config.get("CHILD_FABRIC_NAME", None)
            try:
                self.conversion.validate_fabric_name(msd_fabric)
                self.conversion.validate_fabric_name(child_fabric)
            except (TypeError, ValueError) as error:
                msg = f"{self.class_name}: "
                msg += "Playbook configuration for FABRIC_NAME or CHILD_FABRIC_NAME "
                msg += "contains an invalid FABRIC_NAME. "
                # error below already contains a period "." at the end
                msg += f"Error detail: {error} "
                msg += f"Bad configuration: {config}."
                raise ValueError(msg) from error

    def get_want(self):
        method_name = inspect.stack()[0][3]
        for config in self.config:
            msg = f"{method_name} payload: {config}"
            self.log.debug(msg)
            msd_fabric = config.get("FABRIC_NAME", None)
            child_fabric = config.get("CHILD_FABRIC_NAME", None)
            deploy = config.get("DEPLOY", None)
            config_payload = {'destFabric': msd_fabric, 'sourceFabric': child_fabric, 'DEPLOY': deploy}
            self.payloads.append(copy.deepcopy(config_payload))

    def populate_check_mode(self):
        """
        ### Summary
        Populate ``check_mode`` with the playbook check_mode.

        ### Raises
        -   ValueError if check_mode is not provided.
        """
        method_name = inspect.stack()[0][3]
        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "check_mode is required."
            raise ValueError(msg)

    def populate_config(self):
        """
        ### Summary
        Populate ``config`` with the playbook config.

        ### Raises
        -   ValueError if:
                -   ``state`` is "merged" or "deleted" and ``config`` is None.
                -   ``config`` is not a list.
        """
        method_name = inspect.stack()[0][3]
        states_requiring_config = {"merged", "deleted"}
        self.config = self.params.get("config", None)
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
        ### Summary
        Populate ``state`` with the playbook state.

        ### Raises
        -   ValueError if:
                -   ``state`` is not provided.
                -   ``state`` is not a valid state.
        """
        method_name = inspect.stack()[0][3]

        valid_states = ["deleted", "merged", "query"]

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

# Keeping this function to check lower NDFC version support. yet to get data from Mike
    def get_controller_version(self):
        """
        ### Summary
        Initialize and refresh self.controller_version.

        ### Raises

        -   ``ValueError`` if the controller returns an error when attempting
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


class Deleted(childCommon):
    """
    ### Summary
    Handle deleted state
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)

        self.action = "child_fabric_delete"
        self._implemented_states.add("deleted")

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED child fabric Deleted(): "
        msg += f"state: {self.results.state}, "
        msg += f"check_mode: {self.results.check_mode}"
        self.log.debug(msg)
        self.data = {}

    def commit(self) -> None:
        """
        ### Summary
        delete the fabrics in ``self.want`` that exist on the controller.

        ### Raises

        -   ``ValueError`` if the controller returns an error when attempting to
            delete the fabrics.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}"
        self.log.debug(msg)
        self.validate_input()
        self.get_want()

        self.fab_association = FabricAssociations()
        self.fab_association.rest_send = self.rest_send
        self.fab_association.refresh()
        msg = f"Fab association data{self.fab_association.fabric_association_data}"
        self.log.debug(msg)
        for item in self.fab_association.fabric_association_data:
            fabric_name = item.get("fabricName", None)
            if fabric_name is None:
                continue
            self.data[fabric_name] = item

        self.verify_msd_fab_exists_in_controller()
        self.verify_msd_fab_type()
        for item in self.payloads:
            if not self.verify_child_fabric_is_already_member(item):
                self.results.action = self.action
                self.results.result_current = {"success": True, "changed": False}
                msg = "Given child fabric is already not a member of MSD fabric"
                self.results.response_current = {"RETURN_CODE": 200, "MESSAGE": msg}
                self.results.register_task_result()
            else:
                self.delete = childFabricDelete()
                self.delete.rest_send = self.rest_send
                self.delete.results = self.results

                fabric_names_to_delete = []
                for want in self.payloads:
                    fabric_names_to_delete.append(want["sourceFabric"])
                    fabric_names_to_delete.append(want["destFabric"])
                try:
                    self.delete.fabric_names = fabric_names_to_delete
                except ValueError as error:
                    raise ValueError(f"{error}") from error

                try:
                    self.delete.commit(item)
                except ValueError as error:
                    raise ValueError(f"{error}") from error


class Merged(childCommon):
    """
    ### Summary
    Handle merged state for adding the child Fabrics.

    ### Raises

    -   ``ValueError`` if:
        -   The controller features required for the fabric type are not
            running on the controller.
        -   The playbook parameters are invalid.
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

        self.action = "child_fabric_add"
        self._implemented_states.add("merged")

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.add = childFabricAdd()
        msg = "ENTERED child fabric merged(): "
        msg += f"state: {self.results.state}, "
        msg += f"check_mode: {self.results.check_mode}"
        self.log.debug(msg)
        self.data = {}

    def commit(self) -> None:
        """
        ### Summary
        Add the fabrics in ``self.payloads`` that exist on the controller.

        ### Raises

        -   ``ValueError`` if the controller returns an error when attempting to
            add the fabrics.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}"
        self.log.debug(msg)
        self.get_controller_version()
        # Version validation needs to be added
        self.validate_input()
        self.get_want()

        self.add.results = self.results
        self.fab_association = FabricAssociations()
        self.fab_association.rest_send = self.rest_send
        self.fab_association.refresh()
        msg = f"Fab association data{self.fab_association.fabric_association_data}"
        self.log.debug(msg)
        for item in self.fab_association.fabric_association_data:
            fabric_name = item.get("fabricName", None)
            if fabric_name is None:
                continue
            self.data[fabric_name] = item

        self.verify_msd_fab_exists_in_controller()
        self.verify_msd_fab_type()
        self.verify_child_fab_exists_in_controller()
        self.verify_child_fabric_is_member_of_another_fabric()
        for item in self.payloads:
            if self.verify_child_fabric_is_already_member(item):
                self.results.action = self.action
                self.results.result_current = {"success": True, "changed": False}
                msg = "Child fabric is already member of MSD fabric."
                self.results.response_current = {"RETURN_CODE": 200, "MESSAGE": msg}
                self.results.register_task_result()
            else:
                self.add.rest_send = self.rest_send
                fabric_names_to_add = []
                for want in self.payloads:
                    fabric_names_to_add.append(want["sourceFabric"])
                try:
                    self.add.fabric_names = fabric_names_to_add
                except ValueError as error:
                    raise ValueError(f"{error}") from error

                try:
                    self.add.commit(item)
                except ValueError as error:
                    raise ValueError(f"{error}") from error


class Query(childCommon):
    """
    ### Summary
    Handle query state.

    ### Raises

    -   ``ValueError`` if:
        -   The playbook parameters are invalid.
        -   The controller returns an error when attempting to retrieve
            the fabric details.
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        super().__init__(params)

        self.action = "child_fabric_query"
        self._implemented_states.add("query")
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED Query(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

    def verify_payload(self):
        if self.config is None:
            msg = f"{self.class_name}: "
            msg += "Playbook configuration for FABRIC_NAME is missing"
            raise ValueError(msg)
        for config in self.config:
            try:
                fabric_name = config.get("FABRIC_NAME", None)
                try:
                    self.conversion.validate_fabric_name(fabric_name)
                except (TypeError, ValueError) as error:
                    msg = f"{self.class_name}: "
                    msg += "Playbook configuration for FABRIC_NAME is missing or "
                    msg += "contains an invalid FABRIC_NAME. "
                    # error below already contains a period "." at the end
                    msg += f"Error detail: {error} "
                    msg += f"Bad configuration: {config}."
                    raise ValueError(msg) from error
            except ValueError as error:
                raise ValueError(f"{error}") from error

    def commit(self) -> None:
        """
        ### Summary
        query the fabrics in ``self.want`` that exist on the controller.

        ### Raises

        -   ``ValueError`` if:
            -   Any fabric names are invalid.
            -   The controller returns an error when attempting to
                query the fabrics.
        """
        self.verify_payload()
        self.get_want()
        fabric_query = childFabricQuery()
        fabric_query.rest_send = self.rest_send
        fabric_query.results = self.results

        fabric_names_to_query = []
        for item in self.payloads:
            fabric_names_to_query.append(item["destFabric"])
        try:
            fabric_query.fabric_names = copy.copy(fabric_names_to_query)
        except ValueError as error:
            raise ValueError(f"{error}") from error

        try:
            fabric_query.commit()
        except ValueError as error:
            raise ValueError(f"{error}") from error


def main():
    """
    ### Summary
    main entry point for module execution.

    -   In the event that ``ValueError`` is raised, ``AnsibleModule.fail_json``
        is called with the error message.
    -   Else, ``AnsibleModule.exit_json`` is called with the final result.

    ### Raises
    -   ``ValueError`` if:
        -   The playbook parameters are invalid.
        -   The controller returns an error when attempting to
            delete, add, query child fabrics.
    """

    argument_spec = {}
    argument_spec["config"] = {"required": False, "type": "list", "elements": "dict"}
    argument_spec["state"] = {
        "default": "merged",
        "choices": ["deleted", "merged", "query"],
    }

    ansible_module = AnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True
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
    try:
        task = None
        if params["state"] == "merged":
            task = Merged(params)
        elif params["state"] == "deleted":
            task = Deleted(params)
        elif params["state"] == "query":
            task = Query(params)

        if task is None:
            ansible_module.fail_json(f"Invalid state: {params['state']}")
        task.rest_send = rest_send
        task.commit()
    except ValueError as error:
        ansible_module.fail_json(f"{error}", **task.results.failed_result)

    task.results.build_final_result()

    # Results().failed is a property that returns a set()
    # of boolean values.  pylint doesn't seem to understand this so we've
    # disabled the unsupported-membership-test warning.
    if True in task.results.failed:  # pylint: disable=unsupported-membership-test
        msg = "Module failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)


if __name__ == "__main__":
    main()
