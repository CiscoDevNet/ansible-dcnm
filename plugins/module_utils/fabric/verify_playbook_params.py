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

from ..common.conversion import ConversionUtils
from .param_info import ParamInfo
from .ruleset import RuleSet


class VerifyPlaybookParams:
    """
    - Verify playbook parameters for a controller fabric.

    VerifyPlaybookParams() uses three sources of information in its
    verification of the user's playbook parameters:

    1. The controller fabric configuration (retrieved from the controller)
    2. The fabric template (retrieved from the controller)
    3. The playbook configuration

    The basic workflow is to retrieve each of these, pass them into
    an instance of VerifyPlaybookParams(), and then call
    VerifyPlaybookParams.commit(), which does the verification.

    ## Usage:

    ```python
    # 1. Instantiate the VerifyPlaybookParams class
    verify = VerifyPlaybookParams()

    #---------------------------------------------------------------
    # 2. Retrieve the fabric configuration from controller (here we
    #    use the FabricDetailsByName() class to retrieve the fabric
    #    configuration).  VerifyPlaybookParams() wants only the
    #    nvPairs content of the fabric configuration.
    #---------------------------------------------------------------
    fabric = FabricDetailsByName(ansible_module)
    fabric.refresh()
    fabric.filter = "MyFabric"

    # Add the fabric configuration (if any) to VerifyPlaybookParams()
    if fabric.filtered_data is None:
        # fabric does not exist
        verify.config_controller = None
    else:
        try:
            verify.config_controller = fabric.filtered_data["nvPairs"]
        except ValueError as error:
            ansible_module.fail_json(error, **self.results.failed_result)

    #---------------------------------------------------------------
    # 2. Retrieve the appropriate fabric template (here we use the
    #    TemplateGet() class to retrieve the Easy_Fabric template)
    #---------------------------------------------------------------
    template = TemplateGet()
    template.rest_send = RestSend(ansible_module)
    template.template_name = "Easy_Fabric"
    template.refresh()

    # Add the template to the VerifyPlaybookParams instance
    try:
        verify.template = template.template
    except TypeError as error:
        ansible_module.fail_json(error, **self.results.failed_result)

    #---------------------------------------------------------------
    # 3. Add the playbook config to the VerifyPlaybookParams instance
    #    typically this is retrieved with get_want() within the
    #    main task module.
    #---------------------------------------------------------------
    try:
        verify.config_playbook = playbook_config
    except TypeError as error:
        ansible_module.fail_json(error, **self.results.failed_result)

    # Perform the verification
    try:
        verify.commit()
    except(ValueError, KeyError) as error:
        ansible_module.fail_json(error, **self.results.failed_result)
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.conversion = ConversionUtils()
        self._ruleset = RuleSet()
        self._param_info = ParamInfo()
        self.bad_params = {}
        self.fabric_name = None
        self.local_params = {"DEPLOY"}
        self.parameter = None
        self.params_are_valid = set()

        msg = "ENTERED VerifyPlaybookParams(): "
        self.log.debug(msg)

        self._init_properties()

    def _init_properties(self):
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
        -   getter: return the controller fabric config to be verified.
        -   setter: set the controller fabric config to be verified.
        -   setter: raise ``TypeError`` if the controller config is not a dict.
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
            msg += f"{method_name} must be a dict, or None. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        self.properties["config_controller"] = value

    @property
    def config_playbook(self):
        """
        -   getter: return the playbook config to be verified
        -   setter: set the playbook config to be verified
        -   setter: raise TypeError if playbook config is not a dict
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
            raise TypeError(msg)
        self.properties["config_playbook"] = value

    @property
    def template(self):
        """
        -   getter: return the template used to verify the playbook config
        -   setter: set the template used to verify the playbook config
        -   setter: raise TypeError if template is not a dict
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
            raise TypeError(msg)
        self.properties["template"] = value

    def eval_parameter_rule(self, rule) -> bool:
        """
        -   Evaluate a user parameter value against a rule from
            the fabric template.
        -   Return the result of the evaluation.
        -   Raise KeyError if the rule does not contain expected keys.

        - rule format:
        ```python
        {
            "user_value": <user value for parameter>,
            "parameter": "parameter_name",
            "operator": "operator",
            "value": "<template value for parameter>"
        }
        ```

        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"rule: {rule}"
        self.log.debug(msg)

        parameter = rule.get("parameter", None)
        if parameter is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"'parameter' not found in rule: {rule}"
            raise KeyError(msg)

        user_value = rule.get("user_value", None)
        if user_value is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"'user_value' not found in parameter {parameter} rule: {rule}"
            raise KeyError(msg)

        operator = rule.get("operator", None)
        if operator is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"'operator' not found in parameter {parameter} rule: {rule}"
            raise KeyError(msg)

        rule_value = rule.get("value", None)
        if rule_value is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"'value' not found in parameter {parameter} rule: {rule}"
            raise KeyError(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"parameter: {parameter}, "
        msg += f"user_value: {user_value}, "
        msg += f"operator: {operator}, "
        msg += f"rule_value: {rule_value}"
        self.log.debug(msg)

        if rule_value in [None, "", "null"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rule_value is None. Returning True."
            self.log.debug(msg)
            return True
        if user_value in [None, "", "null"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"playbook value for parameter {parameter} cannot be null"
            self.log.debug(msg)
            raise ValueError(msg)

        eval_string = f"user_value {operator} rule_value"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"eval_string {eval_string}"
        self.log.debug(msg)
        # While eval() can be dangerous with unknown input, the input
        # we're feeding it is from a known source and has been pretty
        # heavily massaged before it gets here.
        result = eval(eval_string)  # pylint: disable=eval-used

        msg = f"{self.class_name}.{method_name}: "
        msg += "EVAL: "
        msg += f"{user_value} "
        msg += f"{operator} "
        msg += f"{rule_value} "
        msg += f"result: {result}"
        self.log.debug(msg)

        return result

    def controller_param_is_valid(self, item) -> bool:
        """
        -   Return None in the following cases
            -   The fabric does not exist on the controller.
            -   The controller's value for the dependent parameter is None
                (more accurately, "")
            -   The controller fabric config does not contain the dependent
                parameter (this is not likely)

        Returning One removes the controller result from consideration
        when determining parameter validity.

        -   Return the evaluated result (True or False) if the controller
            fabric config does contain the dependent parameter.  The
            evaluated result is calculated from:

        eval(controller_param_value rule_operator rule_value)

        -   raise KeyError if self.eval_parameter_rule() fails
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        rule_parameter = item.get("parameter", None)
        rule_value = item.get("value", None)
        rule_operator = item.get("operator", None)

        msg = f"{self.class_name}.{method_name}: "
        msg = f"rule_parameter: {rule_parameter}, "
        msg += f"rule_operator: {rule_operator}, "
        msg += f"rule_value: {rule_value}, "
        self.log.debug(msg)

        # Caller indicated that the fabric does not exist.
        # Return None to remove controller parameter result from consideration.
        if self.config_controller == {}:
            msg = f"Early return: {rule_parameter} fabric does not exist. "
            msg += "Returning None."
            self.log.debug(msg)
            return None

        # The controller config does not contain the parameter.
        # Return None to remove controller parameter result from consideration.
        if rule_parameter not in self.config_controller:
            msg = f"Early return: {rule_parameter} not in config_controller. "
            msg += "Returning None."
            self.log.debug(msg)
            return None

        controller_value = self.conversion.make_none(
            self.conversion.make_boolean(self.config_controller[rule_parameter])
        )

        msg = f"{self.class_name}.{method_name}: "
        msg += f"parameter {rule_parameter}, "
        msg += f"controller_value: type {type(controller_value)}, "
        msg += f"value {controller_value}"
        self.log.debug(msg)

        # If the controller value is None, remove it from consideration.
        if controller_value is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Early return: {rule_parameter} is None.  Returning None."
            self.log.debug(msg)
            return None
        # update item with user's parameter value
        item["user_value"] = controller_value
        try:
            return self.eval_parameter_rule(item)
        except KeyError as error:
            raise KeyError(f"{error}") from error

    def playbook_param_is_valid(self, item) -> bool:
        """
        -   Return None if the playbook config does not contain the
            dependent parameter. This removes the playbook parameter from
            consideration when determining parameter validity
        -   Return evaluated result if the playbook config does contain
            the dependent parameter.  The evaluated result is calculated
            from:

            eval(playbook_param rule_operator rule_value)

        -   raise KeyError if self.eval_parameter_rule() fails
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        rule_parameter = item.get("parameter", None)
        rule_value = item.get("value", None)
        rule_operator = item.get("operator", None)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"rule_parameter: {rule_parameter}, "
        msg += f"rule_operator: {rule_operator}, "
        msg += f"rule_value: {rule_value}, "
        self.log.debug(msg)

        # The playbook config does not contain the parameter.
        # Return None to remove playbook parameter result from consideration.
        if rule_parameter not in self.config_playbook:
            msg = f"Early return: {rule_parameter} not in config_playbook. "
            msg += "Returning None."
            self.log.debug(msg)
            return None

        playbook_value = self.conversion.make_none(
            self.conversion.make_boolean(self.config_playbook[rule_parameter])
        )

        msg = f"{self.class_name}.{method_name}: "
        msg += f"parameter {rule_parameter}, "
        msg += f"controller_value: type {type(playbook_value)}, "
        msg += f"value {playbook_value}"
        self.log.debug(msg)

        # update item with playbook's parameter value
        item["user_value"] = playbook_value
        try:
            return self.eval_parameter_rule(item)
        except KeyError as error:
            raise KeyError(f"{error}") from error

    def default_param_is_valid(self, item) -> bool:
        """
        -   Return None if the fabric defaults (in the fabric template)
            do not contain the dependent parameter. This removes the
            default value from consideration when determining
            parameter validity.
        -   Return evaluated result if the fabric defaults(in the fabric
            template) do contain the dependent parameter.  The evaluated
            result is calculated from:

        eval(dependent_param_default_value rule_operator rule_value)

        -   raise KeyError if self.eval_parameter_rule() fails
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        rule_parameter = item.get("parameter", None)
        rule_value = item.get("value", None)
        rule_operator = item.get("operator", None)

        msg = f"{self.class_name}.{method_name}: "
        msg = f"rule_parameter: {rule_parameter}, "
        msg += f"rule_operator: {rule_operator}, "
        msg += f"rule_value: {rule_value}, "
        self.log.debug(msg)

        # The playbook config contains the parameter.
        # Return None to remove default_param result from consideration.
        if rule_parameter in self.config_playbook:
            msg = f"Early return: parameter: {rule_parameter} in config_playbook. "
            msg += "Returning None."
            self.log.debug(msg)
            return None
        # The controller config contains the parameter.
        # Return None to remove default_param result from consideration.
        if rule_parameter in self.config_controller:
            msg = f"Early return: parameter: {rule_parameter} in config_controller. "
            msg += "Returning None."
            self.log.debug(msg)
            return None

        default_value = self._param_info.parameter(rule_parameter).get("default", None)
        if default_value is None:
            msg = f"Early return: parameter: {rule_parameter} "
            msg += "has no default value. Returning None."
            self.log.debug(msg)
            return None

        # update item with user's parameter value
        item["user_value"] = default_value

        try:
            return self.eval_parameter_rule(item)
        except KeyError as error:
            raise KeyError(f"{error}") from error

    def update_decision_set(self, item) -> set:
        """
        ### Summary
        Update the decision set with the aggregate of results from the
        - controller fabric configuration
        - playbook configuration
        - fabric defaults (from the fabric template)

        - Return the decision set if no errors occur
        - Raise KeyError if controller_param_is_valid() fails
        - Raise KeyError if playbook_param_is_valid() fails
        - Raise KeyError if default_param_is_valid() fails

        ### item format
        item is a dictionary with the following keys
        - parameter: the parameter from the controller config, playbook, or template default
        - operator: The rule operator e.g. "==", "!="
        - value: The parameter's value in the controller config, playbook, or template default
        - Example
          ```json
          {'parameter': 'UNDERLAY_IS_V6', 'operator': '!=', 'value': True}
          ```

        ### Notes
        1. If all of the following return None, then we add True to the decision_set.
           - controller_param_is_valid()
           - playbook_param_is_valid()
           - default_param_is_valid()
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        decision_set = set()

        msg = f"{self.class_name}.{method_name}: "
        msg += f"item {item}"
        self.log.debug(msg)

        parameter = item.get("parameter")

        try:
            controller_is_valid = self.controller_param_is_valid(item)
        except KeyError as error:
            raise KeyError(f"{error}") from error

        msg = f"{self.class_name}.{method_name}: "
        msg += f"parameter: {parameter}, "
        msg += f"controller_is_valid: {controller_is_valid}"
        self.log.debug(msg)

        try:
            playbook_is_valid = self.playbook_param_is_valid(item)
        except KeyError as error:
            raise KeyError(f"{error}") from error

        msg = f"{self.class_name}.{method_name}: "
        msg += f"parameter: {parameter}, "
        msg += f"playbook_is_valid: {playbook_is_valid}"
        self.log.debug(msg)

        try:
            default_is_valid = self.default_param_is_valid(item)
        except KeyError as error:
            raise KeyError(f"{error}") from error

        msg = f"{self.class_name}.{method_name}: "
        msg += f"parameter: {parameter}, "
        msg += f"default_is_valid: {default_is_valid}"
        self.log.debug(msg)

        if controller_is_valid is not None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"parameter: {parameter}, add to decision set: "
            msg += f"controller_is_valid: {controller_is_valid}"
            self.log.debug(msg)
            decision_set.add(controller_is_valid)
        if default_is_valid is not None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"parameter: {parameter}, add to decision set: "
            msg += f"default_is_valid: {default_is_valid}"
            self.log.debug(msg)
            decision_set.add(default_is_valid)
        if playbook_is_valid is not None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"parameter: {parameter}, add to decision set: "
            msg += f"playbook_is_valid: {playbook_is_valid}"
            self.log.debug(msg)
            decision_set.add(playbook_is_valid)

        # If playbook config is not valid, ignore all other results
        if playbook_is_valid is False:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"parameter: {parameter}, "
            msg += f"playbook is invalid: {playbook_is_valid}. "
            msg += "Setting decision_set to False."
            self.log.debug(msg)
            decision_set = {False}

        msg = f"{self.class_name}.{method_name}: "
        msg += f"parameter: {parameter}, "
        msg += f"decision_set: ({decision_set})"
        self.log.debug(msg)

        # If the decision_set is empty, add True.
        if len(decision_set) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"parameter: {parameter}, "
            msg += "decision_set is empty. Setting to True."
            self.log.debug(msg)
            decision_set = {True}

        msg = f"parameter {self.parameter}, "
        msg += f"item: {item}, "
        msg += f"controller_is_valid: {controller_is_valid}, "
        msg += f"playbook_is_valid: {playbook_is_valid}, "
        msg += f"default_is_valid: {default_is_valid}, "
        msg += f"params_are_valid: {self.params_are_valid}, "
        msg += f"decision_set: {decision_set}"
        self.log.debug(msg)

        return decision_set

    def verify_parameter_value(self) -> None:
        """
        -   Verify a parameter's value against valid choices (if any)
            culled from the template.
        -   Return if the parameter is found in the template, and the parameter
            value matches a valid choice in the template.
        -   Return if the parameter is found in the template, the template does
            not contain choices for the parameter.
        -   Skip "local" parameters -- i.e. parameters that are valid in a
            playbook, but are not found in the template -- for example
            ``DEPLOY``, after performing basic verification.
        -   Raise ``KeyError`` if a (non-local) parameter is not found in
            the template.
        -   Raise ``ValueError`` for all parameters, if the parameter value
            is a boolean string.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        playbook_value = self.config_playbook.get(self.parameter)

        # Reject quoted boolean values e.g. "False", "true"
        # try:
        #     self.conversion.reject_boolean_string(self.parameter, playbook_value)
        # except ValueError as error:
        #     playbook_value = self.conversion.make_boolean(playbook_value)
        #     raise ValueError(error) from error

        # Skip "local" parameters i.e. parameters that are valid in a
        # playbook but not found in the template retrieved from the controller
        # e.g. DEPLOY
        if self.parameter in self.local_params:
            return

        # raise KeyError if the parameter is not found in the template
        try:
            param_info = self._param_info.parameter(self.parameter)
        except KeyError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"parameter: {self.parameter} not found in template. "
            msg += f"Error detail: {error}"
            self.log.debug(msg)
            return

        # Return if the parameter is found in the template and the template
        # does not mandate specific choices for the parameter
        if param_info["choices"] is None:
            return

        # Convert string representations of integers to integers
        playbook_value = self.conversion.make_int(playbook_value)

        # Try to convert to boolean, for comparison purposes, if the
        # parameter's type is defined to be boolean in the template.
        if param_info["type"] == "boolean":
            playbook_value = self.conversion.make_boolean(playbook_value)
        # If the user specifies 0/1 for False/True, NDFC fails with a 500 error
        # (at least for ADVERTISE_PIP_BGP).  Let's mandate that the user cannot
        # use 0/1 as a substitute for boolean values and fail here instead.
        # NOTE: self.conversion.make_int() should not (and does not)
        # convert boolean values to integers.
        if param_info["type"] == "boolean" and not isinstance(playbook_value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Parameter: {self.parameter}, "
            msg += f"Invalid value: ({playbook_value}). "
            msg += f"Valid values: {param_info['choices']}"
            raise ValueError(msg)

        # Return if the parameter is found in the template and the parameter
        # value matches a valid choice for the parameter
        if playbook_value in param_info["choices"]:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Parameter: {self.parameter}, "
            msg += f"playbook_value ({playbook_value}). "
            msg += f"in valid values: {param_info['choices']}. "
            msg += "Returning."
            self.log.debug(msg)
            return

        # Raise ValueError if the parameter value does not match any of the
        # choices specified in the template for the parameter
        msg = f"{self.class_name}.{method_name}: "
        msg += f"Parameter: {self.parameter}, "
        msg += f"Invalid value: ({playbook_value}). "
        msg += f"Valid values: {param_info['choices']}"
        raise ValueError(msg)

    def update_decision_set_for_and_rules(self, param_rule) -> None:
        """
        -   Update the decision set for rules containing only AND'd terms.
        -   Update self.params_are_valid with the result of the decision set.
        -   Add the parameter to the bad_params dict if the controller
            would return an error for the parameter (i.e. the updated
            decision set does not contain True).
        -   Raise ``KeyError`` if an error is encountered while updating
            the decision set.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        for item in param_rule.get("terms", {}).get("and"):
            try:
                decision_set = self.update_decision_set(item)
            except KeyError as error:
                raise KeyError(f"{error}") from error

            msg = f"{self.class_name}.{method_name}: "
            msg += f"decision_set: ({decision_set})"
            self.log.debug(msg)

            # bad_params[fabric][param] = <list of bad_param dict>
            if True not in decision_set:
                self.params_are_valid.add(False)

                if self.fabric_name not in self.bad_params:
                    self.bad_params[self.fabric_name] = {}
                if self.parameter not in self.bad_params[self.fabric_name]:
                    self.bad_params[self.fabric_name][self.parameter] = []
                bad_param = {}
                bad_param["fabric_name"] = self.fabric_name
                bad_param["config_param"] = self.parameter
                bad_param["config_value"] = self.config_playbook[self.parameter]
                bad_param["dependent_param"] = item.get("parameter")
                bad_param["dependent_operator"] = item.get("operator")
                bad_param["dependent_value"] = item.get("value")
                bad_param["boolean_operator"] = "and"
                self.bad_params[self.fabric_name][self.parameter].append(bad_param)
            else:
                self.params_are_valid.add(True)

    def update_decision_set_for_or_rules(self, param_rule) -> None:
        """
        -   Update the decision set for rules containing only OR'd terms.
        -   Update self.params_are_valid with the result of the decision set.
        -   Add the parameter to the bad_params dict if the controller
            would return an error for the parameter (i.e. the updated
            decision set does not contain True).
        -   Raise ``KeyError`` if an error is encountered while updating
            the decision set.
        -   Raise ``ValueError`` if an unexpected number of dependent
            parameters are found in param_rule.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        decision_set = set()
        # valid_values is used in the error message for OR'd parameters
        valid_values = set()
        terms = param_rule.get("terms", {}).get("or")

        # update decision_set with the aggregate of results from
        # all terms in the rule.
        for item in terms:
            valid_values.add(item.get("value"))
            try:
                decision_set.update(self.update_decision_set(item))
            except KeyError as error:
                raise KeyError(f"{error}") from error

        # Update params_are_valid with True and return if all params are valid.
        if True in decision_set:
            self.params_are_valid.add(True)
            return

        # Update params_are_valid with False and populate self.bad_params
        # if any of the params were invalid.
        self.params_are_valid.add(False)

        # bad_params[fabric][param] = <list of bad_param dict>
        if self.fabric_name not in self.bad_params:
            self.bad_params[self.fabric_name] = {}
        if self.parameter not in self.bad_params[self.fabric_name]:
            self.bad_params[self.fabric_name][self.parameter] = []

        # OR'd parameters have (thus far) only had one dependent parameter.
        # Specifically, STP_BRIDGE_PRIORITY has two rule terms, each with the
        # same dependent parameter (STP_ROOT_OPTION) but with different values
        # (mst and rstp+).  Raise a ValueError here to alert us if this
        # ever changes.
        verify_one_dependent_parameter_is_present = set()
        for item in terms:
            verify_one_dependent_parameter_is_present.add(item.get("parameter"))
        if len(verify_one_dependent_parameter_is_present) != 1:
            msg = f"{self.class_name}.{method_name}: "
            msg += "OR'd parameters must have one dependent parameter. Got: "
            # sorted(list()) because set() ordering is random which destabilizes
            # unit test regex match.  Also, it's good for consistent
            # (i.e. alphabetized) error messages for the user.
            msg += f"{sorted(list(verify_one_dependent_parameter_is_present))}. "
            msg += f"parameter {self.parameter}, rule {param_rule}."
            raise ValueError(msg)

        bad_param = {}
        bad_param["fabric_name"] = self.fabric_name
        bad_param["config_param"] = self.parameter
        bad_param["config_value"] = self.config_playbook[self.parameter]
        bad_param["dependent_param"] = terms[0].get("parameter")
        bad_param["dependent_operator"] = terms[0].get("operator")
        bad_param["dependent_value"] = valid_values
        bad_param["boolean_operator"] = "or"
        self.bad_params[self.fabric_name][self.parameter].append(bad_param)

    def update_decision_set_for_na_rules(self, param_rule) -> str:
        """
        -   eval() a rule that contains the key 'na'
        -   Raise ``KeyError`` if the rule does not contain keys:
            - ["na"]
            - ["na"]["terms")
        - Raise ``ValueError`` if the rule["na"]["terms"] does not contain one element
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "

        if len(param_rule.get("terms", {}).get("na")) != 1:
            msg += "Rules not containing boolean operators must "
            msg += "contain one term. "
            msg += f"Got rule: {param_rule}"
            raise ValueError(msg)

        for item in param_rule.get("terms", {}).get("na"):
            try:
                decision_set = self.update_decision_set(item)
            except KeyError as error:
                raise KeyError(f"{error}") from error

            # bad_params[fabric][param] = <list of bad_param dict>
            if True not in decision_set:
                self.params_are_valid.add(False)

                if self.fabric_name not in self.bad_params:
                    self.bad_params[self.fabric_name] = {}
                if self.parameter not in self.bad_params[self.fabric_name]:
                    self.bad_params[self.fabric_name][self.parameter] = []
                bad_param = {}
                bad_param["fabric_name"] = self.fabric_name
                bad_param["config_param"] = self.parameter
                bad_param["config_value"] = self.config_playbook[self.parameter]
                bad_param["dependent_param"] = item.get("parameter")
                bad_param["dependent_operator"] = item.get("operator")
                bad_param["dependent_value"] = item.get("value")
                bad_param["boolean_operator"] = "na"
                self.bad_params[self.fabric_name][self.parameter].append(bad_param)
            else:
                self.params_are_valid.add(True)

    def verify_parameter(self):
        """
        Verify a parameter against the template.

        -   Raise ``ValueError`` if FABRIC_NAME is not present in the playbook.
        -   Raise ``ValueError`` if the parameter does not match any of the
            valid values specified in the template for the parameter
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        # self.fabric_name is used in:
        #   - bad_params to help the user identify which
        #     fabric contains the bad parameter(s)
        #   - verify_parameter_value() raise message
        self.fabric_name = self.config_playbook.get("FABRIC_NAME", None)
        if self.fabric_name is None:
            msg = "FABRIC_NAME not found in playbook config."
            raise ValueError(msg)

        # Verify the parameter value against a list of valid choices
        # in the template.
        try:
            self.verify_parameter_value()
        except ValueError as error:
            raise ValueError(error) from error

        if self.parameter not in self._ruleset.ruleset:
            msg = f"SKIP {self.parameter}: Not in ruleset."
            self.log.debug(msg)
            return

        msg = "self.parameter: "
        msg += f"{self.parameter}, "
        msg += "config_playbook_value: "
        msg += f"{self.config_playbook.get(self.parameter)}, "
        msg += "config_controller_value: "
        msg += f"{self.config_controller.get(self.parameter)}"
        self.log.debug(msg)

        param_rule = self._ruleset.ruleset[self.parameter]
        case_and_rule = "and" in param_rule.get("terms") and "or" not in param_rule.get(
            "terms"
        )
        case_or_rule = "or" in param_rule.get("terms") and "and" not in param_rule.get(
            "terms"
        )
        case_na_rule = "na" in param_rule.get("terms")
        msg = f"{self.class_name}.{method_name}: "
        msg += f"PRE_UPDATE: self.params_are_valid: {self.params_are_valid}"
        self.log.debug(msg)
        try:
            if case_and_rule:
                self.update_decision_set_for_and_rules(param_rule)
                msg = f"{self.class_name}.{method_name}: "
                msg += f"UPDATE_FOR_AND_RULES: parameter: {self.parameter} self.params_are_valid: {self.params_are_valid}"
                self.log.debug(msg)
            elif case_or_rule:
                self.update_decision_set_for_or_rules(param_rule)
                msg = f"{self.class_name}.{method_name}: "
                msg += f"UPDATE_FOR_OR_RULES: parameter: {self.parameter} self.params_are_valid: {self.params_are_valid}"
                self.log.debug(msg)
            elif case_na_rule:
                self.update_decision_set_for_na_rules(param_rule)
                msg = f"{self.class_name}.{method_name}: "
                msg += f"UPDATE_FOR_NA_RULES: parameter: {self.parameter} self.params_are_valid: {self.params_are_valid}"
                self.log.debug(msg)
            else:
                msg = f"{self.class_name}.{method_name}: "
                msg += "TODO: Unhandled parameter rule: "
                msg += f"parameter {self.parameter}, "
                msg += f"rule: {param_rule}"
                self.log.debug(msg)
        except (KeyError, ValueError) as error:
            raise ValueError(error) from error

        msg = f"self.params_are_valid: {self.params_are_valid}"
        self.log.debug(msg)

    def validate_commit_parameters(self):
        """
        raise ValueError if required parameters are not set
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        if self.config_controller is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.config_controller "
            msg += "must be set prior to calling commit."
            raise ValueError(msg)

        if self.config_playbook is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.config_playbook "
            msg += "must be set prior to calling commit."
            raise ValueError(msg)

        if self.template is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.template "
            msg += "must be set prior to calling commit."
            raise ValueError(msg)

    def update_param_info(self):
        """
        Update the fabric parameter info based on the fabric template

        -   raise TypeError if the template is not a dict
        -   raise ValueError if ParamInfo.refresh() fails
        """
        try:
            self._param_info.template = self.template
        except TypeError as error:
            raise TypeError(f"{error}") from error

        try:
            self._param_info.refresh()
        except ValueError as error:
            raise ValueError(error) from error

        msg = "self._param_info.info: "
        msg += f"{json.dumps(self._param_info.info, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def update_ruleset(self):
        """
        Update the fabric parameter ruleset based on the fabric template
        """
        self._ruleset.template = self.template
        self._ruleset.refresh()

        msg = "self._ruleset.ruleset: "
        msg += f"{json.dumps(self._ruleset.ruleset, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def generate_error_message(self):
        """
        -   Generate an error message describing the bad parameters and their
            respective resolutions.
        -   Raise ``ValueError`` with this error message so the the main
            task module can catch and handle the error.
        """
        msg = "The following parameter(value) combination(s) are invalid "
        msg += "and need to be reviewed: "

        # bad_params[fabric][param] = <list of bad param dict>
        for fabric_name, fabric_dict in self.bad_params.items():
            msg += f"Fabric: {fabric_name}, "
            for bad_param_list in fabric_dict.values():
                for bad_param in bad_param_list:
                    boolean_operator = bad_param.get("boolean_operator")
                    config_param = bad_param.get("config_param")
                    config_value = bad_param.get("config_value")
                    dependent_param = bad_param.get("dependent_param")
                    dependent_operator = bad_param.get("dependent_operator")
                    dependent_value = bad_param.get("dependent_value")

                    msg += f"{config_param}({config_value}) requires "
                    if boolean_operator == "or":
                        msg += f"{dependent_param} to be one of "
                        msg += f"[{', '.join(sorted(dependent_value))}]. "
                        msg += f"{dependent_param} valid values: "
                        msg += f"{self._param_info.info[dependent_param]['choices']}. "
                    if boolean_operator == "and":
                        msg += f"{dependent_param} {dependent_operator} {dependent_value}, "
                        msg += f"{dependent_param} valid values: "
                        msg += f"{self._param_info.info[dependent_param]['choices']}. "
                    if boolean_operator == "na":
                        msg += f"{dependent_param} {dependent_operator} {dependent_value}. "
                        msg += f"{dependent_param} valid values: "
                        msg += f"{self._param_info.info[dependent_param]['choices']}. "

            msg.rstrip(", ")
        self.log.debug(msg)
        raise ValueError(msg)

    def commit(self):
        """
        -   Verify the playbook config against the retrieved template

        -   Raise ValueError in the following cases:
            - Required parameters are not set prior to calling commit()
            - ParamInfo() returns errors(s)
            - A parameter fails verification
        """
        try:
            self.validate_commit_parameters()
        except ValueError as error:
            raise ValueError(error) from error

        self.update_ruleset()

        try:
            self.update_param_info()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

        msg = "self.config_playbook: "
        msg += f"{json.dumps(self.config_playbook, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        self.params_are_valid = set()
        for self.parameter in self.config_playbook:
            try:
                self.verify_parameter()
            except ValueError as error:
                raise ValueError(error) from error
        if False not in self.params_are_valid:
            return

        self.generate_error_message()
