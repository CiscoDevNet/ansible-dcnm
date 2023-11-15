"""
Endpoints for image management API calls
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

class ApiEndpoints:
    """
    Endpoints for image management API calls
    """

    def __init__(self):
        self.endpoint_api_v1 = "/appcenter/cisco/ndfc/api/v1"

        self.endpoint_feature_manager = f"{self.endpoint_api_v1}/fm"
        self.endpoint_lan_fabric = f"{self.endpoint_api_v1}/lan-fabric"

        self.endpoint_image_management = f"{self.endpoint_api_v1}"
        self.endpoint_image_management += "/imagemanagement"

        self.endpoint_image_upgrade = f"{self.endpoint_image_management}"
        self.endpoint_image_upgrade += "/rest/imageupgrade"

        self.endpoint_package_mgnt = f"{self.endpoint_image_management}"
        self.endpoint_package_mgnt += "/rest/packagemgnt"

        self.endpoint_policy_mgnt = f"{self.endpoint_image_management}"
        self.endpoint_policy_mgnt += "/rest/policymgnt"

        self.endpoint_staging_management = f"{self.endpoint_image_management}"
        self.endpoint_staging_management += "/rest/stagingmanagement"

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
    def install_options(self):
        """
        return endpoint POST /rest/imageupgrade/install-options
        """
        path = f"{self.endpoint_image_upgrade}/install-options"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        return endpoint

    @property
    def image_stage(self):
        """
        return endpoint POST /rest/stagingmanagement/stage-image
        """
        path = f"{self.endpoint_staging_management}/stage-image"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        return endpoint

    @property
    def image_upgrade(self):
        """
        return endpoint POST /rest/imageupgrade/upgrade-image
        """
        path = f"{self.endpoint_image_upgrade}/upgrade-image"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        return endpoint

    @property
    def image_validate(self):
        """
        return endpoint POST /rest/stagingmanagement/validate-image
        """
        path = f"{self.endpoint_staging_management}/validate-image"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        return endpoint

    @property
    def issu_info(self):
        """
        return endpoint GET /rest/packagemgnt/issu
        """
        path = f"{self.endpoint_package_mgnt}/issu"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint

    @property
    def controller_version(self):
        """
        return endpoint GET /appcenter/cisco/ndfc/api/v1/fm/about/version
        """
        path = f"{self.endpoint_feature_manager}/about/version"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint

    @property
    def policies_attached_info(self):
        """
        return endpoint GET /rest/policymgnt/all-attached-policies
        """
        path = f"{self.endpoint_policy_mgnt}/all-attached-policies"
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
    def policy_attach(self):
        """
        return endpoint POST /rest/policymgnt/attach-policy
        """
        path = f"{self.endpoint_policy_mgnt}/attach-policy"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
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
    def policy_detach(self):
        """
        return endpoint DELETE /rest/policymgnt/detach-policy
        """
        path = f"{self.endpoint_policy_mgnt}/detach-policy"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "DELETE"
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

    @property
    def stage_info(self):
        """
        return endpoint GET /rest/stagingmanagement/stage-info
        """
        path = f"{self.endpoint_staging_management}/stage-info"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint

    @property
    def switches_info(self):
        """
        return endpoint GET /rest/inventory/allswitches
        """
        path = f"{self.endpoint_lan_fabric}/rest/inventory/allswitches"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint
