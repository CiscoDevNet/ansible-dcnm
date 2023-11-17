from __future__ import absolute_import, division, print_function

# disabling pylint invalid-name for Ansible standard boilerplate
__metaclass__ = type # pylint: disable=invalid-name

import inspect

from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import \
    ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send


class SwitchDetails(ImageUpgradeCommon):
    """
    Retrieve switch details from the controller and provide property accessors
    for the switch attributes.

    Usage (where module is an instance of AnsibleModule):

    instance = SwitchDetails(module)
    instance.refresh()
    instance.ip_address = 10.1.1.1
    fabric_name = instance.fabric_name
    serial_number = instance.serial_number
    etc...

    Switch details are retrieved by calling instance.refresh().

    Endpoint:
    /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/inventory/allswitches
    """

    def __init__(self, module):
        super().__init__(module)
        self.method_name = inspect.stack()[0][3]

        self.class_name = self.__class__.__name__
        self.endpoints = ApiEndpoints()
        self._init_properties()

    def _init_properties(self):
        self.method_name = inspect.stack()[0][3]

        self.properties = {}
        self.properties["ip_address"] = None
        self.properties["response_data"] = None
        self.properties["response"] = None
        self.properties["result"] = None

    def refresh(self):
        """
        Caller: __init__()

        Refresh switch_details with current switch details from
        the controller.
        """
        self.method_name = inspect.stack()[0][3]

        path = self.endpoints.switches_info.get("path")
        verb = self.endpoints.switches_info.get("verb")

        self.properties["response"] = dcnm_send(self.module, verb, path)
        self.properties["result"] = self._handle_response(self.response, verb)

        if self.response["RETURN_CODE"] != 200:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "Unable to retrieve switch information from the controller. "
            msg += f"Got response {self.response}"
            self.module.fail_json(msg)

        data = self.response.get("DATA")
        self.properties["response_data"] = {}
        for switch in data:
            self.properties["response_data"][switch["ipAddress"]] = switch

    def _get(self, item):
        self.method_name = inspect.stack()[0][3]

        if self.ip_address is None:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += "set instance.ip_address before accessing "
            msg += f"property {item}."
            self.module.fail_json(msg)

        if self.ip_address not in self.properties["response_data"]:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += f"{self.ip_address} does not exist on the controller."
            self.module.fail_json(msg)

        if item not in self.properties["response_data"][self.ip_address]:
            msg = f"{self.class_name}.{self.method_name}: "
            msg += f"{self.ip_address} does not have a key named {item}."
            self.module.fail_json(msg)

        return self.make_boolean(
            self.make_none(self.properties["response_data"][self.ip_address].get(item))
        )

    @property
    def ip_address(self):
        """
        Set the ip_address of the switch to query.

        This needs to be set before accessing this class's properties.
        """
        return self.properties.get("ip_address")

    @ip_address.setter
    def ip_address(self, value):
        self.properties["ip_address"] = value

    @property
    def fabric_name(self):
        """
        Return the fabricName of the switch with ip_address, if it exists.
        Return None otherwise
        """
        return self._get("fabricName")

    @property
    def hostname(self):
        """
        Return the hostName of the switch with ip_address, if it exists.
        Return None otherwise

        NOTES:
        1. This is None for 12.1.2e
        2. Better to use logical_name which is populated in both 12.1.2e and 12.1.3b
        """
        return self._get("hostName")

    @property
    def logical_name(self):
        """
        Return the logicalName of the switch with ip_address, if it exists.
        Return None otherwise
        """
        return self._get("logicalName")

    @property
    def model(self):
        """
        Return the model of the switch with ip_address, if it exists.
        Return None otherwise
        """
        return self._get("model")

    @property
    def response_data(self):
        """
        Return parsed data from the GET request.
        Return None otherwise

        NOTE: Keyed on ip_address
        """
        return self.properties["response_data"]

    @property
    def response(self):
        """
        Return the raw response from the GET request.
        Return None otherwise
        """
        return self.properties["response"]

    @property
    def result(self):
        """
        Return the raw result of the GET request.
        Return None otherwise
        """
        return self.properties["result"]

    @property
    def platform(self):
        """
        Return the platform of the switch with ip_address, if it exists.
        Return None otherwise

        NOTE: This is derived from "model". Is not in the controller response.
        """
        model = self._get("model")
        if model is None:
            return None
        return model.split("-")[0]

    @property
    def role(self):
        """
        Return the switchRole of the switch with ip_address, if it exists.
        Return None otherwise
        """
        return self._get("switchRole")

    @property
    def serial_number(self):
        """
        Return the serialNumber of the switch with ip_address, if it exists.
        Return None otherwise
        """
        return self._get("serialNumber")
