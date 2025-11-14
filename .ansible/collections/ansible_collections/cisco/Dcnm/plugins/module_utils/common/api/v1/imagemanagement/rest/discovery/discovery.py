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

from ..rest import Rest


class Discovery(Rest):
    """
    ## api.v1.imagemanagement.rest.discovery.Discovery()

    ### Description
    Common methods and properties for Discovery() subclasses

    ### Path
    ``/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/discovery/``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.discovery = f"{self.rest}/discovery/"
        msg = "ENTERED api.v1.imagemanagement.rest.Discovery()"
        self.log.debug(msg)


class EpBootflashDiscovery(Discovery):
    """
    ## api.v1.imagemanagement.rest.discovery.EpBootflashDiscovery()

    ### Description
    Return endpoint information for ``bootflash-discovery``.

    The ``bootflash-discovery`` endpoint initiates a rediscovery of the
    latest bootflash contents for the switch specified with ``serial_number``.

    ### Raises
    -   ``ValueError`` if:
        -   ``serial_number`` is not set.

    ### Path
    -   ``../api/v1/imagemanagement/rest/discovery/bootflash-discovery``

    ### Verb
    -   GET

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint
    -   serial_number: set the endpoint query string

    ### Usage
    ```python
    instance = EpBootflashFiles()
    instance.serial_number = "1234567890"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.serial_number = None
        msg = "ENTERED api.v1.imagemanagement.rest.discovery."
        msg += "EpBootflashDiscovery()"
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
            msg = f"{self.class_name}.path: serial_number is required."
            raise ValueError(msg)
        return f"{self.discovery}/bootflash-discovery?serialNumber={self.serial_number}"

    @property
    def serial_number(self):
        """
        ### Summary
        The serial number of the switch hosting the bootflash to be rediscovered.

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
