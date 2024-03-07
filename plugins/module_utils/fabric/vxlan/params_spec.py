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
from typing import Any, Dict


class ParamsSpec:
    """
    Parameter specifications for the dcnm_fabric_vxlan module.
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ParamsSpec()")

        self._params_spec: Dict[str, Any] = {}

    def commit(self):
        """
        build the parameter specification based on the state
        """
        method_name = inspect.stack()[0][3]

        if self.ansible_module.params["state"] is None:
            self.ansible_module.fail_json(msg="state is None")

        if self.ansible_module.params["state"] == "merged":
            self._build_params_spec_for_merged_state()
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
        Build the specs for the playbook parameters expected
        when state == merged.  These are then accessible via
        the @params_spec property.

        Caller: commit()
        """
        msg = "Building params spec for merged state"
        self.log.debug(msg)

        self._params_spec: Dict[str, Any] = {}

        self._params_spec["aaa_remote_ip_enabled"] = {}
        self._params_spec["aaa_remote_ip_enabled"]["default"] = False
        self._params_spec["aaa_remote_ip_enabled"]["required"] = False
        self._params_spec["aaa_remote_ip_enabled"]["type"] = "bool"

        # TODO:6 active_migration
        # active_migration doesn't seem to be represented in
        # the NDFC EasyFabric GUI.  Add this param if we figure out
        # what it's used for and where in the GUI it's represented

        self._params_spec["advertise_pip_bgp"] = {}
        self._params_spec["advertise_pip_bgp"]["default"] = False
        self._params_spec["advertise_pip_bgp"]["required"] = False
        self._params_spec["advertise_pip_bgp"]["type"] = "bool"

        # TODO:6 agent_intf (add if required)

        self._params_spec["anycast_bgw_advertise_pip"] = {}
        self._params_spec["anycast_bgw_advertise_pip"]["default"] = False
        self._params_spec["anycast_bgw_advertise_pip"]["required"] = False
        self._params_spec["anycast_bgw_advertise_pip"]["type"] = "bool"

        self._params_spec["anycast_gw_mac"] = {}
        self._params_spec["anycast_gw_mac"]["default"] = "2020.0000.00aa"
        self._params_spec["anycast_gw_mac"]["required"] = False
        self._params_spec["anycast_gw_mac"]["type"] = "str"

        # self._params_spec["anycast_lb_id"] = {}
        # # self._params_spec["anycast_lb_id"]["default"] = ""
        # # self._params_spec["anycast_lb_id"]["range_max"] = 1023
        # # self._params_spec["anycast_lb_id"]["range_min"] = 0
        # self._params_spec["anycast_lb_id"]["required"] = False
        # self._params_spec["anycast_lb_id"]["type"] = "str"

        self._params_spec["auto_symmetric_default_vrf"] = {}
        self._params_spec["auto_symmetric_default_vrf"]["default"] = False
        self._params_spec["auto_symmetric_default_vrf"]["required"] = False
        self._params_spec["auto_symmetric_default_vrf"]["type"] = "bool"

        self._params_spec["auto_symmetric_vrf_lite"] = {}
        self._params_spec["auto_symmetric_vrf_lite"]["default"] = False
        self._params_spec["auto_symmetric_vrf_lite"]["required"] = False
        self._params_spec["auto_symmetric_vrf_lite"]["type"] = "bool"

        self._params_spec["auto_vrflite_ifc_default_vrf"] = {}
        self._params_spec["auto_vrflite_ifc_default_vrf"]["default"] = False
        self._params_spec["auto_vrflite_ifc_default_vrf"]["required"] = False
        self._params_spec["auto_vrflite_ifc_default_vrf"]["type"] = "bool"

        self._params_spec["bgp_as"] = {}
        self._params_spec["bgp_as"]["required"] = True
        self._params_spec["bgp_as"]["type"] = "str"

        self._params_spec["default_vrf_redis_bgp_rmap"] = {}
        self._params_spec["default_vrf_redis_bgp_rmap"]["default"] = ""
        self._params_spec["default_vrf_redis_bgp_rmap"]["required"] = False
        self._params_spec["default_vrf_redis_bgp_rmap"]["type"] = "str"

        self._params_spec["fabric_name"] = {}
        self._params_spec["fabric_name"]["required"] = True
        self._params_spec["fabric_name"]["type"] = "str"

        self._params_spec["pm_enable"] = {}
        self._params_spec["pm_enable"]["default"] = False
        self._params_spec["pm_enable"]["required"] = False
        self._params_spec["pm_enable"]["type"] = "bool"

        self._params_spec["replication_mode"] = {}
        self._params_spec["replication_mode"]["choices"] = ["Ingress", "Multicast"]
        self._params_spec["replication_mode"]["default"] = "Multicast"
        self._params_spec["replication_mode"]["required"] = False
        self._params_spec["replication_mode"]["type"] = "str"

        self._params_spec["vrf_lite_autoconfig"] = {}
        self._params_spec["vrf_lite_autoconfig"]["choices"] = [0, 1]
        self._params_spec["vrf_lite_autoconfig"]["default"] = 0
        self._params_spec["vrf_lite_autoconfig"]["required"] = False
        self._params_spec["vrf_lite_autoconfig"]["type"] = "int"

    def _build_params_spec_for_deleted_state(self) -> None:
        """
        Build the specs for the playbook parameters expected
        when state == deleted.  These are then accessible via
        the @params_spec property.

        Caller: commit()
        """
        self._params_spec: Dict[str, Any] = {}

        self._params_spec["fabric_name"] = {}
        self._params_spec["fabric_name"]["required"] = True
        self._params_spec["fabric_name"]["type"] = "str"

    def _build_params_spec_for_query_state(self) -> None:
        """
        Build the specs for the playbook parameters expected
        when state == query.  These are then accessible via
        the @params_spec property.

        Caller: commit()
        """
        self._params_spec: Dict[str, Any] = {}

        self._params_spec["fabric_name"] = {}
        self._params_spec["fabric_name"]["required"] = True
        self._params_spec["fabric_name"]["type"] = "str"

    @property
    def params_spec(self) -> Dict[str, Any]:
        """
        return the parameter specification
        """
        return self._params_spec
