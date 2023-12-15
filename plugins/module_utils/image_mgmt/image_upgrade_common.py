#
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

"""
Base class for the other image upgrade classes
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import inspect
from collections.abc import MutableMapping as Map


class ImageUpgradeCommon:
    """
    Base class for the other image upgrade classes

    Usage (where module is an instance of AnsibleModule):

    class MyClass(ImageUpgradeCommon):
        def __init__(self, module):
            super().__init__(module)
        ...
    """

    def __init__(self, module):
        self.class_name = __class__.__name__
        self.method_name = inspect.stack()[0][3]

        self.module = module
        self.params = module.params
        self.debug = False
        self.fd = None
        self.logfile = "/tmp/ansible_dcnm.log"
        self.module = module
        self.log_msg("ImageUpgradeCommon.__init__ DONE")

    def _handle_response(self, response, verb):
        # don't add self.method_name to this method since
        # it is called by other methods and we want their
        # method_names in the log

        if verb == "GET":
            return self._handle_get_response(response)
        if verb in {"POST", "PUT", "DELETE"}:
            return self._handle_post_put_delete_response(response)
        return self._handle_unknown_request_verbs(response, verb)

    def _handle_unknown_request_verbs(self, response, verb):
        self.method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{self.method_name}: "
        msg += f"Unknown request verb ({verb}) for response {response}."
        self.module.fail_json(msg)

    def _handle_get_response(self, response):
        """
        Caller:
            - self._handle_response()
        Handle controller responses to GET requests
        Returns: dict() with the following keys:
        - found:
            - False, if request error was "Not found" and RETURN_CODE == 404
            - True otherwise
        - success:
            - False if RETURN_CODE != 200 or MESSAGE != "OK"
            - True otherwise
        """
        # don't add self.method_name to this method since
        # it is called by other methods and we want their
        # method_names in the log

        result = {}
        success_return_codes = {200, 404}
        if (
            response.get("RETURN_CODE") == 404
            and response.get("MESSAGE") == "Not Found"
        ):
            result["found"] = False
            result["success"] = True
            return result
        if (
            response.get("RETURN_CODE") not in success_return_codes
            or response.get("MESSAGE") != "OK"
        ):
            result["found"] = False
            result["success"] = False
            return result
        result["found"] = True
        result["success"] = True
        return result

    def _handle_post_put_delete_response(self, response):
        """
        Caller:
            - self.self._handle_response()

        Handle POST, PUT responses from the controller.

        Returns: dict() with the following keys:
        - changed:
            - True if changes were made to by the controller
            - False otherwise
        - success:
            - False if RETURN_CODE != 200 or MESSAGE != "OK"
            - True otherwise
        """
        # don't add self.method_name to this method since
        # it is called by other methods and we want their
        # method_names in the log

        result = {}
        if response.get("ERROR") is not None:
            result["success"] = False
            result["changed"] = False
            return result
        if response.get("MESSAGE") != "OK" and response.get("MESSAGE") is not None:
            result["success"] = False
            result["changed"] = False
            return result
        result["success"] = True
        result["changed"] = True
        return result

    def log_msg(self, msg):
        """
        used for debugging. disable this when committing to main
        by setting self.debug to False in __init__()
        """
        if self.debug is False:
            return
        if self.fd is None:
            try:
                # since we need self.fd open throughout several classes
                # we are disabling pylint R1732
                self.fd = open(
                    f"{self.logfile}", "a+", encoding="UTF-8"
                )  # pylint: disable=consider-using-with
            except IOError as err:
                msg = f"error opening logfile {self.logfile}. "
                msg += f"detail: {err}"
                self.module.fail_json(msg)

        self.fd.write(msg)
        self.fd.write("\n")
        self.fd.flush()

    def make_boolean(self, value):
        """
        Return value converted to boolean, if possible.
        Return value, if value cannot be converted.
        """
        self.method_name = inspect.stack()[0][3]

        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ["true", "yes"]:
                return True
            if value.lower() in ["false", "no"]:
                return False
        return value

    def make_none(self, value):
        """
        Return None if value is an empty string, or a string
        representation of a None type
        Return value otherwise
        """
        self.method_name = inspect.stack()[0][3]

        if value in ["", "none", "None", "NONE", "null", "Null", "NULL"]:
            return None
        return value

    def merge_dicts(self, dict1, dict2):
        """
        Merge dict2 into dict1 and return dict1.
        Keys in dict2 have precedence over keys in dict1.
        """
        for key in dict2:
            # self.log_msg(f"DEBUG: {self.class_name}.merge_dicts: key: {key}")

            if isinstance(dict1.get(key, None), Map) and dict2.get(key, None) is None:
                # This is to handle a case where the playbook contains an
                # options dict that is supposed to contain sub-options
                # (in the example below, 'upgrade' should contain 'nxos' and
                # 'epld'), but the dict is empty in the playbook.
                # For example, below, upgrade is specified, but upgrade.nxos
                # and upgrade.epld are not:
                #
                # -   ip_address: 172.22.150.110
                #     upgrade:
                #     options:
                #         epld:
                #             module: 27
                #             golden: false
                # In this case, we copy the entire 'upgrade' dict from dict1 to dict2
                dict2[key] = dict1[key]
            elif (
                key in dict1
                and isinstance(dict1[key], Map)
                and isinstance(dict2[key], Map)
            ):
                self.merge_dicts(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]
        return dict1
