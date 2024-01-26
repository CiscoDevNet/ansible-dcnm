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
__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect
import logging


class ImageUpgradeTaskResult:
    """
    Storage for ImageUpgradeTask result
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ImageUpgradeTaskResult()")

        self.diff_properties = {}
        self.diff_properties["diff_attach_policy"] = "attach_policy"
        self.diff_properties["diff_detach_policy"] = "detach_policy"
        self.diff_properties["diff_issu_status"] = "issu_status"
        self.diff_properties["diff_stage"] = "stage"
        self.diff_properties["diff_upgrade"] = "upgrade"
        self.diff_properties["diff_validate"] = "validate"
        self.response_properties = {}
        self.response_properties["response_attach_policy"] = "attach_policy"
        self.response_properties["response_detach_policy"] = "detach_policy"
        self.response_properties["response_issu_status"] = "issu_status"
        self.response_properties["response_stage"] = "stage"
        self.response_properties["response_upgrade"] = "upgrade"
        self.response_properties["response_validate"] = "validate"

        self._build_properties()

    def _build_properties(self):
        """
        Build the properties dict() with default values
        """
        self.properties = {}
        self.properties["diff_attach_policy"] = []
        self.properties["diff_detach_policy"] = []
        self.properties["diff_issu_status"] = []
        self.properties["diff_stage"] = []
        self.properties["diff_upgrade"] = []
        self.properties["diff_validate"] = []

        self.properties["response_attach_policy"] = []
        self.properties["response_issu_status"] = []
        self.properties["response_detach_policy"] = []
        self.properties["response_stage"] = []
        self.properties["response_upgrade"] = []
        self.properties["response_validate"] = []

    def did_anything_change(self):
        """
        return True if diffs have been appended to any of the diff lists.
        """
        for key in self.diff_properties:
            # skip query state diffs
            if key == "diff_issu_status":
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
    def diff_attach_policy(self):
        """
        Getter for diff_attach_policy property

        Used for merged state where we attach image policies
        to devices.
        """
        return self.properties["diff_attach_policy"]

    @diff_attach_policy.setter
    def diff_attach_policy(self, value):
        """
        Setter for diff_attach_policy property
        """
        self._verify_is_dict(value)
        self.properties["diff_attach_policy"].append(value)

    @property
    def diff_detach_policy(self):
        """
        Getter for diff_detach_policy property

        This is used for deleted state where we detach image policies
        from devices.
        """
        return self.properties["diff_detach_policy"]

    @diff_detach_policy.setter
    def diff_detach_policy(self, value):
        """
        Setter for diff_detach_policy property
        """
        self._verify_is_dict(value)
        self.properties["diff_detach_policy"].append(value)

    @property
    def diff_issu_status(self):
        """
        Getter for diff_issu_status property

        This is used query state diffs of switch issu state
        """
        return self.properties["diff_issu_status"]

    @diff_issu_status.setter
    def diff_issu_status(self, value):
        """
        Setter for diff_issu_status property
        """
        self._verify_is_dict(value)
        self.properties["diff_issu_status"].append(value)

    @property
    def diff_stage(self):
        """
        Getter for diff_stage property
        """
        return self.properties["diff_stage"]

    @diff_stage.setter
    def diff_stage(self, value):
        """
        Setter for diff_stage property
        """
        self._verify_is_dict(value)
        self.properties["diff_stage"].append(value)

    @property
    def diff_upgrade(self):
        """
        Getter for diff_upgrade property
        """
        return self.properties["diff_upgrade"]

    @diff_upgrade.setter
    def diff_upgrade(self, value):
        """
        Setter for diff_upgrade property
        """
        self._verify_is_dict(value)
        self.properties["diff_upgrade"].append(value)

    @property
    def diff_validate(self):
        """
        Getter for diff_validate property
        """
        return self.properties["diff_validate"]

    @diff_validate.setter
    def diff_validate(self, value):
        """
        Setter for diff_validate property
        """
        self._verify_is_dict(value)
        self.properties["diff_validate"].append(value)

    # response properties
    @property
    def response_attach_policy(self):
        """
        Getter for response_attach_policy property

        Used for merged state where we attach image policies
        to devices.
        """
        return self.properties["response_attach_policy"]

    @response_attach_policy.setter
    def response_attach_policy(self, value):
        """
        Setter for response_attach_policy property
        """
        self._verify_is_dict(value)
        self.properties["response_attach_policy"].append(value)

    @property
    def response_detach_policy(self):
        """
        Getter for response_detach_policy property

        This is used for deleted state where we detach image policies
        from devices.
        """
        return self.properties["response_detach_policy"]

    @response_detach_policy.setter
    def response_detach_policy(self, value):
        """
        Setter for response_detach_policy property
        """
        self._verify_is_dict(value)
        self.properties["response_detach_policy"].append(value)

    @property
    def response_issu_status(self):
        """
        Getter for response_issu_status property

        This is used for deleted state where we detach image policies
        from devices.
        """
        return self.properties["response_issu_status"]

    @response_issu_status.setter
    def response_issu_status(self, value):
        """
        Setter for response_issu_status property
        """
        self._verify_is_dict(value)
        self.properties["response_issu_status"].append(value)

    @property
    def response_stage(self):
        """
        Getter for response_stage property
        """
        return self.properties["response_stage"]

    @response_stage.setter
    def response_stage(self, value):
        """
        Setter for response_stage property
        """
        self._verify_is_dict(value)
        self.properties["response_stage"].append(value)

    @property
    def response_upgrade(self):
        """
        Getter for response_upgrade property
        """
        return self.properties["response_upgrade"]

    @response_upgrade.setter
    def response_upgrade(self, value):
        """
        Setter for response_upgrade property
        """
        self._verify_is_dict(value)
        self.properties["response_upgrade"].append(value)

    @property
    def response_validate(self):
        """
        Getter for response_validate property
        """
        return self.properties["response_validate"]

    @response_validate.setter
    def response_validate(self, value):
        """
        Setter for response_validate property
        """
        self._verify_is_dict(value)
        self.properties["response_validate"].append(value)
