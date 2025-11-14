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
from pathlib import PurePosixPath

from ..common.api.v1.imagemanagement.rest.discovery.discovery import \
    EpBootflashDiscovery
from ..common.api.v1.imagemanagement.rest.imagemgnt.bootflash.bootflash import \
    EpBootflashInfo
from ..common.conversion import ConversionUtils
from ..common.properties import Properties
from ..common.results import Results
from .convert_file_info_to_target import ConvertFileInfoToTarget


@Properties.add_rest_send
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
    We start with list of targets, where target is a dictionary containing
    a filepath and a supervisor key:

    ```python
    targets = [
        {
            "filepath": "bootflash:/*.txt",
            "supervisor": "active"
        },
        {
            "filepath": "bootflash:/abc.txt",
            "supervisor": "standby"
        }
    ]
    ```

    1.  Create an instance of BootflashInfo() and set the switches
        property to a list of switch ip addresses.
    2.  Set instance.switch_details to the SwitchDetails() class and
        pass it a separate instance of Results() since we don't want
        to save the results of the switch details query.
    3.  Define a list of switch IP addresses and pass this to the
        ``instance.switches`` property.
    4.  Call ``instance.refresh()`` to retrieve switch details for each of the
        switches in the switches.  This is used to convert switch ip address
        to serial_number, which is required by the bootflash-info endpoint,
        defined in ``EpBootflashInfo()``.
    5.  We then call ``instance.refresh_bootflash_info()`` to retrieve
        bootflash contents for each switch in the switches list.
    6.  We can then filter the results by switch (``filter_switch``),
        supervisor (``filter_supervisor``), and filepath (``filter_filepath``).
    7.  ``filter_filepath`` supports file globbing.  Below, we are filtering
        for any file on any partition with a three-letter name and a .txt
        extension.  e.g. bootflash:/abc.txt.
    8.  We call ``instance.build_matches()`` to build a list of files matching
        the filters.
    9.  We call ``instance.results.register_task_result()`` to register the
        results, which creates instance.results.diff, a list of dictionaries
        keyed on the switch ip address.  Each dictionary contains a list of
        matches for that switch.  The matches are dictionaries containing the
        bootflash information for the file.

    ```python
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    instance = BootflashInfo()
    instance.results = Results()

    # BootflashInfo() uses SwitchDetails() to convert
    # switch ip addresses to switch serial numbers since
    # the NDFC API selects switches by serial number.
    instance.switch_details = SwitchDetails()

    # We pass switch_details.results a separate instance of
    # results because we are not interested in its results.
    instance.switch_details.results = Results()
    instance.switches = ["192.168.1.1", "192.168.1.2"]
    instance.refresh()

    # Filters can be added indenpendently of each other.
    # The more filters added, the more specific the results.
    # ``filter_switch`` is limited to the switches in the
    # ``instance.switches`` list, since this is the information
    # that ``instance.refresh`` caches when ``instance.refresh``
    # is called.

    instance.filter_switch = "192.168.1.1"
    instance.filter_supervisor = "active"
    # filter_filepath supports file globbing.
    # The below means "Any file on any partition with a three-letter
    # name and a .txt extension." e.g. bootflash:/abc.txt
    instance.filter_filepath = "*:/???.txt"

    instance.build_matches()
    instance.results.register_task_result()

    # The results can be printed by accessing instance.results.diff.
    # instance.results.diff is a list of dictionaries.  Each dictionary
    # is keyed on the switch ip address and contains a list of matches for
    # that switch.  The matches are dictionaries containing the bootflash
    # information for the file.

    print(f"{json.dumps(instance.results.diff, sort_keys=True, indent=4)}")

    ```

    ### instance.results.diff Structure

    ```json
        "diff": [
            {
                "172.22.150.112": [
                    {
                        "date": "2024-08-06 16:14:59",
                        "device_name": "cvd-1211-spine",
                        "filepath": "bootflash:/bling.txt",
                        "ip_address": "172.22.150.112",
                        "serial_number": "FOX2109PGCS",
                        "size": "2",
                        "supervisor": "active"
                    }
                ],
                "172.22.150.113": [
                    {
                        "date": "2024-08-06 16:15:59",
                        "device_name": "cvd-1212-spine",
                        "filepath": "bootflash:/blong.txt",
                        "ip_address": "172.22.150.113",
                        "serial_number": "FOX2109PGD0",
                        "size": "2",
                        "supervisor": "active"
                    }
                ],
                "sequence_number": 1
            }
        ]
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.action = "bootflash_info"
        self.bootflash_data_map = {}
        self.conversion = ConversionUtils()
        self.convert_file_info_to_target = ConvertFileInfoToTarget()
        self.ep_bootflash_discovery = EpBootflashDiscovery()
        self.ep_bootflash_info = EpBootflashInfo()
        self.info_dict = {}
        self._matches = []

        # Used to collect individual responses and results for each
        # switch in self.switches.  Keyed on switch ip_address.
        # Updated in refresh_bootflash_info().
        self.diff_dict = {}
        self.response_dict = {}
        self.result_dict = {}

        self._rest_send = None
        self._results = None
        self._switch_details = None
        self._switches = None

        self._filter_filepath = None
        self._filter_supervisor = None
        self._filter_switch = None

        self.valid_supervisor = ["active", "standby"]

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

        def raise_value_error_if_not_set(property_name):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{property_name} must be set prior to calling refresh."
            raise ValueError(msg)

        if self.rest_send is None:
            raise_value_error_if_not_set("rest_send")
        if self.results is None:
            raise_value_error_if_not_set("results")
        if self.switch_details is None:
            raise_value_error_if_not_set("switch_details")
        if self.switches is None:
            raise_value_error_if_not_set("switches")

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
        method_name = inspect.stack()[0][3]
        self.info_dict = {}
        self.response_dict = {}
        self.result_dict = {}
        for switch in self.switches:
            self.switch_details.filter = switch
            try:
                serial_number = self.switch_details.serial_number
            except ValueError as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"serial_number not found for switch {switch}. "
                msg += f"Error detail {error}"
                raise ValueError(msg) from error

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
        Verify that mandatory prerequisites are met before calling
        ``build_matches()``.

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

    def match_filter_filepath(self, target):
        """
        ### Summary
        -   Return True if the target's ``filepath`` matches
            ``filter_filepath``.
        -   Return False otherwise.

        ### Raises
        None
        """
        if not self.filter_filepath:
            return False
        posix = PurePosixPath(target.get("filepath"))
        if not posix.match(self.filter_filepath):
            return False
        return True

    def match_filter_supervisor(self, target):
        """
        ### Summary
        -   Return True if the target's ``bootflash_type`` matches
            ``filter_supervisor``.
        -   Return False otherwise.

        ### Raises
        None
        """
        if not self.filter_supervisor:
            return False
        if target.get("supervisor", None) != self.filter_supervisor:
            return False
        return True

    def match_filter_switch(self, target):
        """
        ### Summary
        -   Return True if the target's ``ip_address`` matches
            ``filter_switch``.
        -   Return False otherwise.

        ### Raises
        None
        """
        if not self.filter_switch:
            return False
        if target.get("ip_address", None) != self.filter_switch:
            return False
        return True

    def build_matches(self) -> None:
        """
        ### Summary
        Build a list of matches from the info_dict.

        ### Raises
        None
        """
        method_name = inspect.stack()[0][3]

        self.validate_prerequisites_for_build_matches()
        self._matches = []

        if self.filter_switch not in self.info:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"filter_switch {self.filter_switch} not found in info."
            self.log.debug(msg)
            return

        data = self.info.get(self.filter_switch, {})
        self.bootflash_data_map = data.get("bootFlashDataMap", {})

        for partition in self.bootflash_data_map:
            for file_info in self.bootflash_data_map[partition]:
                self.convert_file_info_to_target.file_info = file_info
                self.convert_file_info_to_target.commit()
                target = self.convert_file_info_to_target.target
                # no need to test match_filter_switch since we have
                # already filtered on the switch above.
                if not self.match_filter_filepath(target):
                    continue
                if not self.match_filter_supervisor(target):
                    continue
                self._matches.append(target)

        diff = {}
        for match in self._matches:
            # convert_file_info_to_target() ensures that match contains
            # ip_address.
            ip_address = match.get("ip_address", None)
            if ip_address not in diff:
                diff[ip_address] = []
            diff[ip_address].append(match)
        self.diff_dict = diff

    @property
    def filter_filepath(self):
        """
        ### Summary
        Return the current ``filter_filepath``.

        ``filter_filepath`` is a file path used to filter the results
        of the query.  This can include file globbing.

        ### Raises
        None

        ### Examples

        -   All txt files in the bootflash directory
            -   instance.filter_filepath = "bootflash:/*.txt"
        -   All txt files on all flash devices
            -   instance.filter_filepath = "*:/*.txt"
        """
        return self._filter_filepath

    @filter_filepath.setter
    def filter_filepath(self, value):
        msg = "ENTERED BootflashQuery.filter_filepath.setter: "
        msg += f"value {value}"
        self.log.debug(msg)
        self._filter_filepath = value

    @property
    def filter_supervisor(self):
        """
        ### Summary
        Return the current ``filter_supervisor``.

        ``filter_supervisor`` is either "active" or "standby" and represents
         the state of the supervisor which hosts ``filepath``.

        ### Raises
        -   ``ValueError`` if:
            -   value is not one of the valid_supervisor values
                "active" or "standby".

        ### Example
        instance.filter_supervisor = "active"
        """
        return self._filter_supervisor

    @filter_supervisor.setter
    def filter_supervisor(self, value):
        if value not in self.valid_supervisor:
            msg = f"{self.class_name}.filter_supervisor.setter: "
            msg += f"value {value} is not a valid value for supervisor. "
            msg += f"Valid values: {','.join(self.valid_supervisor)}."
            raise ValueError(msg)
        self._filter_supervisor = value

    @property
    def filter_switch(self):
        """
        ### Summary
        Return the current ``filter_switch``.

        ``filter_switch`` is a switch ipv4 address used to filter the results
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
    def matches(self):
        """
        ### Summary
        Return a list of file_info dicts that match the query filters.

        ### Raises
        None

        ### Associated key
        None

        ### Example value
        The leading space with ipAddr's value in pre-3.2.1e Nexus Dashboard responses
        is stripped in build_matches() so you won't have to worry about it.

        ```python
        matches = [
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
        ]
        ```
        """
        self.build_matches()
        return self._matches

    # @matches.setter
    # def matches(self, value):
    #     self._matches = value

    @property
    def switch_details(self):
        """
        ### Summary
        Return the switch_details instance

        ### Raises
        -   ``TypeError`` if ``switch_details`` is not an instance of
            ``SwitchDetails()``.
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
        A list of switch ip addresses.

        ### Raises
        - ``TypeError`` if:
            - switches is not a list.
            - switches contains anything other than strings.
        -  ``ValueError`` if:
            - switches list is empty.

        ### Example

        ```python

        instance = BootflashInfo()
        instance.switches = ["192.168.1.1", "192.168.1.2"]
        switches = instance.switches
        ```
        """
        return self._switches

    @switches.setter
    def switches(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "switches must be a list. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}."
            raise TypeError(msg)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "switches must be a list with at least one ip address. "
            msg += f"got {value}."
            raise ValueError(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "switches must be a list of ip addresses. "
                msg += f"got type {type(item).__name__} for "
                msg += f"value {item}."
                raise TypeError(msg)
        self._switches = value
