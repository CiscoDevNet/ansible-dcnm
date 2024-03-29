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

import inspect
import json
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.image_upgrade_common import \
    ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send


class SwitchIssuDetails(ImageUpgradeCommon):
    """
    Retrieve switch issu details from the controller and provide
    property accessors for the switch attributes.

    Usage: See subclasses.

    Endpoint:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/packagemgnt/issu

    Response body:
    {
        "status": "SUCCESS",
        "lastOperDataObject": [
            {
                "serialNumber": "FDO211218GC",
                "deviceName": "cvd-1312-leaf",
                "fabric": "fff",
                "version": "10.3(2)",
                "policy": "NR3F",
                "status": "In-Sync",
                "reason": "Compliance",
                "imageStaged": "Success",
                "validated": "None",
                "upgrade": "None",
                "upgGroups": "None",
                "mode": "Normal",
                "systemMode": "Normal",
                "vpcRole": null,
                "vpcPeer": null,
                "role": "leaf",
                "lastUpgAction": "Never",
                "model": "N9K-C93180YC-EX",
                "ipAddress": "172.22.150.103",
                "issuAllowed": "",
                "statusPercent": 100,
                "imageStagedPercent": 100,
                "validatedPercent": 0,
                "upgradePercent": 0,
                "modelType": 0,
                "vdcId": 0,
                "ethswitchid": 8430,
                "platform": "N9K",
                "vpc_role": null,
                "ip_address": "172.22.150.103",
                "peer": null,
                "vdc_id": -1,
                "sys_name": "cvd-1312-leaf",
                "id": 3,
                "group": "fff",
                "fcoEEnabled": false,
                "mds": false
            },
            {etc...}
        ]

    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED SwitchIssuDetails()")

        self.endpoints = ApiEndpoints()
        self._init_properties()

    def _init_properties(self):
        # self.properties is already initialized in the parent class
        # action_keys is used in subclasses to determine if any actions
        # are in progress.
        # Property actions_in_progress returns True if so, False otherwise
        self.properties["action_keys"] = set()
        self.properties["action_keys"].add("imageStaged")
        self.properties["action_keys"].add("upgrade")
        self.properties["action_keys"].add("validated")

    def refresh_super(self) -> None:
        """
        Refresh current issu details from the controller.
        """
        method_name = inspect.stack()[0][3]

        path = self.endpoints.issu_info.get("path")
        verb = self.endpoints.issu_info.get("verb")

        msg = f"verb: {verb}, path {path}"
        self.log.debug(msg)

        self.response_current = dcnm_send(self.ansible_module, verb, path)
        self.result_current = self._handle_response(self.response_current, verb)

        msg = f"self.response_current: {json.dumps(self.response_current, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"self.result_current: {json.dumps(self.result_current, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if (
            self.result_current["success"] is False
            or self.result_current["found"] is False
        ):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Bad result when retriving switch "
            msg += "information from the controller"
            self.ansible_module.fail_json(msg, **self.failed_result)

        data = self.response_current.get("DATA").get("lastOperDataObject")

        if data is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "The controller has no switch ISSU information."
            self.ansible_module.fail_json(msg, **self.failed_result)

        if len(data) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "The controller has no switch ISSU information."
            self.ansible_module.fail_json(msg, **self.failed_result)

    @property
    def actions_in_progress(self):
        """
        Return True if any actions are in progress
        Return False otherwise
        """
        for action_key in self.properties["action_keys"]:
            if self._get(action_key) == "In-Progress":
                return True
        return False

    def _get(self, item):
        """
        overridden in subclasses
        """

    @property
    def device_name(self):
        """
        Return the deviceName of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            device name, e.g. "cvd-1312-leaf"
            None
        """
        return self._get("deviceName")

    @property
    def eth_switch_id(self):
        """
        Return the ethswitchid of the switch with
        ip_address, if it exists.
        Return None otherwise

        Possible values:
            integer
            None
        """
        return self._get("ethswitchid")

    @property
    def fabric(self):
        """
        Return the fabric of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            fabric name, e.g. "myfabric"
            None
        """
        return self._get("fabric")

    @property
    def fcoe_enabled(self):
        """
        Return whether FCOE is enabled on the switch with
        ip_address, if it exists.
        Return None otherwise

        Possible values:
            boolean (true/false)
            None
        """
        return self.make_boolean(self._get("fcoEEnabled"))

    @property
    def group(self):
        """
        Return the group of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            group name, e.g. "mygroup"
            None
        """
        return self._get("group")

    @property
    # id is a python keyword, so we can't use it as a property name
    # so we use switch_id instead
    def switch_id(self):
        """
        Return the switch ID of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            Integer
            None
        """
        return self._get("id")

    @property
    def image_staged(self):
        """
        Return the imageStaged of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            Success
            Failed
            None
        """
        return self._get("imageStaged")

    @property
    def image_staged_percent(self):
        """
        Return the imageStagedPercent of the switch with
        ip_address, if it exists.
        Return None otherwise

        Possible values:
            Integer in range 0-100
            None
        """
        return self._get("imageStagedPercent")

    @property
    def ip_address(self):
        """
        Return the ipAddress of the switch, if it exists.
        Return None otherwise

        Possible values:
            switch IP address
            None
        """
        return self._get("ipAddress")

    @property
    def issu_allowed(self):
        """
        Return the issuAllowed value of the switch with
        ip_address, if it exists.
        Return None otherwise

        Possible values:
            ?? TODO:3 check this
            ""
            None
        """
        return self._get("issuAllowed")

    @property
    def last_upg_action(self):
        """
        Return the last upgrade action performed on the switch
        with ip_address, if it exists.
        Return None otherwise

        Possible values:
            ?? TODO:3 check this
            Never
            None
        """
        return self._get("lastUpgAction")

    @property
    def mds(self):
        """
        Return whether the switch with ip_address is an MSD, if it exists.
        Return None otherwise

        Possible values:
            Boolean (True or False)
            None
        """
        return self.make_boolean(self._get("mds"))

    @property
    def mode(self):
        """
        Return the ISSU mode of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            "Normal"
            None
        """
        return self._get("mode")

    @property
    def model(self):
        """
        Return the model of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            model number e.g. "N9K-C93180YC-EX"
            None
        """
        return self._get("model")

    @property
    def model_type(self):
        """
        Return the model type of the switch with
        ip_address, if it exists.
        Return None otherwise

        Possible values:
            Integer
            None
        """
        return self._get("modelType")

    @property
    def peer(self):
        """
        Return the peer of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            ?? TODO:3 check this
            None
        """
        return self._get("peer")

    @property
    def platform(self):
        """
        Return the platform of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            platform, e.g. "N9K"
            None
        """
        return self._get("platform")

    @property
    def policy(self):
        """
        Return the policy attached to the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            policy name, e.g. "NR3F"
            None
        """
        return self._get("policy")

    @property
    def reason(self):
        """
        Return the reason (?) of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            Compliance
            Validate
            Upgrade
            None
        """
        return self._get("reason")

    @property
    def role(self):
        """
        Return the role of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            switch role, e.g. "leaf"
            None
        """
        return self._get("role")

    @property
    def serial_number(self):
        """
        Return the serialNumber of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            switch serial number, e.g. "AB1234567CD"
            None
        """
        return self._get("serialNumber")

    @property
    def status(self):
        """
        Return the sync status of the switch with ip_address, if it exists.
        Return None otherwise

        Details: The sync status is the status of the switch with respect
        to the image policy.  If the switch is in sync with the image policy,
        the status is "In-Sync".  If the switch is out of sync with the image
        policy, the status is "Out-Of-Sync".

        Possible values:
            "In-Sync"
            "Out-Of-Sync"
            None
        """
        return self._get("status")

    @property
    def status_percent(self):
        """
        Return the upgrade (TODO:3 verify this) percentage completion
        of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            Integer in range 0-100
            None
        """
        return self._get("statusPercent")

    @property
    def sys_name(self):
        """
        Return the system name of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            system name, e.g. "cvd-1312-leaf"
            None
        """
        return self._get("sys_name")

    @property
    def system_mode(self):
        """
        Return the system mode of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            "Maintenance" (TODO:3 verify this)
            "Normal"
            None
        """
        return self._get("systemMode")

    @property
    def upgrade(self):
        """
        Return the upgrade status of the switch with ip_address,
        if it exists.
        Return None otherwise

        Possible values:
            Success
            In-Progress
            None
        """
        return self._get("upgrade")

    @property
    def upg_groups(self):
        """
        Return the upgGroups (upgrade groups) of the switch with ip_address,
        if it exists.
        Return None otherwise

        Possible values:
            upgrade group to which the switch belongs e.g. "LEAFS"
            None
        """
        return self._get("upgGroups")

    @property
    def upgrade_percent(self):
        """
        Return the upgrade percent complete of the switch
        with ip_address, if it exists.
        Return None otherwise

        Possible values:
            Integer in range 0-100
            None
        """
        return self._get("upgradePercent")

    @property
    def validated(self):
        """
        Return the validation status of the switch with ip_address,
        if it exists.
        Return None otherwise

        Possible values:
            Failed
            Success
            None
        """
        return self._get("validated")

    @property
    def validated_percent(self):
        """
        Return the validation percent complete of the switch
        with ip_address, if it exists.
        Return None otherwise

        Possible values:
            Integer in range 0-100
            None
        """
        return self._get("validatedPercent")

    @property
    def vdc_id(self):
        """
        Return the vdcId of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            Integer
            None
        """
        return self._get("vdcId")

    @property
    def vdc_id2(self):
        """
        Return the vdc_id of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            Integer (negative values are valid)
            None
        """
        return self._get("vdc_id")

    @property
    def version(self):
        """
        Return the version of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            version, e.g. "10.3(2)"
            None
        """
        return self._get("version")

    @property
    def vpc_peer(self):
        """
        Return the vpcPeer of the switch with ip_address, if it exists.
        Return None otherwise

        Possible values:
            vpc peer e.g.: 10.1.1.1
            None
        """
        return self._get("vpcPeer")

    @property
    def vpc_role(self):
        """
        Return the vpcRole of the switch with ip_address, if it exists.
        Return None otherwise

        NOTE:   Two properties exist for vpc_role in the controller response.
                vpc_role corresponds to vpcRole.
        Possible values:
            vpc role e.g.:
                "primary"
                "secondary"
                "none" -> This will be translated to None
                "none established" (TODO:3 verify this)
                "primary, operational secondary" (TODO:3 verify this)
            None
        """
        return self._get("vpcRole")

    @property
    def vpc_role2(self):
        """
        Return the vpc_role of the switch with ip_address, if it exists.
        Return None otherwise

        NOTE:   Two properties exist for vpc_role in the controller response.
                vpc_role2 corresponds to vpc_role.
        Possible values:
            vpc role e.g.:
                "primary"
                "secondary"
                "none" -> This will be translated to None
                "none established" (TODO:3 verify this)
                "primary, operational secondary" (TODO:3 verify this)
            None
        """
        return self._get("vpc_role")


class SwitchIssuDetailsByIpAddress(SwitchIssuDetails):
    """
    Retrieve switch issu details from the controller and provide
    property accessors for the switch attributes retrieved by ip address.

    Usage (where module is an instance of AnsibleModule):

    instance = SwitchIssuDetailsByIpAddress(module)
    instance.refresh()
    instance.filter = "10.1.1.1"
    image_staged = instance.image_staged
    image_upgraded = instance.image_upgraded
    serial_number = instance.serial_number
    etc...

    See SwitchIssuDetails for more details.
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED SwitchIssuDetailsByIpAddress()")

        self.data_subclass = {}
        self.properties["filter"] = None

    def refresh(self):
        """
        Refresh ip_address current issu details from the controller
        """
        self.refresh_super()
        self.data_subclass = {}
        for switch in self.response_current["DATA"]["lastOperDataObject"]:
            self.data_subclass[switch["ipAddress"]] = switch

        msg = f"{self.class_name}.refresh(): self.data_subclass: "
        msg += f"{json.dumps(self.data_subclass, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _get(self, item):
        method_name = inspect.stack()[0][3]

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a switch ipAddress "
            msg += f"before accessing property {item}."
            self.ansible_module.fail_json(msg, **self.failed_result)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} does not exist on the controller."
            self.ansible_module.fail_json(msg, **self.failed_result)

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            self.ansible_module.fail_json(msg, **self.failed_result)

        return self.make_none(
            self.make_boolean(self.data_subclass[self.filter].get(item))
        )

    @property
    def filtered_data(self):
        """
        Return a dictionary of the switch matching self.filter.
        Return None if the switch does not exist on the controller.
        """
        return self.data_subclass.get(self.filter)

    @property
    def filter(self):
        """
        Set the ip_address of the switch to query.

        This needs to be set before accessing this class's properties.
        """
        return self.properties.get("filter")

    @filter.setter
    def filter(self, value):
        self.properties["filter"] = value


class SwitchIssuDetailsBySerialNumber(SwitchIssuDetails):
    """
    Retrieve switch issu details from NDFC and provide property accessors
    for the switch attributes retrieved by serial_number.

    Usage (where module is an instance of AnsibleModule):

    instance = SwitchIssuDetailsBySerialNumber(module)
    instance.refresh()
    instance.filter = "FDO211218GC"
    instance.refresh()
    image_staged = instance.image_staged
    image_upgraded = instance.image_upgraded
    ip_address = instance.ip_address
    etc...

    See SwitchIssuDetails for more details.

    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED SwitchIssuDetailsBySerialNumber()")

        self.data_subclass = {}
        self.properties["filter"] = None

    def refresh(self):
        """
        Refresh serial_number current issu details from NDFC
        """
        self.refresh_super()

        self.data_subclass = {}
        for switch in self.response_current["DATA"]["lastOperDataObject"]:
            self.data_subclass[switch["serialNumber"]] = switch

        msg = f"{self.class_name}.refresh(): self.data_subclass: "
        msg += f"{json.dumps(self.data_subclass, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _get(self, item):
        method_name = inspect.stack()[0][3]

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a switch serialNumber "
            msg += f"before accessing property {item}."
            self.ansible_module.fail_json(msg, **self.failed_result)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} does not exist "
            msg += "on the controller."
            self.ansible_module.fail_json(msg, **self.failed_result)

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            self.ansible_module.fail_json(msg, **self.failed_result)

        return self.make_none(
            self.make_boolean(self.data_subclass[self.filter].get(item))
        )

    @property
    def filtered_data(self):
        """
        Return a dictionary of the switch matching self.serial_number.
        Return None if the switch does not exist on the controller.
        """
        return self.data_subclass.get(self.filter)

    @property
    def filter(self):
        """
        Set the serial_number of the switch to query.

        This needs to be set before accessing this class's properties.
        """
        return self.properties.get("filter")

    @filter.setter
    def filter(self, value):
        self.properties["filter"] = value


class SwitchIssuDetailsByDeviceName(SwitchIssuDetails):
    """
    Retrieve switch issu details from NDFC and provide property accessors
    for the switch attributes retrieved by device_name.

    Usage (where module is an instance of AnsibleModule):

    instance = SwitchIssuDetailsByDeviceName(module)
    instance.refresh()
    instance.filter = "leaf_1"
    image_staged = instance.image_staged
    image_upgraded = instance.image_upgraded
    ip_address = instance.ip_address
    etc...

    See SwitchIssuDetails for more details.

    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED SwitchIssuDetailsByDeviceName()")

        self.data_subclass = {}
        self.properties["filter"] = None

    def refresh(self):
        """
        Refresh device_name current issu details from NDFC
        """
        self.refresh_super()
        self.data_subclass = {}
        for switch in self.response_current["DATA"]["lastOperDataObject"]:
            self.data_subclass[switch["deviceName"]] = switch

        msg = f"{self.class_name}.refresh(): self.data_subclass: "
        msg += f"{json.dumps(self.data_subclass, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _get(self, item):
        method_name = inspect.stack()[0][3]

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a switch deviceName "
            msg += f"before accessing property {item}."
            self.ansible_module.fail_json(msg, **self.failed_result)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} does not exist "
            msg += "on the controller."
            self.ansible_module.fail_json(msg, **self.failed_result)

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            self.ansible_module.fail_json(msg, **self.failed_result)

        return self.make_none(
            self.make_boolean(self.data_subclass[self.filter].get(item))
        )

    @property
    def filtered_data(self):
        """
        Return a dictionary of the switch matching self.filter.
        Return None of the switch does not exist in NDFC.
        """
        return self.data_subclass.get(self.filter)

    @property
    def filter(self):
        """
        Set the device_name of the switch to query.

        This needs to be set before accessing this class's properties.
        """
        return self.properties.get("filter")

    @filter.setter
    def filter(self, value):
        self.properties["filter"] = value
