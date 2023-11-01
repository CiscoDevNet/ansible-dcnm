import copy
import json
from time import sleep
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import SwitchIssuDetailsBySerialNumber
from ansible_collections.cisco.dcnm.plugins.module_utils.common.controller_version import ControllerVersion

class ImageStage(ImageUpgradeCommon):
    """
    Endpoint:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-image

    Verb: POST

    Usage (where module is an instance of AnsibleModule):

    stage = ImageStage(module)
    stage.serial_numbers = ["FDO211218HH", "FDO211218GC"]
    stage.commit()
    data = stage.data

    Request body (12.1.2e) (yes, serialNum is misspelled):
        {
            "sereialNum": [
                "FDO211218HH",
                "FDO211218GC"
            ]
        }
    Request body (12.1.3b):
        {
            "serialNumbers": [
                "FDO211218HH",
                "FDO211218GC"
            ]
        }

    Response:
        Unfortunately, the response does not contain consistent data.
        Would be better if all responses contained serial numbers as keys so that
        we could verify against a set() of serial numbers.  Sigh.  It is what it is.
        {
            'RETURN_CODE': 200,
            'METHOD': 'POST',
            'REQUEST_PATH': 'https: //172.22.150.244:443/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement/stage-image',
            'MESSAGE': 'OK',
            'DATA': [
                {
                    'key': 'success',
                    'value': ''
                },
                {
                    'key': 'success',
                    'value': ''
                }
            ]
        }

        Response when there are no files to stage:
        [
            {
                "key": "FDO211218GC",
                "value": "No files to stage"
            },
            {
                "key": "FDO211218HH",
                "value": "No files to stage"
            }
        ]
    """

    def __init__(self, module):
        super().__init__(module)
        self.class_name = self.__class__.__name__
        self.endpoints = ApiEndpoints()
        self._init_properties()
        self.serial_numbers_done = set()
        self.controller_version = None
        self.path = None
        self.verb = None
        self.payload = None
        self.issu_detail = SwitchIssuDetailsBySerialNumber(self.module)

    def _init_properties(self):
        self.properties = {}
        self.properties["serial_numbers"] = None
        self.properties["response_data"] = None
        self.properties["result"] = None
        self.properties["response"] = None
        self.properties["check_interval"] = 10  # seconds
        self.properties["check_timeout"] = 1800  # seconds

    def _populate_controller_version(self):
        """
        Populate self.controller_version with the NDFC version.

        Notes:
        1.  This cannot go into ImageUpgradeCommon() due to circular
            imports resulting in RecursionError
        """
        instance = ControllerVersion(self.module)
        instance.refresh()
        self.controller_version = instance.version

    def prune_serial_numbers(self):
        """
        If the image is already staged on a switch, remove that switch's
        serial number from the list of serial numbers to stage.
        """
        serial_numbers = copy.copy(self.serial_numbers)
        for serial_number in serial_numbers:
            self.issu_detail.serial_number = serial_number
            self.issu_detail.refresh()
            if self.issu_detail.image_staged == "Success":
                msg = f"REMOVE: {self.class_name}.prune_serial_numbers: "
                msg += "image already staged for "
                msg += f"{self.issu_detail.device_name}, "
                msg += f"{self.issu_detail.ip_address}, "
                msg += f"{self.issu_detail.serial_number}."
                self.log_msg(msg)
                self.serial_numbers.remove(serial_number)

    def validate_serial_numbers(self):
        """
        Fail if the image_staged state for any serial_number
        is Failed.
        """
        for serial_number in self.serial_numbers:
            self.issu_detail.serial_number = serial_number
            self.issu_detail.refresh()
            if self.issu_detail.image_staged == "Failed":
                msg = "Image staging is failing for the following switch: "
                msg += f"{self.issu_detail.device_name}, "
                msg += f"{self.issu_detail.ip_address}, "
                msg += f"{self.issu_detail.serial_number}. "
                msg += f"Check the switch connectivity to NDFC "
                msg += "and try again."
                self.module.fail_json(msg)
            else:
                self.log_msg(f"Image staging is not failing for the following switch: {self.issu_detail.serial_number}")

    def commit(self):
        """
        Commit the image staging request to NDFC and wait
        for the images to be staged.
        """
        if self.serial_numbers is None:
            msg = f"{self.class_name}.commit() call instance.serial_numbers "
            msg += "before calling commit()."
            self.module.fail_json(msg)
        if len(self.serial_numbers) == 0:
            msg = f"REMOVE: {self.class_name}.commit() no serial numbers to stage."
            self.log_msg(msg)
            return
        self.prune_serial_numbers()
        self.validate_serial_numbers()
        self._wait_for_current_actions_to_complete()

        self.path = self.endpoints.image_stage.get("path")
        self.verb = self.endpoints.image_stage.get("verb")

        self.log_msg(f"REMOVE: {self.class_name}.commit() path: {self.path}")
        self.log_msg(f"REMOVE: {self.class_name}.commit() verb: {self.verb}")
        self.payload = {}
        self._populate_controller_version()
        if self.controller_version == "12.1.2e":
            # Yes, NDFC 12.1.2e wants serialNum to be misspelled
            self.payload["sereialNum"] = self.serial_numbers
        else:
            self.payload["serialNumbers"] = self.serial_numbers
        self.properties["response"] = dcnm_send(
            self.module, self.verb, self.path, data=json.dumps(self.payload)
        )
        self.properties["result"] = self._handle_response(self.response, self.verb)
        self.log_msg(
            f"REMOVE: {self.class_name}.commit() response: {self.response}"
        )
        self.log_msg(f"REMOVE: {self.class_name}.commit() result: {self.result}")
        if not self.result["success"]:
            msg = f"{self.class_name}.commit() failed: {self.result}. "
            msg += f"NDFC response was: {self.response}"
            self.module.fail_json(msg)
        self.properties["response_data"] = self.response.get("DATA")
        self._wait_for_image_stage_to_complete()

    def _wait_for_current_actions_to_complete(self):
        """
        NDFC will not stage an image if there are any actions in progress.
        Wait for all actions to complete before staging image.
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

    def _wait_for_image_stage_to_complete(self):
        """
        # Wait for image stage to complete
        """
        # We're promoting serial_numbers_done to a class-level attribute
        # so that it can be used in unit test asserts.
        self.serial_numbers_done = set()
        timeout = self.check_timeout
        serial_numbers_todo = set(copy.copy(self.serial_numbers))
        while self.serial_numbers_done != serial_numbers_todo and timeout > 0:
            sleep(self.check_interval)
            timeout -= self.check_interval
            msg = f"REMOVE: {self.class_name}."
            msg += "_wait_for_image_stage_to_complete: "
            msg += f"seconds remaining: {timeout}, "
            msg += f"serial_numbers_todo: {sorted(list(serial_numbers_todo))}"
            self.log_msg(msg)
            msg = f"REMOVE: {self.class_name}."
            msg += "_wait_for_image_stage_to_complete: "
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
                staged_percent = self.issu_detail.image_staged_percent
                staged_status = self.issu_detail.image_staged

                msg = f"REMOVE: {self.class_name}."
                msg += "_wait_for_image_stage_to_complete: "
                msg += f"Seconds remaining {timeout}: "
                msg += f"{device_name}, {serial_number}, {ip_address} "
                msg += f"image staged percent: {staged_percent}"
                self.log_msg(msg)

                if staged_status == "Failed":
                    msg = f"Seconds remaining {timeout}: stage image failed "
                    msg += f"for {device_name}, {serial_number}, {ip_address}. "
                    msg += f"image staged percent: {staged_percent}"
                    self.module.fail_json(msg)

                if staged_status == "Success":
                    msg = f"REMOVE: {self.class_name}."
                    msg += "_wait_for_image_stage_to_complete: "
                    msg += f"Seconds remaining {timeout}: stage image complete for "
                    msg += f"for {device_name}, {serial_number}, {ip_address}. "
                    msg += f"image staged percent: {staged_percent}"
                    self.log_msg(msg)
                    self.serial_numbers_done.add(serial_number)

                # if staged_status == None:
                #     msg = f"REMOVE: {self.class_name}."
                #     msg += "_wait_for_image_stage_to_complete: "
                #     msg += f"Seconds remaining {timeout}: stage image "
                #     msg += "not started for "
                #     msg += f"{device_name}, {serial_number}, {ip_address}. "
                #     msg += f"image staged percent: {staged_percent}"
                #     self.log_msg(msg)

                # if staged_status == "In Progress":
                #     msg = f"REMOVE: {self.class_name}."
                #     msg += "_wait_for_image_stage_to_complete: "
                #     msg += f"Seconds remaining {timeout}: stage image "
                #     msg += f"{staged_status} for "
                #     msg += f"{device_name}, {serial_number}, {ip_address}. "
                #     msg += f"image staged percent: {staged_percent}"
                #     self.log_msg(msg)
        if self.serial_numbers_done != serial_numbers_todo:
            msg = f"{self.class_name}."
            msg += "_wait_for_image_stage_to_complete: "
            msg += f"Timed out waiting for image stage to complete. "
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
        Return the stage check interval in seconds
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
        Return the stage check timeout in seconds
        """
        return self.properties.get("check_timeout")

    @check_timeout.setter
    def check_timeout(self, value):
        if not isinstance(value, int):
            msg = f"{self.__class__.__name__}: instance.check_timeout must "
            msg += f"be an integer."
            self.module.fail_json(msg)
        self.properties["check_timeout"] = value
