import inspect
import logging


class InventoryIpv4ToSwitchRole:
    """
    Given a fabric_inventory, convert a switch ipv4_address to switch's role (switchRole).

    ## Usage

    ```python
    from plugins.module_utils.vrf.inventory_ipv4_to_serial_number import InventoryIpv4ToSwitchRole
    fabric_inventory = {
        "10.1.1.1": {
            "switchRole": "leaf",
            # other switch details...
        },
    }

    instance = InventoryIpv4ToSwitchRole()
    instance.fabric_inventory = fabric_inventory
    try:
        switch_role_1 = instance.convert("10.1.1.1")
        switch_role_2 = instance.convert("10.1.1.2")
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

    def convert(self, ipv4_address: str) -> str:
        """
        # Summary

        Given a switch ipv4_address, return the switch_role, e.g. leaf, spine.

        # Raises

        - ValueError if:
          - instance.fabric_inventory is not set before calling this method.
          - ipv4_address is not found in fabric_inventory.
        """
        caller = inspect.stack()[1][3]
        method_name = inspect.stack()[0][3]

        msg = "ENTERED. "
        msg += f"caller: {caller}"
        self.log.debug(msg)

        self._validate_fabric_inventory()
        data = self.fabric_inventory.get(ipv4_address, None)
        if not data:
            msg = f"{self.class_name}.{method_name}: caller {caller}. "
            msg += f"ipv4_address {ipv4_address} not found in fabric_inventory."
            raise ValueError(msg)

        switch_role = data.get("switchRole", None)
        if not switch_role:
            msg = f"{self.class_name}.{method_name}: caller {caller}. "
            msg += f"ipv4_address {ipv4_address} is missing switch_role (switchRole) in fabric_inventory."
            raise ValueError(msg)
        return switch_role

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
