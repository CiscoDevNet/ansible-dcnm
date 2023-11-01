from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import ApiEndpoints

class ControllerVersion(ImageUpgradeCommon):
    """
    Return image version information from the Controller

    NOTES:
    1.  considered using dcnm_version_supported() but it does not return
        minor release info, which is needed due to key changes between
        12.1.2e and 12.1.3b.  For example, see ImageStage().commit()

    Endpoint:
        /appcenter/cisco/ndfc/api/v1/fm/about/version

    Usage (where module is an instance of AnsibleModule):

    instance = ControllerVersion(module)
    instance.refresh()
    if instance.version == "12.1.2e":
        do 12.1.2e stuff
    else:
        do other stuff

    Response:
        {
            "version": "12.1.2e",
            "mode": "LAN",
            "isMediaController": false,
            "dev": false,
            "isHaEnabled": false,
            "install": "EASYFABRIC",
            "uuid": "f49e6088-ad4f-4406-bef6-2419de914ff1",
            "is_upgrade_inprogress": false
        }
    """

    def __init__(self, module):
        super().__init__(module)
        self.class_name = self.__class__.__name__
        self.endpoints = ApiEndpoints()
        self._init_properties()

    def _init_properties(self):
        self.properties = {}
        self.properties["data"] = None
        self.properties["result"] = None
        self.properties["response"] = None

    def refresh(self):
        """
        Refresh self.response_data with current version info from the Controller
        """
        path = self.endpoints.controller_version.get("path")
        verb = self.endpoints.controller_version.get("verb")
        self.properties["response"] = dcnm_send(self.module, verb, path)
        self.properties["result"] = self._handle_response(self.response, verb)

        msg = f"REMOVE: {self.class_name}.refresh() response: {self.response}"
        self.log_msg(msg)

        msg = f"REMOVE: {self.class_name}.refresh() result: {self.result}"
        self.log_msg(msg)

        if self.result["success"] == False or self.result["found"] == False:
            msg = f"{self.class_name}.refresh() failed: {self.result}"
            self.module.fail_json(msg)

        self.properties["response_data"] = self.response.get("DATA")
        if self.response_data is None:
            msg = f"{self.class_name}.refresh() failed: response "
            msg += "does not contain DATA key. Controller response: "
            msg += f"{self.response}"
            self.module.fail_json(msg)

        msg = f"REMOVE: {self.class_name}.refresh() response_data: {self.response_data}"
        self.log_msg(msg)

    def _get(self, item):
        return self.make_boolean(self.make_none(self.response_data.get(item)))

    @property
    def dev(self):
        """
        Return True if the Controller is running a development release.
        Return False if the Controller is not running a development release.
        Return None otherwise

        Possible values:
            True
            False
            None
        """
        return self._get("dev")

    @property
    def install(self):
        """
        Return the value of install, if it exists.
        Return None otherwise

        Possible values:
            EASYFABRIC
            (probably other values)
            None
        """
        return self._get("install")

    @property
    def is_ha_enabled(self):
        """
        Return True if Controller is high-availability enabled.
        Return False if Controller is not high-availability enabled.
        Return None otherwise

        Possible values:
            True
            False
            None
        """
        return self.make_boolean(self._get("isHaEnabled"))

    @property
    def is_media_controller(self):
        """
        Return True if Controller is a media controller.
        Return False if Controller is not a media controller.
        Return None otherwise

        Possible values:
            True
            False
            None
        """
        return self.make_boolean(self._get("isMediaController"))

    @property
    def is_upgrade_inprogress(self):
        """
        Return True if a Controller upgrade is in progress.
        Return False if a Controller upgrade is not in progress.
        Return None otherwise

        Possible values:
            True
            False
            None
        """
        return self.make_boolean(self._get("is_upgrade_inprogress"))

    @property
    def response_data(self):
        """
        Return the data retrieved from the request
        """
        return self.properties.get("response_data")

    @property
    def result(self):
        """
        Return the GET result from the Controller
        """
        return self.properties.get("result")

    @property
    def response(self):
        """
        Return the GET response from the Controller
        """
        return self.properties.get("response")

    @property
    def mode(self):
        """
        Return the controller mode, if it exists.
        Return None otherwise

        Possible values:
            LAN
            None
        """
        return self._get("mode")

    @property
    def uuid(self):
        """
        Return the value of uuid, if it exists.
        Return None otherwise

        Possible values:
            uuid e.g. "f49e6088-ad4f-4406-bef6-2419de914df1"
            None
        """
        return self._get("uuid")

    @property
    def version(self):
        """
        Return the controller version, if it exists.
        Return None otherwise

        Possible values:
            version, e.g. "12.1.2e"
            None
        """
        return self._get("version")

    @property
    def version_major(self):
        """
        Return the controller major version, if it exists.
        Return None otherwise

        We are assuming semantic versioning based on:
        https://semver.org

        Possible values:
            if version is 12.1.2e, return 12
            None
        """
        if self.version is None:
            return None
        return (self._get("version").split("."))[0]

    @property
    def version_minor(self):
        """
        Return the controller minor version, if it exists.
        Return None otherwise

        We are assuming semantic versioning based on:
        https://semver.org

        Possible values:
            if version is 12.1.2e, return 1
            None
        """
        if self.version is None:
            return None
        return (self._get("version").split("."))[1]

    @property
    def version_patch(self):
        """
        Return the controller minor version, if it exists.
        Return None otherwise

        We are assuming semantic versioning based on:
        https://semver.org

        Possible values:
            if version is 12.1.2e, return 2e
            None
        """
        if self.version is None:
            return None
        return (self._get("version").split("."))[2]