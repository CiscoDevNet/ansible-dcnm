#!/usr/bin/python
#
# Copyright (c) 2021 Cisco and/or its affiliates.
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.ansible.netcommon.tests.unit.compat.mock import patch

from ansible_collections.cisco.dcnm.plugins.httpapi import dcnm
from ansible.plugins.httpapi import HttpApiBase

import pytest
import io

__copyright__ = "Copyright (c) 2021 Cisco and/or its affiliates."
__author__ = "Mike Wiebe"


class MockConnection():
    '''Mock the connection object used by httpapi'''

    def __init__(self):
        self._auth = None

    def get_option(self, opt):
        value = None
        if opt == "persistent_connect_timeout":
            value = 1000

        return value

    def send(self, path, data, method, headers, force_basic_auth):
        response = {}
        raw_data = '{"Dcnm-Token":"b9+AJS1rRaFdSq/LNR8tHGwrTJBXO4vZRhm/FBz3mEYecNPLgPdo+DszThfCA7/Ir0utevQKRitVS2KRGc0t1tavaH1wz+C2e5+zTFkAupLD"}'
        response_data = io.BytesIO(raw_data.encode('utf-8'))

        return response, response_data


def test_init():
    httpapi_obj = dcnm.HttpApi('connection')
    assert httpapi_obj.headers['Content-Type'] == "application/json"
    assert httpapi_obj.txt_headers['Content-Type'] == "text/plain"
    assert httpapi_obj.version is None


def test_get_set_version():
    httpapi_obj = dcnm.HttpApi(MockConnection())
    assert httpapi_obj.get_version() is None

    httpapi_obj.set_version('11')
    assert httpapi_obj.get_version() == '11'


def test_login_old():
    # import pdb
    # pdb.set_trace()
    httpapi_obj = dcnm.HttpApi(MockConnection())
    httpapi_obj._login_old('admin', 'password', 'POST', '/path')
