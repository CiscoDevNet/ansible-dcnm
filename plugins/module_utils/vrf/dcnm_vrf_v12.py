# -*- coding: utf-8 -*-
# mypy: disable-error-code="import-untyped"
#
# Copyright (c) 2020-2025 Cisco and/or its affiliates.
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
# pylint: disable=wrong-import-position
from __future__ import absolute_import, division, print_function

# pylint: disable=invalid-name
__metaclass__ = type
__author__ = "Shrishail Kariyappanavar, Karthik Babu Harichandra Babu, Praveen Ramoorthy, Allen Robel"
# pylint: enable=invalid-name
"""
"""
import copy
import inspect
import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Final, Optional, Union

from ansible.module_utils.basic import AnsibleModule
from pydantic import ValidationError

from ...module_utils.common.api.v1.lan_fabric.rest.top_down.fabrics.vrfs.vrfs import EpVrfGet, EpVrfPost
from ...module_utils.common.enums.http_requests import RequestVerb
from ...module_utils.network.dcnm.dcnm import dcnm_get_ip_addr_info, dcnm_send, get_fabric_details, get_fabric_inventory_details, get_sn_fabric_dict
from .inventory_ipv4_to_serial_number import InventoryIpv4ToSerialNumber
from .inventory_ipv4_to_switch_role import InventoryIpv4ToSwitchRole
from .inventory_serial_number_to_ipv4 import InventorySerialNumberToIpv4
from .inventory_serial_number_to_switch_role import InventorySerialNumberToSwitchRole
from .model_controller_response_generic_v12 import ControllerResponseGenericV12
from .model_controller_response_get_fabrics_vrfinfo import ControllerResponseGetFabricsVrfinfoV12
from .model_controller_response_get_int import ControllerResponseGetIntV12
from .model_controller_response_vrfs_attachments_v12 import ControllerResponseVrfsAttachmentsDataItem, ControllerResponseVrfsAttachmentsV12
from .model_controller_response_vrfs_deployments_v12 import ControllerResponseVrfsDeploymentsV12
from .model_controller_response_vrfs_switches_v12 import ControllerResponseVrfsSwitchesDataItem, ControllerResponseVrfsSwitchesV12
from .model_controller_response_vrfs_v12 import ControllerResponseVrfsV12, VrfObjectV12
from .model_have_attach_post_mutate_v12 import HaveAttachPostMutate, HaveLanAttachItem
from .model_payload_vrfs_attachments import PayloadVrfsAttachmentsLanAttachListItem
from .model_payload_vrfs_deployments import PayloadfVrfsDeployments
from .model_playbook_vrf_v12 import PlaybookVrfAttachModel, PlaybookVrfModelV12, PlaybookVrfLiteModel
from .model_vrf_detach_payload_v12 import LanDetachListItemV12, VrfDetachPayloadV12
from .transmute_diff_attach_to_payload import DiffAttachToControllerPayload
from .vrf_controller_payload_v12 import VrfPayloadV12
from .vrf_controller_to_playbook_v12 import VrfControllerToPlaybookV12Model
from .vrf_template_config_v12 import VrfTemplateConfigV12
from .vrf_utils import get_endpoint_with_long_query_string

dcnm_vrf_paths: dict = {
    "GET_VRF_ATTACH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs/attachments?vrf-names={}",
    "GET_VRF_SWITCH": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfs/switches?vrf-names={}&serial-numbers={}",
    "GET_VRF_ID": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/vrfinfo",
    "GET_VLAN": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_VRF_VLAN",
}


@dataclass
class SendToControllerArgs:
    """
    # Summary

    Arguments for DcnmVrf.send_to_controller()

    ## params

    -   `action`: The action to perform (create, update, delete, etc.)
    -   `verb`: The HTTP verb to use (GET, POST, PUT, DELETE)
    -   `path`: The endpoint path for the request
    -   `payload`: The payload to send with the request (None for no payload)
    -   `log_response`: If True, log the response in the result, else
        do not include the response in the result
    -   `is_rollback`: If True, attempt to rollback on failure
    -   `response_model`: Optional[Any] = None

    """

    action: str
    verb: RequestVerb
    path: str
    payload: Optional[Union[dict, list]]
    log_response: bool = True
    is_rollback: bool = False
    response_model: Optional[Any] = None

    dict = asdict


class NdfcVrf12:
    """
    # Summary

    dcnm_vrf module implementation for NDFC version 12
    """

    def __init__(self, module: AnsibleModule):
        self.class_name: str = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        # Temporary hack to determine of usage of Pydantic models is enabled.
        # If True, model-based methods are used.
        # If False, legacy methods are used.
        # Do not set this to True here.  It's set/unset strategically
        # as needed and will be removed once all methods are modified
        # to use Pydantic models.
        self.model_enabled: bool = False

        self.module: AnsibleModule = module
        self.params: dict[str, Any] = module.params

        try:
            self.state: str = self.params["state"]
        except KeyError:
            msg = f"{self.class_name}.__init__(): "
            msg += "'state' parameter is missing from params."
            module.fail_json(msg=msg)

        try:
            self.fabric: str = module.params["fabric"]
        except KeyError:
            msg = f"{self.class_name}.__init__(): "
            msg += "fabric missing from params."
            module.fail_json(msg=msg)

        msg = f"self.state: {self.state}, "
        msg += "self.params: "
        msg += f"{json.dumps(self.params, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.config: Optional[list[dict]] = copy.deepcopy(module.params.get("config"))

        msg = f"self.state: {self.state}, "
        msg += "self.config: "
        msg += f"{json.dumps(self.config, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # Setting self.conf_changed to class scope since, after refactoring,
        # it is initialized and updated in one refactored method
        # (diff_merge_create) and accessed in another refactored method
        # (diff_merge_attach) which reset it to {} at the top of the method
        # (which undid the update in diff_merge_create).
        # TODO: Revisit this in Phase 2 refactoring.
        self.conf_changed: dict = {}
        self.check_mode: bool = False
        self.have_create: list[dict] = []
        self.want_create: list[dict] = []
        # Will eventually replace self.want_create with self.want_create_payload_models
        self.want_create_payload_models: list[VrfPayloadV12] = []
        self.diff_create: list = []
        self.diff_create_update: list = []
        # self.diff_create_quick holds all the create payloads which are
        # missing a vrfId. These payloads are sent to DCNM out of band
        # (in the get_diff_merge()).  We lose diffs for these without this
        # variable. The content stored here will be helpful for cases like
        # "check_mode" and to print diffs[] in the output of each task.
        self.diff_create_quick: list = []
        # self.have_attach is accessed only in self.failure() and is populated in populate_have_attach_models()
        # It will eventually be removed.
        self.have_attach: list = []
        self.have_attach_models: list[HaveAttachPostMutate] = []
        self.want_attach: list = []
        self.want_attach_vrf_lite: dict = {}
        self.diff_attach: list = []
        self.validated_playbook_config: list = []
        self.validated_playbook_config_models: list[PlaybookVrfModelV12] = []
        # diff_detach contains all attachments of a vrf being deleted,
        # especially for state: OVERRIDDEN
        # The diff_detach and delete operations have to happen before
        # create+attach+deploy for vrfs being created. This is to address
        # cases where VLAN from a vrf which is being deleted is used for
        # another vrf. Without this additional logic, the create+attach+deploy
        # go out first and complain the VLAN is already in use.
        self.diff_detach: list = []
        self.have_deploy: dict = {}
        self.have_deploy_model: PayloadfVrfsDeployments = None
        self.want_deploy: dict = {}
        self.want_deploy_model: PayloadfVrfsDeployments = None
        # A playbook configuration model representing what was changed
        self.diff_deploy: dict = {}
        self.diff_undeploy: dict = {}
        self.diff_delete: dict = {}
        self.diff_input_format: list = []
        self.query: list = []

        self.inventory_data: dict = get_fabric_inventory_details(self.module, self.fabric)
        self.ipv4_to_serial_number = InventoryIpv4ToSerialNumber()
        self.ipv4_to_switch_role = InventoryIpv4ToSwitchRole()
        self.serial_number_to_ipv4 = InventorySerialNumberToIpv4()
        self.serial_number_to_switch_role = InventorySerialNumberToSwitchRole()

        self.ipv4_to_serial_number.fabric_inventory = self.inventory_data
        self.ipv4_to_switch_role.fabric_inventory = self.inventory_data
        self.serial_number_to_ipv4.fabric_inventory = self.inventory_data
        self.serial_number_to_switch_role.fabric_inventory = self.inventory_data

        msg = "self.inventory_data: "
        msg += f"{json.dumps(self.inventory_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.fabric_data: dict = get_fabric_details(self.module, self.fabric)

        msg = "self.fabric_data: "
        msg += f"{json.dumps(self.fabric_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        try:
            self.fabric_type: str = self.fabric_data["fabricType"]
        except KeyError:
            msg = f"{self.class_name}.__init__(): "
            msg += "'fabricType' parameter is missing from self.fabric_data."
            self.module.fail_json(msg=msg)

        try:
            self.sn_fab: dict = get_sn_fabric_dict(self.inventory_data)
        except ValueError as error:
            msg += f"{self.class_name}.__init__(): {error}"
            module.fail_json(msg=msg)

        self.paths: dict = dcnm_vrf_paths

        self.result: dict[str, Any] = {"changed": False, "diff": [], "response": []}

        self.failed_to_rollback: bool = False
        self.wait_time_for_delete_loop: Final[int] = 5  # in seconds

        self.vrf_lite_properties: Final[list[str]] = [
            "DOT1Q_ID",
            "IF_NAME",
            "IP_MASK",
            "IPV6_MASK",
            "IPV6_NEIGHBOR",
            "NEIGHBOR_IP",
            "PEER_VRF_NAME",
        ]

        # Controller responses
        self.response: dict = {}
        self.log.debug("DONE")

    def set_model_enabled_true(self) -> None:
        """
        Temporary method to set self.model_enabled to True.

        Will be removed once all methods are refactored to use Pydantic models.
        """
        caller = inspect.stack()[1][3]
        msg = f"{caller} Setting self.model_enabled to True."
        self.log.debug(msg)
        self.model_enabled = True

    def set_model_enabled_false(self) -> None:
        """
        Temporary method to set self.model_enabled to False.

        Will be removed once all methods are refactored to use Pydantic models.
        """
        caller = inspect.stack()[1][3]
        msg = f"{caller} Setting self.model_enabled to False."
        self.log.debug(msg)
        self.model_enabled = False

    def log_list_of_models(self, model_list: list, by_alias: bool = False) -> None:
        """
        # Summary

        Log a list of Pydantic models.
        """
        caller = inspect.stack()[1][3]
        for index, model in enumerate(model_list):
            msg = f"caller: {caller}: by_alias={by_alias}, index {index}. "
            msg += f"{json.dumps(model.model_dump(by_alias=by_alias), indent=4, sort_keys=True)}"
            self.log.debug(msg)

    @staticmethod
    def get_list_of_lists(lst: list, size: int) -> list[list]:
        """
        # Summary

        Given a list of items (lst) and a chunk size (size), return a
        list of lists, where each list is size items in length.

        ## Raises

        -    ValueError if:
                -    lst is not a list.
                -    size is not an integer

        ## Example

        print(get_lists_of_lists([1,2,3,4,5,6,7], 3)

        # -> [[1, 2, 3], [4, 5, 6], [7]]
        """
        if not isinstance(lst, list):
            msg = "lst must be a list(). "
            msg += f"Got {type(lst)}."
            raise ValueError(msg)
        if not isinstance(size, int):
            msg = "size must be an integer. "
            msg += f"Got {type(size)}."
            raise ValueError(msg)
        return [lst[x : x + size] for x in range(0, len(lst), size)]

    @staticmethod
    def find_dict_in_list_by_key_value(search: Optional[list[dict[Any, Any]]], key: str, value: str) -> dict[Any, Any]:
        """
        # Summary

        Find a dictionary in a list of dictionaries.


        ## Raises

        None

        ## Parameters

        -   search: A list of dict, or None
        -   key: The key to lookup in each dict
        -   value: The desired matching value for key

        ## Returns

        Either the first matching dict or an empty dict

        ## Usage

        ```python
        content = [{"foo": "bar"}, {"foo": "baz"}]

        match = find_dict_in_list_by_key_value(search=content, key="foo", value="baz")
        print(f"{match}")
        # -> {"foo": "baz"}

        match = find_dict_in_list_by_key_value(search=content, key="foo", value="bingo")
        print(f"{match}")
        # -> {}

        match = find_dict_in_list_by_key_value(search=None, key="foo", value="bingo")
        print(f"{match}")
        # -> {}
        ```
        """
        if search is None:
            return {}
        for item in search:
            match = item.get(key)
            if match == value:
                return item
        return {}

    def find_model_in_list_by_key_value(self, search: Optional[list], key: str, value: str) -> Any:
        """
        # Summary

        Find a model in a list of models and return the matching model.


        ## Raises

        None

        ## Parameters

        -   search: A list of models, or None
        -   key: The key to lookup in each model
        -   value: The desired matching value for key

        ## Raises

        - None

        ## Returns

        Either the first matching model or None
        """
        if search is None:
            return None
        msg = "ENTERED. "
        msg += f"key: {key}, value: {value}. model_list: length {len(search)}."
        self.log.debug(msg)
        self.log_list_of_models(search, by_alias=False)

        for item in search:
            try:
                match = getattr(item, key)
            except AttributeError:
                return None
            if match == value:
                return item
        return None

    # pylint: disable=inconsistent-return-statements
    def to_bool(self, key: Any, dict_with_key: dict[Any, Any]) -> bool:
        """
        # Summary

        Given a dictionary and key, access dictionary[key] and
        try to convert the value therein to a boolean.

        -   If the value is a boolean, return a like boolean.
        -   If the value is a boolean-like string (e.g. "false"
            "True", etc), return the value converted to boolean.

        ## Raises

        -   ValueError if the value is not convertable to boolean.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        value = dict_with_key.get(key)

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"key: {key}, "
        msg += f"value: {value}"
        self.log.debug(msg)

        result: bool = False
        if value in ["false", "False", False]:
            result = False
        elif value in ["true", "True", True]:
            result = True
        else:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}: "
            msg += f"key: {key}, "
            msg += f"value ({str(value)}), "
            msg += f"with type {type(value)} "
            msg += "is not convertable to boolean."
            self.log.debug(msg)
            raise ValueError(msg)
        return result

    # pylint: enable=inconsistent-return-statements
    @staticmethod
    def property_values_match(dict1: dict[Any, Any], dict2: dict[Any, Any], property_list: list) -> bool:
        """
        Given two dictionaries and a list of keys:

        - Return True if all property values match.
        - Return False otherwise
        """
        for prop in property_list:
            if dict1.get(prop) != dict2.get(prop):
                return False
        return True

    def get_next_fabric_vlan_id(self, fabric: str) -> int:
        """
        # Summary

        Return the next available vlan_id for fabric.

        ## Raises

        - ValueError if:
          - RESPONSE_CODE is not 200
          - Unable to retrieve next available vlan_id for fabric

        ## Notes

        - TODO: This method is not covered by unit tests.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        vlan_path = self.paths["GET_VLAN"].format(fabric)
        args = SendToControllerArgs(
            action="query",
            path=vlan_path,
            verb=RequestVerb.GET,
            payload=None,
            log_response=False,
            is_rollback=False,
            response_model=ControllerResponseGetIntV12,
        )

        self.send_to_controller(args)
        try:
            response = ControllerResponseGetIntV12(**self.response)
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. Error parsing response: {error}. "
            msg += f"Response: {json.dumps(self.response, indent=4, sort_keys=True)}"
            raise ValueError(msg) from error

        if response.RETURN_CODE != 200:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}, "
            msg += f"Failure retrieving autogenerated vlan_id for fabric {fabric}."
            raise ValueError(msg)

        vlan_id = response.DATA

        msg = f"Returning vlan_id: {vlan_id} for fabric {fabric}"
        self.log.debug(msg)
        return vlan_id

    def get_next_fabric_vrf_id(self, fabric: str) -> int:
        """
        # Summary

        Return the next available vrf_id for fabric.

        ## Raises

        - ValueError if:
          - RESPONSE_CODE is not 200
          - Unable to retrieve next available vrf_id for fabric

        ## Notes

        - TODO: This method is not covered by unit tests.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        args = SendToControllerArgs(
            action="query",
            path=self.paths["GET_VRF_ID"].format(fabric),
            verb=RequestVerb.GET,
            payload=None,
            log_response=False,
            is_rollback=False,
            response_model=ControllerResponseGetFabricsVrfinfoV12,
        )

        self.send_to_controller(args)
        try:
            response = ControllerResponseGetFabricsVrfinfoV12(**self.response)
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. Error parsing response: {error}. "
            msg += f"Response: {json.dumps(self.response, indent=4, sort_keys=True)}"
            raise ValueError(msg) from error

        if response.RETURN_CODE != 200:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}, "
            msg += f"Failure retrieving autogenerated vrf_id for fabric {fabric}."
            raise ValueError(msg)

        vrf_id = response.DATA.l3_vni  # pylint: disable=no-member

        msg = f"Returning vrf_id: {vrf_id} for fabric {fabric}"
        self.log.debug(msg)
        return vrf_id

    def diff_for_attach_deploy(self, want_attach_list: list[dict], have_lan_attach_list_models: list[HaveLanAttachItem], replace=False) -> tuple[list, bool]:
        """
        Return attach_list, deploy_vrf

        Where:
        - attach_list is a list of attachment differences
        - deploy_vrf is a boolean
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = f"replace == {replace}"
        self.log.debug(msg)

        attach_list = []
        deploy_vrf = False

        if not want_attach_list:
            return attach_list, deploy_vrf

        for want_attach in want_attach_list:
            if not have_lan_attach_list_models:
                # No have_lan_attach, so always attach
                if self.to_bool("isAttached", want_attach):
                    want_attach = self._prepare_attach_for_deploy(want_attach)
                    attach_list.append(want_attach)
                    if self.to_bool("is_deploy", want_attach):
                        deploy_vrf = True
                continue

            found = False
            for have_lan_attach_model in have_lan_attach_list_models:
                if want_attach.get("serialNumber") != have_lan_attach_model.serial_number:
                    continue

                # Copy freeformConfig from have since the playbook doesn't
                # currently support it.
                want_attach.update({"freeformConfig": have_lan_attach_model.freeform_config})

                # Copy unsupported instanceValues keys from have to want_attach
                want_inst_values, have_inst_values = {}, {}
                if want_attach.get("instanceValues") and have_lan_attach_model.instance_values:
                    want_inst_values = json.loads(want_attach["instanceValues"])
                    have_inst_values = json.loads(have_lan_attach_model.instance_values)
                    # These keys are not currently supported in the playbook,
                    # so copy them from have to want.
                    for key in ["loopbackId", "loopbackIpAddress", "loopbackIpV6Address"]:
                        if key in have_inst_values:
                            want_inst_values[key] = have_inst_values[key]
                    want_attach["instanceValues"] = json.dumps(want_inst_values)

                # Compare extensionValues
                want_extension_values = want_attach.get("extensionValues")
                have_extension_values = have_lan_attach_model.extension_values
                if want_extension_values and have_extension_values:
                    if not self._extension_values_match(want_extension_values, have_extension_values, replace):
                        continue
                elif want_extension_values and not have_extension_values:
                    continue
                elif not want_extension_values and have_extension_values:
                    if not replace:
                        found = True
                    continue

                # Compare deployment/attachment status
                if not self._deployment_status_match(want_attach, have_lan_attach_model):
                    msg = "self._deployment_status_match() returned False."
                    self.log.debug(msg)
                    want_attach = self._prepare_attach_for_deploy(want_attach)
                    attach_list.append(want_attach)
                    if self.to_bool("is_deploy", want_attach):
                        deploy_vrf = True
                    found = True
                    break

                # Continue if instanceValues differ
                if self.dict_values_differ(dict1=want_inst_values, dict2=have_inst_values):
                    continue

                found = True
                break

            if not found:
                if self.to_bool("isAttached", want_attach):
                    want_attach = self._prepare_attach_for_deploy(want_attach)
                    attach_list.append(want_attach)
                    if self.to_bool("is_deploy", want_attach):
                        deploy_vrf = True

        msg = f"Caller {caller}: Returning deploy_vrf: "
        msg += f"{deploy_vrf}, "
        msg += "attach_list: "
        msg += f"{json.dumps(attach_list, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return attach_list, deploy_vrf

    def _prepare_attach_for_deploy(self, want: dict) -> dict:
        """
        # Summary

        Prepare an attachment dictionary for deployment.

        - Removes the "isAttached" key if present.
        - Sets the "deployment" key to True.

        ## Parameters

        - want: dict
            The attachment dictionary to update.

        ## Returns

        - dict: The updated attachment dictionary.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if "isAttached" in want:
            del want["isAttached"]
        want["deployment"] = True
        return want

    def _extension_values_match(self, want_extension_values: str, have_extension_values: str, replace: bool) -> bool:
        """
        # Summary

        Compare the extensionValues of two attachment dictionaries to determine if they match.

        - Convert want and have from JSON strings to dictionaries.
        - Parses and compares the VRF_LITE_CONN lists in both want and have.
        - If replace is True, also checks that the lengths of the VRF_LITE_CONN lists are equal.
        - Compares each interface (IF_NAME) and their properties.

        ## Parameters

        - want_extension_values: str
          - The desired extensionValues, as a JSON string.
        - have_extension_values: str
          - The extensionValues on the controller, as a JSON string.
        - replace: bool
          - True if this is a replace/override operation.
          - False otherwise.

        ## Returns

        - bool: True if the extension values match, False otherwise.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        want_extension_values = json.loads(want_extension_values)
        have_extension_values = json.loads(have_extension_values)

        want_vrf_lite_conn = json.loads(want_extension_values["VRF_LITE_CONN"])
        have_vrf_lite_conn = json.loads(have_extension_values["VRF_LITE_CONN"])
        if replace and (len(want_vrf_lite_conn["VRF_LITE_CONN"]) != len(have_vrf_lite_conn["VRF_LITE_CONN"])):
            return False
        for want_vrf_lite in want_vrf_lite_conn["VRF_LITE_CONN"]:
            for have_vrf_lite in have_vrf_lite_conn["VRF_LITE_CONN"]:
                if want_vrf_lite["IF_NAME"] == have_vrf_lite["IF_NAME"]:
                    if self.property_values_match(want_vrf_lite, have_vrf_lite, self.vrf_lite_properties):
                        return True
        return False

    def _deployment_status_match(self, want: dict, have_lan_attach_model: HaveLanAttachItem) -> bool:
        """
        # Summary

        Compare the deployment and attachment status between two attachment dictionaries.

        - Checks if "isAttached", "deployment", and "is_deploy" keys are equal in both dictionaries.

        ## Parameters

        - want: dict
            The desired attachment dictionary.
        - have: dict
            The current attachment dictionary from the controller.

        ## Returns

        - bool: True if all status flags match, False otherwise.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        # TODO: Remove this conversion once this method is updated to use lan_attach_list_model directly.
        have = have_lan_attach_model.model_dump(by_alias=True)

        msg = f"type(want): {type(want)}, type(have): {type(have)}"
        self.log.debug(msg)
        msg = f"want: {json.dumps(want, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        msg = f"have: {json.dumps(have, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        try:
            want_is_deploy = self.to_bool("is_deploy", want)
            have_is_deploy = self.to_bool("is_deploy", have)
            want_is_attached = self.to_bool("isAttached", want)
            have_is_attached = self.to_bool("isAttached", have)
            want_deployment = self.to_bool("deployment", want)
            have_deployment = self.to_bool("deployment", have)
            return want_is_attached == have_is_attached and want_deployment == have_deployment and want_is_deploy == have_is_deploy
        except ValueError as error:
            msg += f"caller: {caller}. "
            msg += f"{error}. "
            msg += "Returning False."
            self.log.debug(msg)
            return False

    def update_attach_params_extension_values(self, playbook_vrf_attach_model: PlaybookVrfAttachModel) -> dict:
        """
        # Summary

        Given PlaybookVrfAttachModel return a dictionary of extension values that can be used in a payload:

        -   Return a populated extension_values dictionary if the attachment object's vrf_lite parameter is is not null.
        -   Return an empty dictionary if the attachment object's vrf_lite parameter is null.

        ## Raises

        Calls fail_json() if the vrf_lite parameter is not null and the role of the switch in the playbook
        attachment object is not one of the various border roles.

        ## Example PlaybookVrfAttachModel contents

        ```json
        {
            "deploy": true,
            "export_evpn_rt": "5000:100",
            "import_evpn_rt": "5000:100",
            "ip_address": "10.10.10.227",
            "vrf_lite": [
                {
                    "dot1q": 2,
                    "interface": "Ethernet1/16",
                    "ipv4_addr": "10.33.0.2/30",
                    "ipv6_addr": "2010::10:34:0:7/64",
                    "neighbor_ipv4": "10.33.0.1",
                    "neighbor_ipv6": "2010::10:34:0:3",
                    "peer_vrf": "test_vrf_1"
                }
            ]
        }
        ```
        ## Returns

        extension_values: a dictionary containing two keys whose values are JSON strings

        -   "VRF_LITE_CONN": a list of dictionaries containing vrf_lite connection parameters
            - Each dictionary contains the following
                -   "DOT1Q_ID": the dot1q ID as a string
                -   "IF_NAME": the interface name
                -   "IP_MASK": the IPv4 address and mask
                -   "IPV6_MASK": the IPv6 address and mask
                -   "IPV6_NEIGHBOR": the IPv6 neighbor address
                -   "NEIGHBOR_IP": the IPv4 neighbor address
                -   "PEER_VRF_NAME": the peer VRF name
                -   "VRF_LITE_JYTHON_TEMPLATE": the Jython template name for VRF Lite
        -   "MULTISITE_CONN": a JSON string containing an empty MULTISITE_CONN dictionary

        ```json
        {
            "MULTISITE_CONN": "{\"MULTISITE_CONN\": []}",
            "VRF_LITE_CONN": "{\"VRF_LITE_CONN\": [{\"DOT1Q_ID\": \"2\", etc...}]}"
        }
        ```

        ## TODO

        - We need to return a model instead of a dictionary with JSON strings.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if not playbook_vrf_attach_model.vrf_lite:
            msg = "Early return. No vrf_lite extensions to process in playbook."
            self.log.debug(msg)
            return {}

        msg = "playbook_vrf_attach_model: "
        msg += f"{json.dumps(playbook_vrf_attach_model.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # Before applying the vrf_lite config, verify that the switch role begins with border
        ip_address = playbook_vrf_attach_model.ip_address
        switch_role = self.ipv4_to_switch_role.convert(ip_address)
        if not re.search(r"\bborder\b", switch_role.lower()):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "VRF LITE attachments are appropriate only for switches "
            msg += "with Border roles e.g. Border Gateway, Border Spine, etc. "
            msg += "The playbook and/or controller settings for switch "
            msg += f"{ip_address} with role {switch_role} need review."
            self.module.fail_json(msg=msg)

        msg = f"playbook_vrf_attach_model.vrf_lite: length: {len(playbook_vrf_attach_model.vrf_lite)}"
        self.log.debug(msg)
        self.log_list_of_models(playbook_vrf_attach_model.vrf_lite)

        extension_values: dict = {}
        extension_values["VRF_LITE_CONN"] = []
        ms_con: dict = {}
        ms_con["MULTISITE_CONN"] = []
        extension_values["MULTISITE_CONN"] = json.dumps(ms_con)

        for playbook_vrf_lite_model in playbook_vrf_attach_model.vrf_lite:
            # If the playbook contains vrf lite parameters update the extension values.
            vrf_lite_conn: dict = {}
            for param in self.vrf_lite_properties:
                vrf_lite_conn[param] = ""

            vrf_lite_conn["IF_NAME"] = playbook_vrf_lite_model.interface
            # TODO: look into why this has to be a string for unit tests to pass.
            vrf_lite_conn["DOT1Q_ID"] = str(playbook_vrf_lite_model.dot1q)
            vrf_lite_conn["IP_MASK"] = playbook_vrf_lite_model.ipv4_addr
            vrf_lite_conn["NEIGHBOR_IP"] = playbook_vrf_lite_model.neighbor_ipv4
            vrf_lite_conn["IPV6_MASK"] = playbook_vrf_lite_model.ipv6_addr
            vrf_lite_conn["IPV6_NEIGHBOR"] = playbook_vrf_lite_model.neighbor_ipv6
            vrf_lite_conn["PEER_VRF_NAME"] = playbook_vrf_lite_model.peer_vrf
            vrf_lite_conn["VRF_LITE_JYTHON_TEMPLATE"] = "Ext_VRF_Lite_Jython"

            msg = "vrf_lite_conn: "
            msg += f"{json.dumps(vrf_lite_conn, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            vrf_lite_connections: dict = {}
            vrf_lite_connections["VRF_LITE_CONN"] = []
            vrf_lite_connections["VRF_LITE_CONN"].append(copy.deepcopy(vrf_lite_conn))

            if extension_values["VRF_LITE_CONN"]:
                extension_values["VRF_LITE_CONN"]["VRF_LITE_CONN"].extend(vrf_lite_connections["VRF_LITE_CONN"])
            else:
                extension_values["VRF_LITE_CONN"] = copy.deepcopy(vrf_lite_connections)

            extension_values["VRF_LITE_CONN"] = json.dumps(extension_values["VRF_LITE_CONN"])

            msg = "Returning extension_values: "
            msg += f"{json.dumps(extension_values, indent=4, sort_keys=True)}"
            self.log.debug(msg)

        return copy.deepcopy(extension_values)

    def transmute_attach_params_to_payload(self, vrf_attach_model: PlaybookVrfAttachModel, vrf_name: str, deploy: bool, vlan_id: int) -> dict:
        """
        # Summary

        Turn playbook vrf attachment config (PlaybookVrfAttachModel) into an attachment payload for the controller.

        ## Raises

        Calls fail_json() if:

        -   The switch in the attachment object is a spine
        -   If the vrf_lite object is not null, and the switch is not
            a border switch
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        # TODO: Remove this once the method is refactored to use Pydantic models.
        attach = vrf_attach_model.model_dump()
        if not vrf_attach_model:
            msg = "Early return. No attachments to process."
            self.log.debug(msg)
            return {}

        # dcnm_get_ip_addr_info converts serial_numbers, hostnames, etc, to ip addresses.
        ip_address = dcnm_get_ip_addr_info(self.module, vrf_attach_model.ip_address, None, None)
        serial_number = self.ipv4_to_serial_number.convert(vrf_attach_model.ip_address)

        vrf_attach_model.ip_address = ip_address

        msg = f"ip_address: {ip_address}, "
        msg += f"serial_number: {serial_number}, "
        msg += "vrf_attach_model: "
        msg += f"{json.dumps(vrf_attach_model.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not serial_number:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += f"Fabric {self.fabric} does not contain switch "
            msg += f"{ip_address} ({serial_number})."
            self.module.fail_json(msg=msg)

        role = self.inventory_data[vrf_attach_model.ip_address].get("switchRole")

        msg = f"ZZZ: role: {role}, "
        self.log.debug(msg)

        if role.lower() in ("spine", "super spine"):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "VRF attachments are not appropriate for "
            msg += "switches with Spine or Super Spine roles. "
            msg += "The playbook and/or controller settings for switch "
            msg += f"{ip_address} with role {role} need review."
            self.module.fail_json(msg=msg)

        extension_values = self.update_attach_params_extension_values(playbook_vrf_attach_model=vrf_attach_model)
        if extension_values:
            attach.update({"extensionValues": json.dumps(extension_values).replace(" ", "")})
        else:
            attach.update({"extensionValues": ""})

        attach.update({"fabric": self.fabric})
        attach.update({"vrfName": vrf_name})
        attach.update({"vlan": vlan_id})
        # This flag is not to be confused for deploy of attachment.
        # "deployment" should be set to True for attaching an attachment
        # and set to False for detaching an attachment
        attach.update({"deployment": True})
        attach.update({"isAttached": True})
        attach.update({"serialNumber": serial_number})
        attach.update({"is_deploy": deploy})

        # freeformConfig, loopbackId, loopbackIpAddress, and
        # loopbackIpV6Address will be copied from have
        attach.update({"freeformConfig": ""})
        inst_values = {
            "loopbackId": "",
            "loopbackIpAddress": "",
            "loopbackIpV6Address": "",
        }
        inst_values.update(
            {
                "switchRouteTargetImportEvpn": attach.get("import_evpn_rt"),
                "switchRouteTargetExportEvpn": attach.get("export_evpn_rt"),
            }
        )
        attach.update({"instanceValues": json.dumps(inst_values).replace(" ", "")})

        attach.pop("deploy", None)
        attach.pop("ip_address", None)

        msg = "Returning attach: "
        msg += f"{json.dumps(attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        return copy.deepcopy(attach)

    def dict_values_differ(self, dict1: dict, dict2: dict, skip_keys=None) -> bool:
        """
        # Summary

        Given two dictionaries and, optionally, a list of keys to skip:

        -   Return True if the values for any (non-skipped) keys differs.
        -   Return False otherwise

        ## Raises

        -   ValueError if dict1 or dict2 is not a dictionary
        -   ValueError if skip_keys is not a list
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if skip_keys is None:
            skip_keys = []

        msg = f"{self.class_name}.{method_name}: "
        msg += f"caller: {caller}. "
        if not isinstance(skip_keys, list):
            msg += "skip_keys must be a list. "
            msg += f"Got {type(skip_keys)}."
            raise ValueError(msg)
        if not isinstance(dict1, dict):
            msg += "dict1 must be a dict. "
            msg += f"Got {type(dict1)}."
            raise ValueError(msg)
        if not isinstance(dict2, dict):
            msg += "dict2 must be a dict. "
            msg += f"Got {type(dict2)}."
            raise ValueError(msg)

        for key in dict1.keys():
            if key in skip_keys:
                continue
            dict1_value = str(dict1.get(key)).lower()
            dict2_value = str(dict2.get(key)).lower()
            # Treat None and "" as equal
            if dict1_value in (None, "none", ""):
                dict1_value = "none"
            if dict2_value in (None, "none", ""):
                dict2_value = "none"
            if dict1_value != dict2_value:
                msg = f"Values differ: key {key} "
                msg += f"dict1_value {dict1_value}, type {type(dict1_value)} != "
                msg += f"dict2_value {dict2_value}, type {type(dict2_value)}. "
                msg += "returning True"
                self.log.debug(msg)
                return True
        msg = "All dict values are equal. Returning False."
        self.log.debug(msg)
        return False

    def diff_for_create(self, want, have) -> tuple[dict, bool]:
        """
        # Summary

        Given a want and have object, return a tuple of
        (create, configuration_changed) where:
        -   create is a dictionary of parameters to send to the
            controller
        -   configuration_changed is a boolean indicating if
            the configuration has changed
        -   If the configuration has not changed, return an empty
            dictionary for create and False for configuration_changed
        -   If the configuration has changed, return a dictionary
            of parameters to send to the controller and True for
            configuration_changed
        -   If the configuration has changed, but the vrfId is
            None, return an empty dictionary for create and True
            for configuration_changed

        ## Raises

        -   Calls fail_json if the vrfId is not None and the vrfId
            in the want object is not equal to the vrfId in the
            have object.
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        configuration_changed = False
        if not have:
            return {}, configuration_changed

        create = {}

        json_to_dict_want = json.loads(want["vrfTemplateConfig"])
        json_to_dict_have = json.loads(have["vrfTemplateConfig"])

        # vlan_id_want drives the conditional below, so we cannot
        # remove it here (as we did with the other params that are
        # compared in the call to self.dict_values_differ())
        vlan_id_want = str(json_to_dict_want.get("vrfVlanId", ""))

        skip_keys = []
        if vlan_id_want == "0":
            skip_keys = ["vrfVlanId"]
        try:
            templates_differ = self.dict_values_differ(dict1=json_to_dict_want, dict2=json_to_dict_have, skip_keys=skip_keys)
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += f"templates_differ: {error}"
            self.module.fail_json(msg=msg)

        msg = f"templates_differ: {templates_differ}, "
        msg += f"vlan_id_want: {vlan_id_want}"
        self.log.debug(msg)

        if want.get("vrfId") is not None and have.get("vrfId") != want.get("vrfId"):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"vrf_id for vrf {want['vrfName']} cannot be updated to "
            msg += "a different value"
            self.module.fail_json(msg=msg)

        if templates_differ:
            configuration_changed = True
            if want.get("vrfId") is None:
                # The vrf updates with missing vrfId will have to use existing
                # vrfId from the instance of the same vrf on DCNM.
                want["vrfId"] = have["vrfId"]
            create = want

        msg = f"returning configuration_changed: {configuration_changed}, "
        msg += f"create: {create}"
        self.log.debug(msg)

        return create, configuration_changed

    def transmute_playbook_model_to_vrf_create_payload_model(self, vrf_playbook_model: PlaybookVrfModelV12) -> VrfPayloadV12:
        """
        # Summary

        Given an instance of PlaybookVrfModelV12, return an instance of VrfPayloadV12
        suitable for sending to the controller.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if not vrf_playbook_model:
            return vrf_playbook_model

        msg = "vrf_playbook_model (PlaybookVrfModelV12): "
        msg += f"{json.dumps(vrf_playbook_model.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # Transmute PlaybookVrfModelV12 into a vrf_template_config dictionary
        validated_template_config = VrfTemplateConfigV12.model_validate(vrf_playbook_model.model_dump())
        vrf_template_config_dict = validated_template_config.model_dump_json(by_alias=True)

        # Tramsmute PlaybookVrfModelV12 into VrfPayloadV12
        vrf_payload_v12 = VrfPayloadV12(
            fabric=self.fabric,
            service_vrf_template=vrf_playbook_model.service_vrf_template or "",
            source=None,
            vrf_id=vrf_playbook_model.vrf_id or 0,
            vrf_name=vrf_playbook_model.vrf_name,
            vrf_extension_template=vrf_playbook_model.vrf_extension_template or "Default_VRF_Extension_Universal",
            vrf_template=vrf_playbook_model.vrf_template or "Default_VRF_Universal",
            vrf_template_config=vrf_template_config_dict,
        )

        msg = "Returning VrfPayloadV12 instance: "
        msg += f"{json.dumps(vrf_payload_v12.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        return vrf_payload_v12

    def update_create_params(self, vrf: dict) -> dict:
        """
        # Summary

        Given a vrf dictionary from a playbook, return a VRF payload suitable
        for sending to the controller.

        Translate playbook keys into keys expected by the controller.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if not vrf:
            return vrf

        msg = "type(vrf): "
        msg += f"{type(vrf)}) "
        msg += f"vrf: {json.dumps(vrf, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        validated_template_config = VrfTemplateConfigV12.model_validate(vrf)
        template = validated_template_config.model_dump_json(by_alias=True)

        vrf_upd = {
            "fabric": self.fabric,
            "vrfName": vrf["vrf_name"],
            "vrfTemplate": vrf.get("vrf_template", "Default_VRF_Universal"),
            "vrfExtensionTemplate": vrf.get("vrf_extension_template", "Default_VRF_Extension_Universal"),
            "vrfId": vrf.get("vrf_id", None),  # vrf_id will be auto generated in get_diff_merge()
            "serviceVrfTemplate": vrf.get("service_vrf_template", ""),
            "source": None,
            "vrfTemplateConfig": template,
        }

        msg = f"Returning vrf_upd: {json.dumps(vrf_upd, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return vrf_upd

    def get_controller_vrf_object_models(self) -> list[VrfObjectV12]:
        """
        # Summary

        Retrieve all VRF objects from the controller
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        endpoint = EpVrfGet()
        endpoint.fabric_name = self.fabric

        controller_response = dcnm_send(self.module, endpoint.verb.value, endpoint.path)

        if controller_response is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to retrieve endpoint. "
            msg += f"verb {endpoint.verb.value} path {endpoint.path}"
            raise ValueError(msg)

        if isinstance(controller_response, Union[dict, list]):  # Avoid json.dumps(MagicMock) during unit tests
            msg = "controller_response: "
            msg += f"{json.dumps(controller_response, indent=4, sort_keys=True)}"
            self.log.debug(msg)

        validated_response = ControllerResponseVrfsV12(**controller_response)

        msg = "validated_response (ControllerResponseVrfsV12): "
        msg += f"{json.dumps(validated_response.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        missing_fabric, not_ok = self.handle_response(validated_response, "query")

        if missing_fabric or not_ok:
            msg0 = f"caller: {caller}. "
            msg1 = f"{msg0} Fabric {self.fabric} not present on the controller"
            msg2 = f"{msg0} Unable to find vrfs under fabric: {self.fabric}"
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        return validated_response.DATA

    def get_list_of_vrfs_switches_data_item_model(self, attach: dict) -> list[ControllerResponseVrfsSwitchesDataItem]:
        """
        # Summary

        Retrieve the IP/Interface that is connected to the switch with serial_number

        attach must contain at least the following keys:

        - fabric: The fabric to search
        - serialNumber: The serial_number of the switch
        - vrfName: The vrf to search
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = f"attach: {json.dumps(attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        verb = "GET"
        path = self.paths["GET_VRF_SWITCH"].format(attach["fabric"], attach["vrfName"], attach["serialNumber"])
        msg = f"verb: {verb}, path: {path}"
        self.log.debug(msg)
        controller_response = dcnm_send(self.module, verb, path)

        if controller_response is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to retrieve lite_objects."
            raise ValueError(msg)

        msg = "controller_response: "
        msg += f"{json.dumps(controller_response, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        try:
            validated_response = ControllerResponseVrfsSwitchesV12(**controller_response)
        except ValidationError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to parse response: {error}"
            raise ValueError(msg) from error

        msg = "validated_response (ControllerResponseVrfsSwitchesV12): "
        msg += f"{json.dumps(validated_response.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"Returning list of VrfSwitchesDataItem. length {len(validated_response.DATA)}."
        self.log.debug(msg)
        self.log_list_of_models(validated_response.DATA)

        return validated_response.DATA

    def get_list_of_vrfs_switches_data_item_model_new(
        self, lan_attach_item: PayloadVrfsAttachmentsLanAttachListItem
    ) -> list[ControllerResponseVrfsSwitchesDataItem]:
        """
        # Summary

        Will replace get_list_of_vrfs_switches_data_item_model() in the future.
        Retrieve the IP/Interface that is connected to the switch with serial_number

        PayloadVrfsAttachmentsLanAttachListItem must contain at least the following fields:

        - fabric: The fabric to search
        - serial_number: The serial_number of the switch
        - vrf_name: The vrf to search
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = f"lan_attach_item: {json.dumps(lan_attach_item.model_dump(by_alias=False), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        verb = "GET"
        path = self.paths["GET_VRF_SWITCH"].format(lan_attach_item.fabric, lan_attach_item.vrf_name, lan_attach_item.serial_number)
        msg = f"verb: {verb}, path: {path}"
        self.log.debug(msg)
        controller_response = dcnm_send(self.module, verb, path)

        if controller_response is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to retrieve lite_objects."
            raise ValueError(msg)

        msg = "controller_response: "
        msg += f"{json.dumps(controller_response, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        try:
            validated_response = ControllerResponseVrfsSwitchesV12(**controller_response)
        except ValidationError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to parse response: {error}"
            raise ValueError(msg) from error

        msg = "validated_response (ControllerResponseVrfsSwitchesV12): "
        msg += f"{json.dumps(validated_response.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"Returning list of VrfSwitchesDataItem. length {len(validated_response.DATA)}."
        self.log.debug(msg)
        self.log_list_of_models(validated_response.DATA)

        return validated_response.DATA

    def populate_have_create(self, vrf_object_models: list[VrfObjectV12]) -> None:
        """
        # Summary

        Given a list of VrfObjectV12 models, populate self.have_create,
        which is a list of VRF dictionaries used later to generate payloads
        to send to the controller (e.g. diff_create, diff_create_update).

        - Remove vrfStatus
        - Convert vrfTemplateConfig to a JSON string

        ## Raises

        None
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        have_create = []
        for vrf in vrf_object_models:
            vrf_template_config = self.update_vrf_template_config_from_vrf_model(vrf)
            vrf_dict = vrf.model_dump(by_alias=True)
            vrf_dict["vrfTemplateConfig"] = vrf_template_config.model_dump_json(by_alias=True)
            vrf_dict.pop("vrfStatus", None)
            have_create.append(vrf_dict)

        self.have_create = copy.deepcopy(have_create)
        msg = "self.have_create: "
        msg += f"{json.dumps(self.have_create, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def populate_have_deploy(self, get_vrf_attach_response: dict) -> dict:
        """
        Return have_deploy, which is a dict representation of VRFs currently deployed on the controller.

        Use get_vrf_attach_response dict to populate have_deploy.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        vrfs_to_update: set[str] = set()

        for vrf_attach in get_vrf_attach_response.get("DATA", []):
            if not vrf_attach.get("lanAttachList"):
                continue
            attach_list = vrf_attach["lanAttachList"]
            for attach in attach_list:
                deploy = attach.get("isLanAttached")
                deployed = not (deploy and attach.get("lanAttachState") in ("OUT-OF-SYNC", "PENDING"))
                if deployed:
                    vrf_to_deploy = attach.get("vrfName")
                    if vrf_to_deploy:
                        vrfs_to_update.add(vrf_to_deploy)

        have_deploy = {}
        have_deploy["vrfNames"] = ",".join(vrfs_to_update)

        msg = "Returning have_deploy: "
        msg += f"{json.dumps(have_deploy, indent=4)}"
        self.log.debug(msg)

        return copy.deepcopy(have_deploy)

    def populate_have_deploy_model(self, vrf_attach_responses: list[ControllerResponseVrfsAttachmentsDataItem]) -> PayloadfVrfsDeployments:
        """
        Return PayloadfVrfsDeployments, which is a model representation of VRFs currently deployed on the controller.

        Uses vrf_attach_responses (list[ControllerResponseVrfsAttachmentsDataItem]) to populate PayloadfVrfsDeployments.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        vrfs_to_update: set[str] = set()

        for vrf_attach_model in vrf_attach_responses:
            if not vrf_attach_model.lan_attach_list:
                continue
            attach_list_models = vrf_attach_model.lan_attach_list
            for lan_attach_model in attach_list_models:
                deploy = lan_attach_model.is_lan_attached
                deployed = not (deploy and lan_attach_model.lan_attach_state in ("OUT-OF-SYNC", "PENDING"))
                if deployed:
                    vrf_to_deploy = lan_attach_model.vrf_name
                    if vrf_to_deploy:
                        vrfs_to_update.add(vrf_to_deploy)

        have_deploy_model = PayloadfVrfsDeployments(vrf_names=vrfs_to_update)

        msg = "Returning have_deploy_model: "
        msg += f"{json.dumps(have_deploy_model.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        return have_deploy_model

    def populate_have_attach_models(self, vrf_attach_models: list[ControllerResponseVrfsAttachmentsDataItem]) -> None:
        """
        Populate the following using vrf_attach_models (list[ControllerResponseVrfsAttachmentsDataItem]):

        - self.have_attach
        - self.have_attach_models
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = f"vrf_attach_models.PRE_UPDATE: length: {len(vrf_attach_models)}."
        self.log.debug(msg)
        self.log_list_of_models(vrf_attach_models)

        updated_vrf_attach_models: list[HaveAttachPostMutate] = []
        for vrf_attach_model in vrf_attach_models:
            if not vrf_attach_model.lan_attach_list:
                continue
            new_attach_list: list[HaveLanAttachItem] = []
            for lan_attach_item in vrf_attach_model.lan_attach_list:
                msg = "lan_attach_item: "
                msg += f"{json.dumps(lan_attach_item.model_dump(by_alias=False), indent=4, sort_keys=True)}"
                self.log.debug(msg)
                # Mutate attachment
                new_attach_dict = {
                    "deployment": lan_attach_item.is_lan_attached,
                    "extensionValues": "",
                    "fabricName": self.fabric,
                    "instanceValues": lan_attach_item.instance_values,
                    "isAttached": lan_attach_item.lan_attach_state != "NA",
                    "is_deploy": not (lan_attach_item.is_lan_attached and lan_attach_item.lan_attach_state in ("OUT-OF-SYNC", "PENDING")),
                    "serialNumber": lan_attach_item.switch_serial_no,
                    "vlanId": lan_attach_item.vlan_id,
                    "vrfName": lan_attach_item.vrf_name,
                }

                new_lan_attach_item = HaveLanAttachItem(**new_attach_dict)
                msg = "new_lan_attach_item: "
                msg += f"{json.dumps(new_lan_attach_item.model_dump(by_alias=False), indent=4, sort_keys=True)}"
                self.log.debug(msg)

                new_attach = self._update_vrf_lite_extension_model(new_lan_attach_item)

                msg = "new_attach: "
                msg += f"{json.dumps(new_attach.model_dump(by_alias=False), indent=4, sort_keys=True)}"
                self.log.debug(msg)

                new_attach_list.append(new_attach)

            msg = f"new_attach_list: length: {len(new_attach_list)}."
            self.log.debug(msg)
            self.log_list_of_models(new_attach_list)

            new_attach_dict = {
                "lanAttachList": new_attach_list,
                "vrfName": vrf_attach_model.vrf_name,
            }
            new_vrf_attach_model = HaveAttachPostMutate(**new_attach_dict)
            new_vrf_attach_model.lan_attach_list = new_attach_list
            updated_vrf_attach_models.append(new_vrf_attach_model)

            msg = f"updated_vrf_attach_models: length: {len(updated_vrf_attach_models)}."
            self.log.debug(msg)
            self.log_list_of_models(updated_vrf_attach_models)

        updated_vrf_attach_models_dicts = [model.model_dump(by_alias=True) for model in updated_vrf_attach_models]

        self.have_attach = copy.deepcopy(updated_vrf_attach_models_dicts)
        self.have_attach_models = updated_vrf_attach_models
        msg = f"self.have_attach_models.POST_UPDATE: length: {len(self.have_attach_models)}."
        self.log.debug(msg)
        self.log_list_of_models(self.have_attach_models)

    def _update_vrf_lite_extension_model(self, attach: HaveLanAttachItem) -> HaveLanAttachItem:
        """
        # Summary

        - Return updated attach model with VRF Lite extension values if present.
        - Update freeformConfig, if present, else set to an empty string.

        ## Raises

        - None
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = "attach: "
        msg += f"{json.dumps(attach.model_dump(by_alias=False), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        params = {
            "fabric": attach.fabric,
            "serialNumber": attach.serial_number,
            "vrfName": attach.vrf_name,
        }
        lite_objects = self.get_list_of_vrfs_switches_data_item_model(params)
        if not lite_objects:
            msg = "No vrf_lite_objects found. Update freeformConfig and return."
            self.log.debug(msg)
            attach.freeform_config = ""
            return attach

        msg = f"lite_objects: length {len(lite_objects)}."
        self.log.debug(msg)
        self.log_list_of_models(lite_objects)

        for sdl in lite_objects:
            for epv in sdl.switch_details_list:
                if not epv.extension_values:
                    attach.freeform_config = ""
                    continue
                ext_values = epv.extension_values
                if ext_values.vrf_lite_conn is None:
                    continue
                ext_values = ext_values.vrf_lite_conn
                extension_values = {"VRF_LITE_CONN": {"VRF_LITE_CONN": []}}
                for vrf_lite_conn_model in ext_values.vrf_lite_conn:
                    ev_dict = copy.deepcopy(vrf_lite_conn_model.model_dump(by_alias=True))
                    ev_dict.update({"AUTO_VRF_LITE_FLAG": vrf_lite_conn_model.auto_vrf_lite_flag or "false"})
                    ev_dict.update({"VRF_LITE_JYTHON_TEMPLATE": "Ext_VRF_Lite_Jython"})
                    extension_values["VRF_LITE_CONN"]["VRF_LITE_CONN"].append(ev_dict)
                extension_values["VRF_LITE_CONN"] = json.dumps(extension_values["VRF_LITE_CONN"])
                ms_con = {"MULTISITE_CONN": []}
                extension_values["MULTISITE_CONN"] = json.dumps(ms_con)
                attach.extension_values = json.dumps(extension_values).replace(" ", "")
                attach.freeform_config = epv.freeform_config or ""
        return attach

    def get_have(self) -> None:
        """
        # Summary

        Retrieve all VRF objects and attachment objects from the
        controller. Update the following with this information:

        -   self.have_create, see populate_have_create()
        -   self.have_attach_models, see populate_have_attach_models()
        -   self.have_deploy, see populate_have_deploy()
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        validated_vrf_object_models = self.get_controller_vrf_object_models()

        msg = f"validated_vrf_object_models: length {len(validated_vrf_object_models)}."
        self.log.debug(msg)
        self.log_list_of_models(validated_vrf_object_models)

        if not validated_vrf_object_models:
            return

        self.populate_have_create(validated_vrf_object_models)

        current_vrfs_set = {vrf.vrfName for vrf in validated_vrf_object_models}
        controller_response = get_endpoint_with_long_query_string(
            module=self.module,
            fabric_name=self.fabric,
            path=self.paths["GET_VRF_ATTACH"],
            query_string_items=",".join(current_vrfs_set),
            caller=f"{self.class_name}.{method_name}",
        )

        if controller_response is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}: unable to set controller_response."
            raise ValueError(msg)

        msg = "controller_response: "
        msg += f"{json.dumps(controller_response, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        validated_controller_response = ControllerResponseVrfsAttachmentsV12(**controller_response)

        msg = "validated_controller_response: "
        msg += f"{json.dumps(validated_controller_response.model_dump(by_alias=False), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not validated_controller_response.DATA:
            return

        self.have_deploy = self.populate_have_deploy(controller_response)
        self.have_deploy_model = self.populate_have_deploy_model(validated_controller_response.DATA)
        msg = "self.have_deploy_model (by_alias=True): "
        msg += f"{json.dumps(self.have_deploy_model.model_dump(by_alias=True), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.populate_have_attach_models(validated_controller_response.DATA)

    def get_want_attach(self) -> None:
        """
        Populate self.want_attach from self.validated_playbook_config.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        want_attach: list[dict[str, Any]] = []

        for validated_playbook_config_model in self.validated_playbook_config_models:
            vrf_name: str = validated_playbook_config_model.vrf_name
            vrf_attach: dict[Any, Any] = {}
            vrf_attach_payloads: list[dict[Any, Any]] = []

            vrf_deploy: bool = validated_playbook_config_model.deploy or False
            vlan_id: int = validated_playbook_config_model.vlan_id or 0

            if not validated_playbook_config_model.attach:
                msg = f"No attachments for vrf {vrf_name}. Skipping."
                self.log.debug(msg)
                continue
            for vrf_attach_model in validated_playbook_config_model.attach:
                deploy = vrf_deploy
                vrf_attach_payloads.append(self.transmute_attach_params_to_payload(vrf_attach_model, vrf_name, deploy, vlan_id))

            if vrf_attach_payloads:
                vrf_attach.update({"vrfName": vrf_name})
                vrf_attach.update({"lanAttachList": vrf_attach_payloads})
                want_attach.append(vrf_attach)

        self.want_attach = copy.deepcopy(want_attach)
        msg = "self.want_attach: "
        msg += f"{json.dumps(self.want_attach, indent=4)}"
        self.log.debug(msg)

        self.build_want_attach_vrf_lite()

    def build_want_attach_vrf_lite(self) -> None:
        """
        From self.validated_playbook_config_models, build a dictionary, keyed on switch serial_number,
        containing a list of VrfLiteModel.

        ## Example structure

        ```json
        {
            "XYZKSJHSMK4": [
                VrfLiteModel(
                    dot1q=21,
                    interface="Ethernet1/1",
                    ipv4_addr="10.33.0.11/30",
                    ipv6_addr="2010::10:34:0:1/64",
                    neighbor_ipv4="10.33.0.12",
                    neighbor_ipv6="2010::10:34:0:1",
                    peer_vrf="test_vrf_1"
                )
            ]
        }
        ```
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if not self.validated_playbook_config_models:
            msg = "Early return. No validated VRFs found."
            self.log.debug(msg)
            return
        vrf_config_models_with_attachments = [model for model in self.validated_playbook_config_models if model.attach]
        if not vrf_config_models_with_attachments:
            msg = "Early return. No playbook configs containing VRF attachments found."
            self.log.debug(msg)
            return

        for model in vrf_config_models_with_attachments:
            for attachment in model.attach:
                if not attachment.vrf_lite:
                    msg = f"switch {attachment.ip_address} VRF attachment does not contain vrf_lite. Skipping."
                    self.log.debug(msg)
                    continue
                ip_address = attachment.ip_address
                self.want_attach_vrf_lite.update({self.ipv4_to_serial_number.convert(ip_address): attachment.vrf_lite})

        msg = f"self.want_attach_vrf_lite: length: {len(self.want_attach_vrf_lite)}."
        self.log.debug(msg)
        for serial_number, vrf_lite_list in self.want_attach_vrf_lite.items():
            msg = f"serial_number {serial_number}: -> {json.dumps([model.model_dump(by_alias=True) for model in vrf_lite_list], indent=4, sort_keys=True)}"
            self.log.debug(msg)

    def populate_want_create_payload_models(self) -> None:
        """
        Populate self.want_create_payload_models from self.validated_playbook_config_models.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        want_create_payload_models: list[VrfPayloadV12] = []

        for playbook_config_model in self.validated_playbook_config_models:
            want_create_payload_models.append(self.transmute_playbook_model_to_vrf_create_payload_model(playbook_config_model))

        self.want_create_payload_models = want_create_payload_models
        msg = f"self.want_create_payload_models: length: {len(self.want_create_payload_models)}."
        self.log.debug(msg)
        self.log_list_of_models(self.want_create_payload_models)

    def get_want_create(self) -> None:
        """
        Populate self.want_create from self.validated_playbook_config.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        want_create: list[dict[str, Any]] = []

        for vrf in self.validated_playbook_config:
            want_create.append(self.update_create_params(vrf=vrf))

        self.want_create = copy.deepcopy(want_create)
        msg = "self.want_create: "
        msg += f"{json.dumps(self.want_create, indent=4)}"
        self.log.debug(msg)

    def get_want_deploy(self) -> None:
        """
        Populate self.want_deploy from self.validated_playbook_config.
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        want_deploy: dict[str, Any] = {}
        all_vrfs: set = set()

        for vrf in self.validated_playbook_config:
            try:
                vrf_name: str = vrf["vrf_name"]
            except KeyError:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"caller: {caller}. "
                msg += f"vrf missing mandatory key vrf_name: {vrf}"
                self.module.fail_json(msg=msg)
            all_vrfs.add(vrf_name)

        if len(all_vrfs) != 0:
            vrf_names = ",".join(all_vrfs)
            want_deploy.update({"vrfNames": vrf_names})

        self.want_deploy = copy.deepcopy(want_deploy)
        msg = "self.want_deploy: "
        msg += f"{json.dumps(self.want_deploy, indent=4)}"
        self.log.debug(msg)

    def get_want(self) -> None:
        """
        Parse the playbook config and populate:
        - self.want_attach, see get_want_attach()
        - self.want_create, see get_want_create() (to be replaced by self.want_create_payload_models)
        - self.want_create_payload_models, see populate_want_create_payload_models()
        - self.want_deploy, see get_want_deploy()
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        # We're populating both self.want_create and self.want_create_payload_models
        # so that we can gradually replace self.want_create, one method at
        # a time.
        self.get_want_create()
        self.populate_want_create_payload_models()
        self.get_want_attach()
        self.get_want_deploy()

    def get_items_to_detach(self, attach_list: list[dict]) -> list[dict]:
        """
        # Summary

        Given a list of attachment objects, return a list of
        attachment objects that are to be detached.

        This is done by checking for the presence of the
        "isAttached" key in the attachment object and
        checking if the value is True.

        If the "isAttached" key is present and True, it
        indicates that the attachment is attached to a
        VRF and needs to be detached.  In this case,
        remove the "isAttached" key and set the
        "deployment" key to False.

        The modified attachment object is added to the
        detach_list.

        Finally, return the detach_list.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        detach_list = []
        for item in attach_list:
            if "isAttached" not in item:
                continue
            if item["isAttached"]:
                del item["isAttached"]
                item.update({"deployment": False})
                detach_list.append(item)
        return detach_list

    def get_items_to_detach_model(self, attach_list: list[HaveLanAttachItem]) -> Union[VrfDetachPayloadV12, None]:
        """
        # Summary

        Given a list of HaveLanAttachItem objects, return a list of
        VrfDetachPayloadV12 models, or None if no items are to be detached.

        This is done by checking if the isAttached field in each
        HaveLanAttachItem is True.

        If HaveLanAttachItem.isAttached field is True, it indicates that the
        attachment is attached to a VRF and needs to be detached.  In this case,
        mutate the HaveLanAttachItem to a LanDetachListItemV12 which will:

        - Remove the isAttached field
        - Set the deployment field to False

        The LanDetachListItemV12 is added to VrfDetachPayloadV12.lan_attach_list.

        ## Raises

        - fail_json if the vrf_name is not found in lan_detach_items
        - fail_json if multiple different vrf_names are found in lan_detach_items

        ## Returns

        - A VrfDetachPayloadV12 model containing the list of LanDetachListItemV12 objects.
        - None, if no items are to be detached.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        lan_detach_items: list[LanDetachListItemV12] = []

        msg = f"attach_list: length {len(attach_list)}."
        self.log.debug(msg)
        self.log_list_of_models(attach_list)

        for have_lan_attach_item in attach_list:
            if not have_lan_attach_item.is_attached:
                continue
            msg = "have_lan_attach_item: "
            msg += f"{json.dumps(have_lan_attach_item.model_dump(by_alias=False), indent=4, sort_keys=True)}"
            self.log.debug(msg)

            msg = "Mutating HaveLanAttachItem to LanDetachListItemV12."
            self.log.debug(msg)
            lan_detach_item = LanDetachListItemV12(
                deployment=False,
                extensionValues=have_lan_attach_item.extension_values,
                fabric=have_lan_attach_item.fabric,
                freeformConfig=have_lan_attach_item.freeform_config,
                instanceValues=have_lan_attach_item.instance_values,
                is_deploy=have_lan_attach_item.is_deploy,
                serialNumber=have_lan_attach_item.serial_number,
                vlanId=have_lan_attach_item.vlan,
                vrfName=have_lan_attach_item.vrf_name,
            )
            msg = "Mutating HaveLanAttachItem to LanDetachListItemV12. DONE."
            self.log.debug(msg)

            vrf_name = have_lan_attach_item.vrf_name
            lan_detach_items.append(lan_detach_item)

        if not lan_detach_items:
            msg = "No items to detach found in attach_list. Returning None."
            self.log.debug(msg)
            return None

        msg = "Creating VrfDetachPayloadV12 model."
        self.log.debug(msg)

        vrf_name = lan_detach_items[0].vrf_name if lan_detach_items else ""
        if not vrf_name:
            msg = "vrf_name not found in lan_detach_items. Cannot create VrfDetachPayloadV12 model."
            self.module.fail_json(msg=msg)
        if len(set(item.vrf_name for item in lan_detach_items)) > 1:
            msg = "Multiple VRF names found in lan_detach_items. Cannot create VrfDetachPayloadV12 model."
            self.module.fail_json(msg=msg)

        msg = f"lan_detach_items for VrfDetachPayloadV12: length {len(lan_detach_items)}."
        self.log.debug(msg)
        self.log_list_of_models(lan_detach_items)

        detach_list_model = VrfDetachPayloadV12(
            lanAttachList=lan_detach_items,
            vrfName=vrf_name,
        )

        msg = "Creating VrfDetachPayloadV12 model. DONE."
        self.log.debug(msg)

        msg = f"Returning detach_list_model: length(lan_attach_list): {len(detach_list_model.lan_attach_list)}."
        self.log.debug(msg)
        msg = f"{json.dumps(detach_list_model.model_dump(by_alias=False), indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return detach_list_model

    # TODO: rename to populate_diff_delete_model after testing
    def get_diff_delete(self) -> None:
        """
        # Summary

        Called from modules/dcnm_vrf.py

        Using self.have_create, and self.have_attach_models, update the following:

        - diff_detach: a list of attachment objects to detach
        - diff_undeploy: a dictionary of vrf names to undeploy
        - diff_delete: a dictionary of vrf names to delete
        """
        caller = inspect.stack()[1][3]

        self.set_model_enabled_true()

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if self.config:
            self._get_diff_delete_with_config_model()
        else:
            self._get_diff_delete_without_config_model()

        msg = f"self.diff_detach: length: {len(self.diff_detach)}."
        self.log.debug(msg)
        self.log_list_of_models(self.diff_detach, by_alias=False)

        msg = "self.diff_undeploy: "
        msg += f"{json.dumps(self.diff_undeploy, indent=4)}"
        self.log.debug(msg)
        msg = "self.diff_delete: "
        msg += f"{json.dumps(self.diff_delete, indent=4)}"
        self.log.debug(msg)

        self.set_model_enabled_false()

    def _get_diff_delete_with_config_model(self) -> None:
        """
        Handle diff_delete logic when self.config is not empty.

        In this case, we detach, undeploy, and delete the VRFs
        specified in self.config.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        diff_detach: list[VrfDetachPayloadV12] = []
        diff_undeploy: dict = {}
        diff_delete: dict = {}
        all_vrfs = set()

        msg = "self.have_attach_models: "
        self.log.debug(msg)
        self.log_list_of_models(self.have_attach_models, by_alias=True)

        for want_create_payload_model in self.want_create_payload_models:
            if self.find_dict_in_list_by_key_value(search=self.have_create, key="vrfName", value=want_create_payload_model.vrf_name) == {}:
                continue

            diff_delete.update({want_create_payload_model.vrf_name: "DEPLOYED"})

            have_attach_model: HaveAttachPostMutate = self.find_model_in_list_by_key_value(
                search=self.have_attach_models, key="vrf_name", value=want_create_payload_model.vrf_name
            )
            if not have_attach_model:
                msg = f"have_attach_model not found for vrfName: {want_create_payload_model.vrf_name}. "
                msg += "Continuing."
                self.log.debug(msg)
                continue

            msg = "have_attach_model: "
            msg += f"{json.dumps(have_attach_model.model_dump(by_alias=False), indent=4, sort_keys=True)}"
            self.log.debug(msg)

            detach_list_model: VrfDetachPayloadV12 = self.get_items_to_detach_model(have_attach_model.lan_attach_list)
            if not detach_list_model:
                msg = "detach_list_model is None. continuing."
                self.log.debug(msg)
                continue
            msg = f"detach_list_model: length(lan_attach_list): {len(detach_list_model.lan_attach_list)}."
            self.log.debug(msg)
            msg = f"{json.dumps(detach_list_model.model_dump(by_alias=False), indent=4, sort_keys=True)}"
            self.log.debug(msg)
            if detach_list_model.lan_attach_list:
                diff_detach.append(detach_list_model)
                all_vrfs.add(detach_list_model.vrf_name)
        if len(all_vrfs) != 0:
            diff_undeploy.update({"vrfNames": ",".join(all_vrfs)})

        self.diff_detach = diff_detach
        self.diff_undeploy = copy.deepcopy(diff_undeploy)
        self.diff_delete = copy.deepcopy(diff_delete)

    def _get_diff_delete_without_config_model(self) -> None:
        """
        Handle diff_delete logic when self.config is empty or None.

        In this case, we detach, undeploy, and delete all VRFs.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        diff_detach: list[VrfDetachPayloadV12] = []
        diff_undeploy: dict = {}
        diff_delete: dict = {}
        all_vrfs = set()

        msg = "self.have_attach_models: "
        self.log.debug(msg)
        self.log_list_of_models(self.have_attach_models, by_alias=True)

        have_attach_model: HaveAttachPostMutate
        for have_attach_model in self.have_attach_models:
            msg = f"type(have_attach_model): {type(have_attach_model)}"
            self.log.debug(msg)
            diff_delete.update({have_attach_model.vrf_name: "DEPLOYED"})
            detach_list_model = self.get_items_to_detach_model(have_attach_model.lan_attach_list)
            if not detach_list_model:
                msg = "detach_list_model is None. continuing."
                self.log.debug(msg)
                continue
            msg = f"detach_list_model: length(lan_attach_list): {len(detach_list_model.lan_attach_list)}."
            self.log.debug(msg)
            msg = f"{json.dumps(detach_list_model.model_dump(by_alias=False), indent=4, sort_keys=True)}"
            self.log.debug(msg)
            if detach_list_model.lan_attach_list:
                diff_detach.append(detach_list_model)
                all_vrfs.add(detach_list_model.vrf_name)

        if len(all_vrfs) != 0:
            diff_undeploy.update({"vrfNames": ",".join(all_vrfs)})

        self.diff_detach = diff_detach
        self.diff_undeploy = copy.deepcopy(diff_undeploy)
        self.diff_delete = copy.deepcopy(diff_delete)

    def get_diff_override(self) -> None:
        """
        # Summary

        For override state, we delete existing attachments and vrfs (self.have_attach_models) that are not in self.want_create_payload_models.

        Using self.have_attach_models and self.want_create_payload_models, update the following:

        - diff_detach: a list of attachment objects to detach (see append_to_diff_detach)
        - diff_undeploy: a dictionary with single key "vrfNames" and value of a comma-separated list of vrf_names to undeploy
        - diff_delete: a dictionary keyed on vrf_name with value set to "DEPLOYED". These VRFs will be deleted.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        self.get_diff_replace()
        all_vrfs = set()

        for have_attach_model in self.have_attach_models:
            found_in_want = self.find_model_in_list_by_key_value(search=self.want_create_payload_models, key="vrf_name", value=have_attach_model.vrf_name)

            if found_in_want:
                continue
            # VRF exists on the controller but is not in the want list.  Detach and delete it.
            vrf_detach_payload = self.get_items_to_detach_model(have_attach_model.lan_attach_list)
            if vrf_detach_payload:
                self.diff_detach.append(vrf_detach_payload)
                all_vrfs.add(vrf_detach_payload.vrf_name)
                self.diff_delete.update({vrf_detach_payload.vrf_name: "DEPLOYED"})

        if len(all_vrfs) != 0:
            self.diff_undeploy.update({"vrfNames": ",".join(all_vrfs)})

        msg = "self.diff_delete: "
        msg += f"{json.dumps(self.diff_delete, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_detach: "
        self.log.debug(msg)
        self.log_list_of_models(self.diff_detach, by_alias=False)

        msg = "self.diff_undeploy: "
        msg += f"{json.dumps(self.diff_undeploy, indent=4)}"
        self.log.debug(msg)

    def get_diff_replace(self) -> None:
        """
        # Summary

        For replace state, update the following:

        - self.diff_attach: a list of attachment objects to attach
        - self.diff_deploy: a dictionary of vrf names to deploy

        By comparing the current state of attachments (self.have_attach_models)
        with the desired state (self.want_attach) and determining which attachments
        need to be replaced or removed.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        all_vrfs: set = set()
        self.get_diff_merge(replace=True)

        msg = f"self.have_attach_models: length: {len(self.have_attach_models)}."
        self.log.debug(msg)
        self.log_list_of_models(self.have_attach_models, by_alias=True)
        for have_attach_model in self.have_attach_models:
            replace_lan_attach_list = []

            # Find want_attach whose vrfName matches have_attach
            want_attach = next((w for w in self.want_attach if w.get("vrfName") == have_attach_model.vrf_name), None)

            if want_attach:  # matches have_attach
                have_lan_attach_list = have_attach_model.lan_attach_list
                want_lan_attach_list = want_attach.get("lanAttachList", [])

                for have_lan_attach_model in have_lan_attach_list:
                    if have_lan_attach_model.is_attached is False:
                        continue
                    # Check if this have_lan_attach_model exists in want_lan_attach_list by serialNumber
                    if not any(have_lan_attach_model.serial_number == want_lan_attach.get("serialNumber") for want_lan_attach in want_lan_attach_list):
                        have_lan_attach_model.deployment = False
                        # Need to convert model to dict to remove isAttached key. TODO: revisit
                        have_lan_attach_dict = have_lan_attach_model.model_dump(by_alias=True)
                        have_lan_attach_dict.pop("isAttached", None)  # Remove isAttached key
                        replace_lan_attach_list.append(have_lan_attach_dict)
            else:  # have_attach is not in want_attach
                have_attach_in_want_create = self.find_model_in_list_by_key_value(
                    search=self.want_create_payload_models, key="vrf_name", value=have_attach_model.vrf_name
                )
                if not have_attach_in_want_create:
                    continue
                # If have_attach is not in want_attach but is in want_create, detach all attached
                for have_lan_attach_model in have_attach_model.lan_attach_list:
                    if not have_lan_attach_model.is_attached:
                        continue
                    have_lan_attach_model.deployment = False
                    # Need to convert model to dict to remove isAttached key. TODO: revisit
                    have_lan_attach_dict = have_lan_attach_model.model_dump(by_alias=True)
                    have_lan_attach_dict.pop("isAttached", None)  # Remove isAttached key
                    replace_lan_attach_list.append(have_lan_attach_dict)

            if not replace_lan_attach_list:
                continue
            # Find or create the diff_attach entry for this VRF
            diff_attach = next((d for d in self.diff_attach if d.get("vrfName") == have_attach_model.vrf_name), None)
            if diff_attach:
                diff_attach["lanAttachList"].extend(replace_lan_attach_list)
            else:
                attachment = {
                    "vrfName": have_attach_model.vrf_name,
                    "lanAttachList": replace_lan_attach_list,
                }
                self.diff_attach.append(attachment)
            all_vrfs.add(have_attach_model.vrf_name)

        if not all_vrfs:
            msg = "Early return. No VRF attachments required modification for replaced state."
            self.log.debug(msg)
            return

        all_vrfs.update({vrf for vrf in self.want_deploy.get("vrfNames", "").split(",") if vrf})
        self.diff_deploy.update({"vrfNames": ",".join(all_vrfs)})

        msg = "self.diff_attach: "
        msg += f"{json.dumps(self.diff_attach, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_deploy: "
        msg += f"{json.dumps(self.diff_deploy, indent=4)}"
        self.log.debug(msg)

    def diff_merge_create(self, replace=False) -> None:
        """
        # Summary

        Populates the following lists

        - self.diff_create
        - self.diff_create_update
        - self.diff_create_quick

        TODO: arobel: replace parameter is not used.  See Note 1 below.

        Notes
        1.  The replace parameter is not used in this method and should be removed.
            This was used prior to refactoring this method, and diff_merge_attach,
            from an earlier method.  diff_merge_attach() does still use
            the replace parameter.

            In order to remove this, we have to update 35 unit tests, so we'll
            do this as part of a future PR.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        self.conf_changed = {}

        diff_create: list = []
        diff_create_update: list = []
        diff_create_quick: list = []

        want_c: dict = {}
        for want_c in self.want_create:
            vrf_found: bool = False
            have_c: dict = {}
            for have_c in self.have_create:
                if want_c["vrfName"] != have_c["vrfName"]:
                    continue
                vrf_found = True
                msg = "Calling diff_for_create with: "
                msg += f"want_c: {json.dumps(want_c, indent=4, sort_keys=True)}, "
                msg += f"have_c: {json.dumps(have_c, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                diff, changed = self.diff_for_create(want_c, have_c)

                msg = "diff_for_create() returned with: "
                msg += f"changed {changed}, "
                msg += f"diff {json.dumps(diff, indent=4, sort_keys=True)}, "
                self.log.debug(msg)

                msg = f"Updating self.conf_changed[{want_c['vrfName']}] "
                msg += f"with {changed}"
                self.log.debug(msg)
                self.conf_changed.update({want_c["vrfName"]: changed})

                if diff:
                    msg = "Appending diff_create_update with "
                    msg += f"{json.dumps(diff, indent=4, sort_keys=True)}"
                    self.log.debug(msg)
                    diff_create_update.append(diff)
                break

            if vrf_found:
                continue
            vrf_id = want_c.get("vrfId", None)
            if vrf_id is not None:
                diff_create.append(want_c)
            else:
                # Special case:
                # 1. Auto generate vrfId since it is not provided in the playbook task:
                #    - In this case, query the controller for a vrfId and
                #      use it in the payload.
                #    - This vrf create request needs to be pushed individually
                #      i.e. not as a bulk operation.
                # TODO: arobel: review this with Mike to understand why this
                #       couldn't be moved to a method called by push_to_remote().
                vrf_id = self.get_next_fabric_vrf_id(self.fabric)

                want_c.update({"vrfId": vrf_id})

                want_c.update({"vrfTemplateConfig": self.update_vrf_template_config(want_c)})
                want_c["vrfTemplateConfig"]["vrfSegmentId"] = vrf_id

                diff_create_quick.append(want_c)

                if self.module.check_mode:
                    continue

                # arobel: TODO: Not covered by UT
                endpoint = EpVrfPost()
                endpoint.fabric_name = self.fabric

                args = SendToControllerArgs(
                    action="attach",
                    path=endpoint.path,
                    verb=endpoint.verb,
                    payload=json.dumps(want_c),
                    log_response=True,
                    is_rollback=True,
                )
                self.send_to_controller(args)

        self.diff_create = copy.deepcopy(diff_create)
        self.diff_create_update = copy.deepcopy(diff_create_update)
        self.diff_create_quick = copy.deepcopy(diff_create_quick)

        msg = "self.diff_create: "
        msg += f"{json.dumps(self.diff_create, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_create_quick: "
        msg += f"{json.dumps(self.diff_create_quick, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_create_update: "
        msg += f"{json.dumps(self.diff_create_update, indent=4)}"
        self.log.debug(msg)

    def diff_merge_attach(self, replace=False) -> None:
        """
        # Summary

        Populates the following

        - self.diff_attach
        - self.diff_deploy

        By comparing the current state of attachments (self.have_attach_models)
        with the desired state (self.want_attach) and determining which attachments
        need to be updated.

        ## params

        - replace: Passed unaltered to self.diff_for_attach_deploy()
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = f"replace == {replace}."
        self.log.debug(msg)

        if not self.want_attach:
            self.diff_attach = []
            self.diff_deploy = {}
            msg = "Early return. No attachments to process."
            self.log.debug(msg)
            return

        diff_attach: list = []
        diff_deploy: dict = {}
        all_vrfs: set = set()

        msg = "self.want_attach: "
        msg += f"type: {type(self.want_attach)}"
        self.log.debug(msg)
        msg = f"value: {json.dumps(self.want_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "self.have_attach_models: "
        self.log.debug(msg)
        self.log_list_of_models(self.have_attach_models, by_alias=True)

        for want_attach in self.want_attach:
            msg = f"type(want_attach): {type(want_attach)}, "
            msg += f"want_attach: {json.dumps(want_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            # Check user intent for this VRF and don't add it to the all_vrfs
            # set if the user has not requested a deploy.
            want_config_model: PlaybookVrfModelV12 = self.find_model_in_list_by_key_value(
                search=self.validated_playbook_config_models, key="vrf_name", value=want_attach["vrfName"]
            )
            want_config_deploy = want_config_model.deploy if want_config_model else False
            vrf_to_deploy: str = ""
            attach_found = False
            for have_attach_model in self.have_attach_models:
                if want_attach.get("vrfName") != have_attach_model.vrf_name:
                    continue
                attach_found = True
                diff, deploy_vrf_bool = self.diff_for_attach_deploy(
                    want_attach_list=want_attach["lanAttachList"],
                    have_lan_attach_list_models=have_attach_model.lan_attach_list,
                    replace=replace,
                )
                msg = "diff_for_attach_deploy() returned with: "
                msg += f"deploy_vrf_bool {deploy_vrf_bool}, "
                msg += f"diff {json.dumps(diff, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                if diff:
                    base = copy.deepcopy(want_attach)
                    base["lanAttachList"] = diff

                    diff_attach.append(base)
                    if (want_config_deploy is True) and (deploy_vrf_bool is True):
                        vrf_to_deploy = want_attach.get("vrfName")
                else:
                    if want_config_deploy is True and (deploy_vrf_bool or self.conf_changed.get(want_attach.get("vrfName"), False)):
                        vrf_to_deploy = want_attach.get("vrfName")

            msg = f"attach_found: {attach_found}"
            self.log.debug(msg)

            if not attach_found and want_attach.get("lanAttachList"):
                attach_list = []
                for lan_attach in want_attach["lanAttachList"]:
                    if lan_attach.get("isAttached"):
                        del lan_attach["isAttached"]
                    if lan_attach.get("is_deploy") is True:
                        vrf_to_deploy = want_attach["vrfName"]
                    lan_attach["deployment"] = True
                    attach_list.append(copy.deepcopy(lan_attach))
                if attach_list:
                    base = copy.deepcopy(want_attach)
                    base["lanAttachList"] = attach_list
                    diff_attach.append(base)

            if vrf_to_deploy:
                all_vrfs.add(vrf_to_deploy)

        if len(all_vrfs) != 0:
            diff_deploy.update({"vrfNames": ",".join(all_vrfs)})

        self.diff_attach = copy.deepcopy(diff_attach)
        self.diff_deploy = copy.deepcopy(diff_deploy)

        msg = "self.diff_attach: "
        msg += f"{json.dumps(self.diff_attach, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_deploy: "
        msg += f"{json.dumps(self.diff_deploy, indent=4)}"
        self.log.debug(msg)

    def get_diff_merge(self, replace=False):
        """
        # Summary

        Call the following methods

        - diff_merge_create()
        - diff_merge_attach()
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = f"replace == {replace}"
        self.log.debug(msg)

        self.diff_merge_create(replace)
        self.diff_merge_attach(replace)

    def format_diff_attach(self, diff_attach: list[dict], diff_deploy: list[str]) -> list[dict]:
        """
        Populate the diff list with remaining attachment entries.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if len(diff_attach) > 0:
            msg = f"type(diff_attach[0]): {type(diff_attach[0])}, length {len(diff_attach)}"
            self.log.debug(msg)
        msg = "diff_attach: "
        msg += f"{json.dumps(diff_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if len(diff_deploy) > 0:
            msg = f"type(diff_deploy[0]): {type(diff_deploy[0])}, length {len(diff_deploy)}"
            self.log.debug(msg)
        msg = "diff_deploy: "
        msg += f"{json.dumps(diff_deploy, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not diff_attach:
            msg = "No diff_attach entries to process. Returning empty list."
            self.log.debug(msg)
            return []
        diff = []
        for vrf in diff_attach:
            # TODO: arobel: using models, we get a KeyError for lan_attach[vlan], so we try lan_attach[vlanId] too.
            # TODO: arobel: remove this once we've fixed the model to dump what is expected here.
            new_attach_list = [
                {
                    "ip_address": self.serial_number_to_ipv4.convert(lan_attach.get("serialNumber")),
                    "vlan_id": lan_attach.get("vlan") or lan_attach.get("vlanId"),
                    "deploy": lan_attach["deployment"],
                }
                for lan_attach in vrf["lanAttachList"]
            ]
            msg = "ZZZ: new_attach_list: "
            msg += f"{json.dumps(new_attach_list, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            msg = f"ZZZ: diff_deploy: {diff_deploy}"
            self.log.debug(msg)
            if new_attach_list:
                if diff_deploy and vrf["vrfName"] in diff_deploy:
                    diff_deploy.remove(vrf["vrfName"])
                new_attach_dict = {
                    "attach": new_attach_list,
                    "vrf_name": vrf["vrfName"],
                }
                diff.append(new_attach_dict)

        msg = "returning diff (diff_attach): "
        msg += f"{json.dumps(diff, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return diff

    def format_diff_create(self, diff_create: list, diff_attach: list, diff_deploy: list) -> list:
        """
        # Summary

        Populate the diff list with VRF create/update entries.

        ## Raises

        - fail_json if vrfTemplateConfig fails validation
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        diff = []
        for want_d in diff_create:
            found_attach = self.find_dict_in_list_by_key_value(search=diff_attach, key="vrfName", value=want_d["vrfName"])
            found_create = copy.deepcopy(want_d)

            found_create.update(
                {
                    "attach": [],
                    "service_vrf_template": found_create["serviceVrfTemplate"],
                    "vrf_extension_template": found_create["vrfExtensionTemplate"],
                    "vrf_id": found_create["vrfId"],
                    "vrf_name": found_create["vrfName"],
                    "vrf_template": found_create["vrfTemplate"],
                }
            )

            vrf_template_config = json.loads(found_create["vrfTemplateConfig"])
            try:
                vrf_controller_to_playbook = VrfControllerToPlaybookV12Model(**vrf_template_config)
                found_create.update(vrf_controller_to_playbook.model_dump(by_alias=False))
            except ValidationError as error:
                msg = f"{self.class_name}.format_diff_create: Validation error: {error}"
                self.module.fail_json(msg=msg)

            for key in ["fabric", "serviceVrfTemplate", "vrfExtensionTemplate", "vrfId", "vrfName", "vrfTemplate", "vrfTemplateConfig"]:
                found_create.pop(key, None)

            if diff_deploy and found_create["vrf_name"] in diff_deploy:
                diff_deploy.remove(found_create["vrf_name"])
            if not found_attach:
                diff.append(found_create)
                continue

            # TODO: arobel: using models, we get a KeyError for lan_attach[vlan], so we try lan_attach[vlanId] too.
            # TODO: arobel: remove this once we've fixed the model to dump what is expected here.
            found_create["attach"] = [
                {
                    "ip_address": self.serial_number_to_ipv4.convert(lan_attach.get("serialNumber")),
                    "vlan_id": lan_attach.get("vlan") or lan_attach.get("vlanId"),
                    "deploy": lan_attach["deployment"],
                }
                for lan_attach in found_attach["lanAttachList"]
            ]
            diff.append(found_create)
            diff_attach.remove(found_attach)
        msg = "Returning diff (diff_create): "
        msg += f"{json.dumps(diff, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return diff

    def format_diff_deploy(self, diff_deploy: list[str]) -> list:
        """
        # Summary

        Populate the diff list with deploy/undeploy entries.

        ## Raises

        - None

        ## Notes

        - Unit tests all return [] for diff_deploy.  Look into add a test case that returns a non-empty list.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        diff = []
        for vrf in diff_deploy:
            new_deploy_dict = {"vrf_name": vrf}
            diff.append(copy.deepcopy(new_deploy_dict))

        msg = "Returning diff (diff_deploy): "
        msg += f"{json.dumps(diff, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return diff

    def format_diff(self) -> None:
        """
        # Summary

        Called from modules/dcnm_vrf.py

        Populate self.diff_input_format, which represents the
        difference to the controller configuration after the playbook
        has run, from the information in the following lists:

        - self.diff_create
        - self.diff_create_quick
        - self.diff_create_update
        - self.diff_attach
        - self.diff_detach
        - self.diff_deploy
        - self.diff_undeploy

        self.diff_input_format is formatted using keys a user
        would use in a playbook.  The keys in the above lists
        are those used by the controller API.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        diff_create = copy.deepcopy(self.diff_create)
        diff_create_quick = copy.deepcopy(self.diff_create_quick)
        diff_create_update = copy.deepcopy(self.diff_create_update)

        diff_attach = copy.deepcopy(self.diff_attach)
        if len(diff_attach) > 0:
            msg = f"type(diff_attach[0]): {type(diff_attach[0])} length {len(diff_attach)}"
        else:
            msg = f"type(diff_attach): {type(diff_attach)}, length {len(diff_attach)}, "
        self.log.debug(msg)
        msg = f"{json.dumps(diff_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if len(self.diff_detach) > 0:
            msg = f"type(self.diff_detach[0]): {type(self.diff_detach[0])}, length {len(self.diff_detach)}."
        else:
            msg = f"type(self.diff_detach): {type(self.diff_detach)}, length {len(self.diff_detach)}."
        self.log.debug(msg)
        self.log_list_of_models(self.diff_detach, by_alias=False)

        diff_deploy = self.diff_deploy["vrfNames"].split(",") if self.diff_deploy else []
        diff_undeploy = self.diff_undeploy["vrfNames"].split(",") if self.diff_undeploy else []

        diff_create.extend(diff_create_quick)
        diff_create.extend(diff_create_update)
        diff_attach.extend([model.model_dump(by_alias=True) for model in self.diff_detach])
        diff_deploy.extend(diff_undeploy)

        diff = []
        diff.extend(self.format_diff_create(diff_create, diff_attach, diff_deploy))
        diff.extend(self.format_diff_attach(diff_attach, diff_deploy))
        diff.extend(self.format_diff_deploy(diff_deploy))

        self.diff_input_format = copy.deepcopy(diff)
        msg = "self.diff_input_format: "
        msg += f"{json.dumps(self.diff_input_format, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def push_diff_create_update(self, is_rollback=False) -> None:
        """
        # Summary

        Send diff_create_update to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = "self.diff_create_update: "
        msg += f"{json.dumps(self.diff_create_update, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.diff_create_update:
            msg = "Early return. self.diff_create_update is empty."
            self.log.debug(msg)
            return

        action: str = "create"
        endpoint = EpVrfPost()
        endpoint.fabric_name = self.fabric

        for payload in self.diff_create_update:
            args = SendToControllerArgs(
                action=action,
                path=f"{endpoint.path}/{payload['vrfName']}",
                verb=RequestVerb.PUT,
                payload=json.dumps(payload),
                log_response=True,
                is_rollback=is_rollback,
            )
            self.send_to_controller(args)

    def push_diff_detach(self, is_rollback=False) -> None:
        """
        # Summary

        Send diff_detach to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        self.model_enabled = True
        if self.model_enabled:
            self.push_diff_detach_model(is_rollback)
            self.model_enabled = False
            return

        msg = "self.diff_detach: "
        msg += f"{json.dumps(self.diff_detach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.diff_detach:
            msg = "Early return. self.diff_detach is empty."
            self.log.debug(msg)
            return

        # Replace fabricName key (if present) with fabric key
        for diff_attach in self.diff_detach:
            for lan_attach_item in diff_attach["lanAttachList"]:
                if "fabricName" in lan_attach_item:
                    lan_attach_item["fabric"] = lan_attach_item.pop("fabricName", None)
                if lan_attach_item.get("fabric") is None:
                    msg = "lan_attach_item.fabric is None. "
                    msg += f"Setting it to self.fabric ({self.fabric})."
                    self.log.debug(msg)
                    lan_attach_item["fabric"] = self.fabric

        # For multisite fabric, update the fabric name to the child fabric
        # containing the switches
        if self.fabric_type == "MFD":
            for elem in self.diff_detach:
                for node in elem["lanAttachList"]:
                    node["fabric"] = self.sn_fab[node["serialNumber"]]

        for diff_attach in self.diff_detach:
            for vrf_attach in diff_attach["lanAttachList"]:
                if "is_deploy" in vrf_attach.keys():
                    del vrf_attach["is_deploy"]

        msg = "self.diff_detach after processing: "
        msg += f"{json.dumps(self.diff_detach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        action: str = "attach"
        endpoint = EpVrfPost()
        endpoint.fabric_name = self.fabric

        args = SendToControllerArgs(
            action=action,
            path=f"{endpoint.path}/attachments",
            verb=endpoint.verb,
            payload=json.dumps(self.diff_detach),
            log_response=True,
            is_rollback=is_rollback,
        )
        self.send_to_controller(args)

    def push_diff_detach_model(self, is_rollback=False) -> None:
        """
        # Summary

        Send diff_detach to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = "self.diff_detach: "
        self.log.debug(msg)
        self.log_list_of_models(self.diff_detach, by_alias=False)

        if not self.diff_detach:
            msg = "Early return. self.diff_detach is empty."
            self.log.debug(msg)
            return

        # For multisite fabric, update the fabric name to the child fabric
        # containing the switches
        if self.fabric_type == "MFD":
            for model in self.diff_detach:
                for lan_attach_item in model.lan_attach_list:
                    lan_attach_item.fabric = self.sn_fab[lan_attach_item.serial_number]

        for diff_attach_model in self.diff_detach:
            for lan_attach_item in diff_attach_model.lan_attach_list:
                try:
                    del lan_attach_item.is_deploy
                except AttributeError:
                    # If the model does not have is_deploy, skip the deletion
                    msg = "is_deploy not found in lan_attach_item. "
                    msg += "Continuing without deleting is_deploy."
                    self.log.debug(msg)

        action: str = "attach"
        endpoint = EpVrfPost()
        endpoint.fabric_name = self.fabric

        payload = [model.model_dump(by_alias=True, exclude_none=True, exclude_unset=True) for model in self.diff_detach]

        args = SendToControllerArgs(
            action=action,
            path=f"{endpoint.path}/attachments",
            verb=endpoint.verb,
            payload=json.dumps(payload),
            log_response=True,
            is_rollback=is_rollback,
        )
        self.send_to_controller(args)

    def push_diff_undeploy(self, is_rollback=False):
        """
        # Summary

        Send diff_undeploy to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = "self.diff_undeploy: "
        msg += f"{json.dumps(self.diff_undeploy, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.diff_undeploy:
            msg = "Early return. self.diff_undeploy is empty."
            self.log.debug(msg)
            return

        action = "deploy"
        endpoint = EpVrfPost()
        endpoint.fabric_name = self.fabric
        args = SendToControllerArgs(
            action=action,
            path=f"{endpoint.path}/deployments",
            verb=endpoint.verb,
            payload=json.dumps(self.diff_undeploy),
            log_response=True,
            is_rollback=is_rollback,
        )
        self.send_to_controller(args)

    def push_diff_delete(self, is_rollback=False) -> None:
        """
        # Summary

        Send diff_delete to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = "self.diff_delete: "
        msg += f"{json.dumps(self.diff_delete, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.diff_delete:
            msg = "Early return. self.diff_delete is None."
            self.log.debug(msg)
            return

        self.wait_for_vrf_del_ready()

        del_failure: set = set()
        endpoint = EpVrfGet()
        endpoint.fabric_name = self.fabric
        for vrf, state in self.diff_delete.items():
            if state == "OUT-OF-SYNC":
                del_failure.add(vrf)
                continue
            args = SendToControllerArgs(
                action="delete",
                path=f"{endpoint.path}/{vrf}",
                verb=RequestVerb.DELETE,
                payload=json.dumps(self.diff_delete),
                log_response=True,
                is_rollback=is_rollback,
            )
            self.send_to_controller(args)

        if len(del_failure) > 0:
            msg = f"{self.class_name}.push_diff_delete: "
            msg += f"Deletion of vrfs {','.join(del_failure)} has failed"
            self.result["response"].append(msg)
            self.module.fail_json(msg=self.result)

    def get_controller_vrf_attachment_models(self, vrf_name: str) -> list[ControllerResponseVrfsAttachmentsDataItem]:
        """
        ## Summary

        Given a vrf_name, query the controller for the attachment list
        for that vrf and return a list of ControllerResponseVrfsAttachmentsDataItem
        models.

        ## Raises

        - ValueError: If the response from the controller is None.
        - ValueError: If the response from the controller is not valid.
        - fail_json: If the fabric does not exist on the controller.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        path_get_vrf_attach = self.paths["GET_VRF_ATTACH"].format(self.fabric, vrf_name)
        controller_response = dcnm_send(self.module, "GET", path_get_vrf_attach)

        msg = f"path_get_vrf_attach: {path_get_vrf_attach}"
        self.log.debug(msg)
        msg = "controller_response: "
        msg += f"{json.dumps(controller_response, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if controller_response is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to retrieve endpoint. "
            msg += f"verb GET, path {path_get_vrf_attach}"
            raise ValueError(msg)

        validated_response = ControllerResponseVrfsAttachmentsV12(**controller_response)
        msg = "validated_response (ControllerResponseVrfsAttachmentsV12): "
        msg += f"{json.dumps(validated_response.model_dump(by_alias=True), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        generic_response = ControllerResponseGenericV12(**controller_response)
        missing_fabric, not_ok = self.handle_response(generic_response, "query")

        if missing_fabric or not_ok:
            msg0 = f"caller: {caller}. "
            msg1 = f"{msg0} Fabric {self.fabric} not present on DCNM"
            msg2 = f"{msg0} Unable to find attachments for "
            msg2 += f"vrf {vrf_name} under fabric {self.fabric}"
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
        return validated_response.DATA

    def get_diff_query_for_vrfs_in_want(self, vrf_object_models: list[VrfObjectV12]) -> list[dict]:
        """
        Query the controller for the current state of the VRFs in the fabric
        that are present in self.want_create_payload_models.

        ## Raises

        - ValueError: If any controller response is not valid.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        query: list[dict] = []

        if not self.want_create_payload_models:
            msg = "Early return. No VRFs in self.want_create_payload_models to process."
            self.log.debug(msg)
            return query

        if not vrf_object_models:
            msg = f"Early return. No VRFs exist in fabric {self.fabric}."
            self.log.debug(msg)
            return query

        # Lookup controller VRFs by name, used in for loop below.
        vrf_object_model_lookup = {model.vrfName: model for model in vrf_object_models}
        for want_create_payload_model in self.want_create_payload_models:
            vrf_model = vrf_object_model_lookup.get(want_create_payload_model.vrf_name)
            if not vrf_model:
                continue

            query_item = {"parent": vrf_model.model_dump(by_alias=True), "attach": []}
            vrf_attachment_models = self.get_controller_vrf_attachment_models(vrf_model.vrfName)

            msg = f"caller: {caller}. vrf_attachment_models: length {len(vrf_attachment_models)}."
            self.log.debug(msg)
            self.log_list_of_models(vrf_attachment_models)

            for vrf_attachment_model in vrf_attachment_models:
                if want_create_payload_model.vrf_name != vrf_attachment_model.vrf_name or not vrf_attachment_model.lan_attach_list:
                    continue

                for lan_attach_model in vrf_attachment_model.lan_attach_list:
                    params = {
                        "fabric": self.fabric,
                        "serialNumber": lan_attach_model.switch_serial_no,
                        "vrfName": lan_attach_model.vrf_name,
                    }

                    lite_objects = self.get_list_of_vrfs_switches_data_item_model(params)

                    msg = f"Caller {caller}. Called get_list_of_vrfs_switches_data_item_model with params: "
                    msg += f"{json.dumps(params, indent=4, sort_keys=True)}"
                    self.log.debug(msg)
                    msg = f"Caller {caller}. lite_objects: length: {len(lite_objects)}."
                    self.log.debug(msg)
                    self.log_list_of_models(lite_objects)

                    if lite_objects:
                        query_item["attach"].append(lite_objects[0].model_dump(by_alias=True))
            query.append(query_item)

        msg = f"Caller {caller}. Returning query: "
        msg += f"{json.dumps(query, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return copy.deepcopy(query)

    def get_diff_query_for_all_controller_vrfs(self, vrf_object_models: list[VrfObjectV12]) -> list[dict]:
        """
        Query the controller for the current state of all VRFs in the fabric.

        ## Raises

        - ValueError: If the response from the controller is not valid.
        - fail_json: If lite_objects_data is not a list.

        ## Returns

        A list of dictionaries with the following structure:

        [
            {
                "parent": VrfObjectV12
                "attach": [
                    {
                        "ip_address": str,
                        "vlan_id": int,
                        "deploy": bool
                    }
                ]
            }
        ]
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        query: list[dict] = []

        if not vrf_object_models:
            msg = f"Early return. No VRFs exist in fabric {self.fabric}."
            self.log.debug(msg)
            return query

        for vrf in vrf_object_models:

            item = {"parent": vrf.model_dump(by_alias=True), "attach": []}

            vrf_attachment_models = self.get_controller_vrf_attachment_models(vrf.vrfName)

            msg = f"caller: {caller}. vrf_attachment_models: length {len(vrf_attachment_models)}."
            self.log.debug(msg)
            self.log_list_of_models(vrf_attachment_models)

            for vrf_attach in vrf_attachment_models:
                if not vrf_attach.lan_attach_list:
                    continue
                lan_attach_models = vrf_attach.lan_attach_list
                msg = f"lan_attach_models: length: {len(lan_attach_models)}"
                self.log.debug(msg)
                self.log_list_of_models(lan_attach_models)

                for lan_attach_model in lan_attach_models:
                    params = {
                        "fabric": self.fabric,
                        "serialNumber": lan_attach_model.switch_serial_no,
                        "vrfName": lan_attach_model.vrf_name,
                    }
                    msg = f"Calling get_list_of_vrfs_switches_data_item_model with: {params}"
                    self.log.debug(msg)

                    lite_objects = self.get_list_of_vrfs_switches_data_item_model(params)

                    msg = f"Caller {caller}. lite_objects: length: {len(lite_objects)}."
                    self.log.debug(msg)
                    self.log_list_of_models(lite_objects)

                    if not lite_objects:
                        continue
                    item["attach"].append(lite_objects[0].model_dump(by_alias=True))
                query.append(item)

        msg = f"Returning query: {query}"
        self.log.debug(msg)
        return query

    def get_diff_query(self) -> None:
        """
        Query the controller for the current state of the VRFs in the fabric.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        vrf_object_models = self.get_controller_vrf_object_models()

        msg = f"vrf_object_models: length {len(vrf_object_models)}."
        self.log.debug(msg)
        self.log_list_of_models(vrf_object_models)

        if not vrf_object_models:
            return

        if self.config:
            query = self.get_diff_query_for_vrfs_in_want(vrf_object_models)
        else:
            query = self.get_diff_query_for_all_controller_vrfs(vrf_object_models)

        self.query = copy.deepcopy(query)
        msg = f"self.query: {json.dumps(self.query, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def update_vrf_template_config_from_vrf_model(self, vrf_model: VrfObjectV12) -> VrfTemplateConfigV12:
        """
        # Summary

        Update the following fields in VrfObjectV12.VrfTemplateConfigV12 and
        return the updated VrfTemplateConfigV12 model instance.

        - vrfVlanId
          - Updated from VrfObjectModelV12.vlan_id
          - if 0, get the next available vlan_id from the controller
          - else, use the vlan_id in vrfTemplateConfig
        - vrfSegmentId
          - Updated from VrfObjectModelV12.vrf_id
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        # Don't modify the caller's copy
        vrf_model = copy.deepcopy(vrf_model)

        vrf_segment_id = vrf_model.vrfId
        vlan_id = vrf_model.vrfTemplateConfig.vlan_id

        if vlan_id == 0:
            vlan_id = self.get_next_fabric_vlan_id(self.fabric)
            msg = "vlan_id was 0. "
            msg += f"Using next available controller-generated vlan_id: {vlan_id}"
            self.log.debug(msg)

        vrf_model.vrfTemplateConfig.vlan_id = vlan_id
        vrf_model.vrfTemplateConfig.vrf_id = vrf_segment_id
        return vrf_model.vrfTemplateConfig

    def update_vrf_template_config(self, vrf: dict) -> dict:
        """
        TODO: Legacy method.  Remove when all callers are updated to use update_vrf_template_config_from_vrf_model.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        vrf_template_config = json.loads(vrf["vrfTemplateConfig"])
        vlan_id = vrf_template_config.get("vrfVlanId", 0)

        if vlan_id == 0:
            vlan_id = self.get_next_fabric_vlan_id(self.fabric)
            msg = "vlan_id was 0. "
            msg += f"Using next available controller-generated vlan_id: {vlan_id}"
            self.log.debug(msg)

        vrf_template_config.update({"vrfVlanId": vlan_id})
        vrf_template_config.update({"vrfSegmentId": vrf.get("vrfId")})

        msg = f"Returning vrf_template_config: {json.dumps(vrf_template_config, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return json.dumps(vrf_template_config)

    def vrf_model_to_payload(self, vrf_model: VrfObjectV12) -> dict:
        """
        # Summary

        Convert a VrfObjectV12 model to a VrfPayloadV12 model and return
        as a dictionary suitable for sending to the controller.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = f"vrf_model: {json.dumps(vrf_model.model_dump(by_alias=True), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        vrf_payload = VrfPayloadV12(**vrf_model.model_dump(exclude_unset=True, by_alias=True))

        return vrf_payload.model_dump_json(exclude_unset=True, by_alias=True)

    def push_diff_create(self, is_rollback=False) -> None:
        """
        # Summary

        Update the VRFs in self.diff_create and send them to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = "self.diff_create: "
        msg += f"{json.dumps(self.diff_create, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.diff_create:
            msg = "Early return. self.diff_create is empty."
            self.log.debug(msg)
            return

        for vrf in self.diff_create:
            vrf_model = VrfObjectV12(**vrf)
            vrf_model.vrfTemplateConfig = self.update_vrf_template_config_from_vrf_model(vrf_model)

            msg = "Sending vrf create request."
            self.log.debug(msg)

            endpoint = EpVrfPost()
            endpoint.fabric_name = self.fabric
            args = SendToControllerArgs(
                action="create",
                path=endpoint.path,
                verb=endpoint.verb,
                payload=self.vrf_model_to_payload(vrf_model),
                log_response=True,
                is_rollback=is_rollback,
            )
            self.send_to_controller(args)

    def is_border_switch(self, serial_number) -> bool:
        """
        # Summary

        Given a switch serial_number:

        -   Return True if the switch is a border switch
        -   Return False otherwise
        """
        switch_role = self.serial_number_to_switch_role.convert(serial_number)
        return re.search(r"\bborder\b", switch_role.lower())

    def send_to_controller(self, args: SendToControllerArgs) -> None:
        """
        # Summary

        Send a request to the controller.

        Update self.response with the response from the controller.

        ## Raises

        -   ValueError: If the response from the controller is None.

        ## params

        args: instance of SendToControllerArgs containing the following
        -   `action`: The action to perform (create, update, delete, etc.)
        -   `verb`: The HTTP verb to use (GET, POST, PUT, DELETE)
        -   `path`: The URL path to send the request to
        -   `payload`: The payload to send with the request (None for no payload)
        -   `log_response`: If True, log the response in the result, else
            do not include the response in the result
        -   `is_rollback`: If True, attempt to rollback on failure
        -   `response_model`: The model to use to validate the response (optional, default=ControllerResponseGenericV12)

        ## Notes

        1. send_to_controller sends the payload, if provided, as-is. Hence,
           it is the caller's responsibility to ensure payload integrity.
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = "TX controller: "
        self.log.debug(msg)
        msg = f"action: {args.action}, "
        self.log.debug(msg)
        msg = f"verb: {args.verb.value}, "
        msg += f"path: {args.path}, "
        msg += f"log_response: {args.log_response}, "
        msg += "type(payload): "
        msg += f"{type(args.payload)}, "
        self.log.debug(msg)
        msg = "payload: "
        if args.payload is None:
            msg += f"{args.payload}"
        else:
            msg += f"{json.dumps(json.loads(args.payload), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if args.payload is not None:
            controller_response = dcnm_send(self.module, args.verb.value, args.path, args.payload)
        else:
            controller_response = dcnm_send(self.module, args.verb.value, args.path)

        if controller_response is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "Unable to retrieve endpoint. "
            msg += f"verb {args.verb.value}, path {args.path}"
            raise ValueError(msg)

        self.response = copy.deepcopy(controller_response)

        msg = "RX controller:"
        self.log.debug(msg)
        msg = f"verb: {args.verb.value}, "
        msg += f"path: {args.path}"
        self.log.debug(msg)

        msg = "controller_response: "
        msg += f"{json.dumps(controller_response, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "Calling self.handle_response. "
        msg += "self.result[changed]): "
        msg += f"{self.result['changed']}"
        self.log.debug(msg)

        if args.log_response is True:
            self.result["response"].append(controller_response)

        if args.response_model is None:
            response_model = ControllerResponseGenericV12
        else:
            response_model = args.response_model

        try:
            validated_response = response_model(**controller_response)
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += f"Unable to validate controller_response using model {response_model.__name__}. "
            msg += f"controller_response: {json.dumps(controller_response, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            self.module.fail_json(msg=msg, error=str(error))

        msg = f"validated_response: ({response_model.__name__}), "
        msg += f"{json.dumps(validated_response.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        fail, self.result["changed"] = self.handle_response(validated_response, args.action)

        msg = f"caller: {caller}, "
        msg += "RESULT self.handle_response: "
        msg = f"fail: {fail}, changed: {self.result['changed']}"
        self.log.debug(msg)

        if fail:
            if args.is_rollback:
                self.failed_to_rollback = True
                return
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}, "
            msg += "Calling self.failure."
            self.log.debug(msg)
            self.failure(controller_response)

    def get_vrf_attach_fabric_name(self, vrf_attach: PayloadVrfsAttachmentsLanAttachListItem) -> str:
        """
        # Summary

        For multisite fabrics, return the name of the child fabric returned by
        `self.sn_fab[vrf_attach.serialNumber]`

        ## params

        - `vrf_attach`

        A PayloadVrfsAttachmentsLanAttachListItem model.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = "Received vrf_attach: "
        msg += f"{json.dumps(vrf_attach.model_dump(by_alias=True), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if self.fabric_type != "MFD":
            msg = f"FABRIC_TYPE {self.fabric_type} is not MFD. "
            msg += f"Returning unmodified fabric name {vrf_attach.fabric}."
            self.log.debug(msg)
            return vrf_attach.fabric

        msg = f"self.fabric: {self.fabric}, "
        msg += f"fabric_type: {self.fabric_type}, "
        msg += f"vrf_attach.fabric: {vrf_attach.fabric}."
        self.log.debug(msg)

        serial_number = vrf_attach.serial_number

        if serial_number is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "Unable to parse vrf_attach.serial_number. "
            msg += f"{json.dumps(vrf_attach.model_dump(by_alias=False), indent=4, sort_keys=True)}"
            self.log.debug(msg)
            self.module.fail_json(msg)

        child_fabric_name = self.sn_fab[serial_number]

        if child_fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "Unable to determine child_fabric_name for serial_number "
            msg += f"{serial_number}."
            self.log.debug(msg)
            self.module.fail_json(msg)

        msg = f"serial_number: {serial_number}. "
        msg += f"Returning child_fabric_name: {child_fabric_name}. "
        self.log.debug(msg)

        return child_fabric_name

    def push_diff_attach_model(self, is_rollback=False) -> None:
        """
        # Summary

        Send diff_attach to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if not self.diff_attach:
            msg = "Early return. self.diff_attach is empty. "
            msg += f"{json.dumps(self.diff_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            return

        try:
            instance = DiffAttachToControllerPayload()
            instance.ansible_module = self.module
            instance.diff_attach = copy.deepcopy(self.diff_attach)
            instance.fabric_inventory = self.inventory_data
            # TODO: remove once we use fabricTechnology in DiffAttachToControllerPayload
            instance.fabric_type = self.fabric_type
            instance.playbook_models = self.validated_playbook_config_models
            instance.sender = dcnm_send
            instance.commit()
            payload = instance.payload
        except ValueError as error:
            self.module.fail_json(error)

        endpoint = EpVrfPost()
        endpoint.fabric_name = self.fabric
        args = SendToControllerArgs(
            action="attach",
            path=f"{endpoint.path}/attachments",
            verb=endpoint.verb,
            payload=payload,
            log_response=True,
            is_rollback=is_rollback,
        )
        self.send_to_controller(args)

    def push_diff_deploy(self, is_rollback=False):
        """
        # Summary

        Send diff_deploy to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if not self.diff_deploy:
            msg = "Early return. self.diff_deploy is empty."
            self.log.debug(msg)
            return

        endpoint = EpVrfPost()
        endpoint.fabric_name = self.fabric
        args = SendToControllerArgs(
            action="deploy",
            path=f"{endpoint.path}/deployments",
            verb=endpoint.verb,
            payload=json.dumps(self.diff_deploy),
            log_response=True,
            is_rollback=is_rollback,
        )
        self.send_to_controller(args)

    def release_resources_by_id(self, id_list=None) -> None:
        """
        # Summary

        Given a list of resource IDs, send a request to the controller
        to release them.

        ## params

        -   id_list: A list of resource IDs to release.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if id_list is None:
            id_list = []

        if not isinstance(id_list, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "id_list must be a list of resource IDs. "
            msg += f"Got: {id_list}."
            self.module.fail_json(msg)

        try:
            id_list = [int(x) for x in id_list]
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "id_list must be a list of resource IDs. "
            msg += "Where each id is convertable to integer."
            msg += f"Got: {id_list}. "
            msg += f"Error detail: {error}"
            self.module.fail_json(msg)

        # The controller can release only around 500-600 IDs per
        # request (not sure of the exact number).  We break up
        # requests into smaller lists here.  In practice, we'll
        # likely ever only have one resulting list.
        id_list_of_lists = self.get_list_of_lists([str(x) for x in id_list], 512)

        for item in id_list_of_lists:
            msg = "Releasing resource IDs: "
            msg += f"{','.join(item)}"
            self.log.debug(msg)

            path: str = "/appcenter/cisco/ndfc/api/v1/lan-fabric"
            path += "/rest/resource-manager/resources"
            path += f"?id={','.join(item)}"
            args = SendToControllerArgs(
                action="deploy",
                path=path,
                verb=RequestVerb.DELETE,
                payload=None,
                log_response=False,
                is_rollback=False,
            )
            self.send_to_controller(args)

    def release_orphaned_resources(self, vrf: str, is_rollback=False) -> None:
        """
        # Summary

        Release orphaned resources.

        ## Description

        After a VRF delete operation, resources such as the TOP_DOWN_VRF_VLAN
        resource below, can be orphaned from their VRFs.  Below, notice that
        resourcePool.vrfName is null.  This method releases resources if
        the following are true for the resources:

        - allocatedFlag is False
        - entityName == vrf
        - fabricName == self.fabric

        ```json
        [
            {
                "id": 36368,
                "resourcePool": {
                    "id": 0,
                    "poolName": "TOP_DOWN_VRF_VLAN",
                    "fabricName": "f1",
                    "vrfName": null,
                    "poolType": "ID_POOL",
                    "dynamicSubnetRange": null,
                    "targetSubnet": 0,
                    "overlapAllowed": false,
                    "hierarchicalKey": "f1"
                },
                "entityType": "Device",
                "entityName": "VRF_1",
                "allocatedIp": "201",
                "allocatedOn": 1734040978066,
                "allocatedFlag": false,
                "allocatedScopeValue": "FDO211218GC",
                "ipAddress": "172.22.150.103",
                "switchName": "cvd-1312-leaf",
                "hierarchicalKey": "0"
            }
        ]
        ```
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/"
        path += f"resource-manager/fabric/{self.fabric}/"
        path += "pools/TOP_DOWN_VRF_VLAN"

        args = SendToControllerArgs(
            action="release_resources",
            path=path,
            verb=RequestVerb.GET,
            payload=None,
            log_response=False,
            is_rollback=False,
        )
        self.send_to_controller(args)
        resp = copy.deepcopy(self.response)

        generic_response = ControllerResponseGenericV12(**resp)

        fail, self.result["changed"] = self.handle_response(generic_response, action="release_resources")

        if fail:
            if is_rollback:
                self.failed_to_rollback = True
                return
            self.failure(resp)

        delete_ids: list = []
        for item in resp["DATA"]:
            if "entityName" not in item:
                continue
            if item["entityName"] != vrf:
                continue
            if item.get("allocatedFlag") is not False:
                continue
            if item.get("id") is None:
                continue

            msg = f"item {json.dumps(item, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            delete_ids.append(item["id"])

        self.release_resources_by_id(delete_ids)

    def push_to_remote(self, is_rollback=False) -> None:
        """
        # Summary

        Send all diffs to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if self.model_enabled:
            self.push_to_remote_model(is_rollback=is_rollback)
            return

        self.push_diff_create_update(is_rollback=is_rollback)

        # The detach and un-deploy operations are executed before the
        # create,attach and deploy to address cases where a VLAN for vrf
        # attachment being deleted is re-used on a new vrf attachment being
        # created. This is needed specially for state: overridden

        self.push_diff_detach(is_rollback=is_rollback)
        self.push_diff_undeploy(is_rollback=is_rollback)

        msg = "Calling self.push_diff_delete"
        self.log.debug(msg)

        self.push_diff_delete(is_rollback=is_rollback)
        for vrf_name in self.diff_delete:
            self.release_orphaned_resources(vrf=vrf_name, is_rollback=is_rollback)

        self.push_diff_create(is_rollback=is_rollback)
        self.push_diff_attach_model(is_rollback=is_rollback)
        self.push_diff_deploy(is_rollback=is_rollback)

    def push_to_remote_model(self, is_rollback=False) -> None:
        """
        # Summary

        Send all diffs to the controller
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        self.push_diff_create_update(is_rollback=is_rollback)

        # The detach and un-deploy operations are executed before the
        # create,attach and deploy to address cases where a VLAN for vrf
        # attachment being deleted is re-used on a new vrf attachment being
        # created. This is needed specially for state: overridden

        self.push_diff_detach(is_rollback=is_rollback)
        self.push_diff_undeploy(is_rollback=is_rollback)

        msg = "Calling self.push_diff_delete"
        self.log.debug(msg)

        self.push_diff_delete(is_rollback=is_rollback)
        for vrf_name in self.diff_delete:
            self.release_orphaned_resources(vrf=vrf_name, is_rollback=is_rollback)

        self.push_diff_create(is_rollback=is_rollback)
        self.push_diff_attach_model(is_rollback=is_rollback)
        self.push_diff_deploy(is_rollback=is_rollback)

    def wait_for_vrf_del_ready(self, vrf_name: str = "not_supplied") -> None:
        """
        # Summary

        Wait for VRFs to be ready for deletion.

        ## Raises

        Calls fail_json if VRF has associated network attachments.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        msg = f"vrf_name: {vrf_name}"
        self.log.debug(msg)

        msg = "self.diff_delete: "
        msg += f"{json.dumps(self.diff_delete, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        for vrf in self.diff_delete:
            ok_to_delete: bool = False
            path: str = self.paths["GET_VRF_ATTACH"].format(self.fabric, vrf)

            while not ok_to_delete:
                args = SendToControllerArgs(
                    action="query",
                    path=path,
                    verb=RequestVerb.GET,
                    payload=None,
                    log_response=False,
                    is_rollback=False,
                )
                self.send_to_controller(args)

                response = copy.deepcopy(self.response)
                ok_to_delete = True
                if response.get("DATA") is None:
                    time.sleep(self.wait_time_for_delete_loop)
                    continue

                msg = "response: "
                msg += f"{json.dumps(response, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                attach_list: list = response["DATA"][0]["lanAttachList"]
                msg = f"ok_to_delete: {ok_to_delete}, "
                msg += f"attach_list: {json.dumps(attach_list, indent=4)}"
                self.log.debug(msg)

                attach: dict = {}
                for attach in attach_list:
                    if attach["lanAttachState"] == "OUT-OF-SYNC" or attach["lanAttachState"] == "FAILED":
                        self.diff_delete.update({vrf: "OUT-OF-SYNC"})
                        break
                    if attach["lanAttachState"] == "DEPLOYED" and attach["isLanAttached"] is True:
                        vrf_name = attach.get("vrfName", "unknown")
                        fabric_name: str = attach.get("fabricName", "unknown")
                        switch_ip: str = attach.get("ipAddress", "unknown")
                        switch_name: str = attach.get("switchName", "unknown")
                        vlan_id: str = attach.get("vlanId", "unknown")
                        msg = f"Network attachments associated with vrf {vrf_name} "
                        msg += "must be removed (e.g. using the dcnm_network module) "
                        msg += "prior to deleting the vrf. "
                        msg += f"Details: fabric_name: {fabric_name}, "
                        msg += f"vrf_name: {vrf_name}. "
                        msg += "Network attachments found on "
                        msg += f"switch_ip: {switch_ip}, "
                        msg += f"switch_name: {switch_name}, "
                        msg += f"vlan_id: {vlan_id}"
                        self.module.fail_json(msg=msg)
                    if attach["lanAttachState"] != "NA":
                        time.sleep(self.wait_time_for_delete_loop)
                        self.diff_delete.update({vrf: "DEPLOYED"})
                        ok_to_delete = False
                        break
                    self.diff_delete.update({vrf: "NA"})

    def validate_input(self) -> None:
        """Parse the playbook values, validate to param specs."""
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if self.state == "deleted":
            self.validate_playbook_config_deleted_state()
        elif self.state == "merged":
            self.validate_playbook_config_merged_state()
        elif self.state == "overridden":
            self.validate_playbook_config_overridden_state()
        elif self.state == "query":
            self.validate_playbook_config_query_state()
        elif self.state in ("replaced"):
            self.validate_playbook_config_replaced_state()

    def validate_playbook_config(self) -> None:
        """
        # Summary

        Validate self.config against PlaybookVrfModelV12 and update
        self.validated_playbook_config with the validated config.

        ## Raises

        -   Calls fail_json() if the playbook configuration could not be validated

        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if self.config is None:
            return
        for vrf_config in self.config:
            try:
                msg = "Validating playbook configuration."
                self.log.debug(msg)
                validated_playbook_config = PlaybookVrfModelV12(**vrf_config)
                msg = "validated_playbook_config: "
                msg += f"{json.dumps(validated_playbook_config.model_dump(), indent=4, sort_keys=True)}"
                self.log.debug(msg)
            except ValidationError as error:
                msg = f"Failed to validate playbook configuration. Error detail: {error}"
                self.module.fail_json(msg=msg)

            self.validated_playbook_config.append(validated_playbook_config.model_dump())

            msg = "self.validated_playbook_config: "
            msg += f"{json.dumps(self.validated_playbook_config, indent=4, sort_keys=True)}"
            self.log.debug(msg)

    def validate_playbook_config_model(self) -> None:
        """
        # Summary

        Validate self.config against PlaybookVrfModelV12 and updates
        self.validated_playbook_config_models with the validated config.

        ## Raises

        -   Calls fail_json() if the playbook configuration could not be validated

        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if not self.config:
            msg = "Early return. self.config is empty."
            self.log.debug(msg)
            return

        for config in self.config:
            try:
                msg = "Validating playbook configuration."
                self.log.debug(msg)
                validated_playbook_config = PlaybookVrfModelV12(**config)
            except ValidationError as error:
                # We need to pass the unaltered ValidationError
                # directly to the fail_json method for unit tests to pass.
                self.module.fail_json(msg=error)
            self.validated_playbook_config_models.append(validated_playbook_config)

        msg = "self.validated_playbook_config_models: "
        self.log.debug(msg)
        self.log_list_of_models(self.validated_playbook_config_models)

    def validate_playbook_config_deleted_state(self) -> None:
        """
        # Summary

        Validate the input for deleted state.
        """
        if self.state != "deleted":
            return
        if not self.config:
            return
        self.validate_playbook_config_model()
        self.validate_playbook_config()

    def validate_playbook_config_merged_state(self) -> None:
        """
        # Summary

        Validate the input for merged state.
        """
        if self.state != "merged":
            return

        if self.config is None:
            self.config = []

        method_name = inspect.stack()[0][3]
        if len(self.config) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config element is mandatory for merged state"
            self.module.fail_json(msg=msg)

        self.validate_playbook_config_model()
        self.validate_playbook_config()

    def validate_playbook_config_overridden_state(self) -> None:
        """
        # Summary

        Validate the input for overridden state.
        """
        if self.state != "overridden":
            return
        if not self.config:
            return
        self.validate_playbook_config_model()
        self.validate_playbook_config()

    def validate_playbook_config_query_state(self) -> None:
        """
        # Summary

        Validate the input for query state.
        """
        if self.state != "query":
            return
        if not self.config:
            return
        self.validate_playbook_config_model()
        self.validate_playbook_config()

    def validate_playbook_config_replaced_state(self) -> None:
        """
        # Summary

        Validate the input for replaced state.
        """
        if self.state != "replaced":
            return
        if not self.config:
            return
        self.validate_playbook_config_model()
        self.validate_playbook_config()

    def handle_response_deploy(self, controller_response: ControllerResponseGenericV12) -> tuple:
        """
        # Summary

        Handle the response from the controller for deploy operations.

        ## params

        -   res: The response from the controller.

        ## Returns

        -   fail: True if the response indicates a failure, else False
        -   changed: True if the response indicates a change, else False

        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        changed: bool = True
        fail: bool = False
        try:
            response = ControllerResponseVrfsDeploymentsV12(**controller_response.model_dump())
        except ValueError as error:
            msg = "Unable to parse response. "
            msg += f"Error detail: {error}"
            self.module.fail_json(msg=msg)

        msg = "ControllerResponseVrfsDeploymentsV12: "
        msg += f"{json.dumps(response.model_dump(by_alias=True), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if response.DATA == "No switches PENDING for deployment":
            changed = False
        if response.ERROR != "" or response.RETURN_CODE != 200 or response.MESSAGE != "OK":
            fail = True
        return fail, changed

    def handle_response(self, response_model: ControllerResponseGenericV12, action: str = "not_supplied") -> tuple:
        """
        # Summary

        Handle the response from the controller.

        ## params

        -   res: The response from the controller.
        -   action: The action that was performed. Current actions that are
            passed to this method (some of which are not specifically handled)
            are:

            -   attach
            -   create (not specifically handled)
            -   deploy
            -   query
            -   release_resources (not specifically handled)

        ## Returns

        -   fail: True if the response indicates a failure, else False
        -   changed: True if the response indicates a change, else False

        ## Example return

        - (True, False)  # Indicates a failure, no change
        - (False, True). # Indicates success, change
        - (False, False) # Indicates success, no change
        - (True, True)   # Indicates a failure, change

        ## Raises

        -   Calls fail_json() if the response is invalid
        -   Calls fail_json() if the response is not in the expected format

        """
        caller = inspect.stack()[1][3]
        msg = f"ENTERED. caller {caller}, action {action}, self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        try:
            msg = f"response_model: {json.dumps(response_model.model_dump(), indent=4, sort_keys=True)}"
            self.log.debug(msg)
        except TypeError:
            msg = f"response_model: {response_model.model_dump()}"
            self.log.debug(msg)

        fail = False
        changed = True

        if action == "deploy":
            return self.handle_response_deploy(response_model)

        if action == "query":
            # These if blocks handle responses to the query APIs.
            # Basically all GET operations.
            if response_model.ERROR == "Not Found" and response_model.RETURN_CODE == 404:
                return True, False
            if response_model.RETURN_CODE != 200 or response_model.MESSAGE != "OK":
                return False, True
            return False, False

        # Responses to all other operations POST and PUT are handled here.
        if response_model.MESSAGE != "OK" or response_model.RETURN_CODE != 200:
            fail = True
            changed = False
            return fail, changed
        if response_model.ERROR != "":
            fail = True
            changed = False
        if action == "attach" and "is in use already" in str(response_model.DATA):
            fail = True
            changed = False

        return fail, changed

    def failure(self, resp):
        """
        # Summary

        Handle failures.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        # Do not Rollback for Multi-site fabrics
        if self.fabric_type == "MFD":
            self.failed_to_rollback = True
            self.module.fail_json(msg=resp)
            return

        # Implementing a per task rollback logic here so that we rollback
        # to the have state whenever there is a failure in any of the APIs.
        # The idea would be to run overridden state with want=have and have=dcnm_state
        self.want_create = self.have_create
        self.want_attach = self.have_attach
        self.want_deploy = self.have_deploy

        self.have_create = []
        self.have_attach = []
        self.have_deploy = {}
        self.get_have()
        self.get_diff_override()

        self.push_to_remote(is_rollback=True)

        if self.failed_to_rollback:
            msg1 = "FAILED - Attempted rollback of the task has failed, "
            msg1 += "may need manual intervention"
        else:
            msg1 = "SUCCESS - Attempted rollback of the task has succeeded"

        res = copy.deepcopy(resp)
        res.update({"ROLLBACK_RESULT": msg1})

        if not resp.get("DATA"):
            data = copy.deepcopy(resp.get("DATA"))
            if data.get("stackTrace"):
                data.update({"stackTrace": "Stack trace is hidden, use '-vvvvv' to print it"})
                res.update({"DATA": data})

        # pylint: disable=protected-access
        if self.module._verbosity >= 5:
            self.module.fail_json(msg=res)
        # pylint: enable=protected-access

        self.module.fail_json(msg=res)
