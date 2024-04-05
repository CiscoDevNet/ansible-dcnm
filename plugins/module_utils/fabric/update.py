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

        self.fabric_details = FabricDetailsByName(self.ansible_module)
        self._fabric_summary = FabricSummary(self.ansible_module)
        self.endpoints = ApiEndpoints()
        self.rest_send = RestSend(self.ansible_module)

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

        msg = "ENTERED FabricUpdateCommon(): "
        msg += f"action: {self.action}, "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

    def _can_fabric_be_deployed(self, fabric_name):
        """
        return True if the fabric configuration can be saved and deployed
        return False otherwise

        NOTES:
        -   If the fabric is empty, the controller will throw an error when
            attempting to deploy the fabric.
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
            self.cannot_deploy_fabric_reason = "Fabric is empty"
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

    def _prepare_payload_value_for_comparison(self, value):
        """
        convert payload values to controller formats

        Comparison order is important.
        bool needs to be checked before int since:
            isinstance(True, int) == True
            isinstance(False, int) == True
        """
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        return value

    def _prepare_anycast_gw_mac_for_comparison(self, fabric_name, mac_address):
        """
        Try to translate the ANYCAST_GW_MAC payload value to the format
        expected by the controller.

        Return the translated mac_address if successful
        Otherwise:
        -   Set results.failed to True
        -   Set results.changed to False
        -   Register the task result
        -   Call fail_json()
        """
        method_name = inspect.stack()[0][3]
        try:
            mac_address = self.translate_mac_address(mac_address)
        except ValueError as error:
            self.results.failed = True
            self.results.changed = False
            self.results.register_task_result()

            msg = f"{self.class_name}.{method_name}: "
            msg += "Error translating ANYCAST_GW_MAC: "
            msg += f"for fabric {fabric_name}, "
            msg += f"ANYCAST_GW_MAC: {mac_address}, "
            msg += f"Error detail: {error}"
            self.ansible_module.fail_json(msg, **self.results.failed_result)
        return mac_address

    def _fabric_needs_update(self, payload):
        """
        -   Return True if the fabric needs to be updated.
        -   Return False otherwise.
        -   Call fail_json() if any payload key would raise an
            error on the controller.

        The fabric needs to be updated if any of the following are true:
        -   A key in the payload has a different value than the corresponding
            key in fabric configuration on the controller.
        """
        method_name = inspect.stack()[0][3]
        fabric_name = payload.get("FABRIC_NAME", None)
        if fabric_name is None:
            return False

        if fabric_name not in self.fabric_details.all_data:
            return False

        nv_pairs = self.fabric_details.all_data[fabric_name].get("nvPairs", {})

        for payload_key, payload_value in payload.items():
            # Translate payload keys to equivilent keys on the controller
            # if necessary.  This handles cases where the controller key
            # is misspelled and we want our users to use the correct
            # spelling.
            if payload_key in self._key_translations:
                key = self._key_translations[payload_key]
            else:
                key = payload_key

            # Skip the FABRIC_TYPE key since the payload FABRIC_TYPE value
            # will be e.g. "VXLAN_EVPN", whereas the fabric configuration will
            # be something along the lines of "Switch_Fabric"
            if key == "FABRIC_TYPE":
                continue

            # self._key_translations returns None for any keys that would not
            # be found in the controller configuration (e.g. DEPLOY).
            # Skip these keys.
            if key is None:
                continue

            # If a key is in the payload that is not in the fabric
            # configuration on the controller:
            # - Update Results()
            # - Call fail_json()
            if nv_pairs.get(key) is None:
                self.results.diff_current = {}
                self.results.result_current = {"success": False, "changed": False}
                self.results.failed = True
                self.results.changed = False
                self.results.failed_result["msg"] = (
                    f"Key {key} not found in fabric configuration for "
                    f"fabric {fabric_name}"
                )
                self.results.register_task_result()
                msg = f"{self.class_name}.{method_name}: "
                msg += f"Invalid key: {key} found in payload for "
                msg += f"fabric {fabric_name}"
                self.log.debug(msg)
                self.ansible_module.fail_json(msg, **self.results.failed_result)

            value = self._prepare_payload_value_for_comparison(payload_value)

            if key == "ANYCAST_GW_MAC":
                value = self._prepare_anycast_gw_mac_for_comparison(fabric_name, value)

            if value != nv_pairs.get(key):
                msg = f"{self.class_name}.{method_name}: "
                msg += f"key {key}: "
                msg += f"payload_value [{value}] != "
                msg += f"fabric_value: [{nv_pairs.get(key)}]: "
                msg += "Fabric needs update."
                self.log.debug(msg)
                return True
        return False

    def _build_payloads_to_commit(self):
        """
        Build a list of payloads to commit.  Skip payloads for fabrics
        that do not exist on the controller

        Expects self.payloads to be a list of dict, with each dict
        being a payload for the fabric create API endpoint.

        Populates self._payloads_to_commit with a list of payloads
        to commit.
        """
        self.fabric_details.refresh()

        self._payloads_to_commit = []
        for payload in self.payloads:
            if payload.get("FABRIC_NAME", None) in self.fabric_details.all_data:
                if self._fabric_needs_update(payload) is False:
                    continue
                self._payloads_to_commit.append(copy.deepcopy(payload))

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
        if True in self.results.failed:
            return
        self._config_save()
        # Skip config-deploy if any errors were encountered with config-save.
        if True in self.results.failed:
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

        self.send_payload_result[payload["FABRIC_NAME"]] = (
            self.rest_send.result_current["success"]
        )
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

            self.config_save_result[fabric_name] = self.rest_send.result_current[
                "success"
            ]
            if self.rest_send.result_current["success"] is False:
                self.results.diff_current = {}
            else:
                self.results.diff_current = {
                    "FABRIC_NAME": fabric_name,
                    "config_save": "OK",
                }

            self.results.action = "config_save"
            self.results.check_mode = self.check_mode
            self.results.state = self.state
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
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
                self.results.diff_current = {
                    "FABRIC_NAME": fabric_name,
                    "config_deploy": "OK",
                }

            self.results.action = "config_deploy"
            self.results.check_mode = self.check_mode
            self.results.state = self.state
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
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
            self.results.result_current = {"success": True, "changed": False}
            msg = "No fabrics to update."
            self.results.response_current = {"RETURN_CODE": 200, "MESSAGE": msg}
            self.results.register_task_result()
            return
        self._send_payloads()
