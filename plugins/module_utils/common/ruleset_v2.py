# Copyright (c) 2024-2025 Cisco and/or its affiliates.
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
# pylint: disable=too-many-instance-attributes
"""
Generate a ruleset from a controller template
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"


import inspect
import json
import logging
import re
from typing import Optional, Union

from .conversion import ConversionUtils


class RuleSet:
    """
    # Summary

    Generate a ruleset from a controller template

    ## Usage

    ```python
    ruleset = RuleSet()
    ruleset.template = <template>
    ruleset.commit()
    rules = ruleset.ruleset

    parameter = "MY_PARAM"

    # Retrieve annotations for MY_PARAM
    annotations = ruleset.annotations(parameter)

    # Retrieve the annotations.section for MY_PARAM
    section = ruleset.section(parameter)

    # Retrieve whether "MY_PARAM" is an internal
    # parameter. (is_internal will be boolean)
    is_internal = rule.is_internal(parameter)

    # Retrieve whether "MY_PARAM" is mandatory
    # (is_mandatory will be boolean)
    is_mandatory = rule.is_mandatory(parameter)

    # Retrieve IsShow for "MY_PARAM"
    is_show = rule.is_show(parameter)
    ```
    """

    def __init__(self) -> None:
        self.class_name: str = self.__class__.__name__

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")
        self._conversion: ConversionUtils = ConversionUtils()

        self._re_multi_rule: re.Pattern = re.compile(r"^\s*(\(.*\))(.*)(\(.*\))\s*$")

        self.param_name: Optional[str] = None
        self._rule: Optional[str] = None
        self._template: dict = {}
        self._ruleset: dict = {}

    def clean_rule(self) -> None:
        """
        # Summary

        Clean the rule string.

        ## Raises

        None
        """
        if self._rule is None:
            return
        self._rule = self._rule.strip('"')
        self._rule = self._rule.strip("'")
        self._rule = self._rule.replace("$$", "")
        self._rule = self._rule.replace("&&", " and ")
        self._rule = self._rule.replace("||", " or ")
        self._rule = self._rule.replace("==", " == ")
        self._rule = self._rule.replace("!=", " != ")
        self._rule = self._rule.replace("(", " ( ")
        self._rule = self._rule.replace(")", " ) ")
        self._rule = self._rule.replace("true", "True")
        self._rule = self._rule.replace("false", "False")
        self._rule = re.sub(r"\s+", " ", self._rule)

    @property
    def ruleset(self):
        """
        - getter : return the ruleset.
        - setter : set the ruleset.
        """
        return self._ruleset

    @ruleset.setter
    def ruleset(self, value):
        self._ruleset = value

    @property
    def template(self) -> dict:
        """
        # Summary

        -   getter : return a controller template.
        -   setter : set a controller template.
        -   The template is a dictionary retrieved from the controller.

        ## Raises

        -   setter: `ValueError` if the value passed to the setter is not a dictionary.
        """
        return self._template

    @template.setter
    def template(self, value: dict) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name} must be a dictionary."
            raise ValueError(msg)
        self._template = value

    @staticmethod
    def annotations(parameter: dict) -> dict:
        """
        # Summary

        - Return the annotations for the parameter, if any.
        - Return empty dict otherwise.

        ## Raises

        None
        """
        if parameter.get("annotations") is None:
            return {}
        if isinstance(parameter["annotations"], dict) is False:
            return {}
        return parameter["annotations"]

    def is_mandatory(self, parameter: dict) -> bool:
        """
        # Summary

        - Return False if annotations is not present in parameter
        - Return True if annotations["IsMandatory"] is True
        - Return False if annotations["IsMandatory"] is not present
        - Return False if annotations["IsMandatory"] is False
        - Return False if annotations["IsMandatory"] is not set
        - Return annotations["IsMandatory"] if all else fails

        ## Raises

        None
        """
        annotations = self.annotations(parameter)
        if not annotations:
            return False
        if annotations.get("IsMandatory") is None:
            return False
        if annotations["IsMandatory"] in ("true", "True", True):
            return True
        if annotations["IsMandatory"] in ("false", "False", False):
            return False
        return annotations["IsMandatory"]

    def is_show(self, parameter: dict) -> bool:
        """
        # Summary

        - Return False if annotations is not present in parameter
        - Return False if annotations["IsShow"] is not present
        - Return True if annotations["IsShow"] is True
        - Return False if annotations["IsShow"] is False
        - Return annotations["IsShow"] if all else fails

        ## Raises

        None
        """
        method_name = inspect.stack()[0][3]
        annotations = self.annotations(parameter)
        parameter_name = self.name(parameter)
        msg = f"{self.class_name}.{method_name}: IS_SHOW PARAMETER: {parameter_name}. "
        if not annotations:
            msg += "No annotations found. return False."
            self.log.debug(msg)
            return False
        if annotations.get("IsShow") is None:
            msg += "No IsShow found. return False."
            self.log.debug(msg)
            return False
        if annotations["IsShow"] in ("true", "True", True):
            msg += "IsShow is True.  Return True"
            self.log.debug(msg)
            return True
        if annotations["IsShow"] in ("false", "False", False):
            msg += "IsShow is False.  Return False"
            self.log.debug(msg)
            return False
        msg += f"Returning IsShow: {annotations['IsShow']}"
        self.log.debug(msg)
        return annotations["IsShow"]

    def is_internal(self, parameter: dict) -> bool:
        """
        # Summary

        - Return False if annotations is not present in parameter
        - Return False if annotations["IsInternal"] is not present
        - Return True if annotations["IsInternal"] is True
        - Return False if annotations["IsInternal"] is False
        - Return False if all else fails

        ## Raises

        None
        """
        annotations = self.annotations(parameter)
        if not annotations:
            return False
        if annotations.get("IsInternal") is None:
            return False
        if annotations["IsInternal"] in ("true", "True", True):
            return True
        if annotations["IsInternal"] in ("false", "False", False):
            return False
        return False

    def section(self, parameter: dict) -> str:
        """
        - Return "" if annotations is not present
        - Return "" if annotations["Section"] is not present
        - Return annotations["Section"] if present
        """
        annotations = self.annotations(parameter)
        if not annotations:
            return ""
        if annotations.get("Section") is None:
            return ""
        return annotations["Section"]

    @staticmethod
    def name(parameter: dict) -> str:
        """
        # Summary

        Given a parameter dictionary:
        - Return the parameter's name, if present.
        - Return "" otherwise.
        """
        if parameter.get("name") is None:
            return ""
        return parameter["name"]

    def _update_ruleset_no_boolean(self) -> None:
        """
        - Process rules that contain no boolean terms
        - Raise ``ValueError`` for unhandled case if rule is a list.

        ```python
        "VRF_LITE_AUTOCONFIG != Manual"
        ```

        - Ruleset Structure (no boolean):

        ```python
        AUTO_VRFLITE_IFC_DEFAULT_VRF: {
            "terms": {
                "na": [
                    {
                        "operator": "!=",
                        "parameter": "VRF_LITE_AUTOCONFIG",
                        "value": "Manual"
                    }
                ]
            }
        }

        """
        method_name: str = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"key {self.param_name}: {self._rule}"
        self.log.debug(msg)

        self.ruleset[self.param_name] = {}
        self.ruleset[self.param_name]["terms"] = {}
        self.ruleset[self.param_name]["terms"]["na"] = []

        if self._rule is None:
            return

        if isinstance(self._rule, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "UNHANDLED_CASE: rule is a list."
            raise ValueError(msg)

        lhs, op, rhs = self._rule.split(" ")
        rhs_converted: Union[str, bool] = self._conversion.make_boolean(rhs)
        term: dict[str, Union[str, bool]] = {}
        term["parameter"] = lhs
        term["operator"] = op
        term["value"] = rhs_converted
        self.ruleset[self.param_name]["terms"]["na"].append(term)

        msg = f"{self.param_name}: "
        msg += f"{json.dumps(self.ruleset[self.param_name], indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _update_ruleset_boolean(self) -> None:
        """
        - Process rules that contain only boolean "and" or "or" terms

        NOTES:
            - ``&&`` is replaced with `` and `` in ``clean_rule()``
            - ``||`` is replaced with `` or `` in ``clean_rule()``


        ```python
        PARAM = INBAND_MGMT
        "IsShow": "\"LINK_STATE_ROUTING==ospf && UNDERLAY_IS_V6==false\""
        ```

        - Ruleset Structure (AND):

        ```python
        SUBNET_RANGE: {
            "terms": {
                "and": [
                    {
                        "operator": "==",
                        "parameter": "UNDERLAY_IS_V6",
                        "value": false
                    },
                    {
                        "operator": "==",
                        "parameter": "STATIC_UNDERLAY_IP_ALLOC",
                        "value": false
                    }
                ]
            }
        }
        ```

        - Ruleset Structure (OR):

        ```python
        STP_BRIDGE_PRIORITY: {
            "terms": {
                "or": [
                    {
                        "operator": "==",
                        "parameter": "STP_ROOT_OPTION",
                        "value": "rpvst+"
                    },
                    {
                        "operator": "==",
                        "parameter": "STP_ROOT_OPTION",
                        "value": "mst"
                    }
                ]
            }
        }
        ```
        """
        method_name: str = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"key {self.param_name}: {self._rule}"
        self.log.debug(msg)

        if self._rule is None:
            return
        if not isinstance(self._rule, str):
            return
        if "and" in self._rule:
            boolean_type = "and"
        elif "or" in self._rule:
            boolean_type = "or"
        else:
            return

        rule_list: list[str] = self._rule.split(boolean_type)

        rule_list = [x.strip() for x in rule_list]
        rule_list = [re.sub(r"\s+", " ", x) for x in rule_list]
        rule_list = [re.sub(r"\"", "", x) for x in rule_list]
        rule_list = [re.sub(r"\'", "", x) for x in rule_list]
        new_rule = []

        self.ruleset[self.param_name] = {}
        self.ruleset[self.param_name]["terms"] = {}
        self.ruleset[self.param_name]["terms"][boolean_type] = []

        msg = f"{self.class_name}.{method_name}: "
        msg += f"key {self.param_name}: rule_list: {rule_list}"
        self.log.debug(msg)

        for item in rule_list:
            lhs, op, rhs = item.split(" ")
            rhs = rhs.replace('"', "")
            rhs = rhs.replace("'", "")
            rhs = self._conversion.make_boolean(rhs)
            new_rule.append(f"{lhs} {op} {rhs}")

            term = {}
            term["parameter"] = lhs
            term["operator"] = op
            term["value"] = rhs
            self.ruleset[self.param_name]["terms"][boolean_type].append(term)
        msg = f"{boolean_type.upper()}: key {self.param_name}: {new_rule}"
        self.log.debug(msg)
        msg = f"{boolean_type.upper()}: key {self.param_name}: "
        msg += f"{json.dumps(self.ruleset[self.param_name], indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _update_ruleset(self) -> None:
        """
        Update the ruleset for self.parameter and self._rule
        """
        method_name: str = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"key {self.param_name}: {self._rule}"
        self.log.debug(msg)

        if self._rule is None:
            return
        if self._rule in ("true", "True", True):
            return
        if self._rule in ("false", "False", False):
            return
        self.clean_rule()

        match = re.match(self._re_multi_rule, self._rule)
        if match:
            msg = "TODO: multi-rule: "
            msg += f"param_name: {self.param_name} rule: {self._rule}"
            self.log.debug(msg)
            msg = f"match.group(1): {match.group(1)}"
            self.log.debug(msg)
            msg = f"match.group(2): {match.group(2)}"
            self.log.debug(msg)
            msg = f"match.group(3): {match.group(3)}"
            self.log.debug(msg)
        elif "and" in self._rule and "or" not in self._rule:
            self._update_ruleset_boolean()
        elif "or" in self._rule and "and" not in self._rule:
            self._update_ruleset_boolean()
        elif "and" not in self._rule and "or" not in self._rule:
            self._update_ruleset_no_boolean()
        else:
            msg = f"{self.class_name}.{method_name}: "
            msg += "TODO: UNHANDLED_CASE: "
            msg += f"param_name: {self.param_name} rule: {self._rule}"
            self.log.debug(msg)

    def refresh(self) -> None:
        """
        Refresh the ruleset from the template.

        - raise ValueError if template is not set.
        - raise ValueError if template has no parameters.
        - raise ValueError if template[parameters] is not a list.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        if self.template is None:
            msg += "template is not set.  "
            msg += f"Set {self.class_name}.template "
            msg += f"before calling {self.class_name}.{method_name}()."
            raise ValueError(msg)
        if self.template.get("parameters") is None:
            msg += "No parameters in template."
            raise ValueError(msg)
        if isinstance(self.template["parameters"], list) is False:
            msg += "template[parameters] is not a list."
            raise ValueError(msg)

        self._ruleset = {}

        for parameter in self.template["parameters"]:
            if self.is_internal(parameter) is True:
                continue
            if "Hidden" in self.section(parameter):
                continue
            self.param_name = self.name(parameter)
            if self.param_name is None:
                msg += f"name key missing from parameter: {parameter}"
                raise ValueError(msg)
            self._rule = str(self.is_show(parameter))
            self._update_ruleset()
