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

        # Assign a unique sequence number to each diff to enable tracking
        # of the order in which it was executed
        self.diff_sequence_number = 0

        self.final_result = {}
        self._build_properties()
    
    def _build_properties(self):
        self.properties: Dict[str, Any] = {}
        self.properties["action"] = None
        self.properties["changed"] = set()
        self.properties["check_mode"] = False
        self.properties["diff"] = []
        self.properties["failed"] = set()
        self.properties["response"] = []
        self.properties["response_current"] = {}
        self.properties["response_data"] = []
        self.properties["result"] = []
        self.properties["result_current"] = {}
        self.properties["state"] = None

    def get_diff_sequence_number(self) -> int:
        """
        Return a unique sequence number for the current result
        """
        self.diff_sequence_number += 1
        return self.diff_sequence_number

    def did_anything_change(self) -> bool:
        """
        return True if there were any changes
        """
        if self.check_mode is True:
            self.log.debug("check_mode is True.  No changes made.")
            return False
        if len(self.diff) != 0:
            return True
        return False

    def register_task_results(self):
        """
        Register a task's results

        - self.response_ok  : list of controller responses associated with success result
        - self.result_ok    : list of results where success is True
        - self.diff_ok      : list of payloads for which the request succeeded
        - self.response_nok : list of controller responses associated with failed result
        - self.result_nok   : list of results where success is False
        - self.diff_nok     : list of payloads for which the request failed
        """
        method_name = inspect.stack()[0][3]

        self.changed = self.did_anything_change()
        # All requests succeeded, set changed to True and return
        if len(self.result_nok) == 0:
            self.failed = False
        else:
            self.failed = True

        # Provide the results for all (failed and successful) requests

        # Add a sequence number, action, and "OK" result to the
        # response(s) that succeeded
        result_string = "OK"
        for diff in self.diff_ok:
            if diff.get("metadata") is None:
                diff["metadata"] = {}
                diff["metadata"]["action"] = self.action
                diff["metadata"]["check_mode"] = self.check_mode
                diff["metadata"]["sequence_number"] = self.get_diff_sequence_number()
                diff["metadata"]["result"] = result_string
            self.diff = copy.deepcopy(diff)
        for result in self.result_ok:
            if result.get("metadata") is None:
                result["metadata"] = {}
                result["metadata"]["action"] = self.action
                result["metadata"]["check_mode"] = self.check_mode
                result["metadata"]["result"] = result_string
            self.result = copy.deepcopy(result)
            self.result_current = copy.deepcopy(result)
        for response in self.response_ok:
            if response.get("metadata") is None:
                response["metadata"] = {}
                response["metadata"]["action"] = self.action
                response["metadata"]["check_mode"] = self.check_mode
                response["metadata"]["result"] = result_string
            self.response = copy.deepcopy(response)
            self.response_current = copy.deepcopy(response)

        # Add a "FAILED" result to the response(s) that failed
        result_string = "FAILED"
        for diff in self.diff_nok:
            if diff.get("metadata") is None:
                diff["metadata"] = {}
                diff["metadata"]["action"] = self.action
                diff["metadata"]["check_mode"] = self.check_mode
                diff["metadata"]["sequence_number"] = self.get_diff_sequence_number()
                diff["metadata"]["result"] = result_string
            self.diff = copy.deepcopy(diff)
        for result in self.result_nok:
            if result.get("metadata") is None:
                result["metadata"] = {}
                result["metadata"]["action"] = self.action
                result["metadata"]["check_mode"] = self.check_mode
                result["metadata"]["result"] = result_string
            self.result = copy.deepcopy(result)
            self.result_current = copy.deepcopy(result)
        for response in self.response_nok:
            if response.get("metadata") is None:
                response["metadata"] = {}
                response["metadata"]["action"] = self.action
                response["metadata"]["check_mode"] = self.check_mode
                response["metadata"]["result"] = result_string
            self.response = copy.deepcopy(response)
            self.response_current = copy.deepcopy(response)

    def build_final_result(self):
        """
        Build the final result
        """
        self.final_result = {}
        self.final_result["diff"] = {}
        self.final_result["response"] = {}
        self.final_result["result"] = {}
        if True in self.failed:
            self.final_result["failed"] = True
        else:
            self.final_result["failed"] = False
        msg = f"self.changed: {self.changed}"
        self.log.debug(msg)
        if True in self.changed:
            self.final_result["changed"] = True
        else:
            self.final_result["changed"] = False
        self.final_result["diff"]["OK"] = self.diff_ok
        self.final_result["response"]["OK"] = self.response_ok
        self.final_result["result"]["OK"] = self.result_ok
        self.final_result["diff"]["FAILED"] = self.diff_nok
        self.final_result["response"]["FAILED"] = self.response_nok
        self.final_result["result"]["FAILED"] = self.result_nok

    @property
    def failed_result(self) -> Dict[str, Any]:
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
    def action(self):
        """
        Added to results to indicate the action that was taken
        """
        return self.properties.get("action")

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
    def changed(self):
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
        return self.properties.get("check_mode")

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
        self.properties["diff"].append(value)

    @property
    def failed(self):
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
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.failed must be a bool. Got {value}"
            raise ValueError(msg)
        self.properties["failed"].add(value)

    @property
    def response_current(self):
        """
        Return the current POST response from the controller
        instance.commit() must be called first.

        This is a dict of the current response from the controller.
        """
        return self.properties.get("response_current")

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
        self.properties["response"].append(value)

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
        self.properties["result"].append(value)

    @property
    def result_current(self):
        """
        Return the current result from the controller
        instance.commit() must be called first.

        This is a dict containing the current result.
        """
        return self.properties.get("result_current")

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
        return self.properties.get("state")

    @state.setter
    def state(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.{method_name} must be a string. "
            msg += f"Got {value}."
            raise ValueError(msg)
        self.properties["state"] = value
