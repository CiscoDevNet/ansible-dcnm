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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.common_v1 import \
    CommonV1


class ImageManagement(CommonV1):
    """
    ## V1 API - ImageManagement()

    ### Description
    Common methods and properties for CommonV1().ImageManagement() subclasses

    ### Endpoint
    ``/appcenter/cisco/ndfc/api/v1/imagemanagement``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.image_management = f"{self.api_v1}/imagemanagement"
        self.log.debug("ENTERED api.v1.ImageManagement()")