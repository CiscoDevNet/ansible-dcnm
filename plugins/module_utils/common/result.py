#
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
import logging
from typing import Any, Dict


class Result:
    """
    Storage for module result

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
    result.response = response
    result = result.result

    print(result)

    # output will be a dict with the following structure:
    {
        "changed": True, # or False
        "diff": [
            {
                "deleted": [<list of dict representing changes for deleted state>],
                "merged": [<list of dict representing changes for merged state>],
                "overridden": [<list of dict representing changes for overridden state>],
                "query": [<list of dict representing changes for query state>],
                "replaced": [<list of dict representing changes for replaced state>]
            }
        ]
        "response": [<list of dict representing controller response(s)>]
    }
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED Result()")

        self.states = ["deleted", "merged", "overridden", "query", "replaced"]
        self._build_properties()

    def _build_properties(self):
        """
        self.properties holds property values for the class
        """
        self.properties: Dict[str, Any] = {}
        for state in self.states:
            self.properties[state] = []
        self.properties["changed"] = False
        self.properties["response"] = []

    def did_anything_change(self):
        """
        return True if things have been appended to any of the state lists.
        """
        for state in self.states:
            if state == "query":
                continue
            if len(self.properties[state]) != 0:
                return True
        return False

    @property
    def deleted(self):
        """
        return changes for deleted state
        """
        return self.properties["deleted"]

    @deleted.setter
    def deleted(self, value):
        self._verify_is_dict(value)
        self.properties["deleted"].append(value)

    @property
    def merged(self):
        """
        return changes for merged state
        """
        return self.properties["merged"]

    @merged.setter
    def merged(self, value):
        self._verify_is_dict(value)
        self.properties["merged"].append(value)

    @property
    def overridden(self):
        """
        return changes for overridden state
        """
        return self.properties["overridden"]

    @overridden.setter
    def overridden(self, value):
        self._verify_is_dict(value)
        self.properties["overridden"].append(value)

    @property
    def query(self):
        """
        return changes for query state
        """
        return self.properties["query"]

    @query.setter
    def query(self, value):
        self._verify_is_dict(value)
        self.properties["query"].append(value)

    def _verify_is_dict(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "value must be a dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            self.ansible_module.fail_json(msg, **self.result)

    @property
    def replaced(self):
        """
        return changes for replaced state
        """
        return self.properties["replaced"]

    @replaced.setter
    def replaced(self, value):
        self._verify_is_dict(value)
        self.properties["replaced"].append(value)

    @property
    def result(self):
        """
        return a result that AnsibleModule can use
        """
        result = {}
        result["changed"] = self.did_anything_change()
        result["diff"] = {}
        for state in self.states:
            result["diff"][state] = self.properties[state]
        result["response"] = self.properties["response"]
        return result

    @property
    def response(self):
        """
        return the controller response(s)
        """
        return self.properties["response"]

    @response.setter
    def response(self, value):
        self._verify_is_dict(value)
        self.properties["response"].append(value)
