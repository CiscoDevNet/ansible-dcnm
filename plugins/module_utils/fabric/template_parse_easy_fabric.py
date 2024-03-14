#!/usr/bin/env python
"""
Name: ndfc_template_easy_fabric.py
Description:

Generate ruleset and documentation for the NDFC EasyFabric template.

The template is retieved via the following controller endpoint:

/appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates/Easy_Fabric
"""
import json
import re
import sys

import yaml
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.template_parse_common import \
    TemplateParseCommon


class TemplateParseEasyFabric(TemplateParseCommon):
    def __init__(self):
        super().__init__()
        self.translation = None
        self.suboptions = None
        self.documentation = None
        self.ruleset = {}

    @property
    def template_all(self):
        return self._properties["template_all"]

    @template_all.setter
    def template_all(self, value):
        """
        An instance of NdfcTemplateAll()
        """
        self._properties["template_all"] = value

    def init_translation(self):
        """
        All parameters in the playbook are lowercase dunder, while
        NDFC nvPairs contains a mish-mash of styles (and typos),
        for example:
        - enableScheduledBackup
        - default_vrf
        - REPLICATION_MODE
        - DEAFULT_QUEUING_POLICY_CLOUDSCALE

        This method builds a dictionary which maps between NDFC's expected
        parameter names and the corresponding playbook names.
        e.g.:
        DEAFULT_QUEUING_POLICY_CLOUDSCALE -> default_queuing_policy_cloudscale

        The dictionary excludes hidden and internal parameters.
        """
        if self.template is None:
            msg = "exiting. call instance.load_template() first."
            print(f"{msg}")
            sys.exit(1)
        re_uppercase_dunder = "^[A-Z0-9_]+$"
        self.translation = {}
        typo_keys = {
            "DEAFULT_QUEUING_POLICY_CLOUDSCALE": "default_queuing_policy_cloudscale",
            "DEAFULT_QUEUING_POLICY_OTHER": "default_queuing_policy_other",
            "DEAFULT_QUEUING_POLICY_R_SERIES": "default_queuing_policy_r_series",
        }
        camel_keys = {
            "enableRealTimeBackup": "enable_real_time_backup",
            "enableScheduledBackup": "enable_scheduled_backup",
            "scheduledTime": "scheduled_time",
        }
        other_keys = {
            "VPC_ENABLE_IPv6_ND_SYNC": "vpc_enable_ipv6_nd_sync",
            "default_vrf": "default_vrf",
            "default_network": "default_network",
            "vrf_extension_template": "vrf_extension_template",
            "network_extension_template": "network_extension_template",
            "default_pvlan_sec_network": "default_pvlan_sec_network",
        }
        for item in self.template.get("parameters"):
            if self.is_internal(item):
                continue
            if self.is_hidden(item):
                continue
            name = self.get_name(item)
            if not name:
                continue
            if name in typo_keys:
                self.translation[name] = typo_keys[name]
                continue
            if name in camel_keys:
                self.translation[name] = camel_keys[name]
                continue
            if name in other_keys:
                self.translation[name] = other_keys[name]
                continue
            if re.search(re_uppercase_dunder, name):
                self.translation[name] = name.lower()

    def validate_base_prerequisites(self):
        """
        1. Validate that the prerequisites are met before proceeding.
            Specifically:
            - User has set self.template
            - User has set self.template_all
        2. Call self.init_translation() if self.translation is None
        """
        if self.template is None:
            msg = "exiting. call instance.load_template() first."
            print(f"{msg}")
            sys.exit(1)
        if self.translation is None:
            self.init_translation()

    def build_documentation(self):
        """
        Build the documentation for the EasyFabric template.
        """
        self.validate_base_prerequisites()
        if self.template_all is None:
            msg = "exiting. call instance.template_all first."
            print(f"{msg}")
            sys.exit(1)
        self.documentation = {}
        self.documentation["module"] = "dcnm_easy_fabric"
        self.documentation["author"] = "Cisco Systems, Inc."
        self.documentation["description"] = []
        self.documentation["description"].append(
            self.get_template_description(self.template)
        )
        self.documentation["options"] = {}
        self.documentation["options"]["state"] = {}
        self.documentation["options"]["state"]["description"] = []
        value = "The state of DCNM after module completion"
        self.documentation["options"]["state"]["description"].append(value)
        value = "I(deleted), I(merged), and I(query) states are supported."
        self.documentation["options"]["state"]["description"].append(value)
        self.documentation["options"]["state"]["type"] = "str"
        self.documentation["options"]["state"]["choices"] = [
            "deleted",
            "merged",
            "query",
        ]
        self.documentation["options"]["state"]["default"] = "merged"
        self.documentation["options"]["config"] = {}
        self.documentation["options"]["config"]["description"] = []
        value = "A list of fabric configuration dictionaries"
        self.documentation["options"]["config"]["description"].append(value)
        self.documentation["options"]["config"]["type"] = "list"
        self.documentation["options"]["config"]["elements"] = "dict"
        self.documentation["options"]["config"]["suboptions"] = {}

        suboptions = {}
        for item in self.template.get("parameters"):
            if self.is_internal(item):
                continue
            if self.is_hidden(item):
                continue
            if not item.get("name", None):
                continue
            name = self.translation.get(item["name"], None)
            if name is None:
                print(f"WARNING: skipping {item['name']}")
                continue
            suboptions[name] = {}
            suboptions[name]["description"] = []
            suboptions[name]["description"].append(self.get_description(item))
            suboptions[name]["type"] = self.get_parameter_type(item)
            suboptions[name]["required"] = self.is_required(item)
            default = self.get_default_value(item)
            if default is not None:
                suboptions[name]["default"] = default
            choices = self.get_enum(item)
            if len(choices) > 0:
                if "TEMPLATES" in str(choices[0]):
                    tag = str(choices[0]).split(".")[1]
                    choices = self.template_all.get_templates_by_tag(tag)
                suboptions[name]["choices"] = choices
            min_value, max_value = self.get_min_max(item)
            if min_value is not None:
                suboptions[name]["min"] = min_value
            if max_value is not None:
                suboptions[name]["max"] = max_value
            ndfc_label = self.get_display_name(item)
            if ndfc_label is not None:
                suboptions[name]["ndfc_gui_label"] = ndfc_label
            ndfc_section = self.get_section(item)
            if ndfc_section is not None:
                suboptions[name]["ndfc_gui_section"] = ndfc_section

        self.documentation["options"]["config"]["suboptions"] = []
        for key in sorted(suboptions.keys()):
            self.documentation["options"]["config"]["suboptions"].append(
                {key: suboptions[key]}
            )

    def build_ruleset(self):
        """
        Build the ruleset for the EasyFabric template, based on
        annotations.IsShow in each parameter dictionary.

        The ruleset is keyed on parameter name, with values being set of
        rules that determine whether a given parameter is mandatory, based
        on the state of other parameters.

        Usage:

        template.build_ruleset()
        parameter = "unnum_dhcp_end"
        try:
            result = eval(template.ruleset[parameter])
        except:
            result = False
        if result is True:
            print(f"{parameter} is mandatory")
        """
        self.validate_base_prerequisites()
        self.ruleset = {}
        for item in self.template.get("parameters"):
            if self.is_internal(item):
                continue
            if self.is_hidden(item):
                continue
            if not item.get("name", None):
                continue
            name = self.translation.get(item["name"], None)
            if name is None:
                print(f"WARNING: skipping {item['name']}")
                continue
            self.ruleset[name] = item.get("annotations", {}).get("IsShow", None)
        self.ruleset = self.pythonize_ruleset(self.ruleset)

    def pythonize_ruleset(self, ruleset):
        """
        Convert a template ruleset to python code that can be eval()'d
        """
        mixed_rules = {}
        for key in ruleset:
            rule = ruleset[key]
            if rule is None:
                continue
            # print(f"PRE1 : key {key}, RULE: {rule}")
            rule = rule.replace("$$", "")
            rule = rule.replace("&&", " and ")
            rule = rule.replace(r"\"", "")
            rule = rule.replace(r"\'", "")
            rule = rule.replace("||", " or ")
            rule = rule.replace("==", " == ")
            rule = rule.replace("!=", " != ")
            rule = rule.replace("(", " ( ")
            rule = rule.replace(")", " ) ")
            rule = rule.replace("true", " True")
            rule = rule.replace("false", " False")
            rule = re.sub(r"\s+", " ", rule)
            if "and" in rule and "or" in rule:
                mixed_rules[key] = rule
                continue
            if "and" in rule and "or" not in rule:
                rule = rule.split("and")
                rule = [x.strip() for x in rule]
                rule = [re.sub(r"\s{2}+", " ", x) for x in rule]
                # print(f"POST1: key {key}, len {len(rule)} rule: {rule}")
                rule = [re.sub(r"\"", "", x) for x in rule]
                rule = [re.sub(r"\'", "", x) for x in rule]
                # rule = [re.sub(r"\s{2}+", " ", x) for x in rule]
                # print(f"POST2: key {key}, len {len(rule)} rule: {rule}")
                new_rule = []
                for item in rule:
                    lhs, op, rhs = item.split(" ")
                    rhs = rhs.replace('"', "")
                    rhs = rhs.replace("'", "")
                    if rhs not in ["True", "False", True, False]:
                        rhs = f'"{rhs}"'
                    lhs = self.translation.get(lhs, lhs)
                    # print(f"POST3: key {key}: lhs: {lhs}, op: {op}, rhs: {rhs}")
                    new_rule.append(f"{lhs} {op} {rhs}")
                new_rule = " and ".join(new_rule)
                # print(f"POST4: key {key}: {new_rule}")
                ruleset[key] = new_rule
        return ruleset

    def documentation_yaml(self):
        """
        Dump the documentation in YAML format
        """
        if self.documentation is None:
            self.build_documentation()
        print(yaml.dump(self.documentation, indent=4))

    def documentation_json(self):
        """
        Dump the documentation in JSON format
        """
        if self.documentation is None:
            self.build_documentation()
        print(json.dumps(self.documentation, indent=4))
