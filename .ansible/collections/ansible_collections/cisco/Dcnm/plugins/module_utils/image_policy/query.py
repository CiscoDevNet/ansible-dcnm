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

from ..common.properties import Properties


@Properties.add_params
@Properties.add_results
class ImagePolicyQuery:
    """
    ### Summary
    Query image policies

    ### Raises
    -   ``ValueError`` if:
            -   params is not set.
            -   policy_names is not set.
            -   image_policies is not set.
    -   ``TypeError`` if:
            -   policy_names is not a list.
            -   policy_names contains anything other than strings.
            -   image_policies is not an instance of ImagePolicies.

    ### Usage
    ```python
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    results = Results()

    image_policies = ImagePolicies()
    image_policies.rest_send = rest_send
    image_policies.results = results

    instance = ImagePolicyQuery()
    instance.image_policies = ImagePolicies()
    instance.results = results
    instance.policy_names = ["IMAGE_POLICY_1", "IMAGE_POLICY_2"]
    instance.commit()
    diff = instance.results.diff_current # contains the image policy information
    result = instance.results.result_current # contains the result(s) of the query
    response = instance.results.response_current # contains the response(s) from the controller
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.action = "query"
        self._policies_to_query = []
        self._policy_names = None
        self._results = None

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED ImagePolicyQuery(): "
        msg += f"action {self.action}, "
        self.log.debug(msg)

    @property
    def policy_names(self):
        """
        ### Summary
        return the policy names

        ### Raises
        -   ``TypeError`` if:
                -   policy_names is not a list.
                -   policy_names contains anything other than strings.
        -   ``ValueError`` if:
                -   policy_names list is empty.
        """
        return self._policy_names

    @policy_names.setter
    def policy_names(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_names must be a list. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_names must be a list of at least one string. "
            msg += f"got {value}."
            raise ValueError(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "policy_names must be a list of strings. "
                msg += f"got {type(item).__name__} for "
                msg += f"value {item}"
                raise TypeError(msg)
        self._policy_names = value

    # pylint: disable=no-member
    def commit(self):
        """
        ### Summary
        query each of the image policies in self.policy_names

        ### Raises
        -   ``ValueError`` if:
                -   params is not set.
                -   policy_names is not set.
                -   image_policies is not set.

        ### Notes
        -   pylint: disable=no-member is needed due to the rest_send property
            being dynamically created by the @Properties.add_results decorator.
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

        if self.image_policies is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "image_policies must be set to an instance of "
            msg += "ImagePolicies() before calling commit."
            raise ValueError(msg)

        self.image_policies.refresh()

        self.results.action = self.action
        self.results.check_mode = self.params.get("check_mode")
        self.results.state = self.params.get("state", None)

        if self.image_policies.results.result_current.get("success") is False:
            self.results.diff_current = {}
            self.results.failed = True
            self.results.response_current = copy.deepcopy(
                self.image_policies.results.response_current
            )
            self.results.result_current = copy.deepcopy(
                self.image_policies.results.result_current
            )
            self.results.register_task_result()
            return

        self.results.failed = False
        registered_a_result = False
        for policy_name in self.policy_names:
            if policy_name not in self.image_policies.all_policies:
                continue
            registered_a_result = True
            self.results.diff_current = copy.deepcopy(
                self.image_policies.all_policies[policy_name]
            )
            self.results.response_current = copy.deepcopy(
                self.image_policies.results.response_current
            )
            self.results.result_current = copy.deepcopy(
                self.image_policies.results.result_current
            )
            self.results.register_task_result()

        if registered_a_result is False:
            self.results.failed = False
            self.results.diff_current = {}
            # Avoid a failed result if none of the policies were found
            self.results.result_current = {"success": True}
            self.results.register_task_result()

    @property
    def image_policies(self):
        """
        ### Summary
        Return the image_policies instance

        ### Raises
        -   ``TypeError`` if image_policies is not an instance of ImagePolicies
        """
        return self._image_policies

    @image_policies.setter
    def image_policies(self, value):
        method_name = inspect.stack()[0][3]
        _class_have = None
        _class_need = "ImagePolicies"
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
        self._image_policies = value
