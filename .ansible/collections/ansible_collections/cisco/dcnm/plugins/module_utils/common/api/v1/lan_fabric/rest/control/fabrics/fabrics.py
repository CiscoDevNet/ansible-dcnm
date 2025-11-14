# Copyright (c) 2024 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pylint: disable=line-too-long
from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

import inspect
import logging

from ..control import Control
from ........fabric.fabric_types import \
    FabricTypes


class Fabrics(Control):
    """
    ## api.v1.lan-fabric.rest.control.fabrics.Fabrics()

    ### Description
    Common methods and properties for Fabrics() subclasses.

    ### Path
    -   ``/api/v1/lan-fabric/rest/control/fabrics``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.fabric_types = FabricTypes()
        self.fabrics = f"{self.control}/fabrics"
        msg = f"ENTERED api.v1.lan_fabric.rest.control.fabrics.{self.class_name}"
        self.log.debug(msg)
        self._build_properties()

    def _build_properties(self):
        """
        - Set the fabric_name property.
        """
        self.properties["fabric_name"] = None
        self.properties["serial_number"] = None
        self.properties["template_name"] = None
        self.properties["ticket_id"] = None

    @property
    def fabric_name(self):
        """
        - getter: Return the fabric_name.
        - setter: Set the fabric_name.
        - setter: Raise ``ValueError`` if fabric_name is not valid.
        """
        return self.properties["fabric_name"]

    @fabric_name.setter
    def fabric_name(self, value):
        method_name = inspect.stack()[0][3]
        try:
            self.conversion.validate_fabric_name(value)
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{error}"
            raise ValueError(msg) from error
        self.properties["fabric_name"] = value

    @property
    def path_fabric_name(self):
        """
        -   Endpoint path property, including fabric_name.
        -   Raise ``ValueError`` if fabric_name is not set and
            ``self.required_properties`` contains "fabric_name".
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_name is None and "fabric_name" in self.required_properties:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_name must be set prior to accessing path."
            raise ValueError(msg)
        return f"{self.fabrics}/{self.fabric_name}"

    @property
    def path_fabric_name_serial_number(self):
        """
        -   Endpoint path property, including fabric_name and
            switch serial_number.
        -   Raise ``ValueError`` if fabric_name is not set.
        -   Raise ``ValueError`` if serial_number is not set.
        -   /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabricName}/switches/{serialNumber}
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_name must be set prior to accessing path."
            raise ValueError(msg)
        if self.serial_number is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "serial_number must be set prior to accessing path."
            raise ValueError(msg)
        return f"{self.fabrics}/{self.fabric_name}/switches/{self.serial_number}"

    @property
    def path_fabric_name_template_name(self):
        """
        -   Endpoint path property, including fabric_name and template_name.
        -   Raise ``ValueError`` if fabric_name is not set and
            ``self.required_properties`` contains "fabric_name".
        -   Raise ``ValueError`` if template_name is not set and
            ``self.required_properties`` contains "template_name".
        """
        method_name = inspect.stack()[0][3]
        if self.fabric_name is None and "fabric_name" in self.required_properties:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_name must be set prior to accessing path."
            raise ValueError(msg)
        if self.template_name is None and "template_name" in self.required_properties:
            msg = f"{self.class_name}.{method_name}: "
            msg += "template_name must be set prior to accessing path."
            raise ValueError(msg)
        return f"{self.fabrics}/{self.fabric_name}/{self.template_name}"

    @property
    def serial_number(self):
        """
        - getter: Return the switch serial_number.
        - setter: Set the switch serial_number.
        - setter: Raise ``TypeError`` if serial_number is not a string.
        - Default: None
        """
        return self.properties["serial_number"]

    @serial_number.setter
    def serial_number(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Expected string for {method_name}. "
            msg += f"Got {value} with type {type(value).__name__}."
            raise TypeError(msg)
        self.properties["serial_number"] = value

    @property
    def template_name(self):
        """
        - getter: Return the template_name.
        - setter: Set the template_name.
        - setter: Raise ``ValueError`` if template_name is not a string.
        """
        return self.properties["template_name"]

    @template_name.setter
    def template_name(self, value):
        method_name = inspect.stack()[0][3]
        if value not in self.fabric_types.valid_fabric_template_names:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid template_name: {value}. "
            msg += "Expected one of: "
            msg += f"{', '.join(self.fabric_types.valid_fabric_template_names)}."
            raise ValueError(msg)
        self.properties["template_name"] = value

    @property
    def ticket_id(self):
        """
        - getter: Return the ticket_id.
        - setter: Set the ticket_id.
        - setter: Raise ``ValueError`` if ticket_id is not a string.
        - Default: None
        - Note: ticket_id is optional unless Change Control is enabled.
        """
        return self.properties["ticket_id"]

    @ticket_id.setter
    def ticket_id(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Expected string for {method_name}. "
            msg += f"Got {value} with type {type(value).__name__}."
            raise ValueError(msg)
        self.properties["ticket_id"] = value


class EpFabricConfigDeploy(Fabrics):
    """
    ## api.v1.lan-fabric.rest.control.fabrics.EpFabricConfigDeploy()

    ### Description
    Return endpoint to initiate config-deploy on fabric_name
    or fabric_name + switch_id.

     ### Raises
    -   ``ValueError``: If fabric_name is not set.
    -   ``ValueError``: If fabric_name is invalid.
    -   ``ValueError``: If force_show_run is not boolean.
    -   ``ValueError``: If include_all_msd_switches is not boolean.

    ### Path
    -   ``/fabrics/{fabric_name}/config-deploy``
    -   ``/fabrics/{fabric_name}/config-deploy?forceShowRun={force_show_run}``
    -   ``/fabrics/{fabric_name}/config-deploy?inclAllMSDSwitches={include_all_msd_switches}``
    -   ``/fabrics/{fabric_name}/config-deploy/{switch_id}``
    -   ``/fabrics/{fabric_name}/config-deploy/{switch_id}/?forceShowRun={force_show_run}``

    ### Verb
    -   POST

    ### Parameters
    -   fabric_name:
            -   set the ``fabric_name`` to be used in the path
            -   string
            -   required
    -   force_show_run:
            -   set the ``forceShowRun`` value
            -   boolean
            -   default: False
            -   optional
    -   include_all_msd_switches:
            -   set the ``inclAllMSDSwitches`` value
            -   boolean
            -   default: False
            -   optional
    -   path:
            -   retrieve the path for the endpoint
            -   string
    -   switch_id:
            -   set the ``switch_id`` to be used in the path
            -   string or list
            -   optional
            -   if set, ``include_all_msd_switches`` is not added to the path
    -   verb:
            -   retrieve the verb for the endpoint
            -   string (e.g. GET, POST, PUT, DELETE)

    ### Usage
    ```python
    instance = EpFabricConfigDeploy()
    instance.fabric_name = "MyFabric"
    instance.switch_id = ["CHM1234567", "CHM7654321"]
    # or instance.switch_id = "CHM1234567"
    # or instance.switch_id = "CHM7654321,CHM1234567"
    instance.force_show_run = True
    instance.include_all_msd_switches = True
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self._build_properties()
        msg = "ENTERED api.v1.lan_fabric.rest.control.fabrics."
        msg += f"Fabrics.{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["force_show_run"] = False
        self.properties["include_all_msd_switches"] = False
        self.properties["switch_id"] = None
        self.properties["verb"] = "POST"

    @property
    def force_show_run(self):
        """
        -   getter: Return the force_show_run value.
        -   setter: Set the force_show_run value.
        -   setter: Raise ``ValueError`` if force_show_run is
            not a boolean.
        -   Default: False
        -   Optional
        """
        return self.properties["force_show_run"]

    @force_show_run.setter
    def force_show_run(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Expected boolean for {method_name}. "
            msg += f"Got {value} with type {type(value).__name__}."
            raise ValueError(msg)
        self.properties["force_show_run"] = value

    @property
    def include_all_msd_switches(self):
        """
        -   getter: Return the include_all_msd_switches.
        -   setter: Set the include_all_msd_switches.
        -   setter: Raise ``ValueError`` if include_all_msd_switches
            is not a boolean.
        -   Default: False
        -   Optional
        -   Notes:
            -   ``include_all_msd_switches`` is removed from the path if
                ``switch_id`` is set.
        """
        return self.properties["include_all_msd_switches"]

    @include_all_msd_switches.setter
    def include_all_msd_switches(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Expected boolean for {method_name}. "
            msg += f"Got {value} with type {type(value).__name__}."
            raise ValueError(msg)
        self.properties["include_all_msd_switches"] = value

    @property
    def path(self):
        """
        - Override the path property to mandate fabric_name is set.
        - Raise ``ValueError`` if fabric_name is not set.
        """
        _path = self.path_fabric_name
        _path += "/config-deploy"
        if self.switch_id:
            _path += f"/{self.switch_id}"
        _path += f"?forceShowRun={self.force_show_run}"
        if not self.switch_id:
            _path += f"&inclAllMSDSwitches={self.include_all_msd_switches}"
        return _path

    @property
    def switch_id(self):
        """
        -   getter: Return the switch_id value.
        -   setter: Set the switch_id value.
        -   setter: Raise ``TypeError`` if switch_id is not a string or list.
        -   Default: None
        -   Optional
        -   Notes:
            -   ``include_all_msd_switches`` is removed from the path if
                ``switch_id`` is set.
            -   If value is a list, it is converted to a comma-separated
                string.
        """
        return self.properties["switch_id"]

    @switch_id.setter
    def switch_id(self, value):
        method_name = inspect.stack()[0][3]

        def error(param, param_type):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Expected string or list for switch_id. "
            msg += f"Got {param} with type {param_type}."
            raise TypeError(msg)

        if isinstance(value, str):
            pass
        elif isinstance(value, list):
            for item in value:
                if not isinstance(item, str):
                    error(item, type(item).__name__)
            value = ",".join(value)
        else:
            error(value, type(value).__name__)
        self.properties["switch_id"] = value


class EpFabricConfigSave(Fabrics):
    """
    ## V1 API - Fabrics().EpFabricConfigSave()

    ### Description
    Return endpoint to initiate config-save on fabric_name.

    ### Raises
    -  ``ValueError``: If fabric_name is not set.
    -  ``ValueError``: If fabric_name is invalid.
    -  ``ValueError``: If ticket_id is not a string.

    ### Path
    -  ``/fabrics/{fabric_name}/config-save``
    -  ``/fabrics/{fabric_name}/config-save?ticketId={ticket_id}``

    ### Verb
    -   POST

    ### Parameters
    - fabric_name: string
        - set the ``fabric_name`` to be used in the path
        - required
    -   ticket_id: string
            -   optional unless Change Control is enabled
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpFabricConfigSave()
    instance.fabric_name = "MyFabric"
    instance.ticket_id = "MyTicket1234"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self._build_properties()
        msg = "ENTERED api.v1.lan_fabric.rest.control.fabrics."
        msg += f"Fabrics.{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "POST"

    @property
    def path(self):
        """
        - Endpoint for config-save.
        - Set self.ticket_id if Change Control is enabled.
        - Raise ``ValueError`` if fabric_name is not set.
        """
        _path = self.path_fabric_name
        _path += "/config-save"
        if self.ticket_id:
            _path += f"?ticketId={self.ticket_id}"
        return _path


class EpFabricCreate(Fabrics):
    """
    ## V1 API - Fabrics().EpFabricCreate()

    ### Description
    Return endpoint information.

    ### Raises
    -   ``ValueError``: If fabric_name is not set.
    -   ``ValueError``: If fabric_name is invalid.
    -   ``ValueError``: If template_name is not set.
    -   ``ValueError``: If template_name is not a valid fabric template name.

    ### Path
    -   ``/rest/control/fabrics/{FABRIC_NAME}/{TEMPLATE_NAME}``

    ### Verb
    -   POST

    ### Parameters
    - fabric_name: string
        - set the ``fabric_name`` to be used in the path
        - required
    - template_name: string
        - set the ``template_name`` to be used in the path
        - required
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpFabricCreate()
    instance.fabric_name = "MyFabric"
    instance.template_name = "Easy_Fabric"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self.required_properties.add("template_name")
        self._build_properties()
        msg = "ENTERED api.v1.lan_fabric.rest.control.fabrics."
        msg += f"Fabrics.{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "POST"

    @property
    def path(self):
        """
        - Endpoint for fabric create.
        - Raise ``ValueError`` if fabric_name is not set.
        """
        return self.path_fabric_name_template_name


class EpFabricDelete(Fabrics):
    """
    ## V1 API - Fabrics().EpFabricDelete()

    ### Description
    Return endpoint to delete ``fabric_name``.

    ### Raises
    -   ``ValueError``: If fabric_name is not set.
    -   ``ValueError``: If fabric_name is invalid.

    ### Path
    -   ``/fabrics/{fabric_name}``

    ### Verb
    -   DELETE

    ### Parameters
    - fabric_name: string
        - set the ``fabric_name`` to be used in the path
        - required
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpFabricDelete()
    instance.fabric_name = "MyFabric"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self._build_properties()
        msg = "ENTERED api.v1.lan_fabric.rest.control.fabrics."
        msg += f"Fabrics.{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "DELETE"

    @property
    def path(self):
        """
        - Endpoint for fabric delete.
        - Raise ``ValueError`` if fabric_name is not set.
        """
        return self.path_fabric_name


class EpFabricDetails(Fabrics):
    """
    ## V1 API - Fabrics().EpFabricDetails()

    ### Description
    Return the endpoint to query ``fabric_name`` details.

    ### Raises
    -   ``ValueError``: If fabric_name is not set.
    -   ``ValueError``: If fabric_name is invalid.

    ### Path
    -   ``/fabrics/{fabric_name}``

    ### Verb
    -   GET

    ### Parameters
    - fabric_name: string
        - set the ``fabric_name`` to be used in the path
        - required
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpFabricDelete()
    instance.fabric_name = "MyFabric"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self._build_properties()
        msg = "ENTERED api.v1.lan_fabric.rest.control.fabrics."
        msg += f"Fabrics.{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "GET"

    @property
    def path(self):
        return self.path_fabric_name


class EpFabricFreezeMode(Fabrics):
    """
    ## V1 API - Fabrics().EpFabricFreezeMode()

    ### Description
    Return the endpoint to query ``fabric_name`` freezemode status.

    ### Raises
    -   ``ValueError``: If fabric_name is not set.
    -   ``ValueError``: If fabric_name is invalid.

    ### Path
    -   ``/fabrics/{fabric_name}/freezemode``

    ### Verb
    -   GET

    ### Parameters
    - fabric_name: string
        - set the ``fabric_name`` to be used in the path
        - required
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpFabricDelete()
    instance.fabric_name = "MyFabric"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self._build_properties()
        msg = "ENTERED api.v1.lan_fabric.rest.control.fabrics."
        msg += f"Fabrics.{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "GET"

    @property
    def path(self):
        return f"{self.path_fabric_name}/freezemode"


# class EpFabricSummary() See module_utils/common/api/v1/rest/control/switches.py


class EpFabricUpdate(Fabrics):
    """
    ## V1 API - Fabrics().EpFabricUpdate()

    ### Description
    Return endpoint information.

    ### Raises
    -   ``ValueError``: If fabric_name is not set.
    -   ``ValueError``: If fabric_name is invalid.
    -   ``ValueError``: If template_name is not set.
    -   ``ValueError``: If template_name is not a valid fabric template name.

    ### Path
    ``/api/v1/lan-fabric/rest/control/fabrics/{FABRIC_NAME}/{TEMPLATE_NAME}``

    ### Verb
    -   PUT

    ### Parameters
    - fabric_name: string
        - set the ``fabric_name`` to be used in the path
        - required
    - template_name: string
        - set the ``template_name`` to be used in the path
        - required
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpFabricUpdate()
    instance.fabric_name = "MyFabric"
    instance.template_name = "Easy_Fabric_IPFM"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self.required_properties.add("template_name")
        msg = "ENTERED api.v1.lan_fabric.rest.control.fabrics."
        msg += f"Fabrics.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        """
        - Endpoint for fabric create.
        - Raise ``ValueError`` if fabric_name is not set.
        """
        return self.path_fabric_name_template_name

    @property
    def verb(self):
        return "PUT"


class EpFabrics(Fabrics):
    """
    ## V1 API - Fabrics().EpFabrics()

    ### Description
    Return the endpoint to query fabrics.

    ### Raises
    -   None

    ### Path
    -   ``/api/v1/lan-fabric/rest/control/fabrics``

    ### Verb
    -   GET

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpFabrics()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self._build_properties()
        msg = "ENTERED api.v1.lan_fabric.rest.control.fabrics."
        msg += f"Fabrics.{self.class_name}"
        self.log.debug(msg)

    def _build_properties(self):
        super()._build_properties()
        self.properties["verb"] = "GET"

    @property
    def path(self):
        return self.fabrics


class EpMaintenanceModeDeploy(Fabrics):
    """
    ## V1 API - Fabrics().EpMaintenanceModeDeploy()

    ### Description
    Return endpoint to deploy maintenance mode on a switch.

    ### Raises
    -  ``ValueError``: If ``fabric_name`` is not set.
    -  ``ValueError``: If ``fabric_name`` is invalid.
    -  ``ValueError``: If ``serial_number`` is not set.
    -  ``ValueError``: If ``ticket_id`` is not a string.

    ### Path
    -  ``/fabrics/{fabric_name}/switches/{serial_number}/deploy-maintenance-mode``

    ### Verb
    -   POST

    ### Parameters
    - fabric_name: string
        -   set the ``fabric_name`` to be used in the path
        -   required
    - serial_number: string
        -   set the switch ``serial_number`` to be used in the path
        -   required
    - wait_for_mode_change: boolean
        -   instruct the API to wait for the mode change to complete
            before continuing.
        -   optional
        -   default: False
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpMaintenanceModeDeploy()
    instance.fabric_name = "MyFabric"
    instance.serial_number = "CHM1234567"
    instance.wait_for_mode_change = True
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self.required_properties.add("serial_number")
        self._wait_for_mode_change = False
        msg = "ENTERED api.v1.lan_fabric.rest.control.fabrics."
        msg += f"Fabrics.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        """
        - Path for deploy-maintenance-mode
        - Raise ``ValueError`` if fabric_name is not set.
        - Raise ``ValueError`` if serial_number is not set.
        """
        _path = self.path_fabric_name_serial_number
        _path += "/deploy-maintenance-mode"
        if self.wait_for_mode_change:
            _path += "?waitForModeChange=true"
        return _path

    @property
    def verb(self):
        """
        - Return the verb for the endpoint.
        - verb: POST
        """
        return "POST"

    @property
    def wait_for_mode_change(self):
        """
        - getter: Return the wait_for_mode_change value.
        - setter: Set the wait_for_mode_change value.
        - setter: Raise ``TypeError`` if wait_for_mode_change is not a boolean.
        - Type: boolean
        - Default: False
        - Optional
        """
        return self._wait_for_mode_change

    @wait_for_mode_change.setter
    def wait_for_mode_change(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Expected boolean for {method_name}. "
            msg += f"Got {value} with type {type(value).__name__}."
            raise TypeError(msg)
        self._wait_for_mode_change = value


class EpMaintenanceModeEnable(Fabrics):
    """
    ## V1 API - Fabrics().EpMaintenanceModeEnable()

    ### Description
    Return endpoint to enable maintenance mode on a switch.

    ### Raises
    -  ``ValueError``: If ``fabric_name`` is not set.
    -  ``ValueError``: If ``fabric_name`` is invalid.
    -  ``ValueError``: If ``serial_number`` is not set.
    -  ``ValueError``: If ``ticket_id`` is not a string.

    ### Path
    -  ``/fabrics/{fabric_name}/switches/{serial_number}/maintenance-mode``
    -  ``/fabrics/{fabric_name}/switches/{serial_number}/maintenance-mode?ticketId={ticket_id}``

    ### Verb
    -   POST

    ### Parameters
    - fabric_name: string
        - set the ``fabric_name`` to be used in the path
        - required
    - serial_number: string
        - set the switch ``serial_number`` to be used in the path
        - required
    -   ticket_id: string
            -   optional unless Change Control is enabled
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpMaintenanceModeEnable()
    instance.fabric_name = "MyFabric"
    instance.serial_number = "CHM1234567"
    instance.ticket_id = "MyTicket1234"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self.required_properties.add("serial_number")
        msg = "ENTERED api.v1.lan_fabric.rest.control.fabrics."
        msg += f"Fabrics.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        """
        - Path for maintenance-mode enable
        - Raise ``ValueError`` if fabric_name is not set.
        - Raise ``ValueError`` if serial_number is not set.
        - self.ticket_id is mandatory if Change Control is enabled.
        """
        _path = self.path_fabric_name_serial_number
        _path += "/maintenance-mode"
        if self.ticket_id:
            _path += f"?ticketId={self.ticket_id}"
        return _path

    @property
    def verb(self):
        """
        - Return the verb for the endpoint.
        - verb: POST
        """
        return "POST"


class EpMaintenanceModeDisable(Fabrics):
    """
    ## V1 API - Fabrics().EpMaintenanceModeDisable()

    ### Description
    Return endpoint to remove switch from maintenance mode
    (i.e. enable normal mode).

    ### Raises
    -  ``ValueError``: If ``fabric_name`` is not set.
    -  ``ValueError``: If ``fabric_name`` is invalid.
    -  ``ValueError``: If ``serial_number`` is not set.
    -  ``ValueError``: If ``ticket_id`` is not a string.

    ### Path
    -  ``/fabrics/{fabric_name}/switches/{serial_number}/maintenance-mode``
    -  ``/fabrics/{fabric_name}/switches/{serial_number}/maintenance-mode?ticketId={ticket_id}``

    ### Verb
    -   DELETE

    ### Parameters
    - fabric_name: string
        - set the ``fabric_name`` to be used in the path
        - required
    - serial_number: string
        - set the switch ``serial_number`` to be used in the path
        - required
    -   ticket_id: string
            -   optional unless Change Control is enabled
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpMaintenanceModeDisable()
    instance.fabric_name = "MyFabric"
    instance.serial_number = "CHM1234567"
    instance.ticket_id = "MyTicket1234"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("fabric_name")
        self.required_properties.add("serial_number")
        msg = "ENTERED api.v1.lan_fabric.rest.control.fabrics."
        msg += f"Fabrics.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        """
        - Path for maintenance-mode disable
        - Raise ``ValueError`` if fabric_name is not set.
        - Raise ``ValueError`` if serial_number is not set.
        - self.ticket_id is mandatory if Change Control is enabled.
        """
        _path = self.path_fabric_name_serial_number
        _path += "/maintenance-mode"
        if self.ticket_id:
            _path += f"?ticketId={self.ticket_id}"
        return _path

    @property
    def verb(self):
        """
        - Return the endpoint verb.
        - verb: DELETE
        """
        return "DELETE"
