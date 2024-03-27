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

import copy
import inspect
import logging
from typing import Any, Dict

from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
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

        self.endpoints = ApiEndpoints()
        self.rest_send = RestSend(self.ansible_module)
        self._results = Results(self.ansible_module)
        self.path = None
        self.verb = None

        self.response = []
        self.response_current = {}
        self.result = []
        self.result_current = {}

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

    def _set_templates_endpoint(self) -> None:
        """
        Set the endpoint for the template to be retrieved from the controller.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        try:
            endpoint = self.endpoints.templates
        except ValueError as error:
            raise ValueError(error) from error

        self.path = endpoint.get("path")
        self.verb = endpoint.get("verb")

    def refresh(self):
        """
        Retrieve the templates from the controller.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        self._set_templates_endpoint()

        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.commit()

        self.response_current = copy.deepcopy(self.rest_send.response_current)
        self.response.append(copy.deepcopy(self.rest_send.response_current))
        self.result_current = copy.deepcopy(self.rest_send.result_current)
        self.result.append(copy.deepcopy(self.rest_send.result_current))

        if self.response_current.get("RETURN_CODE", None) != 200:
            msg = f"{self.class_name}.{method_name}: "
            msg = "Exiting. Failed to retrieve templates."
            self.log.error(msg)
            self.ansible_module.fail_json(msg, **self._results.failed_result)

        self.templates = self.result_current