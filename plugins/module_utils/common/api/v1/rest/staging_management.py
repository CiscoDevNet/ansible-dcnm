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

from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.image_management import \
    ImageManagement


class StagingManagement(ImageManagement):
    """
    ## V1 API - ImageManagement().StagingManagement()

    ### Description
    Common methods and properties for StagingManagement() subclasses

    ### Path
    ``/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/stagingmanagement``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.staging_management = f"{self.image_management}/rest/stagingmanagement"
        self.log.debug("ENTERED api.v1.StagingManagement()")


class EpImageStage(StagingManagement):
    """
    ## V1 API - StagingManagement().EpImageStage()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/rest/stagingmanagement/stage-image``

    ### Verb
    -   POST

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpImageStage()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED api.v1.StagingManagement.EpImageStage()")
        self._build_properties()

    def _build_properties(self):
        self.properties["path"] = f"{self.staging_management}/stage-image"
        self.properties["verb"] = "POST"


class EpImageValidate(StagingManagement):
    """
    ## V1 API - StagingManagement().EpImageValidate()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/rest/stagingmanagement/validate-image``

    ### Verb
    -   POST

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpImageValidate()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED api.v1.StagingManagement.EpImageValidate()")
        self._build_properties()

    def _build_properties(self):
        self.properties["path"] = f"{self.staging_management}/validate-image"
        self.properties["verb"] = "POST"


class EpStageInfo(StagingManagement):
    """
    ## V1 API - StagingManagement().EpStageInfo()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/rest/stagingmanagement/stage-info``

    ### Verb
    -   GET

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpStageInfo()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED api.v1.StagingManagement.EpStageInfo()")
        self._build_properties()

    def _build_properties(self):
        self.properties["path"] = f"{self.staging_management}/stage-info"
        self.properties["verb"] = "GET"
