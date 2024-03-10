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
__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect
import json
import logging
from typing import Any, Dict
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_fabric import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.results import \
    Results

class TemplateGetAll:
    """
    Retrieve a list of all templates from the controller.

    Usage:

    instance = TemplateGetAll()
    instance.refresh()
    templates = instance.templates
    """
    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module
        self.state = self.ansible_module.params["state"]
        self.check_mode = self.ansible_module.check_mode

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED TemplateGetAll(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self._endpoints = ApiEndpoints()
        self._rest_send = RestSend()
        self._results = Results(self.ansible_module)
        self._init_properties()

    def _init_properties(self) -> None:
        self._properties = {}
        self._properties["templates"] = None

    @property
    def templates(self):
        """
        Return the templates retrieved from the controller.
        """
        return self._properties["templates"]

    @templates.setter
    def templates(self, value: Dict[str, Any]) -> None:
        self._properties["templates"] = value

    def refresh(self):
        """
        Retrieve the templates from the controller.
        """
        method_name = inspect.stack()[0][3]

        try:
            self.endpoint = self._endpoints.templates
        except ValueError as error:
            raise ValueError(error)

        self._rest_send.path = self.endpoint.get("path")
        self._rest_send.verb = self.endpoint.get("verb")
        self._rest_send.commit()

        self.response_current = self._rest_send.response_current
        self.response = self._rest_send.response_current
        self.result_current = self._rest_send.result_current
        self.result = self._rest_send.result_current

        if self.response_current.get("RETURN_CODE", None) != 200:
            msg = f"{self.class_name}.{method_name}: "
            msg = "Exiting. Failed to retrieve templates."
            self.log.error(msg)
            self.ansible_module.fail_json(msg, **self._results.failed_result)

        self.templates = self.result_current

        msg = f"{self.class_name}.{method_name}: "
        msg += f"templates: {json.dumps(self.templates, indent=4, sort_keys=True)}"
