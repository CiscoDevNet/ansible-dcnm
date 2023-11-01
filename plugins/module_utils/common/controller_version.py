from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (dcnm_send)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.ndfc_common import NdfcCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.endpoints import NdfcEndpoints

class NdfcVersion(NdfcCommon):
    """
    Return image version information from NDFC

    NOTES:
    1.  considered using dcnm_version_supported() but it does not return
        minor release info, which is needed due to key changes between
        12.1.2e and 12.1.3b.  For example, see NdfcImageStage().commit()

    Endpoint:
        /appcenter/cisco/ndfc/api/v1/fm/about/version

    Usage (where module is an instance of AnsibleModule):

    instance = NdfcVersion(module)
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
        self.endpoints = NdfcEndpoints()
        self._init_properties()

    def _init_properties(self):
        self.properties = {}
        self.properties["data"] = None
        self.properties["ndfc_result"] = None
        self.properties["ndfc_response"] = None

    def refresh(self):
        """
        Refresh self.ndfc_data with current version info from NDFC
        """
        path = self.endpoints.ndfc_version.get("path")
        verb = self.endpoints.ndfc_version.get("verb")
        self.properties["ndfc_response"] = dcnm_send(self.module, verb, path)
        self.properties["ndfc_result"] = self._handle_response(self.ndfc_response, verb)

        msg = f"REMOVE: {self.class_name}.refresh() ndfc_response: {self.ndfc_response}"
        self.log_msg(msg)

        msg = f"REMOVE: {self.class_name}.refresh() ndfc_result: {self.ndfc_result}"
        self.log_msg(msg)

        if self.ndfc_result["success"] == False or self.ndfc_result["found"] == False:
            msg = f"{self.class_name}.refresh() failed: {self.ndfc_result}"
            self.module.fail_json(msg)

        self.properties["ndfc_data"] = self.ndfc_response.get("DATA")
        if self.ndfc_data is None:
            msg = f"{self.class_name}.refresh() failed: NDFC response "
            msg += "does not contain DATA key. NDFC response: "
            msg += f"{self.ndfc_response}"
            self.module.fail_json(msg)

        msg = f"REMOVE: {self.class_name}.refresh() ndfc_data: {self.ndfc_data}"
        self.log_msg(msg)

    def _get(self, item):
        return self.make_boolean(self.make_none(self.ndfc_data.get(item)))

    @property
    def dev(self):
        """
        Return True if NDFC is a development release.
        Return False if NDFC is not a development release.
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
        Return True if NDFC is a media controller.
        Return False if NDFC is not a media controller.
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
        Return True if NDFC is a media controller.
        Return False if NDFC is not a media controller.
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
        Return True if an NDFC upgrade is in progress.
        Return False if an NDFC upgrade is not in progress.
        Return None otherwise

        Possible values:
            True
            False
            None
        """
        return self.make_boolean(self._get("is_upgrade_inprogress"))

    @property
    def ndfc_data(self):
        """
        Return the data retrieved from the request
        """
        return self.properties.get("ndfc_data")

    @property
    def ndfc_result(self):
        """
        Return the GET result from NDFC
        """
        return self.properties.get("ndfc_result")

    @property
    def ndfc_response(self):
        """
        Return the GET response from NDFC
        """
        return self.properties.get("ndfc_response")

    @property
    def mode(self):
        """
        Return the NDFC mode, if it exists.
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
        Return the NDFC version, if it exists.
        Return None otherwise

        Possible values:
            version, e.g. "12.1.2e"
            None
        """
        return self._get("version")

    @property
    def version_major(self):
        """
        Return the NDFC major version, if it exists.
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
        Return the NDFC minor version, if it exists.
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
        Return the NDFC minor version, if it exists.
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
