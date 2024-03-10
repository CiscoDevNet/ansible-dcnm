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

import logging
from typing import Any, Dict

class Results:
    """
    Return various result templates that AnsibleModule can use.

    results = Results()
    # A generic result that indicates a task failed with no changes
    failed_result = results.failed_result
    # A generic result that indicates a task succeeded
    # obj is an instance of a class that has diff, result, and response properties 
    module_result = results.module_result(obj)

    # output of the above print() will be a dict with the following structure
    # specific keys within the diff and response dictionaries will vary depending
    # on the obj properties
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

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.state = ansible_module.params.get("state")
        self.check_mode = ansible_module.check_mode

        msg = "ENTERED Results(): "
        msg += f"state: {self.state}, "
        msg += f"check_mode: {self.check_mode}"
        self.log.debug(msg)

        self.diff_keys = ["deleted", "merged", "query"]
        self.response_keys = ["deleted", "merged", "query"]

    def did_anything_change(self, obj):
        """
        return True if obj has any changes
        Caller: module_result
        """
        if self.check_mode is True:
            self.log.debug("check_mode is True.  No changes made.")
            return False
        if len(obj.diff) != 0:
            return True
        return False

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
        for key in self.diff_keys:
            result["diff"][key] = []
        for key in self.response_keys:
            result["response"][key] = []
        return result

    @property
    def module_result(self, obj) -> Dict[str, Any]:
        """
        Return a result that AnsibleModule can use
        Result is based on the obj properties: diff, response
        """
        if not isinstance(list, obj.result):
            raise ValueError("obj.result must be a list of dict")
        if not isinstance(list, obj.diff):
            raise ValueError("obj.diff must be a list of dict")
        if not isinstance(list, obj.response):
            raise ValueError("obj.response must be a list of dict")
        result = {}
        result["changed"] = self.did_anything_change(obj)
        result["diff"] = {}
        result["response"] = {}
        for key in self.diff_keys:
            if self.state == key:
                result["diff"][key] = obj.diff
            else:
                result["diff"][key] = []
        for key in self.response_keys:
            if self.state == key:
                result["response"][key] = obj.response
            else:
                result["response"][key] = []
        return result
