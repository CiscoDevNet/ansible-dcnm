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

from ..conversion import ConversionUtils


class ApiNd:
    """
    ## API endpoints for ND- ApiNd()

    ### Description
    Common methods and properties for ApiNd() subclasses.

    ### Path
    ``/api``
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.conversion = ConversionUtils()
        # Popuate in subclasses to indicate which properties
        # are mandatory for the subclass.
        self.required_properties = set()
        self.log.debug("ENTERED api.ApiNd()")
        self.api = "/api"
        self._init_properties()

    def _init_properties(self):
        self._path = None
        self._verb = None

    @property
    def path(self):
        """
        Return the endpoint path.
        """
        return self._path

    @property
    def verb(self):
        """
        Return the endpoint verb.
        """
        return self._verb
