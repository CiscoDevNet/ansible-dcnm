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
import inspect
import json
import logging


class Payload:
    """
    ### Summary
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
        ### Summary
        Return the playbook configuration.

        ### Raises
        -   ``TypeError`` if config is not a dictionary.
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
        self._config = copy.deepcopy(value)

    @property
    def params(self):
        """
        ### Summary
        Return the params dictionary.

        ### Raises
        -   ``TypeError`` if params is not a dictionary.
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
        self._params = copy.deepcopy(value)

    @property
    def payload(self):
        """
        ### Summary
        Return the payload.

        ### Raises
        -   ``TypeError`` if payload is not a dictionary.
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
        self._payload = copy.deepcopy(value)


class Config2Payload(Payload):
    """
    ### Summary
    Convert an image_policy configuration into a payload
    for a POST request to the image-policy API endpoint.

    ### Raises
    -   ``ValueError`` if:
            -   ``config`` is empty.
            -   ``params`` is is not set prior to calling ``commit``.
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED Config2Payload()")

    def commit(self):
        """
        ### Summary
        Convert ``payload`` into a playbook configuration.

        ### Raises
        -   ``ValueError`` if:
            -   ``params`` is not set.
            -   ``config`` is empty.
        """
        method_name = inspect.stack()[0][3]

        if self.params is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "params must be set before calling commit()."
            raise ValueError(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += "config: "
        msg += f"{json.dumps(self.config, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if self.config == {}:
            msg = f"{self.class_name}.{method_name}: "
            msg += "config is empty."
            raise ValueError(msg)

        config = copy.deepcopy(self.config)

        if self.params["state"] in ["deleted", "query"]:
            self.payload["policyName"] = config["name"]
            return
        self.payload["agnostic"] = config["agnostic"]
        self.payload["epldImgName"] = config["epld_image"]
        self.payload["nxosVersion"] = config["release"]
        self.payload["platform"] = config["platform"]
        self.payload["policyDescr"] = config["description"]
        self.payload["policyName"] = config["name"]
        self.payload["policyType"] = config.get("type", "PLATFORM")

        if len(config.get("packages", {}).get("install", [])) != 0:
            self.payload["packageName"] = ",".join(config["packages"]["install"])
        if len(config.get("packages", {}).get("uninstall", [])) != 0:
            self.payload["rpmimages"] = ",".join(config["packages"]["uninstall"])

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.payload {json.dumps(self.payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)


class Payload2Config(Payload):
    """
    ### Summary
    Convert an image-policy endpoint payload into a playbook configuration.

    ### Raises
    -   ``ValueError`` if payload is empty.
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
        -   ``ValueError`` if payload is empty.
        """
        method_name = inspect.stack()[0][3]

        if self.payload == {}:
            msg = f"{self.class_name}.{method_name}: "
            msg += "payload is empty."
            raise ValueError(msg)

        payload = copy.deepcopy(self.payload)
        self.config["agnostic"] = payload["agnostic"]
        self.config["epld_image"] = payload["epldImgName"]
        self.config["release"] = payload["nxosVersion"]
        self.config["platform"] = payload["platform"]
        self.config["description"] = payload["policyDescr"]
        self.config["name"] = payload["policyName"]
        self.config["type"] = payload["policyType"]

        self.config["packages"] = {}
        if payload.get("packageName", "") != "":
            self.config["packages"]["install"] = payload["packageName"].split(",")
        else:
            self.config["packages"]["install"] = []
        if payload.get("rpmimages", "") != "":
            self.config["packages"]["uninstall"] = payload["rpmimages"].split(",")
        else:
            self.config["packages"]["uninstall"] = []
