#
# Copyright (c) 2025 Cisco and/or its affiliates.
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
__author__ = "prabahal"

import copy
import inspect
import json
import logging

from ..common.api.v1.lan_fabric.rest.control.fabrics.msd.msd import \
    EpChildFabricAdd
from ..common.results import Results
from ...module_utils.fabric.common import FabricCommon


class childFabricAdd(FabricCommon):
    """
    methods and properties for adding Child fabric into MSD:

    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.action = "child_fabric_add"
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.ep_fabric_add = EpChildFabricAdd()
        msg = "ENTERED childFabricAdd()"
        self.log.debug(msg)
        self._fabric_names = None
        self.deploy = False

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

    def commit(self, payload):
        """
        ### Summary
        -   Add child fabrics to Mentioned MSD fabric.

        ### Raises
        -   ``ValueError`` if:
            -   ``_validate_commit_parameters`` raises ``ValueError``.

        """
        if 'DEPLOY' in payload:
            self.deploy = payload.pop('DEPLOY')

        try:
            self._validate_commit_parameters()
        except ValueError as error:
            self.results.action = self.action
            self.results.changed = False
            self.results.failed = True
            if self.rest_send is not None:
                self.results.check_mode = self.rest_send.check_mode
                self.results.state = self.rest_send.state
            else:
                self.results.check_mode = False
                self.results.state = "Added"
            self.results.register_task_result()
            raise ValueError(error) from error

        try:
            self.rest_send.path = self.ep_fabric_add.path
            self.rest_send.verb = self.ep_fabric_add.verb
            self.rest_send.payload = payload
            self.rest_send.save_settings()
            self.rest_send.check_mode = False
            self.rest_send.timeout = 1
            self.rest_send.commit()
            self.rest_send.restore_settings()
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error
        if self.rest_send.result_current["success"] is False:
            self.results.diff_current = {}
        else:
            self.results.diff_current = copy.deepcopy(payload)
        self.results.action = self.action
        self.results.state = self.rest_send.state
        self.results.check_mode = self.rest_send.check_mode
        self.results.response_current = copy.deepcopy(
            self.rest_send.response_current
        )
        self.results.result_current = copy.deepcopy(self.rest_send.result_current)
        self.results.register_task_result()
        msg = f"self.results.diff: {json.dumps(self.results.diff, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if True in self.results.failed:
            return

        if self.deploy is True:
            payload.update({'DEPLOY': True})
            self._config_save(payload)

    def _validate_commit_parameters(self):
        """
        - validate the parameters for commit
        - raise ``ValueError`` if ``fabric_names`` is not set
        """
        method_name = inspect.stack()[0][3]

        if self.fabric_names is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_names must be set prior to calling commit."
            raise ValueError(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set prior to calling commit."
            raise ValueError(msg)

        if self.results is None:
            # Instantiate Results() only to register the failure
            self.results = Results()
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set prior to calling commit."
            raise ValueError(msg)
