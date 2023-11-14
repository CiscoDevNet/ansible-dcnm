# Copyright (c) 2020-2024 Cisco and/or its affiliates.
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

"""
Tests for ApiEndpoints class
"""
from __future__ import absolute_import, division, print_function

from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"


def test_image_mgmt_api_00001() -> None:
    """
    Endpoints.__init__
    """
    endpoints = ApiEndpoints()
    assert endpoints.endpoint_api_v1 == "/appcenter/cisco/ndfc/api/v1"
    assert endpoints.endpoint_feature_manager == "/appcenter/cisco/ndfc/api/v1/fm"
    assert (
        endpoints.endpoint_image_management
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement"
    )
    assert (
        endpoints.endpoint_image_upgrade
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade"
    )
    assert endpoints.endpoint_lan_fabric == "/appcenter/cisco/ndfc/api/v1/lan-fabric"
    assert (
        endpoints.endpoint_package_mgnt
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/packagemgnt"
    )
    assert (
        endpoints.endpoint_policy_mgnt
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt"
    )
    assert (
        endpoints.endpoint_staging_management
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement"
    )


def test_image_mgmt_api_00002() -> None:
    """
    Endpoints.bootflash_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.bootflash_info.get("verb") == "GET"
    assert (
        endpoints.bootflash_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imagemgnt/bootFlash/bootflash-info"
    )


def test_image_mgmt_api_00003() -> None:
    """
    Endpoints.install_options
    """
    endpoints = ApiEndpoints()
    assert endpoints.install_options.get("verb") == "POST"
    assert (
        endpoints.install_options.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade/install-options"
    )


def test_image_mgmt_api_00004() -> None:
    """
    Endpoints.image_stage
    """
    endpoints = ApiEndpoints()
    assert endpoints.image_stage.get("verb") == "POST"
    assert (
        endpoints.image_stage.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-image"
    )


def test_image_mgmt_api_00005() -> None:
    """
    Endpoints.image_upgrade
    """
    endpoints = ApiEndpoints()
    assert endpoints.image_upgrade.get("verb") == "POST"
    assert (
        endpoints.image_upgrade.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade/upgrade-image"
    )


def test_image_mgmt_api_00006() -> None:
    """
    Endpoints.image_validate
    """
    endpoints = ApiEndpoints()
    assert endpoints.image_validate.get("verb") == "POST"
    assert (
        endpoints.image_validate.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/validate-image"
    )


def test_image_mgmt_api_00007() -> None:
    """
    Endpoints.issu_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.issu_info.get("verb") == "GET"
    assert (
        endpoints.issu_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/packagemgnt/issu"
    )


def test_image_mgmt_api_00008() -> None:
    """
    Endpoints.controller_version
    """
    endpoints = ApiEndpoints()
    assert endpoints.controller_version.get("verb") == "GET"
    assert (
        endpoints.controller_version.get("path")
        == "/appcenter/cisco/ndfc/api/v1/fm/about/version"
    )


def test_image_mgmt_api_00009() -> None:
    """
    Endpoints.policies_attached_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.policies_attached_info.get("verb") == "GET"
    assert (
        endpoints.policies_attached_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/all-attached-policies"
    )


def test_image_mgmt_api_00010() -> None:
    """
    Endpoints.policies_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.policies_info.get("verb") == "GET"
    assert (
        endpoints.policies_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies"
    )


def test_image_mgmt_api_00011() -> None:
    """
    Endpoints.policy_attach
    """
    endpoints = ApiEndpoints()
    assert endpoints.policy_attach.get("verb") == "POST"
    assert (
        endpoints.policy_attach.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/attach-policy"
    )


def test_image_mgmt_api_00012() -> None:
    """
    Endpoints.policy_create
    """
    endpoints = ApiEndpoints()
    assert endpoints.policy_create.get("verb") == "POST"
    assert (
        endpoints.policy_create.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/platform-policy"
    )


def test_image_mgmt_api_00013() -> None:
    """
    Endpoints.policy_detach
    """
    endpoints = ApiEndpoints()
    assert endpoints.policy_detach.get("verb") == "DELETE"
    assert (
        endpoints.policy_detach.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/detach-policy"
    )


def test_image_mgmt_api_00014() -> None:
    """
    Endpoints.policy_info
    """
    path = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/"
    path += "image-policy/__POLICY_NAME__"
    endpoints = ApiEndpoints()
    assert endpoints.policy_info.get("verb") == "GET"
    assert endpoints.policy_info.get("path") == path


def test_image_mgmt_api_00015() -> None:
    """
    Endpoints.stage_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.stage_info.get("verb") == "GET"
    assert (
        endpoints.stage_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-info"
    )


def test_image_mgmt_api_00016() -> None:
    """
    Endpoints.switches_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.switches_info.get("verb") == "GET"
    assert (
        endpoints.switches_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/inventory/allswitches"
    )
