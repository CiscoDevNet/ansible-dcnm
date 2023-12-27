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


class Payload:
    """
    Convert an image_policy configuration into a payload
    for a POST request to the image policy API endpoint.
    """

    def __init__(self, ansible_module):
        self.ansible_module = ansible_module
        self._payload: Dict[str, Any] = {}
        self._config: Dict[str, Any] = {}

    def commit(self):
        method_name = inspect.stack()[0][3]

        if self.ansible_module.params["state"] == "merged":
            self._build_payload_for_merged_state()
        elif self.ansible_module.params["state"] == "replaced":
            self._build_payload_for_replaced_state()
        elif self.ansible_module.params["state"] == "overridden":
            self._build_payload_for_overridden_state()
        elif self.ansible_module.params["state"] == "deleted":
            self._build_payload_for_deleted_state()
        elif self.ansible_module.params["state"] == "query":
            self._build_payload_for_query_state()
        else:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid state {self.ansible_module.params['state']}"
            self.ansible_module.fail_json(msg)

    def _build_payload_for_merged_state(self):
        method_name = inspect.stack()[0][3]

        if self.config == {}:
            msg = f"{self.class_name}.{method_name}: "
            msg += "self.config is empty"
            self.ansible_module.fail_json(msg)

        self._payload["agnostic"] = self.config["agnostic"]
        self._payload["epldImgName"] = self.config["epld_image"]
        self._payload["nxosVersion"] = self.config["release"]
        self._payload["platform"] = self.config["platform"]
        self._payload["policyDescr"] = self.config["description"]
        self._payload["policyName"] = self.config["name"]
        self._payload["policyType"] = "PLATFORM"

        if len(self.config.get("packages", {}).get("install", [])) != 0:
            self._payload["packageName"] = ",".join(self.config["packages"]["install"])
        if len(self.config.get("packages", {}).get("uninstall", [])) != 0:
            self._payload["rpmimages"] = ",".join(self.config["packages"]["uninstall"])

    @property
    def payload(self):
        if self._payload == {}:
            self.commit()
        return self._payload

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "config must be a dictionary. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg)
        self._config = value
