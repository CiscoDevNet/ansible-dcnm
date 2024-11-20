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

from ..v1 import V1


class ConfigTemplate(V1):
    """
    ## V1 API - ConfigTemplate()

    ### Description
    Common methods and properties for api.v1.ConfigTemplate() subclasses

    ### Path
    ``/appcenter/cisco/ndfc/api/v1/configtemplate``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.configtemplate = f"{self.v1}/configtemplate"
        self.log.debug("ENTERED api.v1.configtemplate.ConfigTemplate()")
