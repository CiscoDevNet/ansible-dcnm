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

import logging

from ..imagemgnt import ImageMgnt


class Bootflash(ImageMgnt):
    """
    ## api.v1.imagemanagement.rest.imagemgt.bootFlash

    ### Description
    Common methods and properties for Bootflash() subclasses

    ### Path
    ``/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imagemgnt/bootFlash``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.bootflash = f"{self.image_mgmt}/bootFlash"
        msg = "ENTERED api.v1.imagemanagement.rest.imagemgnt.Bootflash()"
        self.log.debug(msg)


class EpBootflashFiles(Bootflash):
    """
    ## api.v1.imagemanagement.rest.imagemgnt.bootflash.EpBootFlashFiles()

    ### Description
    Return endpoint information for bootflash-files.

    ### Raises
    -   None

    ### Path
    -   ``../api/v1/imagemanagement/rest/imagemgnt/bootFlash/bootflash-files``

    ### Verb
    -   DELETE

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpBootflashFiles()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED api.v1.imagemanagement.rest.imagemgnt."
        msg += "BootflashFiles.EpBootflashFiles()"
        self.log.debug(msg)

    @property
    def path(self):
        return f"{self.bootflash}/bootflash-files"

    @property
    def verb(self):
        return "DELETE"


class EpBootflashInfo(Bootflash):
    """
    ## api.v1.imagemanagement.rest.imagemgnt.bootflash.EpBootflashInfo()

    ### Description
    Return endpoint information for bootflash-info.

    ### Raises
    -   ``ValueError`` if:
        -   ``serial_number`` is not set.

    ### Path
    -   ``../api/v1/imagemanagement/rest/imagemgnt/bootFlash/bootflash-info?serialNumber={serial_number}``

    ### Verb
    -   DELETE

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpBootflashInfo()
    instance.serial_number = "1234567890"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED api.v1.imagemanagement.rest.imagemgnt."
        msg += "BootflashFiles.EpBootflashInfo()"
        self.log.debug(msg)

    @property
    def path(self):
        """
        ### Summary
        The endpoint path.

        ### Raises
        -   ``ValueError`` if:
            -   ``serial_number`` is not set.
        """
        if self.serial_number is None:
            raise ValueError("serial_number is required")
        return f"{self.bootflash}/bootflash-info?serialNumber={self.serial_number}"

    @property
    def serial_number(self):
        """
        ### Summary
        The serial number of the switch hosting the bootflash devices.

        ### Raises
        None
        """
        return self._serial_number

    @serial_number.setter
    def serial_number(self, value):
        self._serial_number = value

    @property
    def verb(self):
        """
        ### Summary
        The endpoint verb.
        """
        return "GET"
