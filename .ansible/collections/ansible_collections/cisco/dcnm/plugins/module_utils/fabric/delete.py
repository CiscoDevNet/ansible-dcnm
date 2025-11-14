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
from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

import copy
import inspect
import logging

from ..common.api.v1.lan_fabric.rest.control.fabrics.fabrics import \
    EpFabricDelete
from ..common.exceptions import ControllerResponseError
# Import Results() only for the case where the user has not set Results()
# prior to calling commit().  In this case, we instantiate Results()
# in _validate_commit_parameters() so that we can register the failure
# in commit().
from ..common.results import Results
from .common import FabricCommon


class FabricDelete(FabricCommon):
    """
    Delete fabrics

    A fabric must be empty before it can be deleted.

    Usage:

    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.delete import \
        FabricDelete
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
        Results

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

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.action = "fabric_delete"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._fabrics_to_delete = []
        self.ep_fabric_delete = EpFabricDelete()
        self._fabric_names = None

        self._cannot_delete_fabric_reason = None

        msg = "ENTERED FabricDelete()"
        self.log.debug(msg)

    def _get_fabrics_to_delete(self) -> None:
        """
        -   Retrieve fabric info from the controller and set the list of
            controller fabrics that are in our fabric_names list.
        -   Raise ``ValueError`` if any fabric in ``fabric_names``
            cannot be deleted.
        """
        self.fabric_details.refresh()

        self._fabrics_to_delete = []
        for fabric_name in self.fabric_names:
            if fabric_name in self.fabric_details.all_data:
                try:
                    self._verify_fabric_can_be_deleted(fabric_name)
                except ValueError as error:
                    raise ValueError(error) from error
                self._fabrics_to_delete.append(fabric_name)

    def _verify_fabric_can_be_deleted(self, fabric_name):
        """
        raise ``ValueError`` if the fabric cannot be deleted
        return otherwise
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.fabric_summary.fabric_name = fabric_name

        try:
            self.fabric_summary.refresh()
        except (ControllerResponseError, ValueError) as error:
            raise ValueError(error) from error

        if self.fabric_summary.fabric_is_empty is True:
            return
        msg = f"{self.class_name}.{method_name}: "
        msg += f"Fabric {fabric_name} cannot be deleted since it is not "
        msg += "empty. Remove all devices from the fabric and try again."
        raise ValueError(msg)

    def _validate_commit_parameters(self):
        """
        - validate the parameters for commit
        - raise ``ValueError`` if ``fabric_names`` is not set
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        if self.fabric_details is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_details must be set prior to calling commit."
            raise ValueError(msg)

        if self.fabric_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be set prior to calling commit."
            raise ValueError(msg)

        # pylint: disable=no-member
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit."
            raise ValueError(msg)

        # pylint: disable=access-member-before-definition
        # pylint: disable=attribute-defined-outside-init
        if self.results is None:
            # Instantiate Results() only to register the failure
            self.results = Results()
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set prior to calling commit."
            raise ValueError(msg)
        # pylint: enable=access-member-before-definition
        # pylint: enable=attribute-defined-outside-init

    def commit(self):
        """
        - delete each of the fabrics in self.fabric_names
        - raise ``ValueError`` if any commit parameters are invalid
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            self._validate_commit_parameters()
        except ValueError as error:
            self.results.changed = False
            self.results.failed = True
            self.register_result(None)
            raise ValueError(error) from error

        # pylint: disable=no-member
        self.results.action = self.action
        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state
        self.results.diff_current = {}

        try:
            self._get_fabrics_to_delete()
        except ValueError as error:
            self.results.changed = False
            self.results.failed = True
            self.register_result(None)
            raise ValueError(error) from error

        msg = f"self._fabrics_to_delete: {self._fabrics_to_delete}"
        self.log.debug(msg)
        if len(self._fabrics_to_delete) != 0:
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
        # pylint: disable=no-member
        self.rest_send.save_settings()
        self.rest_send.timeout = 1

        for fabric_name in self._fabrics_to_delete:
            try:
                self._send_request(fabric_name)
            except ValueError as error:
                self.results.changed = False
                self.results.failed = True
                self.register_result(fabric_name)
                raise ValueError(error) from error
        self.rest_send.restore_settings()

    def _set_fabric_delete_endpoint(self, fabric_name):
        try:
            self.ep_fabric_delete.fabric_name = fabric_name
            # pylint: disable=no-member
            self.rest_send.path = self.ep_fabric_delete.path
            self.rest_send.verb = self.ep_fabric_delete.verb
        except (ValueError, TypeError) as error:
            raise ValueError(error) from error

    def _send_request(self, fabric_name):
        """
        ### Summary
        Send a delete request to the controller and register the result.

        ### Raises
            -   ``ValueError`` if the fabric delete endpoint cannot be set.
        """
        # pylint: disable=no-member
        try:
            self._set_fabric_delete_endpoint(fabric_name)
            self.rest_send.commit()
        except (ValueError, TypeError) as error:
            raise ValueError(error) from error

        self.register_result(fabric_name)

    def register_result(self, fabric_name):
        """
        -   Register the result of the fabric delete request
        -   If ``fabric_name`` is ``None``, set the result to indicate
            no changes occurred and the request was not successful.
        -   If ``fabric_name`` is not ``None``, set the result to indicate
            the success or failure of the request.
        """
        # pylint: disable=no-member
        self.results.action = self.action
        if self.rest_send is not None:
            self.results.check_mode = self.rest_send.check_mode
            self.results.state = self.rest_send.state
        else:
            self.results.check_mode = False
            self.results.state = "unknown"

        if fabric_name is None or self.rest_send is None:
            self.results.diff_current = {}
            self.results.response_current = {}
            self.results.result_current = {"success": False, "changed": False}
            self.results.register_task_result()
            return

        if self.rest_send.result_current.get("success", None) is True:
            self.results.diff_current = {"FABRIC_NAME": fabric_name}
            # need this to match the else clause below since we
            # pass response_current (altered or not) to the results object
            response_current = copy.deepcopy(self.rest_send.response_current)
        else:
            self.results.diff_current = {}
            # Improve the controller's error message to include the fabric_name
            response_current = copy.deepcopy(self.rest_send.response_current)
            if "DATA" in response_current:
                if "Failed to delete the fabric." in response_current["DATA"]:
                    msg = f"Failed to delete fabric {fabric_name}."
                    response_current["DATA"] = msg

        self.results.response_current = response_current
        self.results.result_current = self.rest_send.result_current

        self.results.register_task_result()

    @property
    def fabric_names(self):
        """
        - getter: return list of fabric_names
        - setter: set list of fabric_names
        - setter: raise ``ValueError`` if ``value`` is not a ``list`` of ``str``
        """
        return self._fabric_names

    @fabric_names.setter
    def fabric_names(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be a list. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise ValueError(msg)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be a list of at least one string. "
            msg += f"got {value}."
            raise ValueError(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "fabric_names must be a list of strings. "
                msg += f"got {type(item).__name__} for "
                msg += f"value {item}"
                raise ValueError(msg)
        self._fabric_names = value
