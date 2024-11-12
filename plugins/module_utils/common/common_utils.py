from __future__ import absolute_import, division, print_function

import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    get_fabric_inventory_details,
    dcnm_version_supported,
    get_ip_sn_dict,
)

__metaclass__ = type
__author__ = "Mallik Mudigonda"


class Version:
    def __init__(self):
        self.class_name = self.__class__.__name__
        self._module = None

    @property
    def module(self):
        return self._module

    @module.setter
    def module(self, value):
        self._module = value

    def commit(self):

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        if self._module is None:
            msg = f"{0}.commit(): ".format(self.class_name)
            msg += "module is not set, which is required."
            raise ValueError(msg)

        self.dcnm_version = dcnm_version_supported(self._module)
        self.log.debug(f"Version = {0}\n".format(self.dcnm_version))


class InventoryData:
    def __init__(self):

        self.class_name = self.__class__.__name__
        self.inventory_data = None
        self._module = None
        self._fabric = None

    @property
    def module(self):
        return self._module

    @module.setter
    def module(self, value):
        self._module = value

    @property
    def fabric(self):
        return self._fabric

    @fabric.setter
    def fabric(self, value):
        self._fabric = value

    def commit(self):

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        if self._module is None:
            msg = f"{0}.commit(): ".format(self.class_name)
            msg += "module is not set, which is required."
            raise ValueError(msg)

        if self._fabric is None:
            msg = f"{0}.commit(): ".format(self.class_name)
            msg += "fabric is not set, which is required."
            raise ValueError(msg)

        self.inventory_data = get_fabric_inventory_details(
            self._module, self._fabric
        )

        inv_data = [
            {
                "IP": d["ipAddress"],
                "Sno": d["serialNumber"],
                "Logical Name": d["logicalName"],
                "Managable": d["managable"],
                "Role": d["switchRoleEnum"],
            }
            for d in self.inventory_data.values()
        ]
        self.log.debug(f"Inventory Data = {0}\n".format(inv_data))


class FabricInfo:
    def __init__(self):
        self.class_name = self.__class__.__name__
        self.monitoring = []
        self._module = None
        self._fabric = None
        self._rest_send = None
        self._paths = None

    @property
    def module(self):
        return self._module

    @module.setter
    def module(self, value):
        self._module = value

    @property
    def fabric(self):
        return self._fabric

    @fabric.setter
    def fabric(self, value):
        self._fabric = value

    @property
    def paths(self):
        return self._paths

    @paths.setter
    def paths(self, value):
        self._paths = value

    @property
    def rest_send(self):
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value):
        self._rest_send = value

    def commit(self):

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        if self._module is None:
            msg = f"{0}.commit(): ".format(self.class_name)
            msg += "module is not set, which is required."
            raise ValueError(msg)

        if self._fabric is None:
            msg = f"{0}.commit(): ".format(self.class_name)
            msg += "fabric is not set, which is required."
            raise ValueError(msg)

        if self._rest_send is None:
            msg = f"{0}.commit(): ".format(self.class_name)
            msg += "rest_send is not set, which is required."
            raise ValueError(msg)

        if self._paths is None:
            msg = f"{0}.commit(): ".format(self.class_name)
            msg += "paths is not set, which is required."
            raise ValueError(msg)

        processed_fabrics = []
        processed_fabrics.append(self._fabric)

        # Get all fabrics which are in monitoring mode. Deploy must be avoided to all fabrics which are part of this list
        for fabric in processed_fabrics:

            path = self._paths["FABRIC_ACCESS_MODE"].format(fabric)

            self._rest_send.path = path
            self._rest_send.verb = "GET"
            self._rest_send.payload = None
            self._rest_send.commit()

            resp = self._rest_send.response[0]

            self.log.debug(f"RST: Fabric Access Mode Resp = {0}\n".format(resp))

            if resp and resp["RETURN_CODE"] == 200:
                if str(resp["DATA"]["readonly"]).lower() == "true":
                    self.monitoring.append(fabric)

        # Check if source fabric is in monitoring mode. If so return an error, since fabrics in monitoring mode do not allow
        # create/modify/delete and deploy operations.
        if self._fabric in self.monitoring:
            self._module.fail_json(
                msg="Error: Source Fabric '{0}' is in Monitoring mode, No changes are allowed on the fabric\n".format(
                    self._fabric
                )
            )


class SwitchInfo:
    def __init__(self):
        self.class_name = self.__class__.__name__
        self._inventory_data = None

    @property
    def inventory_data(self):
        return self._inventory_data

    @inventory_data.setter
    def inventory_data(self, value):
        self._inventory_data = value

    def commit(self):

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        if self._inventory_data is None:
            msg = f"{0}.commit(): ".format(self.class_name)
            msg += "inventory data is not set, which is required."
            raise ValueError(msg)

        self.dcnm_update_switch_mapping_info()
        self.dcnm_update_switch_managability_info()

    def dcnm_update_switch_mapping_info(self):

        # Based on the updated inventory_data, update ip_sn, hn_sn and sn_hn objects
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)
        self.sn_hn = dict([(value, key) for key, value in self.hn_sn.items()])
        self.sn_ip = dict([(value, key) for key, value in self.ip_sn.items()])

        self.log.debug(f"IP_SN = {0}\n".format(self.ip_sn))
        self.log.debug(f"SN_HN = {0}\n".format(self.sn_hn))
        self.log.debug(f"SN_IP = {0}\n".format(self.sn_ip))

    def dcnm_update_switch_managability_info(self):

        # Get all switches which are managable. Deploy must be avoided to all switches which are not part of this list
        managable_ip = [
            (key, self.inventory_data[key]["serialNumber"])
            for key in self.inventory_data
            if str(self.inventory_data[key]["managable"]).lower() == "true"
        ]
        managable_hosts = [
            (
                self.inventory_data[key]["logicalName"],
                self.inventory_data[key]["serialNumber"],
            )
            for key in self.inventory_data
            if str(self.inventory_data[key]["managable"]).lower() == "true"
        ]
        self.managable = dict(managable_ip + managable_hosts)

        self.meta_switches = [
            (
                key,
                self.inventory_data[key]["logicalName"],
                self.inventory_data[key]["serialNumber"],
            )
            for key in self.inventory_data
            if self.inventory_data[key]["switchRoleEnum"] is None
        ]

        self.log.debug(f"Meta Switches = {0}\n".format(self.meta_switches))
        self.log.debug(f"Managable Switches = {0}\n".format(self.managable))
