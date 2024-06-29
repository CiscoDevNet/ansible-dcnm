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


class Payload:
    """
    Base class for Config2Payload and Payload2Config
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._config = {}
        self._params = {}
        self._payload = {}

        msg = "ENTERED Payload()"
        self.log.debug(msg)

    @property
    def config(self):
        """
        return the playbook configuration
        """
        return self._config

    @config.setter
    def config(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "config must be a dictionary. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        self._config = value

    @property
    def params(self):
        """
        return the params dict
        """
        return self._params

    @params.setter
    def params(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "params must be a dictionary. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        self._params = value

    @property
    def payload(self):
        """
        return the payload
        """
        return self._payload

    @payload.setter
    def payload(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload must be a dictionary. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        self._payload = value


class Config2Payload(Payload):
    """
    ### Summary
    Convert an image_policy configuration into a payload
    for a POST request to the image-policy API endpoint.

    ### Raises
    -   ``ValueError`` if:
            -   self.config is empty
            -   self.params is is not set prior to calling commit()
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED Config2Payload()")

    def commit(self):
        """
        Convert self_payload into a playbook configuration
        """
        method_name = inspect.stack()[0][3]

        if self.params is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params must be set before calling commit()."
            raise ValueError(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.config {json.dumps(self.config, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if self.config == {}:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config is empty"
            raise ValueError(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"HERE 1 STATE: {self.params['state']}"
        self.log.debug(msg)

        if self.params["state"] in ["deleted", "query"]:
            self.payload["policyName"] = self.config["name"]
            return
        self.payload["agnostic"] = self.config["agnostic"]
        self.payload["epldImgName"] = self.config["epld_image"]
        self.payload["nxosVersion"] = self.config["release"]
        self.payload["platform"] = self.config["platform"]
        self.payload["policyDescr"] = self.config["description"]
        self.payload["policyName"] = self.config["name"]
        self.payload["policyType"] = self.config.get("type", "PLATFORM")

        if len(self.config.get("packages", {}).get("install", [])) != 0:
            self.payload["packageName"] = ",".join(self.config["packages"]["install"])
        if len(self.config.get("packages", {}).get("uninstall", [])) != 0:
            self.payload["rpmimages"] = ",".join(self.config["packages"]["uninstall"])

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.payload {json.dumps(self.payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)


class Payload2Config(Payload):
    """
    Convert an image-policy endpoint payload into a playbook
    configuration.
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED Payload2Config()")

    def commit(self):
        """
        ### Summary
        build the config from the payload

        ### Raises
        -   ``ValueError`` if payload is empty
        """
        method_name = inspect.stack()[0][3]

        if self.payload == {}:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload is empty"
            raise ValueError(msg)

        self.config["agnostic"] = self.payload["agnostic"]
        self.config["epld_image"] = self.payload["epldImgName"]
        self.config["release"] = self.payload["nxosVersion"]
        self.config["platform"] = self.payload["platform"]
        self.config["description"] = self.payload["policyDescr"]
        self.config["name"] = self.payload["policyName"]
        self.config["type"] = self.payload["policyType"]

        self.config["packages"] = {}
        if self.payload.get("packageName", "") != "":
            self.config["packages"]["install"] = self.payload["packageName"].split(",")
        else:
            self.config["packages"]["install"] = []
        if self.payload.get("rpmimages", "") != "":
            self.config["packages"]["uninstall"] = self.payload["rpmimages"].split(",")
        else:
            self.config["packages"]["uninstall"] = []
