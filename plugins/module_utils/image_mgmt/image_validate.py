import copy
import json
from time import sleep
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import SwitchIssuDetailsBySerialNumber

class ImageValidate(ImageUpgradeCommon):
    """
    Endpoint:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/validate-image

    Verb: POST

    Usage (where module is an instance of AnsibleModule):

    instance = ImageValidate(module)
    instance.serial_numbers = ["FDO211218HH", "FDO211218GC"]
    # non_disruptive is optional
    instance.non_disruptive = True
    instance.commit()
    data = instance.response_data

    Request body:
    {
        "serialNum": ["FDO21120U5D"],
        "nonDisruptive":"true"
    }

    Response body when nonDisruptive is True:
        [StageResponse [key=success, value=]]

    Response body when nonDisruptive is False:
        [StageResponse [key=success, value=]]

    The response is not JSON, nor is it very useful.
    Instead, we poll for validation status using
    SwitchIssuDetailsBySerialNumber.
    """

    def __init__(self, module):
        super().__init__(module)
        self.class_name = self.__class__.__name__
        self.endpoints = ApiEndpoints()
        self._init_properties()
        self.issu_detail = SwitchIssuDetailsBySerialNumber(self.module)

    def _init_properties(self):
        self.properties = {}
        self.properties["check_interval"] = 10  # seconds
        self.properties["check_timeout"] = 1800  # seconds
        self.properties["response_data"] = None
        self.properties["result"] = None
        self.properties["response"] = None
        self.properties["non_disruptive"] = False
        self.properties["serial_numbers"] = None

    # def _populate_controller_version(self):
    #     """
    #     Populate self.controller_version with the NDFC version.

    #     TODO:3 Remove if 12.1.3b works with no changes to request/response payloads.

    #     Notes:
    #     1.  This cannot go into ImageUpgradeCommon() due to circular
    #         imports resulting in RecursionError
    #     """
    #     instance = ControllerVersion(self.module)
    #     instance.refresh()
    #     self.controller_version = instance.version

    def prune_serial_numbers(self):
        """
        If the image is already validated on a switch, remove that switch's
        serial number from the list of serial numbers to validate.
        """
        serial_numbers = copy.copy(self.serial_numbers)
        for serial_number in serial_numbers:
            self.issu_detail.serial_number = serial_number
            self.issu_detail.refresh()
            if self.issu_detail.validated == "Success":
                msg = f"REMOVE: {self.class_name}.prune_serial_numbers: "
                msg += "image already validated for "
                msg += f"{self.issu_detail.serial_number}, "
                msg += f"{self.issu_detail.ip_address}"
                self.log_msg(msg)
                self.serial_numbers.remove(self.issu_detail.serial_number)

    def validate_serial_numbers(self):
        """
        Log a warning if the validated state for any serial_number
        is Failed.

        TODO:1 Need a way to compare current image_policy with the image policy in the response
        TODO:3 If validate == Failed, it may have been from the last operation.
        TODO:3 We can't fail here based on this until we can verify the failure is happening for the current image_policy.
        TODO:3 Change this to a log message and update the unit test if we can't verify the failure is happening for the current image_policy.
        """
        for serial_number in self.serial_numbers:
            self.issu_detail.serial_number = serial_number
            self.issu_detail.refresh()
            if self.issu_detail.validated == "Failed":
                msg = f"{self.class_name}.validate_serial_numbers: "
                msg += "image validation is failing for the following switch: "
                msg += f"{self.issu_detail.device_name}, "
                msg += f"{self.issu_detail.ip_address}, "
                msg += f"{self.issu_detail.serial_number}. "
                msg += "If this persists, check the switch connectivity to NDFC and "
                msg += "try again."
                #self.log_msg(msg)
                self.module.fail_json(msg)

    def build_payload(self):
        self.payload = {}
        self.payload["serialNum"] = self.serial_numbers
        self.payload["nonDisruptive"] = self.non_disruptive

    def commit(self):
        """
        Commit the image validation request to NDFC and wait
        for the images to be validated.
        """
        if self.serial_numbers is None:
            msg = f"{self.class_name}.commit() call instance.serial_numbers "
            msg += "before calling commit()."
            self.module.fail_json(msg)
        if len(self.serial_numbers) == 0:
            msg = f"REMOVE: {self.class_name}.commit() no serial numbers "
            msg += "to validate."
            self.log_msg(msg)
            return
        self.prune_serial_numbers()
        self.validate_serial_numbers()
        self._wait_for_current_actions_to_complete()
        path = self.endpoints.image_validate.get("path")
        verb = self.endpoints.image_validate.get("verb")
        self.build_payload()
        self.properties["response"] = dcnm_send(
            self.module, verb, path, data=json.dumps(self.payload)
        )
        self.properties["result"] = self._handle_response(self.response, verb)
        self.log_msg(
            f"REMOVE: {self.class_name}.commit() response: {self.response}"
        )
        self.log_msg(f"REMOVE: {self.class_name}.commit() result: {self.result}")
        if not self.result["success"]:
            msg = f"{self.class_name}.commit() failed: {self.result}. "
            msg += f"NDFC response was: {self.response}"
            self.module.fail_json(msg)
        self.properties["response_data"] = self.response.get("DATA")
        self._wait_for_image_validate_to_complete()

    def _wait_for_current_actions_to_complete(self):
        """
        NDFC will not validate an image if there are any actions in progress.
        Wait for all actions to complete before validating image.
        Actions include image staging, image upgrade, and image validation.
        """
        self.serial_numbers_done = set()
        serial_numbers_todo = set(copy.copy(self.serial_numbers))
        timeout = self.check_timeout
        while self.serial_numbers_done != serial_numbers_todo and timeout > 0:
            sleep(self.check_interval)
            timeout -= self.check_interval
            for serial_number in self.serial_numbers:
                if serial_number in self.serial_numbers_done:
                    continue
                self.issu_detail.serial_number = serial_number
                self.issu_detail.refresh()
                msg = f"REMOVE: {self.class_name}."
                msg += "_wait_for_current_actions_to_complete: "
                msg += f"{serial_number} actions in progress: "
                msg += f"{self.issu_detail.actions_in_progress}, "
                msg += f"{timeout} seconds remaining."
                self.log_msg(msg)
                if self.issu_detail.actions_in_progress is False:
                    msg = f"REMOVE: {self.class_name}."
                    msg += "_wait_for_current_actions_to_complete: "
                    msg += f"{serial_number} no actions in progress. "
                    msg += f"OK to proceed. {timeout} seconds remaining."
                    self.log_msg(msg)
                    self.serial_numbers_done.add(serial_number)
        if self.serial_numbers_done != serial_numbers_todo:
            msg = f"{self.class_name}."
            msg += "_wait_for_current_actions_to_complete: "
            msg += f"Timed out waiting for actions to complete. "
            msg += f"serial_numbers_done: "
            msg += f"{','.join(sorted(self.serial_numbers_done))}, "
            msg += f"serial_numbers_todo: "
            msg += f"{','.join(sorted(serial_numbers_todo))}"
            self.log_msg(msg)
            self.module.fail_json(msg)

    def _wait_for_image_validate_to_complete(self):
        """
        Wait for image validation to complete
        """
        # We're promiting serial_numbers_done to a class-level attribute
        # so that it can be used in unit test asserts.
        self.serial_numbers_done = set()
        timeout = self.check_timeout
        serial_numbers_todo = set(copy.copy(self.serial_numbers))
        while self.serial_numbers_done != serial_numbers_todo and timeout > 0:
            sleep(self.check_interval)
            timeout -= self.check_interval
            msg = f"REMOVE: {self.class_name}."
            msg += "_wait_for_image_validate_to_complete: "
            msg += f"seconds remaining: {timeout}, "
            msg += f"serial_numbers_todo: {sorted(list(serial_numbers_todo))}"
            self.log_msg(msg)
            msg = f"REMOVE: {self.class_name}."
            msg += "_wait_for_image_validate_to_complete: "
            msg += f"seconds remaining: {timeout}, "
            msg += f"serial_numbers_done: {sorted(list(self.serial_numbers_done))}"
            self.log_msg(msg)
            for serial_number in self.serial_numbers:
                if serial_number in self.serial_numbers_done:
                    continue
                self.issu_detail.serial_number = serial_number
                self.issu_detail.refresh()
                ip_address = self.issu_detail.ip_address
                device_name = self.issu_detail.device_name
                validated_percent = self.issu_detail.validated_percent
                validated_status = self.issu_detail.validated

                msg = f"REMOVE: {self.class_name}."
                msg += "_wait_for_image_validate_to_complete: "
                msg += f"Seconds remaining {timeout}: "
                msg += f"{device_name}, {ip_address}, {serial_number}, "
                msg += f"validated_percent: {validated_percent} "
                msg += f"validated_state: {validated_status}"
                self.log_msg(msg)

                if validated_status == "Failed":
                    msg = f"Seconds remaining {timeout}: validate image "
                    msg += f"{validated_status} for "
                    msg += f"{device_name}, {ip_address}, {serial_number}, "
                    msg += f"image validated percent: {validated_percent}. "
                    msg += "Check the switch e.g. show install log detail, "
                    msg += "show incompatibility-all nxos <image>.  Or "
                    msg += "check NDFC Operations > Image Management > "
                    msg += "Devices > View Details > Validate for "
                    msg += "more details."
                    self.module.fail_json(msg)

                if validated_status == "Success":
                    msg = f"REMOVE: {self.class_name}."
                    msg += "_wait_for_image_validate_to_complete: "
                    msg += f"Seconds remaining {timeout}: validate image "
                    msg += f"{validated_status} for "
                    msg += f"{device_name}, {ip_address}, {serial_number}, "
                    msg += f"image validated percent: {validated_percent}"
                    self.log_msg(msg)
                    self.serial_numbers_done.add(serial_number)

                if validated_status == None:
                    msg = f"REMOVE: {self.class_name}."
                    msg += "_wait_for_image_validate_to_complete: "
                    msg += f"Seconds remaining {timeout}: validate image "
                    msg += "not started for "
                    msg += f"{device_name}, {ip_address}, {serial_number}, "
                    msg += f"image validated percent: {validated_percent}"
                    self.log_msg(msg)

                if validated_status == "In Progress":
                    msg = f"REMOVE: {self.class_name}."
                    msg += "_wait_for_image_validate_to_complete: "
                    msg += f"Seconds remaining {timeout}: validate image "
                    msg += f"{validated_status} for "
                    msg += f"{device_name}, {ip_address}, {serial_number}, "
                    msg += f"image validated percent: {validated_percent}"
                    self.log_msg(msg)
        if self.serial_numbers_done != serial_numbers_todo:
            msg = f"{self.class_name}."
            msg += "_wait_for_image_validate_to_complete: "
            msg += f"Timed out waiting for image validation to complete. "
            msg += f"serial_numbers_done: "
            msg += f"{','.join(sorted(self.serial_numbers_done))}, "
            msg += f"serial_numbers_todo: "
            msg += f"{','.join(sorted(serial_numbers_todo))}"
            self.log_msg(msg)
            self.module.fail_json(msg)

    @property
    def serial_numbers(self):
        """
        Set the serial numbers of the switches to stage.

        This must be set before calling instance.commit()
        """
        return self.properties.get("serial_numbers")

    @serial_numbers.setter
    def serial_numbers(self, value):
        if not isinstance(value, list):
            msg = f"{self.__class__.__name__}: instance.serial_numbers must "
            msg += f"be a python list of switch serial numbers."
            self.module.fail_json(msg)
        self.properties["serial_numbers"] = value

    @property
    def non_disruptive(self):
        """
        Set the non_disruptive flag to True or False.
        """
        return self.properties.get("non_disruptive")

    @non_disruptive.setter
    def non_disruptive(self, value):
        value = self.make_boolean(value)
        if not isinstance(value, bool):
            msg = f"{self.class_name}.non_disruptive: "
            msg += "instance.non_disruptive must "
            msg += f"be a boolean. Got {value}."
            self.module.fail_json(msg)
        self.properties["non_disruptive"] = value

    @property
    def response_data(self):
        """
        Return the result of the image staging request
        for serial_numbers.

        instance.serial_numbers must be set first.
        """
        return self.properties.get("response_data")

    @property
    def result(self):
        """
        Return the POST result from NDFC
        """
        return self.properties.get("result")

    @property
    def response(self):
        """
        Return the POST response from NDFC
        """
        return self.properties.get("response")

    @property
    def check_interval(self):
        """
        Return the validate check interval in seconds
        """
        return self.properties.get("check_interval")

    @check_interval.setter
    def check_interval(self, value):
        if not isinstance(value, int):
            msg = f"{self.__class__.__name__}: instance.check_interval must "
            msg += f"be an integer."
            self.module.fail_json(msg)
        self.properties["check_interval"] = value

    @property
    def check_timeout(self):
        """
        Return the validate check timeout in seconds
        """
        return self.properties.get("check_timeout")

    @check_timeout.setter
    def check_timeout(self, value):
        if not isinstance(value, int):
            msg = f"{self.__class__.__name__}: instance.check_timeout must "
            msg += f"be an integer."
            self.module.fail_json(msg)
        self.properties["check_timeout"] = value

