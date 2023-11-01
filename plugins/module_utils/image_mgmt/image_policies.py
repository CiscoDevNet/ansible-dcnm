from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import ApiEndpoints

class ImagePolicies(ImageUpgradeCommon):
    """
    Retrieve image policy details from the controller and provide
    property accessors for the policy attributes.

    Usage (where module is an instance of AnsibleModule):

    instance = ImagePolicies(module).refresh()
    instance.policy_name = "NR3F"
    if instance.name is None:
        print("policy NR3F does not exist on the controller")
        exit(1)
    policy_name = instance.name
    platform = instance.platform
    epd_image_name = instance.epld_image_name
    etc...

    Policies are retrieved on instantiation of this class.
    Policies can be refreshed by calling instance.refresh().

    Endpoint:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies
    """

    def __init__(self, module):
        super().__init__(module)
        self.class_name = self.__class__.__name__
        self.endpoints = ApiEndpoints()
        self.log_msg(f"{self.class_name}.__init__ entered")
        self._init_properties()
        # TODO:2 Need a way to call refresh() in __init__ with unit-tests being able to mock it
        #self.refresh()

    def _init_properties(self):
        self.properties = {}
        self.properties["policy_name"] = None
        self.properties["response_data"] = None
        self.properties["response"] = None
        self.properties["result"] = None

    def refresh(self):
        """
        Refresh self.image_policies with current image policies from the controller
        """
        path = self.endpoints.policies_info.get("path")
        verb = self.endpoints.policies_info.get("verb")

        self.properties["response"] = dcnm_send(self.module, verb, path)
        self.log_msg(f"{self.class_name}.refresh: response: {self.response}")

        self.properties["result"] = self._handle_response(self.response, verb)
        self.log_msg(f"{self.class_name}.refresh: result: {self.result}")

        msg = f"REMOVE: {self.class_name}.refresh: "
        msg += f"result: {self.result}"
        if not self.result["success"]:
            msg = f"{self.class_name}.refresh: "
            msg += "Bad result when retriving image policy "
            msg += "information from the controller."
            self.module.fail_json(msg)

        data = self.response.get("DATA").get("lastOperDataObject")
        if data is None:
            msg = f"{self.class_name}.refresh: "
            msg += "Bad response when retrieving image policy "
            msg += "information from the controller."
            self.module.fail_json(msg)
        if len(data) == 0:
            msg = f"{self.class_name}.refresh: "
            msg += "the controller has no defined image policies."
            self.module.fail_json(msg)
        self.properties["response_data"] = {}
        for policy in data:
            policy_name = policy.get("policyName")
            if policy_name is None:
                msg = f"{self.class_name}.refresh: "
                msg += "Cannot parse policy information from the controller."
                self.module.fail_json(msg)
            self.properties["response_data"][policy_name] = policy

    def _get(self, item):
        if self.policy_name is None:
            msg = f"{self.class_name}._get: "
            msg += f"instance.policy_name must be set before "
            msg += f"accessing property {item}."
            self.module.fail_json(msg)
        if self.properties['response_data'].get(self.policy_name) is None:
            msg = f"{self.class_name}._get: "
            msg += f"policy_name {self.policy_name} is not defined on "
            msg += "the controller."
            self.module.fail_json(msg)
        return_item = self.make_boolean(self.properties["response_data"][self.policy_name].get(item))
        return_item = self.make_none(return_item)
        return return_item

    @property
    def description(self):
        """
        Return the policyDescr of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("policyDescr")

    @property
    def epld_image_name(self):
        """
        Return the epldImgName of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("epldImgName")

    @property
    def name(self):
        """
        Return the name of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("policyName")

    @property
    def response_data(self):
        """
        Return the parsed data from the response as a dictionary,
        keyed on policy_name.
        """
        return self.properties["response_data"]

    @property
    def response(self):
        """
        Return the raw response from the controller.
        """
        return self.properties["response"]

    @property
    def result(self):
        """
        Return the raw result.
        """
        return self.properties["result"]

    @property
    def policy_name(self):
        """
        Set the name of the policy to query.

        This must be set prior to accessing any other properties
        """
        return self.properties.get("policy_name")

    @policy_name.setter
    def policy_name(self, value):
        self.properties["policy_name"] = value

    @property
    def policy_type(self):
        """
        Return the policyType of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("policyType")

    @property
    def nxos_version(self):
        """
        Return the nxosVersion of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("nxosVersion")

    @property
    def package_name(self):
        """
        Return the packageName of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("packageName")

    @property
    def platform(self):
        """
        Return the platform of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("platform")

    @property
    def platform_policies(self):
        """
        Return the platformPolicies of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("platformPolicies")

    @property
    def ref_count(self):
        """
        Return the reference count of the policy matching self.policy_name,
        if it exists.  The reference count is the number of switches using
        this policy.
        Return None otherwise
        """
        return self._get("ref_count")

    @property
    def rpm_images(self):
        """
        Return the rpmimages of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("rpmimages")

    @property
    def image_name(self):
        """
        Return the imageName of the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("imageName")

    @property
    def agnostic(self):
        """
        Return the value of agnostic for the policy matching self.policy_name,
        if it exists.
        Return None otherwise
        """
        return self._get("agnostic")
