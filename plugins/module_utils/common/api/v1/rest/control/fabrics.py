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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric import \
    LanFabric

class Fabrics(LanFabric):
    """
    V1 API Fabrics endpoints common methods and properties.
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.rest_control_fabrics = f"{self.lan_fabric}/rest/control/fabrics"
        self.log.debug("ENTERED api.v1.LanFabric.Fabrics()")
        self._build_properties()

    def _build_properties(self):
        """
        - Set the fabric_name property.
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
            raise ValueError(msg)
        self.properties["fabric_name"] = value

    @property
    def path(self):
        """
        - Override the path property to mandate fabric_name is set.
        - Raise ``ValueError`` if fabric_name is not set.
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_name is None and "fabric_name" in self.required_properties:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_name must be set prior to accessing path."
            raise ValueError(msg)
        return f"{self.rest_control_fabrics}/{self.fabric_name}"

class FabricsDelete(Fabrics):
    """
    V1 API Fabrics: fabric delete endpoint.
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self._build_properties()
        self.log.debug(f"ENTERED api.v1.LanFabric.Fabrics.{self.class_name}")

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "DELETE"

class FabricsDetails(Fabrics):
    """
    V1 API Fabrics: fabric details endpoint.
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self._build_properties()
        self.log.debug(f"ENTERED api.v1.LanFabric.Fabrics.{self.class_name}")

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "GET"
