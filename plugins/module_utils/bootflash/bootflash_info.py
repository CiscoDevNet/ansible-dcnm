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
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.discovery.discovery import \
    EpBootflashDiscovery
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.imagemgnt.bootflash.bootflash import \
    EpBootflashInfo
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results


@Properties.add_results
class BootflashInfo:
    """
    ### Summary
    Retrieve and filter bootflash contents.

    ### Raises
    -   ``ValueError`` if:
            -   params is not set.
            -   switches is not set.
    -   ``TypeError`` if:
            -   switches is not a list.
            -   switches contains anything other than strings.

    ### Usage

    There are two usage scenarios for this class.  The simple use-case is
    to retrieve bootflash information for one or more switches and subsequently
    filter and access it via the class's convenience properties.

    #### Simple Usage

    ```python
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    instance = BootflashQuery()
    instance.results = Results()

    # BootflashInfo() uses SwitchDetails() to convert
    # switch ip addresses to switch serial numbers since
    # the NDFC API selects switches by serial number.
    instance.switch_details = SwitchDetails()

    # We pass switch_details.results a separate instance of
    # results because we are not interested in its results.
    instance.switch_details.results = Results()
    instance.switches = ["192.168.1.1"]
    instance.refresh()

    # Filters can be added indenpendently of each other.
    # The more filters that are added, the more specific the
    # results will be.
    instance.filter_filename = "nxos_image.bin"
    instance.filter_filepath = "bootflash:/"
    instance.filter_partition = "bootflash:"
    instance.filter_supervisor = "active"
    instance.filter_switch = "192.168.1.1"


    # Assuming there was a match for the filters, the following
    # information can be retrieved.  If there was not a match, these
    # properties will return None.

    date = instance.date
    device_name = instance.device_name
    filename = instance.filename
    filepath = instance.filepath
    ip_address = instance.ip_address
    match = instance.match # dictionary containing raw bootflash information
    name = instance.name
    serial_number = instance.serial_number
    size = instance.size
    supervisor = instance.supervisor
    ```

    #### More involved usage

    ```python
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    results = Results()

    instance = BootflashQuery()
    instance.results = Results()

    # BootflashInfo() uses SwitchDetails() to convert
    # switch ip addresses to serial numbers (which is
    # required by the NDFC API).
    instance.switch_details = SwitchDetails()

    # We pass switch_details.results a separate instance of
    # results because we are not interested in its results.
    instance.switch_details.results = Results()

    # We'll retrieve information about two files
    # on each of two switches.
    switches = ["192.168.1.1", 192.168.1.2"]
    files = ["nxos_image.bin", "nxos_image2.bin"]

    instance.switches = switches
    instance.refresh()
    for switch in switches:
        instance.filter_switch = switch
        for target in targets:
            instance.filter_file = target.get("filename")
            instance.build_matches()
            instance.results.register_task_result()

    # The results can be printed by accessing instance.results.diff.
    # instance.results.diff is a list of dictionaries.  Each dictionary
    # is keyed on the switch ip address and contains a list of matches for
    # that switch.  The matches are dictionaries containing the bootflash
    # information for the file.

    print(f"{json.dumps(instance.results.diff, sort_keys=True, indent=4)}")

    # Accessing individual file information for the first switch in the switches
    # array would go something like:

    switch1 = switches[0]
    filename = instance.results.diff[0][switch1][0]["fileName"]
    size = instance.results.diff[0][switch1][0]["size"]

    ```

    ### Structure

    The structure of the info_dict is a list of dictionaries. The structure of
    each dictionary is provided below.

    The observant reader will notice that NDFC inserts a leading space before
    ipAddr's value i.e.

    " 192.168.1.1"

    We strip this space and update the dictionary with the stripped ip_address
    before returning the dictionary to the user and before populating this
    class's associated ip_address property.

    In this class, the property ``supervisor`` is used to access the value of
    ``bootflash_type``.

    ```json
    {
        "bootflash_type": "active",
        "date": "Sep 19 22:20:07 2023",
        "deviceName": "cvd-1212-spine",
        "fileName": "n9000-epld.10.2.5.M.img",
        "filePath": "bootflash:",
        "ipAddr": " 192.168.1.1",
        "name": "bootflash:",
        "serialNumber": "BDY3814QDD0",
        "size": "218233885"
    }
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.action = "bootflash_query"
        self.conversion = ConversionUtils()
        self.ep_bootflash_discovery = EpBootflashDiscovery()
        self.ep_bootflash_info = EpBootflashInfo()

        self.bootflash_data_map = {}
        self.bootflash_space_map = {}
        self.partitions = []

        self.info_dict = {}
        self.matches = []
        self._match = {}
        # Used to collect individual responses and results for each
        # switch in self.switches.  Keyed on switch ip_address.
        # Updated in refresh_bootflash_info().
        self.response_dict = {}
        self.result_dict = {}

        self._results = None
        self._switch_details = None
        self._switches = None

        self._filter_filename = None
        self._filter_filepath = None
        self._filter_partition = None
        self._filter_supervisor = None
        self._filter_switch = None

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED BootflashQuery(): "
        msg += f"action {self.action}, "
        self.log.debug(msg)

    def validate_refresh_parameters(self) -> None:
        """
        ### Summary
        Verify that mandatory prerequisites are met before calling refresh.

        ### Raises
        -   ``ValueError`` if:
                -   rest_send is not set.
                -   results is not set.
                -   switch_details is not set.
                -   switches is not set.
        """
        # pylint: disable=no-member
        method_name = inspect.stack()[0][3]

        def raise_exception(property_name):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{property_name} must be set prior to calling refresh."
            raise ValueError()

        if self.rest_send is None:
            raise_exception("rest_send")
        if self.results is None:
            raise_exception("results")
        if self.switch_details is None:
            raise_exception("switch_details")
        if self.switches is None:
            raise_exception("switches")

    # pylint: disable=no-member
    def refresh(self):
        """
        ### Summary
        Retrieve switch details for each of the switches in self.switches.

        This is used to convert switch ip address to serial_number, which is
        required by EpBootflashInfo().

        ### Raises
        -   ``ValueError`` if:
                -   switches is not set.

        ### Notes
        -   pylint: disable=no-member is needed due to the results property
            being dynamically created by the @Properties.add_results decorator.
        """
        # pylint: disable=no-member
        self.validate_refresh_parameters()

        self.results.action = self.action
        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state

        self.switch_details.rest_send = self.rest_send
        self.switch_details.results = Results()
        self.switch_details.refresh()

        self.refresh_bootflash_info()

    def refresh_bootflash_info(self):
        """
        ### Summary
        Retrieve bootflash information for each switch in self.switches.

        ### Raises
        None
        """
        self.info_dict = {}
        self.response_dict = {}
        self.result_dict = {}
        for switch in self.switches:
            self.switch_details.filter = switch
            serial_number = self.switch_details.serial_number
            if serial_number is None:
                continue

            # rediscover bootflash contents for the switch
            self.ep_bootflash_discovery.serial_number = serial_number
            self.rest_send.path = self.ep_bootflash_discovery.path
            self.rest_send.verb = self.ep_bootflash_discovery.verb
            self.rest_send.commit()

            # retrieve bootflash information for the switch
            self.ep_bootflash_info.serial_number = serial_number
            self.rest_send.path = self.ep_bootflash_info.path
            self.rest_send.verb = self.ep_bootflash_info.verb
            self.rest_send.commit()

            self.info_dict[switch] = copy.deepcopy(
                self.rest_send.response_current.get("DATA", {})
            )
            self.response_dict[switch] = copy.deepcopy(self.rest_send.response_current)
            self.result_dict[switch] = copy.deepcopy(self.rest_send.result_current)

    def validate_prerequisites_for_build_matches(self):
        """
        ### Summary
        Verify that mandatory prerequisites are met before calling _get()

        ### Raises
        -   ``ValueError`` if:
                -   ``refresh`` has not been called.
                -   ``filter_switch`` is not set.
                -   ``filter_file`` is not set.
        """
        method_name = inspect.stack()[0][3]

        if not self.info:
            msg = f"{self.class_name}.{method_name}: "
            msg += "refresh must be called before retrieving bootflash "
            msg += "properties."
            raise ValueError(msg)

    def strip_ipaddr_leading_space(self, item) -> dict:
        """
        ### Summary
        NDFC inserts a leading space before ipAddr's value. Strip
        this, update the dictionary with the stripped ip_address,
        and return the updated dictionary.

        ### Raises
        -   ``ValueError`` if:
            -   ipAddr key is missing from ``item``.
        """
        method_name = inspect.stack()[0][3]
        ipaddr = item.get("ipAddr", None)
        if ipaddr is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"ipAddr not found in item: {item}."
            raise ValueError(msg)
        item.update({"ipAddr": ipaddr.strip()})
        return copy.deepcopy(item)

    def build_matches(self) -> None:
        """
        ### Summary
        Build a list of matches from the info_dict.

        ### Raises
        None
        """
        method_name = inspect.stack()[0][3]

        self.validate_prerequisites_for_build_matches()
        self.matches = []

        if self.filter_switch not in self.info:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"filter_switch {self.filter_switch} not found in info."
            self.log.debug(msg)
            return

        data = self.info.get(self.filter_switch, {})
        self.bootflash_data_map = data.get("bootFlashDataMap", {})
        self.bootflash_space_map = data.get("bootFlashSpaceMap", {})
        self.partitions = data.get("partitions", [])

        for partition in self.partitions:
            if partition not in self.bootflash_data_map:
                continue
            if self.filter_partition and partition != self.filter_partition:
                continue
            for item in self.bootflash_data_map[partition]:
                item_copy = self.strip_ipaddr_leading_space(item)
                if (
                    self.filter_filename
                    and item_copy.get("fileName", None) != self.filter_filename
                ):
                    continue
                if (
                    self.filter_switch
                    and item_copy.get("ipAddr", None) != self.filter_switch
                ):
                    continue
                if (
                    self.filter_filepath
                    and item_copy.get("filePath", None) != self.filter_filepath
                ):
                    continue
                if (
                    self.filter_supervisor
                    and item_copy.get("bootflash_type", None) != self.filter_supervisor
                ):
                    continue
                self.matches.append(item_copy)

        diff = {}
        for match in self.matches:
            ip_address = match.get("ipAddr", None)
            if ip_address is None:
                continue
            if ip_address not in diff:
                diff[ip_address] = []
            diff[ip_address].append(match)
        self.diff_dict = diff

    def build_match(self) -> None:
        """
        ### Summary
        Populate self.match from self.matches.

        ### Raises
        """
        self.build_matches()

        method_name = inspect.stack()[0][3]
        if len(self.matches) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"No matches found for {self.filter_switch} and "
            msg += f"{self.filter_filename}."
            self.log.debug(msg)

        if len(self.matches) > 1:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Multiple matches found for the provided filters. "
            msg += "The properties in this class do not support retrieval "
            msg += "for multiple matches. Use instance.matches to access all "
            msg += "matches and build your own logic to retrieve values from "
            msg += "multiple matches."
            raise ValueError(msg)

        if len(self.matches) == 1:
            self._match = self.matches[0]
        else:
            self._match = {}

    def populate_property(self, search_item):
        """
        ### Summary
        -   If search_item key exists in self.match, return its value.
        -   Return None otherwise.

        ### Raises
        None
        """

        self.build_match()

        if search_item not in self.match:
            return None

        return self.conversion.make_boolean(
            self.conversion.make_none(self.match[search_item])
        )

    def _get(self, search_item):
        """
        ### Summary
        Return the value of item from self.match.

        self.match is the result of matching the query filters set by the user.

        Query filters:

        -   filter_filename
        -   filter_filepath
        -   filter_partition
        -   filter_supervisor
        -   filter_switch

        ### Raises
        -   None
        """
        self.build_matches()
        return self.populate_property(search_item)

    @property
    def date(self):
        """
        ### Summary
        Return the current ``date``.

        ``date`` is the date stamp of the ``filename`` that was matched.

        ### Raises
        None

        ### Associated key
        ``date``

        ### Example value
        ``Sep 19 22:20:07 2023``
        """
        return self._get("date")

    @property
    def device_name(self):
        """
        ### Summary
        Return the current ``device_name``.

        ``device_name`` is the hostname of the device that hosts the
        ``filename`` that was matched.

        ### Raises
        None

        ### Associated key
        ``deviceName``

        ### Example value
        ``cvd-1212-spine``
        """
        return self._get("deviceName")

    @property
    def filename(self):
        """
        ### Summary
        Return the current ``filename``.

        ``filename`` is the name of the file that was matched.

        ### Raises
        None

        ### Associated key
        ``fileName``

        ### Example value
        ``n9000-epld.10.2.5.M.img``
        """
        return self._get("fileName")

    @property
    def filepath(self):
        """
        ### Summary
        Return the current ``filepath``.

        ``filepath`` is the path to the file that was matched.

        ### Raises
        None

        ### Associated key
        ``filePath``

        ### Example filepath
        ``bootflash:``
        """
        return self._get("filePath")

    @property
    def filter_filename(self):
        """
        ### Summary
        Return the current ``filter_filename``.

        ``filter_filename`` is a filename used to filter the results
        of the query.

        ### Raises
        None

        ### Example
        instance.filter_filename = "nxos_image.bin"
        """
        return self._filter_filename

    @filter_filename.setter
    def filter_filename(self, value):
        msg = "ENTERED BootflashQuery.filter_filename.setter: "
        msg += f"value {value}"
        self.log.debug(msg)
        self._filter_filename = value

    @property
    def filter_filepath(self):
        """
        ### Summary
        Return the current ``filter_filepath``.

        ``filter_filepath`` is a file path used to filter the results
        of the query.

        ### Raises
        None

        ### Example
        instance.filter_filepath = "bootflash:/"
        """
        return self._filter_filepath

    @filter_filepath.setter
    def filter_filepath(self, value):
        msg = "ENTERED BootflashQuery.filter_filepath.setter: "
        msg += f"value {value}"
        self.log.debug(msg)
        self._filter_filepath = value

    @property
    def filter_partition(self):
        """
        ### Summary
        Return the current ``filter_partition``.

        ``filter_partition`` is a partition (flash device) used to filter
        the results of the query.

        ### Raises
        None

        ### Example
        instance.filter_partition = "bootflash:"
        """
        return self._filter_partition

    @filter_partition.setter
    def filter_partition(self, value):
        msg = "ENTERED BootflashQuery.filter_partition.setter: "
        msg += f"value {value}"
        self.log.debug(msg)
        self._filter_partition = value

    @property
    def filter_supervisor(self):
        """
        ### Summary
        Return the current ``filter_supervisor``.

        ``filter_supervisor`` is either "active" or "standby" and represents
         the state of the supervisor which hosts filename.

        ### Raises
        None

        ### Example
        instance.filter_supervisor = "active"
        """
        return self._filter_supervisor

    @filter_supervisor.setter
    def filter_supervisor(self, value):
        self._filter_supervisor = value

    @property
    def filter_switch(self):
        """
        ### Summary
        Return the current filter_switch.

        filter_switch is a switch ipv4 address used to filter the results
        of the query.

        ### Raises
        None
        """
        return self._filter_switch

    @filter_switch.setter
    def filter_switch(self, value):
        self._filter_switch = value

    @property
    def info(self):
        """
        ### Summary
        Return the info_dict instance
        """
        return self.info_dict

    @property
    def ip_address(self):
        """
        ### Summary
        Return the current ``ip_address``.

        ``ip_address`` is the ip address associated with the device that hosts
        the ``filename`` that was matched.

        ### Raises
        None

        ### Associated key
        ``ipAddr``

        ### Example value
        ``192.168.1.2``
        """
        return self._get("ipAddr")

    @property
    def match(self):
        """
        ### Summary
        Return the current file information dictionary, if any,
        that matches the query filters.

        ### Raises
        None

        ### Associated key
        None

        ### Example value
        The leading space in ipAddr's value is stripped in build_matches()
        so you won't have to worry about it.

        ```json
        {
            "bootflash_type": "active",
            "date": "Sep 19 22:20:07 2023",
            "deviceName": "cvd-1212-spine",
            "fileName": "n9000-epld.10.2.5.M.img",
            "filePath": "bootflash:",
            "ipAddr": "172.22.150.113",
            "name": "bootflash:",
            "serialNumber": "BDY3814QDD0",
            "size": "218233885"
        }
        ```
        """
        return self._match

    @property
    def name(self):
        """
        ### Summary
        Return the current ``name``.

        ``name`` is the device name on which the file matching
        ``filter_switch`` + ``filter_file`` resides.

        ### Raises
        None

        ### Associated key
        ``name``

        ### Example value
        ``bootflash:``
        """
        return self._get("name")

    @property
    def supervisor(self):
        """
        ### Summary
        Return the state of the ``supervisor`` card on which ``filename``
        resides.

        ``supervisor`` is either "active" or "standby" and represents the
        status of the supervisor on which the ``filename`` resides.

        ### Raises
        None

        ### Associated key
        ``bootflash_type``

        ### Example value
        -   ``active``
        -   ``standby``
        """
        return self._get("bootflash_type")

    @property
    def serial_number(self):
        """
        ### Summary
        Return the current ``serial_number``.

        ``serial_number`` is the serial number of the device on which
        the file matching ``filter_switch`` + ``filter_file`` resides.

        ### Raises
        None

        ### Associated key
        ``serialNumber``

        ### Example value
        ``ABC1234567``
        """
        return self._get("serialNumber")

    @property
    def size(self):
        """
        ### Summary
        Return the current ``size``.

        ``size`` is the file size in bytes of the file matching
        ``filter_switch`` + ``filter_file``.

        ### Raises
        None

        ### Associated key
        ``size``

        ### Example value
        ``218233885``
        """
        return self._get("size")

    @property
    def switch_details(self):
        """
        ### Summary
        Return the switch_details instance

        ### Raises
        -   ``TypeError`` if switch_details is not an instance of SwitchDetails
        """
        return self._switch_details

    @switch_details.setter
    def switch_details(self, value):
        method_name = inspect.stack()[0][3]
        _class_have = None
        _class_need = "SwitchDetails"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value must be an instance of {_class_need}. "
        msg += f"Got value {value} of type {type(value).__name__}."
        try:
            _class_have = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            raise TypeError(msg) from error
        if _class_have != _class_need:
            raise TypeError(msg)
        self._switch_details = value

    @property
    def switches(self):
        """
        ### Summary
        return the switches list

        ### Raises
        -   ``TypeError`` if:
                -   switches is not a list.
                -   switches contains anything other than strings.
        -   ``ValueError`` if:
                -   switches list is empty.
        """
        return self._switches

    @switches.setter
    def switches(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "switches must be a list. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "switches must be a list of at least one ip address. "
            msg += f"got {value}."
            raise ValueError(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "switches must be a list of ip addresses. "
                msg += f"got {type(item).__name__} for "
                msg += f"value {item}"
                raise TypeError(msg)
        self._switches = value
