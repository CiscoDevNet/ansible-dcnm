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

import inspect
import logging

from ..control import Control


class Switches(Control):
    """
    ## api.v1.lan_fabric.rest.control.switches.Switches()

    ### Description
    Common methods and properties for Switches() subclasses.

    ### Path
    -   ``/api/v1/lan-fabric/rest/control/switches/{fabric_name}``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.switches = f"{self.control}/switches"
        msg = f"ENTERED api.v1.lan_fabric.rest.control.switches.{self.class_name}"
        self.log.debug(msg)
        self._build_properties()

    def _build_properties(self):
        """
        Populate properties specific to this class and its subclasses.
        """
        self.properties["fabric_name"] = None

    @property
    def fabric_name(self):
        """
        - getter: Return the fabric_name.
        - setter: Set the fabric_name.
        - setter: Raise ``ValueError`` if fabric_name is not valid.
        """
        return self.properties["fabric_name"]

    @fabric_name.setter
    def fabric_name(self, value):
        method_name = inspect.stack()[0][3]
        try:
            self.conversion.validate_fabric_name(value)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{error}"
            raise ValueError(msg) from error
        self.properties["fabric_name"] = value

    @property
    def path_fabric_name(self):
        """
        -   Endpoint path property, including fabric_name.
        -   Raise ``ValueError`` if fabric_name is not set and
            ``self.required_properties`` contains "fabric_name".
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_name is None and "fabric_name" in self.required_properties:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_name must be set prior to accessing path."
            raise ValueError(msg)
        return f"{self.switches}/{self.fabric_name}"


class EpFabricSummary(Switches):
    """
    ##api.v1.lan_fabric.rest.control.switches.EpFabricSummary()

    ### Description
    Return endpoint information.

     ### Raises
    -   ``ValueError``: If fabric_name is not set.
    -   ``ValueError``: If fabric_name is invalid.

    ### Path
    -   ``/api/v1/lan-fabric/rest/control/switches/{fabric_name}/overview``

    ### Verb
    -   GET

    ### Parameters
    - fabric_name: string
        - set the ``fabric_name`` to be used in the path
        - required
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpFabricSummary()
    instance.fabric_name = "MyFabric"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self._build_properties()
        msg = "ENTERED api.v1.lan_fabric.rest.control.switches."
        msg += f"{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "GET"

    @property
    def path(self):
        """
        - Override the path property to mandate fabric_name is set.
        - Raise ``ValueError`` if fabric_name is not set.
        """
        return f"{self.path_fabric_name}/overview"
