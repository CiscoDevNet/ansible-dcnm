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

import copy
import inspect
import json
import logging
from typing import Any, Dict


class Results:
    """
    Collect results across tasks.

    Provides a mechanism to collect results across tasks.  The task classes
    must support this Results class.  Specifically, they must implement the
    following:

    1.  Accept an instantiation of Results
        -   Typically a class property is used for this
    2.  Populate the Results instance with the results of the task
        -   Typically done by transferring RestSend's responses to the
            Results instance
    3. Register the results of the task with Results, using:
        -   Results.register_task_results()
        -   Typically done after the task is complete

    Results should be instantiated in the main Ansible Task class and passed
    to all other task classes.  The task classes should populate the Results
    instance with the results of the task and then register the results with
    Results.register_task_results().  This may be done within a separate class
    (as in the example below, where FabricDelete() class is called from the
    TaskDelete() class.  The Results instance can then be used to build the
    final result, by calling Results.build_final_result().


    Example Usage:

    We assume an Ansible module structure as follows:

    TaskCommon() : Common methods used by the various ansible state classes.
    TaskDelete(TaskCommon) : Implements the delete state
    TaskMerge(TaskCommon)  : Implements the merge state
    TaskQuery(TaskCommon)  : Implements the query state
    etc...

    In TaskCommon, Results is instantiated and, hence, is inherited by all
    state classes.:

    class TaskCommon:
        def __init__(self):
            self.results = Results()

        @property
        def results(self):
            '''
            An instance of the Results class.
            '''
            return self.properties["results"]

        @results.setter
        def results(self, value):
            self.properties["results"] = value


    In each of the state classes (TaskDelete, TaskMerge, TaskQuery, etc...)
    a class is instantiated (in the example below, FabricDelete) that
    supports collecting results for the Results instance:

    class TaskDelete(TaskCommon):
        def __init__(self, ansible_module):
            super().__init__(ansible_module)
            self.fabric_delete = FabricDelete(self.ansible_module)

        def commit(self):
            '''
            delete the fabric
            '''
            ...
            self.fabric_delete.fabric_names = ["FABRIC_1", "FABRIC_2"]
            self.fabric_delete.results = self.results
            # results.register_task_results() is called within the
            # commit() method of the FabricDelete class.
            self.fabric_delete.commit()


    Finally, within the main() method of the Ansible module, the final result
    is built by calling Results.build_final_result():

    if ansible_module.params["state"] == "deleted":
        task = TaskDelete(ansible_module)
        task.commit()
    elif ansible_module.params["state"] == "merged":
        task = TaskDelete(ansible_module)
        task.commit()
    etc...

    # Build the final result
    task.results.build_final_result()

    # Call fail_json() or exit_json() based on the final result
    if True in task.results.failed:
        ansible_module.fail_json(**task.results.final_result)
    ansible_module.exit_json(**task.results.final_result)


    # results.final_result will be a dict with the following structure

    {
        "changed": True, # or False
        "failed": True,  # or False
        "diff": {
            "OK": [<list of dict containing changes that succeeded>],
            "FAILED": [<list of dict containing changes that failed>]
        }
        "response": {
            "OK": [<list of dict containing successful controller responses>],
            "FAILED": [<list of dict containing failed controller responses>]
        }
        "result": {
            "OK": [<list of dict containing successful controller responses>],
            "FAILED": [<list of dict containing failed controller responses>]
        }
    }
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED Results():"
        self.log.debug(msg)

        self.diff_keys = ["deleted", "merged", "query"]
        self.response_keys = ["deleted", "merged", "query"]

        self.diff_ok = []
        self.response_ok = []
        self.result_ok = []
        self.diff_nok = []
        self.response_nok = []
        self.result_nok = []

        # Assign a unique sequence number to each registered task
        self.task_sequence_number = 0

        self.final_result = {}
        self._build_properties()

    def _build_properties(self):
        self.properties: Dict[str, Any] = {}
        self.properties["action"] = None
        self.properties["changed"] = set()
        self.properties["check_mode"] = False
        self.properties["diff"] = []
        self.properties["diff_current"] = {}
        self.properties["failed"] = set()
        self.properties["metadata"] = []
        self.properties["response"] = []
        self.properties["response_current"] = {}
        self.properties["response_data"] = []
        self.properties["result"] = []
        self.properties["result_current"] = {}
        self.properties["state"] = None

    def increment_task_sequence_number(self) -> None:
        """
        Increment a unique task sequence number.
        """
        self.task_sequence_number += 1
        msg = f"self.task_sequence_number: {self.task_sequence_number}"
        self.log.debug(msg)

    def did_anything_change(self) -> bool:
        """
        Return True if there were any changes
        Otherwise, return False
        """
        msg = f"{self.class_name}.did_anything_change(): ENTERED: "
        msg += f"self.action: {self.action}, "
        msg += f"self.result_current: {self.result_current}, "
        msg += f"self.diff: {self.diff}"
        self.log.debug(msg)
        if self.check_mode is True:
            return False
        if self.action == "query":
            msg = f"{self.class_name}.did_anything_change(): "
            msg += f"self.action: {self.action}"
            self.log.debug(msg)
            return False
        if self.result_current.get("changed", None) is True:
            return True
        if self.result_current.get("changed", None) is False:
            return False
        if len(self.diff) != 0:
            return True
        return False

    def register_task_result(self):
        """
        Register a task's result.

        1.  Append result_current, response_current, diff_current and
            metadata_current their respective lists (result, response, diff,
            and metadata)
        2.  Set self.changed based on current_diff.
            If current_diff is empty, it is assumed that no changes were made
            and self.changed is set to False.  Else, self.changed is set to True.
        3.  Set self.failed based on current_result.  If current_result["success"]
            is True, self.failed is set to False.  Else, self.failed is set to True.
        4.  Set self.metadata based on current_metadata.

        - self.response  : list of controller responses
        - self.result    : list of results returned by the handler
        - self.diff      : list of diffs
        - self.metadata  : list of metadata
        """
        method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "
        msg += f"ENTERED: self.action: {self.action}, "
        msg += f"self.result_current: {self.result_current}"
        self.log.debug(msg)

        self.increment_task_sequence_number()
        self.metadata = self.metadata_current
        self.response = self.response_current
        self.result = self.result_current
        self.diff = self.diff_current

        if self.did_anything_change() is False:
            self.changed = False
        else:
            self.changed = True

        if self.result_current.get("success") is True:
            self.failed = False
        else:
            self.failed = True

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.diff: {json.dumps(self.diff, indent=4, sort_keys=True)}, "
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.metadata: {json.dumps(self.metadata, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.response: {json.dumps(self.response, indent=4, sort_keys=True)}, "
        self.log.debug(msg)

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.result: {json.dumps(self.result, indent=4, sort_keys=True)}, "
        self.log.debug(msg)

    def build_final_result(self):
        """
        Build the final result
        """
        msg = f"self.changed: {self.changed}, "
        msg = f"self.failed: {self.failed}, "
        self.log.debug(msg)

        if True in self.failed:  # pylint: disable=unsupported-membership-test
            self.final_result["failed"] = True
        else:
            self.final_result["failed"] = False

        if True in self.changed:  # pylint: disable=unsupported-membership-test
            self.final_result["changed"] = True
        else:
            self.final_result["changed"] = False
        self.final_result["diff"] = self.diff
        self.final_result["response"] = self.response
        self.final_result["result"] = self.result
        self.final_result["metadata"] = self.metadata

    @property
    def failed_result(self) -> Dict[str, Any]:
        """
        return a result for a failed task with no changes
        """
        result = {}
        result["changed"] = False
        result["failed"] = True
        result["diff"] = [{}]
        result["response"] = [{}]
        result["result"] = [{}]
        return result

    @property
    def action(self):
        """
        Added to results to indicate the action that was taken
        """
        return self.properties["action"]

    @action.setter
    def action(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.{method_name} must be a string. "
            msg += f"Got {value}."
            raise ValueError(msg)
        msg = f"{self.class_name}.{method_name}: "
        msg += f"value: {value}"
        self.log.debug(msg)
        self.properties["action"] = value

    @property
    def changed(self) -> set[bool]:
        """
        bool = whether we changed anything

        raise ValueError if value is not a bool
        """
        return self.properties["changed"]

    @changed.setter
    def changed(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.changed must be a bool. Got {value}"
            raise ValueError(msg)
        self.properties["changed"].add(value)

    @property
    def check_mode(self):
        """
        check_mode
        """
        return self.properties["check_mode"]

    @check_mode.setter
    def check_mode(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.{method_name} must be a bool. "
            msg += f"Got {value}."
            raise ValueError(msg)
        self.properties["check_mode"] = value

    @property
    def diff(self):
        """
        List of dicts representing the changes made

        raise ValueError if value is not a dict
        """
        return self.properties["diff"]

    @diff.setter
    def diff(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.diff must be a dict. Got {value}"
            raise ValueError(msg)
        value["sequence_number"] = self.task_sequence_number
        self.properties["diff"].append(copy.deepcopy(value))

    @property
    def diff_current(self):
        """
        Return the current diff

        This is a dict of the current diff set by the handler.
        """
        value = self.properties.get("diff_current")
        value["sequence_number"] = self.task_sequence_number
        return value

    @diff_current.setter
    def diff_current(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.diff_current must be a dict. "
            msg += f"Got {value}."
            raise ValueError(msg)
        self.properties["diff_current"] = value

    @property
    def failed(self) -> set[bool]:
        """
        A set() of Boolean values indicating whether any tasks failed

        If the set contains True, at least one task failed
        If the set contains only False all tasks succeeded

        raise ValueError if value is not a bool
        """
        return self.properties["failed"]

    @failed.setter
    def failed(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            # Setting failed, itself failed(!)
            # Add True to failed to indicate this.
            self.properties["failed"].add(True)
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.failed must be a bool. Got {value}"
            raise ValueError(msg)
        self.properties["failed"].add(value)

    @property
    def metadata(self):
        """
        List of dicts representing the metadata (if any)
        for each diff.

        raise ValueError if value is not a dict
        """
        return self.properties["metadata"]

    @metadata.setter
    def metadata(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.metadata must be a dict. Got {value}"
            raise ValueError(msg)
        value["sequence_number"] = self.task_sequence_number
        self.properties["metadata"].append(copy.deepcopy(value))

    @property
    def metadata_current(self):
        """
        Return the current metadata which is comprised of the
        properties action, check_mode, and state.
        """
        value = {}
        value["action"] = self.action
        value["check_mode"] = self.check_mode
        value["state"] = self.state
        value["sequence_number"] = self.task_sequence_number
        return value

    @property
    def response_current(self):
        """
        Return the current POST response from the controller
        instance.commit() must be called first.

        This is a dict of the current response from the controller.
        """
        value = self.properties.get("response_current")
        value["sequence_number"] = self.task_sequence_number
        return value

    @response_current.setter
    def response_current(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.response_current must be a dict. "
            msg += f"Got {value}."
            raise ValueError(msg)
        self.properties["response_current"] = value

    @property
    def response(self):
        """
        Return the aggregated POST response from the controller
        instance.commit() must be called first.

        This is a list of responses from the controller.
        """
        return self.properties.get("response")

    @response.setter
    def response(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.response must be a dict. "
            msg += f"Got {value}."
            raise ValueError(msg)
        value["sequence_number"] = self.task_sequence_number
        self.properties["response"].append(copy.deepcopy(value))

    @property
    def response_data(self):
        """
        Return the contents of the DATA key within current_response.
        """
        return self.properties.get("response_data")

    @response_data.setter
    def response_data(self, value):
        self.properties["response_data"].append(value)

    @property
    def result(self):
        """
        Return the aggregated result from the controller
        instance.commit() must be called first.

        This is a list of results from the controller.
        """
        return self.properties.get("result")

    @result.setter
    def result(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.result must be a dict. "
            msg += f"Got {value}."
            raise ValueError(msg)
        value["sequence_number"] = self.task_sequence_number
        self.properties["result"].append(copy.deepcopy(value))

    @property
    def result_current(self):
        """
        Return the current result from the controller
        instance.commit() must be called first.

        This is a dict containing the current result.
        """
        value = self.properties.get("result_current")
        value["sequence_number"] = self.task_sequence_number
        return value

    @result_current.setter
    def result_current(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.result_current must be a dict. "
            msg += f"Got {value}."
            raise ValueError(msg)
        self.properties["result_current"] = value

    @property
    def state(self):
        """
        Ansible state
        """
        return self.properties["state"]

    @state.setter
    def state(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.{method_name} must be a string. "
            msg += f"Got {value}."
            raise ValueError(msg)
        self.properties["state"] = value
