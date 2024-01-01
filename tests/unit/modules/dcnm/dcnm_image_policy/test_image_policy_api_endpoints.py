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

from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints


def test_image_policy_endpoints_00001() -> None:
    """
    Endpoints.__init__
    """
    endpoints = ApiEndpoints()
    assert endpoints.endpoint_api_v1 == "/appcenter/cisco/ndfc/api/v1"
    assert (
        endpoints.endpoint_image_management
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement"
    )
    assert (
        endpoints.endpoint_policy_mgnt
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt"
    )


def test_image_mgmt_api_00010() -> None:
    """
    Endpoints.policies_attached_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.policies_attached_info.get("verb") == "GET"
    assert (
        endpoints.policies_attached_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/all-attached-policies"
    )


def test_image_mgmt_api_00020() -> None:
    """
    Endpoints.policies_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.policies_info.get("verb") == "GET"
    assert (
        endpoints.policies_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies"
    )


def test_image_mgmt_api_00030() -> None:
    """
    Endpoints.policy_attach
    """
    endpoints = ApiEndpoints()
    assert endpoints.policy_attach.get("verb") == "POST"
    assert (
        endpoints.policy_attach.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/attach-policy"
    )


def test_image_mgmt_api_00040() -> None:
    """
    Endpoints.policy_create
    """
    endpoints = ApiEndpoints()
    assert endpoints.policy_create.get("verb") == "POST"
    assert (
        endpoints.policy_create.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/platform-policy"
    )


def test_image_mgmt_api_00050() -> None:
    """
    Endpoints.policy_detach
    """
    endpoints = ApiEndpoints()
    assert endpoints.policy_detach.get("verb") == "DELETE"
    assert (
        endpoints.policy_detach.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/detach-policy"
    )


def test_image_mgmt_api_00060() -> None:
    """
    Endpoints.policy_info
    """
    path = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/"
    path += "image-policy/__POLICY_NAME__"
    endpoints = ApiEndpoints()
    assert endpoints.policy_info.get("verb") == "GET"
    assert endpoints.policy_info.get("path") == path
