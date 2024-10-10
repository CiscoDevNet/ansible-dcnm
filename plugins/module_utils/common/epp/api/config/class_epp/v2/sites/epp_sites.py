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

# Required for class decorators
# pylint: disable=no-member

import copy
import inspect
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.config.class_ep.v2.sites.sites import \
    EpSites
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties


@Properties.add_rest_send
@Properties.add_results
class EppSites:
    """
    ### Summary
    Parent class for EppSites* subclasses.
    See subclass docstrings for details.

    ### Raises
    None

    ### Data Structure
    ```json
    [
        {
            "aci": {
                "appUserName": "",
                "inbandEpgDN": "",
                "switches": []
            },
            "annotateLock": {},
            "annotation": {
                "default-site-grp": "00000000-e404-4336-97cd-549f7095f3f4",
                "ndfcFabricId": "3",
                "nxCloudCapable": "true"
            },
            "apps": [
                {
                    "appName": "ndfc",
                    "displayName": "Nexus Dashboard Fabric Controller",
                    "version": "12.2.2.238",
                    "vendor": "Cisco"
                }
            ],
            "cloudAci": {
                "provider": "",
                "region": [],
                "regionCount": "",
                "regionName": "",
                "router": [],
                "routerCount": "",
                "virtnet": [],
                "virtualNetworkCount": "",
                "vpc": [],
                "vpcCount": ""
            },
            "controllers": [
                {
                    "mgmtIP": "172.22.150.244",
                    "mgmtIP6": "",
                    "sn": "3F7CDCDE032B",
                    "dataIP": "10.1.3.2",
                    "dataIP6": "",
                    "url": "10.1.3.2:443",
                    "url6": "[]:443",
                    "mgmtUrl": "172.22.150.244:443",
                    "mgmtUrl6": "[]:443",
                    "version": "12.2.2.238",
                    "fabDomain": "",
                    "systemUptime": "",
                    "health": ""
                }
            ],
            "dcnm": {
                "dcnmFabricSiteID": "65001",
                "fabricName": "f1",
                "fabricReadOnly": false,
                "fabricTechnology": "VxlanFabric",
                "fabricType": "SwitchFabric",
                "ha": {
                    "dcnm": []
                },
                "health": "",
                "loginDomain": "DefaultAuth",
                "switches": [
                    {
                        "switchType": "Spine",
                        "sn": "FOX2109PGCS",
                        "model": "N9K-C9504",
                        "version": "10.2(5)",
                        "mgmtIP": "172.22.150.112",
                        "systemUptime": "",
                        "health": "-1",
                        "name": "",
                        "adminState": ""
                    },
                    {
                        "switchType": "Spine",
                        "sn": "FOX2109PGD0",
                        "model": "N9K-C9504",
                        "version": "10.3(1)",
                        "mgmtIP": "172.22.150.113",
                        "systemUptime": "",
                        "health": "-1",
                        "name": "",
                        "adminState": ""
                    },
                    {
                        "switchType": "Leaf",
                        "sn": "FDO211218GC",
                        "model": "N9K-C93180YC-EX",
                        "version": "10.3(1)",
                        "mgmtIP": "172.22.150.103",
                        "systemUptime": "",
                        "health": "-1",
                        "name": "",
                        "adminState": ""
                    },
                    {
                        "switchType": "Leaf",
                        "sn": "FDO211218HH",
                        "model": "N9K-C93180YC-EX",
                        "version": "10.3(1)",
                        "mgmtIP": "172.22.150.104",
                        "systemUptime": "",
                        "health": "-1",
                        "name": "",
                        "adminState": ""
                    },
                    {
                        "switchType": "Leaf",
                        "sn": "FDO211218FV",
                        "model": "N9K-C93180YC-EX",
                        "version": "10.2(5)",
                        "mgmtIP": "172.22.150.105",
                        "systemUptime": "",
                        "health": "-1",
                        "name": "",
                        "adminState": ""
                    }
                ],
                "username": ""
            },
            "disablePolling": false,
            "disablePollingReason": "",
            "displayName": "f1",
            "dualStackPrefMode": "IPv4",
            "fedInfo": {
                "fedMemUUID": "federation-nd1",
                "local": true,
                "name": "nd1",
                "siteFingerprint": "",
                "siteUUID": "87984999-a6dd-42ef-aa84-2b0947750cea"
            },
            "internalOnboard": true,
            "latitude": "",
            "launchURL": "/appcenter/cisco/ndfc/ui/manage/lan-fabrics",
            "longitude": "",
            "meta": {
                "modts": "2024-10-08T21:16:26.004815678Z",
                "createts": "2024-08-06T16:54:42.176155908Z",
                "dn": "ndsites/f1",
                "type": "ndsites",
                "version": 0
            },
            "name": "f1",
            "notifyReason": "",
            "nxos": {
                "allowNDIConfig": true,
                "dcnmFabricSiteID": "",
                "fabricName": "",
                "fabricReadOnly": false,
                "fabricTechnology": "VxlanFabric",
                "fabricType": "SwitchFabric",
                "health": "",
                "switches": []
            },
            "pollingDetectionDone": false,
            "pollingType": "AllIPs",
            "schemaversion": "",
            "securityDomains": [
                "all"
            ],
            "siteHealth": "40.000000",
            "siteIPType": "IPv4",
            "siteReachabilty": {
                "description": "NDFC Fabric on-boarded internally",
                "nodeReachability": [
                    {
                        "ip": "10.1.3.2",
                        "state": "Up"
                    }
                ],
                "state": "Up"
            },
            "siteType": "DCNMNG",
            "updSwitchTimeStamp": "0001-01-01T00:00:00Z",
            "updTimeStamp": "0001-01-01T00:00:00Z",
            "url": "apigw.kube-system:443",
            "useProxy": false,
            "userConfig": false,
            "verifySecure": false
        }
    ]
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.action = "sites"
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED EppSites()"
        self.log.debug(msg)

        self.data = {}
        self.conversion = ConversionUtils()
        self.ep_sites = EpSites()

        self._rest_send = None
        self._results = None
        self._result_code = None
        self._result_message = None

    def register_result(self):
        """
        ### Summary
        Update the results object with the current state of the endpoint
        and register the result.

        ### Raises
        -   ``ValueError``if:
                -    ``Results()`` raises ``TypeError``
        """
        method_name = inspect.stack()[0][3]
        try:
            self.results.action = self.action
            self.results.response_current = self.rest_send.response_current
            self.results.result_current = self.rest_send.result_current
            if self.results.response_current.get("RETURN_CODE") in [200, 400]:
                self.results.failed = False
            else:
                self.results.failed = True
            # endpoint never changes the controller state
            self.results.changed = False
            self.results.register_task_result()
        except TypeError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Failed to register result. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def validate_refresh_parameters(self) -> None:
        """
        ### Summary
        Validate that mandatory parameters are set before calling refresh().

        ### Raises
        -   ``ValueError``if:
                -   ``rest_send`` is not set.
                -   ``results`` is not set.
        """
        method_name = inspect.stack()[0][3]
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.rest_send must be set before calling "
            msg += f"{self.class_name}.refresh()."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.results must be set before calling "
            msg += f"{self.class_name}.refresh()."
            raise ValueError(msg)

    def refresh_super(self):
        """
        ### Summary
        Call the controller endpoint, refresh the endpoint response, and
        populate self.data with the results.

        ### Raises
        -   ``ValueError`` if:
                -   ``validate_refresh_parameters()`` raises ``ValueError``.
                -   ``RestSend`` raises ``TypeError`` or ``ValueError``.
                -   ``register_result()`` raises ``ValueError``.

        ### Notes
        -   ``self.data`` is a dictionary of endpoint response elements, keyed on
            fabric name.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            self.validate_refresh_parameters()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.rest_send.path = self.ep_sites.path
            self.rest_send.verb = self.ep_sites.verb

            # We always want to get this endpoint's current state,
            # regardless of the current value of check_mode.
            # We save the current check_mode and timeout settings, set
            # rest_send.check_mode to False so the request will be sent
            # to the controller, and then restore the original settings.

            self.rest_send.save_settings()
            self.rest_send.check_mode = False
            self.rest_send.timeout = 1
            self.rest_send.commit()
            self.rest_send.restore_settings()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

        self.data = {}
        response_data = self.rest_send.response_current.get("DATA")
        self._result_code = self.rest_send.response_current.get("RETURN_CODE")
        if self.result_code in [400, 401]:
            # TODO: Verify 400 response
            self._result_message = response_data.get("message")
            msg = f"Received result_code {self.result_code}. "
            msg += f"Message: {self._result_message}"
            self.log.debug(msg)
            self.data = {}
        elif self.result_code == 200:
            self.data = self.rest_send.response_current.get("DATA", {})
        else:
            message = self.rest_send.response_current.get("MESSAGE")
            msg = f"Got RETURN_CODE {self.result_code} with message {message}"
            raise ValueError(msg)

        msg = f"{self.class_name}.{method_name}: calling self.rest_send.commit() DONE"
        self.log.debug(msg)

    def _get(self, item):
        """
        ### Summary
        overridden in subclasses
        """

    @property
    def all_data(self):
        """
        ### Summary
        Return all endpoint data from the controller (i.e. self.data)

        ``refresh`` must be called before accessing this property.

        ### Raises
        None
        """
        return self.data

    @property
    def result_code(self):
        """
        ### Summary
        Return the result code in the response

        ### Type
        int

        ### Example
        200
        """
        return self._result_code

    @property
    def result_message(self):
        """
        -   If the RETURN_CODE (self.result_code) == 400, result_message
            will be DATA.message.
        -   In all other cases result_message will be response.MESSAGE
        """
        return self._result_message


class EppSitesByName(EppSites):
    """
    ### Summary
    Retrieve site details from the controller by providing the
    site fabric name, and provide property accessors for the site
    attributes.

    ### Raises
    -   ``ValueError`` if:
            -   ``super.__init__()`` raises ``ValueError``.
            -   ``refresh_super()`` raises ``ValueError``.
            -   ``refresh()`` raises ``ValueError``.
            -   ``filter`` is not set before accessing properties.
            -   ``federation_name`` does not exist on the controller.
            -   An attempt is made to access a key that does not exist
                for the filtered federation_name.

    ### Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.epp.api.class_epp.v2.sites.epp_sites import EppSitesByName
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = EppSitesByName()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    instance.filter = "MyFabricName"

    # all details for "MyFabricName"
    details_dict = instance.filtered_data
    if details_dict is None:
        # fabric does not exist on the controller
    # etc...
    ```

    Or:

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.epp.api.class_epp.v2.sites.epp_sites import EppSitesByName
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import Results
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import Sender

    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = EppSitesByName()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    all_fabrics = instance.all_data
    ```

    Where ``all_sites`` will be a dictionary of all fabrics known to the controller.
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        super().__init__()

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED EppSitesByName()"
        self.log.debug(msg)

        self.data_subclass = {}
        self._name = None
        self._filter = None

    def refresh(self):
        """
        ### Refresh sites current details from the controller

        ### Raises
        -   ``ValueError`` if:
                -   Mandatory properties are not set.
        """
        try:
            self.refresh_super()
        except ValueError as error:
            msg = "Failed to refresh sites details: "
            msg += f"Error detail: {error}."
            raise ValueError(msg) from error

        # data_subclass is keyed on name
        self.data_subclass = {}
        for item in self.data:
            name = item.get("name")
            if name is None:
                continue
            self.data_subclass[name] = copy.deepcopy(item)

    def _get(self, item):
        """
        Retrieve the value of top-level items.

        -   raise ``ValueError`` if ``self.filter`` has not been set.
        -   raise ``ValueError`` if ``self.filter`` (fabric_name) does not exist
            on the controller.
        -   raise ``ValueError`` if item is not a valid property name for the fabric.

        See also: ``_get_nv_pair()``
        """
        method_name = inspect.stack()[0][3]

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a fabric name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric name {self.filter} does not exist on the "
            msg += "controller."
            raise ValueError(msg)

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(self.data_subclass[self.filter].get(item))
        )

    def verify_filter(self, item):
        """
        ### Summary
        Verify that filter is set and that data_subclass contains filter.

        ### Raises
        - ``ValueError`` if:
                -   ``self.filter`` has not been set.
                -   ``self.filter`` (fabric name) does not exist on the controller.
        """
        method_name = inspect.stack()[0][3]
        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a fabric name "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"fabric name {self.filter} "
            msg += "does not exist on the controller."
            raise ValueError(msg)

    def _get_dict_value_by_keyname(self, prop, item):
        """
        ### Summary
        Retrieve the value of MATCH.prop.item for filter.

        ### Raises
        - ``ValueError`` if:
                -   ``self.filter`` has not been set.
                -   ``self.filter`` (fabric name) does not exist on the controller.
                -   ``item`` is not a valid property name in MATCH.propname.

        ### Usage
        -   ``prop`` is a property in this class that returns a dictionary.
            Examples include: aci, annotation, cloud_aci, dcnm, fed_info.

        ### Example
        ```python
        ### Return fedInfo.fedMemUUID
        fed_mem_uuid = self._get_dict_value_by_keyname(self.fed_info, "fedMemUUID")
        ```
        """
        method_name = inspect.stack()[0][3]

        try:
            self.verify_filter(item)
        except ValueError as error:
            raise ValueError(error) from error

        value = prop.get(item)
        if value is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter}.dcnm.{item} does not exist."
            raise ValueError(msg)

        return self.conversion.make_none(self.conversion.make_boolean(value))

    @property
    def aci(self):
        """
        ### Summary
        Returns aci

        ### Type
        dict
        """
        return self._get("aci")

    @property
    def aci_app_username(self):
        """
        ### Summary
        Returns aci.appUserName

        ### Type
        str
        """
        return self._get_dict_value_by_keyname(self.aci, "appUserName")

    @property
    def aci_inband_epg_dn(self):
        """
        ### Summary
        Returns aci.inbandEpgDN

        ### Type
        str
        """
        return self._get_dict_value_by_keyname(self.aci, "inbandEpgDN")

    @property
    def aci_switches(self):
        """
        ### Summary
        Returns aci.switches

        ### Type
        list
        """
        return self._get_dict_value_by_keyname(self.aci, "switches")

    @property
    def annotate_lock(self):
        """
        ### Summary
        Returns annotateLock

        ### Type
        dict
        """
        return self._get("annotateLock")

    @property
    def annotation(self):
        """
        ### Summary
        Returns annotation

        ### Type
        dict
        """
        return self._get("annotation")

    @property
    def annotation_default_site_grp(self):
        """
        ### Summary
        Returns annotation.default-site-grp

        ### Type
        str

        ### Example
        "00000000-e404-4336-97cd-549f7095f3f4"
        """
        return self._get_dict_value_by_keyname(self.annotation, "default-site-grp")

    @property
    def annotation_ndfc_fabric_id(self):
        """
        ### Summary
        Returns annotation.ndfcFabricId

        ### Type
        str

        ### Example
        "3"
        """
        return self._get_dict_value_by_keyname(self.annotation, "ndfcFabricId")

    @property
    def annotation_nx_cloud_capable(self):
        """
        ### Summary
        Returns annotation.nxCloudCapable

        ### Type
        bool

        ### Example
        True
        """
        return self._get_dict_value_by_keyname(self.annotation, "nxCloudCapable")

    @property
    def apps(self):
        """
        ### Summary
        Returns apps

        ### Type
        list of dict
        """
        return self._get("apps")

    @property
    def apps_by_app_name(self):
        """
        ### Summary
        Returns apps keyed on appName

        ### Type
        dict
        """
        apps = {}
        if self._get("apps") is None:
            return {}
        for app in self._get("apps"):
            if app is None:
                continue
            app_name = app.get("appName")
            if app_name is None:
                continue
            apps[app_name] = copy.deepcopy(app)
        return apps

    @property
    def cloud_aci(self):
        """
        ### Summary
        Returns cloudAci

        ### Type
        dict
        """
        return self._get("cloudAci")

    @property
    def cloud_aci_provider(self):
        """
        ### Summary
        Returns cloudAci.provider

        ### Type
        str or None

        ### Example
        None
        """
        return self._get_dict_value_by_keyname(self.cloud_aci, "provider")

    @property
    def cloud_aci_region(self):
        """
        ### Summary
        Returns cloudAci.region

        ### Type
        list

        ### Example
        []
        """
        return self._get_dict_value_by_keyname(self.cloud_aci, "region")

    @property
    def cloud_aci_region_count(self):
        """
        ### Summary
        Returns cloudAci.regionCount

        ### Type
        str or None

        ### Example
        None
        """
        return self._get_dict_value_by_keyname(self.cloud_aci, "regionCount")

    @property
    def cloud_aci_region_name(self):
        """
        ### Summary
        Returns cloudAci.regionName

        ### Type
        str or None

        ### Example
        None
        """
        return self._get_dict_value_by_keyname(self.cloud_aci, "regionName")

    @property
    def cloud_aci_router(self):
        """
        ### Summary
        Returns cloudAci.router

        ### Type
        list

        ### Example
        []
        """
        return self._get_dict_value_by_keyname(self.cloud_aci, "router")

    @property
    def cloud_aci_router_count(self):
        """
        ### Summary
        Returns cloudAci.routerCount

        ### Type
        str or None

        ### Example
        None
        """
        return self._get_dict_value_by_keyname(self.cloud_aci, "routerCount")

    @property
    def cloud_aci_virtnet(self):
        """
        ### Summary
        Returns cloudAci.virtnet

        ### Type
        list

        ### Example
        []
        """
        return self._get_dict_value_by_keyname(self.cloud_aci, "virtnet")

    @property
    def cloud_aci_virtual_network_count(self):
        """
        ### Summary
        Returns cloudAci.virtualNetworkCount

        ### Type
        str or None

        ### Example
        None
        """
        return self._get_dict_value_by_keyname(self.cloud_aci, "virtualNetworkCount")

    @property
    def cloud_aci_vpc(self):
        """
        ### Summary
        Returns cloudAci.vpc

        ### Type
        list

        ### Example
        []
        """
        return self._get_dict_value_by_keyname(self.cloud_aci, "vpc")

    @property
    def cloud_aci_vpc_count(self):
        """
        ### Summary
        Returns cloudAci.vpcCount

        ### Type
        str or None

        ### Example
        None
        """
        return self._get_dict_value_by_keyname(self.cloud_aci, "vpcCount")

    @property
    def controllers(self):
        """
        ### Summary
        Returns controllers

        ### Type
        list of dict
        """
        return self._get("controllers")

    @property
    def dcnm(self):
        """
        ### Summary
        Returns dcnm

        ### Type
        dict
        """
        return self._get("dcnm")

    @property
    def dcnm_fabric_site_id(self):
        """
        ### Summary
        Returns dcnm.dcnmFabricSiteID

        ### Type
        str or None

        ### Example
        "65001"
        """
        return self._get_dict_value_by_keyname(self.dcnm, "dcnmFabricSiteID")

    @property
    def dcnm_fabric_name(self):
        """
        ### Summary
        Returns dcnm.fabricName

        ### Type
        str or None

        ### Example
        "f1"
        """
        return self._get_dict_value_by_keyname(self.dcnm, "fabricName")

    @property
    def dcnm_fabric_read_only(self):
        """
        ### Summary
        Returns dcnm.fabricReadOnly

        ### Type
        bool

        ### Example
        False
        """
        return self._get_dict_value_by_keyname(self.dcnm, "fabricReadOnly")

    @property
    def dcnm_fabric_technology(self):
        """
        ### Summary
        Returns dcnm.fabricTechnology

        ### Type
        str or None

        ### Example
        "VxlanFabric"
        """
        return self._get_dict_value_by_keyname(self.dcnm, "fabricTechnology")

    @property
    def dcnm_fabric_type(self):
        """
        ### Summary
        Returns dcnm.fabricType

        ### Type
        str or None

        ### Example
        "SwitchFabric"
        """
        return self._get_dict_value_by_keyname(self.dcnm, "fabricType")

    @property
    def dcnm_ha(self):
        """
        ### Summary
        Returns dcnm.ha

        ### Type
        dict
        """
        return self._get_dict_value_by_keyname(self.dcnm, "ha")

    @property
    def dcnm_health(self):
        """
        ### Summary
        Returns dcnm.health

        ### Type
        str or None

        ### Example
        None
        """
        return self._get_dict_value_by_keyname(self.dcnm, "health")

    @property
    def dcnm_login_domain(self):
        """
        ### Summary
        Returns dcnm.loginDomain

        ### Type
        str or None

        ### Example
        "DefaultAuth"
        """
        return self._get_dict_value_by_keyname(self.dcnm, "loginDomain")

    @property
    def dcnm_switches(self):
        """
        ### Summary
        Returns dcnm.switches

        ### Type
        list of dict
        """
        return self._get_dict_value_by_keyname(self.dcnm, "switches")

    @property
    def dcnm_switches_by_serial_number(self):
        """
        ### Summary
        Returns dcnm_switches converted to dict and keyed on switch serial_number

        ### Type
        dict
        """
        switches_dict = {}
        switches = self._get_dict_value_by_keyname(self.dcnm, "switches")
        if switches is None:
            return switches_dict
        for switch in switches:
            if switch is None:
                continue
            switch_serial_number = switch.get("sn")
            if switch_serial_number is None:
                continue
            switches_dict[switch_serial_number] = copy.deepcopy(switch)
        return copy.deepcopy(switches_dict)

    @property
    def dcnm_username(self):
        """
        ### Summary
        Returns dcnm.username

        ### Type
        str or None

        ### Example
        None
        """
        return self._get_dict_value_by_keyname(self.dcnm, "username")

    @property
    def disable_polling(self):
        """
        ### Summary
        Returns disablePolling

        ### Type
        bool

        ### Example
        False
        """
        return self._get("disablePolling")

    @property
    def disable_polling_reason(self):
        """
        ### Summary
        Returns disablePollingReason

        ### Type
        str or None

        ### Example
        None
        """
        return self._get("disablePollingReason")

    @property
    def display_name(self):
        """
        ### Summary
        Returns displayName

        ### Type
        str
        """
        return self._get("displayName")

    @property
    def dual_stack_pref_mode(self):
        """
        ### Summary
        Returns dualStackPrefMode

        ### Type
        str
        """
        return self._get("dualStackPrefMode")

    @property
    def fed_info(self):
        """
        ### Summary
        Returns fedInfo

        ### Type
        dict
        """
        return self._get("fedInfo")

    @property
    def fed_info_fed_mem_uuid(self):
        """
        ### Summary
        Returns fedInfo.fedMemUUID

        ### Type
        str or None

        ### Example
        "federation-nd1"
        """
        return self._get_dict_value_by_keyname(self.fed_info, "fedMemUUID")

    @property
    def fed_info_local(self):
        """
        ### Summary
        Returns fedInfo.local

        ### Type
        bool

        ### Example
        True
        """
        return self._get_dict_value_by_keyname(self.fed_info, "local")

    @property
    def internal_onboard(self):
        """
        ### Summary
        Returns internalOnboard

        ### Type
        bool
        """
        return self._get("internalOnboard")

    @property
    def latitude(self):
        """
        ### Summary
        Returns latitude

        ### Type
        str
        """
        return self._get("latitude")

    @property
    def launch_url(self):
        """
        ### Summary
        Returns launchURL

        ### Type
        str
        """
        return self._get("launchURL")

    @property
    def longitude(self):
        """
        ### Summary
        Returns longitude

        ### Type
        str
        """
        return self._get("longitude")

    @property
    def meta(self):
        """
        ### Summary
        Returns meta

        ### Type
        dict
        """
        return self._get("meta")

    @property
    def meta_modified_timestamp(self):
        """
        ### Summary
        Returns meta.modts

        ### Type
        str

        ### Example
        "2024-10-09T19:32:54.867207847Z"
        """
        return self._get_dict_value_by_keyname(self.meta, "modts")

    @property
    def meta_created_timestamp(self):
        """
        ### Summary
        Returns meta.createts

        ### Type
        str

        ### Example
        "2024-10-09T19:32:54.499741517Z"
        """
        return self._get_dict_value_by_keyname(self.meta, "createts")

    @property
    def meta_dn(self):
        """
        ### Summary
        Returns meta.dn

        ### Type
        str

        ### Example
        "ndsites/f2"
        """
        return self._get_dict_value_by_keyname(self.meta, "dn")

    @property
    def meta_type(self):
        """
        ### Summary
        Returns meta.type

        ### Type
        str

        ### Example
        "ndsites"
        """
        return self._get_dict_value_by_keyname(self.meta, "type")

    @property
    def meta_version(self):
        """
        ### Summary
        Returns meta.version

        ### Type
        str or None

        ### Example
        "0"
        """
        return self._get_dict_value_by_keyname(self.meta, "version")

    @property
    def name(self):
        """
        ### Summary
        Returns name

        ### Type
        str or None

        ### Example
        "f2"
        """
        return self._get("name")

    @property
    def notify_reason(self):
        """
        ### Summary
        Returns notifyReason

        ### Type
        str or None

        ### Example
        None
        """
        return self._get("notifyReason")

    @property
    def nxos(self):
        """
        ### Summary
        Returns nxos

        ### Type
        dict
        """
        return self._get("nxos")

    @property
    def nxos_allow_ndi_config(self):
        """
        ### Summary
        Returns nxos.allowNDIConfig

        ### Type
        bool

        ### Example
        True
        """
        return self._get_dict_value_by_keyname(self.nxos, "allowNDIConfig")

    @property
    def nxos_dcnm_fabric_site_id(self):
        """
        ### Summary
        Returns nxos.dcnmFabricSiteID

        ### Type
        str or None

        ### Example
        None
        """
        return self._get_dict_value_by_keyname(self.nxos, "dcnmFabricSiteID")

    @property
    def nxos_fabric_name(self):
        """
        ### Summary
        Returns nxos.fabricName

        ### Type
        str or None

        ### Example
        None
        """
        return self._get_dict_value_by_keyname(self.nxos, "fabricName")

    @property
    def nxos_fabric_read_only(self):
        """
        ### Summary
        Returns nxos.fabricReadOnly

        ### Type
        bool

        ### Example
        False
        """
        return self._get_dict_value_by_keyname(self.nxos, "fabricReadOnly")

    @property
    def nxos_fabric_technology(self):
        """
        ### Summary
        Returns nxos.fabricTechnology

        ### Type
        str or None

        ### Example
        "VxlanFabric"
        """
        return self._get_dict_value_by_keyname(self.nxos, "fabricTechnology")

    @property
    def nxos_fabric_type(self):
        """
        ### Summary
        Returns nxos.fabricType

        ### Type
        str or None

        ### Example
        "SwitchFabric"
        """
        return self._get_dict_value_by_keyname(self.nxos, "fabricType")

    @property
    def nxos_health(self):
        """
        ### Summary
        Returns nxos.health

        ### Type
        str or None

        ### Example
        None
        """
        return self._get_dict_value_by_keyname(self.nxos, "health")

    @property
    def nxos_switches(self):
        """
        ### Summary
        Returns nxos.switches

        ### Type
        list

        ### Example
        []
        """
        return self._get_dict_value_by_keyname(self.nxos, "switches")

    @property
    def polling_detection_done(self):
        """
        ### Summary
        Returns pollingDetectionDone

        ### Type
        bool
        """
        return self._get("pollingDetectionDone")

    @property
    def polling_type(self):
        """
        ### Summary
        Returns pollingType

        ### Type
        str
        """
        return self._get("pollingType")

    @property
    def schema_version(self):
        """
        ### Summary
        Returns schemaversion

        ### Type
        str
        """
        return self._get("schemaversion")

    @property
    def security_domains(self):
        """
        ### Summary
        Returns securityDomains

        ### Type
        list
        """
        return self._get("securityDomains")

    @property
    def site_health(self):
        """
        ### Summary
        Returns siteHealth

        ### Type
        str

        ### Example
        "100.000000"
        """
        return self._get("siteHealth")

    @property
    def site_ip_type(self):
        """
        ### Summary
        Returns siteIPType

        ### Type
        str

        ### Example
        "IPv4"
        """
        return self._get("siteIPType")

    @property
    def site_reachability(self):
        """
        ### Summary
        Returns siteReachabilty

        ### Type
        dict
        """
        return self._get("siteReachabilty")

    @property
    def site_reachability_description(self):
        """
        ### Summary
        Returns siteReachabilty.description

        ### Type
        str or None

        ### Example
        "NDFC Fabric on-boarded internally"
        """
        return self._get_dict_value_by_keyname(self.site_reachability, "description")

    @property
    def site_reachability_node_reachability(self):
        """
        ### Summary
        Returns siteReachabilty.nodeReachability

        ### Type
        list of dict
        """
        return self._get_dict_value_by_keyname(
            self.site_reachability, "nodeReachability"
        )

    @property
    def site_reachability_state(self):
        """
        ### Summary
        Returns siteReachabilty.state

        ### Type
        str or None

        ### Example
        "Up"
        """
        return self._get_dict_value_by_keyname(self.site_reachability, "state")

    @property
    def site_type(self):
        """
        ### Summary
        Returns siteType

        ### Type
        str

        ### Example
        "DCNMNG"
        """
        return self._get("siteType")

    @property
    def upd_switch_time_stamp(self):
        """
        ### Summary
        Returns updSwitchTimeStamp

        ### Type
        str

        ### Example
        "0001-01-01T00:00:00Z"
        """
        return self._get("updSwitchTimeStamp")

    @property
    def upd_time_stamp(self):
        """
        ### Summary
        Returns updTimeStamp

        ### Type
        str

        ### Example
        "0001-01-01T00:00:00Z"
        """
        return self._get("updTimeStamp")

    @property
    def url(self):
        """
        ### Summary
        Returns url

        ### Type
        str

        ### Example
        "apigw.kube-system:443"
        """
        return self._get("url")

    @property
    def use_proxy(self):
        """
        ### Summary
        Returns useProxy

        ### Type
        bool

        ### Example
        False
        """
        return self._get("useProxy")

    @property
    def user_config(self):
        """
        ### Summary
        Returns userConfig

        ### Type
        bool

        ### Example
        False
        """
        return self._get("userConfig")

    @property
    def verify_secure(self):
        """
        ### Summary
        Returns verifySecure

        ### Type
        bool

        ### Example
        False
        """
        return self._get("verifySecure")

    @property
    def filtered_data(self):
        """
        ### Summary
        The DATA portion of the dictionary for the fabric specified with filter.

        ### Raises
        -   ``ValueError`` if:
                -   ``self.filter`` has not been set.

        ### Returns
        - A dictionary of the fabric matching self.filter.
        - ``None``, if the fabric does not exist on the controller.
        """
        method_name = inspect.stack()[0][3]
        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.filter must be set before accessing "
            msg += f"{self.class_name}.filtered_data."
            raise ValueError(msg)
        return self.data_subclass.get(self.filter, None)

    @property
    def filter(self):
        """
        ### Summary
        Set the fabric name to query.

        ### Raises
        None

        ### NOTES
        ``filter`` must be set before accessing this class's properties.
        """
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value
