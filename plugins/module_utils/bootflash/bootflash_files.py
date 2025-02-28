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

from ..common.api.v1.imagemanagement.rest.imagemgnt.bootflash.bootflash import \
    EpBootflashFiles
from ..common.conversion import ConversionUtils
from ..common.properties import Properties


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
            -   ``filename`` is not set before calling add_file()
            -   ``filepath`` is not set before calling add_file()
            -   ``ip_address`` is not set before calling add_file()
            -   ``supervisor`` is not set before calling add_file()
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
    instance.supervisor = "active"
    instance.filename = "nxos_image.bin"
    instance.filepath = "bootflash:/mydir"
    instance.ip_address = "192.168.1.1"
    instance.partition = "bootflash:"
    # optional
    # instance.target = target_dict # see target property for details
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
        # self.diff is keyed on switch ip_address and is updated
        # in self.update_diff().
        self.diff = {}
        self.ep_bootflash_files = EpBootflashFiles()

        self.ok_to_delete_files_reason = None
        self.mandatory_target_keys = [
            "filepath",
            "ip_address",
            "serial_number",
            "supervisor",
        ]
        self.payload = {"deleteFiles": []}
        self.switch_details_refreshed = False

        self._filename = None
        self._filepath = None
        self._ip_address = None
        self._partition = None
        self._rest_send = None
        self._results = None
        self._supervisor = None
        self._switch_details = None
        self._target = None

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
                -   ``switch_details`` is not set.
                -   ``rest_send`` is not set.
        """
        method_name = inspect.stack()[0][3]

        def raise_exception(property_name):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{property_name} must be set before calling {method_name}."
            raise ValueError(f"{msg}")

        if self.switch_details is None:
            raise_exception("switch_details")
        # pylint: disable=no-member
        if self.rest_send is None:
            raise_exception("rest_send")

        if self.switch_details_refreshed is False:
            self.switch_details.rest_send = self.rest_send
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
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{error}"
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
        if self.payload["deleteFiles"]:
            self.rest_send.path = self.ep_bootflash_files.path
            self.rest_send.verb = self.ep_bootflash_files.verb
            self.rest_send.payload = self.payload
            self.rest_send.commit()
            self.results.response_current = copy.deepcopy(
                self.rest_send.response_current
            )
            self.results.result_current = copy.deepcopy(self.rest_send.result_current)
        else:
            self.results.result_current = {"success": True, "changed": False}
            self.results.response_current = {
                "MESSAGE": "No files to delete.",
                "RETURN_CODE": 200,
            }

        self.results.diff_current = copy.deepcopy(self.diff)
        self.results.register_task_result()

    def validate_prerequisites_for_add_file(self):
        """
        ### Summary
        Verify that mandatory prerequisites are met before calling add_file()

        ### Raises
        -   ``ValueError`` if:
                -   ``filename`` is not set.
                -   ``filepath`` is not set.
                -   ``ip_address`` is not set.
                -   ``supervisor`` is not set.
                -   ``switch_details`` is not set.
                -   ``target`` is not set.
        """
        method_name = inspect.stack()[0][3]

        def raise_exception(property_name):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{property_name} must be set before calling add_file()."
            raise ValueError(f"{msg}")

        if not self.filename:
            raise_exception("filename")
        if not self.filepath:
            raise_exception("filepath")
        if not self.ip_address:
            raise_exception("ip_address")
        if not self.supervisor:
            raise_exception("supervisor")
        if not self.switch_details:
            raise_exception("switch_details")
        if not self.target:
            raise_exception("target")

    def partition_and_serial_number_exist_in_payload(self):
        """
        ### Summary
        -   Return True if the partition and serialNumber associated with the
            file exist in the payload.
        -   Return False otherwise.

        ### Raises
        None

        ### payload Structure

        "deleteFiles": [
            {
                "files": [
                    {
                        "bootflashType": "active",
                        "fileName": "bar.txt",
                        "filePath": "bootflash:"
                    }
                ],
                "partition": "bootflash:",
                "serialNumber": "FOX2109PGCS"
            },
            {
                "files": [
                    {
                        "bootflashType": "active",
                        "fileName": "black.txt",
                        "filePath": "bootflash:"
                    }
                ],
                "partition": "bootflash:",
                "serialNumber": "FOX2109PGD0"
            }
        ]
        """
        found = False
        for item in self.payload["deleteFiles"]:
            serial_number = item.get("serialNumber")
            partition = item.get("partition")
            if serial_number != self.ip_address_to_serial_number(self.ip_address):
                continue
            if partition != self.partition:
                continue
            found = True
            break
        return found

    def add_file_to_existing_payload(self):
        """
        ### Summary
        Add a file to the payload if the following are true:
        -   The serialNumber and partition associated with the file exist in
            the payload.
        -   The file does not already exist in the files list for that
            serialNumber and partition.

        ### Raises
        None

        ### Details
        We are looking at the following structure.

        ```json
        {
            "deleteFiles": [
                {
                    "files": [
                        {
                            "bootflashType": "active",
                            "fileName": "air.txt",
                            "filePath": "bootflash:"
                        },
                        {
                            "bootflashType": "active",
                            "fileName": "earth.txt",
                            "filePath": "bootflash:"
                        },
                    ],
                    "partition": "bootflash:",
                    "serialNumber": "FOX2109PGCS"
                },
            ]
        }
        """
        for item in self.payload["deleteFiles"]:
            serial_number = item.get("serialNumber")
            partition = item.get("partition")
            if serial_number != self.ip_address_to_serial_number(self.ip_address):
                continue
            if partition != self.partition:
                continue
            files = item.get("files")
            for file in files:
                if (
                    file.get("fileName") == self.filename
                    and file.get("bootflashType") == self.supervisor
                ):
                    return
            files.append(
                {
                    "bootflashType": self.supervisor,
                    "fileName": self.filename,
                    "filePath": self.filepath,
                }
            )
            item.update({"files": files})

    def add_file_to_payload(self):
        """
        ### Summary
        Add a file to the payload if the serialNumber and partition do not
        yet exist in the payload.

        ### Raises
        None
        """
        if not self.partition_and_serial_number_exist_in_payload():
            add_payload = {
                "serialNumber": self.ip_address_to_serial_number(self.ip_address),
                "partition": self.partition,
                "files": [
                    {
                        "bootflashType": self.supervisor,
                        "fileName": self.filename,
                        "filePath": self.filepath,
                    }
                ],
            }
            self.payload["deleteFiles"].append(add_payload)
        else:
            self.add_file_to_existing_payload()

    def add_file(self):
        """
        ### Summary
        Add a file to the payload.

        ### Raises
        -   ``ValueError`` if:
                -   The switch does not allow file deletion.
        """
        method_name = inspect.stack()[0][3]
        self.validate_prerequisites_for_add_file()

        if not self.ok_to_delete_files(self.ip_address):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Cannot delete files on switch {self.ip_address}. "
            msg += f"Reason: {self.ok_to_delete_files_reason}."
            raise ValueError(msg)

        self.add_file_to_payload()
        self.update_diff()

    def update_diff(self):
        """
        ### Summary
        Update ``diff`` with ``target``.

        ### Raises
        None

        ### Notes
        -   ``target`` has already been validated to be set (not None) in
            ``validate_prerequisites_for_add_file()``.
        -   ``target`` has already been validated to be a dictionary and to
            contain ``ip_address`` in ``target.setter``.
        """
        ip_address = self.target.get("ip_address")
        if ip_address not in self.diff:
            self.diff[ip_address] = []
        self.diff[ip_address].append(self.target)

    @property
    def filepath(self):
        """
        ### Summary
        Return the current ``filepath``.

        ``filepath`` is the path to the file to be deleted.

        ### Raises
        None

        ### Associated key
        ``filePath``

        ### Example values
        -   ``bootflash:``
        -   ``bootflash:/mydir/mysubdir/``
        """
        return self._filepath

    @filepath.setter
    def filepath(self, value):
        self._filepath = value

    @property
    def filename(self):
        """
        ### Summary
        Return the current ``filename``.

        ``filename`` is the name of the file to be deleted.

        ### Raises
        None

        ### Associated key
        ``fileName``

        ### Example value
        ``n9000-epld.10.2.5.M.img``
        """
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def ip_address(self):
        """
        ### Summary
        The ip address of the switch on which ``filename`` resides.

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
    def partition(self):
        """
        ### Summary
        The partition on which ``filename`` resides.

        ### Raises
        None

        ### Associated key
        ``partition``

        ### Example value
        ``bootflash:``
        """
        return self._partition

    @partition.setter
    def partition(self, value):
        self._partition = value

    @property
    def supervisor(self):
        """
        ### Summary
        Return the current ``supervisor``.

        ``supervisor`` is the switch supervisor card (active or standby)
        on which ``filename`` resides.

        ### Raises
        None

        ### Associated key
        ``bootflashType``

        ### Example values
        -   ``active``
        -   ``standby``
        """
        return self._supervisor

    @supervisor.setter
    def supervisor(self, value):
        self._supervisor = value

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

    @property
    def target(self):
        """
        ### Summary
        ``target`` is a dictionary that is used to set the diff passed to
        Results.

        ``target`` is appended to a list of targets in
        ``BootflashFiles().add_file()``, so must be passed for each file
        to be deleted.  See Usage example in the class docstring.

        ### ``target`` Structure
        ```json
        {
            "date": "2023-09-19 22:20:07",
            "device_name": "cvd-1212-spine",
            "filepath": "bootflash:/n9000-epld.10.2.5.M.img",
            "ip_address": "192.168.1.1",
            "serial_number": "BDY3814QDD0",
            "size": "218233885",
            "supervisor": "active"
        }
        ```

        ### Raises
        -   ``TypeError`` if:
                -   ``target`` is not a dictionary.
        -   ``ValueError`` if:
                -   ``target`` is missing a mandatory key.

        ### Associated key
        None

        ### Notes
        1.  Since (at least with the dcnm_bootflash module) the
            user references switches using ip_address, and the NDFC
            bootflash-files payload includes only serialNumber, we
            decided to use ``target`` as the diff since it contains the
            ip_address and serial_number (as well as the size, date
            etc, which are potentially more useful than the info in
            the payload.
        2.  ``BootflashFiles()`` requires that the ``ip_address`` key
            be present in target, since it uses ``ip_address`` as the key
            for the diff.  Of the other fields, we also require that filepath,
            serial_number and supervisor are present since they add value
            to the diff.  The other fields shown above SHOULD be included
            but their absence will not raise an error.
        """
        return self._target

    @target.setter
    def target(self, value):
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "

        if not isinstance(value, dict):
            msg += "target must be a dictionary. "
            msg += f"Got type {type(value).__name__} for value {value}."
            raise TypeError(msg)
        for key in self.mandatory_target_keys:
            if value.get(key) is None:
                msg += f"{key} key missing from value {value}."
                raise ValueError(msg)
        self._target = value
