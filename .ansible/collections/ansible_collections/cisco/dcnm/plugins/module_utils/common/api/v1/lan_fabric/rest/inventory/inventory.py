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
# pylint: disable=line-too-long
from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

import logging

from ..rest import Rest


class Inventory(Rest):
    """
    ## api.v1.lan_fabric.rest.inventory.Inventory()

    ### Description
    Common methods and properties for Inventory() subclasses.

    ### Path
    -   ``/api/v1/lan-fabric/rest/inventory``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.inventory = f"{self.rest}/inventory"
        msg = f"ENTERED api.v1.lan_fabric.rest.inventory.{self.class_name}"
        self.log.debug(msg)
        self._build_properties()

    def _build_properties(self):
        """
        Populate properties specific to this class and its subclasses.
        """


class EpAllSwitches(Inventory):
    """
    ##api.v1.lan_fabric.rest.inventory.EpAllSwitches()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/api/v1/lan-fabric/rest/inventory/allswitches``

    ### Verb
    -   GET

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpAllSwitches()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self._build_properties()
        msg = "ENTERED api.v1.lan_fabric.rest.inventory."
        msg += f"{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "GET"

    @property
    def path(self):
        """
        Return endpoint path.
        """
        return f"{self.inventory}/allswitches"
