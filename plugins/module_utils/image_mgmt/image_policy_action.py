import json
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import ImagePolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import SwitchIssuDetailsBySerialNumber


class ImagePolicyAction(ImageUpgradeCommon):
    """
    Perform image policy actions on the controller for one or more switches.

    Support for the following actions:
        - attach
        - detach
        - query

    Usage (where module is an instance of AnsibleModule):

    instance = ImagePolicyAction(module)
    instance.policy_name = "NR3F"
    instance.action = "attach" # or detach, or query
    instance.serial_numbers = ["FDO211218GC", "FDO211218HH"]
    instance.commit()
    # for query only
    query_result = instance.query_result

    Endpoints:
    For action == attach:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/attach-policy
    For action == detach:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/detach-policy
    For action == query:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/image-policy/__POLICY_NAME__
    """

    def __init__(self, module):
        super().__init__(module)
        self.class_name = self.__class__.__name__
        self.endpoints = ApiEndpoints()
        self._init_properties()
        self.image_policies = ImagePolicies(self.module)
        self.switch_issu_details = SwitchIssuDetailsBySerialNumber(self.module)
        self.valid_actions = {"attach", "detach", "query"}

    def _init_properties(self):
        self.properties = {}
        self.properties["action"] = None
        self.properties["response"] = None
        self.properties["result"] = None
        self.properties["policy_name"] = None
        self.properties["query_result"] = None
        self.properties["serial_numbers"] = None

    def build_attach_payload(self):
        """
        build the payload to send in the POST request
        to attach policies to devices

        caller _attach_policy()
        """
        self.payloads = []
        # TODO:2 Need a way to call refresh() in __init__ with unit-tests being able to mock it
        self.switch_issu_details.refresh()
        for serial_number in self.serial_numbers:
            self.switch_issu_details.serial_number = serial_number
            payload = {}
            payload["policyName"] = self.policy_name
            payload["hostName"] = self.switch_issu_details.device_name
            payload["ipAddr"] = self.switch_issu_details.ip_address
            payload["platform"] = self.switch_issu_details.platform
            payload["serialNumber"] = self.switch_issu_details.serial_number
            for item in payload:
                if payload[item] is None:
                    msg = f"Unable to determine {item} for switch "
                    msg += f"{self.switch_issu_details.ip_address}, "
                    msg += f"{self.switch_issu_details.serial_number}, "
                    msg += f"{self.switch_issu_details.device_name}. "
                    msg += "Please verify that the switch is managed by "
                    msg += "the controller."
                    self.module.fail_json(msg)
            self.payloads.append(payload)

    def validate_request(self):
        """
        validations prior to commit() should be added here.
        """
        self.log_msg(f"REMOVE: {self.class_name}.validate_request: Entered")
        if self.action is None:
            msg = f"{self.class_name}.validate_request: "
            msg += "instance.action must be set before "
            msg += "calling commit()"
            self.module.fail_json(msg)

        if self.policy_name is None:
            msg = f"{self.class_name}.validate_request: "
            msg += "instance.policy_name must be set before "
            msg += "calling commit()"
            self.module.fail_json(msg)

        self.log_msg(f"REMOVE: {self.class_name}.validate_request: action {self.action}")

        if self.action == "query":
            return

        self.log_msg(f"REMOVE: {self.class_name}.validate_request: serial_numbers {self.serial_numbers}")

        if self.serial_numbers is None:
            msg = f"{self.class_name}.validate_request: "
            msg += "instance.serial_numbers must be set before "
            msg += "calling commit()"
            self.module.fail_json(msg)


        # TODO:2 Need a way to call refresh() in __init__ with unit-tests being able to mock it
        self.image_policies.refresh()
        self.switch_issu_details.refresh()
        # Fail if the image policy does not support the switch platform
        self.image_policies.policy_name = self.policy_name
        for serial_number in self.serial_numbers:
            self.switch_issu_details.serial_number = serial_number
            if self.switch_issu_details.platform not in self.image_policies.platform:
                msg = f"policy {self.policy_name} does not support platform "
                msg += f"{self.switch_issu_details.platform}. {self.policy_name} "
                msg += "supports the following platform(s): "
                msg += f"{self.image_policies.platform}"
                self.module.fail_json(msg)

    def commit(self):
        self.validate_request()
        if self.action == "attach":
            self._attach_policy()
        elif self.action == "detach":
            self._detach_policy()
        elif self.action == "query":
            self._query_policy()
        else:
            msg = f"{self.class_name}.commit: "
            msg += f"Unknown action {self.action}."
            self.module.fail_json(msg)

    def _attach_policy(self):
        """
        Attach policy_name to the switch(es) associated with serial_numbers

        NOTES:
        1. This method creates a list of responses and results which
        are accessible via properties response and result,
        respectively.
        """
        self.build_attach_payload()
        path = self.endpoints.policy_attach.get("path")
        verb = self.endpoints.policy_attach.get("verb")
        responses = []
        results = []
        for payload in self.payloads:
            response = dcnm_send(self.module, verb, path, data=json.dumps(payload))
            result = self._handle_response(response, verb)
            if not result["success"]:
                msg = f"{self.class_name}._attach_policy: "
                msg += f"Bad result when attaching policy {self.policy_name} "
                msg += f"to switch {payload['ipAddr']}."
                self.module.fail_json(msg)
            responses.append(response)
            results.append(result)
        self.properties["response"] = responses
        self.properties["result"] = results

    def _detach_policy(self):
        """
        Detach policy_name from the switch(es) associated with serial_numbers
        verb: DELETE
        endpoint: /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/detach-policy
        query_params: ?serialNumber=FDO211218GC,FDO21120U5D
        """
        path = self.endpoints.policy_detach.get("path")
        verb = self.endpoints.policy_detach.get("verb")
        query_params = ",".join(self.serial_numbers)
        path += f"?serialNumber={query_params}"
        response = dcnm_send(self.module, verb, path)
        result = self._handle_response(response, verb)
        if not result["success"]:
            self._failure(response)
        self.properties["response"] = response
        self.properties["result"] = result

    def _query_policy(self):
        """
        Query the image policy
        verb: GET
        endpoint: /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/image-policy/__POLICY_NAME__
        """
        path = self.endpoints.policy_info.get("path")
        verb = self.endpoints.policy_info.get("verb")
        path = path.replace("__POLICY_NAME__", self.policy_name)
        response = dcnm_send(self.module, verb, path)
        result = self._handle_response(response, verb)
        if not result["success"]:
            self._failure(response)
        self.properties["query_result"] = response.get("DATA")
        self.properties["response"] = response
        self.properties["result"] = result

    @property
    def query_result(self):
        """
        Return the value of properties["query_result"].
        """
        return self.properties.get("query_result")

    @property
    def action(self):
        """
        Set the action to take. Either "attach" or "detach".

        Must be set prior to calling instance.commit()
        """
        return self.properties.get("action")

    @action.setter
    def action(self, value):
        if value not in self.valid_actions:
            msg = f"{self.class_name}: instance.action must be "
            msg += f"one of {','.join(sorted(self.valid_actions))}"
            self.module.fail_json(msg)
        self.properties["action"] = value

    @property
    def response(self):
        """
        Return the raw response from the controller.

        Assumes that commit() has been called.

        In the case of attach, this is a list of responses.
        """
        return self.properties.get("response")

    @property
    def result(self):
        """
        Return the raw result.

        Assumes that commit() has been called.

        In the case of attach, this is a list of results.
        """
        return self.properties.get("result")

    @property
    def policy_name(self):
        """
        Set the name of the policy to attach, detach, query.

        Must be set prior to calling instance.commit()
        """
        return self.properties.get("policy_name")

    @policy_name.setter
    def policy_name(self, value):
        self.properties["policy_name"] = value

    @property
    def serial_numbers(self):
        """
        Set the serial numbers of the switches to/from which
        policy_name will be attached or detached.

        Must be set prior to calling instance.commit()
        """
        return self.properties.get("serial_numbers")

    @serial_numbers.setter
    def serial_numbers(self, value):
        if not isinstance(value, list):
            msg = f"{self.class_name}: instance.serial_numbers must "
            msg += f"be a python list of switch serial numbers."
            self.module.fail_json(msg)
        self.properties["serial_numbers"] = value

