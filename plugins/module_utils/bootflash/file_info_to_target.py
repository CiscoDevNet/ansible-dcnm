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
from datetime import datetime
from pathlib import PurePosixPath


class FileInfoToTarget:
    """
    ### Summary
    Build a target dictionary from a ``file_info`` dictionary.

    Convert ``file_info`` into ``Target Structure``.

    ### Raises

    ### ``file_info`` (from bootflash-info endpoint response)
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

    ### ``target`` Structure
    ```json
    {
        "filepath": "bootflash:/n9000-epld.10.2.5.M.img",
        "supervisor": "active"
        "ip_address": "192.168.1.1"
        "serial_number": "BDY3814QDD0"
    }
    ```

    ### Usage
    ```python
    instance = FileInfoToTarget()
    instance.file_info = {
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
    instance.commit()
    print(instance.target)
    ```

    ### Output
    ```json
    {
        "filepath": "bootflash:/n9000-epld.10.2.5.M.img",
        "supervisor": "active"
    }
    ```
    """

    def __init__(self) -> None:
        self.class_name = self.__class__.__name__

        self.timestamp_format = "%b %d %H:%M:%S %Y"
        self._file_info = None
        self._filename = None
        self._filepath = None
        self._ip_address = None
        self._serial_number = None
        self._supervisor = None
        self._target = None

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED FileInfoToTarget(): "
        self.log.debug(msg)

    def commit(self) -> None:
        """
        ### Summary
        Given ``file_info``, which is the information for a single file from
        the bootflash-info endpoint response, build a ``target`` dictionary.

        1.  Build a Posix path ``filepath`` from the ``file_info`` dictionary.
        2.  Add ``bootflash_type`` value as the value for
            ``self.target.supervisor``.
        3. Add ip_address and serial_number to the target dictionary.

        ### Raises
        -   ``ValueError`` if:
            -   ``target`` cannot be built from ``file_info``.

        ### ``file_info`` (from bootflash-info endpoint response)
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

        ### ``target`` Structure
        ```json
        {
            "date":
            "device_name": "cvd-1212-spine",
            "filepath": "bootflash:/n9000-epld.10.2.5.M.img",
            "ip_address": "192.168.1.1",
            "serial_number": "BDY3814QDD0",
            "size": "218233885",
            "supervisor": "active"
        }
        ```

        """
        method_name = inspect.stack()[0][3]

        def raise_error(msg):
            raise ValueError(f"{self.class_name}.{method_name}: {msg}")

        try:
            posixpath = PurePosixPath(self.name, self.filename)
        except TypeError as error:
            msg = "Could not build PosixPath from filepath and filename. "
            msg += f"filepath: {self.filepath}, filename: {self.filename}. "
            msg += f"Error detail: {error}"
            raise_error(msg)

        try:
            self.target = {
                "date": str(self.date),
                "device_name": self.device_name,
                "filepath": str(PurePosixPath(posixpath)),
                "ip_address": self.ip_address,
                "serial_number": self.serial_number,
                "size": self.size,
                "supervisor": self.supervisor,
            }
        except (TypeError, ValueError) as error:
            msg = "Could not build target from file_info. "
            msg = f"{self.file_info}. "
            msg += f"Error detail: {error}"
            raise_error(msg)

    def _get(self, key):
        """
        ### Summary
        Get the value of a key from the ``file_info`` dictionary.

        ### Raises
        -   ``ValueError`` if:
            -   ``file_info`` has not been set before calling _get.
            -   ``key`` is not in the target dictionary.
        """
        method_name = inspect.stack()[0][3]

        def raise_error(msg):
            raise ValueError(f"{self.class_name}.{method_name}: {msg}")

        if self.file_info is None:
            msg = "file_info must be set before calling ``_get()``."
            raise_error(msg)

        if key not in self.file_info:
            msg = f"Missing key {key} in file_info: {self.file_info}."
            raise_error(msg)

        return self.file_info.get(key)

    @property
    def file_info(self):
        """
        ### Summary
        A single file dictionary from the bootflash-info endpoint response.

        ### Raises
        -   ``ValueError`` if:
            -   ``file_info`` is not a dictionary.
            -   ``file_info`` does not contain the requisite keys.

        ### Expected Structure
        This class uses the following keys from the file_info dictionary:
        -   fileName
        -   filePath
        -   bootflash_type

        ### Example
        ```json
        {
            "bootflash_type": "active",
            "date": "Sep 19 22:20:07 2023",
            "deviceName": "cvd-1212-spine",
            "fileName": "n9000-epld.10.2.5.M.img",
            "filePath": "bootflash:",
            "ipAddr": "192.168.1.1",
            "name": "bootflash:",
            "serialNumber": "BDY3814QDD0",
            "size": "218233885"
        }
        ```
        """
        return self._file_info

    @file_info.setter
    def file_info(self, value):
        self._file_info = value

    @property
    def date(self):
        """
        ### Summary
        The value of ``date`` from the ``file_info`` dictionary
        converted to a ``datetime`` object.  The string representation of
        this object will be "YYYY-MM-DD HH:MM:SS".

        ### Raises
        -   ``ValueError`` if:
            -   ``file_info`` has not been set before accessing.
            -   ``date`` is not in the ``file_info`` dictionary.
            -   ``date`` cannot be converted to a datetime object.
        """
        method_name = inspect.stack()[0][3]
        try:
            _date = datetime.strptime(self._get("date"), self.timestamp_format)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg = "Could not convert date to datetime object. "
            msg += f"date: {self._get('date')}. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error
        return _date

    @property
    def device_name(self):
        """
        ### Summary
        The value of ``deviceName`` from the ``file_info`` dictionary.

        ### Raises
        ``ValueError`` if:
        -   ``file_info`` has not been set before accessing.
        -   ``deviceName`` is not in the ``file_info`` dictionary.
        """
        return self._get("deviceName")

    @property
    def filename(self):
        """
        ### Summary
        The value of ``fileName`` from the ``file_info`` dictionary.

        ### Raises
        ``ValueError`` if:
        -   ``file_info`` has not been set before accessing.
        -   ``fileName`` is not in the ``file_info`` dictionary.
        """
        return self._get("fileName")

    @property
    def filepath(self):
        """
        ### Summary
        The value of ``filePath`` from the ``file_info`` dictionary.

        ### Raises
        ``ValueError`` if:
        -   ``file_info`` has not been set before accessing.
        -   ``filePath`` is not in the ``file_info`` dictionary.
        """
        return self._get("filePath")

    @property
    def ip_address(self):
        """
        ### Summary
        The stripped value of ``ipAddr`` from the ``file_info`` dictionary.

        ### Raises
        ``ValueError`` if:
        -   ``file_info`` has not been set before accessing.
        -   ``ipAddr`` is not in the ``file_info`` dictionary.
        """
        return self._get("ipAddr").strip()

    @property
    def name(self):
        """
        ### Summary
        The value of ``name`` from the ``file_info`` dictionary.

        ### Raises
        ``ValueError`` if:
        -   ``file_info`` has not been set before accessing.
        -   ``name`` is not in the ``file_info`` dictionary.
        """
        return self._get("name")

    @property
    def serial_number(self):
        """
        ### Summary
        The value of ``serialNumber`` from the ``file_info`` dictionary.

        ### Raises
        ``ValueError`` if:
        -   ``file_info`` has not been set before accessing.
        -   ``serialNumber`` is not in the ``file_info`` dictionary.
        """
        return self._get("serialNumber")

    @property
    def size(self):
        """
        ### Summary
        The value of ``size`` from the ``file_info`` dictionary.

        ### Raises
        ``ValueError`` if:
        -   ``file_info`` has not been set before accessing.
        -   ``size`` is not in the ``file_info`` dictionary.
        """
        return self._get("size")

    @property
    def target(self):
        """
        ### Summary
        The target dictionary built from the ``file_info`` dictionary.

        ### Raises
        ``ValueError`` if:
        -   ``commit()`` has not been called before accessing.
        """
        if self._target is None:
            msg = f"{self.class_name}.target: "
            msg += "target has not been built. Call commit() before accessing."
            raise ValueError(msg)
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    @property
    def supervisor(self):
        """
        ### Summary
        The value of ``bootflash_type`` from the ``file_info`` dictionary.

        ### Raises
        ``ValueError`` if:
        -   ``file_info`` has not been set before accessing.
        -   ``bootflash_type`` is not in the ``file_info`` dictionary.
        """
        return self._get("bootflash_type")
