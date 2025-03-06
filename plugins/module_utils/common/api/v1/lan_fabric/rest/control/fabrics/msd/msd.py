# Copyright (c) 2025 Cisco and/or its affiliates.
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
__author__ = "prabahal"

import logging

from ..fabrics import Fabrics


class Msd(Fabrics):
    """
    ## api.v1.lan-fabric.rest.control.fabrics.Msd()

    ### Description
    Common methods and properties for Msd() subclasses.

    ### Path
    -   ``/api/v1/lan-fabric/rest/control/fabrics/msd``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.msd = f"{self.fabrics}/msd"
        msg = f"ENTERED api.v1.lan_fabric.rest.control.fabrics.{self.class_name}"
        self.log.debug(msg)


class EpFabricAssociations(Msd):
    """
    ## api.v1.lan-fabric.rest.control.fabrics.msd.EpFabricAssociations()

    ### Description
    Common methods and properties for EpFabricAssociations() subclasses.

    ### Path
    -   ``/api/v1/lan-fabric/rest/control/fabrics/msd/fabric-associations``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = f"ENTERED api.v1.lan_fabric.rest.control.fabrics.msd.{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "GET"

    @property
    def path(self):
        """
        Return endpoint path.
        """
        return f"{self.msd}/fabric-associations"


class EpChildFabricAdd(Msd):
    """
    ## api.v1.lan-fabric.rest.control.fabrics.msd.EpChildFabricAdd()

    ### Description
    Common methods and properties for EpChildFabricAdd() subclasses.

    ### Path
    -   ``/api/v1/lan-fabric/rest/control/fabrics/msdAdd``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.msdAdd = f"{self.msd}Add"
        msg = f"ENTERED api.v1.lan_fabric.rest.control.fabrics.msd.{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "POST"

    @property
    def path(self):
        """
        Return endpoint path.
        """
        return f"{self.msd}Add"


class EpChildFabricExit(Msd):
    """
    ## api.v1.lan-fabric.rest.control.fabrics.msd.EpChildFabricExit()

    ### Description
    Common methods and properties for EpChildFabricExit() subclasses.

    ### Path
    -   ``/api/v1/lan-fabric/rest/control/fabrics/msdExit``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.msdExit = f"{self.msd}Exit"
        msg = f"ENTERED api.v1.lan_fabric.rest.control.fabrics.msd.{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "POST"

    @property
    def path(self):
        """
        Return endpoint path.
        """
        return f"{self.msd}Exit"
