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
import json
import logging
from typing import Any, Dict

from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.common import \
    ImagePolicyCommon


class Payload(ImagePolicyCommon):
    """
    Base class for Config2Payload and Payload2Config
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED Payload()")

        self._build_properties()

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        # self.properties is instantiated in ImagePolicyCommon
        self.properties["payload"] = {}
        self.properties["config"] = {}

    @property
    def payload(self):
        """
        return the payload
        """
        return self.properties["payload"]

    @payload.setter
    def payload(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be a dictionary. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg)
        self.properties["payload"] = value

    @property
    def config(self):
        """
        return the playbook configuration
        """
        return self.properties["config"]

    @config.setter
    def config(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "config must be a dictionary. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg)
        self.properties["config"] = value


class Config2Payload(Payload):
    """
    Convert an image_policy configuration into a payload
    for a POST request to the image-policy API endpoint.
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED Config2Payload()")

    def commit(self):
        """
        Convert self_payload into a playbook configuration
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"properties[config] {json.dumps(self.properties['config'], indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if self.properties["config"] == {}:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config is empty"
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"HERE 1 STATE: {self.ansible_module.params['state']}"
        self.log.debug(msg)

        if self.ansible_module.params["state"] in ["deleted", "query"]:
            self.properties["payload"]["policyName"] = self.properties["config"]["name"]
            return
        self.properties["payload"]["agnostic"] = self.properties["config"]["agnostic"]
        self.properties["payload"]["epldImgName"] = self.properties["config"][
            "epld_image"
        ]
        self.properties["payload"]["nxosVersion"] = self.properties["config"]["release"]
        self.properties["payload"]["platform"] = self.properties["config"]["platform"]
        self.properties["payload"]["policyDescr"] = self.properties["config"][
            "description"
        ]
        self.properties["payload"]["policyName"] = self.properties["config"]["name"]
        self.properties["payload"]["policyType"] = self.properties["config"].get(
            "type", "PLATFORM"
        )

        if len(self.properties["config"].get("packages", {}).get("install", [])) != 0:
            self.properties["payload"]["packageName"] = ",".join(
                self.properties["config"]["packages"]["install"]
            )
        if len(self.properties["config"].get("packages", {}).get("uninstall", [])) != 0:
            self.properties["payload"]["rpmimages"] = ",".join(
                self.properties["config"]["packages"]["uninstall"]
            )

        msg = f"{self.class_name}.{method_name}: "
        msg += f"properties[payload] {json.dumps(self.properties['payload'], indent=4, sort_keys=True)}"
        self.log.debug(msg)

class Payload2Config(Payload):
    """
    Convert an image-policy endpoint payload into a playbook
    configuration.
    """

    def __init__(self, ansible_module):
        super().__init__(ansible_module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED Payload2Config()")

    def commit(self):
        """
        build the config from the payload
        """
        method_name = inspect.stack()[0][3]

        if self.properties["payload"] == {}:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload is empty"
            self.ansible_module.fail_json(msg)

        self.properties["config"]["agnostic"] = self.properties["payload"]["agnostic"]
        self.properties["config"]["epld_image"] = self.properties["payload"][
            "epldImgName"
        ]
        self.properties["config"]["release"] = self.properties["payload"]["nxosVersion"]
        self.properties["config"]["platform"] = self.properties["payload"]["platform"]
        self.properties["config"]["description"] = self.properties["payload"][
            "policyDescr"
        ]
        self.properties["config"]["name"] = self.properties["payload"]["policyName"]
        self.properties["config"]["type"] = self.properties["payload"]["policyType"]

        self.properties["config"]["packages"] = {}
        if self.properties["payload"].get("packageName", "") != "":
            self.properties["config"]["packages"]["install"] = self.properties[
                "payload"
            ]["packageName"].split(",")
        else:
            self.properties["config"]["packages"]["install"] = []
        if self.properties["payload"].get("rpmimages", "") != "":
            self.properties["config"]["packages"]["uninstall"] = self.properties[
                "payload"
            ]["rpmimages"].split(",")
        else:
            self.properties["config"]["packages"]["uninstall"] = []
