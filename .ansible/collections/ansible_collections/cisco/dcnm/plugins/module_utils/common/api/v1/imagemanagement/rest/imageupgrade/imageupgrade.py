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

import logging

from ..rest import Rest


class ImageUpgrade(Rest):
    """
    ## api.v1.imagemanagement.rest.imageupgrade.ImageUpgrade()

    ### Description
    Common methods and properties for ImageUpgrade() subclasses.

    ### Path
    -   ``/api/v1/imagemanagement/rest/imageupgrade``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.imageupgrade = f"{self.rest}/imageupgrade"
        msg = f"ENTERED api.v1.imagemanagement.rest.{self.class_name}"
        self.log.debug(msg)
        self._build_properties()

    def _build_properties(self):
        """
        - Add any class-specific properties to self.properties.
        """


class EpInstallOptions(ImageUpgrade):
    """
    ## V1 API - Fabrics().EpInstallOptions()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/api/v1/imagemanagement/rest/imageupgrade/install-options``

    ### Verb
    -   POST

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    ep_install_options = EpInstallOptions()
    path = ep_install_options.path
    verb = ep_install_options.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"imageupgrade.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        """
        - Return the path for the endpoint.
        """
        return f"{self.imageupgrade}/install-options"

    @property
    def verb(self):
        """
        - Return the verb for the endpoint.
        """
        return "POST"


class EpUpgradeImage(ImageUpgrade):
    """
    ## V1 API - Fabrics().EpUpgradeImage()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/api/v1/imagemanagement/rest/imageupgrade/upgrade-image``

    ### Verb
    -   POST

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    ep_upgrade_image = EpUpgradeImage()
    path = ep_upgrade_image.path
    verb = ep_upgrade_image.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"imageupgrade.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        """
        - Return the path for the endpoint.
        """
        return f"{self.imageupgrade}/upgrade-image"

    @property
    def verb(self):
        """
        - Return the verb for the endpoint.
        """
        return "POST"
