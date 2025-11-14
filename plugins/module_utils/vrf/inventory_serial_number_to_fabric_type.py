import inspect
import logging


class InventorySerialNumberToFabricType:
    """
    Given a fabric_inventory, convert a switch serial_number to the hosting fabric's fabricTechnology (fabric type).

    ## Usage

    ```python
    from plugins.module_utils.vrf.inventory_ipv4_to_serial_number import InventorySerialNumberToFabricType
    fabric_inventory = {
        "10.1.1.1": {
            "serialNumber": "ABC123456",
            "fabricTechnology": "VXLANFabric",
            # other switch details...
        },
    }

    instance = InventorySerialNumberToFabricType()
    instance.fabric_inventory = fabric_inventory
    try:
        fabric_type_1 = instance.convert("ABC123456")
        fabric_type_2 = instance.convert("CDE123456")
        # etc...
    except ValueError as error:
        print(f"Error: {error}")
    ```
    """

    def __init__(self):
        """
        # Summary

        - Set class_name
        - Initialize the logger
        - Initialize class attributes

        # Raises

        - None
        """
        self.class_name = self.__class__.__name__
        self._setup_logger()
        self.fabric_inventory: dict = {}

    def _setup_logger(self) -> None:
        """Initialize the logger."""
        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

    def _validate_fabric_inventory(self) -> None:
        """
        # Summary

        Validate that fabric_inventory is set and not empty.

        # Raises

        - ValueError: If fabric_inventory is not set or is empty.
        """
        if not self.fabric_inventory:
            msg = f"{self.class_name}: fabric_inventory is not set or is empty."
            raise ValueError(msg)

    def convert(self, serial_number: str) -> str:
        """
        # Summary

        Given a switch serial_number, return the fabric_type of the
        fabric in which the switch resides.

        # Raises

        - ValueError if:
          - instance.fabric_inventory is not set before calling this method.
          - serial_number is not found in fabric_inventory.
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}"
        self.log.debug(msg)

        self._validate_fabric_inventory()
        for data in self.fabric_inventory.values():
            if data.get("serialNumber") != serial_number:
                continue
            fabric_type = data.get("fabricTechnology")

        if not fabric_type:
            msg = f"{self.class_name}.{method_name}: caller {caller}. "
            msg += f"serial_number {serial_number} not found, or has no associated fabric_type."
            raise ValueError(msg)
        return fabric_type

    @property
    def fabric_inventory(self) -> dict:
        """
        Return the fabric_inventory, which maps ipv4_address to switch_data.
        """
        return self._fabric_inventory

    @fabric_inventory.setter
    def fabric_inventory(self, value: dict):
        """
        Set the fabric_inventory, which maps ipv4_address to switch_data.
        """
        self._fabric_inventory = value
