# from ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upgrade import \
#     ApiEndpoints

from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import ApiEndpoints

"""
controller_version: 12
description: Verify that class ApiEndpoints returns the correct API endpoints
"""


def test_dcnm_image_upgrade_endpoints_init() -> None:
    """
    Endpoints.__init__
    """
    endpoints = ApiEndpoints()
    endpoints.__init__()
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


def test_dcnm_image_upgrade_endpoints_bootflash_info() -> None:
    """
    Endpoints.bootflash_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.bootflash_info.get("verb") == "GET"
    assert (
        endpoints.bootflash_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imagemgnt/bootFlash/bootflash-info"
    )


def test_dcnm_image_upgrade_endpoints_install_options() -> None:
    """
    Endpoints.install_options
    """
    endpoints = ApiEndpoints()
    assert endpoints.install_options.get("verb") == "POST"
    assert (
        endpoints.install_options.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade/install-options"
    )


def test_dcnm_image_upgrade_endpoints_image_stage() -> None:
    """
    Endpoints.image_stage
    """
    endpoints = ApiEndpoints()
    assert endpoints.image_stage.get("verb") == "POST"
    assert (
        endpoints.image_stage.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-image"
    )


def test_dcnm_image_upgrade_endpoints_image_upgrade() -> None:
    """
    Endpoints.image_upgrade
    """
    endpoints = ApiEndpoints()
    assert endpoints.image_upgrade.get("verb") == "POST"
    assert (
        endpoints.image_upgrade.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade/upgrade-image"
    )


def test_dcnm_image_upgrade_endpoints_image_validate() -> None:
    """
    Endpoints.image_validate
    """
    endpoints = ApiEndpoints()
    assert endpoints.image_validate.get("verb") == "POST"
    assert (
        endpoints.image_validate.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/validate-image"
    )


def test_dcnm_image_upgrade_endpoints_issu_info() -> None:
    """
    Endpoints.issu_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.issu_info.get("verb") == "GET"
    assert (
        endpoints.issu_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/packagemgnt/issu"
    )


def test_dcnm_image_upgrade_endpoints_controller_version() -> None:
    """
    Endpoints.controller_version
    """
    endpoints = ApiEndpoints()
    assert endpoints.controller_version.get("verb") == "GET"
    assert (
        endpoints.controller_version.get("path")
        == "/appcenter/cisco/ndfc/api/v1/fm/about/version"
    )


def test_dcnm_image_upgrade_endpoints_policies_attached_info() -> None:
    """
    Endpoints.policies_attached_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.policies_attached_info.get("verb") == "GET"
    assert (
        endpoints.policies_attached_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/all-attached-policies"
    )


def test_dcnm_image_upgrade_endpoints_policies_info() -> None:
    """
    Endpoints.policies_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.policies_info.get("verb") == "GET"
    assert (
        endpoints.policies_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies"
    )


def test_dcnm_image_upgrade_endpoints_policy_attach() -> None:
    """
    Endpoints.policy_attach
    """
    endpoints = ApiEndpoints()
    assert endpoints.policy_attach.get("verb") == "POST"
    assert (
        endpoints.policy_attach.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/attach-policy"
    )


def test_dcnm_image_upgrade_endpoints_policy_create() -> None:
    """
    Endpoints.policy_create
    """
    endpoints = ApiEndpoints()
    assert endpoints.policy_create.get("verb") == "POST"
    assert (
        endpoints.policy_create.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/platform-policy"
    )


def test_dcnm_image_upgrade_endpoints_policy_detach() -> None:
    """
    Endpoints.policy_detach
    """
    endpoints = ApiEndpoints()
    assert endpoints.policy_detach.get("verb") == "DELETE"
    assert (
        endpoints.policy_detach.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/detach-policy"
    )


def test_dcnm_image_upgrade_endpoints_policy_info() -> None:
    """
    Endpoints.policy_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.policy_info.get("verb") == "GET"
    assert (
        endpoints.policy_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/image-policy/__POLICY_NAME__"
    )


def test_dcnm_image_upgrade_endpoints_stage_info() -> None:
    """
    Endpoints.stage_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.stage_info.get("verb") == "GET"
    assert (
        endpoints.stage_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-info"
    )


def test_dcnm_image_upgrade_endpoints_switches_info() -> None:
    """
    Endpoints.switches_info
    """
    endpoints = ApiEndpoints()
    assert endpoints.switches_info.get("verb") == "GET"
    assert (
        endpoints.switches_info.get("path")
        == "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/inventory/allswitches"
    )
