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

from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.template_get import \
    TemplateGet
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.vxlan.template_parse_easy_fabric import \
    TemplateParseEasyFabric


class VerifyPlaybookParams:
    """
    Verify playbook parameters NDFC VxLAN fabric

    Usage:

    instance = VerifyPlaybookParams(ansible_module)
    instance.playbook_config = playbook_config
    instance.commit()
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self._template_get = TemplateGet(self.ansible_module)
        self._template_parse_easy_fabric = TemplateParseEasyFabric()

        self.state = self.ansible_module.params["state"]
        msg = "ENTERED VerifyPlaybookParams(): "
        msg += f"state: {self.state}"
        self.log.debug(msg)

        self._build_properties()

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        self.properties = {}
        self.properties["config"] = None

    @property
    def config(self):
        """
        getter: return the config to verify
        setter: set the config to verify
        """
        return self.properties["config"]

    @config.setter
    def config(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "config must be a dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg)
        self.properties["config"] = value

    def refresh_template(self) -> None:
        """
        Retrieve the template used to verify config
        """
        self._template_get.template_name = "Easy_Fabric"
        self._template_get.refresh()
        self.template = self._template_get.template

    def commit(self):
        """
        verify the config against the retrieved template
        """
        method_name = inspect.stack()[0][3]
        if self.config is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.config must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.failed_result)

        self._template_parse_easy_fabric.template = self.template
        self._template_parse_easy_fabric.build_ruleset()

        msg = f"self.config: {json.dumps(self.config, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        for parameter in self.config:
            result = eval(f"{self._template_parse_easy_fabric.ruleset[parameter.lower()]}")
            if result is True:
                self.log.debug(f"ZZZ Parameter {parameter} is mandatory.")
            else:
                self.log.debug(f"ZZZ Parameter {parameter} is optional.")

