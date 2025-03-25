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
__author__ = "Prabahal"
import copy
import inspect
import logging

from ..common.results import Results
from ..msd.Fabric_associations import FabricAssociations


class childFabricQuery():
    """
    ### Summary
    Query child fabrics.

    ### Raises
    -   ``ValueError`` if:
        -   ``fabric_names`` is not set.
        -   ``rest_send`` is not set.
        -   ``results`` is not set.
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.action = "child_fabric_query"

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._fabric_names = None
        self._fabric_associations = []
        self.rest_send = None
        msg = "ENTERED ChildFabricQuery()"
        self.log.debug(msg)

    @property
    def fabric_names(self):
        """
        ### Summary
        -   setter: return the fabric names
        -   getter: set the fabric_names

        ### Raises
        -   ``ValueError`` if:
            -   ``value`` is not a list.
            -   ``value`` is an empty list.
            -   ``value`` is not a list of strings.

        """
        return self._fabric_names

    @fabric_names.setter
    def fabric_names(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be a list. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise ValueError(msg)
        if len(value) == 0:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be a list of at least one string. "
            msg += f"got {value}."
            raise ValueError(msg)
        for item in value:
            if not isinstance(item, str):
                msg = f"{self.class_name}.{method_name}: "
                msg += "fabric_names must be a list of strings. "
                msg += f"got {type(item).__name__} for "
                msg += f"value {item}"
                raise ValueError(msg)
        self._fabric_names = value

    def _validate_commit_parameters(self):
        """
        ### Summary
        -   validate the parameters for commit.

        ### Raises
        -   ``ValueError`` if:
            -   ``fabric_names`` is not set.
            -   ``rest_send`` is not set.
            -   ``results`` is not set.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        if self.fabric_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be set before calling commit."
            raise ValueError(msg)

        # pylint: disable=no-member
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit."
            raise ValueError(msg)

        # pylint: disable=access-member-before-definition
        if self.results is None:
            # Instantiate Results() to register the failure
            self.results = Results()
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set before calling commit."
            raise ValueError(msg)

    def commit(self):
        """
        ### Summary
        -   query each of the fabrics in ``fabric_names``.

        ### Raises
        -   ``ValueError`` if:
            -   ``_validate_commit_parameters`` raises ``ValueError``.

        """
        try:
            self._validate_commit_parameters()
        except ValueError as error:
            # pylint: disable=no-member
            self.results.action = self.action
            self.results.changed = False
            self.results.failed = True
            if self.rest_send is not None:
                self.results.check_mode = self.rest_send.check_mode
                self.results.state = self.rest_send.state
            else:
                self.results.check_mode = False
                self.results.state = "query"
            self.results.register_task_result()
            raise ValueError(error) from error
            # pylint: enable=no-member
        try:
            self.fab_association = FabricAssociations()
            self.fab_association.rest_send = self.rest_send
            self.fab_association.refresh()

        except (TypeError, ValueError) as error:
            raise ValueError(error) from error

        self.data = {}
        if self.fab_association.fabric_association_data is None:
            # The DATA key should always be present. We should never hit this.
            return
        for item in self.fab_association.fabric_association_data:
            fabric_name = item.get("fabricName", None)
            if fabric_name is None:
                continue
            self.data[fabric_name] = item

        add_to_diff = {}
        for fabric_name in self.fabric_names:
            for item in self.data:
                if self.data[item]['fabricParent'] == fabric_name:
                    add_to_diff[self.data[item]['fabricName']] = self.data[item]

        msg = f"filtered data : {add_to_diff}"
        self.log.debug(msg)
        # pylint: disable=no-member
        self.results.action = self.action
        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state
        # pylint: disable=no-member
        self.results.diff_current = add_to_diff
        if not add_to_diff:
            self.results.result_current = {"success": True, "found": False}
        else:
            self.results.result_current = {"success": True, "found": True}
        self.results.response_current = copy.deepcopy(
            self.rest_send.response_current
        )
        self.results.result_current = copy.deepcopy(
            self.results.result_current
        )
        self.results.register_task_result()
