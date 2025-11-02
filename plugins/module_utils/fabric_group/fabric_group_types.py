#
# Copyright (c) 2024-2025 Cisco and/or its affiliates.
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
# pylint: disable=too-many-instance-attributes
"""
Fabric group type definitions for the dcnm_fabric_group module.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import logging


class FabricGroupTypes:
    """
    # Summary

    Fabric group type definitions for the dcnm_fabric_group module.

    Currently supported fabric group types:

    -   MCFG - Multi-Cluster Fabric Group

    ## Raises

    -   `ValueError` if:
        -   `fabric_group_type` is set to an invalid fabric group type.
        -   `template_name`, `mandatory_parameters`, or `feature_name` is accessed before `fabric_group_type` is set.

    ## Usage

    ```python
    # import and instantiate the class
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_groups.fabric_group_types import FabricGroupTypes
    fabric_group_types = FabricGroupTypes()

    # Access the set of valid fabric types
    valid_fabric_group_types = fabric_group_types.valid_fabric_group_types
    # Do something with valid_fabric_group_types omitted

    # Set the fabric group type for which further operations will be performed
    try:
        fabric_group_types.fabric_group_type = "MCFG"
    except ValueError as error:
        raise ValueError(error) from error

    # Access the template name for the MCFG fabric group type
    template_name = fabric_group_types.template_name

    # Access mandatory parameters for the MCFG fabric group type
    mandatory_parameters = fabric_group_types.mandatory_parameters

    # Access the feature name required for the MCFG fabric group type
    feature_name = fabric_group_types.feature_name

    # Access the internal fabric type name for the MCFG fabric group type
    fabric_type = fabric_group_types.fabric_type
    ```

    """

    def __init__(self) -> None:
        self.class_name: str = self.__class__.__name__

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")
        self._template_name: str = ""
        self._fabric_group_type: str = ""
        self._init_fabric_group_types()

    def _init_fabric_group_types(self) -> None:
        """
        # Summary

        This is the single place to add new fabric group types.

        Initializes the following:

        -   fabric_group_type_to_template_name_map dict()
        -   fabric_group_type_to_feature_name_map dict()
        -   fabric_group_type_to_fabric_type_map dict()
        -   _valid_fabric_group_types - Sorted list() of fabric group types
        -  _mandatory_parameters_all_fabric_groups list()
        -  _mandatory_parameters dict() keyed on fabric group type
            - Value is a list of mandatory parameters for the fabric group type

        ## Raises

        None
        """
        self._fabric_group_type_to_template_name_map: dict[str, str] = {}
        self._fabric_group_type_to_template_name_map["MCFG"] = "MSD_Fabric"

        # Map fabric group type to the feature name that must be running
        # on the controller to enable the fabric group type.
        self._fabric_group_type_to_feature_name_map: dict[str, str] = {}
        self._fabric_group_type_to_feature_name_map["MCFG"] = "vxlan"

        # Map the fabric group type to its internal FABRIC_TYPE name
        self._fabric_group_type_to_fabric_type_map: dict[str, str] = {}
        self._fabric_group_type_to_fabric_type_map["MCFG"] = "MFD"

        self._valid_fabric_group_types: set[str] = set(self._fabric_group_type_to_template_name_map.keys())

        self._mandatory_parameters_all_fabric_groups: list[str] = []
        self._mandatory_parameters_all_fabric_groups.append("FABRIC_NAME")
        self._mandatory_parameters_all_fabric_groups.append("FABRIC_TYPE")

        self._mandatory_parameters = {}
        self._mandatory_parameters["MCFG"] = copy.copy(self._mandatory_parameters_all_fabric_groups)
        self._mandatory_parameters["MCFG"].sort()

    @property
    def fabric_group_type(self) -> str:
        """
        # Summary

        -   getter: Return the currently-set fabric group type.
        -   setter: Set the fabric group type.

        ## Raises

        -   setter: `ValueError` if value is not a valid fabric group type
        """
        return self._fabric_group_type

    @fabric_group_type.setter
    def fabric_group_type(self, value: str) -> None:
        method_name: str = inspect.stack()[0][3]
        if value not in self._valid_fabric_group_types:
            msg = f"{self.class_name}.{method_name}.setter: "
            msg += f"Invalid fabric group type: {value}. "
            msg += "Expected one of: "
            msg += f"{', '.join(self._valid_fabric_group_types)}."
            raise ValueError(msg)
        self._fabric_group_type = value

    @property
    def fabric_type(self) -> str:
        """
        # Summary

        Return the internal FABRIC_TYPE name for the currently-set fabric group type.

        ## Raises

        -   `ValueError` if `fabric_group_type` is not set.
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_group_type is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Set {self.class_name}.fabric_group_type before accessing "
            msg += f"{self.class_name}.{method_name}"
            raise ValueError(msg)
        return self._fabric_group_type_to_fabric_type_map[self.fabric_group_type]

    @property
    def feature_name(self) -> str:
        """
        # Summary

        Return the feature name that must be enabled on the controller
        for the currently-set fabric group type.

        ## Raises

        -   `ValueError` if `fabric_group_type` is not set.
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_group_type is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Set {self.class_name}.fabric_group_type before accessing "
            msg += f"{self.class_name}.{method_name}"
            raise ValueError(msg)
        return self._fabric_group_type_to_feature_name_map[self.fabric_group_type]

    @property
    def mandatory_parameters(self) -> list[str]:
        """
        # Summary

        Return the mandatory playbook parameters for the currently-set fabric group type as a sorted list().

        ## Raises

        -   `ValueError` if `fabric_group_type` is not set.
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_group_type is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Set {self.class_name}.fabric_group_type before accessing "
            msg += f"{self.class_name}.{method_name}"
            raise ValueError(msg)
        return self._mandatory_parameters[self.fabric_group_type]

    @property
    def template_name(self) -> str:
        """
        # Summary

        Return the template name for the currently-set fabric group type.

        ## Raises

        -   `ValueError` if
            -   `fabric_group_type` is not set.
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_group_type is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Set {self.class_name}.fabric_group_type before accessing "
            msg += f"{self.class_name}.{method_name}"
            raise ValueError(msg)
        return self._fabric_group_type_to_template_name_map[self.fabric_group_type]

    @property
    def valid_fabric_group_types(self) -> list[str]:
        """
        # Summary

        Return a sorted list() of valid fabric group types.

        ## Raises

        None
        """
        return sorted(self._valid_fabric_group_types)

    @property
    def valid_fabric_group_template_names(self) -> list[str]:
        """
        # Summary

        Return a sorted list() of valid fabric group template names.

        ## Raises

        None
        """
        return sorted(self._fabric_group_type_to_template_name_map.values())
