import inspect
import json
import logging

from .model_playbook_vrf_v12 import PlaybookVrfModelV12


class SerialNumberToVrfLite:
    """
    Given a list of validated playbook configuration models,
    build a mapping of switch serial numbers to lists of VrfLiteModel instances.

    Usage:
    ```python

    from your_module import SerialNumberToVrfLite
    serial_number_to_vrf_lite = SerialNumberToVrfLite()
    instance.playbook_models = validated_playbook_config_models
    instance.commit()
    instance.serial_number = serial_number1
    vrf_lite_list = instance.vrf_lite
    instance.serial_number = serial_number2
    vrf_lite_list = instance.vrf_lite
    # etc...
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self._fabric_inventory: dict = {}
        self._playbook_models: list[PlaybookVrfModelV12] = []
        self.serial_number_to_vrf_lite: dict = {}
        self.commit_done: bool = False

    def commit(self) -> None:
        """
        From self.validated_playbook_config_models, build a dictionary, keyed on switch serial_number,
        containing a list of VrfLiteModel.

        ## Example structure

        ```json
        {
            "XYZKSJHSMK4": [
                VrfLiteModel(
                    dot1q=21,
                    interface="Ethernet1/1",
                    ipv4_addr="10.33.0.11/30",
                    ipv6_addr="2010::10:34:0:1/64",
                    neighbor_ipv4="10.33.0.12",
                    neighbor_ipv6="2010::10:34:0:1",
                    peer_vrf="test_vrf_1"
                )
            ]
        }
        ```
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}."
        self.log.debug(msg)

        if not self.playbook_models:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Set instance.playbook_models before calling commit()."
            raise ValueError(msg)

        if not self.fabric_inventory:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Set instance.fabric_inventory before calling commit()."
            raise ValueError(msg)

        self.commit_done = True
        vrf_config_models_with_attachments = [model for model in self._playbook_models if model.attach]
        if not vrf_config_models_with_attachments:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Early return. No playbook configs containing VRF attachments found."
            self.log.debug(msg)
            return

        for model in vrf_config_models_with_attachments:
            for attachment in model.attach:
                if not attachment.vrf_lite:
                    msg = f"{self.class_name}.{method_name}: "
                    msg += f"switch {attachment.ip_address} VRF attachment does not contain vrf_lite. Skipping."
                    self.log.debug(msg)
                    continue
                ip_address = attachment.ip_address
                self.serial_number_to_vrf_lite.update({self.ipv4_address_to_serial_number(ip_address): attachment.vrf_lite})

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.serial_number_to_vrf_lite: length: {len(self.serial_number_to_vrf_lite)}."
        self.log.debug(msg)
        for serial_number, vrf_lite_list in self.serial_number_to_vrf_lite.items():
            msg = f"{self.class_name}.{method_name}: "
            msg += f"serial_number {serial_number}: -> {json.dumps([model.model_dump(by_alias=True) for model in vrf_lite_list], indent=4, sort_keys=True)}"
            self.log.debug(msg)

    def ipv4_address_to_serial_number(self, ip_address) -> str:
        """
        Given a switch ip_address, return the switch serial number.

        If ip_address is not found, return an empty string.

        ## Raises

        - ValueError: If instance.fabric_inventory is not set before calling this method.
        """
        caller = inspect.stack()[1][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}"
        self.log.debug(msg)

        data = self.fabric_inventory.get(ip_address, None)
        if not data:
            msg = f"{self.class_name}: ip_address {ip_address} not found in fabric_inventory."
            raise ValueError(msg)

        serial_number = data.get("serialNumber", None)
        if not serial_number:
            msg = f"{self.class_name}: ip_address {ip_address} does not have a serial number."
            raise ValueError(msg)
        return serial_number

    @property
    def fabric_inventory(self) -> dict:
        """
        Return the fabric inventory.
        """
        return self._fabric_inventory

    @fabric_inventory.setter
    def fabric_inventory(self, value: str):
        """
        Set the fabric_inventory.  Used to convert IP addresses to serial numbers.
        """
        if not isinstance(value, dict):
            msg = f"{self.class_name}: fabric_inventory must be a dict. "
            msg += f"Got {type(value).__name__}."
            raise TypeError(msg)
        self._fabric_inventory = value

    @property
    def playbook_models(self) -> list[PlaybookVrfModelV12]:
        """
        Return the list of playbook models (list[PlaybookVrfModelV12]).
        """
        return self._playbook_models

    @playbook_models.setter
    def playbook_models(self, value: list[PlaybookVrfModelV12]):
        if not isinstance(value, list):
            msg = f"{self.class_name}: playbook_models must be list[PlaybookVrfModelV12]. "
            msg += f"Got {type(value).__name__}."
            raise TypeError(msg)
        self._playbook_models = value

    @property
    def serial_number(self) -> str:
        """
        Return the serial number for which to retrieve VRF Lite models.
        """
        return self._serial_number

    @serial_number.setter
    def serial_number(self, value: str):
        """
        Set the serial number for which to retrieve VRF Lite models.
        """
        if not isinstance(value, str):
            msg = f"{self.class_name}: serial_number must be a string. "
            msg += f"Got {type(value).__name__}."
            raise TypeError(msg)
        self._serial_number = value

    @property
    def vrf_lite(self) -> list:
        """
        Get the list of VrfLiteModel instances for the specified serial number.
        """
        if not self.serial_number:
            msg = f"{self.class_name}: serial_number must be set before accessing vrf_lite."
            raise ValueError(msg)
        if not self.commit_done:
            self.commit()
            self.commit_done = True
        return self.serial_number_to_vrf_lite.get(self.serial_number, None)
