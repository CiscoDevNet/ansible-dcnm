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
__author__ = "Prabahal"

import copy
import inspect
import json
import logging

from ..common.api.v1.lan_fabric.rest.control.fabrics.msd.msd import \
    EpFabricAssociations


# Import Results() only for the case where the user has not set Results()
# prior to calling commit().  In this case, we instantiate Results()
# in _validate_commit_parameters() so that we can register the failure
# in commit().
from ..common.results import Results


class FabricAssociations():

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.data = None
        self.results = Results()
        self.refreshed = False
        self.fabric_association_data = []

    @property
    def all_data(self) -> dict:
        """
        - Return raw fabric association data from the controller.
        - Raise ``ValueError`` if ``refresh()`` has not been called.
        """
        method_name = inspect.stack()[0][3]
        try:
            self.verify_refresh_has_been_called(method_name)
        except ValueError as error:
            raise ValueError(error) from error
        return self.fabric_association_data

    def verify_refresh_has_been_called(self, attempted_method_name):
        """
        - raise ``ValueError`` if ``refresh()`` has not been called.
        """
        if self.refreshed is True:
            return
        msg = f"{self.class_name}.refresh() must be called before accessing "
        msg += f"{self.class_name}.{attempted_method_name}."
        raise ValueError(msg)

    def refresh(self):

        method_name = inspect.stack()[0][3]
        self.ep_fabrics_associations = EpFabricAssociations()
        self.rest_send.path = self.ep_fabrics_associations.path
        self.rest_send.verb = self.ep_fabrics_associations.verb
        save_check_mode = self.rest_send.check_mode
        self.rest_send.check_mode = False
        self.rest_send.commit()
        self.rest_send.check_mode = save_check_mode
        self.fabric_association_data = copy.deepcopy(self.rest_send.response_current.get("DATA", {}))

        msg = f"self.data: {json.dumps(self.data, indent=4, sort_keys=True)}"
        self.log.debug(msg)
        self.refreshed = True

        self.results.response_current = self.rest_send.response_current
        self.results.response = self.rest_send.response_current
        self.results.result_current = self.rest_send.result_current
        self.results.result = self.rest_send.result_current

        self.results.register_task_result()

        if self.results.result_current.get("success", None) is False:
            msg = f"{self.class_name}: {method_name}: "
            msg += "Fabric Association response from NDFC controller returns failure. "
            msg += "Cannot proceed further."
            raise ValueError(msg)
