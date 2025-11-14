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

import logging

from ..v2 import V2


class EpSites(V2):
    """
    ## Api().Config().ClassEp().V2().EpSites()

    ### Description

    Endpoint information for retrieving Federation Sites from the
    controller.

    ### Raises

    -   None

    ### Path

    ``/api/config/class/v2/sites``

    ### Verb

    ``GET``

    ### Parameters

    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.config.class_ep.v2.sites import EpSites
    instance = EpSites()
    path = instance.path
    verb = instance.verb
    ```

    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED api.config.class_ep.v2.sites.EpSites()")
        # trailing backslash is needed here
        self._path = f"{self.v2}/sites/"
        self._verb = "GET"
