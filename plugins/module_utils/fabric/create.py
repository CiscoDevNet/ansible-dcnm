#
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

from ..common.api.v1.lan_fabric.rest.control.fabrics.fabrics import \
    EpFabricCreate
from .common import FabricCommon
from .fabric_types import FabricTypes


class FabricCreateCommon(FabricCommon):
    """
    Common methods and properties for:
    - FabricCreate
    - FabricCreateBulk
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.action = "fabric_create"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.ep_fabric_create = EpFabricCreate()
        self.fabric_types = FabricTypes()

        # path and verb cannot be defined here because
        # EpFabricCreate().fabric_name must be set first.
        # Set these to None here and define them later in
        # _set_fabric_create_endpoint().
        self.path: str = None
        self.verb: str = None

        self._payloads_to_commit: list = []

        msg = "ENTERED FabricCreateCommon()"
        self.log.debug(msg)

    def _build_payloads_to_commit(self) -> None:
        """
        Build a list of payloads to commit.  Skip any payloads that
        already exist on the controller.

        Expects self.payloads to be a list of dict, with each dict
        being a payload for the fabric create API endpoint.

        Populates self._payloads_to_commit with a list of payloads
        to commit.
        """
        self.fabric_details.refresh()

        self._payloads_to_commit: list = []
        for payload in self.payloads:
            if payload.get("FABRIC_NAME", None) in self.fabric_details.all_data:
                continue
            self._payloads_to_commit.append(copy.deepcopy(payload))

    def _set_fabric_create_endpoint(self, payload):
        """
        - Set the endpoint for the fabric create API call.
        - raise ``ValueError`` if FABRIC_TYPE in the payload is invalid
        - raise ``ValueError`` if the fabric_type to template_name mapping fails
        - raise ``ValueError`` if the fabric_create endpoint assignment fails
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        try:
            self.ep_fabric_create.fabric_name = payload.get("FABRIC_NAME")
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.fabric_type = copy.copy(payload.get("FABRIC_TYPE"))
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.fabric_types.fabric_type = self.fabric_type
            template_name = self.fabric_types.template_name
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.ep_fabric_create.template_name = template_name
        except ValueError as error:
            raise ValueError(error) from error

        payload.pop("FABRIC_TYPE", None)
        self.path = self.ep_fabric_create.path
        self.verb = self.ep_fabric_create.verb

    def _add_ext_fabric_type_to_payload(self, payload: dict) -> dict:
        """
        # Summary

        If the payload contains an external fabric type (e.g ISN)
        and does not contain the EXT_FABRIC_TYPE key, add this
        key with the default value that NDFC GUI uses for displaying
        the fabric type.

        # Raises

        None
        """
        method_name = inspect.stack()[0][3]

        fabric_type = payload.get("FABRIC_TYPE")
        if fabric_type not in self.fabric_types.external_fabric_types:
            return payload
        if "EXT_FABRIC_TYPE" in payload:
            return payload
        value = self.fabric_types.fabric_type_to_ext_fabric_type_map.get(fabric_type)
        if value is None:
            return payload
        payload["EXT_FABRIC_TYPE"] = value

        msg = f"{self.class_name}.{method_name}: "
        msg += "Added EXT_FABRIC_TYPE to payload. "
        msg += f"fabric_type: {fabric_type}, "
        msg += f"value: {value}"
        self.log.debug(msg)
        return payload

    def _send_payloads(self):
        """
        -   If ``check_mode`` is ``False``, send the payloads
            to the controller.
        -   If ``check_mode`` is ``True``, do not send the payloads
            to the controller.
        -   In both cases, register results.
        -   raise ``ValueError`` if the fabric_create endpoint assignment fails

        NOTES:
        -   This overrides the parent class method.
        """
        for payload in self._payloads_to_commit:
            payload = self._add_ext_fabric_type_to_payload(payload)

            try:
                self._set_fabric_create_endpoint(payload)
            except ValueError as error:
                raise ValueError(error) from error

            # For FabricUpdate, the DEPLOY key is mandatory.
            # For FabricCreate, it is not.
            # Remove it if it exists.
            payload.pop("DEPLOY", None)

            # We don't want RestSend to retry on errors since the likelihood of a
            # timeout error when creating a fabric is low, and there are many cases
            # of permanent errors for which we don't want to retry.
            # pylint: disable=no-member
            self.rest_send.timeout = 1

            self.rest_send.path = self.path
            self.rest_send.verb = self.verb
            self.rest_send.payload = payload
            self.rest_send.commit()

            if self.rest_send.result_current["success"] is False:
                self.results.diff_current = {}
            else:
                self.results.diff_current = copy.deepcopy(payload)
            self.results.action = self.action
            self.results.state = self.rest_send.state
            self.results.check_mode = self.rest_send.check_mode
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()

            msg = f"self.results.diff: {json.dumps(self.results.diff, indent=4, sort_keys=True)}"
            self.log.debug(msg)

    @property
    def payloads(self):
        """
        Payloads must be a ``list`` of ``dict`` of payloads for the
        ``fabric_create`` endpoint.

        - getter: Return the fabric create payloads
        - setter: Set the fabric create payloads
        - setter: raise ``ValueError`` if ``payloads`` is not a ``list`` of ``dict``
        - setter: raise ``ValueError`` if any payload is missing mandatory keys
        """
        return self._payloads

    @payloads.setter
    def payloads(self, value):
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"value: {value}"
        self.log.debug(msg)

        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be a list of dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise ValueError(msg)
        for item in value:
            try:
                self._verify_payload(item)
            except ValueError as error:
                raise ValueError(error) from error
        self._payloads = value


class FabricCreateBulk(FabricCreateCommon):
    """
    Create fabrics in bulk.  Skip any fabrics that already exist.

    Usage:

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.create import \
        FabricCreateBulk
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
        Results

    payloads = [
        { "FABRIC_NAME": "fabric1", "BGP_AS": 65000 },
        { "FABRIC_NAME": "fabric2", "BGP_AS": 65001 }
    ]
    results = Results()
    instance = FabricCreateBulk(ansible_module)
    instance.rest_send = RestSend(ansible_module)
    instance.payloads = payloads
    instance.results = results
    instance.commit()
    results.build_final_result()

    # diff contains a dictionary of payloads that succeeded and/or failed
    diff = results.diff
    # result contains the result(s) of the fabric create request
    result = results.result
    # response contains the response(s) from the controller
    response = results.response

    # results.final_result contains all of the above info, and can be passed
    # to the exit_json and fail_json methods of AnsibleModule:

    if True in results.failed:
        msg = "Fabric create failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self._payloads = None
        self.log.debug("ENTERED FabricCreateBulk()")

    def commit(self):
        """
        # create fabrics.

        - Skip any fabrics that already exist on the controller.
        - raise ``ValueError`` if ``payloads`` is not set.
        - raise ``ValueError`` if payload fixup fails.
        - raise ``ValueError`` if sending the payloads fails.
        """
        method_name = inspect.stack()[0][3]

        # pylint: disable=no-member
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit. "
            raise ValueError(msg)

        if self.payloads is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            raise ValueError(msg)

        self._build_payloads_to_commit()

        msg = "self._payloads_to_commit: "
        msg += f"{json.dumps(self._payloads_to_commit, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if len(self._payloads_to_commit) == 0:
            return
        try:
            self._fixup_payloads_to_commit()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self._send_payloads()
        except ValueError as error:
            raise ValueError(error) from error


class FabricCreate(FabricCreateCommon):
    """
    Create a VXLAN fabric on the controller and register the result.

    NOTES:
    -   FabricCreate is NOT used currently, though may be useful in the future.
    -   FabricCreateBulk is used instead.
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self._payload = None
        self.log.debug("ENTERED FabricCreate()")

    def commit(self):
        """
        -   Send the fabric create request to the controller.
        -   raise ``ValueError`` if ``rest_send`` is not set.
        -   raise ``ValueError`` if ``payload`` is not set.
        -   raise ``ValueError`` if ``fabric_create`` endpoint
            assignment fails.
        -   return if the fabric already exists on the controller.

        NOTES:
        -   FabricCreate().commit() is very similar to
            FabricCreateBulk().commit() since we convert the payload
            to a list and leverage the processing that already exists
            in FabricCreateCommom()
        """
        method_name = inspect.stack()[0][3]
        if self.rest_send is None:  # pylint: disable=no-member
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit. "
            raise ValueError(msg)

        if self.payload is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be set prior to calling commit. "
            raise ValueError(msg)

        self._build_payloads_to_commit()

        if len(self._payloads_to_commit) == 0:
            return
        try:
            self._fixup_payloads_to_commit()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self._send_payloads()
        except ValueError as error:
            raise ValueError(error) from error

    @property
    def payload(self):
        """
        Return a fabric create payload.
        """
        return self._payload

    @payload.setter
    def payload(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be a dict. "
            msg += f"Got type {type(value).__name__}, "
            msg += f"value {value}"
            raise ValueError(msg)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload is empty."
            raise ValueError(msg)
        try:
            self._verify_payload(value)
        except ValueError as error:
            raise ValueError(error) from error
        self._payload = value
        # payloads is also set to a list containing one payload.
        # commit() calls FabricCreateCommon()._build_payloads_to_commit(),
        # which expects a list of payloads.
        # FabricCreateCommon()._build_payloads_to_commit() verifies that
        # the fabric does not already exist on the controller.
        self._payloads = [value]
