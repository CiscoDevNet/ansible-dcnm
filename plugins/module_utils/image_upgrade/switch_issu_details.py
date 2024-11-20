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
import logging

from ..common.api.v1.imagemanagement.rest.packagemgnt.packagemgnt import \
    EpIssu
from ..common.conversion import ConversionUtils
from ..common.properties import Properties


@Properties.add_rest_send
@Properties.add_results
class SwitchIssuDetails:
    """
    ### Summary
    Retrieve switch issu details from the controller and provide
    property getters for the switch attributes.

    ### Usage
    See subclasses.

    ### Endpoint
    ```
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/packagemgnt/issu
    ```

    ### Response body
    ```json
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
    }
    ```

    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.action = "switch_issu_details"
        self.conversion = ConversionUtils()
        self.ep_issu = EpIssu()
        self.data = {}
        self._action_keys = set()
        self._action_keys.add("imageStaged")
        self._action_keys.add("upgrade")
        self._action_keys.add("validated")

        self._rest_send = None
        self._results = None

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

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

    def refresh_super(self) -> None:
        """
        ### Summary
        Refresh current issu details from the controller.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        try:
            self.validate_refresh_parameters()
        except ValueError as error:
            raise ValueError(error) from error

        try:
            self.rest_send.path = self.ep_issu.path
            self.rest_send.verb = self.ep_issu.verb

            # We always want to get the issu details from the controller,
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

        self.data = self.rest_send.response_current.get("DATA", {}).get(
            "lastOperDataObject", {}
        )

        diff = {}
        for item in self.data:
            ip_address = item.get("ipAddress")
            if ip_address is None:
                continue
            diff[ip_address] = item

        self.results.action = self.action
        self.results.state = self.rest_send.state
        # Set check_mode to True so that results.changed will be set to False
        # (since we didn't make any changes).
        self.results.check_mode = True
        self.results.diff_current = diff
        self.results.response_current = self.rest_send.response_current
        self.results.result_current = self.rest_send.result_current
        self.results.register_task_result()

        if (
            self.rest_send.result_current["success"] is False
            or self.rest_send.result_current["found"] is False
        ):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Bad result when retriving switch "
            msg += "ISSU details from the controller."
            raise ValueError(msg)

        if self.data is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "The controller has no switch ISSU information."
            raise ValueError(msg)

        if len(self.data) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "The controller has no switch ISSU information."
            raise ValueError(msg)

    @property
    def actions_in_progress(self):
        """
        ### Summary
        -   Return ``True`` if any actions are in progress.
        -   Return ``False`` otherwise.
        """
        for action_key in self._action_keys:
            if self._get(action_key) == "In-Progress":
                return True
        return False

    def _get(self, item):
        """
        ### Summary
        overridden in subclasses
        """

    @property
    def device_name(self):
        """
        ### Summary
        -   Return the ``deviceName`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
            ``device name``, e.g. "cvd-1312-leaf"
        -   ``None``
        """
        return self._get("deviceName")

    @property
    def eth_switch_id(self):
        """
        -   Return the ``ethswitchid`` of the switch with
            ``ip_address``, if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``int()``
        -   ``None``
        """
        return self._get("ethswitchid")

    @property
    def fabric(self):
        """
        -   Return the ``fabric`` name of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   fabric name, e.g. ``myfabric``
        -   ``None``
        """
        return self._get("fabric")

    @property
    def fcoe_enabled(self):
        """
        -   Return whether FCOE is enabled on the switch with
            ``ip_address``, if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``bool()`` (true/false)
        -   ``None``
        """
        return self.conversion.make_boolean(self._get("fcoEEnabled"))

    @property
    def group(self):
        """
        -   Return the ``group`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   group name, e.g. ``mygroup``
        -   ``None``
        """
        return self._get("group")

    @property
    # id is a python keyword, so we can't use it as a property name
    # so we use switch_id instead
    def switch_id(self):
        """
        -   Return the switch ``id`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``int()``
        -   ``None``
        """
        return self._get("id")

    @property
    def image_staged(self):
        """
        -   Return the ``imageStaged`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``Success``
        -   ``Failed``
        -   ``None``
        """
        return self._get("imageStaged")

    @property
    def image_staged_percent(self):
        """
        -   Return the ``imageStagedPercent`` of the switch with
            ``ip_address``, if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``int()`` in range ``0-100``
        -   ``None``
        """
        return self._get("imageStagedPercent")

    @property
    def ip_address(self):
        """
        -   Return the ``ipAddress`` of the switch, if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   switch IP address, e.g. ``192.168.1.1``
        -   ``None``
        """
        return self._get("ipAddress")

    @property
    def issu_allowed(self):
        """
        -   Return the ``issuAllowed`` value of the switch with
            ``ip_address``, if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ?? TODO:3 check this
        -   ``None``
        """
        return self._get("issuAllowed")

    @property
    def last_upg_action(self):
        """
        -   Return the last upgrade action performed on the switch
            with ``ip_address``, if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ?? TODO:3 check this
        -   ``Never``
        -   ``None``
        """
        return self._get("lastUpgAction")

    @property
    def mds(self):
        """
        -   Return whether the switch with ``ip_address`` is an MDS,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``bool()`` (True or False)
        -   ``None``
        """
        return self.conversion.make_boolean(self._get("mds"))

    @property
    def mode(self):
        """
        -   Return the ISSU mode of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``Normal``
        -   ``None``
        """
        return self._get("mode")

    @property
    def model(self):
        """
        -   Return the `model` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   model number e.g. ``N9K-C93180YC-EX``.
        -   ``None``
        """
        return self._get("model")

    @property
    def model_type(self):
        """
        -   Return the ``modelType`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``int()``
        -   ``None``
        """
        return self._get("modelType")

    @property
    def peer(self):
        """
        -   Return the ``peer`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ?? TODO:3 check this
        -   ``None``
        """
        return self._get("peer")

    @property
    def platform(self):
        """
        -   Return the ``platform`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``platform``, e.g. ``N9K``
        -   ``None``
        """
        return self._get("platform")

    @property
    def policy(self):
        """
        -   Return the image ``policy`` attached to the switch with
            ``ip_address``, if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``policy``, e.g. ``NR3F``
        -   ``None``
        """
        return self._get("policy")

    @property
    def reason(self):
        """
        ### Summary
        -   Return the ``reason`` (?) of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``Compliance``
        -   ``Validate``
        -   ``Upgrade``
        -   ``None``
        """
        return self._get("reason")

    @property
    def role(self):
        """
        ### Summary
        -   Return the ``role`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   switch role, e.g. ``leaf``
        -   ``None``
        """
        return self._get("role")

    @property
    def serial_number(self):
        """
        ### Summary
        -   Return the ``serialNumber`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   switch serial number, e.g. ``AB1234567CD``
        -   ``None``
        """
        return self._get("serialNumber")

    @property
    def status(self):
        """
        ### Summary
        -   Return the sync ``status`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Details
        The sync status is the status of the switch with respect to the
        image policy.  If the switch is in sync with the image policy,
        the status is ``In-Sync``.  If the switch is out of sync with
        the image policy, the status is ``Out-Of-Sync``.

        ### Possible values
        -   ``In-Sync``
        -   ``Out-Of-Sync``
        -   ``None``
        """
        return self._get("status")

    @property
    def status_percent(self):
        """
        ### Summary
        -   Return the upgrade (TODO:3 verify this) percentage completion
            of the switch with ``ip_address``, if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``int()`` in range ``0-100``
        -   ``None``
        """
        return self._get("statusPercent")

    @property
    def sys_name(self):
        """
        ### Summary
        -   Return the system name of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``system name``, e.g. ``cvd-1312-leaf``
        -   ``None``
        """
        return self._get("sys_name")

    @property
    def system_mode(self):
        """
        ### Summary
        -   Return the system mode of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``Maintenance`` (TODO:3 verify this)
        -   ``Normal``
        -   ``None``
        """
        return self._get("systemMode")

    @property
    def upgrade(self):
        """
        ### Summary
        -   Return the ``upgrade`` status of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``Success``
        -   ``In-Progress``
        -   ``None``
        """
        return self._get("upgrade")

    @property
    def upg_groups(self):
        """
        ### Summary
        -   Return the ``upgGroups`` (upgrade groups) of the switch with
            ``ip_address``, if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   upgrade group to which the switch belongs e.g. ``LEAFS``
        -   ``None``
        """
        return self._get("upgGroups")

    @property
    def upgrade_percent(self):
        """
        ### Summary
        -   Return the upgrade percent complete of the switch with
            ``ip_address``, if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``int()`` in range 0-100
        -   ``None``
        """
        return self._get("upgradePercent")

    @property
    def validated(self):
        """
        ### Summary
        -   Return the ``validated`` status of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``Failed``
        -   ``Success``
        -   ``None``
        """
        return self._get("validated")

    @property
    def validated_percent(self):
        """
        ### Summary
        -   Return the ``validatedPercent`` complete of the switch
            with ``ip_address``, if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``int()`` in range 0-100
        -   ``None``
        """
        return self._get("validatedPercent")

    @property
    def vdc_id(self):
        """
        ### Summary
        -   Return the ``vdcId`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ''int()''
        -   ``None``
        """
        return self._get("vdcId")

    @property
    def vdc_id2(self):
        """
        ### Summary
        -   Return the ``vdc_id`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   ``int()`` (negative values are valid)
        -   ``None``
        """
        return self._get("vdc_id")

    @property
    def version(self):
        """
        ### Summary
        -   Return the ``version`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Possible values
        -   version, e.g. ``10.3(2)``
        -   ``None``
        """
        return self._get("version")

    @property
    def vpc_peer(self):
        """
        ### Summary
        -   Return the ``vpcPeer`` of the switch with ``ip_address``,
            if it exists.  ``vpcPeer`` is the IP address of the switch's
            VPC peer.
        -   Return ``None`` otherwise.

        ### Possible values
        -   vpc peer e.g.: ``10.1.1.1``
        -   ``None``
        """
        return self._get("vpcPeer")

    @property
    def vpc_role(self):
        """
        ### Summary
        -   Return the ``vpcRole`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### NOTES
            -   Two properties exist for vpc_role in the controller response.
                ``vpc_role`` corresponds to vpcRole.
        ### Possible values
        -   ``primary``
        -   ``secondary``
        -   ``none`
                -   This will be translated to ``None``
        -   ``none established``
                -   TODO:3 verify this
        -   ``primary, operational secondary``
                -   TODO:3 verify this
        -   ``None``
                - python NoneType
        """
        return self._get("vpcRole")

    @property
    def vpc_role2(self):
        """
        ### Summary
        Return the ``vpc_role`` of the switch with ``ip_address``,
            if it exists.
        -   Return ``None`` otherwise.

        ### Notes
        -   Two properties exist for vpc_role in the controller response.
            vpc_role2 corresponds to vpc_role.

        ### Possible values
        -   ``primary``
        -   ``secondary``
        -   ``none`
                -   This will be translated to ``None``
        -   ``none established``
                -   TODO:3 verify this
        -   ``primary, operational secondary``
                -   TODO:3 verify this
        -   ``None``
                - python NoneType
        """
        return self._get("vpc_role")


class SwitchIssuDetailsByIpAddress(SwitchIssuDetails):
    """
    ### Summary
    Retrieve switch issu details from the controller and provide property
    getters for the switch attributes retrieved by ip_address.

    ### Raises
    -   ``ValueError`` if:
            -   ``filter`` is not set before accessing properties.

    ### Usage

    ```python
    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = SwitchIssuDetailsByIpAddress()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    instance.filter = "10.1.1.1"
    image_staged = instance.image_staged
    image_upgraded = instance.image_upgraded
    serial_number = instance.serial_number
    ### etc...
    ```

    See SwitchIssuDetails for more details.
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.data_subclass = {}
        self._filter = None

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

    def refresh(self):
        """
        ### Summary
        Refresh ip_address current issu details from the controller.

        ### Raises
        None
        """
        self.refresh_super()
        method_name = inspect.stack()[0][3]
        self.action = "switch_issu_details_by_ip_address"

        self.data_subclass = {}
        for switch in self.rest_send.response_current["DATA"]["lastOperDataObject"]:
            self.data_subclass[switch["ipAddress"]] = switch

    def _get(self, item):
        """
        ### Summary
        Return the value of the switch property matching self.filter.

        ### Raises
        -   ``ValueError`` if:
                -   ``filter`` is not set before accessing properties.
                -   ``filter`` does not exist on the controller.
                -   ``filter`` references an unknown property name.
        """
        method_name = inspect.stack()[0][3]

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a switch ipAddress "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} does not exist on the controller."
            raise ValueError(msg)

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(self.data_subclass[self.filter].get(item))
        )

    @property
    def filtered_data(self):
        """
        ### Summary
        -   Return a dictionary of the switch matching ``filter``.
        -   Return ``None`` if the switch does not exist on the controller.
        """
        return self.data_subclass.get(self.filter)

    @property
    def filter(self):
        """
        ### Summary
        Set the ``ipv4_address`` of the switch to query.

        ``filter`` needs to be set before accessing this class's properties.
        """
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value


class SwitchIssuDetailsBySerialNumber(SwitchIssuDetails):
    """
    ### Summary
    Retrieve switch issu details from the controller and provide property
    getters for the switch attributes retrieved by serial_number.

    ### Usage

    ```python
    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = SwitchIssuDetailsBySerialNumber()
    instance.rest_send = rest_send
    instance.results = Results()
    instance.refresh()
    instance.filter = "FDO211218GC"
    image_staged = instance.image_staged
    image_upgraded = instance.image_upgraded
    ip_address = instance.ip_address
    # etc...
    ```
    See SwitchIssuDetails for more details.
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]
        self.action = "switch_issu_details_by_serial_number"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.data_subclass = {}
        self._filter = None

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

    def refresh(self):
        """
        ### Summary
        Refresh serial_number current issu details from the controller.

        ### Raises
        None
        """
        self.refresh_super()
        method_name = inspect.stack()[0][3]

        self.data_subclass = {}
        for switch in self.rest_send.response_current["DATA"]["lastOperDataObject"]:
            self.data_subclass[switch["serialNumber"]] = switch

    def _get(self, item):
        """
        ### Summary
        Return the value of the switch property matching self.filter.

        ### Raises
        -   ``ValueError`` if:
                -   ``filter`` is not set before accessing properties.
                -   ``filter`` does not exist on the controller.
                -   ``filter`` references an unknown property name.
        """
        method_name = inspect.stack()[0][3]

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a switch serialNumber "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} does not exist "
            msg += "on the controller."
            raise ValueError(msg)

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(self.data_subclass[self.filter].get(item))
        )

    @property
    def filtered_data(self):
        """
        ### Summary
        -   Return a dictionary of the switch matching self.serial_number.
        -   Return ``None`` if the switch does not exist on the controller.

        ### Raises
        None
        """
        return self.data_subclass.get(self.filter)

    @property
    def filter(self):
        """
        ### Summary
        Set the serial_number of the switch to query.

        ``filter`` needs to be set before accessing this class's properties.

        ### Raises
        None
        """
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value


class SwitchIssuDetailsByDeviceName(SwitchIssuDetails):
    """
    ### Summary
    Retrieve switch issu details from the controller and provide property
    getters for the switch attributes retrieved by ``device_name``.

    ### Raises
    -   ``ValueError`` if:
            -   ``filter`` is not set before calling refresh().

    ### Usage

    ```python
    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module

    rest_send = RestSend(params)
    rest_send.sender = sender
    rest_send.response_handler = ResponseHandler()

    instance = SwitchIssuDetailsByDeviceName()
    instance.refresh()
    instance.filter = "leaf_1"
    image_staged = instance.image_staged
    image_upgraded = instance.image_upgraded
    ip_address = instance.ip_address
    # etc...
    ```

    See SwitchIssuDetails for more details.
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]
        self.action = "switch_issu_details_by_device_name"

        self.data_subclass = {}
        self._filter = None

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

    def refresh(self):
        """
        ### Summary
        Refresh device_name current issu details from the controller.

        ### Raises
        None
        """
        self.refresh_super()
        method_name = inspect.stack()[0][3]

        self.data_subclass = {}
        for switch in self.rest_send.response_current["DATA"]["lastOperDataObject"]:
            self.data_subclass[switch["deviceName"]] = switch

    def _get(self, item):
        """
        ### Summary
        Return the value of the switch property matching self.filter.

        ### Raises
        -   ``ValueError`` if:
                -   ``filter`` is not set before accessing properties.
                -   ``filter`` does not exist on the controller.
                -   ``filter`` references an unknown property name.
        """
        method_name = inspect.stack()[0][3]

        if self.filter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "set instance.filter to a switch deviceName "
            msg += f"before accessing property {item}."
            raise ValueError(msg)

        if self.data_subclass.get(self.filter) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} does not exist "
            msg += "on the controller."
            raise ValueError(msg)

        if self.data_subclass[self.filter].get(item) is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter} unknown property name: {item}."
            raise ValueError(msg)

        return self.conversion.make_none(
            self.conversion.make_boolean(self.data_subclass[self.filter].get(item))
        )

    @property
    def filtered_data(self):
        """
        ### Summary
        -   Return a dictionary of the switch matching ``filter``.
        -   Return ``None`` if the switch does not exist on the
            controller.
        """
        return self.data_subclass.get(self.filter)

    @property
    def filter(self):
        """
        ### Summary
        Set the device_name of the switch to query.

        ``filter`` needs to be set before accessing this class's properties.
        """
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value
