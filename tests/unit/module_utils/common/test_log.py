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
# pylint: disable=unused-import
# Some fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-argument
# Some tests require calling protected methods
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    does_not_raise, log_fixture)


def test_log_00010(log) -> None:
    """
    Function
    - log_msg

    Test
    - log_msg returns None when debug is False
    """
    with does_not_raise():
        instance = log

    error_message = "This is an error message"
    instance.debug = False
    assert instance.log_msg(error_message) is None


def test_log_00011(tmp_path, log) -> None:
    """
    Function
    - log_msg

    Test
    - log_msg does not write to the logfile when debug is False
    """
    directory = tmp_path / "test_log_msg"
    directory.mkdir()
    filename = directory / "test_log_msg.txt"

    msg = "This is an error message"

    with does_not_raise():
        instance = log
        instance.debug = False
        instance.logfile = filename
        instance.log_msg(msg)

    match = r"\[Errno 2\] "
    match += "No such file or directory"
    with pytest.raises(FileNotFoundError, match=match):
        filename.read_text(encoding="UTF-8")


def test_log_00012(tmp_path, log) -> None:
    """
    Function
    - log_msg

    Test
    - log_msg writes to the logfile when debug is True
    """
    directory = tmp_path / "test_log_msg"
    directory.mkdir()
    filename = directory / "test_log_msg.txt"

    msg = "This is an error message"

    with does_not_raise():
        instance = log
        instance.debug = True
        instance.logfile = filename
        instance.log_msg(msg)

    assert filename.read_text(encoding="UTF-8") == msg + "\n"


def test_log_00013(tmp_path, log) -> None:
    """
    Function
    - log_msg

    Test
    - log_msg calls fail_json if the logfile cannot be opened

    Description
    To ensure an error is generated, we attempt a write to a filename
    that is too long for the target OS.
    """
    directory = tmp_path / "test_log_msg"
    directory.mkdir()
    filename = directory / f"test_{'a' * 2000}_log_msg.txt"

    msg = "This is an error message"

    with does_not_raise():
        instance = log
        instance.debug = True
        instance.logfile = filename

    match = "error writing to logfile"
    with pytest.raises(AnsibleFailJson, match=match):
        instance.log_msg(msg)


def test_log_00020(log) -> None:
    """
    Function
    - debug

    Test
    - log_msg calls fail_json if debug is not a boolean
    """
    with does_not_raise():
        instance = log

    match = "Invalid type for debug. Expected bool. "
    with pytest.raises(AnsibleFailJson, match=match):
        instance.debug = 10
