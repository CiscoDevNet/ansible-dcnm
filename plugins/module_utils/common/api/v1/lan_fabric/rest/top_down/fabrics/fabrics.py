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

from ..top_down import TopDown


class Fabrics(TopDown):
    """
    ## api.v1.lan-fabric.rest.top-down.fabrics.Fabrics()

    ### Description
    Common methods and properties for top-down.fabrics.Fabrics() subclasses.

    ### Path
    -   ``/api/v1/lan-fabric/rest/top_down/fabrics``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.fabrics = f"{self.top_down}/fabrics"
        msg = f"ENTERED api.v1.lan_fabric.rest.top_down.fabrics.{self.class_name}"
        self.log.debug(msg)
        self._build_properties()

    def _build_properties(self):
        """
        - Set the fabric_name property.
        """
        self.properties["fabric_name"] = None
        self.properties["ticket_id"] = None

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
        return f"{self.fabrics}/{self.fabric_name}"

    @property
    def ticket_id(self):
        """
        - getter: Return the ticket_id.
        - setter: Set the ticket_id.
        - setter: Raise ``ValueError`` if ticket_id is not a string.
        - Default: None
        - Note: ticket_id is optional unless Change Control is enabled.
        """
        return self.properties["ticket_id"]

    @ticket_id.setter
    def ticket_id(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Expected string for {method_name}. "
            msg += f"Got {value} with type {type(value).__name__}."
            raise ValueError(msg)
        self.properties["ticket_id"] = value
