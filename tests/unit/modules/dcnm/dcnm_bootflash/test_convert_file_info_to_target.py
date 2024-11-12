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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# Also, fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-import, protected-access, use-implicit-booleaness-not-comparison

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect
from datetime import datetime

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.convert_file_info_to_target import \
    ConvertFileInfoToTarget
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_bootflash.utils import (
    does_not_raise, file_info, targets_convert_file_info_to_target)


def test_convert_file_info_to_target_00000() -> None:
    """
    ### Classes and Methods
    - ConvertFileInfoToTarget()
        - __init__()

    ### Summary
    - Verify class attributes are initialized to expected values.

    ### Test
    -   Class attributes are initialized to expected values.
    -   Exceptions are not not raised.
    """
    with does_not_raise():
        instance = ConvertFileInfoToTarget()
    assert instance.action == "convert_file_info_to_target"
    assert instance.class_name == "ConvertFileInfoToTarget"

    assert instance._file_info is None
    assert instance._filename is None
    assert instance._filepath is None
    assert instance._ip_address is None
    assert instance._serial_number is None
    assert instance._supervisor is None
    assert instance._target is None
    assert instance.timestamp_format == "%b %d %H:%M:%S %Y"


def test_convert_file_info_to_target_00100() -> None:
    """
    ### Classes and Methods
    - ConvertFileInfoToTarget()
        - commit()

    ### Summary
    -   Verify commit() happy path.
    -   Given a file_info dict, verify that a properly-constructed
        target dict is built and that individual getter properties return
        expected values.

    ### Test
    -   Exceptions are not not raised.
    -   target dict is built as expected.
    -   Individual getter properties return expected values.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ConvertFileInfoToTarget()
        instance.file_info = file_info(f"{key}")
        instance.commit()

    assert instance.target == targets_convert_file_info_to_target(key)
    assert instance.date == datetime(2023, 9, 19, 22, 20, 7)
    assert instance.device_name == "cvd-1212-spine"
    assert instance.filepath == "bootflash:"
    assert instance.ip_address == "192.168.1.1"
    assert instance.name == "bootflash:"
    assert instance.size == "218233885"
    assert instance.serial_number == "BDY3814QDD0"
    assert instance.supervisor == "active"


def test_convert_file_info_to_target_00110() -> None:
    """
    ### Classes and Methods
    - ConvertFileInfoToTarget()
        - commit()

    ### Summary
    -   Verify ``commit()`` raises exception when called without first
        setting ``file_info``.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = ConvertFileInfoToTarget()
    match = r"ConvertFileInfoToTarget\.validate_commit_parameters:\s+"
    match += r"file_info must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_convert_file_info_to_target_00120() -> None:
    """
    ### Classes and Methods
    - ConvertFileInfoToTarget()
        - commit()

    ### Summary
    -   Verify ``commit()`` raises ``ValueError`` when ``PurePosixPath``
        raises ``TypeError``.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ConvertFileInfoToTarget()
        instance.file_info = file_info(f"{key}")

    # Depending on the version of PurePosixPath, the Error detail may vary.
    match = r"ConvertFileInfoToTarget.commit:\s+"
    match += r"Could not build PosixPath from name and filename\.\s+"
    match += r"name: 10, filename: foo\.\s+"
    match += r"Error detail:.*"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_convert_file_info_to_target_00130() -> None:
    """
    ### Classes and Methods
    - ConvertFileInfoToTarget()
        - commit()

    ### Summary
    -   Verify ``commit()`` raises ``ValueError`` when filepath does not
        contain ":/".

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ConvertFileInfoToTarget()
        instance.file_info = file_info(f"{key}")

    match = r"ConvertFileInfoToTarget.commit:\s+"
    match += r"Invalid filepath bootflash\/foo constructed from\s+"
    match += r"name: bootflash, filename: foo\.\s+"
    match += r"Missing ':\/' in the path\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_convert_file_info_to_target_00200() -> None:
    """
    ### Classes and Methods
    - ConvertFileInfoToTarget()
        - date

    ### Summary
    -   Verify ``ValueError`` is raised if ``file_info`` has not been set
        before accessing getter properties, like ``date``.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = ConvertFileInfoToTarget()

    match = r"ConvertFileInfoToTarget\._get:\s+"
    match += r"file_info must be set before calling ``_get\(\)``\."
    with pytest.raises(ValueError, match=match):
        instance.date  # pylint: disable=pointless-statement


def test_convert_file_info_to_target_00210() -> None:
    """
    ### Classes and Methods
    - ConvertFileInfoToTarget()
        - date

    ### Summary
    -   Verify ``ValueError`` is raised if date cannot convert file_info.date
        to ``YYYY-MM-DD HH-MM-SS`` format.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ConvertFileInfoToTarget()

    match = r"ConvertFileInfoToTarget.date:\s+"
    match += r"Could not convert date to datetime object\.\s+"
    match += r"date: Sep 19 22:20:07 202\.\s+"
    match += r"Error detail:\s+"
    match += (
        r"time data 'Sep 19 22:20:07 202' does not match format '%b %d %H:%M:%S %Y'\."
    )
    with pytest.raises(ValueError, match=match):
        instance.file_info = file_info(f"{key}")
        instance.date  # pylint: disable=pointless-statement


def test_convert_file_info_to_target_00300() -> None:
    """
    ### Classes and Methods
    - ConvertFileInfoToTarget()
        - target

    ### Summary
    -   Verify ``ValueError`` is raised if ``target`` is accessed before
        calling commit.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    with does_not_raise():
        instance = ConvertFileInfoToTarget()

    match = r"ConvertFileInfoToTarget.target:\s+"
    match += r"target has not been built\.\s+"
    match += r"Call commit\(\) before accessing\."
    with pytest.raises(ValueError, match=match):
        instance.target  # pylint: disable=pointless-statement
