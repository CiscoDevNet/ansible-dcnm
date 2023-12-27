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
__author__ = "Allen Robel"


class ApiEndpoints:
    """
    Endpoints for image policy API calls
    """

    def __init__(self):
        self.endpoint_api_v1 = "/appcenter/cisco/ndfc/api/v1"

        self.endpoint_image_management = f"{self.endpoint_api_v1}"
        self.endpoint_image_management += "/imagemanagement"

        self.endpoint_policy_mgnt = f"{self.endpoint_image_management}"
        self.endpoint_policy_mgnt += "/rest/policymgnt"

    @property
    def bootflash_info(self):
        """
        return endpoint GET /rest/imagemgnt/bootFlash
        """
        path = f"{self.endpoint_image_management}/rest/imagemgnt/bootFlash"
        path += "/bootflash-info"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint

    @property
    def policies_info(self):
        """
        return endpoint GET /rest/policymgnt/policies
        """
        path = f"{self.endpoint_policy_mgnt}/policies"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint

    @property
    def policy_create(self):
        """
        return endpoint POST /rest/policymgnt/platform-policy
        """
        path = f"{self.endpoint_policy_mgnt}/platform-policy"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        return endpoint

    @property
    def policy_info(self):
        """
        return endpoint GET /rest/policymgnt/image-policy/__POLICY_NAME__

        Replace __POLICY_NAME__ with the policy_name to query
        e.g. path.replace("__POLICY_NAME__", "NR1F")
        """
        path = f"{self.endpoint_policy_mgnt}/image-policy/__POLICY_NAME__"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint
