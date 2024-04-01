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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.ruleset import \
    RuleSet
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.template_get import \
    TemplateGet
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_defaults import \
    FabricDefaults


class VerifyPlaybookParams:
    """
    Verify playbook parameters for a controller fabric

    Usage:

    instance = VerifyPlaybookParams(ansible_module)
    instance.config = playbook_config
    instance.refresh_template()
    instance.commit()
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self._template_get = TemplateGet(self.ansible_module)
        self._ruleset = RuleSet()
        self._fabric_defaults = FabricDefaults()
        self.results = Results()
        self.params_are_valid = set()
        self.bad_params = {}

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
        self.properties["template"] = None

    @property
    def config(self):
        """
        getter: return the config to be verified
        setter: set the config to be verified
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

    @property
    def template(self):
        """
        getter: return the template used to verify the playbook config
        setter: set the template used to verify the playbook config
        """
        return self.properties["template"]

    @template.setter
    def template(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "template must be a dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg, **self.results.failed_result)
        self.properties["template"] = value

    def refresh_template(self) -> None:
        """
        Retrieve the template used to verify config
        """
        self._template_get.template_name = "Easy_Fabric"
        self._template_get.refresh()
        self.template = self._template_get.template

    def config_param_value_is_valid(self, parameter, rule) -> bool:
        """
        If parameter is in the playbook config, return boolean returned by:

            eval(config[param] rule[operator] rule[value])

        Return True, otherwise.

        raise ValueError if "op" or "value" keys are not found in rule
        """
        method_name = inspect.stack()[0][3]
        msg = f"parameter: {parameter}, "
        msg += f"rule: {rule}, "
        self.log.debug(msg)
        if parameter not in self.config:
            msg = f"SKIP {parameter}: Not in config.  Returning TRUE."
            self.log.debug(msg)
            return True

        msg = f"parameter: {parameter}, "
        msg += f"rule: {rule}, "
        msg += f"config_value: {self.config[parameter]}"
        self.log.debug(msg)

        operator = rule.get("op", None)
        value = rule.get("value", None)
        if operator is None:
            msg = f"op not found in parameter {parameter} rule: {rule}"
            raise ValueError(msg)
        if value is None:
            msg = f"value not found in parameter {parameter} rule: {rule}"
            raise ValueError(msg)
        result = eval("self.config[parameter] " + operator + " rule['value']")
        msg = f"{self.class_name}.{method_name}: "
        msg += f"EVAL: {self.config[parameter]} {operator} {rule.get('value')} "
        msg += f"result: {result}"
        self.log.debug(msg)
        return result

    def default_param_value_is_valid(self, parameter, rule) -> bool:
        """
        If parameter has a default value, return boolean returned by:

            eval(parameter_default_value rule[operator] rule[value])

        Return False, otherwise.

        raise ValueError if "op" or "value" keys are not found in rule
        """
        method_name = inspect.stack()[0][3]
        default_value = None
        try:
            default_value = self._fabric_defaults.parameter(parameter)
            msg = f"parameter: {parameter}, "
            msg += f"rule: {rule}, "
            msg += f"default {default_value}"
            self.log.debug(msg)
        except KeyError:
            return False

        operator = rule.get("op", None)
        value = rule.get("value", None)
        if operator is None:
            msg = f"op not found in parameter {parameter} rule: {rule}"
            raise ValueError(msg)
        if value is None:
            msg = f"value not found in parameter {parameter} rule: {rule}"
            raise ValueError(msg)

        result = eval("default_value " + operator + " rule['value']")
        msg = f"{self.class_name}.{method_name}: "
        msg += f"EVAL: {default_value} {operator} {rule.get('value')} "
        msg += f"result: {result}"
        self.log.debug(msg)
        return result

    def verify_parameter(self):
        """
        Verify a parameter against the template
        """
        method_name = inspect.stack()[0][3]
        msg = f"self.parameter: {self.parameter}, "
        msg += f"config_value {self.config[self.parameter]}"
        self.log.debug(msg)

        if self.parameter not in self._ruleset.ruleset:
            msg = f"SKIP {self.parameter}: Not in ruleset."
            self.log.debug(msg)
            return

        rule = self._ruleset.ruleset[self.parameter]
        msg = f"ZZZ: parameter: {self.parameter}, "
        msg += f"rule: {json.dumps(rule, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        for key, rule in rule.get("mandatory", {}).items():
            config_is_valid = self.config_param_value_is_valid(key, rule)
            default_is_valid = self.default_param_value_is_valid(key, rule)
            if config_is_valid is False and default_is_valid is False:
                self.params_are_valid.add(False)
                self.bad_params[self.parameter] = {}
                self.bad_params[self.parameter]["config_param"] = self.parameter
                self.bad_params[self.parameter]["config_value"] = self.config[self.parameter]
                self.bad_params[self.parameter]["dependent_param"] = key
                self.bad_params[self.parameter]["dependent_operator"] = rule.get("op")
                self.bad_params[self.parameter]["dependent_value"] = rule.get("value")
            else:
                self.params_are_valid.add(True)

            msg = f"ZZZ: parameter {self.parameter}, "
            msg += f"key: {key}, "
            msg += f"rule: {rule}, "
            msg += f"config_is_valid: {config_is_valid}, "
            msg += f"default_is_valid: {default_is_valid}, "
            msg += f"params_are_valid: {self.params_are_valid}"
            self.log.debug(msg)

        msg = f"self.params_are_valid: {self.params_are_valid}"
        self.log.debug(msg)
        msg = f"self.bad_params: {self.bad_params}"
        self.log.debug(msg)

    def commit(self):
        """
        verify the config against the retrieved template
        """
        method_name = inspect.stack()[0][3]
        if self.config is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.config must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        if self.template is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.refresh_template() must be called prior to calling commit."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        self._ruleset.template = self.template
        self._ruleset.refresh()

        try:
            self._fabric_defaults.template = self.template
        except ValueError as error:
            msg = f"{error}"
            self.log.debug(msg)
            self.ansible_module.fail_json(msg, **self.results.failed_result)
        try:
            self._fabric_defaults.refresh()
        except ValueError as error:
            msg = f"{error}"
            self.log.debug(msg)
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        msg = f"self.config: {json.dumps(self.config, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"self._ruleset.ruleset: {json.dumps(self._ruleset.ruleset, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.params_are_valid = set()
        for self.parameter in self.config:
            self.verify_parameter()

        if False in self.params_are_valid:
            msg = "The following parameter(value) are invalid and need to be reviewed: "
            for key, result in sorted(self.bad_params.items()):
                config_param = result.get("config_param")
                config_value = result.get("config_value")
                dependent_param = result.get("dependent_param")
                dependent_operator = result.get("dependent_operator")
                dependent_value = result.get("dependent_value")
                msg += f"{config_param}({config_value}) requires "
                msg += f"{dependent_param} {dependent_operator} {dependent_value}, "
            msg.rstrip(", ")
            self.log.debug(msg)
            self.ansible_module.fail_json(msg, **self.results.failed_result)
