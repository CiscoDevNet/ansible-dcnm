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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.imagemgnt.bootflash.bootflash import \
    EpBootflashInfo

@Properties.add_params
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
    ```python
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    results = Results()

    instance = BootflashQuery()
    instance.results = results
    instance.switches = ["192.168.1.1", "192.168.1.2"]
    instance.commit()
    diff = instance.results.diff_current # contains the image policy information
    result = instance.results.result_current # contains the result(s) of the query
    response = instance.results.response_current # contains the response(s) from the controller
    ```

    ### Structure

    The structure of the info_dict is a list of dictionaries. Each dictionary
    contains the following keys:

    ```json
    {
        "bootflash_type": "active",
        "date": "Sep 19 22:20:07 2023",
        "deviceName": "cvd-1212-spine",
        "fileName": "n9000-epld.10.2.5.M.img",
        "filePath": "bootflash:",
        "ipAddr": " 172.22.150.113",
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

        self._info_dict = {}
        self.matches = []
        self.match = {}
        self._results = None
        self._switch_details = None
        self._switches = None

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED BootflashQuery(): "
        msg += f"action {self.action}, "
        self.log.debug(msg)


    # pylint: disable=no-member
    def refresh(self):
        """
        ### Summary
        query each of the switches in self.switches

        ### Raises
        -   ``ValueError`` if:
                -   switches is not set.

        ### Notes
        -   pylint: disable=no-member is needed due to the rest_send property
            being dynamically created by the @Properties.add_results decorator.
        """
        method_name = inspect.stack()[0][3]

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling refresh."
            raise ValueError(msg)

        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set prior to calling refresh."
            raise ValueError(msg)

        if self.switch_details is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "switch_details must be set prior to calling refresh."
            raise ValueError(msg)

        if self.switches is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "switches must be set prior to calling refresh."
            raise ValueError(msg)

        self.results.action = self.action
        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state

        self.switch_details.rest_send = self.rest_send
        self.switch_details.results = Results()
        self.switch_details.refresh()

        self.refresh_bootflash_info()

    def refresh_bootflash_info(self):
        method_name = inspect.stack()[0][3]

        self.info_dict = {}
        for switch in self.switches:
            self.switch_details.filter = switch
            serial_number = self.switch_details.serial_number
            if serial_number is None:
                continue
            self.info_dict[switch] = {}
            endpoint = EpBootflashInfo()
            endpoint.serial_number = serial_number
            self.rest_send.path = endpoint.path
            self.rest_send.verb = endpoint.verb
            self.rest_send.commit()
            self.info_dict[switch] = copy.deepcopy(self.rest_send.response_current.get("DATA", {}))

    def validate_prerequisites_for_get(self):
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

        if self.filter_switch is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "filter_switch must be set before "
            msg += f"accessing match properties."
            raise ValueError(msg)

        if self.filter_file is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "filter_file must be set before "
            msg += f"accessing match properties."
            raise ValueError(msg)

    def build_matches(self):
        """
        ### Summary
        Build a list of matches from the info_dict.

        ### Raises
        """
        method_name = inspect.stack()[0][3]

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

        if len(self.partitions) == 0:
            return

        for partition in self.partitions:
            if partition not in self.bootflash_data_map:
                continue
            for item in self.bootflash_data_map[partition]:
                if item.get("fileName", None) != self.filter_file:
                    continue
                self.matches.append(item)

    def populate_property(self, search_item):
        """
        ### Summary
        Populate the property (search_item) from the match.

        ### Raises
        -   ``ValueError`` if:
            -   ``search_item`` is not a key in the match.
        """
        method_name = inspect.stack()[0][3]
        if len(self.matches) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"No matches found for {self.filter_switch} and "
            msg += f"{self.filter_file}."
            self.log.debug(msg)
            return None

        if len(self.matches) > 1:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Multiple matches found for {self.filter_switch} and "
            msg += f"{self.filter_file}."
            self.log.debug(msg)
            return None

        self.match = self.matches[0]

        if search_item not in self.match:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.filter_switch} {self.filter_file} does not have "
            msg += f"a key named {search_item}."
            raise ValueError(msg)

        return self.conversion.make_boolean(
            self.conversion.make_none(self.match[search_item])
        )

    def _get(self, search_item):
        """
        ### Summary
        Return the value of item from the switch and file matching
        ``filter_switch`` and ``filter_file``.

        ### Raises
        -   ``ValueError`` if ``filter_switch`` and ``filter_file`` are
            not set.
        """
        method_name = inspect.stack()[0][3]

        self.validate_prerequisites_for_get()
        self.build_matches()
        return self.populate_property(search_item)

    @property
    def bootflash_type(self):
        """
        ### Summary
        Return the current ``bootflash_type``.

        ``bootflash_type`` is the type of bootflash on which the matching
        file_name resides.

        ### Raises
        None

        ### Associated key
        ``bootflash_type``

        ### Example value
        ``active``
        """
        return self._get("bootflash_type")

    @property
    def date(self):
        """
        ### Summary
        Return the current ``date``.

        ``date`` is the date stamp of the file_name matching filter_switch
        and filter_file.  Associated with key ``date``.

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

        ``device_name`` is the hostname of the device matching filter_switch
        and filter_file.

        ### Raises
        None

        ### Associated key
        ``deviceName``

        ### Example value
        ``cvd-1212-spine``
        """
        return self._get("deviceName")

    @property
    def file_name(self):
        """
        ### Summary
        Return the current ``file_name``.

        ``file_name`` is the name of the file that was matched.

        ### Raises
        None

        ### Associated key
        ``fileName``

        ### Example value
        ``n9000-epld.10.2.5.M.img``
        """
        return self._get("fileName")

    @property
    def file_path(self):
        """
        ### Summary
        Return the current ``file_path``.

        ``file_path`` is the path to the file that was matched
        on ``filter_switch`` + ``filter_file``.

        ### Raises
        None

        ### Associated key
        ``filePath``

        ### Example file_path
        ``bootflash:``
        """
        return self._get("fileName")

    @property
    def filter_file(self):
        """
        ### Summary
        Return the current filter_file.

        filter_file is a filename used to filter the results of the query
        to a file.

        ### Raises
        None 
        """
        return self._filter_file

    @filter_file.setter
    def filter_file(self, value):
        msg = "ENTERED BootflashQuery.filter_file.setter: "
        msg += f"value {value}"
        self.log.debug(msg)
        self._filter_file = value

    @property
    def filter_switch(self):
        """
        ### Summary
        Return the current filter_switch.

        filter_switch is a switch ipv4 address used to filter the results
        of the query to a single switch.

        ### Raises
        None 
        """
        return self._filter_switch

    @filter_switch.setter
    def filter_switch(self, value):
        msg = "ENTERED BootflashQuery.filter_switch.setter: "
        msg += f"value {value}"
        self.log.debug(msg)
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

        ``ip_address`` is ip address associated with the device matching
        ``filter_switch`` and ``filter_file``.

        ### Raises
        None

        ### Associated key
        ``ipAddr``

        ### Example value
        ``192.168.1.2``
        """
        return self._get("ipAddr")

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
        return self._get("fileName")

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
