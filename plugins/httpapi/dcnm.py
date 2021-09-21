#!/usr/bin/python
#
# Copyright (c) 2020 Cisco and/or its affiliates.
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: Mike Wiebe (mikewiebe)
httpapi: dcnm
short_description: Ansible DCNM HTTPAPI Plugin.
description:
  - This DCNM plugin provides the HTTPAPI transport methods needed to initiate
    a connection to the DCNM controller, send API requests and process the
    respsonse from the controller.
version_added: "0.9.0"
"""

import json
import requests

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.plugins.httpapi import HttpApiBase

# Remove later
import inspect

import datetime


def logit(msg):
    with open('/tmp/alog.txt', 'a') as of:
        d = datetime.datetime.now().replace(microsecond=0).isoformat()
        of.write("---- %s ----\n%s\n" % (d, msg))


class HttpApi(HttpApiBase):

    def __init__(self, *args, **kwargs):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        super(HttpApi, self).__init__(*args, **kwargs)
        self.headers = {
            'Content-Type': "application/json"
        }
        self.txt_headers = {
            'Content-Type': "text/plain"
        }

    def _login_old(self, username, password, method, path):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        ''' DCNM Helper Function to login to DCNM version 11.
        '''
        # Ansible expresses the persistent_connect_timeout in seconds.
        # This value needs to be converted to milliseconds for DCNM
        timeout = self.connection.get_option("persistent_connect_timeout") * 1000
        data = "{'expirationTime': %s}" % timeout

        try:
            response, response_data = self.connection.send(path, data, method=method, headers=self.headers, force_basic_auth=True)
            response_value = self._get_response_value(response_data)
            self.connection._auth = {'Dcnm-Token': self._response_to_json(response_value)['Dcnm-Token']}
            self.login_succeeded = True
            logit('Old Auth: {}'.format(self.connection._auth))
            logit('Login Succeeded: {}'.format(self.login_succeeded))

        except Exception as e:
            logit('Attempt old login - FAILED')
            self.fail_msg.append('Error on attempt to connect and authenticate with DCNM controller: {}'.format(e))

    def _login_latest(self, username, password, method, path):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        ''' Nexus Dashboard NDFC Helper Function to login to NDFC version 12 or later.
        '''
        login_domain = 'DefaultAuth'
        # login_domain = 'local'
        payload = {'username': self.connection.get_option('remote_user'), 'password': self.connection.get_option('password'), 'domain': login_domain}
        data = json.dumps(payload)
        try:
            response, response_data = self.connection.send(path, data, method=method, headers=self.headers)
            self.connection._auth = {'Authorization': 'Bearer {0}'.format(self._response_to_json12(response_data).get('token'))}
            self.login_succeeded = True
            logit('New Auth: {}'.format(self.connection._auth))
            logit('Login Succeeded: {}'.format(self.login_succeeded))

        except Exception as e:
            logit('Attempt latest login - FAILED')
            self.fail_msg.append('Error on attempt to connect and authenticate with NDFC controller: {}'.format(e))

    def login(self, username, password):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        ''' DCNM/NDFC Login Method.  This method is automatically called by the
            Ansible plugin architecture if an active Token is not already
            available.
        '''
        self.login_succeeded = False
        self.fail_msg = []
        method = 'POST'
        path = {'dcnm': '/rest/logon', 'ndfc': '/login'}

        # Attempt to login to DCNM version 11
        self._login_old(username, password, method, path['dcnm'])

        # If login attempt failed then try NDFC version 12
        if not self.login_succeeded:
            self._login_latest(username, password, method, path['ndfc'])

        # If both login attemps fail, raise ConnectionError
        if not self.login_succeeded:
            raise ConnectionError(self._return_info(None, method, path, self.fail_msg))

    def _logout_old(self, method, path):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        logit('_logout_old Auth: {}'.format(self.connection._auth))

        try:
            logit('Attempt old logout')
            response, response_data = self.connection.send(path, self.connection._auth['Dcnm-Token'], method=method, headers=self.headers, force_basic_auth=True)
            self.logout_succeeded = True
            logit('Attempt old logout - succeeded')

        except Exception as e:
            logit('Attemp old logout - FAILED')
            self.fail_msg.append('Error on attempt to logout from DCNM controller: {}'.format(e))

    def _logout_latest(self, method, path):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        logit('_logout_latest Auth: {}'.format(self.connection._auth))
        try:
            logit('Attemp latest logout')
            response, response_data = self.connection.send(path, {}, method=method, headers=self.headers)
            self.logout_succeeded = True
            logit('Attempt latest logout - succeeded')

        except Exception as e:
            logit('Attemp latest logout - FAILED')
            self.fail_msg.append('Error on attempt to logout from NDFC controller: {}'.format(e))

    def logout(self):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        if self.connection._auth is None:
            logit('Cookie is not set, so no need to log out')
            return

        self.logout_succeeded = False
        self.fail_msg = []
        method = 'POST'
        path = {'dcnm': '/rest/logout', 'ndfc': '/logout'}

        # Attempt to logout of DCNM version 11
        self._logout_old(method, path['dcnm'])

        # If logout attempt failed then try NDFC version 12
        if not self.logout_succeeded:
            self._logout_latest(method, path['ndfc'])

        # If both login attemps fail, raise ConnectionError
        if not self.logout_succeeded:
            logit('NOTE: LOGOUT FAILED - {}'.format(self.fail_msg))
            raise ConnectionError(self._return_info(None, method, path, self.fail_msg))

        logit('logout, setting auth to none')
        self.connection._auth = None

    def check_url_connection(self):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        # Verify HTTPS request URL for DCNM controller is accessible
        try:
            requests.head(self.connection._url, verify=False)
        except requests.exceptions.RequestException as e:
            msg = """

                  Please verify that the DCNM controller HTTPS URL ({}) is
                  reachable from the Ansible controller and try again

                  """.format(self.connection._url)
            raise ConnectionError(str(e) + msg)

    def send_request(self, method, path, json=None):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        ''' This method handles all DCNM REST API requests other then login '''

        if json is None:
            json = {}

        self.check_url_connection()

        try:
            # Perform some very basic path input validation.
            path = str(path)
            if path[0] != '/':
                msg = 'Value of <path> does not appear to be formated properly'
                raise ConnectionError(self._return_info(None, method, path, msg))
            response, rdata = self.connection.send(path, json, method=method, headers=self.headers, force_basic_auth=True)
            return self._verify_response(response, method, path, rdata)
        except Exception as e:
            eargs = e.args[0]
            if isinstance(eargs, dict) and eargs.get('METHOD'):
                return eargs
            raise ConnectionError(str(e))

    def send_txt_request(self, method, path, txt=None):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        ''' This method handles all DCNM REST API requests other then login '''
        if txt is None:
            txt = ''

        self.check_url_connection()

        try:
            # Perform some very basic path input validation.
            path = str(path)
            if path[0] != '/':
                msg = 'Value of <path> does not appear to be formated properly'
                raise ConnectionError(self._return_info(None, method, path, msg))
            response, rdata = self.connection.send(path, txt, method=method,
                                                   headers=self.txt_headers,
                                                   force_basic_auth=True)
            return self._verify_response(response, method, path, rdata)
        except Exception as e:
            eargs = e.args[0]
            if isinstance(eargs, dict) and eargs.get('METHOD'):
                return eargs
            raise ConnectionError(str(e))

    def _verify_response(self, response, method, path, rdata):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        ''' Process the return code and response object from DCNM '''

        rv = self._get_response_value(rdata)
        jrd = self._response_to_json(rv)
        rc = response.getcode()
        path = response.geturl()
        msg = response.msg
        if rc >= 200 and rc <= 299:
            return self._return_info(rc, method, path, msg, jrd)
        if rc >= 400:
            # Add future error code processing here
            pass
        else:
            msg = 'Unknown RETURN_CODE: {}'.format(rc)
        raise ConnectionError(self._return_info(rc, method, path, msg, jrd))

    def _get_response_value(self, response_data):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        ''' Extract string data from response_data returned from DCNM '''
        return to_text(response_data.getvalue())

    def _response_to_json(self, response_text):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        ''' Convert response_text to json format '''
        try:
            return json.loads(response_text) if response_text else {}
        # JSONDecodeError only available on Python 3.5+
        except ValueError:
            return 'Invalid JSON response: {}'.format(response_text)

    def _response_to_json12(self, response_text):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        ''' Convert response_text to json format '''

        try:
            response_value = response_text.getvalue()
        except Exception:
            response_value = response_text
        response_text = to_text(response_value)

        try:
            return json.loads(response_text) if response_text else {}
        # # JSONDecodeError only available on Python 3.5+
        except ValueError:
            return 'Invalid JSON response: {}'.format(response_text)

    def _return_info(self, rc, method, path, msg, json_respond_data=None):
        logmsg = 'FUNCTION {}'.format(inspect.stack()[0][3])
        logit(logmsg)
        ''' Format success/error data and return with consistent format '''

        info = {}
        info['RETURN_CODE'] = rc
        info['METHOD'] = method
        info['REQUEST_PATH'] = path
        info['MESSAGE'] = msg
        info['DATA'] = json_respond_data

        return info
