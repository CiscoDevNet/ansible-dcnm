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
__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect
import json
import logging
from logging.config import dictConfig
from os import environ


class Log:
    """
    ### Summary
    Create the base dcnm logging object.

    ### Raises
    -   ``ValueError`` if:
            -   An error is encountered reading the logging config file.
            -   An error is encountered parsing the logging config file.
            -   An invalid handler is found in the logging config file.
                    -   Valid handlers are listed in self.valid_handlers,
                        which currently contains: "file".
            -   No formatters are found in the logging config file that
                are associated with the configured handlers.
    -   ``TypeError`` if:
            -   ``develop`` is not a boolean.

    ### Usage

    By default, Log() does the following:

    1.  Reads the environment variable ``NDFC_LOGGING_CONFIG`` to determine
        the path to the logging config file.  If the environment variable is
        not set, then logging is disabled.
    2.  Sets ``develop`` to False.  This disables exceptions raised by the
        logging module itself.

    Hence, the simplest usage for Log() is:

    -   Set the environment variable ``NDFC_LOGGING_CONFIG`` to the
        path of the logging config file.  ``bash`` shell is used in the
        example below.

    ```bash
    export NDFC_LOGGING_CONFIG="/path/to/logging_config.json"
    ```

    -   Instantiate a Log() object instance and call ``commit()`` on the instance:

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.log_v2 import Log
    try:
        log = Log()
        log.commit()
    except ValueError as error:
        # handle error
    ```

    To later disable logging, unset the environment variable.
    ``bash`` shell is used in the example below.

    ```bash
    unset NDFC_LOGGING_CONFIG
    ```

    To enable exceptions from the logging module (not recommended, unless needed for
    development), set ``develop`` to True:

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.log_v2 import Log
    try:
        log = Log()
        log.develop = True
        log.commit()
    except ValueError as error:
        # handle error
    ```

    To directly set the path to the logging config file, overriding the
    ``NDFC_LOGGING_CONFIG`` environment variable, set the ``config``
    property prior to calling ``commit()``:

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.log_v2 import Log
    try:
        log = Log()
        log.config = "/path/to/logging_config.json"
        log.commit()
    except ValueError as error:
        # handle error
    ```

    At this point, a base/parent logger is created for which all other
    loggers throughout the dcnm collection will be children.
    This allows for a single logging config to be used for all modules in the
    collection, and allows for the logging config to be specified in a
    single place external to the code.

    ### Example module code using the Log() object

    In the main() function of a module.
    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.common.log_v2 import Log

    def main():
        try:
            log = Log()
            log.commit()
        except ValueError as error:
            ansible_module.fail_json(msg=str(error))

        task = AnsibleTask()
    ```

    In the AnsibleTask() class (or any other classes running in the
    main() function's call stack i.e. classes instantiated in either
    main() or in AnsibleTask()).

    ```python
    class AnsibleTask:
        def __init__(self):
            self.class_name = self.__class__.__name__
            self.log = logging.getLogger(f"dcnm.{self.class_name}")
        def some_method(self):
            self.log.debug("This is a debug message.")
    ```

    ### Logging Config File
    The logging config file MUST conform to ``logging.config.dictConfig``
    from Python's standard library and MUST NOT contain any handlers or
    that log to stdout or stderr.  The logging config file MUST only
    contain handlers that log to files.

    An example logging config file is shown below:

    ```json
    {
        "version": 1,
        "formatters": {
            "standard": {
                "class": "logging.Formatter",
                "format": "%(asctime)s - %(levelname)s - [%(name)s.%(funcName)s.%(lineno)d] %(message)s"
            }
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "level": "DEBUG",
                "filename": "/tmp/dcnm.log",
                "mode": "a",
                "encoding": "utf-8",
                "maxBytes": 50000000,
                "backupCount": 4
            }
        },
        "loggers": {
            "dcnm": {
                "handlers": [
                    "file"
                ],
                "level": "DEBUG",
                "propagate": false
            }
        },
        "root": {
            "level": "INFO",
            "handlers": [
                "file"
            ]
        }
    }
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        # Disable exceptions raised by the logging module.
        # Set this to True during development to catch logging errors.
        logging.raiseExceptions = False

        self.valid_handlers = set()
        self.valid_handlers.add("file")

        self._build_properties()

    def _build_properties(self) -> None:
        self.properties = {}
        self.properties["config"] = environ.get("NDFC_LOGGING_CONFIG", None)
        self.properties["develop"] = False

    def disable_logging(self):
        """
        ### Summary
        -   Disable logging by removing all handlers from the base logger.

        ### Raises
        None
        """
        logger = logging.getLogger()
        for handler in logger.handlers.copy():
            try:
                logger.removeHandler(handler)
            except ValueError:  # if handler already removed
                pass
        logger.addHandler(logging.NullHandler())
        logger.propagate = False

    def enable_logging(self):
        """
        ### Summary
        -   Enable logging by reading the logging config file and configuring
            the base logger instance.
        ### Raises
        -   ``ValueError`` if:
                -   An error is encountered reading the logging config file.
        """
        if str(self.config).strip() == "":
            return

        try:
            with open(self.config, "r", encoding="utf-8") as file:
                try:
                    logging_config = json.load(file)
                except json.JSONDecodeError as error:
                    msg = f"error parsing logging config from {self.config}. "
                    msg += f"Error detail: {error}"
                    raise ValueError(msg) from error
        except IOError as error:
            msg = f"error reading logging config from {self.config}. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

        try:
            self.validate_logging_config(logging_config)
        except ValueError as error:
            raise ValueError(str(error)) from error

        try:
            dictConfig(logging_config)
        except (RuntimeError, TypeError, ValueError) as error:
            msg = "logging.config.dictConfig: "
            msg += f"Unable to configure logging from {self.config}. "
            msg += f"Error detail: {error}"
            raise ValueError(msg) from error

    def validate_logging_config(self, logging_config: dict) -> None:
        """
        ### Summary
        -   Validate the logging config file.
        -   Ensure that the logging config file does not contain any handlers
            that log to console, stdout, or stderr.

        ### Raises
        -   ``ValueError`` if:
                -   The logging config file contains no handlers.
                -   The logging config file contains a handler other than
                    the handlers listed in self.valid_handlers (see class
                    docstring).

        ### Usage
        ```python
        log = Log()
        log.config = "/path/to/logging_config.json"
        log.commit()
        ```
        """
        if len(logging_config.get("handlers", {})) == 0:
            msg = "logging.config.dictConfig: "
            msg += "No file handlers found. "
            msg += "Add a file handler to the logging config file "
            msg += f"and try again: {self.config}"
            raise ValueError(msg)
        bad_handlers = []
        for handler in logging_config.get("handlers", {}):
            if handler not in self.valid_handlers:
                msg = "logging.config.dictConfig: "
                msg += "handlers found that may interrupt Ansible module "
                msg += "execution. "
                msg += "Remove these handlers from the logging config file "
                msg += "and try again. "
                bad_handlers.append(handler)
        if len(bad_handlers) > 0:
            msg += f"Handlers: {','.join(bad_handlers)}. "
            msg += f"Logging config file: {self.config}."
            raise ValueError(msg)

    def commit(self):
        """
        ### Summary
        -   If ``config`` is None, disable logging.
        -   If ``config`` is a JSON file conformant with
            ``logging.config.dictConfig``, read the file and configure the
            base logger instance from the file's contents.

        ### Raises
        -   ``ValueError`` if:
                -   An error is encountered reading the logging config file.

        ### Notes
        1.  If self.config is None, then logging is disabled.
        2.  If self.config is a path to a JSON file, then the file is read
            and logging is configured from the file.

        ### Usage
        ```python
        log = Log()
        log.config = "/path/to/logging_config.json"
        log.commit()
        ```
        """
        if self.config is None:
            self.disable_logging()
        else:
            self.enable_logging()

    @property
    def config(self):
        """
        ### Summary
        Path to a JSON file from which logging config is read.
        JSON file must conform to ``logging.config.dictConfig`` from Python's
        standard library.

        ### Default
        If the environment variable ``NDFC_LOGGING_CONFIG`` is set, then
        the value of that variable is used.  Otherwise, None.

        The environment variable can be overridden by directly setting
        ``config`` to one of the following prior to calling ``commit()``:

        1.  None.  Logging will be disabled.
        2.  Path to a JSON file from which logging config is read.
            Must conform to ``logging.config.dictConfig`` from Python's
            standard library.
        """
        return self.properties["config"]

    @config.setter
    def config(self, value):
        self.properties["config"] = value

    @property
    def develop(self):
        """
        ### Summary
        Disable or enable exceptions raised by the logging module.

        ### Default
        False

        ### Valid Values
        -   ``True``:  Exceptions will be raised by the logging module.
        -   ``False``: Exceptions will not be raised by the logging module.
        """
        return self.properties["develop"]

    @develop.setter
    def develop(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: Expected boolean for develop. "
            msg += f"Got: type {type(value).__name__} for value {value}."
            raise TypeError(msg)
        self.properties["develop"] = value
        logging.raiseExceptions = value
