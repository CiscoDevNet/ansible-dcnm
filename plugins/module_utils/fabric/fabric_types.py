#
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
import logging


class FabricTypes:
    """
    Fabric type definitions for the dcnm_fabric module.

    Usage

    # import and instantiate the class
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_types import FabricTypes
    fabric_types = FabricTypes()

    # Access the set of valid fabric types
    valid_fabric_types = fabric_types.valid_fabric_types
    <do something with valid_fabric_types omitted>

    # Set the fabric type for which further operations will be performed
    try:
        fabric_types.fabric_type = "VXLAN_EVPN"
    except ValueError as error:
        raise ValueError(error) from error

    # Access the template name for the VXLAN_EVPN fabric type
    template_name = fabric_types.template_name

    # Access mandatory parameters for the VXLAN_EVPN fabric type
    mandatory_parameters = fabric_types.mandatory_parameters
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED FabricTypes(): "
        self.log.debug(msg)

        self._init_fabric_types()
        self._init_properties()

    def _init_fabric_types(self) -> None:
        """
        This is the single place to add new fabric types.

        Initialize the following:
        -   fabric_type_to_template_name_map dict()
        -   fabric_type_to_feature_name_map dict()
        -   _valid_fabric_types - Sorted list() of fabric types
        -  _mandatory_parameters_all_fabrics list()
        -  _mandatory_parameters dict() keyed on fabric type
            - Value is a list of mandatory parameters for the fabric type
        """
        self._fabric_type_to_template_name_map = {}
        self._fabric_type_to_template_name_map["IPFM"] = "Easy_Fabric_IPFM"
        self._fabric_type_to_template_name_map["ISN"] = "External_Fabric"
        self._fabric_type_to_template_name_map["LAN_CLASSIC"] = "LAN_Classic"
        self._fabric_type_to_template_name_map["VXLAN_EVPN"] = "Easy_Fabric"
        self._fabric_type_to_template_name_map["VXLAN_EVPN_MSD"] = "MSD_Fabric"

        # Map fabric type to the feature name that must be running
        # on the controller to enable the fabric type.
        self._fabric_type_to_feature_name_map = {}
        self._fabric_type_to_feature_name_map["IPFM"] = "pmn"
        self._fabric_type_to_feature_name_map["ISN"] = "vxlan"
        self._fabric_type_to_feature_name_map["LAN_CLASSIC"] = "lan"
        self._fabric_type_to_feature_name_map["VXLAN_EVPN"] = "vxlan"
        self._fabric_type_to_feature_name_map["VXLAN_EVPN_MSD"] = "vxlan"

        # Map fabric type to the value that the controller GUI displays
        # in the Fabric Type column at NDFC -> Manage -> Fabrics
        # This is needed only for fabrics that use the External_Fabric
        # template, e.g. ISN, and will be inserted into the POST request
        # payload for external fabrics as (in the case of ISN fabric type):
        # "EXT_FABRIC_TYPE": "Multi-Site External Network"
        #
        # Exposed via property fabric_type_to_ext_fabric_type_map
        self._fabric_type_to_ext_fabric_type_map = {}
        self._fabric_type_to_ext_fabric_type_map["ISN"] = "Multi-Site External Network"

        self._valid_fabric_types = sorted(self._fabric_type_to_template_name_map.keys())

        # self._external_fabric_types is used in conjunction with
        # self._fabric_type_to_ext_fabric_type_map.  This is used in (at least)
        # FabricCreateCommon() to determine if EXT_FABRIC_TYPE key needs to be
        # added to a payload.
        #
        # Exposed via property external_fabric_types
        self._external_fabric_types = set()
        self._external_fabric_types.add("ISN")

        self._mandatory_parameters_all_fabrics = []
        self._mandatory_parameters_all_fabrics.append("FABRIC_NAME")
        self._mandatory_parameters_all_fabrics.append("FABRIC_TYPE")

        self._mandatory_parameters = {}
        self._mandatory_parameters["IPFM"] = copy.copy(
            self._mandatory_parameters_all_fabrics
        )
        self._mandatory_parameters["ISN"] = copy.copy(
            self._mandatory_parameters_all_fabrics
        )
        self._mandatory_parameters["LAN_CLASSIC"] = copy.copy(
            self._mandatory_parameters_all_fabrics
        )
        self._mandatory_parameters["VXLAN_EVPN"] = copy.copy(
            self._mandatory_parameters_all_fabrics
        )
        self._mandatory_parameters["ISN"].append("BGP_AS")
        self._mandatory_parameters["VXLAN_EVPN"].append("BGP_AS")
        self._mandatory_parameters["VXLAN_EVPN_MSD"] = copy.copy(
            self._mandatory_parameters_all_fabrics
        )

        self._mandatory_parameters["IPFM"].sort()
        self._mandatory_parameters["ISN"].sort()
        self._mandatory_parameters["LAN_CLASSIC"].sort()
        self._mandatory_parameters["VXLAN_EVPN"].sort()
        self._mandatory_parameters["VXLAN_EVPN_MSD"].sort()

    def _init_properties(self) -> None:
        """
        Initialize properties specific to this class
        """
        self._properties = {}
        self._properties["fabric_type"] = None
        self._properties["template_name"] = None
        self._properties["valid_fabric_types"] = self._valid_fabric_types

    @property
    def external_fabric_types(self):
        """
        # Summary

        set() containing all external fabric types e.g. ISN.

        # Raises

        None
        """
        return self._external_fabric_types

    @property
    def fabric_type(self):
        """
        -   getter: Return the currently-set fabric type.
        -   setter: Set the fabric type.
        -   setter: raise ``ValueError`` if value is not a valid fabric type
        """
        return self._properties["fabric_type"]

    @fabric_type.setter
    def fabric_type(self, value):
        """
        -   Set the fabric type.
        -   raise ``ValueError`` if value is not a valid fabric type
        """
        if value not in self.valid_fabric_types:
            msg = f"{self.class_name}.fabric_type.setter: "
            msg += f"Invalid fabric type: {value}. "
            msg += f"Expected one of: {', '.join(self.valid_fabric_types)}."
            raise ValueError(msg)
        self._properties["fabric_type"] = value

    @property
    def fabric_type_to_ext_fabric_type_map(self):
        """
        # Summary

        Returns a dictionary, keyed on fabric_type (e.g. "ISN"),
        whose value is a string that the NDFC GUI uses to describe the
        external fabric type. See the Fabric Type column at
        NDFC -> Manage -> Fabrics for an example of how this is used
        by the NDFC GUI.
        """
        return self._fabric_type_to_ext_fabric_type_map

    @property
    def feature_name(self):
        """
        -   getter: Return the feature name that must be enabled on the controller
            for the currently-set fabric type.
        -   getter: raise ``ValueError`` if FabricTypes().fabric_type is not set.
        """
        if self.fabric_type is None:
            msg = f"{self.class_name}.feature_name: "
            msg += f"Set {self.class_name}.fabric_type before accessing "
            msg += f"{self.class_name}.feature_name"
            raise ValueError(msg)
        return self._fabric_type_to_feature_name_map[self.fabric_type]

    @property
    def mandatory_parameters(self):
        """
        -   getter: Return the mandatory playbook parameters for the
            currently-set fabric type as a sorted list().
        -   getter: raise ``ValueError`` if FabricTypes().fabric_type
            is not set.
        """
        if self.fabric_type is None:
            msg = f"{self.class_name}.mandatory_parameters: "
            msg += f"Set {self.class_name}.fabric_type before accessing "
            msg += f"{self.class_name}.mandatory_parameters"
            raise ValueError(msg)
        return self._mandatory_parameters[self.fabric_type]

    @property
    def template_name(self):
        """
        -   getter: Return the template name for the currently-set fabric type.
        -   getter: raise ``ValueError`` if FabricTypes().fabric_type is not set.
        """
        if self.fabric_type is None:
            msg = f"{self.class_name}.template_name: "
            msg += f"Set {self.class_name}.fabric_type before accessing "
            msg += f"{self.class_name}.template_name"
            raise ValueError(msg)
        return self._fabric_type_to_template_name_map[self.fabric_type]

    @property
    def valid_fabric_types(self):
        """
        Return a sorted list() of valid fabric types.
        """
        return self._properties["valid_fabric_types"]

    @property
    def valid_fabric_template_names(self):
        """
        Return a sorted list() of valid fabric template names.
        """
        return sorted(self._fabric_type_to_template_name_map.values())
