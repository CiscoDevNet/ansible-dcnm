# Copyright (c) 2024 Cisco and/or its affiliates.
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
Delete fabrics. A fabric must be empty before it can be deleted.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import logging
from typing import Literal

from ..common.api.v1.lan_fabric.rest.control.fabrics.fabrics import EpFabricDelete
from ..common.exceptions import ControllerResponseError
from ..common.operation_type import OperationType
from ..common.rest_send_v2 import RestSend

# Import Results() only for the case where the user has not set Results()
# prior to calling commit().  In this case, we instantiate Results()
# in _validate_commit_parameters() so that we can register the failure
# in commit().
from ..common.results_v2 import Results
from .common_v2 import FabricCommon
from .fabric_details_v3 import FabricDetailsByName
from .fabric_summary_v2 import FabricSummary


class FabricDelete(FabricCommon):
    """
    Delete fabrics

    A fabric must be empty before it can be deleted.

    Usage:

    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.delete import FabricDelete
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import Results

    instance = FabricDelete(ansible_module)
    instance.fabric_names = ["FABRIC_1", "FABRIC_2"]
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
        msg = "Query failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)
    """

    def __init__(self) -> None:
        super().__init__()
        self.class_name: str = self.__class__.__name__
        self.action: str = "fabric_delete"

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")
        self._fabric_details_by_name: FabricDetailsByName = FabricDetailsByName()
        self._fabric_summary: FabricSummary = FabricSummary()
        self._results: Results = Results()
        self._results.operation_type = OperationType.DELETE
        self._rest_send: RestSend = RestSend(params={})

        self._cannot_delete_fabric_reason: str = ""
        self._ep_fabric_delete: EpFabricDelete = EpFabricDelete()
        self._fabric_names: list[str] = []
        self._fabrics_to_delete: list[str] = []

        msg = "ENTERED FabricDelete()"
        self.log.debug(msg)

    def _get_fabrics_to_delete(self) -> None:
        """
        -   Retrieve fabric info from the controller and set the list of
            controller fabrics that are in our fabric_names list.
        -   Raise ``ValueError`` if any fabric in ``fabric_names``
            cannot be deleted.
        """
        method_name: str = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self._fabric_details_by_name.refresh()

        msg = f"{self.class_name}.{method_name}: "
        msg += "self._fabric_details_by_name.fabric_names: "
        msg += f"{self._fabric_details_by_name.fabric_names}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.fabric_names: {self.fabric_names}"
        self.log.debug(msg)

        self._fabrics_to_delete = []
        for fabric_name in self.fabric_names:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Checking if fabric {fabric_name} can be deleted."
            self.log.debug(msg)
            if fabric_name in self._fabric_details_by_name.fabric_names:
                try:
                    self._verify_fabric_can_be_deleted(fabric_name=fabric_name)
                except ValueError as error:
                    raise ValueError(error) from error
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Fabric {fabric_name} can be deleted. "
                msg += "Appending to self._fabric_to_delete."
                self.log.debug(msg)
                self._fabrics_to_delete.append(fabric_name)
        msg = f"{self.class_name}.{method_name}: "
        msg += f"self._fabrics_to_delete: {self._fabrics_to_delete}"
        self.log.debug(msg)

    def _verify_fabric_can_be_deleted(self, fabric_name: str) -> None:
        """
        # Summary

        Verify that fabric_name can be deleted by checking that it is empty.

        ## Raises

        ### ValueError

        - fabric_name cannot be deleted
        """
        method_name: str = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self._fabric_summary.fabric_name = fabric_name

        try:
            self._fabric_summary.refresh()
        except (ControllerResponseError, ValueError) as error:
            raise ValueError(error) from error

        if self._fabric_summary.fabric_is_empty is True:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Fabric {fabric_name} is empty and can be deleted."
            self.log.debug(msg)
            return
        msg = f"{self.class_name}.{method_name}: "
        msg += f"Fabric {fabric_name} cannot be deleted since it is not "
        msg += "empty. Remove all devices from the fabric and try again."
        self.log.debug(msg)
        raise ValueError(msg)

    def _validate_commit_parameters(self) -> None:
        """
        # Summary

        Validate the parameters for commit

        ## Raises

        ### ValueError

        - `fabric_names` is not set
        """
        method_name: str = inspect.stack()[0][3]  # pylint: disable=unused-variable

        if not self._rest_send.params:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit."
            raise ValueError(msg)

    def commit(self) -> None:
        """
        # Summary

        Delete each of the fabrics in self.fabric_names.

        ## Raises

        ### ValueError

        - Any parameters required by commit() are invalid
        """
        try:
            self._validate_commit_parameters()
        except ValueError as error:
            self._results.add_changed(False)
            self._results.add_failed(True)
            self.register_result(fabric_name="")
            raise ValueError(error) from error

        self._fabric_summary.rest_send = self._rest_send
        self._fabric_summary.results = Results()

        self._fabric_details_by_name.rest_send = self._rest_send
        self._fabric_details_by_name.results = Results()

        self._results.action = self.action
        self._results.check_mode = self._rest_send.check_mode
        self._results.state = self._rest_send.state
        self._results.diff_current = {}

        try:
            self._get_fabrics_to_delete()
        except ValueError as error:
            self._results.add_changed(False)
            self._results.add_failed(True)
            self.register_result(fabric_name="")
            raise ValueError(error) from error

        msg = f"self._fabrics_to_delete: {self._fabrics_to_delete}"
        self.log.debug(msg)
        if len(self._fabrics_to_delete) != 0:
            try:
                self._send_requests()
            except ValueError as error:
                self.register_result(fabric_name="")
                raise ValueError(error) from error
            return

        self._results.add_changed(False)
        self._results.add_failed(False)
        self._results.result_current = {"success": True, "changed": False}
        msg = "No fabrics to delete"
        self._results.response_current = {"RETURN_CODE": 200, "MESSAGE": msg}
        self._results.register_task_result()

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

        for fabric_name in self._fabrics_to_delete:
            try:
                self._send_request(fabric_name)
            except ValueError as error:
                self.register_result(fabric_name="")
                raise ValueError(error) from error
        self.rest_send.restore_settings()

    def _set_fabric_delete_endpoint(self, fabric_name: str) -> None:
        """
        # Summary

        Set the fabric delete endpoint parameters in RestSend.

        ## Raises

        ### ValueError

        -   If fabric_name is invalid.
        -   If verb is not a string.

        ### TypeError

        -   If verb is not a valid HTTP method.
        """
        try:
            self._ep_fabric_delete.fabric_name = fabric_name
            self._rest_send.path = self._ep_fabric_delete.path
            self._rest_send.verb = self._ep_fabric_delete.verb
        except (ValueError, TypeError) as error:
            raise ValueError(error) from error

    def _send_request(self, fabric_name: str) -> None:
        """
        ### Summary
        Send a delete request to the controller and register the result.

        ### Raises
            -   ``ValueError`` if the fabric delete endpoint cannot be set.
        """
        # pylint: disable=no-member
        try:
            self._set_fabric_delete_endpoint(fabric_name)
        except (ValueError, TypeError) as error:
            raise ValueError(error) from error

        try:
            self._rest_send.commit()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error
        self.register_result(fabric_name=fabric_name)

    def register_result(self, fabric_name: str) -> None:
        """
        -   Register the result of the fabric delete request
        -   If `fabric_name` is "" (empty string), set the result to indicate
            no changes occurred and the request was not successful.
        -   If `fabric_name` is not "" (empty string), set the result to indicate
            the success or failure of the request.
        """
        method_name: str = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self._results.action = self.action
        if self._rest_send.params:
            self._results.check_mode = self._rest_send.check_mode
            self._results.state = self._rest_send.state
        else:
            self._results.check_mode = False
            self._results.state = "unknown"

        if fabric_name == "" or not self._rest_send.params:
            self._results.diff_current = {}
            self._results.response_current = {}
            self._results.result_current = {"success": False, "changed": False}
            self._results.register_task_result()
            return

        if self._rest_send.result_current.get("success", None) is True:
            self._results.diff_current = {"FABRIC_NAME": fabric_name}
            # need this to match the else clause below since we
            # pass response_current (altered or not) to the results object
            response_current = copy.deepcopy(self._rest_send.response_current)
        else:
            self._results.diff_current = {}
            # Improve the controller's error message to include the fabric_name
            response_current = copy.deepcopy(self._rest_send.response_current)
            if "DATA" in response_current:
                if "Failed to delete the fabric." in response_current["DATA"]:
                    msg = f"Failed to delete fabric {fabric_name}."
                    response_current["DATA"] = msg

        self._results.response_current = response_current
        self._results.result_current = self._rest_send.result_current

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self._results.result_current: {self._results.result_current}"
        self.log.debug(msg)

        self._results.register_task_result()

    @property
    def fabric_names(self) -> list[str]:
        """
        - getter: return list of fabric_names
        - setter: set list of fabric_names
        - setter: raise ``ValueError`` if ``value`` is not a ``list`` of ``str``
        """
        return self._fabric_names

    @fabric_names.setter
    def fabric_names(self, value: list[str]) -> None:
        method_name: str = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be a list. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise ValueError(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "fabric_names must be a list of strings. "
                msg += f"got {type(item).__name__} for "
                msg += f"value {item}"
                raise ValueError(msg)
        self._fabric_names = value

    @property
    def rest_send(self) -> RestSend:
        """
        # Summary

        An instance of the RestSend class.

        ## Raises

        -   setter: `TypeError` if the value is not an instance of RestSend.
        -   setter: `ValueError` if RestSend.params is not set.

        ## getter

        Return an instance of the RestSend class.

        ## setter

        Set an instance of the RestSend class.
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        method_name: str = inspect.stack()[0][3]
        _class_have: str = ""
        _class_need: Literal["RestSend"] = "RestSend"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        if not value.params:
            msg = f"{self.class_name}.{method_name}: "
            msg += "RestSend.params must be set."
            raise ValueError(msg)
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        # Summary

        An instance of the Results class.

        ## Raises

        -   setter: `TypeError` if the value is not an instance of Results.

        ## getter

        Return an instance of the Results class.

        ## setter

        Set an instance of the Results class.
        """
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        method_name: str = inspect.stack()[0][3]
        _class_have: str = ""
        _class_need: Literal["Results"] = "Results"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._results = value
        self._results.action = self.action
        self._results.operation_type = OperationType.DELETE
