# Copyright (c) 2025 Cisco and/or its affiliates.
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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# Also, fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-import, protected-access, use-implicit-booleaness-not-comparison, unused-variable

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import logging

import pytest
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_log import DcnmLog
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    does_not_raise

from utils import (params_error_severity, params_missing_msg,
                   params_missing_severity)


def test_dcnm_log_00000() -> None:
    """
    ### Classes and Methods
    - DcnmLog()
        - __init__()

    ### Summary
    __init__() happy path with minimal config.
    - Verify class attributes are initialized to expected values.
    - params.severity is missing so the default (DEBUG) is used.

    ### Test
    -   Class attributes are initialized to expected values.
    -   Exceptions are not not raised.
    """
    with does_not_raise():
        instance = DcnmLog(params_missing_severity)
    assert instance.class_name == "DcnmLog"
    assert instance.params == params_missing_severity
    assert instance.message == params_error_severity["msg"]
    assert instance.severity == "DEBUG"
    assert instance.result["changed"] is False
    assert instance.result["failed"] is False
    log_instance = logging.getLogger(f"dcnm.{instance.class_name}")
    assert isinstance(instance.log, type(log_instance))


def test_dcnm_log_00010() -> None:
    """
    ### Classes and Methods
    - DcnmLog()
        - __init__()

    ### Summary
    __init__() happy path with minimal config.
    - Verify class attributes are initialized to expected values.
    - params.severity is set to DEBUG

    ### Test
    -   Class attributes are initialized to expected values.
    -   Exceptions are not not raised.
    """
    with does_not_raise():
        instance = DcnmLog(params_error_severity)
    assert instance.class_name == "DcnmLog"
    assert instance.params == params_error_severity
    assert instance.message == params_error_severity["msg"]
    assert instance.severity == params_error_severity["severity"]
    assert instance.result["changed"] is False
    assert instance.result["failed"] is False
    log_instance = logging.getLogger(f"dcnm.{instance.class_name}")
    assert isinstance(instance.log, type(log_instance))


def test_dcnm_log_00020() -> None:
    """
    ### Classes and Methods
    - DcnmLog()
        - __init__()

    ### Summary
    __init__() sad path
    - params.msg is missing

    ### Test
    -   ValueError is raised with expected error message.
    """
    match = r"Exiting. Missing mandatory parameter: msg"
    with pytest.raises(ValueError, match=match):
        instance = DcnmLog(params_missing_msg)
