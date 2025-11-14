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
import json
import logging

from ..common.api.v1.imagemanagement.rest.policymgnt.policymgnt import \
    EpPolicyCreate
from ..common.properties import Properties
from ..common.results import Results
from .image_policies import ImagePolicies


@Properties.add_rest_send
@Properties.add_results
@Properties.add_params
class ImagePolicyCreateCommon:
    """
    ### Summary
    Common methods and properties for:
    - ImagePolicyCreate
    - ImagePolicyCreateBulk

    See respective class docstrings for more information.
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.action = "create"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._image_policies = ImagePolicies()
        self._image_policies.results = Results()

        self.endpoint = EpPolicyCreate()
        self.path = self.endpoint.path
        self.verb = self.endpoint.verb

        self._payloads_to_commit = []

        self._mandatory_payload_keys = set()
        self._mandatory_payload_keys.add("nxosVersion")
        self._mandatory_payload_keys.add("policyName")
        self._mandatory_payload_keys.add("policyType")

        self._params = None
        self._payload = None
        self._payloads = None
        self._rest_send = None
        self._results = None

        msg = "ENTERED ImagePolicyCreateCommon(): "
        msg += f"action: {self.action}, "
        self.log.debug(msg)

    def verify_payload(self, payload):
        """
        ### Summary
        Verify that the payload is a dict and contains all mandatory keys.

        ### Raises
        -   ``TypeError`` if payload is not a dict.
        -   ``ValueError`` if payload is missing mandatory keys.
        """
        method_name = inspect.stack()[0][3]
        if not isinstance(payload, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be a dict. "
            msg += f"Got type {type(payload).__name__}, "
            msg += f"value {payload}."
            raise TypeError(msg)

        missing_keys = []
        for key in self._mandatory_payload_keys:
            if key not in payload:
                missing_keys.append(key)
        if len(missing_keys) == 0:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += "payload is missing mandatory keys: "
        msg += f"{sorted(missing_keys)}"
        raise ValueError(msg)

    def build_payloads_to_commit(self):
        """
        ### Summary
        Build a list of payloads to commit.  Skip any payloads that
        already exist on the controller.

        ### Raises
        None

        ### Notes
        Expects self.payloads to be a list of dict, with each dict
        being a payload for endpoint ``EpPolicyCreate()``.

        Populate ``self._payloads_to_commit`` with a list of payloads
        to commit.
        """
        method_name = inspect.stack()[0][3]

        self._image_policies.rest_send = self.rest_send  # pylint: disable=no-member
        self._image_policies.refresh()

        self._payloads_to_commit = []
        for payload in self.payloads:
            if payload.get("policyName") in self._image_policies.all_policies:
                continue
            self._payloads_to_commit.append(copy.deepcopy(payload))
        msg = f"{self.class_name}.{method_name}: "
        msg += "self._payloads_to_commit: "
        msg += f"{json.dumps(self._payloads_to_commit, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    # pylint: disable=no-member
    def send_payloads(self):
        """
        ### Summary
        -   If check_mode is False, send the payloads to the controller.
        -   If check_mode is True, do not send the payloads to the controller.
        -   In both cases, update results.

        ### Raises
        None
        """
        self.rest_send.check_mode = self.params.get("check_mode")

        for payload in self._payloads_to_commit:

            # We don't want RestSend to retry on errors since the likelihood of a
            # timeout error when creating an image policy is low, and there are
            # cases of permanent errors for which we don't want to retry.
            self.rest_send.timeout = 1

            self.rest_send.path = self.path
            self.rest_send.verb = self.verb
            self.rest_send.payload = payload
            self.rest_send.commit()

            msg = "rest_send.result_current: "
            msg += (
                f"{json.dumps(self.rest_send.result_current, indent=4, sort_keys=True)}"
            )
            self.log.debug(msg)

            if self.rest_send.result_current["success"] is False:
                self.results.diff_current = {}
            else:
                self.results.diff_current = copy.deepcopy(payload)

            self.results.action = self.action
            self.results.state = self.params.get("state")
            self.results.check_mode = self.params.get("check_mode")
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()

    @property
    def payloads(self):
        """
        ### Summary
        Return the image policy payloads.

        Payloads must be a list of dict. Each dict is a payload for endpoint
        ``EpPolicyCreate()``.

        ### Raises
        -   ``TypeError`` if:
                -   ``payloads`` is not a list.
                -   Any element within ``payloads`` is not a dict.
                -   Any element within ``payloads`` is missing mandatory keys.
        """
        return self._payloads

    @payloads.setter
    def payloads(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        if not isinstance(value, list):
            msg += "payloads must be a list of dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        msg += "Error verifying payload: "
        for item in value:
            try:
                self.verify_payload(item)
            except ValueError as error:
                msg += f"{error}"
                raise ValueError(msg) from error
            except TypeError as error:
                msg += f"{error}"
                raise TypeError(msg) from error
        self._payloads = value


class ImagePolicyCreateBulk(ImagePolicyCreateCommon):
    """
    ### Summary
    Given a properly-constructed list of payloads, bulk-create the
    image policies therein.  The payload format is given below.

    ### Raises
    -   ``ValueError`` if
            -   ``payloads`` is not set prior to calling ``commit``.
            -   ``rest_send`` is not set prior to calling ``commit``.
            -   ``results`` is not set prior to calling ``commit``.
            -   ``params`` is not set prior to calling ``commit``.
    -   ``TypeError`` if
            -   ``payloads`` is not a list.
            -   ``payload`` is not a dict.

    ### Payload format
    ```
    agnostic        bool(), optional. true or false
    epldImgName     str(), optional. name of an EPLD image to install.
    nxosVersion     str(), required. NX-OS version as version_type_arch
    packageName:    str(), optional, A comma-separated list of packages
    platform:       str(), optional, one of N9K, N6K, N5K, N3K
    policyDesc      str(), optional, description for the image policy
    policyName:     str(), required.  Name of the image policy.
    policyType      str(), required. PLATFORM or UMBRELLA
    rpmimages:      str(), optional. A comma-separated list of packages to uninstall
    ```

    ### Example list of payloads:
    ```json
    [
        {
            "agnostic": False,
            "epldImgName": "n9000-epld.10.3.2.F.img",
            "nxosVersion": "10.3.1_nxos64-cs_64bit",
            "packageName": "mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm",
            "platform": "N9K",
            "policyDescr": "image policy of 10.3(3)F",
            "policyName": "FOO",
            "policyType": "PLATFORM",
            "rpmimages": "mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000"
        },
        {
            "nxosVersion": "10.3.1_nxos64-cs_64bit",
            "policyName": "FOO",
            "policyType": "PLATFORM"
        }
    ]
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED ImagePolicyCreateBulk():"
        self.log.debug(msg)

    def commit(self):
        """
        ### Summary
        Create policies.  Skip policies that exist on the controller.

        ### Raises
        -   ``ValueError`` if:
                -   ``params`` is not set prior to calling ``commit``.
                -   ``payloads`` is not set prior to calling ``commit``.
                -   ``rest_send`` is not set prior to calling ``commit``.
                -   ``results`` is not set prior to calling ``commit``.
        """
        method_name = inspect.stack()[0][3]

        if self.params is None:  # pylint: disable=no-member
            msg = f"{self.class_name}.{method_name}: "
            msg += "params must be set prior to calling commit."
            raise ValueError(msg)

        if self.payloads is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            raise ValueError(msg)

        if self.rest_send is None:  # pylint: disable=no-member
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit."
            raise ValueError(msg)

        if self.results is None:  # pylint: disable=no-member
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set prior to calling commit."
            raise ValueError(msg)

        self.build_payloads_to_commit()
        if len(self._payloads_to_commit) == 0:
            return
        self.send_payloads()


class ImagePolicyCreate(ImagePolicyCreateCommon):
    """
    ### Summary
    This class is not used by dcnm_image_policy.

    Given an image policy payload, send an image policy create request
    to controller endpoint ``EpPolicyCreate()``.

    ### Raises
    -   ``ValueError`` if:
            -   ``payload`` is not set prior to calling ``commit``.
            -   ``rest_send`` is not set prior to calling ``commit``.
            -   ``results`` is not set prior to calling ``commit``.
            -   ``params`` is not set prior to calling ``commit``.
    -   ``TypeError`` if:
            -   ``payload`` is not a dict.

    ### Payload format
    ```
    agnostic        bool(), optional. true or false
    epldImgName     str(), optional. name of an EPLD image to install.
    nxosVersion     str(), required. NX-OS version as version_type_arch
    packageName:    str(), optional, A comma-separated list of packages
    platform:       str(), optional, one of N9K, N6K, N5K, N3K
    policyDesc      str(), optional, description for the image policy
    policyName:     str(), required.  Name of the image policy.
    policyType      str(), required. PLATFORM or UMBRELLA
    rpmimages:      str(), optional. A comma-separated list of packages to uninstall
    ```

    ### Example payload
    ```json
    {
        "agnostic": false,
        "epldImgName": "n9000-epld.10.3.2.F.img",
        "nxosVersion": "10.3.1_nxos64-cs_64bit",
        "packageName": "mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm",
        "platform": "N9K",
        "policyDescr": "image policy of 10.3(3)F",
        "policyName": "FOO",
        "policyType": "PLATFORM",
        "rpmimages": "mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000"
    }
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED ImagePolicyCreate(): "
        self.log.debug(msg)

        self.data = {}

    @property
    def payload(self):
        """
        ### Summary
        An image policy payload. See class docstring for the payload structure.

        ### Raises
        -   ``TypeError`` if payload is not a dict.
        """
        return self._payload

    @payload.setter
    def payload(self, value):
        self.verify_payload(value)
        self._payloads = [value]
        self._payload = value

    def commit(self):
        """
        ### Summary
        Create policy. If policy already exists on the controller, do nothing.

        ### Raises
        -   ``ValueError`` if:
                -   ``params`` is not set prior to calling ``commit``.
                -   ``payload`` is not set prior to calling ``commit``.
                -   ``rest_send`` is not set prior to calling ``commit``.
                -   ``results`` is not set prior to calling ``commit``.
        """
        method_name = inspect.stack()[0][3]
        if self.params is None:  # pylint: disable=no-member
            msg = f"{self.class_name}.{method_name}: "
            msg += "params must be set prior to calling commit."
            raise ValueError(msg)

        if self.payload is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be set prior to calling commit."
            raise ValueError(msg)

        if self.rest_send is None:  # pylint: disable=no-member
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit."
            raise ValueError(msg)

        if self.results is None:  # pylint: disable=no-member
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set prior to calling commit."
            raise ValueError(msg)

        self.build_payloads_to_commit()

        if len(self._payloads_to_commit) == 0:
            return
        self.send_payloads()
