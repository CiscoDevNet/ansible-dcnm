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
    Parameter specifications for the dcnm_image_upgrade module.

    ## Raises
    -   ``ValueError`` if:
            -   ``params["state"]`` is missing.
            -   ``params["state"]`` is not a valid state.
            -   ``params`` is not set before calling ``commit``.
    -   ``TypeError`` if:
            -   ``params`` is not a dict.
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._params_spec: dict = {}
        self.valid_states = set()
        self.valid_states.add("deleted")
        self.valid_states.add("merged")
        self.valid_states.add("query")

        self.log.debug("ENTERED ParamsSpec() v2")

    def commit(self):
        """
        ### Summary
        Build the parameter specification based on the state.

        ## Raises
        -   ``ValueError`` if:
                -   ``params`` is not set.
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
        if self.params["state"] == "query":
            self._build_params_spec_for_query_state()

    def build_ip_address(self):
        """
        ### Summary
        Build the parameter specification for the ``ip_address`` parameter.

        ### Raises
        None
        """
        self._params_spec["ip_address"] = {}
        self._params_spec["ip_address"]["required"] = True
        self._params_spec["ip_address"]["type"] = "ipv4"

    def build_policy(self):
        """
        ### Summary
        Build the parameter specification for the ``policy`` parameter.

        ### Raises
        None
        """
        self._params_spec["policy"] = {}
        self._params_spec["policy"]["required"] = False
        self._params_spec["policy"]["type"] = "str"

    def build_reboot(self):
        """
        ### Summary
        Build the parameter specification for the ``reboot`` parameter.

        ### Raises
        None
        """
        self._params_spec["reboot"] = {}
        self._params_spec["reboot"]["required"] = False
        self._params_spec["reboot"]["type"] = "bool"
        self._params_spec["reboot"]["default"] = False

    def build_stage(self):
        """
        ### Summary
        Build the parameter specification for the ``stage`` parameter.

        ### Raises
        None
        """
        self._params_spec["stage"] = {}
        self._params_spec["stage"]["required"] = False
        self._params_spec["stage"]["type"] = "bool"
        self._params_spec["stage"]["default"] = True

    def build_validate(self):
        """
        ### Summary
        Build the parameter specification for the ``validate`` parameter.

        ### Raises
        None
        """
        self._params_spec["validate"] = {}
        self._params_spec["validate"]["required"] = False
        self._params_spec["validate"]["type"] = "bool"
        self._params_spec["validate"]["default"] = True

    def build_upgrade(self):
        """
        ### Summary
        Build the parameter specification for the ``upgrade`` parameter.

        ### Raises
        None
        """
        self._params_spec["upgrade"] = {}
        self._params_spec["upgrade"]["required"] = False
        self._params_spec["upgrade"]["type"] = "dict"
        self._params_spec["upgrade"]["default"] = {}
        self._params_spec["upgrade"]["epld"] = {}
        self._params_spec["upgrade"]["epld"]["required"] = False
        self._params_spec["upgrade"]["epld"]["type"] = "bool"
        self._params_spec["upgrade"]["epld"]["default"] = False
        self._params_spec["upgrade"]["nxos"] = {}
        self._params_spec["upgrade"]["nxos"]["required"] = False
        self._params_spec["upgrade"]["nxos"]["type"] = "bool"
        self._params_spec["upgrade"]["nxos"]["default"] = True

    def build_options(self):
        """
        ### Summary
        Build the parameter specification for the ``options`` parameter.

        ### Raises
        None
        """
        section = "options"
        self._params_spec[section] = {}
        self._params_spec[section]["required"] = False
        self._params_spec[section]["type"] = "dict"
        self._params_spec[section]["default"] = {}

    def build_options_nxos(self):
        """
        ### Summary
        Build the parameter specification for the ``options.nxos`` parameter.

        ### Raises
        None
        """
        section = "options"
        sub_section = "nxos"
        self._params_spec[section][sub_section] = {}
        self._params_spec[section][sub_section]["required"] = False
        self._params_spec[section][sub_section]["type"] = "dict"
        self._params_spec[section][sub_section]["default"] = {}

        self._params_spec[section][sub_section]["mode"] = {}
        self._params_spec[section][sub_section]["mode"]["required"] = False
        self._params_spec[section][sub_section]["mode"]["type"] = "str"
        self._params_spec[section][sub_section]["mode"]["default"] = "disruptive"
        self._params_spec[section][sub_section]["mode"]["choices"] = [
            "disruptive",
            "non_disruptive",
            "force_non_disruptive",
        ]

        self._params_spec[section][sub_section]["bios_force"] = {}
        self._params_spec[section][sub_section]["bios_force"]["required"] = False
        self._params_spec[section][sub_section]["bios_force"]["type"] = "bool"
        self._params_spec[section][sub_section]["bios_force"]["default"] = False

    def build_options_epld(self):
        """
        ### Summary
        Build the parameter specification for the ``options.epld`` parameter.

        ### Raises
        None
        """
        section = "options"
        sub_section = "epld"
        self._params_spec[section][sub_section] = {}
        self._params_spec[section][sub_section]["required"] = False
        self._params_spec[section][sub_section]["type"] = "dict"
        self._params_spec[section][sub_section]["default"] = {}

        self._params_spec[section][sub_section]["module"] = {}
        self._params_spec[section][sub_section]["module"]["required"] = False
        self._params_spec[section][sub_section]["module"]["type"] = ["str", "int"]
        self._params_spec[section][sub_section]["module"]["preferred_type"] = "str"
        self._params_spec[section][sub_section]["module"]["default"] = "ALL"
        self._params_spec[section][sub_section]["module"]["choices"] = [
            str(x) for x in range(1, 33)
        ]
        self._params_spec[section][sub_section]["module"]["choices"].extend(
            list(range(1, 33))
        )
        self._params_spec[section][sub_section]["module"]["choices"].append("ALL")

        self._params_spec[section][sub_section]["golden"] = {}
        self._params_spec[section][sub_section]["golden"]["required"] = False
        self._params_spec[section][sub_section]["golden"]["type"] = "bool"
        self._params_spec[section][sub_section]["golden"]["default"] = False

    def build_options_reboot(self):
        """
        ### Summary
        Build the parameter specification for the ``options.reboot`` parameter.

        ### Raises
        None
        """
        section = "options"
        sub_section = "reboot"
        self._params_spec[section][sub_section] = {}
        self._params_spec[section][sub_section]["required"] = False
        self._params_spec[section][sub_section]["type"] = "dict"
        self._params_spec[section][sub_section]["default"] = {}

        self._params_spec[section][sub_section]["config_reload"] = {}
        self._params_spec[section][sub_section]["config_reload"]["required"] = False
        self._params_spec[section][sub_section]["config_reload"]["type"] = "bool"
        self._params_spec[section][sub_section]["config_reload"]["default"] = False

        self._params_spec[section][sub_section]["write_erase"] = {}
        self._params_spec[section][sub_section]["write_erase"]["required"] = False
        self._params_spec[section][sub_section]["write_erase"]["type"] = "bool"
        self._params_spec[section][sub_section]["write_erase"]["default"] = False

    def build_options_package(self):
        """
        ### Summary
        Build the parameter specification for the ``options.package`` parameter.

        ### Raises
        None
        """
        section = "options"
        sub_section = "package"
        self._params_spec[section][sub_section] = {}
        self._params_spec[section][sub_section]["required"] = False
        self._params_spec[section][sub_section]["type"] = "dict"
        self._params_spec[section][sub_section]["default"] = {}

        self._params_spec[section][sub_section]["install"] = {}
        self._params_spec[section][sub_section]["install"]["required"] = False
        self._params_spec[section][sub_section]["install"]["type"] = "bool"
        self._params_spec[section][sub_section]["install"]["default"] = False

        self._params_spec[section][sub_section]["uninstall"] = {}
        self._params_spec[section][sub_section]["uninstall"]["required"] = False
        self._params_spec[section][sub_section]["uninstall"]["type"] = "bool"
        self._params_spec[section][sub_section]["uninstall"]["default"] = False

    def _build_params_spec_for_merged_state(self) -> None:
        """
        ### Summary
        Build the specs for the parameters expected when state is
        ``merged``.

        ### Raises
        None
        """
        self.build_ip_address()
        self.build_policy()
        self.build_reboot()
        self.build_stage()
        self.build_validate()
        self.build_upgrade()
        self.build_options()
        self.build_options_nxos()
        self.build_options_epld()
        self.build_options_reboot()
        self.build_options_package()

    def _build_params_spec_for_deleted_state(self) -> None:
        """
        ### Summary
        Build the specs for the parameters expected when state is
        ``deleted``.

        ### Raises
        None

        ### Notes
        -   Parameters for ``deleted`` state are the same as ``merged`` state.
        """
        self._build_params_spec_for_merged_state()

    def _build_params_spec_for_query_state(self) -> None:
        """
        ### Summary
        Build the specs for the parameters expected when state is
        ``query``.

        ### Raises
        None
        """
        self.build_ip_address()

    @property
    def params(self) -> dict:
        """
        ### Summary
        Expects value to be a dictionary containing, at mimimum,
        the key ``state`` with value being one of:
        - deleted
        - merged
        - query

        ### Raises
        -   ``TypeError`` if:
                -   ``value`` is not a dict.
        -   ``ValueError`` if:
                -   ``value["state"]`` is missing.
                -   ``value["state"]`` is not a valid state.

        ### Details
        -   Valid params:
                -   ``{"state": "deleted"}``
                -   ``{"state": "merged"}``
                -   ``{"state": "query"}``
        -   getter: return the params
        -   setter: set the params
        """
        return self._params

    @params.setter
    def params(self, value) -> None:
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

        ### Raises
        None
        """
        return self._params_spec
