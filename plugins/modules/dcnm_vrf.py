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

import json
import socket
import time
import copy
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    get_fabric_inventory_details, dcnm_send, validate_list_of_dicts, \
    dcnm_get_ip_addr_info, get_ip_sn_dict
from ansible.module_utils.basic import AnsibleModule

__author__ = "Shrishail Kariyappanavar"

DOCUMENTATION = '''
---
module: dcnm_vrf
short_description: Add and remove VRFs from a DCNM managed VXLAN fabric.
version_added: "0.9.0"
description:
    - "Add and remove VRFs from a DCNM managed VXLAN fabric."
author: Shrishail Kariyappanavar(@nkshrishail)
options:
  fabric:
    description:
    - 'Name of the target fabric for vrf operations'
    type: str
    required: yes
  state:
    description:
      - The state of DCNM after module completion.
    type: str
    choices:
      - merged
      - replaced
      - overridden
      - deleted
      - query
    default: merged
  config:
    description: 'List of details of vrfs being managed'
    type: list
    elements: dict
    required: true
    note: Not required for state deleted
    suboptions:
      vrf_name:
        description: 'Name of the vrf being managed'
        type: str
        required: true
      vrf_id:
        description: 'ID of the vrf being managed'
        type: int
        required: true
      vrf_template:
        description: 'Name of the config template to be used'
        type: str
        default: 'Default_VRF_Universal'
      vrf_extension_template:
        description: 'Name of the extension config template to be used'
        type: str
        default: 'Default_VRF_Extension_Universal'
      service_vrf_template:
        description: 'Service vrf template'
        type: str
        default: None
      suboptions:
        attach:
          description: 'List of vrf attachment details'
          type: list
          elements: dict
        deploy:
          description: 'Global knob to control whether to deploy the attachment'
          type: bool
          default: true
          suboptions:
            ip_address:
              description: 'IP address of the switch where vrf will be attached or detached'
              type: ipv4
              required: true
            vlan_id:
              description: 'vlan ID for the vrf attachment'
              type: int
              required: true
            deploy:
              description: 'Per switch knob to control whether to deploy the attachment'
              type: bool
              default: true
'''

EXAMPLES = '''
This module supports the following states:

Merged:
  VRFs defined in the playbook will be merged into the target fabric.
    - If the VRF does not exist it will be added.
    - If the VRF exists but properties managed by the playbook are different
      they will be updated if possible.
    - VRFs that are not specified in the playbook will be untouched.

Replaced:
  VRFs defined in the playbook will be replaced in the target fabric.
    - If the VRF does not exist it will be added.
    - If the VRF exists but properties managed by the playbook are different
      they will be updated if possible.
    - Properties that can be managed by the module but are  not specified
      in the playbook will be deleted or defaulted if possible.
    - VRFs that are not specified in the playbook will be untouched.

Overridden:
  VRFs defined in the playbook will be overridden in the target fabric.
    - If the VRF does not exist it will be added.
    - If the VRF exists but properties managed by the playbook are different
      they will be updated if possible.
    - Properties that can be managed by the module but are not specified
      in the playbook will be deleted or defaulted if possible.
    - VRFs that are not specified in the playbook will be deleted.

Deleted:
  VRFs defined in the playbook will be deleted.
  If no VRFs are provided in the playbook, all VRFs present on that DCNM fabric will be deleted.

Query:
  Returns the current DCNM state for the VRFs listed in the playbook.

rollback functionality:
This module supports task level rollback functionality. If any task runs into failures, as part of failure
handling, the module tries to bring the state of the DCNM back to the state captured in have structure at the
beginning of the task execution. Following few lines provide a logical description of how this works,
if (failure)
    want data = have data
    have data = get state of DCNM
    Run the module in override state with above set of data to produce the required set of diffs
    and push the diff payloads to DCNM.
If rollback fails, the module does not attempt to rollback again, it just quits with appropriate error messages.

# The two VRFs below will be merged into the target fabric.
- name: Merge vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: merged
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      attach:
      - ip_address: 192.168.1.224
        vlan_id: 202
        deploy: true
      - ip_address: 192.168.1.225
        vlan_id: 203
        deploy: false
    - vrf_name: ansible-vrf-r2
      vrf_id: 9008012
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      attach:
      - ip_address: 192.168.1.224
        vlan_id: 402
      - ip_address: 192.168.1.225
        vlan_id: 403

# The two VRFs below will be replaced in the target fabric.
- name: Replace vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: replaced
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      attach:
      - ip_address: 192.168.1.224
        vlan_id: 202
        deploy: true
      # Delete this attachment
      # - ip_address: 192.168.1.225
      #   vlan_id: 203
      # deploy: true
      # Create the following attachment
      - ip_address: 192.168.1.226
        vlan_id: 204
        deploy: true
    # Dont touch this if its present on DCNM
    # - vrf_name: ansible-vrf-r2
    #   vrf_id: 9008012
    #   vrf_template: Default_VRF_Universal
    #   vrf_extension_template: Default_VRF_Extension_Universal
    #   attach:
    #   - ip_address: 192.168.1.224
    #     vlan_id: 402
    #   - ip_address: 192.168.1.225
    #     vlan_id: 403

# The two VRFs below will be overridden in the target fabric.
- name: Override vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: overridden
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
      attach:
      - ip_address: 192.168.1.224
        vlan_id: 202
        deploy: true
      # Delete this attachment
      # - ip_address: 192.168.1.225
      #   vlan_id: 203
      #   deploy: true
      # Create the following attachment
      - ip_address: 192.168.1.226
        vlan_id: 204
        deploy: true
    # Delete this vrf
    # - vrf_name: ansible-vrf-r2
    #   vrf_id: 9008012
    #   vrf_template: Default_VRF_Universal
    #   vrf_extension_template: Default_VRF_Extension_Universal
    #   attach:
    #   - ip_address: 192.168.1.224
    #     vlan_id: 402
    #   - ip_address: 192.168.1.225
    #     vlan_id: 403

- name: Delete selected vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: deleted
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
    - vrf_name: ansible-vrf-r2
      vrf_id: 9008012
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal

- name: Delete all the vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: deleted

- name: Query vrfs
  cisco.dcnm.dcnm_vrf:
    fabric: vxlan-fabric
    state: query
    config:
    - vrf_name: ansible-vrf-r1
      vrf_id: 9008011
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
    - vrf_name: ansible-vrf-r2
      vrf_id: 9008012
      vrf_template: Default_VRF_Universal
      vrf_extension_template: Default_VRF_Extension_Universal
'''


class DcnmVrf:

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.fabric = module.params['fabric']
        self.config = copy.deepcopy(module.params.get('config'))
        self.check_mode = False
        self.have_create = []
        self.want_create = []
        self.diff_create = []
        # This variable is created specifically to hold all the create payloads which are missing a
        # vrfId. These payloads are sent to DCNM out of band (basically in the get_diff_merge())
        # We lose diffs for these without this variable. The content stored here will be helpful for
        # cases like "check_mode" and to print diffs[] in the output of each task.
        self.diff_create_quick = []
        self.have_attach = []
        self.want_attach = []
        self.diff_attach = []
        # diff_detach is to list all attachments of a vrf being deleted, especially for state: OVERRIDDEN
        # The diff_detach and delete operations have to happen before create+attach+deploy for vrfs being created.
        # This is specifically to address cases where VLAN from a vrf which is being deleted is used for another
        # vrf. Without this additional logic, the create+attach+deploy go out first and complain the VLAN is already
        # in use.
        self.diff_detach = []
        self.have_deploy = {}
        self.want_deploy = {}
        self.diff_deploy = {}
        self.diff_undeploy = {}
        self.diff_delete = {}
        self.diff_input_format = []
        self.query = []
        self.inventory_data = get_fabric_inventory_details(self.module, self.fabric)
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)

        self.result = dict(
            changed=False,
            diff=[],
            response=[]
        )

        self.failed_to_rollback = False
        self.WAIT_TIME_FOR_DELETE_LOOP = 5  # in seconds

    def diff_for_attach_deploy(self, want_a, have_a):

        attach_list = []

        if not want_a:
            return attach_list

        dep_vrf = False
        for want in want_a:
            found = False
            if have_a:
                for have in have_a:
                    if want['serialNumber'] == have['serialNumber']:
                        found = True

                        if bool(have['isAttached']) and bool(want['isAttached']):
                            if have['vlan'] != want['vlan']:
                                del want['isAttached']
                                attach_list.append(want)
                                continue

                        if bool(have['isAttached']) is not bool(want['isAttached']):
                            del want['isAttached']
                            attach_list.append(want)
                            continue

                        if bool(have['deployment']) is not bool(want['deployment']):
                            dep_vrf = True

            if not found:
                if bool(want['deployment']):
                    del want['isAttached']
                    attach_list.append(want)

        return attach_list, dep_vrf

    def update_attach_params(self, attach, vrf_name, deploy):

        if not attach:
            return {}

        serial = ""
        attach['ip_address'] = dcnm_get_ip_addr_info(self.module, attach['ip_address'], None, None)
        for ip, ser in self.ip_sn.items():
            if ip == attach['ip_address']:
                serial = ser

        if not serial:
            self.module.fail_json(msg='Fabric: {} does not have the switch: {}'
                                  .format(self.fabric, attach['ip_address']))

        role = self.inventory_data[attach['ip_address']].get('switchRole')
        if role.lower() == 'spine' or role.lower() == 'super spine':
            msg = 'VRFs cannot be attached to switch {} with role {}'.format(attach['ip_address'], role)
            self.module.fail_json(msg=msg)

        attach.update({'fabric': self.fabric})
        attach.update({'vrfName': vrf_name})
        attach.update({'vlan': attach.get('vlan_id')})
        attach.update({'deployment': deploy})
        attach.update({'isAttached': deploy})
        attach.update({'serialNumber': serial})
        attach.update({'extensionValues': ""})
        attach.update({'instanceValues': ""})
        attach.update({'freeformConfig': ""})
        if 'deploy' in attach:
            del attach['deploy']
        del attach['vlan_id']
        del attach['ip_address']

        return attach

    def diff_for_create(self, want, have):

        if not have:
            return {}

        create = {}
        if want['vrfId'] is not None and have['vrfId'] != want['vrfId']:
            self.module.fail_json(msg="vrf_id for vrf:{} cant be updated to a different value".format(want['vrfName']))
        elif have['serviceVrfTemplate'] != want['serviceVrfTemplate'] or \
                have['source'] != want['source'] or \
                have['vrfTemplate'] != want['vrfTemplate'] or \
                have['vrfExtensionTemplate'] != want['vrfExtensionTemplate']:

            if want['vrfId'] is None:
                # The vrf updates with missing vrfId will have to use existing
                # vrfId from the instance of the same vrf on DCNM.
                want['vrfId'] = have['vrfId']
            create = want
        else:
            pass

        return create

    def update_create_params(self, vrf):

        if not vrf:
            return vrf

        v_template = vrf.get('vrf_template', 'Default_VRF_Universal')
        ve_template = vrf.get('vrf_extension_template', 'Default_VRF_Extension_Universal')
        src = vrf.get('source', None)
        s_v_template = vrf.get('service_vrf_template', None)

        vrf_upd = {
            'fabric': self.fabric,
            'vrfName': vrf['vrf_name'],
            'vrfTemplate': v_template,
            'vrfExtensionTemplate': ve_template,
            'vrfId': vrf.get('vrf_id', None),  # vrf_id will be auto generated in get_diff_merge()
            'serviceVrfTemplate': s_v_template,
            'source': src
        }
        template_conf = {
            'vrfSegmentId': vrf.get('vrf_id', None),
            'vrfName': vrf['vrf_name']
        }
        vrf_upd.update({'vrfTemplateConfig': json.dumps(template_conf)})

        return vrf_upd

    def get_have(self):

        have_create = []
        have_deploy = {}

        curr_vrfs = ''

        method = 'GET'
        path = '/rest/top-down/fabrics/{}/vrfs'.format(self.fabric)

        vrf_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, 'query_dcnm')

        if missing_fabric or not_ok:
            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find vrfs under fabric: {}".format(self.fabric)

            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

        if not vrf_objects.get('DATA'):
            return

        for vrf in vrf_objects['DATA']:
            curr_vrfs += vrf['vrfName'] + ','

        path = '/rest/top-down/fabrics/{}/vrfs/attachments?vrf-names={}'.format(self.fabric, curr_vrfs[:-1])

        vrf_attach_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, 'query_dcnm')

        if missing_fabric or not_ok:
            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find attachments for " \
                   "vrfs: {} under fabric: {}".format(curr_vrfs[:-1], self.fabric)

            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
            return

        if not vrf_attach_objects['DATA']:
            return

        for vrf in vrf_objects['DATA']:
            t_conf = {
                'vrfSegmentId': vrf['vrfId'],
                'vrfName': vrf['vrfName']
            }

            vrf.update({'vrfTemplateConfig': json.dumps(t_conf)})
            del vrf['vrfStatus']
            have_create.append(vrf)

        upd_vrfs = ''

        for vrf_attach in vrf_attach_objects['DATA']:
            if not vrf_attach.get('lanAttachList'):
                continue
            attach_list = vrf_attach['lanAttachList']
            dep_vrf = ''
            for attach in attach_list:
                attach_state = False if attach['lanAttachState'] == "NA" else True
                deploy = attach['isLanAttached']
                if bool(deploy) and (attach['lanAttachState'] == "OUT-OF-SYNC" or
                                     attach['lanAttachState'] == "PENDING"):
                    deploy = False

                if bool(deploy):
                    dep_vrf = attach['vrfName']

                sn = attach['switchSerialNo']
                vlan = attach['vlanId']

                # The deletes and updates below are done to update the incoming dictionary format to
                # match to what the outgoing payload requirements mandate.
                # Ex: 'vlanId' in the attach section of incoming payload needs to be changed to 'vlan'
                # on the attach section of outgoing payload.

                del attach['vlanId']
                del attach['switchSerialNo']
                del attach['switchName']
                del attach['switchRole']
                del attach['ipAddress']
                del attach['lanAttachState']
                del attach['isLanAttached']
                del attach['vrfId']
                del attach['fabricName']

                attach.update({'fabric': self.fabric})
                attach.update({'vlan': vlan})
                attach.update({'serialNumber': sn})
                attach.update({'deployment': deploy})
                attach.update({'extensionValues': ""})
                attach.update({'instanceValues': ""})
                attach.update({'freeformConfig': ""})
                attach.update({'isAttached': attach_state})

            if dep_vrf:
                upd_vrfs += dep_vrf + ","

        have_attach = vrf_attach_objects['DATA']

        if upd_vrfs:
            have_deploy.update({'vrfNames': upd_vrfs[:-1]})

        self.have_create = have_create
        self.have_attach = have_attach
        self.have_deploy = have_deploy

    def get_want(self):
        want_create = []
        want_attach = []
        want_deploy = {}

        all_vrfs = ""

        if not self.config:
            return

        for vrf in self.config:
            vrf_attach = {}
            vrfs = []

            vrf_deploy = vrf.get('deploy', True)

            want_create.append(self.update_create_params(vrf))

            if not vrf.get('attach'):
                continue
            for attach in vrf['attach']:
                deploy = vrf_deploy if "deploy" not in attach else attach['deploy']
                vrfs.append(self.update_attach_params(attach,
                                                      vrf['vrf_name'],
                                                      deploy))
            if vrfs:
                vrf_attach.update({'vrfName': vrf['vrf_name']})
                vrf_attach.update({'lanAttachList': vrfs})
                want_attach.append(vrf_attach)

            all_vrfs += vrf['vrf_name'] + ","

        if all_vrfs:
            want_deploy.update({'vrfNames': all_vrfs[:-1]})

        self.want_create = want_create
        self.want_attach = want_attach
        self.want_deploy = want_deploy

    def get_diff_delete(self):

        diff_detach = []
        diff_undeploy = {}
        diff_delete = {}

        all_vrfs = ''

        if self.config:

            for want_c in self.want_create:
                if not next((have_c for have_c in self.have_create if have_c['vrfName'] == want_c['vrfName']), None):
                    continue
                diff_delete.update({want_c['vrfName']: 'DEPLOYED'})

                have_a = next((attach for attach in self.have_attach if attach['vrfName'] == want_c['vrfName']), None)

                if not have_a:
                    continue

                to_del = []
                atch_h = have_a['lanAttachList']
                for a_h in atch_h:
                    if a_h['isAttached']:
                        del a_h['isAttached']
                        a_h.update({'deployment': False})
                        to_del.append(a_h)
                if to_del:
                    have_a.update({'lanAttachList': to_del})
                    diff_detach.append(have_a)
                    all_vrfs += have_a['vrfName'] + ","
            if all_vrfs:
                diff_undeploy.update({'vrfNames': all_vrfs[:-1]})

        else:
            for have_a in self.have_attach:
                to_del = []
                atch_h = have_a['lanAttachList']
                for a_h in atch_h:
                    if a_h['isAttached']:
                        del a_h['isAttached']
                        a_h.update({'deployment': False})
                        to_del.append(a_h)
                if to_del:
                    have_a.update({'lanAttachList': to_del})
                    diff_detach.append(have_a)
                    all_vrfs += have_a['vrfName'] + ","

                diff_delete.update({have_a['vrfName']: 'DEPLOYED'})
            if all_vrfs:
                diff_undeploy.update({'vrfNames': all_vrfs[:-1]})

        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete

    def get_diff_override(self):

        all_vrfs = ''
        diff_delete = {}

        self.get_diff_replace()

        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_detach = self.diff_detach
        diff_deploy = self.diff_deploy
        diff_undeploy = self.diff_undeploy

        for have_a in self.have_attach:
            found = next((vrf for vrf in self.want_create if vrf['vrfName'] == have_a['vrfName']), None)

            to_del = []
            if not found:
                atch_h = have_a['lanAttachList']
                for a_h in atch_h:
                    if a_h['isAttached']:
                        del a_h['isAttached']
                        a_h.update({'deployment': False})
                        to_del.append(a_h)

                if to_del:
                    have_a.update({'lanAttachList': to_del})
                    diff_detach.append(have_a)
                    all_vrfs += have_a['vrfName'] + ","

                diff_delete.update({have_a['vrfName']: 'DEPLOYED'})

        if all_vrfs:
            diff_undeploy.update({'vrfNames': all_vrfs[:-1]})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete

    def get_diff_replace(self):
        all_vrfs = ''

        self.get_diff_merge()
        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_deploy = self.diff_deploy

        for have_a in self.have_attach:
            r_vrf_list = []
            h_in_w = False
            for want_a in self.want_attach:
                if have_a['vrfName'] == want_a['vrfName']:
                    h_in_w = True
                    atch_h = have_a['lanAttachList']
                    atch_w = want_a.get('lanAttachList')

                    for a_h in atch_h:
                        if not a_h['isAttached']:
                            continue
                        a_match = False

                        if atch_w:
                            for a_w in atch_w:
                                if a_h['serialNumber'] == a_w['serialNumber']:
                                    # Have is already in diff, no need to continue looking for it.
                                    a_match = True
                                    break
                        if not a_match:
                            del a_h['isAttached']
                            a_h.update({'deployment': False})
                            r_vrf_list.append(a_h)
                    break

            if not h_in_w:
                found = next((vrf for vrf in self.want_create if vrf['vrfName'] == have_a['vrfName']), None)
                if found:
                    atch_h = have_a['lanAttachList']
                    for a_h in atch_h:
                        if not bool(a_h['isAttached']):
                            continue
                        del a_h['isAttached']
                        a_h.update({'deployment': False})
                        r_vrf_list.append(a_h)

            if r_vrf_list:
                in_diff = False
                for d_attach in self.diff_attach:
                    if have_a['vrfName'] == d_attach['vrfName']:
                        in_diff = True
                        d_attach['lanAttachList'].extend(r_vrf_list)
                        break

                if not in_diff:
                    r_vrf_dict = {
                        'vrfName': have_a['vrfName'],
                        'lanAttachList': r_vrf_list
                    }
                    diff_attach.append(r_vrf_dict)
                    all_vrfs += have_a['vrfName'] + ","

        if not all_vrfs:
            self.diff_create = diff_create
            self.diff_attach = diff_attach
            self.diff_deploy = diff_deploy
            return

        if not self.diff_deploy:
            diff_deploy.update({'vrfNames': all_vrfs[:-1]})
        else:
            vrfs = self.diff_deploy['vrfNames'] + "," + all_vrfs[:-1]
            diff_deploy.update({'vrfNames': vrfs})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy

    def get_diff_merge(self):
        # Special cases:
        # 1. Auto generate vrfId if its not mentioned by user:
        #    In this case, we need to query the DCNM to get a usable ID and use it in the payload.
        #    And also, any such vrf create requests need to be pushed individually(not bulk op).

        diff_create = []
        diff_create_quick = []
        diff_attach = []
        diff_deploy = {}
        prev_vrf_id_fetched = None

        all_vrfs = ""

        for want_c in self.want_create:
            found = False
            for have_c in self.have_create:
                if want_c['vrfName'] == have_c['vrfName']:
                    found = True
                    diff = self.diff_for_create(want_c, have_c)
                    if diff:
                        diff_create.append(diff)
                    break
            if not found:
                vrf_id = want_c.get('vrfId', None)
                if vrf_id is None:
                    # vrfId is not provided by user.
                    # Need to query DCNM to fetch next available vrfId and use it here.
                    method = 'POST'
                    result = dict(
                        changed=False,
                        response=''
                    )

                    attempt = 0
                    while True or attempt < 10:
                        attempt += 1
                        path = '/rest/managed-pool/fabrics/{}/partitions/ids'.format(self.fabric)
                        vrf_id_obj = dcnm_send(self.module, method, path)

                        missing_fabric, not_ok = self.handle_response(vrf_id_obj, 'query_dcnm')

                        if missing_fabric or not_ok:
                            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
                            msg2 = "Unable to generate vrfId for vrf: {} " \
                                   "under fabric: {}".format(want_c['vrfName'], self.fabric)

                            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

                        if not vrf_id_obj['DATA']:
                            continue

                        vrf_id = vrf_id_obj['DATA'].get('partitionSegmentId')
                        if vrf_id != prev_vrf_id_fetched:
                            want_c.update({'vrfId': vrf_id})
                            template_conf = {
                                'vrfSegmentId': vrf_id,
                                'vrfName': want_c['vrfName']
                            }
                            want_c.update({'vrfTemplateConfig': json.dumps(template_conf)})
                            prev_vrf_id_fetched = vrf_id
                            break

                    if not vrf_id:
                        self.module.fail_json(msg="Unable to generate vrfId for vrf: {} "
                                                  "under fabric: {}".format(want_c['vrfName'], self.fabric))

                    create_path = '/rest/top-down/fabrics/{}/vrfs'.format(self.fabric)

                    diff_create_quick.append(want_c)

                    if self.module.check_mode:
                        continue

                    resp = dcnm_send(self.module, method, create_path,
                                     json.dumps(want_c))
                    self.result['response'].append(resp)
                    fail, self.result['changed'] = self.handle_response(resp, "create")
                    if fail:
                        self.failure(resp)

                else:
                    diff_create.append(want_c)

        for want_a in self.want_attach:
            dep_vrf = ''
            found = False
            for have_a in self.have_attach:
                if want_a['vrfName'] == have_a['vrfName']:

                    found = True
                    diff, vrf = self.diff_for_attach_deploy(want_a['lanAttachList'], have_a['lanAttachList'])

                    if diff:
                        base = want_a.copy()
                        del base['lanAttachList']
                        base.update({'lanAttachList': diff})
                        diff_attach.append(base)
                        dep_vrf = want_a['vrfName']
                    else:
                        if vrf:
                            dep_vrf = want_a['vrfName']

            if not found and want_a.get('lanAttachList'):
                atch_list = []
                for attach in want_a['lanAttachList']:
                    del attach['isAttached']
                    if bool(attach['deployment']):
                        atch_list.append(attach)
                if atch_list:
                    base = want_a.copy()
                    del base['lanAttachList']
                    base.update({'lanAttachList': atch_list})
                    diff_attach.append(base)
                    dep_vrf = want_a['vrfName']

            if dep_vrf:
                all_vrfs += dep_vrf + ","

        if all_vrfs:
            diff_deploy.update({'vrfNames': all_vrfs[:-1]})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_create_quick = diff_create_quick

    def format_diff(self):
        diff = []

        diff_create = copy.deepcopy(self.diff_create)
        diff_create_quick = copy.deepcopy(self.diff_create_quick)
        diff_attach = copy.deepcopy(self.diff_attach)
        diff_detach = copy.deepcopy(self.diff_detach)
        diff_deploy = self.diff_deploy['vrfNames'].split(",") if self.diff_deploy else []
        diff_undeploy = self.diff_undeploy['vrfNames'].split(",") if self.diff_undeploy else []

        diff_create.extend(diff_create_quick)
        diff_attach.extend(diff_detach)
        diff_deploy.extend(diff_undeploy)

        for want_d in diff_create:

            found_a = next((vrf for vrf in diff_attach if vrf['vrfName'] == want_d['vrfName']), None)

            found_c = want_d

            src = found_c['source']
            found_c.update({'vrf_name': found_c['vrfName']})
            found_c.update({'vrf_id': found_c['vrfId']})
            found_c.update({'vrf_template': found_c['vrfTemplate']})
            found_c.update({'vrf_extension_template': found_c['vrfExtensionTemplate']})
            del found_c['source']
            found_c.update({'source': src})
            found_c.update({'service_vrf_template': found_c['serviceVrfTemplate']})
            found_c.update({'attach': []})

            del found_c['fabric']
            del found_c['vrfName']
            del found_c['vrfId']
            del found_c['vrfTemplate']
            del found_c['vrfExtensionTemplate']
            del found_c['serviceVrfTemplate']
            del found_c['vrfTemplateConfig']

            if diff_deploy:
                diff_deploy.remove(found_c['vrf_name'])
            if not found_a:
                diff.append(found_c)
                continue

            attach = found_a['lanAttachList']

            for a_w in attach:
                attach_d = {}

                for k, v in self.ip_sn.items():
                    if v == a_w['serialNumber']:
                        attach_d.update({'ip_address': k})
                        break
                attach_d.update({'vlan_id': a_w['vlan']})
                attach_d.update({'deploy': a_w['deployment']})
                found_c['attach'].append(attach_d)

            diff.append(found_c)

            diff_attach.remove(found_a)

        for vrf in diff_attach:
            new_attach_dict = {}
            new_attach_list = []
            attach = vrf['lanAttachList']

            for a_w in attach:
                attach_d = {}

                for k, v in self.ip_sn.items():
                    if v == a_w['serialNumber']:
                        attach_d.update({'ip_address': k})
                        break
                attach_d.update({'vlan_id': a_w['vlan']})
                attach_d.update({'deploy': a_w['deployment']})
                new_attach_list.append(attach_d)

            if new_attach_list:
                if diff_deploy:
                    diff_deploy.remove(vrf['vrfName'])
                new_attach_dict.update({'attach': new_attach_list})
                new_attach_dict.update({'vrf_name': vrf['vrfName']})
                diff.append(new_attach_dict)

        for vrf in diff_deploy:
            new_deploy_dict = {'vrf_name': vrf}
            diff.append(new_deploy_dict)

        self.diff_input_format = diff

    def get_diff_query(self):

        query = []

        if self.have_create or self.have_attach:

            for want_c in self.want_create:
                try:
                    found_c = (next((vrf for vrf in self.have_create if vrf['vrfName'] == want_c['vrfName']), None)).copy()
                except AttributeError as error:
                    continue
                found_a = next((vrf for vrf in self.have_attach if vrf['vrfName'] == want_c['vrfName']), None)
                found_w = next((vrf for vrf in self.want_attach if vrf['vrfName'] == want_c['vrfName']), None)

                src = found_c['source']
                found_c.update({'vrf_name': found_c['vrfName']})
                found_c.update({'vrf_id': found_c['vrfId']})
                found_c.update({'vrf_template': found_c['vrfTemplate']})
                found_c.update({'vrf_extension_template': found_c['vrfExtensionTemplate']})
                del found_c['source']
                found_c.update({'source': src})
                found_c.update({'service_vrf_template': found_c['serviceVrfTemplate']})
                found_c.update({'attach': []})

                del found_c['fabric']
                del found_c['vrfName']
                del found_c['vrfId']
                del found_c['vrfTemplate']
                del found_c['vrfExtensionTemplate']
                del found_c['serviceVrfTemplate']
                del found_c['vrfTemplateConfig']

                if not found_w:
                    query.append(found_c)
                    continue

                attach_w = found_w['lanAttachList']
                attach_l = found_a['lanAttachList']

                for a_w in attach_w:
                    attach_d = {}
                    serial = a_w['serialNumber']
                    found = False
                    for a_l in attach_l:
                        if a_l['serialNumber'] == serial:
                            found = True
                            break

                    if found:
                        for k, v in self.ip_sn.items():
                            if v == a_l['serialNumber']:
                                attach_d.update({'ip_address': k})
                                break
                        attach_d.update({'vlan_id': a_l['vlan']})
                        attach_d.update({'deploy': a_l['isAttached']})
                        found_c['attach'].append(attach_d)

                if attach_d:
                    query.append(found_c)

        self.query = query

    def push_to_remote(self, is_rollback=False):

        #
        # The detach and un-deploy operations are executed before the create,attach and deploy to particularly
        # address cases where a VLAN for vrf attachment being deleted is re-used on a new vrf attachment being
        # created. This is needed specially for state: overridden
        #

        path = '/rest/top-down/fabrics/{}/vrfs'.format(self.fabric)
        bulk_create_path = '/rest/top-down/bulk-create/vrfs'

        method = 'POST'
        if self.diff_detach:
            detach_path = path + '/attachments'
            resp = dcnm_send(self.module, method, detach_path, json.dumps(self.diff_detach))
            self.result['response'].append(resp)
            fail, self.result['changed'] = self.handle_response(resp, "attach")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        method = 'POST'
        if self.diff_undeploy:
            deploy_path = path + '/deployments'
            resp = dcnm_send(self.module, method, deploy_path, json.dumps(self.diff_undeploy))
            self.result['response'].append(resp)
            fail, self.result['changed'] = self.handle_response(resp, "deploy")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        del_failure = ''

        if self.diff_delete and self.wait_for_vrf_del_ready():
            method = 'DELETE'
            for vrf, state in self.diff_delete.items():
                if state == 'OUT-OF-SYNC':
                    del_failure += vrf + ","
                    continue
                delete_path = path + "/" + vrf
                resp = dcnm_send(self.module, method, delete_path)
                self.result['response'].append(resp)
                fail, self.result['changed'] = self.handle_response(resp, "delete")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        if del_failure:
            self.result['response'].append('Deletion of vrfs {} has failed'.format(del_failure[:-1]))
            self.module.fail_json(msg=self.result)

        method = 'POST'
        if self.diff_create:
            resp = dcnm_send(self.module, method, bulk_create_path, json.dumps(self.diff_create))
            self.result['response'].append(resp)
            fail, self.result['changed'] = self.handle_response(resp, "create")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        method = 'POST'
        if self.diff_attach:
            attach_path = path + '/attachments'
            resp = dcnm_send(self.module, method, attach_path, json.dumps(self.diff_attach))
            self.result['response'].append(resp)
            fail, self.result['changed'] = self.handle_response(resp, "attach")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

        method = 'POST'
        if self.diff_deploy:
            deploy_path = path + '/deployments'
            resp = dcnm_send(self.module, method, deploy_path, json.dumps(self.diff_deploy))
            self.result['response'].append(resp)
            fail, self.result['changed'] = self.handle_response(resp, "deploy")
            if fail:
                if is_rollback:
                    self.failed_to_rollback = True
                    return
                self.failure(resp)

    def wait_for_vrf_del_ready(self):

        method = 'GET'
        if self.diff_delete:
            for vrf in self.diff_delete:
                state = False
                path = '/rest/top-down/fabrics/{}/vrfs/attachments?vrf-names={}'.format(self.fabric, vrf)
                while not state:
                    resp = dcnm_send(self.module, method, path)
                    state = True
                    if resp.get('DATA') is not None:
                        attach_list = resp['DATA'][0]['lanAttachList']
                        for atch in attach_list:
                            if atch['lanAttachState'] == 'OUT-OF-SYNC' or atch['lanAttachState'] == 'FAILED':
                                self.diff_delete.update({vrf: 'OUT-OF-SYNC'})
                                break
                            if atch['lanAttachState'] != 'NA':
                                self.diff_delete.update({vrf: 'DEPLOYED'})
                                state = False
                                time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                                break
                            self.diff_delete.update({vrf: 'NA'})

            return True

    def validate_input(self):
        """Parse the playbook values, validate to param specs."""

        state = self.params['state']

        vrf_spec = dict(
            vrf_name=dict(required=True, type='str', length_max=32),
            vrf_id=dict(type='int', range_max=16777214),
            vrf_template=dict(type='str', default='Default_VRF_Universal'),
            vrf_extension_template=dict(type='str', default='Default_VRF_Extension_Universal'),
            source=dict(type='str', default=None),
            service_vrf_template=dict(type='str', default=None),
            attach=dict(type='list'),
            deploy=dict(type='bool')
        )
        att_spec = dict(
            ip_address=dict(required=True, type='str'),
            vlan_id=dict(type='int', range_max=4094),
            deploy=dict(type='bool', default=True)
        )

        msg = None
        if self.config:
            for vrf in self.config:
                if 'vrf_name' not in vrf:
                    msg = "vrf_name is mandatory under vrf parameters"

                if 'attach' in vrf and vrf['attach']:
                    for attach in vrf['attach']:
                        if 'ip_address' not in attach or 'vlan_id' not in attach:
                            msg = "ip_address and vlan_id are mandatory under attach parameters"

        else:
            if state == 'merged' or state == 'overridden' or \
                    state == 'replaced' or state == 'query':
                msg = "config: element is mandatory for this state {}".format(state)

        if msg:
            self.module.fail_json(msg=msg)

        if self.config:
            validated = []
            valid_vrf, invalid_params = validate_list_of_dicts(self.config, vrf_spec)
            for vrf in valid_vrf:
                if vrf.get('attach'):
                    valid_att, invalid_att = validate_list_of_dicts(vrf['attach'], att_spec)
                    vrf['attach'] = valid_att
                    invalid_params.extend(invalid_att)
                validated.append(vrf)

            if invalid_params:
                msg = 'Invalid parameters in playbook: {}'.format('\n'.join(invalid_params))
                self.module.fail_json(msg=msg)

    def handle_response(self, res, op):

        fail = False
        changed = True

        if op == 'query_dcnm':
            # This if blocks handles responses to the query APIs against DCNM.
            # Basically all GET operations.
            #
            if res.get('ERROR') == 'Not Found' and res['RETURN_CODE'] == 404:
                return True, False
            if res['RETURN_CODE'] != 200 or res['MESSAGE'] != 'OK':
                return False, True
            return False, False

        # Responses to all other operations POST and PUT are handled here.
        if res.get('MESSAGE') != 'OK':
            fail = True
            changed = False
            return fail, changed
        if res.get('ERROR'):
            fail = True
            changed = False
        if op == 'attach' and 'is in use already' in str(res.values()):
            fail = True
            changed = False
        if op == 'deploy' and 'No switches PENDING for deployment' in str(res.values()):
            changed = False

        return fail, changed

    def failure(self, resp):

        # Implementing a per task rollback logic here so that we rollback DCNM to the have state
        # whenever there is a failure in any of the APIs.
        # The idea would be to run overridden state with want=have and have=dcnm_state
        self.want_create = self.have_create
        self.want_attach = self.have_attach
        self.want_deploy = self.have_deploy

        self.have_create = []
        self.have_attach = []
        self.have_deploy = {}
        self.get_have()
        self.get_diff_override()

        self.push_to_remote(True)

        if self.failed_to_rollback:
            msg1 = "FAILED - Attempted rollback of the task has failed, may need manual intervention"
        else:
            msg1 = 'SUCCESS - Attempted rollback of the task has succeeded'

        res = copy.deepcopy(resp)
        res.update({'ROLLBACK_RESULT': msg1})

        if not resp.get('DATA'):
            data = copy.deepcopy(resp.get('DATA'))
            if data.get('stackTrace'):
                data.update({'stackTrace': 'Stack trace is hidden, use \'-vvvvv\' to print it'})
                res.update({'DATA': data})

        if self.module._verbosity >= 5:
            self.module.fail_json(msg=res)

        self.module.fail_json(msg=res)


def main():
    """ main entry point for module execution
    """

    element_spec = dict(
        fabric=dict(required=True, type='str'),
        config=dict(required=False, type='list'),
        state=dict(default='merged',
                   choices=['merged', 'replaced', 'deleted', 'overridden', 'query'])
    )

    module = AnsibleModule(argument_spec=element_spec,
                           supports_check_mode=True)

    dcnm_vrf = DcnmVrf(module)

    if not dcnm_vrf.ip_sn:
        module.fail_json(msg="Fabric {} missing on DCNM or does not have any switches".format(dcnm_vrf.fabric))

    dcnm_vrf.validate_input()

    dcnm_vrf.get_want()
    dcnm_vrf.get_have()

    if module.params['state'] == 'merged':
        dcnm_vrf.get_diff_merge()

    if module.params['state'] == 'replaced':
        dcnm_vrf.get_diff_replace()

    if module.params['state'] == 'overridden':
        dcnm_vrf.get_diff_override()

    if module.params['state'] == 'deleted':
        dcnm_vrf.get_diff_delete()

    if module.params['state'] == 'query':
        dcnm_vrf.get_diff_query()
        dcnm_vrf.result['response'] = dcnm_vrf.query

    dcnm_vrf.format_diff()
    dcnm_vrf.result['diff'] = dcnm_vrf.diff_input_format

    if dcnm_vrf.diff_create or dcnm_vrf.diff_attach or dcnm_vrf.diff_detach or dcnm_vrf.diff_deploy \
            or dcnm_vrf.diff_undeploy or dcnm_vrf.diff_delete or dcnm_vrf.diff_create_quick:
        dcnm_vrf.result['changed'] = True
    else:
        module.exit_json(**dcnm_vrf.result)

    if module.check_mode:
        module.exit_json(**dcnm_vrf.result)

    dcnm_vrf.push_to_remote()

    module.exit_json(**dcnm_vrf.result)


if __name__ == '__main__':
    main()
