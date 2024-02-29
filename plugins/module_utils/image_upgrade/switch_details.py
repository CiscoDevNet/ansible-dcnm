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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend


class SwitchDetails(ImageUpgradeCommon):
    """
    Retrieve switch details from the controller and provide property accessors
    for the switch attributes.

    Usage (where module is an instance of AnsibleModule):

    instance = SwitchDetails(module)
    instance.refresh()
    instance.ip_address = 10.1.1.1
    fabric_name = instance.fabric_name
    serial_number = instance.serial_number
    etc...

    Switch details are retrieved by calling instance.refresh().

    Endpoint:
    /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/inventory/allswitches
    """

    def __init__(self, module):
        super().__init__(module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED SwitchDetails()")

        self.endpoints = ApiEndpoints()
        self.path = self.endpoints.switches_info.get("path")
        self.verb = self.endpoints.switches_info.get("verb")

        self.rest_send = RestSend(self.module)

        self._init_properties()

    def _init_properties(self):
        # self.properties is already initialized in the parent class
        self.properties["ip_address"] = None
        self.properties["info"] = {}

    def refresh(self):
        """
        Caller: __init__()

        Refresh switch_details with current switch details from
        the controller.
        """
        method_name = inspect.stack()[0][3]

        self.rest_send.verb = self.verb
        self.rest_send.path = self.path
        self.rest_send.commit()

        msg = f"self.rest_send.response_current: {self.rest_send.response_current}"
        self.log.debug(msg)

        msg = f"self.rest_send.result_current: {self.rest_send.result_current}"
        self.log.debug(msg)

        self.response = self.rest_send.response_current
        self.response_current = self.rest_send.response_current
        self.response_data = self.response_current.get("DATA", "No_DATA_SwitchDetails")

        self.result = self.rest_send.result_current
        self.result_current = self.rest_send.result_current

        if self.response_current["RETURN_CODE"] != 200:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Unable to retrieve switch information from the controller. "
            msg += f"Got response {self.response_current}"
            self.module.fail_json(msg, **self.failed_result)

        data = self.response_current.get("DATA")
        self.properties["info"] = {}
        for switch in data:
            self.properties["info"][switch["ipAddress"]] = switch

        msg = f"self.properties[info]: {json.dumps(self.properties['info'], indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _get(self, item):
        method_name = inspect.stack()[0][3]

        if self.ip_address is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.ip_address before accessing "
            msg += f"property {item}."
            self.module.fail_json(msg, **self.failed_result)

        if self.ip_address not in self.properties["info"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.ip_address} does not exist on the controller."
            self.module.fail_json(msg, **self.failed_result)

        if item not in self.properties["info"][self.ip_address]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.ip_address} does not have a key named {item}."
            self.module.fail_json(msg, **self.failed_result)

        return self.make_boolean(
            self.make_none(self.properties["info"][self.ip_address].get(item))
        )

    @property
    def ip_address(self):
        """
        Set the ip_address of the switch to query.

        This needs to be set before accessing this class's properties.
        """
        return self.properties.get("ip_address")

    @ip_address.setter
    def ip_address(self, value):
        self.properties["ip_address"] = value

    @property
    def fabric_name(self):
        """
        Return the fabricName of the switch with ip_address, if it exists.
        Return None otherwise
        """
        return self._get("fabricName")

    @property
    def hostname(self):
        """
        Return the hostName of the switch with ip_address, if it exists.
        Return None otherwise

        NOTES:
        1. This is None for 12.1.2e
        2. Better to use logical_name which is populated in both 12.1.2e and 12.1.3b
        """
        return self._get("hostName")

    @property
    def logical_name(self):
        """
        Return the logicalName of the switch with ip_address, if it exists.
        Return None otherwise
        """
        return self._get("logicalName")

    @property
    def model(self):
        """
        Return the model of the switch with ip_address, if it exists.
        Return None otherwise
        """
        return self._get("model")

    @property
    def info(self):
        """
        Return parsed data from the GET request.
        Return None otherwise

        NOTE: Keyed on ip_address
        """
        return self.properties["info"]

    @property
    def platform(self):
        """
        Return the platform of the switch with ip_address, if it exists.
        Return None otherwise

        NOTE: This is derived from "model". Is not in the controller response.
        """
        model = self._get("model")
        if model is None:
            return None
        return model.split("-")[0]

    @property
    def role(self):
        """
        Return the switchRole of the switch with ip_address, if it exists.
        Return None otherwise
        """
        return self._get("switchRole")

    @property
    def serial_number(self):
        """
        Return the serialNumber of the switch with ip_address, if it exists.
        Return None otherwise
        """
        return self._get("serialNumber")
