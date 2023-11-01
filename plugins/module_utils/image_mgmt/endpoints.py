class NdfcEndpoints:
    """
    Endpoints for NDFC image management API calls
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
        path = f"{self.endpoint_image_management}/rest/imagemgnt/bootFlash"
        path += f"/bootflash-info"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint

    @property
    def install_options(self):
        path = f"{self.endpoint_image_upgrade}/install-options"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        return endpoint

    @property
    def image_stage(self):
        path = f"{self.endpoint_staging_management}/stage-image"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        return endpoint

    @property
    def image_upgrade(self):
        path = f"{self.endpoint_image_upgrade}/upgrade-image"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        return endpoint

    @property
    def image_validate(self):
        path = f"{self.endpoint_staging_management}/validate-image"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        return endpoint

    @property
    def issu_info(self):
        path = f"{self.endpoint_package_mgnt}/issu"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint
    
    @property
    def ndfc_version(self):
        path = f"{self.endpoint_feature_manager}/about/version"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint

    @property
    def policies_attached_info(self):
        path = f"{self.endpoint_policy_mgnt}/all-attached-policies"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint
    
    @property
    def policies_info(self):
        path = f"{self.endpoint_policy_mgnt}/policies"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint

    @property
    def policy_attach(self):
        path = f"{self.endpoint_policy_mgnt}/attach-policy"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        return endpoint

    @property
    def policy_create(self):
        path = f"{self.endpoint_policy_mgnt}/platform-policy"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        return endpoint

    @property
    def policy_detach(self):
        path = f"{self.endpoint_policy_mgnt}/detach-policy"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "DELETE"
        return endpoint
    
    @property
    def policy_info(self):
        # Replace __POLICY_NAME__ with the policy_name to query
        # e.g. path.replace("__POLICY_NAME__", "NR1F")
        path = f"{self.endpoint_policy_mgnt}/image-policy/__POLICY_NAME__"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint
    
    @property
    def stage_info(self):
        path = f"{self.endpoint_staging_management}/stage-info"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint
    
    @property
    def switches_info(self):
        path = f"{self.endpoint_lan_fabric}/rest/inventory/allswitches"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        return endpoint
