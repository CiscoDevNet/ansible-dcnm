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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_defaults import \
    FabricDefaults
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.ruleset import \
    RuleSet
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.template_get import \
    TemplateGet


class VerifyPlaybookParams:
    """
    Verify playbook parameters for a controller fabric

    Usage:

    fabric_details = FabricDetailsByName(ansible_module)
    fabric_details.refresh()
    fabric_details.filter = "MyFabric"
    if fabric_details.filtered_data is None:
        # fabric does not exist
        instance.config_controller = None
    else:
        instance.config_controller = fabric_details.filtered_data["nvPairs"]

    instance = VerifyPlaybookParams(ansible_module)
    instance.config_playbook = playbook_config
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
        self.parameter = None

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
        self.properties["config_playbook"] = None
        self.properties["config_controller"] = None
        self.properties["template"] = None

    @property
    def config_controller(self):
        """
        getter: return the controller fabric config to be verified
        setter: set the controller fabric config to be verified
        """
        return self.properties["config_controller"]

    @config_controller.setter
    def config_controller(self, value):
        method_name = inspect.stack()[0][3]
        if value is None:
            self.properties["config_controller"] = {}
            return
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "config_controller must be a dict, or None. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg)
        self.properties["config_controller"] = value

    @property
    def config_playbook(self):
        """
        getter: return the playbook config to be verified
        setter: set the playbook config to be verified
        """
        return self.properties["config_playbook"]

    @config_playbook.setter
    def config_playbook(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "config_playbook must be a dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg)
        self.properties["config_playbook"] = value

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

    @staticmethod
    def make_boolean(value):
        """
        Return value converted to boolean, if possible.
        Otherwise, return value.

        TODO: This method is duplicated in several other classes.
        TODO: Would be good to move this to a Utility() class.
        """
        if str(value).lower() in ["true", "yes"]:
            return True
        if str(value).lower() in ["false", "no"]:
            return False
        return value

    @staticmethod
    def make_none(value):
        """
        Return None if value is a string representation of a None type
        Otherwise, return value

        TODO: This method is duplicated in several other classes.
        TODO: Would be good to move this to a Utility() class.
        """
        if str(value).lower in ["", "none", "null"]:
            return None
        return value

    def refresh_template(self) -> None:
        """
        Retrieve the template used to verify config
        """
        msg = "TODO: derive template name from FABRIC_TYPE in playbook config"
        self.log.debug(msg)
        self._template_get.template_name = "Easy_Fabric"
        self._template_get.refresh()
        self.template = self._template_get.template

    def eval_parameter_rule(self, parameter, param_value, rule) -> bool:
        method_name = inspect.stack()[0][3]

        rule_operator = rule.get("op", None)
        if rule_operator is None:
            msg = f"op not found in parameter {parameter} rule: {rule}"
            raise ValueError(msg)

        rule_value = rule.get("value", None)
        if rule_value is None:
            msg = f"value not found in parameter {parameter} rule: {rule}"
            raise ValueError(msg)

        # While eval() can be dangerous with unknown input, the input
        # we're feeding it is from a known source, and has been pretty
        # heavily massaged before it gets here.
        eval_string = f"param_value {rule_operator} rule_value"
        result = eval(eval_string)  # pylint: disable=eval-used

        msg = f"{self.class_name}.{method_name}: "
        msg += "EVAL: "
        msg += f"{param_value} "
        msg += f"{rule_operator} "
        msg += f"{rule_value} "
        msg += f"result: {result}"
        self.log.debug(msg)

        return result

    def controller_param_is_valid(self, parameter, rule) -> bool:
        """
        If the controller fabric config contains the dependent parameter,
        return evaluated result derived from:

            eval(controller_param_value rule_operator rule_value)

        Return None otherwise to remove controller parameter result
        from consideration.

        raise ValueError if "op" or "value" keys are not found in rule
        """
        method_name = inspect.stack()[0][3]
        msg = f"parameter: {parameter}, "
        msg += f"rule: {rule}, "
        self.log.debug(msg)

        # Caller indicated that the fabric does not exist.
        # Return None to remove controller parameter result from consideration.
        if self.config_controller == {}:
            msg = f"Early return: {parameter} fabric does not exist. "
            msg += "Returning None."
            self.log.debug(msg)
            return None

        # The controller config does not contain the parameter.
        # Return None to remove controller parameter result from consideration.
        if parameter not in self.config_controller:
            msg = f"Early return: {parameter} not in config_controller. "
            msg += "Returning None."
            self.log.debug(msg)
            return None

        parameter_value = self.make_boolean(self.config_controller[parameter])
        return self.eval_parameter_rule(parameter, parameter_value, rule)

    def playbook_param_is_valid(self, parameter, rule) -> bool:
        """
        If the playbook config contains the dependent parameter,
        return evaluated result derived from:

            eval(playbook_param rule_operator rule_value)

        Return None otherwise to remove playbook parameter result
        from consideration.

        raise ValueError if "op" or "value" keys are not found in rule
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        # The playbook config does not contain the parameter.
        # Return None to remove playbook parameter result from consideration.
        if parameter not in self.config_playbook:
            msg = f"Early return: {parameter} not in config_playbook. "
            msg += "Returning None."
            self.log.debug(msg)
            return None

        msg = f"parameter: {parameter}, "
        msg += f"rule: {rule}, "
        msg += f"parameter_value: {self.config_playbook[parameter]}"
        self.log.debug(msg)

        parameter_value = self.make_boolean(self.config_playbook[parameter])
        return self.eval_parameter_rule(parameter, parameter_value, rule)

    def default_param_is_valid(self, parameter, rule) -> bool:
        """
        If fabric defaults (from the fabric template) contain the
        dependent parameter parameter return evaluated result
        derived from:

            eval(dependent_param_default_value rule_operator rule_value)

        Return None otherwise to remove default parameter result
        from consideration.

        raise ValueError if "op" or "value" keys are not found in rule
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        # The playbook config contains the parameter.
        # Return None to remove default_param result from consideration.
        if parameter in self.config_playbook:
            msg = f"Early return: parameter: {parameter} in config_playbook. "
            msg += "Returning None."
            self.log.debug(msg)
            return None

        # The controller config contains the parameter.
        # Return None to remove default_param result from consideration.
        if parameter in self.config_controller:
            msg = f"Early return: parameter: {parameter} in config_controller. "
            msg += "Returning None."
            self.log.debug(msg)
            return None

        default_value = None
        try:
            default_value = self._fabric_defaults.parameter(parameter)
        except KeyError:
            # A default value does not exist for parameter.
            # Return None to remove default_param result from consideration.
            msg = f"Early return: parameter: {parameter} has no default value. "
            msg += "Returning None."
            self.log.debug(msg)
            return None

        return self.eval_parameter_rule(parameter, default_value, rule)

    def update_decision_set(self, dependent_param, rule):
        decision_set = set()
        controller_is_valid = self.controller_param_is_valid(dependent_param, rule)
        playbook_is_valid = self.playbook_param_is_valid(dependent_param, rule)
        default_is_valid = self.default_param_is_valid(dependent_param, rule)

        if controller_is_valid is not None:
            decision_set.add(controller_is_valid)
        if default_is_valid is not None:
            decision_set.add(default_is_valid)
        if playbook_is_valid is not None:
            decision_set.add(playbook_is_valid)
        # If playbook config is not valid, ignore all other results
        if not playbook_is_valid:
            decision_set = {False}

        msg = f"parameter {self.parameter}, "
        msg += f"dependent_param: {dependent_param}, "
        msg += f"rule: {rule}, "
        msg += f"controller_is_valid: {controller_is_valid}, "
        msg += f"playbook_is_valid: {playbook_is_valid}, "
        msg += f"default_is_valid: {default_is_valid}, "
        msg += f"params_are_valid: {self.params_are_valid}, "
        msg += f"decision_set: {decision_set}"
        self.log.debug(msg)

        return decision_set

    def verify_parameter(self):
        """
        Verify a parameter against the template
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        if self.parameter not in self._ruleset.ruleset:
            msg = f"SKIP {self.parameter}: Not in ruleset."
            self.log.debug(msg)
            return

        # Used in bad_params to help the user identify which fabric
        # contains the bad parameters.
        fabric_name = self.config_playbook.get("FABRIC_NAME")
        if fabric_name is None:
            msg = "FABRIC_NAME not found in playbook config."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        msg = "self.parameter: "
        msg += f"{self.parameter}, "
        msg += "config_playbook_value: "
        msg += f"{self.config_playbook.get(self.parameter)}, "
        msg += "config_controller_value: "
        msg += f"{self.config_controller.get(self.parameter)}"
        self.log.debug(msg)

        param_rule = self._ruleset.ruleset[self.parameter]

        for dependent_param, rule in param_rule.get("mandatory", {}).items():
            decision_set = self.update_decision_set(dependent_param, rule)

            # bad_params[fabric][param] = <list of bad_param dict>
            if True not in decision_set:
                self.params_are_valid.add(False)

                if fabric_name not in self.bad_params:
                    self.bad_params[fabric_name] = {}
                if self.parameter not in self.bad_params[fabric_name]:
                    self.bad_params[fabric_name][self.parameter] = []
                bad_param = {}
                bad_param["fabric_name"] = fabric_name
                bad_param["config_param"] = self.parameter
                bad_param["config_value"] = self.config_playbook[self.parameter]
                bad_param["dependent_param"] = dependent_param
                bad_param["dependent_operator"] = rule.get("op")
                bad_param["dependent_value"] = rule.get("value")
                self.bad_params[fabric_name][self.parameter].append(bad_param)
            else:
                self.params_are_valid.add(True)

        msg = f"self.params_are_valid: {self.params_are_valid}"
        self.log.debug(msg)

    def validate_commit_parameters(self):
        """
        fail_json if required parameters are not set
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        if self.config_controller is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.config_controller "
            msg += "must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        if self.config_playbook is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.config_playbook "
            msg += "must be set prior to calling commit."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

        if self.template is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.refresh_template() "
            msg += "must be called prior to calling commit."
            self.ansible_module.fail_json(msg, **self.results.failed_result)

    def update_fabric_defaults(self):
        """
        Update fabric parameter default values based on
        the fabric template
        """
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

    def update_ruleset(self):
        """
        Update the fabric parameter ruleset based on the fabric template
        """
        self._ruleset.template = self.template
        self._ruleset.refresh()

        msg = "self._ruleset.ruleset: "
        msg += f"{json.dumps(self._ruleset.ruleset, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def commit(self):
        """
        verify the config against the retrieved template
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        self.validate_commit_parameters()
        self.update_ruleset()
        self.update_fabric_defaults()

        msg = "self.config_playbook: "
        msg += f"{json.dumps(self.config_playbook, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.params_are_valid = set()
        for self.parameter in self.config_playbook:
            self.verify_parameter()
        if False not in self.params_are_valid:
            return

        msg = "The following parameter(value) combination(s) are invalid "
        msg += "and need to be reviewed: "
        # bad_params[fabric][param] = <list of bad param dict>
        for fabric_name in self.bad_params:
            msg += f"Fabric: {fabric_name}, "
            for _, bad_param_list in self.bad_params[fabric_name].items():
                for bad_param in bad_param_list:
                    config_param = bad_param.get("config_param")
                    config_value = bad_param.get("config_value")
                    dependent_param = bad_param.get("dependent_param")
                    dependent_operator = bad_param.get("dependent_operator")
                    dependent_value = bad_param.get("dependent_value")
                    msg += f"{config_param}({config_value}) requires "
                    msg += f"{dependent_param} {dependent_operator} {dependent_value}, "
            msg.rstrip(", ")
        self.log.debug(msg)
        self.ansible_module.fail_json(msg, **self.results.failed_result)
