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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.vxlan.verify_playbook_params import \
    VerifyPlaybookParams


class FabricUpdateCommon(FabricCommon):
    """
    Common methods and properties for:
    - FabricUpdate
    - FabricUpdateBulk
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__
        self.action = "update"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED FabricUpdateCommon(): "
        msg += f"action: {self.action}, "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

        self.fabric_details = FabricDetailsByName(self.ansible_module)
        self._fabric_summary = FabricSummary(self.ansible_module)
        self.endpoints = ApiEndpoints()
        self.rest_send = RestSend(self.ansible_module)
        # self._verify_params = VerifyPlaybookParams(self.ansible_module)


        # path and verb cannot be defined here because endpoints.fabric name
        # must be set first.  Set these to None here and define them later in
        # the commit() method.
        self.path = None
        self.verb = None
        # List of fabrics that have the deploy flag set to True
        # and that are not empty.
        # Updated in _build_fabrics_to_config_deploy()
        self._fabrics_to_config_deploy = []
        # List of fabrics that have the deploy flag set to True
        # Updated in _build_fabrics_to_config_save()
        self._fabrics_to_config_save = []

        self._payloads_to_commit = []

        # Number of successful fabric update payloads
        # Used to determine if all fabric updates were successful
        self.successful_fabric_payloads = 0

        self.cannot_deploy_fabric_reason = ""

        self._mandatory_payload_keys = set()
        self._mandatory_payload_keys.add("FABRIC_NAME")
        self._mandatory_payload_keys.add("DEPLOY")

        # key: fabric_name, value: boolean
        # If True, the operation was successful
        # If False, the operation was not successful
        self.config_save_result = {}
        self.config_deploy_result = {}
        self.send_payload_result = {}

    def _can_fabric_be_deployed(self, fabric_name):
        """
        return True if the fabric configuration can be saved and deployed
        return False otherwise
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "ENTERED"
        self.log.debug(msg)
        self._fabric_summary.fabric_name = fabric_name
        self._fabric_summary.refresh()
        msg = "self._fabric_summary.fabric_is_empty: "
        msg += f"{self._fabric_summary.fabric_is_empty}"
        self.log.debug(msg)
        if self._fabric_summary.fabric_is_empty is True:
            self.cannot_deploy_fabric_reason = "Fabric is not empty"
            return False
        return True

    def _verify_payload(self, payload):
        """
        Verify that the payload is a dict and contains all mandatory keys
        """
        method_name = inspect.stack()[0][3]
        if not isinstance(payload, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be a dict. "
            msg += f"Got type {type(payload).__name__}, "
            msg += f"value {payload}"
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        missing_keys = []
        for key in self._mandatory_payload_keys:
            if key not in payload:
                missing_keys.append(key)
        if len(missing_keys) == 0:
            return

        msg = f"{self.class_name}.{method_name}: "
        msg += "payload is missing mandatory keys: "
        msg += f"{sorted(missing_keys)}. "
        msg += f"payload: {sorted(payload)}"
        self.ansible_module.fail_json(msg, **self.results.failed_result)

    def _build_payloads_to_commit(self):
        """
        Build a list of payloads to commit.  Skip any payloads that
        already exist on the controller.

        Expects self.payloads to be a list of dict, with each dict
        being a payload for the fabric create API endpoint.

        Populates self._payloads_to_commit with a list of payloads
        to commit.
        """
        self.fabric_details.refresh()

        self._payloads_to_commit = []
        for payload in self.payloads:
            if payload.get("FABRIC_NAME", None) in self.fabric_details.all_data:
                self._payloads_to_commit.append(copy.deepcopy(payload))

    def _fixup_payloads_to_commit(self):
        """
        Make any modifications to the payloads prior to sending them
        to the controller.

        Add any modifications to the list below.

        - Translate ANYCAST_GW_MAC to a format the controller understands
        """
        for payload in self._payloads_to_commit:
            if "ANYCAST_GW_MAC" in payload:
                payload["ANYCAST_GW_MAC"] = self.translate_mac_address(
                    payload["ANYCAST_GW_MAC"]
                )

    def _send_payloads(self):
        """
        If check_mode is False, send the payloads to the controller
        If check_mode is True, do not send the payloads to the controller

        In both cases, update results
        """
        self.rest_send.check_mode = self.check_mode

        self._build_fabrics_to_config_deploy()
        self._fixup_payloads_to_commit()
        for payload in self._payloads_to_commit:
            self._send_payload(payload)

        # Skip config-save if any errors were encountered with fabric updates.
        if len(self.results.result_nok) != 0:
            return
        self._config_save()
        # Skip config-deploy if any errors were encountered with config-save.
        if len(self.results.result_nok) != 0:
            return
        self._config_deploy()

    def _build_fabrics_to_config_deploy(self):
        """
        Build a list of fabrics to config-deploy and config-save

        This also removes the DEPLOY key from the payload

        Skip:
        - payloads without FABRIC_NAME key (shouldn't happen, but just in case)
        - fabrics with DEPLOY key set to False
        - Empty fabrics (these cannot be config-deploy'ed or config-save'd)
        """
        method_name = inspect.stack()[0][3]
        for payload in self._payloads_to_commit:
            fabric_name = payload.get("FABRIC_NAME", None)
            if fabric_name is None:
                continue
            deploy = payload.pop("DEPLOY", None)
            if deploy is not True:
                continue
            if self._can_fabric_be_deployed(fabric_name) is False:
                continue

            msg = f"{self.class_name}.{method_name}: "
            msg += f"_can_fabric_be_deployed: {self._can_fabric_be_deployed(fabric_name)}, "
            msg += (
                f"self.cannot_deploy_fabric_reason: {self.cannot_deploy_fabric_reason}"
            )
            self.log.debug(msg)

            msg = f"{self.class_name}.{method_name}: "
            msg += f"Adding fabric_name: {fabric_name}"
            self.log.debug(msg)

            self._fabrics_to_config_deploy.append(fabric_name)
            self._fabrics_to_config_save.append(fabric_name)

    def _set_fabric_update_endpoint(self, payload):
        """
        Set the endpoint for the fabric create API call.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self.endpoints.fabric_name = payload.get("FABRIC_NAME")
        self.fabric_type = copy.copy(payload.get("FABRIC_TYPE"))
        self.endpoints.template_name = self.fabric_type_to_template_name(
            self.fabric_type
        )
        try:
            endpoint = self.endpoints.fabric_update
        except ValueError as error:
            self.ansible_module.fail_json(error)

        payload.pop("FABRIC_TYPE", None)
        self.path = endpoint["path"]
        self.verb = endpoint["verb"]

    def _send_payload(self, payload):
        """
        Send one fabric update payload
        """
        method_name = inspect.stack()[0][3]
        self._set_fabric_update_endpoint(payload)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"verb: {self.verb}, path: {self.path}, "
        msg += f"payload: {json.dumps(payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # We don't want RestSend to retry on errors since the likelihood of a
        # timeout error when updating a fabric is low, and there are many cases
        # of permanent errors for which we don't want to retry.
        self.rest_send.timeout = 1

        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.payload = payload
        self.rest_send.commit()

        if self.rest_send.result_current["success"] is False:
            self.results.diff_current = {}
        else:
            self.results.diff_current = copy.deepcopy(payload)

        self.send_payload_result[payload["FABRIC_NAME"]] = self.rest_send.result_current["success"]
        self.results.action = self.action
        self.results.check_mode = self.check_mode
        self.results.state = self.state
        self.results.response_current = copy.deepcopy(self.rest_send.response_current)
        self.results.result_current = copy.deepcopy(self.rest_send.result_current)
        self.results.register_task_result()

    def _config_save(self):
        """
        Save the fabric configuration to the controller
        """
        method_name = inspect.stack()[0][3]
        for fabric_name in self._fabrics_to_config_save:
            msg = f"{self.class_name}.{method_name}: fabric_name: {fabric_name}"
            self.log.debug(msg)
            if fabric_name not in self.send_payload_result:
                # Skip config-save if send_payload failed
                msg = f"{self.class_name}.{method_name}: "
                msg += f"WARNING: fabric_name: {fabric_name} not in send_payload_result"
                self.log.debug(msg)
                continue
            if self.send_payload_result[fabric_name] is False:
                # Skip config-save if send_payload failed
                # Set config_save_result to False so that config_deploy is skipped
                self.config_save_result[fabric_name] = False
                continue

            try:
                self.endpoints.fabric_name = fabric_name
                self.path = self.endpoints.fabric_config_save.get("path")
                self.verb = self.endpoints.fabric_config_save.get("verb")
            except ValueError as error:
                self.ansible_module.fail_json(error, **self.results.failed_result)

            self.rest_send.path = self.path
            self.rest_send.verb = self.verb
            self.rest_send.payload = None
            self.rest_send.commit()

            self.config_save_result[fabric_name] = self.rest_send.result_current["success"]
            if self.rest_send.result_current["success"] is False:
                self.results.diff_current = {}
            else:
                self.results.diff_current = {"FABRIC_NAME": fabric_name, "config_save": "OK"}

            self.results.action = "config_save"
            self.results.check_mode = self.check_mode
            self.results.state = self.state
            self.results.response_current = copy.deepcopy(self.rest_send.response_current)
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()

            self.config_save_result = self.rest_send.result_current

    def _config_deploy(self):
        """
        Deploy the fabric configuration to the controller
        """
        method_name = inspect.stack()[0][3]
        for fabric_name in self._fabrics_to_config_deploy:
            msg = f"{self.class_name}.{method_name}: fabric_name: {fabric_name}"
            self.log.debug(msg)

            if self.config_save_result.get(fabric_name) is False:
                # Skip config-deploy if config-save failed
                continue

            try:
                self.endpoints.fabric_name = fabric_name
                self.path = self.endpoints.fabric_config_deploy.get("path")
                self.verb = self.endpoints.fabric_config_deploy.get("verb")
            except ValueError as error:
                self.ansible_module.fail_json(error, **self.results.failed_result)

            self.rest_send.path = self.path
            self.rest_send.verb = self.verb
            self.rest_send.payload = None
            self.rest_send.commit()

            self.config_deploy_result = self.rest_send.result_current["success"]
            if self.rest_send.result_current["success"] is False:
                self.results.diff_current = {}
                self.results.diff = {"FABRIC_NAME": fabric_name, "config_deploy": "OK"}
            else:
                self.results.diff_current = {"FABRIC_NAME": fabric_name, "config_deploy": "OK"}

            self.results.action = "config_deploy"
            self.results.check_mode = self.check_mode
            self.results.state = self.state
            self.results.response_current = copy.deepcopy(self.rest_send.response_current)
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
            self.results.register_task_result()

    @property
    def payloads(self):
        """
        Return the fabric create payloads

        Payloads must be a list of dict. Each dict is a
        payload for the fabric create API endpoint.
        """
        return self.properties["payloads"]

    @payloads.setter
    def payloads(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be a list of dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg, **self.results.failed_result)
        for item in value:
            self._verify_payload(item)
        self.properties["payloads"] = value


class FabricUpdateBulk(FabricUpdateCommon):
    """
    Update fabrics in bulk.

    Usage:
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.update import \
        FabricUpdateBulk
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
        Results

    payloads = [ 
        { "FABRIC_NAME": "fabric1", "BGP_AS": 65000, "DEPLOY": True },
        { "FABRIC_NAME": "fabric2", "BGP_AS": 65001, "DEPLOY: False }
    ]
    results = Results()
    instance = FabricUpdateBulk(ansible_module)
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
        msg = "Fabric update(s) failed."
        ansible_module.fail_json(msg, **task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricUpdateBulk()")

        self._build_properties()

    def _build_properties(self):
        """
        Add properties specific to this class
        """
        # properties dict is already initialized in the parent class
        self.properties["payloads"] = None

    def commit(self):
        """
        Update fabrics.
        """
        method_name = inspect.stack()[0][3]
        if self.payloads is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payloads must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        self.results.action = self.action
        self.results.check_mode = self.check_mode
        self.results.state = self.state

        self._build_payloads_to_commit()
        if len(self._payloads_to_commit) == 0:
            self.results.diff_current = {}
            self.results.result_current = {"success": True}
            msg = "No fabrics to create."
            self.results.response_current = {"RETURN_CODE": 200, "MESSAGE": msg}
            self.results.register_task_result()
            return
        self._send_payloads()
        


class FabricUpdate(FabricUpdateCommon):
    """
    Update a fabric on the controller.
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricUpdate()")

        self.data = {}
        self.endpoints = ApiEndpoints()
        self.rest_send = RestSend(self.ansible_module)

        self._init_properties()

    def _init_properties(self):
        # self.properties is already initialized in the parent class
        self.properties["payload"] = None

    def commit(self):
        """
        Send the fabric create request to the controller.
        """
        method_name = inspect.stack()[0][3]
        if self.payload is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Exiting. Missing mandatory property: payload"
            self.ansible_module.fail_json(msg)

        if len(self.payload) == 0:
            self.ansible_module.exit_json(**self.results.failed_result)

        fabric_name = self.payload.get("FABRIC_NAME")
        if fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload is missing mandatory FABRIC_NAME key."
            self.ansible_module.fail_json(msg)

        self.endpoints.fabric_name = fabric_name
        self.endpoints.template_name = "Easy_Fabric"
        try:
            endpoint = self.endpoints.fabric_create
        except ValueError as error:
            self.ansible_module.fail_json(error)

        path = endpoint["path"]
        verb = endpoint["verb"]

        self.rest_send.path = path
        self.rest_send.verb = verb
        self.rest_send.payload = self.payload
        self.rest_send.commit()

        if self.rest_send.result_current["success"] is False:
            self.results.diff_current = {}
        else:
            self.results.diff_current = self.payload

        self.results.action = self.action
        self.results.check_mode = self.check_mode
        self.results.state = self.state
        self.results.result_current = self.rest_send.result_current
        self.results.response_current = self.rest_send.response_current
        self.results.register_task_result()

    @property
    def payload(self):
        """
        Return a fabric create payload.
        """
        return self.properties["payload"]

    @payload.setter
    def payload(self, value):
        self.properties["payload"] = value
