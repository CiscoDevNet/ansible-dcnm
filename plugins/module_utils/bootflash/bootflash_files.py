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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.imagemgnt.bootflash.bootflash import \
    EpBootflashFiles
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.properties import \
    Properties


@Properties.add_rest_send
@Properties.add_results
class BootflashFiles:
    """
    ### Summary
    Delete files from bootflash devices.

    ### Raises
    -   ``ValueError`` if:
            -   ``rest_send`` is not set before calling commit()
            -   ``results`` is not set before calling commit()
            -   ``switch_details`` is not set before calling commit()
            -   payload.deleteFiles is empty when calling commit()
            -   ``bootflash_type`` is not set before calling add_file()
            -   ``file_name`` is not set before calling add_file()
            -   ``file_path`` is not set before calling add_file()
            -   ``ip_address`` is not set before calling add_file()
            -   ``switch_details`` is not set before calling add_file()
    -   ``TypeError`` if:
            -   ``switch_details`` is not an instance of ``SwitchDetails``.
            -   ip_address to serial_number conversion fails.

    ### Usage

    ```python
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    results = Results()

    instance = BootflashFiles()
    instance.results = Results()

    # BootflashFiles() uses SwitchDetails() to convert
    # switch ip addresses to serial numbers (which is
    # required by the NDFC API).
    instance.switch_details = SwitchDetails()

    # We pass switch_details.results a separate instance of
    # results because we are not interested in its results.
    instance.switch_details.results = Results()

    # Delete a file in the root directory of the bootflash
    # on the active supervisor of switch 192.168.1.1:
    instance.bootflash_type = "active"
    instance.file_name = "nxos_image.bin"
    instance.file_path = "bootflash:/mydir"
    instance.ip_address = "192.168.1.1"
    instance.partition = "bootflash:"
    instance.add_file()
    instance.commit()
    ```

    ### Payload Structure

    The structure of the request body to delete bootflash files.

    ```json
    {
        "deleteFiles": [
            {
                "serialNumber": "ABO1234567C",
                "partition": "bootflash:",
                "files": [
                    {
                        "filePath": "bootflash:",
                        "fileName": "20210922_230124_poap_3543_init.log",
                        "fileSize": "1335985152",
                        "bootflashType": "active"
                    }
                ]
            }
        ]
    }
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.action = "bootflash_delete"
        self.conversion = ConversionUtils()
        self.ep_bootflash_info = EpBootflashFiles()

        # Used to collect individual responses and results for each
        # switch in self.switches.  Keyed on switch ip_address.
        # Updated in refresh_bootflash_info().
        self.response_dict = {}
        self.result_dict = {}

        self.ok_to_delete_files_reason = None
        self.payload = {"deleteFiles": []}

        self._bootflash_type = None
        self._file_name = None
        self._file_path = None
        self._file_size = None
        self._ip_address = None

        self.switch_details_refreshed = False

        self._rest_send = None
        self._results = None
        self._switch_details = None

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED BootflashQuery(): "
        msg += f"action {self.action}, "
        self.log.debug(msg)

    def refresh_switch_details(self):
        """
        ### Summary
        If switch details are not already refreshed, refresh them.

        ### Raises
        -   ``ValueError`` if:
                -   switch_details is not set.
        """
        method_name = inspect.stack()[0][3]

        if self.switch_details is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"switch_details must be set before calling {method_name}."
            raise ValueError(msg)

        if self.switch_details_refreshed is False:
            self.switch_details.refresh()
            self.switch_details_refreshed = True

    def ip_address_to_serial_number(self, ip_address):
        """
        ### Summary
        Convert ip_address to serial_number.

        ### Raises
        -   ``ValueError`` if:
                -   switch_details is not set.
        """
        method_name = inspect.stack()[0][3]

        self.refresh_switch_details()

        self.switch_details.filter = ip_address
        try:
            serial_number = self.switch_details.serial_number
        except TypeError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "switch_details.refresh() must be called before calling "
            msg += f"{method_name}. "
            msg += f"Error detail: {error}."
            raise ValueError(msg) from error
        return serial_number

    def ok_to_delete_files(self, ip_address):
        """
        ### Summary
        -   Return True if files can be deleted on the switch with ip_address.
        -   Return False otherwise.

        ### Raises
        None
        """
        self.refresh_switch_details()
        bad_modes = ["inconsistent", "migration"]
        self.switch_details.filter = ip_address
        if self.switch_details.mode in bad_modes:
            reason = f"switch mode is {self.switch_details.mode}"
            self.ok_to_delete_files_reason = reason
            return False
        return True

    def validate_commit_parameters(self) -> None:
        """
        ### Summary
        Verify that mandatory prerequisites are met before calling commit.

        ### Raises
        -   ``ValueError`` if:
                -   rest_send is not set.
                -   results is not set.
                -   switch_details is not set.
                -   payload is not set.
        """
        # pylint: disable=no-member
        method_name = inspect.stack()[0][3]

        def raise_exception(property_name):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{property_name} must be set before calling commit()."
            raise ValueError(f"{msg}")

        if not self.rest_send:
            raise_exception("rest_send")
        if not self.results:
            raise_exception("results")
        if not self.switch_details:
            raise_exception("switch_details")
        if len(self.payload["deleteFiles"]) == 0:
            raise_exception("payload")

    def commit(self):
        """
        ### Summary
        Send the payload to delete files.

        ### Raises
        -   ``ValueError`` if:
                -   Mandatory parameters are not set.

        ### Notes
        -   pylint: disable=no-member is needed due to the results property
            being dynamically created by the @Properties.add_results decorator.
        """
        # pylint: disable=no-member
        self.validate_commit_parameters()

        self.results.action = self.action
        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state

        self.delete_files()

    def delete_files(self):
        """
        ### Summary
        Delete files that have been added with add_files().

        ### Raises
        None
        """
        # pylint: disable=no-member
        self.rest_send.path = self.ep_bootflash_info.path
        self.rest_send.verb = self.ep_bootflash_info.verb
        self.rest_send.payload = self.payload
        self.rest_send.commit()

        self.results.diff_current = copy.deepcopy(self.payload)
        self.results.response_current = copy.deepcopy(self.rest_send.response_current)
        self.results.result_current = copy.deepcopy(self.rest_send.result_current)
        self.results.register_task_result()

    def validate_prerequisites_for_add_file(self):
        """
        ### Summary
        Verify that mandatory prerequisites are met before calling add_file()

        ### Raises
        -   ``ValueError`` if:
                -   ``bootflash_type`` is not set.
                -   ``file_name`` is not set.
                -   ``file_path`` is not set.
                -   ``ip_address`` is not set.
        """
        method_name = inspect.stack()[0][3]

        def raise_exception(property_name):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{property_name} must be set before calling add_file()."
            raise ValueError(f"{msg}")

        if not self.bootflash_type:
            raise_exception("bootflash_type")
        if not self.file_name:
            raise_exception("file_name")
        if not self.file_path:
            raise_exception("file_path")
        if not self.ip_address:
            raise_exception("ip_address")
        if not self.switch_details:
            raise_exception("switch_details")

    def add_file(self):
        """
        ### Summary
        Add a file to the payload.

        ### Raises
        None
        """
        self.validate_prerequisites_for_add_file()

        if not self.ok_to_delete_files(self.ip_address):
            msg = f"Cannot delete files on switch {self.ip_address}. "
            msg += f"Reason: {self.ok_to_delete_files_reason}."
            raise ValueError(msg)

        add_payload = {
            "serialNumber": self.ip_address_to_serial_number(self.ip_address),
            "partition": self.file_path,
            "files": [
                {
                    "filePath": self.file_path,
                    "fileName": self.file_name,
                    # "fileSize": self.file_size,
                    "bootflashType": self.bootflash_type,
                }
            ],
        }

        self.payload["deleteFiles"].append(add_payload)

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
        return self._bootflash_type

    @bootflash_type.setter
    def bootflash_type(self, value):
        self._bootflash_type = value

    @property
    def file_path(self):
        """
        ### Summary
        Return the current ``file_path``.

        ``file_path`` is the path to the file to be deleted.

        ### Raises
        None

        ### Associated key
        ``filePath``

        ### Example values
        -   ``bootflash:``
        -   ``bootflash:/mydir/mysubdir``
        """
        return self._file_path

    @file_path.setter
    def file_path(self, value):
        self._file_path = value

    @property
    def file_name(self):
        """
        ### Summary
        Return the current ``file_name``.

        ``file_name`` is the name of the file to be deleted.

        ### Raises
        None

        ### Associated key
        ``fileName``

        ### Example value
        ``n9000-epld.10.2.5.M.img``
        """
        return self._file_name

    @file_name.setter
    def file_name(self, value):
        self._file_name = value

    @property
    def ip_address(self):
        """
        ### Summary
        The ip address of the switch on which ``file_name`` resides.

        ### Raises
        None

        ### Associated key
        ``serialNumber`` (ip_address is converted to serialNumber)

        ### Example value
        ``192.168.1.2``
        """
        return self._ip_address

    @ip_address.setter
    def ip_address(self, value):
        self._ip_address = value

    @property
    def file_size(self):
        """
        ### Summary
        The file size, in bytes, of ``file_name``.

        ### Raises
        None

        ### Associated key
        ``fileSize``

        ### Example value
        ``218233885``
        """
        return self._file_size

    @file_size.setter
    def file_size(self, value):
        self._file_size = value

    @property
    def switch_details(self):
        """
        ### Summary
        An instance of the ``SwitchDetails()`` class.

        ### Raises
        -   ``TypeError`` if ``switch_details`` is not an instance of
            ``SwitchDetails``.
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
