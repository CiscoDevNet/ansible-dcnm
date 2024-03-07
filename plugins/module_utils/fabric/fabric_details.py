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

from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_fabric import \
    RestSend

class FabricDetails(FabricCommon):
    """
    Retrieve fabric details from the controller and provide
    property accessors for the fabric attributes.
    """
    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricDetails()")

        self.data = {}
        self.endpoints = ApiEndpoints()
        self.rest_send = RestSend(self.ansible_module)

        self._init_properties()

    def _init_properties(self):
        # self.properties is already initialized in the parent class
        self.properties["foo"] = "bar"

    def refresh_super(self):
        """
        Refresh the fabric details from the controller.
        """
        method_name = inspect.stack()[0][3]
        endpoint = self.endpoints.fabrics
        self.rest_send.path = endpoint.get("path")
        self.rest_send.verb = endpoint.get("verb")
        self.rest_send.commit()
        self.data = {}
        for item in self.rest_send.response_current["DATA"]:
            self.data[item["fabricName"]] = item
            msg = f"item: {json.dumps(item, indent=4, sort_keys=True)}"
            self.log.debug(msg)

    def _get(self, item):
        """
        overridden in subclasses
        """

    def _get_nv_pair(self, item):
        """
        overridden in subclasses
        """

    @property
    def all_data(self):
        """
        Return all fabric details from the controller.
        """
        return self.data

    @property
    def asn(self):
        """
        Return the BGP asn of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - e.g. 65000
            - None
        """
        return self._get("asn")

    @property
    def enable_pbr(self):
        """
        Return the PBR enable state of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: boolean
        Possible values:
            - True
            - False
            - None
        """
        return self._get_nv_pair("ENABLE_PBR")

    @property
    def fabric_id(self):
        """
        Return the fabricId of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - e.g. FABRIC-5
            - None
        """
        return self._get("fabricId")

    @property
    def fabric_type(self):
        """
        Return the fabricType of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - Switch_Fabric
            - None
        """
        return self._get("fabricType")

    @property
    def replication_mode(self):
        """
        Return the replicationMode of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - Ingress
            - Multicast
            - None
        """
        return self._get("replicationMode")

    @property
    def template_name(self):
        """
        Return the templateName of the fabric specified with filter,
        if it exists.
        Return None otherwise

        Type: string
        Possible values:
            - Easy_Fabric
            - TODO - add other values
            - None
        """
        return self._get("templateName")

class FabricDetailsByName(FabricDetails):
    """
    Retrieve fabric details from the controller and provide
    property accessors for the fabric attributes.

    Usage (where module is an instance of AnsibleModule):

    instance = FabricDetailsByName(module)
    instance.refresh()
    instance.filter = "MyFabric"
    bgp_as = instance.bgp_as
    fabric_dict = instance.filtered_data
    etc...

    See FabricDetails for more details.
    """
    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricDetailsByName()")

        self.data_subclass = {}
        self.properties["filter"] = None

    def refresh(self):
        """
        Refresh fabric_name current details from the controller
        """
        self.refresh_super()
        self.data_subclass = {}
        for item in self.response_current:
            self.data_subclass[item["fabricName"]] = item

        msg = f"{self.class_name}.refresh(): self.data_subclass: "
        msg += f"{json.dumps(self.data_subclass, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _get(self, item):
        method_name = inspect.stack()[0][3]

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a fabric name "
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

    def _get_nv_pair(self, item):
        method_name = inspect.stack()[0][3]

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a fabric name "
            msg += f"before accessing property {item}."
            self.ansible_module.fail_json(msg, **self.failed_result)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name {self.filter} "
            msg += "does not exist on the controller."
            self.ansible_module.fail_json(msg, **self.failed_result)

        if self.data_subclass[self.filter].get("nvPairs", {}).get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name {self.filter} "
            msg += f"unknown property name: {item}."
            self.ansible_module.fail_json(msg, **self.failed_result)

        return self.make_none(
            self.make_boolean(self.data_subclass[self.filter].get("nvPairs").get(item))
        )

    @property
    def filtered_data(self):
        """
        Return a dictionary of the fabric matching self.filter.
        Return None if the fabric does not exist on the controller.
        """
        return self.data_subclass.get(self.filter)

    @property
    def filter(self):
        """
        Set the fabric_name of the fabric to query.

        This needs to be set before accessing this class's properties.
        """
        return self.properties.get("filter")

    @filter.setter
    def filter(self, value):
        self.properties["filter"] = value
