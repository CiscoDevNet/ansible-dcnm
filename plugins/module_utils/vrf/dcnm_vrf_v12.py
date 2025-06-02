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

import pydantic
from ansible.module_utils.basic import AnsibleModule

from ...module_utils.common.api.v1.lan_fabric.rest.top_down.fabrics.vrfs.vrfs import EpVrfGet, EpVrfPost
from ...module_utils.common.enums.http_requests import RequestVerb
from ...module_utils.network.dcnm.dcnm import (
    dcnm_get_ip_addr_info,
    dcnm_send,
    get_fabric_details,
    get_fabric_inventory_details,
    get_ip_sn_dict,
    get_sn_fabric_dict,
)
from .controller_response_generic_v12 import ControllerResponseGenericV12
from .controller_response_vrfs_attachments_v12 import ControllerResponseVrfsAttachmentsV12, VrfsAttachmentsDataItem
from .controller_response_vrfs_deployments_v12 import ControllerResponseVrfsDeploymentsV12
from .controller_response_vrfs_switches_v12 import ControllerResponseVrfsSwitchesV12, ExtensionPrototypeValue, VrfLiteConnProtoItem, VrfsSwitchesDataItem
from .controller_response_vrfs_v12 import ControllerResponseVrfsV12, VrfObjectV12
from .model_detach_list_v12 import DetachList, LanDetachItem
from .model_have_attach_post_mutate_v12 import HaveAttachPostMutate, HaveLanAttachItem
from .model_vrf_attach_payload_v12 import VrfAttachPayloadV12
from .vrf_controller_payload_v12 import VrfPayloadV12
from .vrf_controller_to_playbook_v12 import VrfControllerToPlaybookV12Model
from .vrf_playbook_model_v12 import VrfPlaybookModelV12
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

    """

    action: str
    verb: RequestVerb
    path: str
    payload: Optional[Union[dict, list]]
    log_response: bool = True
    is_rollback: bool = False

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
        self.diff_create: list = []
        self.diff_create_update: list = []
        # self.diff_create_quick holds all the create payloads which are
        # missing a vrfId. These payloads are sent to DCNM out of band
        # (in the get_diff_merge()).  We lose diffs for these without this
        # variable. The content stored here will be helpful for cases like
        # "check_mode" and to print diffs[] in the output of each task.
        self.diff_create_quick: list = []
        self.have_attach: list = []
        self.have_attach_model: list[HaveAttachPostMutate] = []
        self.want_attach: list = []
        self.diff_attach: list = []
        self.validated: list = []
        # diff_detach contains all attachments of a vrf being deleted,
        # especially for state: OVERRIDDEN
        # The diff_detach and delete operations have to happen before
        # create+attach+deploy for vrfs being created. This is to address
        # cases where VLAN from a vrf which is being deleted is used for
        # another vrf. Without this additional logic, the create+attach+deploy
        # go out first and complain the VLAN is already in use.
        self.diff_detach: list = []
        self.have_deploy: dict = {}
        self.want_deploy: dict = {}
        self.diff_deploy: dict = {}
        self.diff_undeploy: dict = {}
        self.diff_delete: dict = {}
        self.diff_input_format: list = []
        self.query: list = []

        self.inventory_data: dict = get_fabric_inventory_details(self.module, self.fabric)

        msg = "self.inventory_data: "
        msg += f"{json.dumps(self.inventory_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.ip_sn: dict = {}
        self.hn_sn: dict = {}
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)
        self.sn_ip: dict = {value: key for (key, value) in self.ip_sn.items()}
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

    def log_list_of_models(self, model_list, by_alias: bool = False) -> None:
        for index, model in enumerate(model_list):
            msg = f"{index}. {json.dumps(model.model_dump(by_alias=by_alias), indent=4, sort_keys=True)}"
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
          - The controller returns None
        - fail_json() if:
          - The return code in the controller response is not 200
          - A vlan_id is not found in the response

        ## Notes

        - TODO: This method is not covered by unit tests.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}"
        self.log.debug(msg)

        vlan_path = self.paths["GET_VLAN"].format(fabric)
        vlan_data = dcnm_send(self.module, "GET", vlan_path)

        msg = "vlan_path: "
        msg += f"{vlan_path}"
        self.log.debug(msg)

        msg = "vlan_data: "
        msg += f"{json.dumps(vlan_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if vlan_data is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. Unable to retrieve endpoint. "
            msg += f"verb GET, path {vlan_path}"
            raise ValueError(msg)

        if vlan_data["RETURN_CODE"] != 200:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}, "
            msg += f"Failure getting autogenerated vlan_id {vlan_data} for fabric {fabric}."
            self.module.fail_json(msg=msg)

        vlan_id = vlan_data.get("DATA")
        if not vlan_id:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}, "
            msg += f"Failure getting autogenerated vlan_id {vlan_data} for fabric {fabric}."
            self.module.fail_json(msg=msg)

        msg = f"Returning vlan_id: {vlan_id} for fabric {fabric}"
        self.log.debug(msg)
        return vlan_id

    def get_next_fabric_vrf_id(self, fabric: str) -> int:
        """
        # Summary

        Return the next available vrf_id for fabric.

        ## Raises

        - fail_json() if:
          - fabric does not exist on the controller
          - Unable to retrieve next available vrf_id for fabric

        ## Notes

        - TODO: This method is not covered by unit tests.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        attempt = 0
        vrf_id: int = -1
        while attempt < 10:
            attempt += 1
            path = self.paths["GET_VRF_ID"].format(fabric)
            vrf_id_obj = dcnm_send(self.module, "GET", path)
            msg = f"vrf_id_obj: {json.dumps(vrf_id_obj, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            generic_response = ControllerResponseGenericV12(**vrf_id_obj)
            missing_fabric, not_ok = self.handle_response(generic_response, "query")

            if missing_fabric or not_ok:
                msg0 = f"{self.class_name}.{method_name}: "
                msg1 = f"{msg0} Fabric {fabric} not present on the controller"
                msg2 = f"{msg0} Unable to generate vrfId under fabric {fabric}"
                self.module.fail_json(msg=msg1 if missing_fabric else msg2)

            if not vrf_id_obj:
                continue
            if not vrf_id_obj["DATA"]:
                continue

            vrf_id = vrf_id_obj["DATA"].get("l3vni")

        if vrf_id == -1:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Unable to retrieve vrf_id for fabric {fabric}"
            self.module.fail_json(msg)

        msg = f"Returning vrf_id: {vrf_id} for fabric {fabric}"
        self.log.debug(msg)
        return int(str(vrf_id))

    def diff_for_attach_deploy(self, want_attach_list: list[dict], have_attach_list: list[dict], replace=False) -> tuple[list, bool]:
        """
        Return attach_list, deploy_vrf

        Where:
        - attach_list is a list of attachment differences
        - deploy_vrf is a boolean
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"replace == {replace}"
        self.log.debug(msg)

        attach_list = []
        deploy_vrf = False

        if not want_attach_list:
            return attach_list, deploy_vrf

        for want_attach in want_attach_list:
            if not have_attach_list:
                # No have_attach, so always attach
                if self.to_bool("isAttached", want_attach):
                    want_attach = self._prepare_attach_for_deploy(want_attach)
                    attach_list.append(want_attach)
                    if self.to_bool("is_deploy", want_attach):
                        deploy_vrf = True
                continue

            found = False
            for have_attach in have_attach_list:
                if want_attach.get("serialNumber") != have_attach.get("serialNumber"):
                    continue

                # Copy freeformConfig from have since the playbook doesn't
                # currently support it.
                want_attach.update({"freeformConfig": have_attach.get("freeformConfig", "")})

                # Copy unsupported instanceValues keys from have to want_attach
                want_inst_values, have_inst_values = {}, {}
                if want_attach.get("instanceValues") and have_attach.get("instanceValues"):
                    want_inst_values = json.loads(want_attach["instanceValues"])
                    have_inst_values = json.loads(have_attach["instanceValues"])
                    # These keys are not currently supported in the playbook,
                    # so copy them from have to want.
                    for key in ["loopbackId", "loopbackIpAddress", "loopbackIpV6Address"]:
                        if key in have_inst_values:
                            want_inst_values[key] = have_inst_values[key]
                    want_attach["instanceValues"] = json.dumps(want_inst_values)

                # Compare extensionValues
                if want_attach.get("extensionValues") and have_attach.get("extensionValues"):
                    if not self._extension_values_match(want_attach, have_attach, replace):
                        continue
                elif want_attach.get("extensionValues") and not have_attach.get("extensionValues"):
                    continue
                elif not want_attach.get("extensionValues") and have_attach.get("extensionValues"):
                    if not replace:
                        found = True
                    continue

                # Compare deployment/attachment status
                if not self._deployment_status_match(want_attach, have_attach):
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
        if "isAttached" in want:
            del want["isAttached"]
        want["deployment"] = True
        return want

    def _extension_values_match(self, want: dict, have: dict, replace: bool) -> bool:
        """
        # Summary

        Compare the extensionValues of two attachment dictionaries to determine if they match.

        - Parses and compares the VRF_LITE_CONN lists in both want and have.
        - If replace is True, also checks that the lengths of the VRF_LITE_CONN lists are equal.
        - Compares each interface (IF_NAME) and their properties.

        ## Parameters

        - want: dict
            The desired attachment dictionary.
        - have: dict
            The current attachment dictionary from the controller.
        - replace: bool
            Whether this is a replace/override operation.

        ## Returns

        - bool: True if the extension values match, False otherwise.
        """
        want_ext = json.loads(want["extensionValues"])
        have_ext = json.loads(have["extensionValues"])
        want_e = json.loads(want_ext["VRF_LITE_CONN"])
        have_e = json.loads(have_ext["VRF_LITE_CONN"])
        if replace and (len(want_e["VRF_LITE_CONN"]) != len(have_e["VRF_LITE_CONN"])):
            return False
        for wlite in want_e["VRF_LITE_CONN"]:
            for hlite in have_e["VRF_LITE_CONN"]:
                if wlite["IF_NAME"] == hlite["IF_NAME"]:
                    if self.property_values_match(wlite, hlite, self.vrf_lite_properties):
                        return True
        return False

    def _deployment_status_match(self, want: dict, have: dict) -> bool:
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
        msg += f"caller: {caller}. "
        self.log.debug(msg)
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

    def update_attach_params_extension_values(self, attach: dict) -> dict:
        """
        # Summary

        Given an attachment object (see example below):

        -   Return a populated extension_values dictionary
            if the attachment object's vrf_lite parameter is
            not null.
        -   Return an empty dictionary if the attachment object's
            vrf_lite parameter is null.

        ## Raises

        Calls fail_json() if the vrf_lite parameter is not null
        and the role of the switch in the attachment object is not
        one of the various border roles.

        ## Example attach object

        - extensionValues content removed for brevity
        - instanceValues content removed for brevity

        ```json
            {
                "deployment": true,
                "export_evpn_rt": "",
                "extensionValues": "{}",
                "fabric": "f1",
                "freeformConfig": "",
                "import_evpn_rt": "",
                "instanceValues": "{}",
                "isAttached": true,
                "is_deploy": true,
                "serialNumber": "FOX2109PGCS",
                "vlan": 500,
                "vrfName": "ansible-vrf-int1",
                "vrf_lite": [
                    {
                        "dot1q": 2,
                        "interface": "Ethernet1/2",
                        "ipv4_addr": "10.33.0.2/30",
                        "ipv6_addr": "2010::10:34:0:7/64",
                        "neighbor_ipv4": "10.33.0.1",
                        "neighbor_ipv6": "2010::10:34:0:3",
                        "peer_vrf": "ansible-vrf-int1"
                    }
                ]
            }
        ```

        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        if not attach["vrf_lite"]:
            msg = "Early return. No vrf_lite extensions to process."
            self.log.debug(msg)
            return {}

        extension_values: dict = {}
        extension_values["VRF_LITE_CONN"] = []
        ms_con: dict = {}
        ms_con["MULTISITE_CONN"] = []
        extension_values["MULTISITE_CONN"] = json.dumps(ms_con)

        # Before applying the vrf_lite config, verify that the
        # switch role begins with border

        role: str = self.inventory_data[attach["ip_address"]].get("switchRole")

        if not re.search(r"\bborder\b", role.lower()):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "VRF LITE attachments are appropriate only for switches "
            msg += "with Border roles e.g. Border Gateway, Border Spine, etc. "
            msg += "The playbook and/or controller settings for switch "
            msg += f"{attach['ip_address']} with role {role} need review."
            self.module.fail_json(msg=msg)

        item: dict
        for item in attach["vrf_lite"]:

            # If the playbook contains vrf lite parameters
            # update the extension values.
            vrf_lite_conn: dict = {}
            for param in self.vrf_lite_properties:
                vrf_lite_conn[param] = ""

            if item["interface"]:
                vrf_lite_conn["IF_NAME"] = item["interface"]
            if item["dot1q"]:
                vrf_lite_conn["DOT1Q_ID"] = str(item["dot1q"])
            if item["ipv4_addr"]:
                vrf_lite_conn["IP_MASK"] = item["ipv4_addr"]
            if item["neighbor_ipv4"]:
                vrf_lite_conn["NEIGHBOR_IP"] = item["neighbor_ipv4"]
            if item["ipv6_addr"]:
                vrf_lite_conn["IPV6_MASK"] = item["ipv6_addr"]
            if item["neighbor_ipv6"]:
                vrf_lite_conn["IPV6_NEIGHBOR"] = item["neighbor_ipv6"]
            if item["peer_vrf"]:
                vrf_lite_conn["PEER_VRF_NAME"] = item["peer_vrf"]

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

    def update_attach_params(self, attach: dict, vrf_name: str, deploy: bool, vlan_id: int) -> dict:
        """
        # Summary

        Turn an attachment object (attach) into a payload for the controller.

        ## Raises

        Calls fail_json() if:

        -   The switch in the attachment object is a spine
        -   If the vrf_lite object is not null, and the switch is not
            a border switch
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        if not attach:
            msg = "Early return. No attachments to process."
            self.log.debug(msg)
            return {}

        # dcnm_get_ip_addr_info converts serial_numbers,
        # hostnames, etc, to ip addresses.
        attach["ip_address"] = dcnm_get_ip_addr_info(self.module, attach["ip_address"], None, None)

        serial = self.ip_to_serial_number(attach["ip_address"])

        msg = "ip_address: "
        msg += f"{attach['ip_address']}, "
        msg += "serial: "
        msg += f"{serial}, "
        msg += "attach: "
        msg += f"{json.dumps(attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not serial:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += f"Fabric {self.fabric} does not contain switch "
            msg += f"{attach['ip_address']}"
            self.module.fail_json(msg=msg)

        role = self.inventory_data[attach["ip_address"]].get("switchRole")

        if role.lower() in ("spine", "super spine"):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "VRF attachments are not appropriate for "
            msg += "switches with Spine or Super Spine roles. "
            msg += "The playbook and/or controller settings for switch "
            msg += f"{attach['ip_address']} with role {role} need review."
            self.module.fail_json(msg=msg)

        extension_values = self.update_attach_params_extension_values(attach)
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
        attach.update({"serialNumber": serial})
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
                "switchRouteTargetImportEvpn": attach["import_evpn_rt"],
                "switchRouteTargetExportEvpn": attach["export_evpn_rt"],
            }
        )
        attach.update({"instanceValues": json.dumps(inst_values).replace(" ", "")})

        if "deploy" in attach:
            del attach["deploy"]
        if "ip_address" in attach:
            del attach["ip_address"]

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
        msg += f"caller: {caller}. "
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
        msg += f"caller: {caller}. "
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

    def update_create_params(self, vrf: dict) -> dict:
        """
        # Summary

        Given a vrf dictionary from a playbook, return a VRF payload suitable
        for sending to the controller.

        Translate playbook keys into keys expected by the controller.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        if not vrf:
            return vrf

        msg = f"vrf: {json.dumps(vrf, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        vrf_upd = {
            "fabric": self.fabric,
            "vrfName": vrf["vrf_name"],
            "vrfTemplate": vrf.get("vrf_template", "Default_VRF_Universal"),
            "vrfExtensionTemplate": vrf.get("vrf_extension_template", "Default_VRF_Extension_Universal"),
            "vrfId": vrf.get("vrf_id", None),  # vrf_id will be auto generated in get_diff_merge()
            "serviceVrfTemplate": vrf.get("service_vrf_template", ""),
            "source": None,
        }

        validated_template_config = VrfTemplateConfigV12.model_validate(vrf)
        template = validated_template_config.model_dump_json(by_alias=True)
        vrf_upd.update({"vrfTemplateConfig": template})

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
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        endpoint = EpVrfGet()
        endpoint.fabric_name = self.fabric

        vrf_objects = dcnm_send(self.module, endpoint.verb.value, endpoint.path)

        if vrf_objects is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to retrieve endpoint. "
            msg += f"verb {endpoint.verb.value} path {endpoint.path}"
            raise ValueError(msg)

        response = ControllerResponseVrfsV12(**vrf_objects)

        msg = f"ControllerResponseVrfsV12: {json.dumps(response.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        missing_fabric, not_ok = self.handle_response(response, "query")

        if missing_fabric or not_ok:
            msg0 = f"caller: {caller}. "
            msg1 = f"{msg0} Fabric {self.fabric} not present on the controller"
            msg2 = f"{msg0} Unable to find vrfs under fabric: {self.fabric}"
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        return response.DATA

    def get_list_of_vrfs_switches_data_item_model(self, attach: dict) -> list[VrfsSwitchesDataItem]:
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
        msg += f"caller: {caller}"
        self.log.debug(msg)

        msg = f"attach: {json.dumps(attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        verb = "GET"
        path = self.paths["GET_VRF_SWITCH"].format(attach["fabric"], attach["vrfName"], attach["serialNumber"])
        msg = f"verb: {verb}, path: {path}"
        self.log.debug(msg)
        lite_objects = dcnm_send(self.module, verb, path)

        if lite_objects is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to retrieve lite_objects."
            raise ValueError(msg)

        try:
            response = ControllerResponseVrfsSwitchesV12(**lite_objects)
        except pydantic.ValidationError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to parse response: {error}"
            raise ValueError(msg) from error

        msg = f"Returning list of VrfSwitchesDataItem. length {len(response.data)}."
        self.log.debug(msg)
        self.log_list_of_models(response.data)

        return response.data

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
        msg += f"caller: {caller}. "
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

    def populate_have_deploy(self, get_vrf_attach_response: dict) -> None:
        """
        Populate self.have_deploy using get_vrf_attach_response.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
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
        if vrfs_to_update:
            have_deploy["vrfNames"] = ",".join(vrfs_to_update)
        self.have_deploy = copy.deepcopy(have_deploy)

        msg = "self.have_deploy: "
        msg += f"{json.dumps(self.have_deploy, indent=4)}"
        self.log.debug(msg)

    def populate_have_attach(self, get_vrf_attach_response: dict) -> None:
        """
        Populate self.have_attach using get_vrf_attach_response.

        Mutates items in lanAttachList per the examples below.  Specifically:

        -  Generates deployment from vrf_attach.lanAttachList.isLanAttached
        -  Generates extensionValues from lite_objects (see _update_vrf_lite_extension)
        -  Generates fabric from self.fabric
        -  Generates freeformConfig from SwitchDetails.freeform_config (if exists) or from "" (see _update_vrf_lite_extension)
        -  Generates instanceValues from vrf_attach.lanAttachList.instanceValues
        -  Generates isAttached from vrf_attach.lanAttachList.lanAttachState
        -  Generates is_deploy from vrf_attach.lanAttachList.isLanAttached and vrf_attach.lanAttachList.lanAttachState
        -  Generates serialNumber from vrf_attach.lanAttachList.switchSerialNo
        -  Generates vlan from vrf_attach.lanAttachList.vlanId
        -  Generates vrfName from vrf_attach.lanAttachList.vrfName

        ## PRE Mutation Example

        ```json
            {
                "fabricName": "test-fabric",
                "ipAddress": "10.10.10.227",
                "isLanAttached": true,
                "lanAttachState": "DEPLOYED",
                "switchName": "n9kv_leaf4",
                "switchRole": "border",
                "switchSerialNo": "XYZKSJHSMK4",
                "vlanId": "202",
                "vrfId": "9008011",
                "vrfName": "test_vrf_1"
            }
        ```

        ## POST Mutation Example

        ```json
            {
                "deployment": true,
                "extensionValues": "{contents removed for brevity}",
                "fabric": "test_fabric",
                "freeformConfig": "",
                "instanceValues": null,
                "isAttached": true,
                "is_deploy": true,
                "serialNumber": "XYZKSJHSMK4",
                "vlan": "202",
                "vrfName": "test_vrf_1"
            }
        ```
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        have_attach = copy.deepcopy(get_vrf_attach_response.get("DATA", []))

        msg = "have_attach.PRE_UPDATE: "
        msg += f"{json.dumps(have_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        for vrf_attach in have_attach:
            if not vrf_attach.get("lanAttachList"):
                continue
            new_attach_list = []
            for attach in vrf_attach["lanAttachList"]:
                if not isinstance(attach, dict):
                    msg = f"{self.class_name}.{method_name}: {caller}: attach is not a dict."
                    self.module.fail_json(msg=msg)

                # Prepare new attachment dict
                attach_state = attach.get("lanAttachState") != "NA"
                deploy = attach.get("isLanAttached")
                deployed = not (deploy and attach.get("lanAttachState") in ("OUT-OF-SYNC", "PENDING"))
                switch_serial_number = attach.get("switchSerialNo")
                vlan = attach.get("vlanId")
                inst_values = attach.get("instanceValues", None)
                vrf_name = attach.get("vrfName", "")

                # Build new attach dict with required keys
                new_attach = {
                    "deployment": deploy,
                    "extensionValues": "",
                    "fabric": self.fabric,
                    "instanceValues": inst_values,
                    "isAttached": attach_state,
                    "is_deploy": deployed,
                    "serialNumber": switch_serial_number,
                    "vlan": vlan,
                    "vrfName": vrf_name,
                }

                new_attach = self._update_vrf_lite_extension(new_attach)

                new_attach_list.append(new_attach)
            vrf_attach["lanAttachList"] = new_attach_list

        msg = "have_attach.POST_UPDATE: "
        msg += f"{json.dumps(have_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.have_attach = copy.deepcopy(have_attach)

    def _update_vrf_lite_extension(self, attach: dict) -> dict:
        """
        # Summary

        - Return updated attach dict with VRF Lite extension values if present.
        - Update freeformConfig, if present, else set to an empty string.

        ## Raises

        - None
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        msg = "attach: "
        msg += f"{json.dumps(attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        lite_objects = self.get_list_of_vrfs_switches_data_item_model(attach)
        if not lite_objects:
            msg = "No vrf_lite_objects found. Update freeformConfig and return."
            self.log.debug(msg)
            attach["freeformConfig"] = ""
            return copy.deepcopy(attach)

        msg = f"lite_objects: length {len(lite_objects)}."
        self.log.debug(msg)
        self.log_list_of_models(lite_objects)

        for sdl in lite_objects:
            for epv in sdl.switch_details_list:
                if not epv.extension_values:
                    attach["freeformConfig"] = ""
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
                attach["extensionValues"] = json.dumps(extension_values).replace(" ", "")
                attach["freeformConfig"] = epv.freeform_config or ""
        return copy.deepcopy(attach)

    def populate_have_attach_model(self, vrf_attach_models: list[VrfsAttachmentsDataItem]) -> None:
        """
        Populate self.have_attach using get_vrf_attach_response.
        """
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
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

            # vrf_attach_model.lan_attach_list = new_attach_list
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
        self.have_attach_model = updated_vrf_attach_models
        msg = f"self.have_attach.POST_UPDATE: length: {len(self.have_attach)}."
        self.log.debug(msg)
        msg = f"{json.dumps(self.have_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

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
        msg += f"caller: {caller}. "
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
        -   self.have_attach, see populate_have_attach()
        -   self.have_deploy, see populate_have_deploy()
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        vrf_object_models = self.get_controller_vrf_object_models()

        msg = f"vrf_object_models: length {len(vrf_object_models)}."
        self.log.debug(msg)
        self.log_list_of_models(vrf_object_models)

        if not vrf_object_models:
            return

        self.populate_have_create(vrf_object_models)

        current_vrfs_set = {vrf.vrfName for vrf in vrf_object_models}
        get_vrf_attach_response = get_endpoint_with_long_query_string(
            module=self.module,
            fabric_name=self.fabric,
            path=self.paths["GET_VRF_ATTACH"],
            query_string_items=",".join(current_vrfs_set),
            caller=f"{self.class_name}.{method_name}",
        )

        if get_vrf_attach_response is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}: unable to set get_vrf_attach_response."
            raise ValueError(msg)

        get_vrf_attach_response_model = ControllerResponseVrfsAttachmentsV12(**get_vrf_attach_response)

        msg = "get_vrf_attach_response_model: "
        msg += f"{json.dumps(get_vrf_attach_response_model.model_dump(by_alias=False), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not get_vrf_attach_response_model.data:
            return

        self.populate_have_deploy(get_vrf_attach_response)
        # self.populate_have_attach(get_vrf_attach_response)
        self.populate_have_attach_model(get_vrf_attach_response_model.data)

        msg = "self.have_attach: "
        msg += f"{json.dumps(self.have_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def get_want_attach(self) -> None:
        """
        Populate self.want_attach from self.validated.
        """
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        want_attach: list[dict[str, Any]] = []

        for vrf in self.validated:
            vrf_name: str = vrf.get("vrf_name")
            vrf_attach: dict[Any, Any] = {}
            vrfs: list[dict[Any, Any]] = []

            vrf_deploy: bool = vrf.get("deploy", True)
            vlan_id: int = vrf.get("vlan_id", 0)

            if not vrf.get("attach"):
                msg = f"No attachments for vrf {vrf_name}. Skipping."
                self.log.debug(msg)
                continue
            for attach in vrf["attach"]:
                deploy = vrf_deploy
                vrfs.append(self.update_attach_params(attach, vrf_name, deploy, vlan_id))

            if vrfs:
                vrf_attach.update({"vrfName": vrf_name})
                vrf_attach.update({"lanAttachList": vrfs})
                want_attach.append(vrf_attach)

        self.want_attach = copy.deepcopy(want_attach)
        msg = "self.want_attach: "
        msg += f"{json.dumps(self.want_attach, indent=4)}"
        self.log.debug(msg)

    def get_want_create(self) -> None:
        """
        Populate self.want_create from self.validated.
        """
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        want_create: list[dict[str, Any]] = []

        for vrf in self.validated:
            want_create.append(self.update_create_params(vrf=vrf))

        self.want_create = copy.deepcopy(want_create)
        msg = "self.want_create: "
        msg += f"{json.dumps(self.want_create, indent=4)}"
        self.log.debug(msg)

    def get_want_deploy(self) -> None:
        """
        Populate self.want_deploy from self.validated.
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        want_deploy: dict[str, Any] = {}
        all_vrfs: set = set()

        for vrf in self.validated:
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
        - self.want_create, see get_want_create()
        - self.want_deploy, see get_want_deploy()
        """
        self.get_want_create()
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
        msg += f"caller: {caller}."
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

    def get_items_to_detach_model(self, attach_list: list[HaveLanAttachItem]) -> DetachList:
        """
        # Summary

        Given a list of HaveLanAttachItem objects, return a list of
        DetachList models.

        This is done by checking if the isAttached field in each
        HaveLanAttachItem is True.

        If HaveLanAttachItem.isAttached field is True, it indicates that the
        attachment is attached to a VRF and needs to be detached.  In this case,
        mutate the HaveLanAttachItem to a LanDetachItem which will:

        - Remove the isAttached field
        - Set the deployment field to False

        The LanDetachItem is added to DetachList.lan_attach_list.

        Finally, return the DetachList model.
        """
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)
        lan_detach_items: list[LanDetachItem] = []

        msg = f"attach_list: length {len(attach_list)}."
        self.log.debug(msg)
        self.log_list_of_models(attach_list)

        for have_lan_attach_item in attach_list:
            if not have_lan_attach_item.is_attached:
                continue
            msg = "have_lan_attach_item: "
            msg += f"{json.dumps(have_lan_attach_item.model_dump(by_alias=False), indent=4, sort_keys=True)}"
            self.log.debug(msg)

            msg = "Mutating HaveLanAttachItem to LanDetachItem."
            self.log.debug(msg)
            lan_detach_item = LanDetachItem(
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
            msg = "Mutating HaveLanAttachItem to LanDetachItem. DONE."
            self.log.debug(msg)

            vrf_name = have_lan_attach_item.vrf_name
            lan_detach_items.append(lan_detach_item)

        msg = "Creating DetachList model."
        self.log.debug(msg)

        vrf_name = lan_detach_items[0].vrf_name if lan_detach_items else ""
        if not vrf_name:
            msg = "vrf_name not found in lan_detach_items. Cannot create DetachList model."
            self.module.fail_json(msg=msg)
        if len(set(item.vrf_name for item in lan_detach_items)) > 1:
            msg = "Multiple VRF names found in lan_detach_items. Cannot create DetachList model."
            self.module.fail_json(msg=msg)

        msg = f"lan_detach_items for DetachList: length {len(lan_detach_items)}."
        self.log.debug(msg)
        self.log_list_of_models(lan_detach_items)

        detach_list_model = DetachList(
            lanAttachList=lan_detach_items,
            vrfName=vrf_name,
        )

        msg = "Creating DetachList model. DONE."
        self.log.debug(msg)

        msg = f"Returning detach_list_model: length(lan_attach_list): {len(detach_list_model.lan_attach_list)}."
        self.log.debug(msg)
        msg = f"{json.dumps(detach_list_model.model_dump(by_alias=False), indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return detach_list_model

    def get_diff_delete(self) -> None:
        """
        # Summary

        Using self.have_create, and self.have_attach, update
        the following:

        - diff_detach: a list of attachment objects to detach
        - diff_undeploy: a dictionary of vrf names to undeploy
        - diff_delete: a dictionary of vrf names to delete
        """
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        self.model_enabled = True

        if self.config:
            self._get_diff_delete_with_config()
        else:
            self._get_diff_delete_without_config()

        msg = "self.diff_detach: "
        if not self.model_enabled:
            msg += f"{json.dumps(self.diff_detach, indent=4)}"
            self.log.debug(msg)
        else:
            self.log_list_of_models(self.diff_detach, by_alias=False)

        msg = "self.diff_undeploy: "
        msg += f"{json.dumps(self.diff_undeploy, indent=4)}"
        self.log.debug(msg)
        msg = "self.diff_delete: "
        msg += f"{json.dumps(self.diff_delete, indent=4)}"
        self.log.debug(msg)

    def _get_diff_delete_with_config(self) -> None:
        """
        Handle diff_delete logic when self.config is not empty.

        In this case, we detach, undeploy, and delete the VRFs
        specified in self.config.
        """
        if self.model_enabled:
            self._get_diff_delete_with_config_model()
            return
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        diff_detach: list[dict] = []
        diff_undeploy: dict = {}
        diff_delete: dict = {}
        all_vrfs = set()

        msg = "self.have_attach: "
        msg += f"{json.dumps(self.have_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        for want_c in self.want_create:
            if self.find_dict_in_list_by_key_value(search=self.have_create, key="vrfName", value=want_c["vrfName"]) == {}:
                continue

            diff_delete.update({want_c["vrfName"]: "DEPLOYED"})

            have_a = self.find_dict_in_list_by_key_value(search=self.have_attach, key="vrfName", value=want_c["vrfName"])
            if not have_a:
                continue

            detach_items = self.get_items_to_detach(have_a["lanAttachList"])
            if detach_items:
                have_a.update({"lanAttachList": detach_items})
                diff_detach.append(have_a)
                all_vrfs.add(have_a["vrfName"])
        if len(all_vrfs) != 0:
            diff_undeploy.update({"vrfNames": ",".join(all_vrfs)})

        self.diff_detach = copy.deepcopy(diff_detach)
        self.diff_undeploy = copy.deepcopy(diff_undeploy)
        self.diff_delete = copy.deepcopy(diff_delete)

    def _get_diff_delete_without_config(self) -> None:
        """
        Handle diff_delete logic when self.config is empty or None.

        In this case, we detach, undeploy, and delete all VRFs.
        """
        if self.model_enabled:
            self._get_diff_delete_without_config_model()
            return
        diff_detach: list[dict] = []
        diff_undeploy: dict = {}
        diff_delete: dict = {}
        all_vrfs = set()

        for have_a in self.have_attach:
            detach_items = self.get_items_to_detach(have_a["lanAttachList"])
            if detach_items:
                have_a.update({"lanAttachList": detach_items})
                diff_detach.append(have_a)
                all_vrfs.add(have_a.get("vrfName"))

            diff_delete.update({have_a["vrfName"]: "DEPLOYED"})
        if len(all_vrfs) != 0:
            diff_undeploy.update({"vrfNames": ",".join(all_vrfs)})

        self.diff_detach = copy.deepcopy(diff_detach)
        self.diff_undeploy = copy.deepcopy(diff_undeploy)
        self.diff_delete = copy.deepcopy(diff_delete)

    def _get_diff_delete_with_config_model(self) -> None:
        """
        Handle diff_delete logic when self.config is not empty.

        In this case, we detach, undeploy, and delete the VRFs
        specified in self.config.
        """
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        diff_detach: list[DetachList] = []
        diff_undeploy: dict = {}
        diff_delete: dict = {}
        all_vrfs = set()

        msg = "self.have_attach_model: "
        self.log.debug(msg)
        self.log_list_of_models(self.have_attach_model, by_alias=True)

        for want_c in self.want_create:
            if self.find_dict_in_list_by_key_value(search=self.have_create, key="vrfName", value=want_c["vrfName"]) == {}:
                continue

            diff_delete.update({want_c["vrfName"]: "DEPLOYED"})

            have_attach_model: HaveAttachPostMutate = self.find_model_in_list_by_key_value(
                search=self.have_attach_model, key="vrf_name", value=want_c["vrfName"]
            )
            if not have_attach_model:
                msg = f"ZZZ: have_attach_model not found for vrfName: {want_c['vrfName']}. "
                msg += "Continuing."
                self.log.debug(msg)
                continue

            msg = "ZZZ: have_attach_model: "
            msg += f"{json.dumps(have_attach_model.model_dump(by_alias=False), indent=4, sort_keys=True)}"
            self.log.debug(msg)

            detach_list_model: DetachList = self.get_items_to_detach_model(have_attach_model.lan_attach_list)
            msg = f"ZZZ: detach_list_model: length(lan_attach_list): {len(detach_list_model.lan_attach_list)}."
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
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        diff_detach: list[DetachList] = []
        diff_undeploy: dict = {}
        diff_delete: dict = {}
        all_vrfs = set()

        msg = "self.have_attach_model: "
        self.log.debug(msg)
        self.log_list_of_models(self.have_attach_model, by_alias=True)

        have_attach_model: HaveAttachPostMutate
        for have_attach_model in self.have_attach_model:
            msg = f"ZZZ: type(have_attach_model): {type(have_attach_model)}"
            self.log.debug(msg)
            diff_delete.update({have_attach_model.vrf_name: "DEPLOYED"})
            detach_list_model = self.get_items_to_detach_model(have_attach_model.lan_attach_list)
            if detach_list_model.lan_attach_list:
                diff_detach.append(detach_list_model)
                all_vrfs.add(detach_list_model.vrf_name)

        if len(all_vrfs) != 0:
            diff_undeploy.update({"vrfNames": ",".join(all_vrfs)})

        self.diff_detach = diff_detach
        self.diff_undeploy = copy.deepcopy(diff_undeploy)
        self.diff_delete = copy.deepcopy(diff_delete)

    def get_diff_override(self):
        """
        # Summary

        For override state, we delete existing attachments and vrfs
        (self.have_attach) that are not in the want list.

        Using self.have_attach and self.want_create, update
        the following:

        - diff_detach: a list of attachment objects to detach
        - diff_undeploy: a dictionary of vrf names to undeploy
        - diff_delete: a dictionary keyed on vrf name indicating
          the deployment status of the vrf e.g. "DEPLOYED"
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        all_vrfs = set()
        diff_delete = {}

        self.get_diff_replace()

        diff_detach = copy.deepcopy(self.diff_detach)
        diff_undeploy = copy.deepcopy(self.diff_undeploy)

        for have_a in self.have_attach:
            found = self.find_dict_in_list_by_key_value(search=self.want_create, key="vrfName", value=have_a["vrfName"])

            if not found:
                detach_list = self.get_items_to_detach(have_a["lanAttachList"])

                if detach_list:
                    have_a.update({"lanAttachList": detach_list})
                    diff_detach.append(have_a)
                    all_vrfs.add(have_a["vrfName"])

                diff_delete.update({have_a["vrfName"]: "DEPLOYED"})

        if len(all_vrfs) != 0:
            diff_undeploy.update({"vrfNames": ",".join(all_vrfs)})

        self.diff_delete = copy.deepcopy(diff_delete)
        self.diff_detach = copy.deepcopy(diff_detach)
        self.diff_undeploy = copy.deepcopy(diff_undeploy)

        msg = "self.diff_delete: "
        msg += f"{json.dumps(self.diff_delete, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_detach: "
        msg += f"{json.dumps(self.diff_detach, indent=4)}"
        self.log.debug(msg)

        msg = "self.diff_undeploy: "
        msg += f"{json.dumps(self.diff_undeploy, indent=4)}"
        self.log.debug(msg)

    def get_diff_replace(self) -> None:
        """
        # Summary

        For replace state, update the attachment objects in self.have_attach
        that are not in the want list.

        - diff_attach: a list of attachment objects to attach
        - diff_deploy: a dictionary of vrf names to deploy
        - diff_delete: a dictionary of vrf names to delete
        """
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        all_vrfs: set = set()
        self.get_diff_merge(replace=True)
        diff_attach = self.diff_attach
        diff_deploy = self.diff_deploy

        for have_attach in self.have_attach:
            msg = f"ZZZ: type(have_attach): {type(have_attach)}"
            self.log.debug(msg)
            replace_vrf_list = []

            # Find matching want_attach by vrfName
            want_attach = next((w for w in self.want_attach if w.get("vrfName") == have_attach.get("vrfName")), None)

            if want_attach:
                have_lan_attach_list = have_attach.get("lanAttachList", [])
                want_lan_attach_list = want_attach.get("lanAttachList", [])

                for have_lan_attach in have_lan_attach_list:
                    if have_lan_attach.get("isAttached") is False:
                        continue
                    # Check if this have_lan_attach exists in want_lan_attach_list by serialNumber
                    if not any(have_lan_attach.get("serialNumber") == want_lan_attach.get("serialNumber") for want_lan_attach in want_lan_attach_list):
                        if "isAttached" in have_lan_attach:
                            del have_lan_attach["isAttached"]
                        have_lan_attach["deployment"] = False
                        replace_vrf_list.append(have_lan_attach)
            else:
                # If have_attach is not in want_attach but is in want_create, detach all attached
                found = self.find_dict_in_list_by_key_value(search=self.want_create, key="vrfName", value=have_attach.get("vrfName"))
                if found:
                    for lan_attach in have_attach.get("lanAttachList", []):
                        if lan_attach.get("isAttached"):
                            del lan_attach["isAttached"]
                            lan_attach["deployment"] = False
                            replace_vrf_list.append(lan_attach)

            if replace_vrf_list:
                # Find or create the diff_attach entry for this VRF
                d_attach = next((d for d in diff_attach if d.get("vrfName") == have_attach.get("vrfName")), None)
                if d_attach:
                    d_attach["lanAttachList"].extend(replace_vrf_list)
                else:
                    attachment = {
                        "vrfName": have_attach["vrfName"],
                        "lanAttachList": replace_vrf_list,
                    }
                    diff_attach.append(attachment)
                all_vrfs.add(have_attach["vrfName"])

        if not all_vrfs:
            self.diff_attach = copy.deepcopy(diff_attach)
            self.diff_deploy = copy.deepcopy(diff_deploy)
            return

        for vrf in self.diff_deploy.get("vrfNames", "").split(","):
            all_vrfs.add(vrf)
        diff_deploy.update({"vrfNames": ",".join(all_vrfs)})

        self.diff_attach = copy.deepcopy(diff_attach)
        self.diff_deploy = copy.deepcopy(diff_deploy)

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
        msg += f"caller: {caller}. "
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

        ## params

        - replace: Passed unaltered to self.diff_for_attach_deploy()
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += f"replace == {replace}"
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

        msg = "self.have_attach: "
        msg += f"type: {type(self.have_attach)}"
        self.log.debug(msg)
        msg = f"value: {json.dumps(self.have_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        for want_attach in self.want_attach:
            msg = f"type(want_attach): {type(want_attach)}, "
            msg += f"want_attach: {json.dumps(want_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            # Check user intent for this VRF and don't add it to the all_vrfs
            # set if the user has not requested a deploy.
            want_config = self.find_dict_in_list_by_key_value(search=self.config, key="vrf_name", value=want_attach["vrfName"])
            vrf_to_deploy: str = ""
            attach_found = False
            for have_attach in self.have_attach:
                msg = f"type(have_attach): {type(have_attach)}, "
                msg += f"have_attach: {json.dumps(have_attach, indent=4, sort_keys=True)}"
                self.log.debug(msg)

                msg = f"want_attach[vrfName]: {want_attach.get('vrfName')}"
                self.log.debug(msg)
                msg = f"have_attach[vrfName]: {have_attach.get('vrfName')}"
                self.log.debug(msg)
                msg = f"want_config[deploy]: {want_config.get('deploy')}"
                self.log.debug(msg)

                if want_attach.get("vrfName") != have_attach.get("vrfName"):
                    continue
                attach_found = True
                diff, deploy_vrf_bool = self.diff_for_attach_deploy(
                    want_attach_list=want_attach["lanAttachList"],
                    have_attach_list=have_attach["lanAttachList"],
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
                    if (want_config.get("deploy") is True) and (deploy_vrf_bool is True):
                        vrf_to_deploy = want_attach.get("vrfName")
                else:
                    if want_config.get("deploy") is True and (deploy_vrf_bool or self.conf_changed.get(want_attach.get("vrfName"), False)):
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
        msg += f"caller: {caller}. "
        msg += f"replace == {replace}"
        self.log.debug(msg)

        self.diff_merge_create(replace)
        self.diff_merge_attach(replace)

    def format_diff_attach(self, diff_attach: list, diff_deploy: list) -> list:
        """
        Populate the diff list with remaining attachment entries.
        """
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        msg = "ZZZ: diff_attach: "
        msg += f"{json.dumps(diff_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        msg = "ZZZ: diff_deploy: "
        msg += f"{json.dumps(diff_deploy, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        if not diff_attach:
            msg = "ZZZ: No diff_attach entries to process. Returning empty list."
            self.log.debug(msg)
            return []
        diff = []
        for vrf in diff_attach:
            # TODO: arobel: using models, we get a KeyError for lan_attach[vlan], so we try lan_attach[vlanId] too.
            # TODO: arobel: remove this once we've fixed the model to dump what is expected here.
            new_attach_list = [
                {
                    "ip_address": next((k for k, v in self.ip_sn.items() if v == lan_attach["serialNumber"]), None),
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

        msg = "ZZZ: returning diff: "
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

            json_to_dict = json.loads(found_create["vrfTemplateConfig"])
            try:
                vrf_controller_to_playbook = VrfControllerToPlaybookV12Model(**json_to_dict)
                found_create.update(vrf_controller_to_playbook.model_dump(by_alias=False))
            except pydantic.ValidationError as error:
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
                    "ip_address": next((k for k, v in self.ip_sn.items() if v == lan_attach["serialNumber"]), None),
                    "vlan_id": lan_attach.get("vlan") or lan_attach.get("vlanId"),
                    "deploy": lan_attach["deployment"],
                }
                for lan_attach in found_attach["lanAttachList"]
            ]
            diff.append(found_create)
            diff_attach.remove(found_attach)
        return diff

    def format_diff_deploy(self, diff_deploy) -> list:
        """
        # Summary

        Populate the diff list with deploy/undeploy entries.

        ## Raises

        - None
        """
        diff = []
        for vrf in diff_deploy:
            new_deploy_dict = {"vrf_name": vrf}
            diff.append(copy.deepcopy(new_deploy_dict))
        return diff

    def format_diff(self) -> None:
        """
        # Summary

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
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        if self.model_enabled:
            self.format_diff_model()
            return

        diff_create = copy.deepcopy(self.diff_create)
        diff_create_quick = copy.deepcopy(self.diff_create_quick)
        diff_create_update = copy.deepcopy(self.diff_create_update)
        diff_attach = copy.deepcopy(self.diff_attach)
        msg = "ZZZ: diff_attach: "
        msg += f"{json.dumps(diff_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        diff_detach = copy.deepcopy(self.diff_detach)
        msg = "ZZZ: diff_detach: "
        msg += f"{json.dumps(self.diff_detach, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        diff_deploy = self.diff_deploy["vrfNames"].split(",") if self.diff_deploy else []
        diff_undeploy = self.diff_undeploy["vrfNames"].split(",") if self.diff_undeploy else []

        diff_create.extend(diff_create_quick)
        diff_create.extend(diff_create_update)
        diff_attach.extend(diff_detach)
        diff_deploy.extend(diff_undeploy)

        diff = []
        diff.extend(self.format_diff_create(diff_create, diff_attach, diff_deploy))
        diff.extend(self.format_diff_attach(diff_attach, diff_deploy))
        diff.extend(self.format_diff_deploy(diff_deploy))

        self.diff_input_format = copy.deepcopy(diff)
        msg = "self.diff_input_format: "
        msg += f"{json.dumps(self.diff_input_format, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def format_diff_model(self) -> None:
        """
        # Summary

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
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        diff_create = copy.deepcopy(self.diff_create)
        diff_create_quick = copy.deepcopy(self.diff_create_quick)
        diff_create_update = copy.deepcopy(self.diff_create_update)
        diff_attach = copy.deepcopy(self.diff_attach)
        msg = "ZZZ: diff_attach: "
        msg += f"{json.dumps(diff_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        diff_detach = copy.deepcopy(self.diff_detach)
        msg = "ZZZ: diff_detach: "
        self.log.debug(msg)
        self.log_list_of_models(diff_detach, by_alias=False)
        diff_deploy = self.diff_deploy["vrfNames"].split(",") if self.diff_deploy else []
        diff_undeploy = self.diff_undeploy["vrfNames"].split(",") if self.diff_undeploy else []

        diff_create.extend(diff_create_quick)
        diff_create.extend(diff_create_update)
        diff_attach.extend([model.model_dump(by_alias=True) for model in diff_detach])
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
        msg += f"caller: {caller}. "
        msg += "self.diff_create_update: "
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
        if self.model_enabled:
            self.push_diff_detach_model(is_rollback)
            return

        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += "self.diff_detach: "
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
        msg += f"caller: {caller}. "
        msg += "self.diff_detach: "
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
        msg += f"caller: {caller}. "
        msg += "self.diff_undeploy: "
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
        msg += f"caller: {caller}. "
        msg += "self.diff_delete: "
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

    def get_controller_vrf_attachment_models(self, vrf_name: str) -> list[VrfsAttachmentsDataItem]:
        """
        ## Summary

        Given a vrf_name, query the controller for the attachment list
        for that vrf and return a list of VrfsAttachmentsDataItem
        models.

        ## Raises

        - ValueError: If the response from the controller is None.
        - ValueError: If the response from the controller is not valid.
        - fail_json: If the fabric does not exist on the controller.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        path_get_vrf_attach = self.paths["GET_VRF_ATTACH"].format(self.fabric, vrf_name)
        get_vrf_attach_response = dcnm_send(self.module, "GET", path_get_vrf_attach)

        msg = f"path_get_vrf_attach: {path_get_vrf_attach}"
        self.log.debug(msg)
        msg = "get_vrf_attach_response: "
        msg += f"{json.dumps(get_vrf_attach_response, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if get_vrf_attach_response is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{caller}: Unable to retrieve endpoint. "
            msg += f"verb GET, path {path_get_vrf_attach}"
            raise ValueError(msg)

        response = ControllerResponseVrfsAttachmentsV12(**get_vrf_attach_response)
        msg = "ControllerResponseVrfsAttachmentsV12: "
        msg += f"{json.dumps(response.model_dump(by_alias=True), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        generic_response = ControllerResponseGenericV12(**get_vrf_attach_response)
        missing_fabric, not_ok = self.handle_response(generic_response, "query")

        if missing_fabric or not_ok:
            msg0 = f"caller: {caller}. "
            msg1 = f"{msg0} Fabric {self.fabric} not present on DCNM"
            msg2 = f"{msg0} Unable to find attachments for "
            msg2 += f"vrf {vrf_name} under fabric {self.fabric}"
            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
        return response.data

    def get_diff_query_for_vrfs_in_want(self, vrf_object_models: list[VrfObjectV12]) -> list[dict]:
        """
        Query the controller for the current state of the VRFs in the fabric
        that are present in self.want_create.

        ## Raises

        - ValueError: If any controller response is not valid.
        """
        caller = inspect.stack()[1][3]
        query: list[dict] = []

        if not self.want_create:
            msg = f"caller: {caller}. "
            msg += "Early return. No VRFs to process."
            self.log.debug(msg)
            return query

        if not vrf_object_models:
            msg = f"caller: {caller}. "
            msg += f"Early return. No VRFs exist in fabric {self.fabric}."
            self.log.debug(msg)
            return query

        # Lookup controller VRFs by name, used in for loop below.
        vrf_lookup = {vrf.vrfName: vrf for vrf in vrf_object_models}

        for want_c in self.want_create:
            vrf = vrf_lookup.get(want_c["vrfName"])
            if not vrf:
                continue

            item = {"parent": vrf.model_dump(by_alias=True), "attach": []}
            vrf_attachment_models = self.get_controller_vrf_attachment_models(vrf.vrfName)

            msg = f"caller: {caller}. vrf_attachment_models: length {len(vrf_attachment_models)}."
            self.log.debug(msg)
            self.log_list_of_models(vrf_attachment_models)

            for vrf_attachment_model in vrf_attachment_models:
                if want_c["vrfName"] != vrf_attachment_model.vrf_name or not vrf_attachment_model.lan_attach_list:
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
                        item["attach"].append(lite_objects[0].model_dump(by_alias=True))
            query.append(item)

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
        query: list[dict] = []

        if not vrf_object_models:
            msg = f"caller: {caller}. "
            msg += f"Early return. No VRFs exist in fabric {self.fabric}."
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
        msg += f"caller: {caller}. "
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
        msg += f"caller: {caller}."
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
        msg += f"caller: {caller}. "
        msg += f"vrf_model: {json.dumps(vrf_model.model_dump(by_alias=True), indent=4, sort_keys=True)}"
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
        msg += f"caller: {caller}. "
        msg += "self.diff_create: "
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
        is_border = False
        for ip_address, serial in self.ip_sn.items():
            if serial != serial_number:
                continue
            role = self.inventory_data[ip_address].get("switchRole")
            re_result = re.search(r"\bborder\b", role.lower())
            if re_result:
                is_border = True
        return is_border

    def get_extension_values_from_lite_objects(self, lite: list[ExtensionPrototypeValue]) -> list[VrfLiteConnProtoItem]:
        """
        # Summary

        Given a list of lite objects (ExtensionPrototypeValue), return:

        -   A list containing the extensionValues (VrfLiteConnProtoItem),
            if any, from these lite objects.
        -   An empty list, if the lite objects have no extensionValues

        ## Raises

        None
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        extension_values_list: list[VrfLiteConnProtoItem] = []
        for item in lite:
            if item.extension_type != "VRF_LITE":
                continue
            extension_values_list.append(item.extension_values)

        msg = f"Returning extension_values_list (list[VrfLiteConnProtoItem]). length: {len(extension_values_list)}."
        self.log.debug(msg)
        self.log_list_of_models(extension_values_list)

        return extension_values_list

    def update_vrf_attach_vrf_lite_extensions(self, vrf_attach, lite: list[ExtensionPrototypeValue]) -> dict:
        """
        # Summary

        ## params

        -   vrf_attach
            A vrf_attach object containing a vrf_lite extension
            to update
        -   lite: A list of current vrf_lite extension models
            (ExtensionPrototypeValue) from the switch

        ## Description

        1.  Merge the values from the vrf_attach object into a matching
            vrf_lite extension object (if any) from the switch.
        2.  Update the vrf_attach object with the merged result.
        3.  Return the updated vrf_attach object.

        If no matching ExtensionPrototypeValue model is found,
        return the unmodified vrf_attach object.

        "matching" in this case means:

        1.  The extensionType of the switch's extension object is VRF_LITE
        2.  The IF_NAME in the extensionValues of the extension object
            matches the interface in vrf_attach.vrf_lite.
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        msg += "vrf_attach: "
        msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        serial_number = vrf_attach.get("serialNumber")

        msg = f"serial_number: {serial_number}"
        self.log.debug(msg)

        if vrf_attach.get("vrf_lite") is None:
            if "vrf_lite" in vrf_attach:
                del vrf_attach["vrf_lite"]
            vrf_attach["extensionValues"] = ""
            msg = f"serial_number: {serial_number}, "
            msg += "vrf_attach does not contain a vrf_lite configuration. "
            msg += "Returning it with empty extensionValues. "
            msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            return copy.deepcopy(vrf_attach)

        msg = f"serial_number: {serial_number}, "
        msg += f"Received list of lite_objects (list[ExtensionPrototypeValue]). length: {len(lite)}."
        self.log.debug(msg)
        self.log_list_of_models(lite)

        ext_values = self.get_extension_values_from_lite_objects(lite)
        if ext_values is None:
            ip_address = self.serial_number_to_ip(serial_number)
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "No VRF LITE capable interfaces found on "
            msg += "this switch. "
            msg += f"ip: {ip_address}, "
            msg += f"serial_number: {serial_number}"
            self.log.debug(msg)
            self.module.fail_json(msg=msg)

        matches: dict = {}
        user_vrf_lite_interfaces = []
        switch_vrf_lite_interfaces = []
        for item in vrf_attach.get("vrf_lite"):
            item_interface = item.get("interface")
            user_vrf_lite_interfaces.append(item_interface)
            for ext_value in ext_values:
                ext_value_interface = ext_value.if_name
                switch_vrf_lite_interfaces.append(ext_value_interface)
                msg = f"item_interface: {item_interface}, "
                msg += f"ext_value_interface: {ext_value_interface}"
                self.log.debug(msg)
                if item_interface != ext_value_interface:
                    continue
                msg = "Found item: "
                msg += f"item[interface] {item_interface}, == "
                msg += f"ext_values.if_name {ext_value_interface}."
                self.log.debug(msg)
                msg = f"{json.dumps(item, indent=4, sort_keys=True)}"
                self.log.debug(msg)
                matches[item_interface] = {"user": item, "switch": ext_value}
        if not matches:
            ip_address = self.serial_number_to_ip(serial_number)
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "No matching interfaces with vrf_lite extensions "
            msg += f"found on switch {ip_address} ({serial_number}). "
            msg += "playbook vrf_lite_interfaces: "
            msg += f"{','.join(sorted(user_vrf_lite_interfaces))}. "
            msg += "switch vrf_lite_interfaces: "
            msg += f"{','.join(sorted(switch_vrf_lite_interfaces))}."
            self.log.debug(msg)
            self.module.fail_json(msg)

        msg = "Matching extension object(s) found on the switch. "
        msg += "Proceeding to convert playbook vrf_lite configuration "
        msg += "to payload format. "

        extension_values = {"VRF_LITE_CONN": [], "MULTISITE_CONN": []}

        for interface, item in matches.items():
            user = item["user"]
            switch = item["switch"]
            msg = f"interface: {interface}: "
            self.log.debug(msg)
            msg = "item.user: "
            msg += f"{json.dumps(user, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            msg = "item.switch: "
            msg += f"{json.dumps(switch.model_dump(), indent=4, sort_keys=True)}"
            self.log.debug(msg)

            nbr_dict = {
                "IF_NAME": user.get("interface"),
                "DOT1Q_ID": str(user.get("dot1q") or switch.dot1q_id),
                "IP_MASK": user.get("ipv4_addr") or switch.ip_mask,
                "NEIGHBOR_IP": user.get("neighbor_ipv4") or switch.neighbor_ip,
                "NEIGHBOR_ASN": switch.neighbor_asn,
                "IPV6_MASK": user.get("ipv6_addr") or switch.ipv6_mask,
                "IPV6_NEIGHBOR": user.get("neighbor_ipv6") or switch.ipv6_neighbor,
                "AUTO_VRF_LITE_FLAG": switch.auto_vrf_lite_flag,
                "PEER_VRF_NAME": user.get("peer_vrf") or switch.peer_vrf_name,
                "VRF_LITE_JYTHON_TEMPLATE": "Ext_VRF_Lite_Jython",
            }
            extension_values["VRF_LITE_CONN"].append(nbr_dict)

        ms_con = {"MULTISITE_CONN": []}
        extension_values["MULTISITE_CONN"] = json.dumps(ms_con)
        extension_values["VRF_LITE_CONN"] = json.dumps({"VRF_LITE_CONN": extension_values["VRF_LITE_CONN"]})
        vrf_attach["extensionValues"] = json.dumps(extension_values).replace(" ", "")
        if vrf_attach.get("vrf_lite") is not None:
            del vrf_attach["vrf_lite"]

        msg = "Returning modified vrf_attach: "
        msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        return copy.deepcopy(vrf_attach)

    def ip_to_serial_number(self, ip_address):
        """
        Given a switch ip_address, return the switch serial number.

        If ip_address is not found, return None.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}"
        self.log.debug(msg)

        return self.ip_sn.get(ip_address)

    def serial_number_to_ip(self, serial_number):
        """
        Given a switch serial_number, return the switch ip address.

        If serial_number is not found, return None.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}, "
        msg += f"serial_number: {serial_number}. "
        msg += f"Returning ip: {self.sn_ip.get(serial_number)}."
        self.log.debug(msg)

        return self.sn_ip.get(serial_number)

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

        ## Notes

        1. send_to_controller sends the payload, if provided, as-is. Hence,
           it is the caller's responsibility to ensure payload integrity.
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}"
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
            response = dcnm_send(self.module, args.verb.value, args.path, args.payload)
        else:
            response = dcnm_send(self.module, args.verb.value, args.path)

        if response is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "Unable to retrieve endpoint. "
            msg += f"verb {args.verb.value}, path {args.path}"
            raise ValueError(msg)

        self.response = copy.deepcopy(response)

        msg = "RX controller:"
        self.log.debug(msg)
        msg = f"verb: {args.verb.value}, "
        msg += f"path: {args.path}"
        self.log.debug(msg)
        msg = "response: "
        msg += f"{json.dumps(response, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "Calling self.handle_response. "
        msg += "self.result[changed]): "
        msg += f"{self.result['changed']}"
        self.log.debug(msg)

        if args.log_response is True:
            self.result["response"].append(response)

        generic_response = ControllerResponseGenericV12(**response)
        msg = "ControllerResponseGenericV12: "
        msg += f"{json.dumps(generic_response.model_dump(), indent=4, sort_keys=True)}"
        self.log.debug(msg)

        fail, self.result["changed"] = self.handle_response(generic_response, args.action)

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
            self.failure(response)

    def update_vrf_attach_fabric_name(self, vrf_attach: dict) -> dict:
        """
        # Summary

        For multisite fabrics, replace `vrf_attach.fabric` with the name of
        the child fabric returned by `self.sn_fab[vrf_attach.serialNumber]`

        ## params

        - `vrf_attach`

        A `vrf_attach` dictionary containing the following keys:

            - `fabric` : fabric name
            - `serialNumber` : switch serial number
        """
        method_name = inspect.stack()[0][3]
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}. "
        self.log.debug(msg)

        msg = "Received vrf_attach: "
        msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if self.fabric_type != "MFD":
            msg = "Early return. "
            msg += f"FABRIC_TYPE {self.fabric_type} is not MFD. "
            msg += "Returning unmodified vrf_attach."
            self.log.debug(msg)
            return copy.deepcopy(vrf_attach)

        parent_fabric_name = vrf_attach.get("fabric")

        msg = f"fabric_type: {self.fabric_type}, "
        msg += "replacing parent_fabric_name "
        msg += f"({parent_fabric_name}) "
        msg += "with child fabric name."
        self.log.debug(msg)

        serial_number = vrf_attach.get("serialNumber")

        if serial_number is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "Unable to parse serial_number from vrf_attach. "
            msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            self.module.fail_json(msg)

        child_fabric_name = self.sn_fab[serial_number]

        if child_fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"caller: {caller}. "
            msg += "Unable to determine child fabric name for serial_number "
            msg += f"{serial_number}."
            self.log.debug(msg)
            self.module.fail_json(msg)

        msg = f"serial_number: {serial_number}, "
        msg += f"child fabric name: {child_fabric_name}. "
        self.log.debug(msg)

        vrf_attach["fabric"] = child_fabric_name

        msg += "Updated vrf_attach: "
        msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        return copy.deepcopy(vrf_attach)

    def update_lan_attach_list(self, diff_attach: dict) -> list:
        """
        # Summary

        Update the lanAttachList in diff_attach and return the updated
        list.

        - Set vrf_attach.vlan to 0
        - If vrf_attach.vrf_lite is null, delete it
        - If the switch is not a border switch, fail the module
        - Get associated vrf_lite objects from the switch
        - Update vrf lite extensions with information from the vrf_lite objects
        - If vrf_attach.fabricName is present, replace it with vrf_attach.fabric
        - If, after replacing vrf_attach.fabricName, vrf_attach.fabric is None, fail the module

        ## Raises

        - fail_json: If the switch is not a border switch
        - fail_json: If vrf_attach.fabric is None after processing
        - fail_json: If vrf_attach does not contain a fabric key after processing
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = f"caller {caller}, "
        msg += "ENTERED. "
        self.log.debug(msg)

        new_lan_attach_list = []
        for vrf_attach in diff_attach["lanAttachList"]:
            vrf_attach.update(vlan=0)

            serial_number = vrf_attach.get("serialNumber")
            ip_address = self.serial_number_to_ip(serial_number)
            msg = f"ip_address {ip_address} ({serial_number}), "
            msg += "vrf_attach: "
            msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            vrf_attach = self.update_vrf_attach_fabric_name(vrf_attach)

            if "fabric" not in vrf_attach and "fabricName" in vrf_attach:
                vrf_attach["fabric"] = vrf_attach.pop("fabricName", None)
            if "fabric" not in vrf_attach:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"caller {caller}. "
                msg += "vrf_attach does not contain a fabric key. "
                msg += f"ip: {ip_address}, serial number: {serial_number}"
                self.module.fail_json(msg=msg)
            if vrf_attach.get("fabric") is None:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"caller {caller}. "
                msg += "vrf_attach.fabric is None. "
                msg += f"ip: {ip_address}, serial number: {serial_number}"
                self.module.fail_json(msg=msg)

            if "is_deploy" in vrf_attach:
                del vrf_attach["is_deploy"]
            # if vrf_lite is null, delete it.
            if not vrf_attach.get("vrf_lite"):
                if "vrf_lite" in vrf_attach:
                    msg = "vrf_lite exists, but is null. Delete it."
                    self.log.debug(msg)
                    del vrf_attach["vrf_lite"]
                new_lan_attach_list.append(vrf_attach)
                msg = f"ip_address {ip_address} ({serial_number}), "
                msg += "deleted null vrf_lite in vrf_attach and "
                msg += "skipping VRF Lite processing. "
                msg += "updated vrf_attach: "
                msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
                self.log.debug(msg)
                continue

            # VRF Lite processing

            msg = f"ip_address {ip_address} ({serial_number}), "
            msg += "vrf_attach.get(vrf_lite): "
            if vrf_attach.get("vrf_lite"):
                msg += f"{json.dumps(vrf_attach.get('vrf_lite'), indent=4, sort_keys=True)}"
            else:
                msg += f"{vrf_attach.get('vrf_lite')}"
            self.log.debug(msg)

            if not self.is_border_switch(serial_number):
                # arobel TODO: Not covered by UT
                msg = f"{self.class_name}.{method_name}: "
                msg += f"caller {caller}. "
                msg += "VRF LITE cannot be attached to "
                msg += "non-border switch. "
                msg += f"ip: {ip_address}, "
                msg += f"serial number: {serial_number}"
                self.module.fail_json(msg=msg)

            lite_objects_model = self.get_list_of_vrfs_switches_data_item_model(vrf_attach)

            msg = f"ip_address {ip_address} ({serial_number}), "
            msg += f"lite_objects: length {len(lite_objects_model)}."
            self.log_list_of_models(lite_objects_model)

            if not lite_objects_model:
                msg = f"ip_address {ip_address} ({serial_number}), "
                msg += "No lite objects. Append vrf_attach and continue."
                self.log.debug(msg)
                new_lan_attach_list.append(vrf_attach)
                continue

            lite = lite_objects_model[0].switch_details_list[0].extension_prototype_values
            msg = f"ip_address {ip_address} ({serial_number}), "
            msg += f"lite (list[ExtensionPrototypeValue]). length: {len(lite)}."
            self.log.debug(msg)
            self.log_list_of_models(lite)

            msg = f"ip_address {ip_address} ({serial_number}), "
            msg += "old vrf_attach: "
            msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            vrf_attach = self.update_vrf_attach_vrf_lite_extensions(vrf_attach, lite)
            msg = f"ip_address {ip_address} ({serial_number}), "
            msg += "new vrf_attach: "
            msg += f"{json.dumps(vrf_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            new_lan_attach_list.append(vrf_attach)
        return copy.deepcopy(new_lan_attach_list)

    def push_diff_attach(self, is_rollback=False) -> None:
        """
        # Summary

        Send diff_attach to the controller
        """
        caller = inspect.stack()[1][3]

        msg = f"caller {caller}, "
        msg += "ENTERED. "
        self.log.debug(msg)

        self.model_enabled = True

        msg = f"self.model_enabled: {self.model_enabled}."
        self.log.debug(msg)

        if self.model_enabled:
            self.push_diff_attach_model(is_rollback)
            return

        msg = "self.diff_attach PRE: "
        msg += f"{json.dumps(self.diff_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if not self.diff_attach:
            msg = "Early return. self.diff_attach is empty. "
            msg += f"{json.dumps(self.diff_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            return

        new_diff_attach_list: list = []
        for diff_attach in self.diff_attach:
            msg = "diff_attach: "
            msg += f"{json.dumps(diff_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            new_lan_attach_list = self.update_lan_attach_list(diff_attach)

            msg = "Updating diff_attach[lanAttachList] with: "
            msg += f"{json.dumps(new_lan_attach_list, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            diff_attach["lanAttachList"] = copy.deepcopy(new_lan_attach_list)
            new_diff_attach_list.append(copy.deepcopy(diff_attach))

            msg = "new_diff_attach_list: "
            msg += f"{json.dumps(new_diff_attach_list, indent=4, sort_keys=True)}"
            self.log.debug(msg)

        endpoint = EpVrfPost()
        endpoint.fabric_name = self.fabric
        args = SendToControllerArgs(
            action="attach",
            path=f"{endpoint.path}/attachments",
            verb=endpoint.verb,
            payload=json.dumps(new_diff_attach_list),
            log_response=True,
            is_rollback=is_rollback,
        )
        self.send_to_controller(args)

    def push_diff_attach_model(self, is_rollback=False) -> None:
        """
        # Summary

        Send diff_attach to the controller
        """
        caller = inspect.stack()[1][3]

        msg = f"caller {caller}, "
        msg += "ENTERED. "
        self.log.debug(msg)

        if not self.diff_attach:
            msg = "Early return. self.diff_attach is empty. "
            msg += f"{json.dumps(self.diff_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)
            return

        msg = f"type(self.diff_attach): {type(self.diff_attach)}."
        self.log.debug(msg)
        msg = f"self.diff_attach: PRE_UPDATE: {json.dumps(self.diff_attach, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        new_diff_attach_list: list = []
        for diff_attach in self.diff_attach:
            msg = f"type(diff_attach): {type(diff_attach)}."
            self.log.debug(msg)
            msg = "diff_attach: "
            msg += f"{json.dumps(diff_attach, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            new_lan_attach_list = self.update_lan_attach_list(diff_attach)

            msg = "Updating diff_attach[lanAttachList] with new_lan_attach_list: "
            msg += f"{json.dumps(new_lan_attach_list, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            diff_attach["lanAttachList"] = copy.deepcopy(new_lan_attach_list)
            new_diff_attach_list.append(copy.deepcopy(diff_attach))

            msg = "new_diff_attach_list: "
            msg += f"{json.dumps(new_diff_attach_list, indent=4, sort_keys=True)}"
            self.log.debug(msg)

        # Transmute new_diff_attach_list to a list of VrfAttachPayloadV12 models
        payload = [VrfAttachPayloadV12(**item) for item in new_diff_attach_list]
        msg = f"payload: type(payload[0]): {type(payload[0])} length: {len(payload)}."
        self.log.debug(msg)
        self.log_list_of_models(payload)

        endpoint = EpVrfPost()
        endpoint.fabric_name = self.fabric
        args = SendToControllerArgs(
            action="attach",
            path=f"{endpoint.path}/attachments",
            verb=endpoint.verb,
            payload=json.dumps([model.model_dump(exclude_unset=True, by_alias=True) for model in payload]),
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

        msg = f"caller: {caller}. "
        msg += "ENTERED."
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

        msg = f"caller: {caller}. "
        msg += "ENTERED."
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
        self.log.debug("ENTERED")

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
        msg += f"caller: {caller}."
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
        self.push_diff_attach(is_rollback=is_rollback)
        self.push_diff_deploy(is_rollback=is_rollback)

    def push_to_remote_model(self, is_rollback=False) -> None:
        """
        # Summary

        Send all diffs to the controller
        """
        caller = inspect.stack()[1][3]
        msg = "ENTERED. "
        msg += f"caller: {caller}."
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
        self.push_diff_attach(is_rollback=is_rollback)
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
        msg += f"caller: {caller}, "
        msg += f"vrf_name: {vrf_name}"
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
        self.log.debug("ENTERED")

        if self.state == "deleted":
            self.validate_input_deleted_state()
        elif self.state == "merged":
            self.validate_input_merged_state()
        elif self.state == "overridden":
            self.validate_input_overridden_state()
        elif self.state == "query":
            self.validate_input_query_state()
        elif self.state in ("replaced"):
            self.validate_input_replaced_state()

    def validate_vrf_config(self) -> None:
        """
        # Summary

        Validate self.config against VrfPlaybookModelV12 and update
        self.validated with the validated config.

        ## Raises

        -   Calls fail_json() if the input is invalid

        """
        if self.config is None:
            return
        for vrf_config in self.config:
            try:
                self.log.debug("Calling VrfPlaybookModelV12")
                config = VrfPlaybookModelV12(**vrf_config)
                msg = f"config.model_dump_json(): {config.model_dump_json()}"
                self.log.debug(msg)
                self.log.debug("Calling VrfPlaybookModelV12 DONE")
            except pydantic.ValidationError as error:
                self.module.fail_json(msg=error)

            self.validated.append(config.model_dump())

            msg = f"self.validated: {json.dumps(self.validated, indent=4, sort_keys=True)}"
            self.log.debug(msg)

    def validate_input_deleted_state(self) -> None:
        """
        # Summary

        Validate the input for deleted state.
        """
        if self.state != "deleted":
            return
        if not self.config:
            return
        self.validate_vrf_config()

    def validate_input_merged_state(self) -> None:
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

        self.validate_vrf_config()

    def validate_input_overridden_state(self) -> None:
        """
        # Summary

        Validate the input for overridden state.
        """
        if self.state != "overridden":
            return
        if not self.config:
            return
        self.validate_vrf_config()

    def validate_input_query_state(self) -> None:
        """
        # Summary

        Validate the input for query state.
        """
        if self.state != "query":
            return
        if not self.config:
            return
        self.validate_vrf_config()

    def validate_input_replaced_state(self) -> None:
        """
        # Summary

        Validate the input for replaced state.
        """
        if self.state != "replaced":
            return
        if not self.config:
            return
        self.validate_vrf_config()

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
        msg = f"ENTERED. caller {caller}, action {action}"
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

        self.push_to_remote(True)

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
