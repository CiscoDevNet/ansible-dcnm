# Copyright (c) 2020-2025 Cisco and/or its affiliates.
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
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
author: Mike Wiebe (@mikewiebe)
name: dcnm
short_description: Ansible DCNM HTTPAPI Plugin.
description:
  - This DCNM plugin provides the HTTPAPI transport methods needed to initiate
    a connection to the DCNM controller, send API requests and process the
    respsonse from the controller.
version_added: "0.9.0"
options:
  login_domain:
    description:
    - The login domain name to use for user authentication
    - Only needed for NDFC
    type: string
    default: local
    env:
    - name: ANSIBLE_HTTPAPI_LOGIN_DOMAIN
    vars:
    - name: ansible_httpapi_login_domain
"""

import json

# Any third party modules should be imported as below, if not sanity tests will fail
try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.plugins.httpapi import HttpApiBase

# Constants
DCNM_VERSION = 11
NDFC_VERSION = 12
HTTP_SUCCESS_MIN = 200
HTTP_SUCCESS_MAX = 600
DEFAULT_LOGIN_DOMAIN = "local"
DEFAULT_RETRY_COUNT = 5


class HttpApi(HttpApiBase):
    def __init__(self, *args, **kwargs):
        super(HttpApi, self).__init__(*args, **kwargs)
        self.headers = {"Content-Type": "application/json", 'Transfer-Encoding': 'chunked'}
        self.urlencoded_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.txt_headers = {"Content-Type": "text/plain"}
        self.version = None
        self.retrycount = DEFAULT_RETRY_COUNT

    def get_version(self):
        return self.version

    def set_version(self, version):
        self.version = version

    # This function is used to store the authentication token information received. This will be used to build auth headers
    # when using "requests" module for uploading images whih uses multi-part-frames.
    def set_token(self, token):
        self.token = token

    def get_token(self):
        return self.token

    def _attempt_login(self, login_config):
        """Unified login method that handles different API versions and formats."""
        try:
            response, response_data = self.connection.send(
                login_config["path"], login_config["data"], method="POST", headers=self.headers, force_basic_auth=login_config.get("force_basic_auth", False)
            )

            vrd = self._verify_response(response, "POST", login_config["path"], response_data)
            if vrd["RETURN_CODE"] != 200:
                self.login_fail_msg.append("Error on attempt to authenticate with {0} controller: {1}".format(login_config["controller_type"], vrd))
                return False

            # Set authentication based on version
            if login_config["version"] == 11:
                response_value = self._get_response_value(response_data)
                token = self._response_to_json(response_value)["Dcnm-Token"]
                self.connection._auth = {"Dcnm-Token": token}
            else:  # version 12+
                token = self._response_to_json12(response_data).get("token")
                self.connection._auth = {
                    "Authorization": "Bearer {0}".format(token),
                    "Cookie": "AuthCookie={0}".format(token),
                }

            self.login_succeeded = True
            self.set_version(login_config["version"])
            self.set_token(self.connection._auth)
            return True

        except Exception as e:
            self.login_fail_msg.append("Error on attempt to authenticate with {0} controller: {1}".format(login_config["controller_type"], e))
            return False

    def login(self, username, password):
        """DCNM/NDFC Login Method. Tries different login methods in order."""
        self.login_succeeded = False
        self.login_fail_msg = []
        login_domain = self.get_option("login_domain") or "local"

        # Define login configurations in order of preference
        login_configs = [
            {
                "controller_type": "NDFC",
                "version": 12,
                "path": "/login",
                "data": json.dumps({"userName": username, "userPasswd": password, "domain": login_domain}),
                "force_basic_auth": False,
            },
            {
                "controller_type": "NDFC_Legacy",
                "version": 12,
                "path": "/login",
                "data": json.dumps({"username": username, "password": password, "domain": login_domain}),
                "force_basic_auth": False,
            },
            {
                "controller_type": "DCNM",
                "version": 11,
                "path": "/rest/logon",
                "data": "{'expirationTime': %s}" % (self.connection.get_option("persistent_connect_timeout") * 1000),
                "force_basic_auth": True,
            },
        ]

        # Try each login method
        for config in login_configs:
            if self._attempt_login(config):
                return

        # If all login attempts fail, raise ConnectionError
        raise ConnectionError(self.login_fail_msg)

    def _attempt_logout(self, logout_config):
        """Unified logout method for different API versions."""
        try:
            response, response_data = self.connection.send(
                logout_config["path"],
                logout_config["data"],
                method="POST",
                headers=self.headers,
                force_basic_auth=logout_config.get("force_basic_auth", False),
            )

            vrd = self._verify_response(response, "POST", logout_config["path"], response_data)
            if vrd["RETURN_CODE"] != 200:
                self.logout_fail_msg.append("Error on attempt to logout from {0} controller: {1}".format(logout_config["controller_type"], vrd))
                return False

            return True

        except Exception as e:
            self.logout_fail_msg.append("Error on attempt to logout from {0} controller: {1}".format(logout_config["controller_type"], e))
            return False

    def logout(self):
        """DCNM/NDFC Logout Method."""
        if self.connection._auth is None:
            return  # Already logged out

        if self.version is None:
            raise ConnectionError("Version not detected, cannot perform logout")

        self.logout_succeeded = False
        self.logout_fail_msg = []

        # Configure logout based on version
        if self.version == 11:
            logout_config = {"controller_type": "DCNM", "path": "/rest/logout", "data": self.connection._auth["Dcnm-Token"], "force_basic_auth": True}
        else:  # version 12+
            logout_config = {"controller_type": "NDFC", "path": "/logout", "data": {}, "force_basic_auth": False}

        # Attempt logout
        if self._attempt_logout(logout_config):
            self.logout_succeeded = True
            self.connection._auth = None
        else:
            error_message = "Logout failed: " + "; ".join(self.logout_fail_msg)
            raise ConnectionError(error_message)

    def check_url_connection(self):
        # Verify HTTPS request URL for DCNM controller is accessible
        try:
            requests.head(self.connection._url, verify=False)
        except requests.exceptions.RequestException as e:
            msg = """

                  Please verify that the DCNM controller HTTPS URL ({0}) is
                  reachable from the Ansible controller and try again

                  """.format(
                self.connection._url
            )
            raise ConnectionError(str(e) + msg)

    def get_url_connection(self):
        return self.connection._url

    def _send_request_internal(self, method, path, data=None, headers=None):
        """Internal method to handle common request logic."""
        self.check_url_connection()

        # Validate path
        path = str(path)
        if not path.startswith("/"):
            msg = "Value of <path> does not appear to be formatted properly"
            raise ConnectionError(self._return_info(None, method, path, msg))

        # Use provided headers or defaults
        request_headers = headers or self.headers

        try:
            response, rdata = self.connection.send(path, data, self.retrycount, method=method, headers=request_headers, force_basic_auth=True)
            return self._verify_response(response, method, path, rdata)
        except Exception as e:
            if e.args:
                eargs = e.args[0]
            else:
                eargs = e
            if isinstance(eargs, dict) and eargs.get("METHOD"):
                return eargs

            error_msg = "Please verify your login credentials, access permissions and fabric details and try again"
            raise ConnectionError(str(e) + ". " + error_msg)

    def send_request(self, method, path, json=None):
        """This method handles all DCNM REST API requests other than login"""
        return self._send_request_internal(method, path, json or {}, self.headers)

    def send_urlencoded_request(self, method, path, urlencoded=None):
        """This method handles all DCNM REST API urlencoded requests other than login"""
        return self._send_request_internal(method, path, urlencoded or {}, self.urlencoded_headers)

    def send_txt_request(self, method, path, txt=None):
        """This method handles all DCNM REST API text requests other than login"""
        return self._send_request_internal(method, path, txt or "", self.txt_headers)

    def _verify_response(self, response, method, path, rdata):
        """Process the return code and response object from DCNM"""
        rv = self._get_response_value(rdata)
        jrd = self._response_to_json(rv)
        rc = response.getcode()
        path = response.geturl()
        msg = response.msg

        # Check if return code is in acceptable range
        if HTTP_SUCCESS_MIN <= rc <= HTTP_SUCCESS_MAX:
            return self._return_info(rc, method, path, msg, jrd)
        else:
            msg = "Unknown RETURN_CODE: {0}".format(rc)
            raise ConnectionError(self._return_info(rc, method, path, msg, jrd))

    def _get_response_value(self, response_data):
        """Extract string data from response_data returned from DCNM"""
        return to_text(response_data.getvalue())

    def _response_to_json(self, response_text):
        """Convert response_text to json format"""
        try:
            return json.loads(response_text) if response_text else {}
        except json.JSONDecodeError:
            return "Invalid JSON response: {0}".format(response_text)
        except Exception as e:
            return "Error decoding JSON response: {0}".format(str(e))

    def _response_to_json12(self, response_text):
        """Convert response_text to json format"""

        try:
            response_value = response_text.getvalue()
        except Exception:
            response_value = response_text
        response_text = to_text(response_value)

        try:
            return json.loads(response_text) if response_text else {}
        # # JSONDecodeError only available on Python 3.5+
        except ValueError:
            return "Invalid JSON response: {0}".format(response_text)

    def _return_info(self, rc, method, path, msg, json_respond_data=None):
        """Format success/error data and return with consistent format"""

        info = {}
        info["RETURN_CODE"] = rc
        info["METHOD"] = method
        info["REQUEST_PATH"] = path
        info["MESSAGE"] = msg
        info["DATA"] = json_respond_data

        return info
