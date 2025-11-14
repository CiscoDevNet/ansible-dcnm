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
    EpPolicies
from ..common.conversion import ConversionUtils
from ..common.exceptions import ControllerResponseError
from ..common.properties import Properties


@Properties.add_rest_send
@Properties.add_results
class ImagePolicies:
    """
    ### Summary
    Retrieve image policy details from the controller and provide
    property accessors for the policy attributes.

    ### Usage

    ```python
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    instance = ImagePolicies()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    instance.policy_name = "NR3F"
    if instance.name is None:
        print("policy NR3F does not exist on the controller")
        exit(1)
    policy_name = instance.name
    platform = instance.platform
    epd_image_name = instance.epld_image_name
    ```
    etc...

    Policies can be refreshed by calling ``instance.refresh()``.

    ### Endpoint:
    ``/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies``
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.conversion = ConversionUtils()
        self.endpoint = EpPolicies()
        self.data = {}
        self._all_policies = None
        self._policy_name = None
        self._response_data = None
        self._results = None
        self._rest_send = None

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

    # pylint: disable=no-member
    def refresh(self):
        """
        ### Summary
        Refresh the image policy details from the controller and
        populate self.data with the results.

        self.data is a dictionary of image policy details, keyed on
        image policy name.

        ### Raises
        -   ``ControllerResponseError`` if:
                -   The controller response is missing the expected data.
        -   ``ValueError`` if:
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
                -   The controller response cannot be parsed.

        ### Notes
        -   pylint: disable=no-member is needed because the rest_send, results,
            and params properties are dynamically created by the
            @Properties class decorators.
        """
        method_name = inspect.stack()[0][3]
        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.rest_send must be set before calling refresh."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.results must be set before calling refresh."
            raise ValueError(msg)

        # We always want to get the controller's current image policy
        # state. We set check_mode to False here so the request will be
        # sent to the controller.
        msg = f"{self.class_name}.{method_name}: "
        msg += f"endpoint.verb: {self.endpoint.verb}, "
        msg += f"endpoint.path: {self.endpoint.path}, "
        self.log.debug(msg)
        self.rest_send.save_settings()
        self.rest_send.check_mode = False
        self.rest_send.path = self.endpoint.path
        self.rest_send.verb = self.endpoint.verb
        self.rest_send.commit()
        self.rest_send.restore_settings()

        data = self.rest_send.response_current.get("DATA", {}).get("lastOperDataObject")

        if data is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Bad response when retrieving image policy "
            msg += "information from the controller."
            raise ControllerResponseError(msg)

        if len(data) == 0:
            msg = "the controller has no defined image policies."
            self.log.debug(msg)

        self._response_data = {}
        self._all_policies = {}
        self.data = {}

        for policy in data:
            policy_name = policy.get("policyName")
            if policy_name is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += "Cannot parse policy information from the controller."
                raise ValueError(msg)
            self.data[policy_name] = policy
            self._response_data[policy_name] = policy

        self._all_policies = copy.deepcopy(self._response_data)

        self.results.response_current = self.rest_send.response_current
        self.results.result_current = self.rest_send.result_current

    def _get(self, item):
        """
        ### Summary
        Return the value of item from the policy matching self.policy_name.

        ### Raises
        -   ``ValueError`` if ``policy_name`` is not set..
        """
        method_name = inspect.stack()[0][3]

        if self.policy_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.policy_name must be set before "
            msg += f"accessing property {item}."
            raise ValueError(msg)

        if self.policy_name not in self._response_data:
            return None

        if item == "policy":
            return self._response_data[self.policy_name]

        if item not in self._response_data[self.policy_name]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.policy_name} does not have a key named {item}."
            raise ValueError(msg)

        return self.conversion.make_boolean(
            self.conversion.make_none(self._response_data[self.policy_name][item])
        )

    @property
    def all_policies(self) -> dict:
        """
        ### Summary
        Return dict containing all policies, keyed on policy_name.
        """
        if self._all_policies is None:
            return {}
        return self._all_policies

    @property
    def description(self):
        """
        ### Summary
        -   Return the ``policyDescr`` of the policy matching ``policy_name``,
            if it exists.
        -   Return None otherwise.
        """
        return self._get("policyDescr")

    @property
    def epld_image_name(self):
        """
        ### Summary
        -   Return the ``epldImgName`` of the policy matching ``policy_name``,
            if it exists.
        -   Return None otherwise.
        """
        return self._get("epldImgName")

    @property
    def name(self):
        """
        ### Summary
        -   Return the ``name`` of the policy matching ``policy_name``,
            if it exists.
        -   Return None otherwise.
        """
        return self._get("policyName")

    @property
    def policy_name(self):
        """
        ### Summary
        Set the name of the policy to query.

        This must be set prior to accessing any other properties
        """
        return self._policy_name

    @policy_name.setter
    def policy_name(self, value):
        self._policy_name = value

    @property
    def policy(self):
        """
        ### Summary
        -   Return the policy data of the policy matching ``policy_name``,
            if it exists.
        -   Return None otherwise.
        """
        return self._get("policy")

    @property
    def policy_type(self):
        """
        ### Summary
        -   Return the ``policyType`` of the policy matching ``policy_name``,
            if it exists.
        -   Return None otherwise.
        """
        return self._get("policyType")

    @property
    def response_data(self) -> dict:
        """
        ### Summary
        -   Return dict containing the DATA portion of a controller response,
            keyed on ``policy_name``.
        -   Return an empty dict otherwise.
        """
        if self._response_data is None:
            return {}
        return self._response_data

    @property
    def nxos_version(self):
        """
        ### Summary
        -   Return the ``nxosVersion`` of the policy matching ``policy_name``,
            if it exists.
        -   Return None otherwise.
        """
        return self._get("nxosVersion")

    @property
    def package_name(self):
        """
        ### Summary
        -   Return the ``packageName`` of the policy matching ``policy_name``,
            if it exists.
        -   Return None otherwise.
        """
        return self._get("packageName")

    @property
    def platform(self):
        """
        ### Summary
        -   Return the ``platform`` of the policy matching ``policy_name``,
            if it exists.
        -   Return None otherwise.
        """
        return self._get("platform")

    @property
    def platform_policies(self):
        """
        ### Summary
        -   Return the ``platformPolicies`` of the policy matching
            ``policy_name``, if it exists.
        -   Return None otherwise.
        """
        return self._get("platformPolicies")

    @property
    def ref_count(self):
        """
        ### Summary
        -   Return the reference count of the policy matching ``policy_name``,
            if it exists.  The reference count indicates the number of
            switches using this policy.
        -   Return None otherwise.
        """
        return self._get("ref_count")

    @property
    def rpm_images(self):
        """
        ### Summary
        -   Return the ``rpmimages`` of the policy matching ``policy_name``,
            if it exists.
        -   Return None otherwise.
        """
        return self._get("rpmimages")

    @property
    def image_name(self):
        """
        ### Summary
        -   Return the ``imageName`` of the policy matching ``policy_name``,
            if it exists.
        -   Return None otherwise.
        """
        return self._get("imageName")

    @property
    def agnostic(self):
        """
        ### Summary
        -   Return the value of agnostic for the policy matching
            ``policy_name``, if it exists.
        -   Return None otherwise.
        """
        return self._get("agnostic")
