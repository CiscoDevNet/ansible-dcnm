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
import re

from ..common.conversion import ConversionUtils


class RuleSetCommon:
    """
    Common methods for the RuleSet class.

    This may be merged back into RuleSet at some point.
    """

    def __init__(self) -> None:
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.conversion = ConversionUtils()

        self.re_multi_rule = re.compile(r"^\s*(\(.*\))(.*)(\(.*\))\s*$")

        self.param_name = None
        self.rule = None
        self.properties = {}
        self.properties["template"] = None
        self.properties["ruleset"] = {}

    def clean_rule(self):
        """
        Clean the rule string.
        """
        self.rule = self.rule.strip('"')
        self.rule = self.rule.strip("'")
        self.rule = self.rule.replace("$$", "")
        self.rule = self.rule.replace("&&", " and ")
        self.rule = self.rule.replace("||", " or ")
        self.rule = self.rule.replace("==", " == ")
        self.rule = self.rule.replace("!=", " != ")
        self.rule = self.rule.replace("(", " ( ")
        self.rule = self.rule.replace(")", " ) ")
        self.rule = self.rule.replace("true", "True")
        self.rule = self.rule.replace("false", "False")
        self.rule = re.sub(r"\s+", " ", self.rule)

    @property
    def ruleset(self):
        """
        - getter : return the ruleset.
        - setter : set the ruleset.
        """
        return self.properties["ruleset"]

    @ruleset.setter
    def ruleset(self, value):
        self.properties["ruleset"] = value

    @property
    def template(self):
        """
        -   getter : return a controller template.
        -   setter : set a controller template.
        -   The template is a dictionary retrieved from the controller.
        """
        return self.properties["template"]

    @template.setter
    def template(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name} must be a dictionary."
            raise ValueError(msg)
        self.properties["template"] = value

    @staticmethod
    def annotations(parameter):
        """
        Return the annotations for the parameter, if any.

        Otherwise, return None.
        """
        if parameter.get("annotations") is None:
            return None
        if isinstance(parameter["annotations"], dict) is False:
            return None
        return parameter["annotations"]

    def is_mandatory(self, parameter):
        """
        - Return False if annotations is not present
        - Return True if annotations["IsMandatory"] is True
        - Return False if annotations["IsMandatory"] is not present
        - Return False if annotations["IsMandatory"] is False
        - Return False if annotations["IsMandatory"] is not set
        - Return annotations["IsMandatory"] if all else fails
        """
        annotations = self.annotations(parameter)
        if annotations is None:
            return False
        if annotations.get("IsMandatory") is None:
            return False
        if annotations["IsMandatory"] in ("true", "True", True):
            return True
        if annotations["IsMandatory"] in ("false", "False", False):
            return False
        return annotations["IsMandatory"]

    def is_show(self, parameter):
        """
        - Return False if annotations is not present
        - Return False if annotations["IsShow"] is not present
        - Return True if annotations["IsShow"] is True
        - Return False if annotations["IsShow"] is False
        - Return annotations["IsShow"] if all else fails
        """
        annotations = self.annotations(parameter)
        if annotations is None:
            return False
        if annotations.get("IsShow") is None:
            return False
        if annotations["IsShow"] in ("true", "True", True):
            return True
        if annotations["IsShow"] in ("false", "False", False):
            return False
        return annotations["IsShow"]

    def is_internal(self, parameter):
        """
        - Return False if annotations is not present
        - Return False if annotations["IsInternal"] is not present
        - Return True if annotations["IsInternal"] is True
        - Return False if annotations["IsInternal"] is False
        - Return False if all else fails
        """
        annotations = self.annotations(parameter)
        if annotations is None:
            return False
        if annotations.get("IsInternal") is None:
            return False
        if annotations["IsInternal"] in ("true", "True", True):
            return True
        if annotations["IsInternal"] in ("false", "False", False):
            return False
        return False

    def section(self, parameter):
        """
        - Return "" if annotations is not present
        - Return "" if annotations["Section"] is not present
        - Return annotations["Section"] if present
        """
        annotations = self.annotations(parameter)
        if annotations is None:
            return ""
        if annotations.get("Section") is None:
            return ""
        return annotations["Section"]

    @staticmethod
    def name(parameter):
        """
        - Return the parameter's name, if present.
        - Return None otherwise.
        """
        if parameter.get("name") is None:
            return None
        return parameter["name"]


class RuleSet(RuleSetCommon):
    """
    # Generate a ruleset from a controller template

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

    def _update_ruleset_no_boolean(self):
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
        method_name = inspect.stack()[0][3]
        msg = f"key {self.param_name}: {self.rule}"
        self.log.debug(msg)

        self.ruleset[self.param_name] = {}
        self.ruleset[self.param_name]["terms"] = {}
        self.ruleset[self.param_name]["terms"]["na"] = []

        if isinstance(self.rule, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "UNHANDLED_CASE: rule is a list."
            raise ValueError(msg)

        lhs, op, rhs = self.rule.split(" ")
        rhs = self.conversion.make_boolean(rhs)
        term = {}
        term["parameter"] = lhs
        term["operator"] = op
        term["value"] = rhs
        self.ruleset[self.param_name]["terms"]["na"].append(term)

        msg = f"{self.param_name}: "
        msg += f"{json.dumps(self.ruleset[self.param_name], indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _update_ruleset_boolean(self):
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
        if "and" in self.rule:
            boolean_type = "and"
        elif "or" in self.rule:
            boolean_type = "or"
        else:
            return

        self.rule = self.rule.split(boolean_type)

        self.rule = [x.strip() for x in self.rule]
        self.rule = [re.sub(r"\s+", " ", x) for x in self.rule]
        self.rule = [re.sub(r"\"", "", x) for x in self.rule]
        self.rule = [re.sub(r"\'", "", x) for x in self.rule]
        new_rule = []

        self.ruleset[self.param_name] = {}
        self.ruleset[self.param_name]["terms"] = {}
        self.ruleset[self.param_name]["terms"][boolean_type] = []

        for item in self.rule:
            lhs, op, rhs = item.split(" ")
            rhs = rhs.replace('"', "")
            rhs = rhs.replace("'", "")
            rhs = self.conversion.make_boolean(rhs)
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
        Update the ruleset for self.parameter and self.rule
        """
        if self.rule is None:
            return
        if self.rule in ("true", "True", True):
            return
        if self.rule in ("false", "False", False):
            return
        self.clean_rule()

        match = re.match(self.re_multi_rule, self.rule)
        if match:
            msg = "TODO: multi-rule: "
            msg += f"param_name: {self.param_name} rule: {self.rule}"
            self.log.debug(msg)
            msg = f"match.group(1): {match.group(1)}"
            self.log.debug(msg)
            msg = f"match.group(2): {match.group(2)}"
            self.log.debug(msg)
            msg = f"match.group(3): {match.group(3)}"
            self.log.debug(msg)
        elif "and" in self.rule and "or" not in self.rule:
            self._update_ruleset_boolean()
        elif "or" in self.rule and "and" not in self.rule:
            self._update_ruleset_boolean()
        elif "and" not in self.rule and "or" not in self.rule:
            self._update_ruleset_no_boolean()
        else:
            msg = "TODO: UNHANDLED_CASE: "
            msg += f"param_name: {self.param_name} rule: {self.rule}"
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

        self.properties["ruleset"] = {}

        for parameter in self.template["parameters"]:
            if self.is_internal(parameter) is True:
                continue
            if "Hidden" in self.section(parameter):
                continue
            self.param_name = self.name(parameter)
            if self.param_name is None:
                msg += f"name key missing from parameter: {parameter}"
                raise ValueError(msg)
            self.rule = self.is_show(parameter)
            self._update_ruleset()
