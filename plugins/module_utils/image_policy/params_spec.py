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

import inspect
from typing import Any, Dict


class ParamsSpec:
    """
    Parameter specifications for the dcnm_image_policy module.
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module
        self._params_spec: Dict[str, Any] = {}

    def commit(self):
        method_name = inspect.stack()[0][3]

        if self.ansible_module.params["state"] == None:
            self.ansible_module.fail_json(msg="state is None")

        if self.ansible_module.params["state"] == "merged":
            # self._build_params_spec_for_merged_state()
            self._build_params_spec_for_merged_state_proposed()
        elif self.ansible_module.params["state"] == "replaced":
            self._build_params_spec_for_replaced_state()
        elif self.ansible_module.params["state"] == "overridden":
            self._build_params_spec_for_overridden_state()
        elif self.ansible_module.params["state"] == "deleted":
            self._build_params_spec_for_deleted_state()
        elif self.ansible_module.params["state"] == "query":
            self._build_params_spec_for_query_state()
        else:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid state {self.ansible_module.params['state']}"
            self.ansible_module.fail_json(msg)

    def _build_params_spec_for_merged_state(self) -> None:
        """
        Build the specs for the parameters expected when state == merged.

        Caller: _validate_configs()
        Return: params_spec, a dictionary containing playbook
                parameter specifications.
        """
        # print("Building params spec for merged state")
        self._params_spec: Dict[str, Any] = {}

        self._params_spec["agnostic"] = {}
        self._params_spec["agnostic"]["required"] = False
        self._params_spec["agnostic"]["type"] = "bool"
        self._params_spec["agnostic"]["default"] = False

        self._params_spec["description"] = {}
        self._params_spec["description"]["default"] = ""
        self._params_spec["description"]["required"] = False
        self._params_spec["description"]["type"] = "str"

        self._params_spec["disabled_rpm"] = {}
        self._params_spec["disabled_rpm"]["default"] = ""
        self._params_spec["disabled_rpm"]["required"] = False
        self._params_spec["disabled_rpm"]["type"] = "str"

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

        self._params_spec["release"] = {}
        self._params_spec["release"]["required"] = True
        self._params_spec["release"]["type"] = "str"

        self._params_spec["packages"] = {}
        self._params_spec["packages"]["default"] = []
        self._params_spec["packages"]["required"] = False
        self._params_spec["packages"]["type"] = "list"

    def _build_params_spec_for_merged_state_proposed(self) -> None:
        """
        Build the specs for the parameters expected when state == merged.

        Caller: _validate_configs()
        Return: params_spec, a dictionary containing playbook
                parameter specifications.
        """
        # print("Building params spec for merged state PROPOSED")
        self._params_spec: Dict[str, Any] = {}

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

    def _build_params_spec_for_replaced_state(self) -> None:
        self._build_params_spec_for_merged_state_proposed()

    def _build_params_spec_for_deleted_state(self) -> None:
        """
        Build the specs for the parameters expected when state == deleted.

        Caller: _validate_configs()
        Return: params_spec, a dictionary containing playbook
                parameter specifications.
        """
        self._params_spec: Dict[str, Any] = {}

        self._params_spec["name"] = {}
        self._params_spec["name"]["required"] = True
        self._params_spec["name"]["type"] = "str"

    def _build_params_spec_for_replaced_state(self) -> None:
        self._build_params_spec_for_merged_state_proposed()

    @property
    def params_spec(self) -> Dict[str, Any]:
        return self._params_spec
