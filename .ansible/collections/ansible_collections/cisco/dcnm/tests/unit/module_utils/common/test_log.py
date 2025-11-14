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

import logging

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    MockAnsibleModule, does_not_raise, log_fixture)


def test_log_00010(tmp_path, log) -> None:
    """
    Function
    - log.info()
    - log.debug()
    - log.warning()
    - log.critical()

    Test
    -   log.<level> logs to the logfile
    -   The function name is in the log message
        (the formatter includes the function name)
    """
    with does_not_raise():
        ansible_module = MockAnsibleModule()
        instance = Log(ansible_module)

    directory = tmp_path / "test_log_msg"
    directory.mkdir()
    filename = directory / "test_log_msg.txt"

    config = {
        "version": 1,
        "formatters": {
            "standard": {
                "class": "logging.Formatter",
                "format": "%(asctime)s - %(levelname)s - [%(name)s.%(funcName)s.%(lineno)d] %(message)s",
            }
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "level": "DEBUG",
                "filename": filename,
                "mode": "a",
                "encoding": "utf-8",
                "maxBytes": 500000,
                "backupCount": 4,
            }
        },
        "loggers": {
            "dcnm": {"handlers": ["file"], "level": "DEBUG", "propagate": False}
        },
        "root": {"level": "INFO", "handlers": ["file"]},
    }
    info_msg = "foo"
    debug_msg = "bing"
    warning_msg = "bar"
    critical_msg = "baz"
    instance.config = config
    instance.commit()
    log = logging.getLogger("dcnm.test_logger")
    log.info(info_msg)
    log.debug(debug_msg)
    log.warning(warning_msg)
    log.critical(critical_msg)
    assert logging.getLevelName(log.getEffectiveLevel()) == "DEBUG"
    assert info_msg in filename.read_text(encoding="UTF-8")
    assert debug_msg in filename.read_text(encoding="UTF-8")
    assert warning_msg in filename.read_text(encoding="UTF-8")
    assert critical_msg in filename.read_text(encoding="UTF-8")
    # test that the function name is in the log message
    assert "test_log_00010" in filename.read_text(encoding="UTF-8")


def test_log_00011(caplog, log) -> None:
    """
    Function
    - log.config
    - log.commit()

    Test
    - Nothing is logged when config is None
    """
    with does_not_raise():
        ansible_module = MockAnsibleModule()
        instance = Log(ansible_module)
        instance.commit()

    info_msg = "foo"
    debug_msg = "bing"
    warning_msg = "bar"
    critical_msg = "baz"
    log = logging.getLogger("dcnm.test_logger")
    log.info(info_msg)
    log.debug(debug_msg)
    log.warning(warning_msg)
    log.critical(critical_msg)
    assert info_msg not in caplog.text
    assert debug_msg not in caplog.text
    assert warning_msg not in caplog.text
    assert critical_msg not in caplog.text


def test_log_00012(log) -> None:
    """
    Function
    - log.config
    - log.commit()

    Test
    - fail_json is called if dictConfig raises a ValueError
    """
    match = "error configuring logging from dict. "
    match += "detail: dictionary doesn't specify a version"

    with does_not_raise():
        instance = log

    instance.config = {}
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_log_00013(log) -> None:
    """
    Function
    - log.config
    - log.commit()

    Test
    - fail_json is called if config file doesn't exist
    """
    match = "error reading logging config from "
    match += r"\/foo\/bar\/baz\/loony\.json\. "
    match += r"detail: \[Errno 2\] No such file or directory: "
    match += r"'\/foo\/bar\/baz\/loony\.json'"

    with does_not_raise():
        instance = log

    instance.config = "/foo/bar/baz/loony.json"
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()
