# Copyright (c) 2020-2023 Cisco and/or its affiliates.
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


class HttpApi(HttpApiBase):
    def __init__(self, *args, **kwargs):
        super(HttpApi, self).__init__(*args, **kwargs)
        self.headers = {"Content-Type": "application/json"}
        self.txt_headers = {"Content-Type": "text/plain"}
        self.version = None
        # Retry count for send API
        self.retrycount = 5

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

    def _login_old(self, username, password, method, path):
        """DCNM Helper Function to login to DCNM version 11."""
        # Ansible expresses the persistent_connect_timeout in seconds.
        # This value needs to be converted to milliseconds for DCNM
        timeout = self.connection.get_option("persistent_connect_timeout") * 1000
        data = "{'expirationTime': %s}" % timeout

        try:
            response, response_data = self.connection.send(
                path, data, method=method, headers=self.headers, force_basic_auth=True
            )
            vrd = self._verify_response(response, method, path, response_data)
            if vrd["RETURN_CODE"] != 200:
                self.login_fail_msg.append(
                    "Error on attempt to connect and authenticate with DCNM controller: {0}".format(
                        vrd
                    )
                )
                return

            response_value = self._get_response_value(response_data)
            self.connection._auth = {
                "Dcnm-Token": self._response_to_json(response_value)["Dcnm-Token"]
            }
            self.login_succeeded = True
            self.set_version(11)
            self.set_token(self.connection._auth)

        except Exception as e:
            self.login_fail_msg.append(
                "Error on attempt to connect and authenticate with DCNM controller: {0}".format(
                    e
                )
            )

    def _login_latestv1(self, username, password, login_domain, method, path):
        """Nexus Dashboard NDFC Helper Function to login to NDFC version 12 or later."""
        payload = {
            "username": username,
            "password": password,
            "domain": login_domain
        }
        data = json.dumps(payload)
        try:
            response, response_data = self.connection.send(
                path, data, method=method, headers=self.headers
            )
            vrd = self._verify_response(response, method, path, response_data)
            if vrd["RETURN_CODE"] != 200:
                self.login_fail_msg.append(
                    "Error on attempt to connect and authenticate with NDFC controller: {0}".format(
                        vrd
                    )
                )
                return

            self.connection._auth = {
                "Authorization": "Bearer {0}".format(
                    self._response_to_json12(response_data).get("token")
                )
            }
            self.login_succeeded = True
            self.set_version(12)
            self.set_token(self.connection._auth)

        except Exception as e:
            self.login_fail_msg.append(
                "Error on attempt to connect and authenticate with NDFC controller: {0}".format(
                    e
                )
            )

    def _login_latestv2(self, username, password, login_domain, method, path):
        """Nexus Dashboard NDFC Helper Function to login to NDFC version 12 or later."""
        payload = {
            "userName": username,
            "userPasswd": password,
            "domain": login_domain
        }
        data = json.dumps(payload)
        try:
            response, response_data = self.connection.send(
                path, data, method=method, headers=self.headers
            )
            vrd = self._verify_response(response, method, path, response_data)
            if vrd["RETURN_CODE"] != 200:
                self.login_fail_msg.append(
                    "Error on attempt to connect and authenticate with NDFC controller: {0}".format(
                        vrd
                    )
                )
                return

            self.connection._auth = {
                "Authorization": "Bearer {0}".format(
                    self._response_to_json12(response_data).get("token")
                )
            }
            self.login_succeeded = True
            self.set_version(12)
            self.set_token(self.connection._auth)

        except Exception as e:
            self.login_fail_msg.append(
                "Error on attempt to connect and authenticate with NDFC controller: {0}".format(
                    e
                )
            )

    def login(self, username, password):
        """DCNM/NDFC Login Method.  This method is automatically called by the
        Ansible plugin architecture if an active Token is not already
        available.
        """
        self.login_succeeded = False
        self.login_fail_msg = []
        login_domain = "local"  # default login domain of Nexus Dashboard
        method = "POST"
        path = {"dcnm": "/rest/logon", "ndfc": "/login"}
        login12Func = [self._login_latestv2, self._login_latestv1]

        # Attempt to login to DCNM version 11
        self._login_old(username, password, method, path["dcnm"])

        # If login attempt failed then try NDFC version 12
        if self.get_option("login_domain") is not None:
            login_domain = self.get_option("login_domain")
        if not self.login_succeeded:
            for func in login12Func:
                func(username, password, login_domain, method, path["ndfc"])
                if self.login_succeeded:
                    break

        # If both login attemps fail, raise ConnectionError
        if not self.login_succeeded:
            raise ConnectionError(self.login_fail_msg)

    def _logout_old(self, method, path):
        try:
            response, response_data = self.connection.send(
                path,
                self.connection._auth["Dcnm-Token"],
                method=method,
                headers=self.headers,
                force_basic_auth=True,
            )
            vrd = self._verify_response(response, method, path, response_data)
            if vrd["RETURN_CODE"] != 200:
                self.logout_fail_msg.append(
                    "Error on attempt to logout from DCNM controller: {0}".format(vrd)
                )
                return

            self.logout_succeeded = True

        except Exception as e:
            self.logout_fail_msg.append(
                "Error on attempt to logout from DCNM controller: {0}".format(e)
            )

    def _logout_latest(self, method, path):
        try:
            response, response_data = self.connection.send(
                path, {}, method=method, headers=self.headers
            )
            vrd = self._verify_response(response, method, path, response_data)
            if vrd["RETURN_CODE"] != 200:
                self.logout_fail_msg.append(
                    "Error on attempt to logout from NDFC controller: {0}".format(vrd)
                )
                return

            self.logout_succeeded = True

        except Exception as e:
            self.logout_fail_msg.append(
                "Error on attempt to logout from NDFC controller: {0}".format(e)
            )

    def logout(self):
        if self.connection._auth is None:
            return

        self.logout_succeeded = False
        self.logout_fail_msg = []
        method = "POST"
        path = {"dcnm": "/rest/logout", "ndfc": "/logout"}

        if self.version == 11:
            # Logout of DCNM version 11
            self._logout_old(method, path["dcnm"])
        elif self.version >= 12:
            # Logout of DCNM version 12
            self._logout_latest(method, path["ndfc"])

        # If both login attemps fail, raise ConnectionError
        if not self.logout_succeeded:
            raise ConnectionError(self.logout_fail_msg)

        self.connection._auth = None

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

    def send_request(self, method, path, json=None):
        """This method handles all DCNM REST API requests other then login"""

        if json is None:
            json = {}

        self.check_url_connection()

        msg = '". Please verify your login credentials, access permissions and fabric details and try again '

        try:
            # Perform some very basic path input validation.
            path = str(path)
            if path[0] != "/":
                msg = "Value of <path> does not appear to be formated properly"
                raise ConnectionError(self._return_info(None, method, path, msg))
            response, rdata = self.connection.send(
                path, json, self.retrycount, method=method, headers=self.headers, force_basic_auth=True
            )
            return self._verify_response(response, method, path, rdata)
        except Exception as e:
            # In some cases netcommon raises execeptions without arguments, so check for exception args.
            if e.args:
                eargs = e.args[0]
            else:
                eargs = e
            if isinstance(eargs, dict) and eargs.get("METHOD"):
                return eargs
            raise ConnectionError(str(e) + msg)

    def send_txt_request(self, method, path, txt=None):
        """This method handles all DCNM REST API requests other then login"""
        if txt is None:
            txt = ""

        self.check_url_connection()

        msg = '". Please verify your login credentials, access permissions and fabric details and try again '

        try:
            # Perform some very basic path input validation.
            path = str(path)
            if path[0] != "/":
                msg = "Value of <path> does not appear to be formated properly"
                raise ConnectionError(self._return_info(None, method, path, msg))
            response, rdata = self.connection.send(
                path,
                txt,
                self.retrycount,
                method=method,
                headers=self.txt_headers,
                force_basic_auth=True,
            )
            return self._verify_response(response, method, path, rdata)
        except Exception as e:
            # In some cases netcommon raises execeptions without arguments, so check for exception args.
            if e.args:
                eargs = e.args[0]
            else:
                eargs = e
            if isinstance(eargs, dict) and eargs.get("METHOD"):
                return eargs
            raise ConnectionError(str(e) + msg)

    def _verify_response(self, response, method, path, rdata):
        """Process the return code and response object from DCNM"""

        rv = self._get_response_value(rdata)
        jrd = self._response_to_json(rv)
        rc = response.getcode()
        path = response.geturl()
        msg = response.msg
        # This function calls self._return_info to pass the response
        # data back in a structured dictionary format.
        # A ConnectionError is generated if the return code is unknown.
        if rc >= 200 and rc <= 600:
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
        # JSONDecodeError only available on Python 3.5+
        except ValueError:
            return "Invalid JSON response: {0}".format(response_text)

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
