# (c) 2020 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_vrf
from .dcnm_module import TestDcnmModule, set_module_args


class TestDcnmVrfModule(TestDcnmModule):

    module = dcnm_vrf

    def setUp(self):
        super(TestDcnmVrfModule, self).setUp()

        self.mock_dcnm_send = patch('ansible_collections.cisco.dcnm.plugins.modules.dcnm_vrf.dcnm_send')
        self.run_dcnm_send = self.mock_dcnm_send.start()

    def tearDown(self):
        super(TestDcnmVrfModule, self).tearDown()
        self.mock_dcnm_send.stop()

    def load_fixtures(self, response=None, device=''):
        create_err_resp = list([dict(ERROR='Bad Request')])
        attach_success_resp = dict({'vrf-on-switch':'SUCCESS'})
        attach_err_resp = dict({'vrf-on-switch':'Entered VRF VLAN ID 103 is in use already'})
        deploy_success_resp = dict({"status":""})

        if '_create_new' in self._testMethodName:
            self.run_dcnm_send.side_effect = [create_err_resp, dict()]
        elif '_create_duplicate' in self._testMethodName:
            self.run_dcnm_send.side_effect = [dict(vrfName='test_vrf'), dict()]
        elif '_create_with_used' in self._testMethodName:
            self.run_dcnm_send.side_effect = [create_err_resp, create_err_resp]
        elif 'attach_multiple' in self._testMethodName or 'attach_single' in self._testMethodName:
            self.run_dcnm_send.side_effect = [attach_success_resp]
        elif 'used_vlan' in self._testMethodName:
            self.run_dcnm_send.side_effect = [attach_err_resp]
        elif 'deploy' in self._testMethodName:
            self.run_dcnm_send.side_effect = [deploy_success_resp]
        else:
            pass

    def test_dcnm_vrf_create_new(self):
        set_module_args(dict(action='create', fabric='test_fabric', vrf_name='test_vrf', vrf_id=919191))
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get('changed'))

    def test_dcnm_vrf_create_duplicate(self):
        set_module_args(dict(action='create', fabric='test_fabric', vrf_name='test_vrf', vrf_id=919191))
        result = self.execute_module(changed=False, failed=False)
        self.assertFalse(result.get('changed'))

    def test_dcnm_vrf_create_with_used_vrfid(self):
        set_module_args(dict(action='create', fabric='test_fabric', vrf_name='test_vrf', vrf_id=919191))
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual(result.get('msg')[1], 'VRF ID is already in use')

    def test_dcnm_vrf_attach_single_switch(self):
        set_module_args(dict(action='attach', fabric='test_fabric', vrf_name='test_vrf',
                             deployment='False', serial_numbers_vlans=[{'947BSAMCAU1':'103'}]))
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get('changed'))

    def test_dcnm_vrf_attach_multiple_switches(self):
        set_module_args(dict(action='attach', fabric='test_fabric', vrf_name='test_vrf',
                             deployment='False', serial_numbers_vlans=[{'947BSAMCAU1':'103'},
                                                                       {'947BSAMCBV1':'104'}]))
        result = self.execute_module(changed=True, failed=False)
        self.assertTrue(result.get('changed'))

    def test_dcnm_vrf_attach_with_used_vlan(self):
        set_module_args(dict(action='attach', fabric='test_fabric', vrf_name='test_vrf',
                             deployment='False', serial_numbers_vlans=[{'947BSAMCAU1':'103'}]))
        result = self.execute_module(changed=False, failed=True)
        self.assertTrue(result.get('failed'))

    def test_dcnm_vrf_deploy(self):
        set_module_args(dict(action='deploy', fabric='test_fabric', vrf_name='test_vrf'))
        result = self.execute_module(changed=True)
        self.assertTrue(result.get('changed'))
