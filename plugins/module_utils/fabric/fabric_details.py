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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.common import \
    FabricCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints


class FabricDetails(FabricCommon):
    """
    Parent class for *FabricDetails() subclasses.
    See subclass docstrings for details.
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED FabricDetails()"
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.data = {}
        self.endpoints = ApiEndpoints()
        self.rest_send = RestSend(self.ansible_module)
        self.results = Results()
        # We always want to get the controller's current fabric state
        # so we set check_mode to False here so the request will be
        # sent to the controller
        self.rest_send.check_mode = False

        self._init_properties()

    def _init_properties(self):
        # self.properties is already initialized in the parent class
        pass

    def refresh_super(self):
        """
        Refresh the fabric details from the controller and
        populate self.data with the results.

        self.data is a dictionary of fabric details, keyed on
        fabric name.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        endpoint = self.endpoints.fabrics
        self.rest_send.path = endpoint.get("path")
        self.rest_send.verb = endpoint.get("verb")
        self.rest_send.commit()
        self.data = {}
        if self.rest_send.response_current.get("DATA") is None:
            return
        for item in self.rest_send.response_current.get("DATA"):
            self.data[item["fabricName"]] = item

        msg = f"self.data: {json.dumps(self.data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = "self.rest_send.response_current: "
        msg += (
            f"{json.dumps(self.rest_send.response_current, indent=4, sort_keys=True)}"
        )
        self.log.debug(msg)

        self.results.response_current = self.rest_send.response_current
        self.results.response = self.rest_send.response_current
        self.results.result_current = self.rest_send.result_current
        self.results.result = self.rest_send.result_current

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
        Return all fabric details from the controller (i.e. self.data)
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
    # BGP AS for fabric "MyFabric"
    bgp_as = instance.asn

    # all fabric details for "MyFabric"
    fabric_dict = instance.filtered_data
    etc...

    Or:

    instance.FabricDetailsByName(module)
    instance.refresh()
    all_fabrics = instance.all_data

    Where all_fabrics will be a dictionary of all fabrics
    on the controller, keyed on fabric name.
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
        self.data_subclass = copy.deepcopy(self.data)

    def _get(self, item):
        """
        Retrieve the value of the top-level (non-nvPair) item for fabric_name
        (anything not in the nvPairs dictionary).

        See also: _get_nv_pair()
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"instance.filter {self.filter} "
        self.log.debug(msg)

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a fabric name "
            msg += f"before accessing property {item}."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} does not exist on the controller."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        return self.make_none(
            self.make_boolean(self.data_subclass[self.filter].get(item))
        )

    def _get_nv_pair(self, item):
        """
        Retrieve the value of the nvPair item for fabric_name.

        See also: _get()
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"instance.filter {self.filter} "
        self.log.debug(msg)

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a fabric name "
            msg += f"before accessing property {item}."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name {self.filter} "
            msg += "does not exist on the controller."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        if self.data_subclass[self.filter].get("nvPairs", {}).get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric_name {self.filter} "
            msg += f"unknown property name: {item}."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

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


class FabricDetailsByNvPair(FabricDetails):
    """
    Retrieve fabric details from the controller filtered
    by nvPair key and value.  This sets the filtered_data
    property to a dictionary of all fabrics on the controller
    that match filter_key and filter_value.

    Usage (where ansible_module is an instance of AnsibleModule):

    instance = FabricDetailsNvPair(ansible_module)
    instance.refresh()
    instance.filter_key = "DCI_SUBNET_RANGE"
    instance.filter_value = "10.33.0.0/16"
    fabrics = instance.filtered_data
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED FabricDetailsByNvPair()")

        self.data_subclass = {}
        self.properties["filter_key"] = None
        self.properties["filter_value"] = None

    def refresh(self):
        """
        Refresh fabric_name current details from the controller
        """
        if self.filter_key is None:
            msg = "set instance.filter_key to a nvPair key "
            msg += "before calling refresh()."
            self.ansible_module.fail_json(msg, **self.results.failed_result)
        if self.filter_value is None:
            msg = "set instance.filter_value to a nvPair value "
            msg += "before calling refresh()."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        self.refresh_super()
        for item, value in self.data.items():
            if value.get("nvPairs", {}).get(self.filter_key) == self.filter_value:
                self.data_subclass[item] = value

    @property
    def filtered_data(self):
        """
        Return a dictionary of the fabric(s) matching self.filter_key
        and self.filter_value.
        Return None if the fabric does not exist on the controller.
        """
        return self.data_subclass

    @property
    def filter_key(self):
        """
        Return the nvPairs key to filter on.

        This should be an exact match for the key in the nvPairs
        dictionary for the fabric.
        """
        return self.properties.get("filter_key")

    @filter_key.setter
    def filter_key(self, value):
        self.properties["filter_key"] = value

    @property
    def filter_value(self):
        """
        Return the nvPairs value to filter on.

        This should be an exact match for the value in the nvPairs
        dictionary for the fabric.
        """
        return self.properties.get("filter_value")

    @filter_value.setter
    def filter_value(self, value):
        self.properties["filter_value"] = value
