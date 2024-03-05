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
import logging


class ImagePolicyTaskResult:
    """
    Storage for ImagePolicyTask result

    Usage:

    NOTES:
    1.  Assumes deleted and merged are class instances with diff properties
        that return the diff for the deleted and merged states.
    2.  diff must be a dict()
    3.  result.deleted, etc do not overwrite the existing value.  They append
        to it.  So, for example:
        result.deleted = {"foo": "bar"}
        result.deleted = {"baz": "qux"}
        print(result.deleted)
        Output: [{"foo": "bar"}, {"baz": "qux"}]
    4. result.response is a list of dicts.  Each dict represents a response
         from the controller.

    result = Result(ansible_module)
    result.deleted = deleted.diff # Appends to deleted-state changes
    result.merged = merged.diff   # Appends to merged-state changes
    # If a class doesn't have a diff property, then just append the dict
    # that represents the changes for a given state.
    result.overridden = {"foo": "bar"}
    etc for other states
    # If you want to append a response from the controller, then do this:
    result.response = response_from_controller

    print(result.result)

    # output of the above print() will be a dict with the following structure:
    {
        "changed": True, # or False
        "diff": {
            "deleted": [<list of dict representing changes for deleted state>],
            "merged": [<list of dict representing changes for merged state>],
            "overridden": [<list of dict representing changes for overridden state>],
            "query": [<list of dict representing changes for query state>],
            "replaced": [<list of dict representing changes for replaced state>]
        }
        "response": {
            "deleted": [<list of dict representing responses from the controller>],
            "merged": [<list of dict representing responses from the controller>],
            "overridden": [<list of dict representing responses from the controller>],
            "query": [<list of dict representing responses from the controller>],
            "replaced": [<list of dict representing responses from the controller>]
        }
    }
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module
        self.check_mode = self.ansible_module.check_mode

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED ImagePolicyTaskResult(): "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.states = ["deleted", "merged", "overridden", "query", "replaced"]

        self.diff_properties = {}
        self.diff_properties["diff_deleted"] = "deleted"
        self.diff_properties["diff_merged"] = "merged"
        self.diff_properties["diff_overridden"] = "overridden"
        self.diff_properties["diff_query"] = "query"
        self.diff_properties["diff_replaced"] = "replaced"
        self.response_properties = {}
        self.response_properties["response_deleted"] = "deleted"
        self.response_properties["response_merged"] = "merged"
        self.response_properties["response_overridden"] = "overridden"
        self.response_properties["response_query"] = "query"
        self.response_properties["response_replaced"] = "replaced"

        self._build_properties()

    def _build_properties(self):
        """
        Build the properties dict() with default values
        """
        self.properties = {}
        self.properties["diff_deleted"] = []
        self.properties["diff_merged"] = []
        self.properties["diff_overridden"] = []
        self.properties["diff_query"] = []
        self.properties["diff_replaced"] = []

        self.properties["response_deleted"] = []
        self.properties["response_merged"] = []
        self.properties["response_overridden"] = []
        self.properties["response_query"] = []
        self.properties["response_replaced"] = []

    def did_anything_change(self):
        """
        return True if diffs have been appended to any of the diff lists.
        """
        if self.check_mode is True:
            self.log.debug("check_mode is True.  No changes made.")
            return False
        for key in self.diff_properties:
            # skip query state diffs
            if key == "diff_query":
                continue
            if len(self.properties[key]) != 0:
                return True
        return False

    def _verify_is_dict(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "value must be a dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg, **self.failed_result)

    @property
    def failed_result(self):
        """
        return a result for a failed task with no changes
        """
        result = {}
        result["changed"] = False
        result["failed"] = True
        result["diff"] = {}
        result["response"] = {}
        for key in self.diff_properties:
            result["diff"][key] = []
        for key in self.response_properties:
            result["response"][key] = []
        return result

    @property
    def module_result(self):
        """
        return a result that AnsibleModule can use
        """
        result = {}
        result["changed"] = self.did_anything_change()
        result["diff"] = {}
        result["response"] = {}
        for key, diff_key in self.diff_properties.items():
            result["diff"][diff_key] = self.properties[key]
        for key, response_key in self.response_properties.items():
            result["response"][response_key] = self.properties[key]
        return result

    # diff properties
    @property
    def diff_deleted(self):
        """
        Getter for diff_deleted property

        Used for deleted state i.e. delete image policies
        """
        return self.properties["diff_deleted"]

    @diff_deleted.setter
    def diff_deleted(self, value):
        """
        Setter for diff_deleted property
        """
        self._verify_is_dict(value)
        self.properties["diff_deleted"].append(value)

    @property
    def diff_merged(self):
        """
        Getter for diff_merged property

        This is used for merged state i.e. create image policies
        """
        return self.properties["diff_merged"]

    @diff_merged.setter
    def diff_merged(self, value):
        """
        Setter for diff_merged property
        """
        self._verify_is_dict(value)
        self.properties["diff_merged"].append(value)

    @property
    def diff_overridden(self):
        """
        Getter for diff_overridden property

        This is used for overridden state diffs
        """
        return self.properties["diff_overridden"]

    @diff_overridden.setter
    def diff_overridden(self, value):
        """
        Setter for diff_overridden property
        """
        self._verify_is_dict(value)
        self.properties["diff_overridden"].append(value)

    @property
    def diff_query(self):
        """
        Getter for diff_query property

        There should never be a diff for query state.
        """
        return self.properties["diff_query"]

    @diff_query.setter
    def diff_query(self, value):
        """
        Setter for diff_query property
        """
        self._verify_is_dict(value)
        self.properties["diff_query"].append(value)

    @property
    def diff_replaced(self):
        """
        Getter for diff_replaced property
        """
        return self.properties["diff_replaced"]

    @diff_replaced.setter
    def diff_replaced(self, value):
        """
        Setter for diff_replaced property
        """
        self._verify_is_dict(value)
        self.properties["diff_replaced"].append(value)

    # response properties
    @property
    def response_deleted(self):
        """
        Getter for response_deleted property
        """
        return self.properties["response_deleted"]

    @response_deleted.setter
    def response_deleted(self, value):
        """
        Setter for response_deleted property
        """
        self._verify_is_dict(value)
        self.properties["response_deleted"].append(value)

    @property
    def response_merged(self):
        """
        Getter for response_merged property
        """
        return self.properties["response_merged"]

    @response_merged.setter
    def response_merged(self, value):
        """
        Setter for response_merged property
        """
        self._verify_is_dict(value)
        self.properties["response_merged"].append(value)

    @property
    def response_overridden(self):
        """
        Getter for response_overridden property
        """
        return self.properties["response_overridden"]

    @response_overridden.setter
    def response_overridden(self, value):
        """
        Setter for response_overridden property
        """
        self._verify_is_dict(value)
        self.properties["response_overridden"].append(value)

    @property
    def response_query(self):
        """
        Getter for response_query property
        """
        return self.properties["response_query"]

    @response_query.setter
    def response_query(self, value):
        """
        Setter for response_query property
        """
        self._verify_is_dict(value)
        self.properties["response_query"].append(value)

    @property
    def response_replaced(self):
        """
        Getter for response_replaced property
        """
        return self.properties["response_replaced"]

    @response_replaced.setter
    def response_replaced(self, value):
        """
        Setter for response_replaced property
        """
        self._verify_is_dict(value)
        self.properties["response_replaced"].append(value)
