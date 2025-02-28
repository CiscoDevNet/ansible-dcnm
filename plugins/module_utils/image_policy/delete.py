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

from ..common.api.v1.imagemanagement.rest.policymgnt.policymgnt import \
    EpPolicyDelete
from ..common.properties import Properties
from ..common.results import Results
from .image_policies import ImagePolicies


@Properties.add_rest_send
@Properties.add_results
@Properties.add_params
class ImagePolicyDelete:
    """
    ### Summary
    Delete image policies

    ### Raises
    -   ``ValueError`` if:
            -   ``params`` is not set prior to calling commit.
            -   ``policy_names`` is not set prior to calling commit.
            -   ``rest_send`` is not set prior to calling commit.
            -   ``results`` is not set prior to calling commit.
            -   ``params`` is missing the ``check_mode`` key.
            -   ``params`` is missing the ``state`` key.
            -   ``state`` is not one of deleted, merged, overridden, query, replaced.
            -   One or more policies in ``policy_names`` have devices attached.
    -  ``TypeError`` if:
            -   ``policy_names`` is not a list.
            -   ``policy_names`` is not a list of strings.

    ### Usage - Delete specific image policies
    ```python
    instance = ImagePolicyDelete()
    instance.policy_names = ["IMAGE_POLICY_1", "IMAGE_POLICY_2"]
    instance.commit()
    ```

    ### Usage - Delete all image policies
    ```python
    instance = ImagePolicyDelete()
    instance.policy_names = ["delete_all_image_policies"]
    instance.commit()
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.action = "delete"
        self.check_mode = None
        self.endpoint = EpPolicyDelete()
        self.path = self.endpoint.path
        self.payload = None
        self.state = None
        self.verb = self.endpoint.verb

        self._image_policies = ImagePolicies()
        self._image_policies.results = Results()
        self._params = None
        self._policies_to_delete = []
        self._policy_names = None
        self._results = None
        self._rest_send = None

        msg = "ENTERED ImagePolicyDelete(): "
        msg += f"action: {self.action}, "
        self.log.debug(msg)

    def _verify_image_policy_ref_count(self, instance, policy_names):
        """
        ### Summary
        Verify that all image policies in policy_names have a ref_count of 0
        (i.e. no devices are using the policy).

        ### Raises
        -   ``ValueError`` if any policy in policy_names has a ref_count
            greater than 0 (i.e. devices are using the policy).

        ### Parameters
        -   ``instance`` : ImagePolicies() instance
        -   ``policy_names`` : list of policy names
        """
        method_name = inspect.stack()[0][3]
        _non_zero_ref_counts = {}
        for policy_name in policy_names:
            instance.policy_name = policy_name
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.policy_name: {instance.policy_name}, "
            msg += f"instance.ref_count: {instance.ref_count}."
            self.log.debug(msg)
            # If the policy does not exist on the controller, the ref_count
            # will be None. We skip these too.
            if instance.ref_count in [0, None]:
                continue
            _non_zero_ref_counts[policy_name] = instance.ref_count
        if len(_non_zero_ref_counts) == 0:
            return
        msg = f"{self.class_name}.{method_name}: "
        msg += "One or more policies have devices attached. "
        msg += "Detach these policies from all devices first using "
        msg += "the dcnm_image_upgrade module, with state == deleted. "
        for policy_name, ref_count in _non_zero_ref_counts.items():
            msg += f"policy_name: {policy_name}, "
            msg += f"ref_count: {ref_count}. "
        raise ValueError(msg)

    def _get_policies_to_delete(self) -> None:
        """
        ### Summary
        Retrieve image policies from the controller and return the
        list of controller policies that are in our policy_names list.

        If policy_names list contains a single element, and that element
        is "delete_all_image_policies", then all policies on the controller
        are returned.

        ### Raises
        -   ``ValueError`` if any policy in policy_names has a ref_count
            greater than 0 (i.e. devices are using the policy).
        """
        method_name = inspect.stack()[0][3]
        # pylint: disable=no-member
        self._image_policies.rest_send = self.rest_send
        # pylint: enable=no-member
        self._image_policies.refresh()
        if (
            "delete_all_image_policies" in self.policy_names
            and len(self.policy_names) == 1
        ):
            self.policy_names = list(self._image_policies.all_policies.keys())
        try:
            self._verify_image_policy_ref_count(self._image_policies, self.policy_names)
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{error}"
            raise ValueError(msg) from error

        self._policies_to_delete = []
        for policy_name in self.policy_names:
            if policy_name in self._image_policies.all_policies:
                msg = f"Policy {policy_name} exists on the controller. "
                msg += f"Appending {policy_name} to _policies_to_delete."
                self.log.debug(msg)
                self._policies_to_delete.append(policy_name)

    # pylint: disable=no-member
    def _validate_commit_parameters(self):
        """
        ### Summary
        Validate the parameters for commit.

        ### Raises
        -   ``ValueError`` if:
                -   ``params`` is not set prior to calling commit.
                -   ``policy_names`` is not set prior to calling commit.
                -   ``rest_send`` is not set prior to calling commit.
                -   ``results`` is not set prior to calling commit.
        """
        method_name = inspect.stack()[0][3]
        if self.params is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params must be set prior to calling commit."
            raise ValueError(msg)

        if self.policy_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_names must be set prior to calling commit."
            raise ValueError(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit."
            raise ValueError(msg)

        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set prior to calling commit."
            raise ValueError(msg)

    def commit(self):
        """
        ### Summary
        delete each of the image policies in self.policy_names.

        ### Raises
        -   ``ValueError`` if:
                -   ``params`` is not set.
                -   ``policy_names`` is not set.
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        try:
            self._validate_commit_parameters()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{error}"
            raise ValueError(msg) from error

        self.check_mode = self.params.get("check_mode")
        self.state = self.params.get("state")

        self._get_policies_to_delete()

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self._policies_to_delete: {self._policies_to_delete}"
        self.log.debug(msg)

        if len(self._policies_to_delete) != 0:
            self._send_requests()
        else:
            msg = "No image policies to delete."
            self.log.debug(msg)
            self.results.action = self.action
            self.results.check_mode = self.check_mode
            self.results.state = self.state
            self.results.diff_current = {}
            self.results.result_current = {"success": True, "changed": False}
            self.results.changed = False
            self.results.failed = False
            self.results.response_current = {"RETURN_CODE": 200, "MESSAGE": msg}
            self.results.register_task_result()

    def _send_requests(self):
        """
        ### Summary
        -   If check_mode is False, send the requests to the controller.
        -   If check_mode is True, do not send the requests to the controller.
        -   In both cases, populate the following lists.

        ```text
        - self.response_ok  : list of controller responses associated with success result
        - self.result_ok    : list of results where success is True
        - self.diff_ok      : list of payloads for which the request succeeded
        - self.response_nok : list of controller responses associated with failed result
        - self.result_nok   : list of results where success is False
        - self.diff_nok     : list of payloads for which the request failed
        ```
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.rest_send.save_settings()
        self.rest_send.check_mode = self.check_mode

        # We don't want RestSend to retry on errors since the likelihood of a
        # timeout error when deleting image policies is low, and there
        # are cases of permanent errors for which we don't want to retry.
        self.rest_send.timeout = 1

        msg = f"{self.class_name}.{method_name}: "
        msg += f"Deleting policies {self._policies_to_delete}"
        self.log.debug(msg)

        self.payload = {"policyNames": self._policies_to_delete}
        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.payload = copy.deepcopy(self.payload)
        self.rest_send.commit()
        self.rest_send.restore_settings()

        self.register_result()

    def register_result(self):
        """
        ### Summary
        Register the result of the fabric create request
        """
        if self.rest_send.result_current["success"]:
            self.results.failed = False
            self.results.diff_current = self.payload
        else:
            self.results.diff_current = {}
            self.results.failed = True

        self.results.action = self.action
        self.results.check_mode = self.check_mode
        self.results.state = self.state
        self.results.result_current = self.rest_send.result_current
        self.results.response_current = self.rest_send.response_current
        self.results.register_task_result()

    @property
    def policy_names(self):
        """
        ### Summary
        A list of policy names to delete.

        ### Raises
        -   ``TypeError`` if:
                -   ``policy_names`` is not a list of strings.
        """
        return self._policy_names

    @policy_names.setter
    def policy_names(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_names must be a list. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}."
            raise TypeError(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "policy_names must be a list of strings. "
                msg += f"got {type(item).__name__} for "
                msg += f"list item {item}."
                raise TypeError(msg)
        self._policy_names = value
