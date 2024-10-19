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

from ..rest import Rest


class PolicyMgnt(Rest):
    """
    ## api.v1.imagemanagement.rest.policymgnt.PolicyMgnt()

    ### Description
    Common methods and properties for PolicyMgnt() subclasses

    ### Path
    ``/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.policymgnt = f"{self.rest}/policymgnt"
        self.log.debug("ENTERED api.v1.PolicyMgnt()")


class EpPolicies(PolicyMgnt):
    """
    ## api.v1.imagemanagement.rest.policymgnt.EpPolicies()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/api/v1/imagemanagement/rest/policymgnt/policies``

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
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"policymgnt.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        return f"{self.policymgnt}/policies"

    @property
    def verb(self):
        return "GET"


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
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"policymgnt.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        return f"{self.policymgnt}/all-attached-policies"

    @property
    def verb(self):
        return "GET"


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
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"policymgnt.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        return f"{self.policymgnt}/attach-policy"

    @property
    def verb(self):
        return "POST"


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
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"policymgnt.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        return f"{self.policymgnt}/platform-policy"

    @property
    def verb(self):
        return "POST"


class EpPolicyDelete(PolicyMgnt):
    """
    ## V1 API - PolicyMgnt().EpPolicyDelete()

    ### Description
    Delete image policies.

    ### Raises
    -   None

    ### Path
    -   ``/rest/policymgnt/policy``

    ### Verb
    -   DELETE

    ### Notes
    Expects a JSON payload as shown below, where ``policyNames`` is a
    comma-separated list of policy names.

    ```json
        {
            "policyNames": "policyA,policyB,etc"
        }
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"policymgnt.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        return f"{self.policymgnt}/policy"

    @property
    def verb(self):
        return "DELETE"


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
        self._serial_numbers = None
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"policymgnt.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        """
        ### Summary
        The endpoint path.

        ### Raises
        -   ``ValueError`` if:
                -   ``path`` is accessed before setting ``serial_numbers``.
        """
        if self.serial_numbers is None:
            msg = f"{self.class_name}.serial_numbers must be set before "
            msg += f"accessing {self.class_name}.path."
            raise ValueError(msg)
        query_param = ",".join(self.serial_numbers)
        return f"{self.policymgnt}/detach-policy?serialNumber={query_param}"

    @property
    def verb(self):
        return "DELETE"

    @property
    def serial_numbers(self):
        """
        ### Summary
        A ``list`` of switch serial numbers.

        ### Raises
        -   ``TypeError`` if:
                -   ``serial_numbers`` is not a ``list``.
        """
        return self._serial_numbers

    @serial_numbers.setter
    def serial_numbers(self, value):
        if not isinstance(value, list):
            msg = f"{self.class_name}.serial_numbers must be a list "
            msg += "of switch serial numbers."
            raise TypeError(msg)
        self._serial_numbers = value


class EpPolicyEdit(PolicyMgnt):
    """
    ## V1 API - PolicyMgnt().EpPolicyEdit()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/rest/policymgnt/edit-policy``

    ### Verb
    -   POST

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpPolicyEdit()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"policymgnt.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        return f"{self.policymgnt}/edit-policy"

    @property
    def verb(self):
        return "POST"


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
        self._policy_name = None
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"policymgnt.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        method_name = inspect.stack()[0][3]
        if self.policy_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.policy_name must be set before "
            msg += f"accessing {method_name}."
            raise ValueError(msg)
        return f"{self.policymgnt}/image-policy/{self.policy_name}"

    @property
    def verb(self):
        return "GET"

    @property
    def policy_name(self):
        """
        - getter: Return the policy_name.
        - setter: Set the policy_name.
        """
        return self._policy_name

    @policy_name.setter
    def policy_name(self, value):
        self._policy_name = value
