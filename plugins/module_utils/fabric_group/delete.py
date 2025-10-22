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
# pylint: disable=too-many-instance-attributes
"""
Delete fabric groups
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import logging

from ..common.api.onemanage.endpoints import EpOneManageFabricDelete
from ..common.exceptions import ControllerResponseError
from ..common.rest_send_v2 import RestSend

# Import Results() only for the case where the user has not set Results()
# prior to calling commit().  In this case, we instantiate Results()
# in _validate_commit_parameters() so that we can register the failure
# in commit().
from ..common.results_v2 import Results
from ..fabric_group.fabric_group_details import FabricGroupDetails
from ..fabric_group.fabric_group_member_info import FabricGroupMemberInfo


class FabricGroupDelete:
    """
    Delete fabric groups

    A fabric group must be empty before it can be deleted.

    Usage:

    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.delete import \
        FabricGroupDelete
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import \
        Results

    instance = FabricGroupDelete(ansible_module)
    instance.fabric_group_names = ["FABRIC_1", "FABRIC_2"]
    instance.results = self.results
    instance.commit()
    results.build_final_result()

    # diff contains a dictionary of changes made
    diff = results.diff
    # result contains the result(s) of the delete request
    result = results.result
    # response contains the response(s) from the controller
    response = results.response

    # results.final_result contains all of the above info, and can be passed
    # to the exit_json and fail_json methods of AnsibleModule:

    if True in results.failed:
        msg = "Delete failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.action = "fabric_group_delete"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._fabric_groups_to_delete = []
        self.ep_fabric_group_delete = EpOneManageFabricDelete()
        self._fabric_group_names: list[str] = []

        self._cannot_delete_fabric_reason: str = ""

        self._fabric_group_details: FabricGroupDetails = FabricGroupDetails()
        self._fabric_group_member_info: FabricGroupMemberInfo = FabricGroupMemberInfo()
        # Properties to be set by caller
        self._rest_send: RestSend = RestSend({})
        self._results: Results = Results()

        msg = f"ENTERED {self.class_name} "
        msg += f"action: {self.action}"
        self.log.debug(msg)

    def _get_fabric_groups_to_delete(self) -> None:
        """
        -   Retrieve fabric group info from the controller and set the list of
            controller fabric groups that are in our fabric_group_names list.
        -   Raise ``ValueError`` if any fabric in ``fabric_group_names``
            cannot be deleted.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name} ENTERED"
        self.log.debug(msg)

        self.fabric_group_details.rest_send = self.rest_send
        self.fabric_group_details.results = self.results
        self._fabric_groups_to_delete = []
        for fabric_group_name in self.fabric_group_names:
            self.fabric_group_details.fabric_group_name = fabric_group_name
            self.fabric_group_details.refresh()
            if fabric_group_name in self.fabric_group_details.all_data:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Found fabric group {fabric_group_name} on controller."
                self.log.debug(msg)
                try:
                    self._verify_fabric_group_can_be_deleted(fabric_group_name)
                except ValueError as error:
                    raise ValueError(error) from error
                self._fabric_groups_to_delete.append(fabric_group_name)

    def _verify_fabric_group_can_be_deleted(self, fabric_group_name):
        """
        raise ``ValueError`` if the fabric cannot be deleted
        return otherwise
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name} ENTERED"
        self.log.debug(msg)

        self._fabric_group_member_info.rest_send = self.rest_send
        self._fabric_group_member_info.results = self.results
        self._fabric_group_member_info.fabric_group_name = fabric_group_name
        try:
            self._fabric_group_member_info.refresh()
        except (ControllerResponseError, ValueError) as error:
            raise ValueError(error) from error

        if self._fabric_group_member_info.count == 0:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Fabric group {fabric_group_name} "
        msg += f"in cluster {self._fabric_group_member_info.cluster_name} "
        msg += "cannot be deleted since it contains "
        msg += f"{self._fabric_group_member_info.count} members "
        msg += f"{self._fabric_group_member_info.members}. "
        msg += "Remove all members from the fabric group and try again."
        raise ValueError(msg)

    def _validate_commit_parameters(self):
        """
        - validate the parameters for commit
        - raise ``ValueError`` if ``fabric_group_names`` is not set
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name} ENTERED"
        self.log.debug(msg)

        if not self.fabric_group_names:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_names must be set prior to calling commit."
            raise ValueError(msg)

        if not self.rest_send.params:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send.params must be set prior to calling commit."
            raise ValueError(msg)

    def commit(self):
        """
        - delete each of the fabrics in self.fabric_group_names
        - raise ``ValueError`` if any commit parameters are invalid
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name} ENTERED"
        self.log.debug(msg)

        try:
            self._validate_commit_parameters()
        except ValueError as error:
            self.results.changed = False
            self.results.failed = True
            self.register_result(None)
            raise ValueError(error) from error

        self.results.action = self.action
        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state
        self.results.diff_current = {}

        try:
            self._get_fabric_groups_to_delete()
        except ValueError as error:
            self.results.changed = False
            self.results.failed = True
            self.register_result(None)
            raise ValueError(error) from error

        if len(self._fabric_groups_to_delete) != 0:
            try:
                self._send_requests()
            except ValueError as error:
                self.results.changed = False
                self.results.failed = True
                self.register_result(None)
                raise ValueError(error) from error
            return

        self.results.changed = False
        self.results.failed = False
        self.results.result_current = {"success": True, "changed": False}
        msg = "No fabrics to delete"
        self.results.response_current = {"RETURN_CODE": 200, "MESSAGE": msg}
        self.results.register_task_result()

    def _send_requests(self):
        """
        -   Update RestSend() parameters:
                - check_mode : Enables or disables sending the request
                - timeout : Reduce to 1 second from default of 300 seconds
        -   Call _send_request() for each fabric to be deleted.
        -   Raise ``ValueError`` if any fabric cannot be deleted.

        NOTES:
        -   We don't want RestSend to retry on errors since the likelihood of a
            timeout error when deleting a fabric is low, and there are cases of
            permanent errors for which we don't want to retry.  Hence, we set
            timeout to 1 second and restore the original timeout after the
            requests are sent.
        """
        self.rest_send.save_settings()
        self.rest_send.timeout = 1

        for fabric_group_name in self._fabric_groups_to_delete:
            try:
                self._send_request(fabric_group_name)
            except ValueError as error:
                self.results.changed = False
                self.results.failed = True
                self.register_result(fabric_group_name)
                raise ValueError(error) from error
        self.rest_send.restore_settings()

    def _set_fabric_group_delete_endpoint(self, fabric_group_name):
        try:
            self.ep_fabric_group_delete.fabric_name = fabric_group_name
            self.rest_send.path = self.ep_fabric_group_delete.path
            self.rest_send.verb = self.ep_fabric_group_delete.verb
        except (ValueError, TypeError) as error:
            raise ValueError(error) from error

    def _send_request(self, fabric_group_name):
        """
        ### Summary
        Send a delete request to the controller and register the result.

        ### Raises
            -   ``ValueError`` if the fabric delete endpoint cannot be set.
        """
        try:
            self._set_fabric_group_delete_endpoint(fabric_group_name)
            self.rest_send.commit()
        except (ValueError, TypeError) as error:
            raise ValueError(error) from error

        self.register_result(fabric_group_name)

    def register_result(self, fabric_group_name):
        """
        -   Register the result of the fabric delete request
        -   If ``fabric_group_name`` is ``None``, set the result to indicate
            no changes occurred and the request was not successful.
        -   If ``fabric_group_name`` is not ``None``, set the result to indicate
            the success or failure of the request.
        """
        self.results.action = self.action
        if self.rest_send is not None:
            self.results.check_mode = self.rest_send.check_mode
            self.results.state = self.rest_send.state
        else:
            self.results.check_mode = False
            self.results.state = "unknown"

        if fabric_group_name is None or self.rest_send is None:
            self.results.diff_current = {}
            self.results.response_current = {}
            self.results.result_current = {"success": False, "changed": False}
            self.results.register_task_result()
            return

        if self.rest_send.result_current.get("success", None) is True:
            self.results.diff_current = {"fabric_group_name": fabric_group_name}
            # need this to match the else clause below since we
            # pass response_current (altered or not) to the results object
            response_current = copy.deepcopy(self.rest_send.response_current)
        else:
            self.results.diff_current = {}
            # Improve the controller's error message to include the fabric_group_name
            response_current = copy.deepcopy(self.rest_send.response_current)
            if "DATA" in response_current:
                if "Failed to delete the fabric." in response_current["DATA"]:
                    msg = f"Failed to delete fabric group {fabric_group_name}."
                    response_current["DATA"] = msg

        self.results.response_current = response_current
        self.results.result_current = self.rest_send.result_current

        self.results.register_task_result()

    @property
    def fabric_group_names(self) -> list[str]:
        """
        - getter: return list of fabric_group_names
        - setter: set list of fabric_group_names
        - setter: raise ``ValueError`` if ``value`` is not a ``list`` of ``str``
        """
        return self._fabric_group_names

    @fabric_group_names.setter
    def fabric_group_names(self, value: list[str]) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_names must be a list. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise ValueError(msg)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_names must be a list of at least one string. "
            msg += f"got {value}."
            raise ValueError(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "fabric_group_names must be a list of strings. "
                msg += f"got {type(item).__name__} for "
                msg += f"value {item}"
                raise ValueError(msg)
        self._fabric_group_names = value

    @property
    def fabric_group_details(self) -> FabricGroupDetails:
        """
        An instance of FabricGroupDetails.
        """
        return self._fabric_group_details

    @fabric_group_details.setter
    def fabric_group_details(self, value: FabricGroupDetails) -> None:
        self._fabric_group_details = value

    @property
    def rest_send(self) -> RestSend:
        """
        An instance of the RestSend class.
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        An instance of the Results class.
        """
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        self._results = value
