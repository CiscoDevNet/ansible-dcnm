#!/usr/bin/env python
import json
import logging
import re
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils

class RuleSetCommon:
    """
    Common methods for the RuleSet class.

    This may be merged back into RuleSet at some point.
    """

    def __init__(self) -> None:
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.conversion = ConversionUtils()

        self.rule = None
        self.properties = {}
        self.properties["template"] = None
        self.properties["ruleset"] = {}

    def clean_rule(self):
        """
        Clean the rule string.
        """
        method_name = "clean_rule"
        msg = f"{self.class_name}.{method_name}: "
        msg += f"PRE1 : RULE: {self.rule}"
        self.log.debug(msg)
        self.rule = self.rule.strip('"')
        self.rule = self.rule.strip("'")
        self.rule = self.rule.replace("$$", "")
        self.rule = self.rule.replace("&&", " and ")
        self.rule = self.rule.replace("||", " or ")
        self.rule = self.rule.replace("==", " == ")
        self.rule = self.rule.replace("!=", " != ")
        self.rule = self.rule.replace("(", " ( ")
        self.rule = self.rule.replace(")", " ) ")
        self.rule = self.rule.replace("true", " True")
        self.rule = self.rule.replace("false", " False")
        self.rule = re.sub(r"\s+", " ", self.rule)
        msg = f"{self.class_name}.{method_name}: "
        msg += f"PRE2 : RULE: {self.rule}"
        self.log.debug(msg)

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
        return self.properties["template"]

    @template.setter
    def template(self, value):
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
    # Generate a ruleset from a template

    ## Usage

    ```python
    ruleset = RuleSet()
    ruleset.template = <template>
    ruleset.commit()
    rules = ruleset.ruleset
    ```
    """

    def __init__(self) -> None:
        super().__init__()

    def _update_ruleset_no_boolean(self):
        """
        # Process rules that contain no boolean terms

        ```python
        "VRF_LITE_AUTOCONFIG != Manual"
        ```
        """
        msg = f"key {self.param_name}: {self.rule}"
        self.log.debug(msg)

        if isinstance(self.rule, list):
            for item in self.rule:
                lhs, op, rhs = item.split(" ")
                rhs = self.conversion.make_boolean(rhs)
                if self.param_name not in self.ruleset:
                    self.ruleset[self.param_name] = {}
                    self.ruleset[self.param_name]["mandatory"] = {}
                self.ruleset[self.param_name]["mandatory"][lhs] = {}
                self.ruleset[self.param_name]["mandatory"][lhs]["operator"] = op
                self.ruleset[self.param_name]["mandatory"][lhs]["value"] = rhs
            return
        lhs, op, rhs = self.rule.split(" ")
        rhs = self.conversion.make_boolean(rhs)
        if self.param_name not in self.ruleset:
            self.ruleset[self.param_name] = {}
            self.ruleset[self.param_name]["mandatory"] = {}
        self.ruleset[self.param_name]["mandatory"][lhs] = {}
        self.ruleset[self.param_name]["mandatory"][lhs]["operator"] = op
        self.ruleset[self.param_name]["mandatory"][lhs]["value"] = rhs

    def _update_ruleset_rule_and(self):
        """
        # Process rules that contain only boolean "and" terms

        NOTE: ``&&`` is replaced with `` and `` in ``clean_rule()``

        ```python
        "IsShow": "\"LINK_STATE_ROUTING==ospf && UNDERLAY_IS_V6==false\""
        ```
        """
        self.rule = self.rule.split("and")
        self.rule = [x.strip() for x in self.rule]
        self.rule = [re.sub(r"\s+", " ", x) for x in self.rule]
        self.rule = [re.sub(r"\"", "", x) for x in self.rule]
        self.rule = [re.sub(r"\'", "", x) for x in self.rule]
        new_rule = []
        for item in self.rule:
            lhs, op, rhs = item.split(" ")
            rhs = rhs.replace('"', "")
            rhs = rhs.replace("'", "")
            rhs = self.conversion.make_boolean(rhs)
            new_rule.append(f"{lhs} {op} {rhs}")
            if self.param_name not in self.ruleset:
                self.ruleset[self.param_name] = {}
                self.ruleset[self.param_name]["mandatory"] = {}
            self.ruleset[self.param_name]["mandatory"][lhs] = {}
            self.ruleset[self.param_name]["mandatory"][lhs]["operator"] = op
            self.ruleset[self.param_name]["mandatory"][lhs]["value"] = rhs

    def _update_ruleset(self) -> None:
        """
        Update the ruleset for self.parameter and self.rule
        """
        # print(f"_update_ruleset: 1. self.rule: {self.rule}")
        if self.rule is None:
            return
        if self.rule in ("true", "True", True):
            return
        if self.rule in ("false", "False", False):
            return
        self.clean_rule()
        if "and" in self.rule and "or" in self.rule:
            # TODO: handle this case
            msg = "TODO: UNHANDLED_CASE: and+or in rule. "
            msg += f"param_name: {self.param_name} rule: {self.rule}"
            self.log.debug(msg)
            pass
        if "and" in self.rule and "or" not in self.rule:
            self._update_ruleset_rule_and()
        if "and" not in self.rule and "or" not in self.rule:
            self._update_ruleset_no_boolean()

    def refresh(self) -> None:
        """
        Refresh the ruleset from the template.

        - raise ValueError if template is not set.
        - raise ValueError if template has no parameters.
        - raise ValueError if template[parameters] is not a list.
        """
        if self.template is None:
            msg = "template is not set.  "
            msg += "Call instance.template = <template> "
            msg += "before calling instance.refresh()."
            raise ValueError(msg)
        if self.template.get("parameters") is None:
            msg = "No parameters in template."
            raise ValueError(msg)
        if isinstance(self.template["parameters"], list) is False:
            msg = "template[parameters] is not a list."
            raise ValueError(msg)
        for parameter in self.template["parameters"]:
            parameter_name = parameter.get("name")
            self.log.debug(f"REFRESH: parameter_name: {parameter_name}")
            if self.is_internal(parameter) is True:
                continue
            if "Hidden" in self.section(parameter):
                continue
            self.param_name = self.name(parameter)
            if parameter_name == "AUTO_SYMMETRIC_VRF_LITE":
                self.log.debug(f"parameter: {self.param_name}")
            if self.param_name is None:
                continue
            self.rule = self.is_show(parameter)
            self._update_ruleset()
