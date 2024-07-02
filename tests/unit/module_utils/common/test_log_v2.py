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

import inspect
import json
import logging
from os import environ

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.log_v2 import \
    Log
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    does_not_raise


def logging_config(logging_config_file) -> dict:
    """
    ### Summary
    Return a logging configuration conformant with logging.config.dictConfig.
    """
    return {
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
                "filename": logging_config_file,
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


def test_log_v2_00010(tmp_path) -> None:
    """
    ### Methods
    -   Log().commit()

    ### Test
    -   Happy path.
    -   log.<level> logs to the logfile.
    -   The log message contains the calling method's name.
    """
    method_name = inspect.stack()[0][3]
    log_dir = tmp_path / "log_dir"
    log_dir.mkdir()
    config_file = log_dir / "logging_config.json"
    log_file = log_dir / "dcnm.log"
    config = logging_config(str(log_file))
    with open(config_file, "w", encoding="UTF-8") as fp:
        json.dump(config, fp)

    environ["NDFC_LOGGING_CONFIG"] = str(config_file)

    with does_not_raise():
        instance = Log()
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
    assert logging.getLevelName(log.getEffectiveLevel()) == "DEBUG"
    assert info_msg in log_file.read_text(encoding="UTF-8")
    assert debug_msg in log_file.read_text(encoding="UTF-8")
    assert warning_msg in log_file.read_text(encoding="UTF-8")
    assert critical_msg in log_file.read_text(encoding="UTF-8")
    # test that the log message includes the method name
    assert method_name in log_file.read_text(encoding="UTF-8")


def test_log_v2_00100(tmp_path) -> None:
    """
    ### Methods
    -   Log().commit()

    ### Test
    -   Nothing is logged when NDFC_LOGGING_CONFIG is not set
    """
    log_dir = tmp_path / "log_dir"
    log_dir.mkdir()
    config_file = log_dir / "logging_config.json"
    log_file = log_dir / "dcnm.log"
    config = logging_config(str(log_file))
    with open(config_file, "w", encoding="UTF-8") as fp:
        json.dump(config, fp)

    with does_not_raise():
        instance = Log()
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
    # test that nothing was logged (file was not created)
    with pytest.raises(FileNotFoundError):
        log_file.read_text(encoding="UTF-8")


@pytest.mark.parametrize("env_var", [(""), ("   ")])
def test_log_v2_00110(tmp_path, env_var) -> None:
    """
    ### Methods
    -   Log().commit()

    ### Test
    -   Nothing is logged when NDFC_LOGGING_CONFIG is set to an
        an empty string.
    """
    log_dir = tmp_path / "log_dir"
    log_dir.mkdir()
    config_file = log_dir / "logging_config.json"
    log_file = log_dir / "dcnm.log"
    config = logging_config(str(log_file))
    with open(config_file, "w", encoding="UTF-8") as fp:
        json.dump(config, fp)

    environ["NDFC_LOGGING_CONFIG"] = env_var

    with does_not_raise():
        instance = Log()
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
    # test that nothing was logged (file was not created)
    with pytest.raises(FileNotFoundError):
        log_file.read_text(encoding="UTF-8")


def test_log_v2_00120(tmp_path) -> None:
    """
    ### Methods
    -   Log().commit()

    ### Test Setup
    -   NDFC_LOGGING_CONFIG is set to a file that exists,
        which would normally enable logging.
    -   Log().config is set to None, which overrides NDFC_LOGGING_CONFIG.

    ### Test
    -   Nothing is logged becase Log().config overrides NDFC_LOGGING_CONFIG.
    """
    log_dir = tmp_path / "log_dir"
    log_dir.mkdir()
    config_file = log_dir / "logging_config.json"
    log_file = log_dir / "dcnm.log"
    config = logging_config(str(log_file))
    with open(config_file, "w", encoding="UTF-8") as fp:
        json.dump(config, fp)

    environ["NDFC_LOGGING_CONFIG"] = str(config_file)

    with does_not_raise():
        instance = Log()
        instance.config = None
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
    # test that nothing was logged (file was not created)
    with pytest.raises(FileNotFoundError):
        log_file.read_text(encoding="UTF-8")


def test_log_v2_00200() -> None:
    """
    ### Methods
    - Log().commit()

    ### Test
    -   ``ValueError`` is raised if logging config file does not exist.
    """
    config_file = "DOES_NOT_EXIST.json"
    environ["NDFC_LOGGING_CONFIG"] = config_file

    with does_not_raise():
        instance = Log()

    match = rf"error reading logging config from {config_file}\.\s+"
    match += r"Error detail:\s+\[Errno 2\]\s+No such file or directory:\s+"
    match += rf"\'{config_file}\'"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_log_v2_00210(tmp_path) -> None:
    """
    ### Methods
    - Log().commit()

    ### Test
    -   ``ValueError`` is raised if logging config file contains invalid JSON.
    """
    log_dir = tmp_path / "log_dir"
    log_dir.mkdir()
    config_file = log_dir / "logging_config.json"
    with open(config_file, "w", encoding="UTF-8") as fp:
        json.dump({"BAD": "JSON"}, fp)

    environ["NDFC_LOGGING_CONFIG"] = str(config_file)

    with does_not_raise():
        instance = Log()

    match = r"logging.config.dictConfig:\s+"
    match += r"No file handlers found\.\s+"
    match += r"Add a file handler to the logging config file\s+"
    match += rf"and try again: {config_file}"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_log_v2_00220(tmp_path) -> None:
    """
    ### Methods
    - Log().commit()

    ### Test
    -   ``ValueError`` is raised if logging config file does not contain JSON.
    """
    log_dir = tmp_path / "log_dir"
    log_dir.mkdir()
    config_file = log_dir / "logging_config.json"
    with open(config_file, "w", encoding="UTF-8") as fp:
        fp.write("NOT JSON")

    environ["NDFC_LOGGING_CONFIG"] = str(config_file)

    with does_not_raise():
        instance = Log()

    match = rf"error parsing logging config from {config_file}\.\s+"
    match += r"Error detail: Expecting value: line 1 column 1 \(char 0\)"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_log_v2_00230(tmp_path) -> None:
    """
    ### Methods
    -   Log().commit()

    ### Test
    -   ``ValueError`` is raised if logging config file contains
        handler(s) that emit to non-file destinations.
    """
    log_dir = tmp_path / "log_dir"
    log_dir.mkdir()
    config_file = log_dir / "logging_config.json"
    log_file = log_dir / "dcnm.log"
    config = logging_config(str(log_file))
    config["handlers"]["console"] = {
        "class": "logging.StreamHandler",
        "formatter": "standard",
        "level": "DEBUG",
        "stream": "ext://sys.stdout",
    }
    with open(config_file, "w", encoding="UTF-8") as fp:
        json.dump(config, fp)

    environ["NDFC_LOGGING_CONFIG"] = str(config_file)

    with does_not_raise():
        instance = Log()

    match = r"logging.config.dictConfig:\s+"
    match += r"handlers found that may interrupt Ansible module\s+"
    match += r"execution\.\s+"
    match += r"Remove these handlers from the logging config file and\s+"
    match += r"try again\.\s+"
    match += r"Handlers:\s+.*\.\s+"
    match += r"Logging config file:\s+.*\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_log_v2_00240(tmp_path) -> None:
    """
    ### Methods
    -   Log().commit()

    ### Test
    -   ``ValueError`` is raised if logging config file does not
        contain any handlers.

    ### NOTES:
    -   test_log_v2_00210, raises the same error message in the case where
        the logging config file contains JSON that is not conformant with
        dictConfig.
    """
    log_dir = tmp_path / "log_dir"
    log_dir.mkdir()
    config_file = log_dir / "logging_config.json"
    log_file = log_dir / "dcnm.log"
    config = logging_config(str(log_file))
    del config["handlers"]
    with open(config_file, "w", encoding="UTF-8") as fp:
        json.dump(config, fp)

    environ["NDFC_LOGGING_CONFIG"] = str(config_file)

    with does_not_raise():
        instance = Log()

    match = r"logging.config.dictConfig:\s+"
    match += r"No file handlers found\.\s+"
    match += r"Add a file handler to the logging config file\s+"
    match += rf"and try again: {config_file}"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_log_v2_00250(tmp_path) -> None:
    """
    ### Methods
    -   Log().commit()

    ### Test
    -   ``ValueError`` is raised if logging config file does not
        contain any formatters or contains formatters that are not
        associated with handlers.
    """
    log_dir = tmp_path / "log_dir"
    log_dir.mkdir()
    config_file = log_dir / "logging_config.json"
    log_file = log_dir / "dcnm.log"
    config = logging_config(str(log_file))
    del config["formatters"]
    with open(config_file, "w", encoding="UTF-8") as fp:
        json.dump(config, fp)

    environ["NDFC_LOGGING_CONFIG"] = str(config_file)

    with does_not_raise():
        instance = Log()

    match = r"logging.config.dictConfig:\s+"
    match += r"Unable to configure logging from\s+.*\.\s+"
    match += r"Error detail: Unable to configure handler.*"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_log_v2_00300() -> None:
    """
    ### Methods
    -   Log().develop (setter)

    ### Test
    -   ``TypeError`` is raised if develop is set to a non-bool.
    """
    with does_not_raise():
        instance = Log()

    match = r"Log\.develop:\s+"
    match += r"Expected boolean for develop\.\s+"
    match += r"Got: type str for value FOO\."
    with pytest.raises(TypeError, match=match):
        instance.develop = "FOO"


@pytest.mark.parametrize("develop", [(True), (False)])
def test_log_v2_00310(develop) -> None:
    """
    ### Methods
    -   Log().develop (setter)

    ### Test
    -   develop is set correctly if passed a bool.
    -   No exceptions are raised.
    """
    with does_not_raise():
        instance = Log()
        instance.develop = develop
    assert instance.develop == develop
