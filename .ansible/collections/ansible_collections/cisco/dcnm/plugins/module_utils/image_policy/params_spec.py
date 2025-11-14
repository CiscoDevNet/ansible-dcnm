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


class ParamsSpec:
    """
    ### Summary
    Parameter specifications for the dcnm_image_policy module.

    ### Raises
    -   ``ValueError`` if params is not set before calling ``commit()``
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._params_spec: dict = {}
        self.valid_states = set()
        self.valid_states.add("deleted")
        self.valid_states.add("merged")
        self.valid_states.add("overridden")
        self.valid_states.add("query")
        self.valid_states.add("replaced")

        self.log.debug("ENTERED ParamsSpec() v2")

    def commit(self):
        """
        ### Summary
        Build the parameter specification based on the state

        ## Raises
        -   ``ValueError`` if ``params`` is not set.

        """
        method_name = inspect.stack()[0][3]

        if self._params is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"params must be set before calling {method_name}."
            raise ValueError(msg)

        if self.params["state"] == "deleted":
            self._build_params_spec_for_deleted_state()
        if self.params["state"] == "merged":
            self._build_params_spec_for_merged_state()
        if self.params["state"] == "overridden":
            self._build_params_spec_for_overridden_state()
        if self.params["state"] == "query":
            self._build_params_spec_for_query_state()
        if self.params["state"] == "replaced":
            self._build_params_spec_for_replaced_state()

    def _build_params_spec_for_merged_state(self) -> None:
        """
        ### Summary
        Build the specs for the parameters expected when state is
        ``merged``.

        ### Raises
        None
        """
        self._params_spec: dict = {}

        self._params_spec["agnostic"] = {}
        self._params_spec["agnostic"]["default"] = False
        self._params_spec["agnostic"]["required"] = False
        self._params_spec["agnostic"]["type"] = "bool"

        self._params_spec["description"] = {}
        self._params_spec["description"]["default"] = ""
        self._params_spec["description"]["required"] = False
        self._params_spec["description"]["type"] = "str"

        self._params_spec["epld_image"] = {}
        self._params_spec["epld_image"]["default"] = ""
        self._params_spec["epld_image"]["required"] = False
        self._params_spec["epld_image"]["type"] = "str"

        self._params_spec["name"] = {}
        self._params_spec["name"]["required"] = True
        self._params_spec["name"]["type"] = "str"

        self._params_spec["platform"] = {}
        self._params_spec["platform"]["required"] = True
        self._params_spec["platform"]["type"] = "str"
        self._params_spec["platform"]["choices"] = ["N9K", "N7K", "N77", "N6K", "N5K"]

        self._params_spec["packages"] = {}
        self._params_spec["packages"]["default"] = {}
        self._params_spec["packages"]["required"] = False
        self._params_spec["packages"]["type"] = "dict"

        self._params_spec["packages"]["install"] = {}
        self._params_spec["packages"]["install"]["default"] = []
        self._params_spec["packages"]["install"]["required"] = False
        self._params_spec["packages"]["install"]["type"] = "list"

        self._params_spec["packages"]["uninstall"] = {}
        self._params_spec["packages"]["uninstall"]["default"] = []
        self._params_spec["packages"]["uninstall"]["required"] = False
        self._params_spec["packages"]["uninstall"]["type"] = "list"

        self._params_spec["release"] = {}
        self._params_spec["release"]["required"] = True
        self._params_spec["release"]["type"] = "str"

        self._params_spec["type"] = {}
        self._params_spec["type"]["default"] = "PLATFORM"
        self._params_spec["type"]["required"] = False
        self._params_spec["type"]["type"] = "str"

    def _build_params_spec_for_overridden_state(self) -> None:
        """
        ### Summary
        Build the specs for the parameters expected when state is
        ``overridden``.

        ### Raises
        None
        """
        self._build_params_spec_for_merged_state()

    def _build_params_spec_for_replaced_state(self) -> None:
        """
        ### Summary
        Build the specs for the parameters expected when state is
        ``replaced``.

        ### Raises
        None
        """
        self._build_params_spec_for_merged_state()

    def _build_params_spec_for_deleted_state(self) -> None:
        """
        ### Summary
        Build the specs for the parameters expected when state is
        ``deleted``.

        ### Raises
        None
        """
        self._params_spec: dict = {}

        self._params_spec["name"] = {}
        self._params_spec["name"]["required"] = True
        self._params_spec["name"]["type"] = "str"

    def _build_params_spec_for_query_state(self) -> None:
        """
        ### Summary
        Build the specs for the parameters expected when state is
        ``query``.

        ### Raises
        None
        """
        self._params_spec: dict = {}

        self._params_spec["name"] = {}
        self._params_spec["name"]["required"] = True
        self._params_spec["name"]["type"] = "str"

    def _build_params_spec_for_replaced_state(self) -> None:
        self._build_params_spec_for_merged_state()

    @property
    def params(self) -> dict:
        """
        ### Summary
        Expects value to be a dictionary containing, at mimimum,
        the key ``state`` with value of one of:
        - deleted
        - merged
        - overridden
        - query
        - replaced

        ### Raises
        -   setter: ``ValueError`` if value is not a dict
        -   setter: ``ValueError`` if value["state"] is missing
        -   setter: ``ValueError`` if value["state"] is not a valid state

        ### Details
        -   Valid params:
                -   ``{"state": "deleted"}``
                -   ``{"state": "merged"}``
                -   ``{"state": "overridden"}``
                -   ``{"state": "query"}``
                -   ``{"state": "replaced"}``
        -   getter: return the params
        -   setter: set the params
        """
        return self._params

    @params.setter
    def params(self, value: dict) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}.setter: "
            msg += "Invalid type. Expected dict but "
            msg += f"got type {type(value).__name__}, "
            msg += f"value {value}."
            raise TypeError(msg)

        if value.get("state", None) is None:
            msg = f"{self.class_name}.{method_name}.setter: "
            msg += "params.state is required but missing."
            raise ValueError(msg)

        if value["state"] not in self.valid_states:
            msg = f"{self.class_name}.{method_name}.setter: "
            msg += f"params.state is invalid: {value['state']}. "
            msg += f"Expected one of {', '.join(self.valid_states)}."
            raise ValueError(msg)

        self._params = value

    @property
    def params_spec(self) -> dict:
        """
        ### Summary
        Return the parameter specification
        """
        return self._params_spec
