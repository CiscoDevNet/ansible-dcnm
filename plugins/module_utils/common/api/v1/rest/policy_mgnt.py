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

import inspect
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.image_management import \
    ImageManagement


class PolicyMgnt(ImageManagement):
    """
    ## V1 API - ImageManagement().PolicyMgnt()

    ### Description
    Common methods and properties for PolicyMgnt() subclasses

    ### Path
    ``/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.policy_mgmt = f"{self.image_management}/rest/policymgnt"
        self.log.debug("ENTERED api.v1.PolicyMgnt()")


class EpPolicies(PolicyMgnt):
    """
    ## V1 API - PolicyMgnt().EpPolicies()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/rest/policymgnt/policies``

    ### Verb
    -   GET

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpPolicies()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED api.v1.PolicyMgnt.EpPolicies()")
        self._build_properties()

    def _build_properties(self):
        self.properties["path"] = f"{self.policy_mgmt}/policies"
        self.properties["verb"] = "GET"


class EpPoliciesAllAttached(PolicyMgnt):
    """
    ## V1 API - PolicyMgnt().EpPoliciesAllAttached()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/rest/policymgnt/all-attached-policies``

    ### Verb
    -   GET

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpPoliciesAllAttached()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED api.v1.PolicyMgnt.EpPoliciesAllAttached()")
        self._build_properties()

    def _build_properties(self):
        self.properties["path"] = f"{self.policy_mgmt}/all-attached-policies"
        self.properties["verb"] = "GET"


class EpPolicyAttach(PolicyMgnt):
    """
    ## V1 API - PolicyMgnt().EpPolicyAttach()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/rest/policymgnt/attach-policy``

    ### Verb
    -   POST

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpPolicyAttach()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED api.v1.PolicyMgnt.EpPolicyAttach()")
        self._build_properties()

    def _build_properties(self):
        self.properties["path"] = f"{self.policy_mgmt}/attach-policy"
        self.properties["verb"] = "POST"


class EpPolicyCreate(PolicyMgnt):
    """
    ## V1 API - PolicyMgnt().EpPolicyCreate()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/rest/policymgnt/platform-policy``

    ### Verb
    -   POST

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpPolicyCreate()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED api.v1.PolicyMgnt.EpPolicyCreate()")
        self._build_properties()

    def _build_properties(self):
        self.properties["path"] = f"{self.policy_mgmt}/platform-policy"
        self.properties["verb"] = "POST"


class EpPolicyDetach(PolicyMgnt):
    """
    ## V1 API - PolicyMgnt().EpPolicyDetach()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/rest/policymgnt/detach-policy``

    ### Verb
    -   DELETE

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpPolicyDetach()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED api.v1.PolicyMgnt.EpPolicyDetach()")
        self._build_properties()

    def _build_properties(self):
        self.properties["path"] = f"{self.policy_mgmt}/detach-policy"
        self.properties["verb"] = "DELETE"


class EpPolicyInfo(PolicyMgnt):
    """
    ## V1 API - PolicyMgnt().EpPolicyInfo()

    ### Description
    Return endpoint information.

    ### Raises
    -  ``ValueError``: If path is accessed before setting policy_name.

    ### Path
    -   ``/rest/policymgnt/image-policy/{policy_name}``

    ### Verb
    -   GET

    ### Parameters
    -   policy_name: str
            -   set the policy_name
            -   required
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpPolicyInfo()
    instance.policy_name = "MyPolicy"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED api.v1.PolicyMgnt.EpPolicyDetach()")
        self._build_properties()

    def _build_properties(self):
        self.properties["policy_name"] = None
        self.properties["path"] = f"{self.policy_mgmt}/image-policy"
        self.properties["verb"] = "GET"

    @property
    def path(self):
        method_name = inspect.stack()[0][3]
        if self.policy_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.policy_name must be set before "
            msg += f"accessing {method_name}."
            raise ValueError(msg)
        return f"{self.properties['path']}/{self.policy_name}"

    @property
    def policy_name(self):
        """
        - getter: Return the policy_name.
        - setter: Set the policy_name.
        """
        return self.properties["policy_name"]

    @policy_name.setter
    def policy_name(self, value):
        self.properties["policy_name"] = value
