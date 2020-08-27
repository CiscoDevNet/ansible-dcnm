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
import re
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import get_fabric_inventory_details, \
    dcnm_send, validate_list_of_dicts, dcnm_get_ip_addr_info, get_ip_sn_dict
from ansible.module_utils.connection import Connection
from ansible.module_utils.basic import AnsibleModule

__author__ = "Chris Van Heuveln, Shrishail Kariyappanavar"

DOCUMENTATION = '''
---
module: dcnm_network
short_description: Add and remove Networks from a DCNM managed VXLAN fabric.
version_added: "0.9.0"
description:
    - "Add and remove Networks from a DCNM managed VXLAN fabric."
author: Chris Van Heuveln(@chrisvanheuveln), Shrishail Kariyappanavar(@nkshrishail)
options:
  fabric:
    description:
    - 'Name of the target fabric for network operations'
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
    description: 'List of details of networks being managed'
    type: list
    elements: dict
    required: true
    note: Not required for state deleted
    suboptions:
      net_name:
        description: 'Name of the network being managed'
        type: str
        required: true
      vrf_name:
        description: 'Name of the VRF to which the network belongs to'
        type: str
        required: true
      net_id:
        description: 'ID of the network being managed'
        type: int
        required: false
      net_template:
        description: 'Name of the config template to be used'
        type: str
        default: 'Default_Network_Universal'
      net_extension_template:
        description: 'Name of the extension config template to be used'
        type: str
        default: 'Default_Network_Extension_Universal'
      vlan_id:
        description: 'VLAN ID for the network'
        type: int
        required: false
        note: If not specified in the playbook, DCNM will auto-select an available vlan_id
      routing_tag:
        description: 'Routing Tag for the network profile'
        type: int
        required: false
        default: 12345
      gw_ip_subnet:
        description: 'Gateway with subnet for the network'
        type: ipv4
        required: false
      attach:
        description: 'List of network attachment details'
        type: list
        elements: dict
        suboptions:
          ip_address:
            description: 'IP address of the switch where the network will be attached or detached'
            type: ipv4
            required: true
          ports:
            description: 'List of switch interfaces where the network will be attached'
            type: str
            required: true
          deploy:
            description: 'Per switch knob to control whether to deploy the attachment'
            type: bool
            default: true
      deploy:
        description: 'Global knob to control whether to deploy the attachment'
        type: bool
        default: true
'''

EXAMPLES = '''
This module supports the following states:

Merged:
  Networks defined in the playbook will be merged into the target fabric.
    - If the network does not exist it will be added.
    - If the network exists but properties managed by the playbook are different
      they will be updated if possible.
    - Networks that are not specified in the playbook will be untouched.

Replaced:
  Networks defined in the playbook will be replaced in the target fabric.
    - If the Networks does not exist it will be added.
    - If the Networks exists but properties managed by the playbook are different
      they will be updated if possible.
    - Properties that can be managed by the module but are not specified
      in the playbook will be deleted or defaulted if possible.
    - Networks that are not specified in the playbook will be untouched.

Overridden:
  Networks defined in the playbook will be overridden in the target fabric.
    - If the Networks does not exist it will be added.
    - If the Networks exists but properties managed by the playbook are different
      they will be updated if possible.
    - Properties that can be managed by the module but are not specified
      in the playbook will be deleted or defaulted if possible.
    - Networks that are not specified in the playbook will be deleted.

Deleted:
  Networks defined in the playbook will be deleted.
  If no Networks are provided in the playbook, all Networks present on that DCNM fabric will be deleted.

Query:
  Returns the current DCNM state for the Networks listed in the playbook.

- name: Merge networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: merged
    config:
    - net_name: ansible-net13
      vrf_name: Tenant-1
      net_id: 7005
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 150
      gw_ip_subnet: '192.168.30.1/24'
      attach:
      - ip_address: 192.168.1.224
        ports: [Ethernet1/13, Ethernet1/14]
        deploy: true
      - ip_address: 192.168.1.225
        ports: [Ethernet1/13, Ethernet1/14]
        deploy: true
        deploy: true
    - net_name: ansible-net12
      vrf_name: Tenant-2
      net_id: 7002
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 151
      gw_ip_subnet: '192.168.40.1/24'
      attach:
      - ip_address: 192.168.1.224
        ports: [Ethernet1/11, Ethernet1/12]
        deploy: true
      - ip_address: 192.168.1.225
        ports: [Ethernet1/11, Ethernet1/12]
        deploy: true
      deploy: false

- name: Replace networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: replaced
    config:
      - net_name: ansible-net13
        vrf_name: Tenant-1
        net_id: 7005
        net_template: Default_Network_Universal
        net_extension_template: Default_Network_Extension_Universal
        vlan_id: 150
        gw_ip_subnet: '192.168.30.1/24'
        attach:
        - ip_address: 192.168.1.224
          # Replace the ports with new ports
          # ports: [Ethernet1/13, Ethernet1/14]
          ports: [Ethernet1/16, Ethernet1/17]
          deploy: true
          # Delete this attachment
        # - ip_address: 192.168.1.225
        #   ports: [Ethernet1/13, Ethernet1/14]
        #   deploy: true
        deploy: true
        # Dont touch this if its present on DCNM
        # - net_name: ansible-net12
        #   vrf_name: Tenant-2
        #   net_id: 7002
        #   net_template: Default_Network_Universal
        #   net_extension_template: Default_Network_Extension_Universal
        #   vlan_id: 151
        #   gw_ip_subnet: '192.168.40.1/24'
        #   attach:
        #     - ip_address: 192.168.1.224
        #       ports: [Ethernet1/11, Ethernet1/12]
        #       deploy: true
        #     - ip_address: 192.168.1.225
        #       ports: [Ethernet1/11, Ethernet1/12]
        #       deploy: true
        #   deploy: false

- name: Override networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: overridden
    config:
    - net_name: ansible-net13
      vrf_name: Tenant-1
      net_id: 7005
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 150
      gw_ip_subnet: '192.168.30.1/24'
      attach:
      - ip_address: 192.168.1.224
        # Replace the ports with new ports
        # ports: [Ethernet1/13, Ethernet1/14]
        ports: [Ethernet1/16, Ethernet1/17]
        deploy: true
        # Delete this attachment
        # - ip_address: 192.168.1.225
        #   ports: [Ethernet1/13, Ethernet1/14]
        #   deploy: true
        deploy: true
      # Delete this network
      # - net_name: ansible-net12
      #   vrf_name: Tenant-2
      #   net_id: 7002
      #   net_template: Default_Network_Universal
      #   net_extension_template: Default_Network_Extension_Universal
      #   vlan_id: 151
      #   gw_ip_subnet: '192.168.40.1/24'
      #   attach:
      #   - ip_address: 192.168.1.224
      #     ports: [Ethernet1/11, Ethernet1/12]
      #     deploy: true
      #   - ip_address: 192.168.1.225
      #     ports: [Ethernet1/11, Ethernet1/12]
      #     deploy: true
      #   deploy: false

- name: Delete selected networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: deleted
    config:
    - net_name: ansible-net13
      vrf_name: Tenant-1
      net_id: 7005
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 150
      gw_ip_subnet: '192.168.30.1/24'
    - net_name: ansible-net12
      vrf_name: Tenant-2
      net_id: 7002
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 151
      gw_ip_subnet: '192.168.40.1/24'
      deploy: false

- name: Delete all the networkss
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: deleted

- name: Query Networks
  cisco.dcnm.dcnm_network:
    fabric: vxlan-fabric
    state: query
    - net_name: ansible-net13
      vrf_name: Tenant-1
      net_id: 7005
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 150
      gw_ip_subnet: '192.168.30.1/24'
    - net_name: ansible-net12
      vrf_name: Tenant-2
      net_id: 7002
      net_template: Default_Network_Universal
      net_extension_template: Default_Network_Extension_Universal
      vlan_id: 151
      gw_ip_subnet: '192.168.40.1/24'
      deploy: false
'''


class DcnmNetwork:

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.fabric = module.params['fabric']
        self.config = copy.deepcopy(module.params.get('config'))
        self.check_mode = False
        self.conn = Connection(module._socket_path)
        self.have_create = []
        self.want_create = []
        self.diff_create = []
        self.diff_create_update = []
        # This variable is created specifically to hold all the create payloads which are missing a
        # networkId. These payloads are sent to DCNM out of band (basically in the get_diff_merge())
        # We lose diffs for these without this variable. The content stored here will be helpful for
        # cases like "check_mode" and to print diffs[] in the output of each task.
        self.diff_create_quick = []
        self.have_attach = []
        self.want_attach = []
        self.diff_attach = []
        self.validated   = []
        # diff_detach is to list all attachments of a network being deleted, especially for state: OVERRIDDEN
        # The diff_detach and delete operations have to happen before create+attach+deploy for networks being created.
        # This is specifically to address cases where VLAN from a network which is being deleted is used for another
        # network. Without this additional logic, the create+attach+deploy go out first and complain the VLAN is already
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
            response=[],
            warnings=[]
        )

        self.failed_to_rollback = False
        self.WAIT_TIME_FOR_DELETE_LOOP = 5  # in seconds

    def diff_for_attach_deploy(self, want_a, have_a, replace=False):

        attach_list = []

        if not want_a:
            return attach_list

        dep_net = False
        for want in want_a:
            found = False
            if have_a:
                for have in have_a:
                    if want['serialNumber'] == have['serialNumber']:
                        found = True

                        if bool(have['isAttached']) and bool(want['isAttached']):
                            h_sw_ports = have['switchPorts'].split(",") if have['switchPorts'] else []
                            w_sw_ports = want['switchPorts'].split(",") if want['switchPorts'] else []

                            # This is needed to handle cases where vlan is updated after deploying the network
                            # and attachments. This ensures that the attachments before vlan update will use previous
                            # vlan id. All the active attachments on DCNM will have a vlan-id.
                            if have.get('vlan'):
                                want['vlan'] = have.get('vlan')

                            if sorted(h_sw_ports) != sorted(w_sw_ports):
                                atch_sw_ports = list(set(w_sw_ports) - set(h_sw_ports))

                                # Adding some logic which is needed for replace and override.
                                if replace:
                                    dtach_sw_ports = list(set(h_sw_ports) - set(w_sw_ports))

                                    if not atch_sw_ports and not dtach_sw_ports:
                                        continue

                                    want.update({'switchPorts': ','.join(atch_sw_ports) if atch_sw_ports else ""})
                                    want.update(
                                        {'detachSwitchPorts': ','.join(dtach_sw_ports) if dtach_sw_ports else ""})

                                    del want['isAttached']
                                    attach_list.append(want)

                                    continue

                                if not atch_sw_ports:
                                    # The attachments in the have consist of attachments in want and more.
                                    continue

                                want.update({'switchPorts': ','.join(atch_sw_ports)})
                                del want['isAttached']
                                attach_list.append(want)
                                continue

                        if bool(have['isAttached']) is not bool(want['isAttached']):
                            # When the attachment is to be detached and undeployed, ignore any changes
                            # to the attach section in the want(i.e in the playbook).

                            if not bool(want['isAttached']):
                                del have['isAttached']
                                have.update({'deployment': False})
                                attach_list.append(have)
                                continue
                            del want['isAttached']
                            attach_list.append(want)
                            continue

                        if bool(have['deployment']) is not bool(want['deployment']):
                            # We hit this section when attachment is successful, but, deployment is stuck in PENDING or
                            # OUT-OF-SYNC. In such cases, we just add the object to deploy list only. have['deployment']
                            # is set to False when deployment is PENDING or OUT-OF-SYNC - ref - get_have()
                            dep_net = True

            if not found:
                if bool(want['deployment']):
                    del want['isAttached']
                    attach_list.append(want)

        return attach_list, dep_net

    def update_attach_params(self, attach, net_name, deploy):

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
            msg = 'Networks cannot be attached to switch {} with role {}'.format(attach['ip_address'], role)
            self.module.fail_json(msg=msg)

        attach.update({'fabric': self.fabric})
        attach.update({'networkName': net_name})
        attach.update({'serialNumber': serial})
        attach.update({'switchPorts': ','.join(attach['ports'])})
        attach.update({'detachSwitchPorts': ""})  # Is this supported??Need to handle correct
        attach.update({'vlan': 0})
        attach.update({'dot1QVlan': 0})
        attach.update({'untagged': False})
        attach.update({'deployment': deploy})
        attach.update({'isAttached': deploy})
        attach.update({'extensionValues': ""})
        attach.update({'instanceValues': ""})
        attach.update({'freeformConfig': ""})
        if 'deploy' in attach:
            del attach['deploy']
        del attach['ports']
        del attach['ip_address']

        return attach

    def diff_for_create(self, want, have):

        # Possible update scenarios
        # vlanId - Changing vlanId on an already deployed network only affects new attachments
        # gwIpAddress - Changing the gwIpAddress needs all attachments to be re-deployed

        warn_msg = None
        if not have:
            return {}

        gw_changed = False
        create = {}

        if want.get('networkId') and want['networkId'] != have['networkId']:
            self.module.fail_json(msg="networkId can not be updated on existing network: {}".
                                  format(want['networkName']))

        if have['vrf'] != want['vrf']:
            self.module.fail_json(msg="The network {} existing already can not change"
                                      " the VRF association from vrf:{} to vrf:{}".
                                  format(want['networkName'], have['vrf'], want['vrf']))

        json_to_dict_want = json.loads(want['networkTemplateConfig'])
        json_to_dict_have = json.loads(have['networkTemplateConfig'])

        gw_ip_want = json_to_dict_want.get('gatewayIpAddress', "")
        gw_ip_have = json_to_dict_have.get('gatewayIpAddress', "")
        vlanId_want = json_to_dict_want.get('vlanId', "")
        vlanId_have = json_to_dict_have.get('vlanId', "")

        if vlanId_want:

            if have['networkTemplate'] != want['networkTemplate'] or \
                    have['networkExtensionTemplate'] != want['networkExtensionTemplate'] or \
                    gw_ip_have != gw_ip_want or vlanId_have != vlanId_want:
                # The network updates with missing networkId will have to use existing
                # networkId from the instance of the same network on DCNM.

                if vlanId_have != vlanId_want:
                    warn_msg = 'The VLAN change will effect only new attachments.'

                if gw_ip_have != gw_ip_want:
                    gw_changed = True

                want.update({'networkId': have['networkId']})
                create = want

        else:

            if have['networkTemplate'] != want['networkTemplate'] or \
                    have['networkExtensionTemplate'] != want['networkExtensionTemplate'] or \
                    gw_ip_have != gw_ip_want:
                # The network updates with missing networkId will have to use existing
                # networkId from the instance of the same network on DCNM.

                if gw_ip_have != gw_ip_want:
                    gw_changed = True

                want.update({'networkId': have['networkId']})
                create = want

        return create, gw_changed, warn_msg

    def update_create_params(self, net):

        if not net:
            return net

        state = self.params['state']

        n_template = net.get('net_template', 'Default_Network_Universal')
        ne_template = net.get('net_extension_template', 'Default_Network_Extension_Universal')

        if state == 'deleted':
            net_upd = {
                'fabric': self.fabric,
                'networkName': net['net_name'],
                'networkId': net.get('net_id', None),  # Network id will be auto generated in get_diff_merge()
                'networkTemplate': n_template,
                'networkExtensionTemplate': ne_template,
            }
        else:
            net_upd = {
                'fabric': self.fabric,
                'vrf': net['vrf_name'],
                'networkName': net['net_name'],
                'networkId': net.get('net_id', None),  # Network id will be auto generated in get_diff_merge()
                'networkTemplate': n_template,
                'networkExtensionTemplate': ne_template,
            }

        template_conf = {
            'vlanId': str(net.get('vlan_id', "")),
            'gatewayIpAddress': net.get('gw_ip_subnet', ""),
            'isLayer2Only': False,
            'tag': net.get('routing_tag', "")
        }

        net_upd.update({'networkTemplateConfig': json.dumps(template_conf)})

        return net_upd

    def get_have(self):

        have_create = []
        have_deploy = {}

        curr_networks = []
        dep_networks = []

        state = self.params['state']

        method = 'GET'
        path = '/rest/top-down/fabrics/{}/vrfs'.format(self.fabric)

        vrf_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(vrf_objects, 'query_dcnm')

        if missing_fabric or not_ok:
            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find VRFs under fabric: {}".format(self.fabric)

            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
            return

        if not vrf_objects['DATA']:
            return

        if not state == 'deleted':
            if self.config:
                for net in self.config:
                    vrf_found = False
                    vrf_missing = net['vrf_name']
                    for vrf in vrf_objects['DATA']:
                        if vrf_missing == vrf['vrfName']:
                            vrf_found = True
                            break
                    if not vrf_found:
                        self.module.fail_json(msg="VRF: {} is missing in fabric: {}".format(vrf_missing, self.fabric))

        for vrf in vrf_objects['DATA']:

            path = '/rest/top-down/fabrics/{}/networks?vrf-name={}'.format(self.fabric, vrf['vrfName'])

            networks_per_vrf = dcnm_send(self.module, method, path)

            if not networks_per_vrf['DATA']:
                continue

            for net in networks_per_vrf['DATA']:
                json_to_dict = json.loads(net['networkTemplateConfig'])
                t_conf = {
                    'vlanId': json_to_dict.get('vlanId', ""),
                    'gatewayIpAddress': json_to_dict.get('gatewayIpAddress', ""),
                    'isLayer2Only': json_to_dict.get('isLayer2Only', False),
                    'tag': json_to_dict.get('tag', "")
                }

                net.update({'networkTemplateConfig': json.dumps(t_conf)})
                del net['displayName']
                del net['serviceNetworkTemplate']
                del net['source']

                curr_networks.append(net['networkName'])

                have_create.append(net)

        if not curr_networks:
            return

        path = '/rest/top-down/fabrics/{}/networks/attachments?network-names={}'. \
            format(self.fabric, ','.join(curr_networks))

        net_attach_objects = dcnm_send(self.module, method, path)

        missing_fabric, not_ok = self.handle_response(net_attach_objects, 'query_dcnm')

        if missing_fabric or not_ok:
            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
            msg2 = "Unable to find attachments for " \
                   "networks: {} under fabric: {}".format(','.join(curr_networks), self.fabric)

            self.module.fail_json(msg=msg1 if missing_fabric else msg2)
            return

        if not net_attach_objects['DATA']:
            return

        for net_attach in net_attach_objects['DATA']:
            if not net_attach.get('lanAttachList'):
                continue
            attach_list = net_attach['lanAttachList']
            dep_net = ''
            for attach in attach_list:
                attach_state = False if attach['lanAttachState'] == "NA" else True
                deploy = attach['isLanAttached']
                if bool(deploy) and (attach['lanAttachState'] == "OUT-OF-SYNC" or attach['lanAttachState'] == "PENDING"):
                    deploy = False

                if bool(deploy):
                    dep_net = attach['networkName']

                sn = attach['switchSerialNo']
                vlan = attach['vlanId']
                ports = attach['portNames']

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
                del attach['fabricName']
                del attach['portNames']
                del attach['switchDbId']
                del attach['networkId']

                attach.update({'fabric': self.fabric})
                attach.update({'vlan': vlan})
                attach.update({'serialNumber': sn})
                attach.update({'deployment': deploy})
                attach.update({'extensionValues': ""})
                attach.update({'instanceValues': ""})
                attach.update({'freeformConfig': ""})
                attach.update({'isAttached': attach_state})
                attach.update({'dot1QVlan': 0})
                attach.update({'detachSwitchPorts': ""})
                attach.update({'switchPorts': ports})
                attach.update({'untagged': False})

            if dep_net:
                dep_networks.append(dep_net)

        have_attach = net_attach_objects['DATA']

        if dep_networks:
            have_deploy.update({'networkNames': ','.join(dep_networks)})

        self.have_create = have_create
        self.have_attach = have_attach
        self.have_deploy = have_deploy

    def get_want(self):

        want_create = []
        want_attach = []
        want_deploy = {}

        all_networks = ""

        if not self.config:
            return

        for net in self.validated:
            net_attach = {}
            networks = []

            net_deploy = net.get('deploy', True)
            vlan_id = net.get('vlan_id', "")

            want_create.append(self.update_create_params(net))

            if not net.get('attach'):
                continue
            for attach in net['attach']:
                deploy = net_deploy if "deploy" not in attach else attach['deploy']
                networks.append(self.update_attach_params(attach,
                                                          net['net_name'],
                                                          deploy))
            if networks:
                net_attach.update({'networkName': net['net_name']})
                net_attach.update({'lanAttachList': networks})
                want_attach.append(net_attach)

            all_networks += net['net_name'] + ","

        if all_networks:
            want_deploy.update({'networkNames': all_networks[:-1]})

        self.want_create = want_create
        self.want_attach = want_attach
        self.want_deploy = want_deploy

    def get_diff_delete(self):

        diff_detach = []
        diff_undeploy = {}
        diff_delete = {}

        all_nets = ''

        if self.config:

            for want_c in self.want_create:
                if not next((have_c for have_c in self.have_create if have_c['networkName'] == want_c['networkName']), None):
                    continue
                diff_delete.update({want_c['networkName']: 'DEPLOYED'})

                have_a = next((attach for attach in self.have_attach if attach['networkName'] == want_c['networkName']), None)

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
                    all_nets += have_a['networkName'] + ","
            if all_nets:
                diff_undeploy.update({'networkNames': all_nets[:-1]})

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
                    all_nets += have_a['networkName'] + ","

                diff_delete.update({have_a['networkName']: 'DEPLOYED'})
            if all_nets:
                diff_undeploy.update({'networkNames': all_nets[:-1]})

        self.diff_detach = diff_detach
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete

    def get_diff_override(self):

        all_nets = ''
        diff_delete = {}

        warn_msg = self.get_diff_replace()

        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_detach = self.diff_detach
        diff_deploy = self.diff_deploy
        diff_undeploy = self.diff_undeploy

        for have_a in self.have_attach:
            # This block will take care of deleting all the networks that are only present on DCNM but not on playbook
            # The "if not found" block will go through all attachments under those networks and update them so that
            # they will be detached and also the network name will be added to delete payload.

            found = next((net for net in self.want_create if net['networkName'] == have_a['networkName']), None)

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
                    all_nets += have_a['networkName'] + ","

                # The following is added just to help in deletion, we need to wait for detach transaction to complete
                # before attempting to delete the network.
                diff_delete.update({have_a['networkName']: 'DEPLOYED'})

        if all_nets:
            diff_undeploy.update({'networkNames': all_nets[:-1]})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_undeploy = diff_undeploy
        self.diff_delete = diff_delete
        self.diff_detach = diff_detach
        return warn_msg

    def get_diff_replace(self):

        all_nets = ''

        warn_msg = self.get_diff_merge(replace=True)
        diff_create = self.diff_create
        diff_attach = self.diff_attach
        diff_deploy = self.diff_deploy

        for have_a in self.have_attach:
            r_net_list = []
            h_in_w = False
            for want_a in self.want_attach:
                # This block will take care of deleting any attachments that are present only on DCNM
                # but, not on the playbook. In this case, the playbook will have a network and few attaches under it,
                # but, the attaches may be different to what the DCNM has for the same network.
                if have_a['networkName'] == want_a['networkName']:
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
                            r_net_list.append(a_h)
                    break

            if not h_in_w:
                # This block will take care of deleting all the attachments which are in DCNM but
                # are not mentioned in the playbook. The playbook just has the network, but, does not have any attach
                # under it.
                found = next((net for net in self.want_create if net['networkName'] == have_a['networkName']), None)
                if found:
                    atch_h = have_a['lanAttachList']
                    for a_h in atch_h:
                        if not a_h['isAttached']:
                            continue
                        del a_h['isAttached']
                        a_h.update({'deployment': False})
                        r_net_list.append(a_h)

            if r_net_list:
                in_diff = False
                for d_attach in self.diff_attach:
                    if have_a['networkName'] == d_attach['networkName']:
                        in_diff = True
                        d_attach['lanAttachList'].extend(r_net_list)
                        break

                if not in_diff:
                    r_net_dict = {
                        'networkName': have_a['networkName'],
                        'lanAttachList': r_net_list
                    }
                    diff_attach.append(r_net_dict)
                    all_nets += have_a['networkName'] + ","

        if not all_nets:
            self.diff_create = diff_create
            self.diff_attach = diff_attach
            self.diff_deploy = diff_deploy
            return warn_msg

        if not self.diff_deploy:
            diff_deploy.update({'networkNames': all_nets[:-1]})
        else:
            nets = self.diff_deploy['networkNames'] + "," + all_nets[:-1]
            diff_deploy.update({'networkNames': nets})

        self.diff_create = diff_create
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        return warn_msg

    def get_diff_merge(self, replace=False):

        #
        # Special cases:
        # 1. Update gateway on an existing network:
        #    We need to use the network_update API with PUT method to update the nw with new gw.
        #    attach logic remains same, but, we need to re-deploy the network in any case to reflect the new gw.
        # 2. Update vlan-id on an existing network:
        #    This change will only affect new attachments of the same network.
        # 3. Auto generate networkId if its not mentioned by user:
        #    In this case, we need to query the DCNM to get a usable ID and use it in the payload.
        #    And also, any such network create requests need to be pushed individually(not bulk op).

        diff_create = []
        diff_create_update = []
        diff_create_quick = []
        diff_attach = []
        diff_deploy = {}
        prev_net_id_fetched = None

        gw_changed = {}
        warn_msg = None

        for want_c in self.want_create:
            found = False
            for have_c in self.have_create:
                if want_c['networkName'] == have_c['networkName']:

                    found = True
                    diff, gw_chg, warn_msg = self.diff_for_create(want_c, have_c)
                    gw_changed.update({want_c['networkName']: gw_chg})
                    if diff:
                        diff_create_update.append(diff)
                    break
            if not found:
                net_id = want_c.get('networkId', None)

                if not net_id:
                    # networkId(VNI-id) is not provided by user.
                    # Need to query DCNM to fetch next available networkId and use it here.

                    method = 'POST'
                    result = dict(
                        changed=False,
                        response=''
                    )

                    attempt = 0
                    while True or attempt < 10:
                        attempt += 1
                        path = '/rest/managed-pool/fabrics/{}/segments/ids'.format(self.fabric)
                        net_id_obj = dcnm_send(self.module, method, path)

                        missing_fabric, not_ok = self.handle_response(net_id_obj, 'query_dcnm')

                        if missing_fabric or not_ok:
                            msg1 = "Fabric {} not present on DCNM".format(self.fabric)
                            msg2 = "Unable to generate networkId for network: {} " \
                                   "under fabric: {}".format(want_c['networkName'], self.fabric)

                            self.module.fail_json(msg=msg1 if missing_fabric else msg2)

                        if not net_id_obj['DATA']:
                            continue

                        net_id = net_id_obj['DATA'].get('segmentId')
                        if net_id != prev_net_id_fetched:
                            want_c.update({'networkId': net_id})
                            prev_net_id_fetched = net_id
                            break

                    if not net_id:
                        self.module.fail_json(msg="Unable to generate networkId for network: {} "
                                                  "under fabric: {}".format(want_c['networkName'], self.fabric))

                    create_path = '/rest/top-down/fabrics/{}/networks'.format(self.fabric)
                    diff_create_quick.append(want_c)

                    resp = dcnm_send(self.module, method, create_path, json.dumps(want_c))
                    self.result['response'].append(resp)
                    fail, self.result['changed'] = self.handle_response(resp, "create")
                    if fail:
                        self.failure(resp)

                else:
                    diff_create.append(want_c)

        all_nets = []
        for want_a in self.want_attach:
            dep_net = ''
            found = False
            for have_a in self.have_attach:
                if want_a['networkName'] == have_a['networkName']:

                    found = True
                    diff, net = self.diff_for_attach_deploy(want_a['lanAttachList'], have_a['lanAttachList'],
                                                            replace)

                    if diff:
                        base = want_a.copy()
                        del base['lanAttachList']
                        base.update({'lanAttachList': diff})
                        diff_attach.append(base)
                        dep_net = want_a['networkName']
                    else:
                        if net or gw_changed.get(want_a['networkName'], False):
                            dep_net = want_a['networkName']

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
                    dep_net = want_a['networkName']

            if dep_net:
                all_nets.append(dep_net)

        if all_nets:
            diff_deploy.update({'networkNames': ','.join(all_nets)})

        self.diff_create = diff_create
        self.diff_create_update = diff_create_update
        self.diff_attach = diff_attach
        self.diff_deploy = diff_deploy
        self.diff_create_quick = diff_create_quick

        return warn_msg

    def format_diff(self):

        diff = []

        diff_create = copy.deepcopy(self.diff_create)
        diff_create_quick = copy.deepcopy(self.diff_create_quick)
        diff_create_update = copy.deepcopy(self.diff_create_update)
        diff_attach = copy.deepcopy(self.diff_attach)
        diff_detach = copy.deepcopy(self.diff_detach)
        diff_deploy = self.diff_deploy['networkNames'].split(",") if self.diff_deploy else []
        diff_undeploy = self.diff_undeploy['networkNames'].split(",") if self.diff_undeploy else []

        diff_create.extend(diff_create_quick)
        diff_create.extend(diff_create_update)
        diff_attach.extend(diff_detach)
        diff_deploy.extend(diff_undeploy)

        for want_d in diff_create:

            found_a = next((net for net in diff_attach if net['networkName'] == want_d['networkName']), None)

            found_c = want_d

            json_to_dict = json.loads(found_c['networkTemplateConfig'])

            found_c.update({'net_name': found_c['networkName']})
            found_c.update({'vrf_name': found_c['vrf']})
            found_c.update({'net_id': found_c['networkId']})
            found_c.update({'vlan_id': json_to_dict.get('vlanId', "")})
            found_c.update({'gw_ip_subnet': json_to_dict.get('gatewayIpAddress', "")})
            found_c.update({'net_template': found_c['networkTemplate']})
            found_c.update({'net_extension_template': found_c['networkExtensionTemplate']})
            found_c.update({'attach': []})

            del found_c['fabric']
            del found_c['networkName']
            del found_c['networkId']
            del found_c['networkTemplate']
            del found_c['networkExtensionTemplate']
            del found_c['networkTemplateConfig']
            del found_c['vrf']

            if diff_deploy and found_c['net_name'] in diff_deploy:
                diff_deploy.remove(found_c['net_name'])
            if not found_a:
                diff.append(found_c)
                continue

            attach = found_a['lanAttachList']

            for a_w in attach:
                attach_d = {}
                detach_d = {}

                for k, v in self.ip_sn.items():
                    if v == a_w['serialNumber']:
                        attach_d.update({'ip_address': k})
                        break
                if a_w['detachSwitchPorts']:
                    detach_d.update({'ip_address': attach_d['ip_address']})
                    detach_d.update({'ports': a_w['detachSwitchPorts']})
                    detach_d.update({'deploy': False})
                    found_c['attach'].append(detach_d)
                attach_d.update({'ports': a_w['switchPorts']})
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
                detach_d = {}

                for k, v in self.ip_sn.items():
                    if v == a_w['serialNumber']:
                        attach_d.update({'ip_address': k})
                        break
                if a_w['detachSwitchPorts']:
                    detach_d.update({'ip_address': attach_d['ip_address']})
                    detach_d.update({'ports': a_w['detachSwitchPorts']})
                    detach_d.update({'deploy': False})
                    new_attach_list.append(detach_d)
                attach_d.update({'ports': a_w['switchPorts']})
                attach_d.update({'deploy': a_w['deployment']})
                new_attach_list.append(attach_d)

            if new_attach_list:
                if diff_deploy and vrf['networkName'] in diff_deploy:
                    diff_deploy.remove(vrf['networkName'])
                new_attach_dict.update({'attach': new_attach_list})
                new_attach_dict.update({'net_name': vrf['networkName']})
                diff.append(new_attach_dict)

        for net in diff_deploy:
            new_deploy_dict = {'net_name': net}
            diff.append(new_deploy_dict)

        self.diff_input_format = diff

    def get_diff_query(self):

        query = []

        if self.have_create or self.have_attach:

            for want_c in self.want_create:
                try:
                    found_c = (
                        next((net for net in self.have_create if net['networkName'] == want_c['networkName']), None)).copy()
                except AttributeError as error:
                    continue
                found_a = next((net for net in self.have_attach if net['networkName'] == want_c['networkName']), None)
                found_w = next((net for net in self.want_attach if net['networkName'] == want_c['networkName']), None)

                json_to_dict = json.loads(found_c['networkTemplateConfig'])

                found_c.update({'net_name': found_c['networkName']})
                found_c.update({'vrf_name': found_c['vrf']})
                found_c.update({'net_id': found_c['networkId']})
                found_c.update({'vlan_id': json_to_dict.get('vlanId', "")})
                found_c.update({'gw_ip_subnet': json_to_dict.get('gatewayIpAddress', "")})
                found_c.update({'net_template': found_c['networkTemplate']})
                found_c.update({'net_extension_template': found_c['networkExtensionTemplate']})
                found_c.update({'attach': []})

                del found_c['fabric']
                del found_c['networkName']
                del found_c['networkId']
                del found_c['networkTemplate']
                del found_c['networkExtensionTemplate']
                del found_c['networkTemplateConfig']
                del found_c['vrf']

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
                        attach_d.update({'ports': a_l['switchPorts']})
                        attach_d.update({'deploy': a_l['isAttached']})
                        found_c['attach'].append(attach_d)

                if attach_d:
                    query.append(found_c)

        self.query = query

    def wait_for_del_ready(self):

        method = 'GET'
        if self.diff_delete:
            for net in self.diff_delete:
                state = False
                path = '/rest/top-down/fabrics/{}/networks/attachments?network-names={}'.format(self.fabric, net)
                while not state:
                    resp = dcnm_send(self.module, method, path)
                    state = True
                    if resp['DATA']:
                        attach_list = resp['DATA'][0]['lanAttachList']
                        for atch in attach_list:
                            if atch['lanAttachState'] == 'OUT-OF-SYNC' or atch['lanAttachState'] == 'FAILED':
                                self.diff_delete.update({net: 'OUT-OF-SYNC'})
                                break
                            if atch['lanAttachState'] != 'NA':
                                self.diff_delete.update({net: 'DEPLOYED'})
                                state = False
                                time.sleep(self.WAIT_TIME_FOR_DELETE_LOOP)
                                break
                            self.diff_delete.update({net: 'NA'})

            return True

    def push_to_remote(self, is_rollback=False):

        path = '/rest/top-down/fabrics/{}/networks'.format(self.fabric)
        bulk_create_path = '/rest/top-down/bulk-create/networks'

        method = 'PUT'
        if self.diff_create_update:
            for net in self.diff_create_update:
                update_path = path + '/{}'.format(net['networkName'])
                resp = dcnm_send(self.module, method, update_path, json.dumps(net))
                self.result['response'].append(resp)
                fail, self.result['changed'] = self.handle_response(resp, "create")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        #
        # The detach and un-deploy operations are executed before the create,attach and deploy to particularly
        # address cases where a VLAN of a network being deleted is re-used on a new network being created. This is
        # needed specially for state: overridden
        #

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

        method = 'DELETE'
        del_failure = ''
        if self.diff_delete and self.wait_for_del_ready():
            for net, state in self.diff_delete.items():
                if state == 'OUT-OF-SYNC':
                    del_failure += net + ","
                    continue
                delete_path = path + "/" + net
                resp = dcnm_send(self.module, method, delete_path)
                self.result['response'].append(resp)
                fail, self.result['changed'] = self.handle_response(resp, "delete")
                if fail:
                    if is_rollback:
                        self.failed_to_rollback = True
                        return
                    self.failure(resp)

        if del_failure:
            resp = 'Deletion of Networkss {} has failed'.format(del_failure[:-1])
            self.result['response'].append(resp)
            if is_rollback:
                self.failed_to_rollback = True
                return
            self.failure(resp)

        if self.diff_create:
            for net in self.diff_create:
                json_to_dict = json.loads(net['networkTemplateConfig'])
                vlanId = json_to_dict.get('vlanId', "")

                if not vlanId:
                    vlan_path = '/rest/resource-manager/vlan/{}?vlanUsageType=TOP_DOWN_VRF_VLAN'.format(self.fabric)
                    vlan_data = dcnm_send(self.module, 'GET', vlan_path)

                    if vlan_data['RETURN_CODE'] != 200:
                        self.module.fail_json(msg='Failure getting autogenerated vlan_id {}'.format(vlan_data))
                    vlanId = vlan_data['DATA']

                t_conf = {
                    'vlanId': vlanId,
                    'gatewayIpAddress': json_to_dict.get('gatewayIpAddress', ""),
                    'isLayer2Only': json_to_dict.get('isLayer2Only', False),
                    'tag': json_to_dict.get('tag', "")
                }

                net.update({'networkTemplateConfig': json.dumps(t_conf)})

                method = 'POST'
                resp = dcnm_send(self.module, method, path, json.dumps(net))
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
            for attempt in range(0, 50):
                resp = dcnm_send(self.module, method, attach_path, json.dumps(self.diff_attach))
                update_in_progress = False
                for key in resp['DATA'].keys():
                    if re.search(r'Failed.*Please try after some time', resp['DATA'][key]):
                        update_in_progress = True
                if update_in_progress:
                    time.sleep(1)
                    continue
                else:
                    break
            self.result['response'].append(resp)
            fail, self.result['changed'] = self.handle_response(resp, "attach")
            # If we get here and an update_in_progress is True then
            # not all of the attachments were successful which represents a
            # failure condition.
            if fail or update_in_progress:
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

    def validate_input(self):

        """Parse the playbook values, validate to param specs."""

        net_spec = dict(
            net_name=dict(required=True, type='str', length_max=64),
            net_id=dict(type='int', range_max=16777214),
            vrf_name=dict(type='str', length_max=32),
            attach=dict(type='list'),
            deploy=dict(type='bool'),
            gw_ip_subnet=dict(type='ipv4_subnet', default=""),
            vlan_id=dict(type='int', range_max=4094),
            routing_tag=dict(type='int', default=12345, range_max=4294967295),
            net_template=dict(type='str', default='Default_Network_Universal'),
            net_extension_template=dict(type='str', default='Default_Network_Extension_Universal')
        )
        att_spec = dict(
            ip_address=dict(required=True, type='str'),
            ports=dict(required=True, type='list'),
            deploy=dict(type='bool', default=True)
        )

        if self.config:
            msg = None
            # Validate net params
            valid_net, invalid_params = validate_list_of_dicts(self.config, net_spec)
            for net in valid_net:
                if net.get('attach'):
                    valid_att, invalid_att = validate_list_of_dicts(net['attach'], att_spec)
                    net['attach'] = valid_att
                    invalid_params.extend(invalid_att)
                self.validated.append(net)

            if invalid_params:
                msg = 'Invalid parameters in playbook: {}'.format('\n'.join(invalid_params))
                self.module.fail_json(msg=msg)

        else:
            state = self.params['state']
            msg = None

            if state == 'merged' or state == 'overridden' or \
                    state == 'replaced' or state == 'query':
                msg = "config: element is mandatory for this state {}".format(state)

        if msg:
            self.module.fail_json(msg=msg)

    def handle_response(self, resp, op):

        fail = False
        changed = True

        res = resp.copy()

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
        if op == 'attach' and 'Invalid interfaces' in str(res.values()):
            fail = True
            changed = True
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

    dcnm_net = DcnmNetwork(module)

    if not dcnm_net.ip_sn:
        module.fail_json(msg="Fabric {} missing on DCNM or does not have any switches".format(dcnm_net.fabric))

    dcnm_net.validate_input()

    dcnm_net.get_want()
    dcnm_net.get_have()

    warn_msg = None

    if module.params['state'] == 'merged':
        warn_msg = dcnm_net.get_diff_merge()

    if module.params['state'] == 'replaced':
        warn_msg = dcnm_net.get_diff_replace()

    if module.params['state'] == 'overridden':
        warn_msg = dcnm_net.get_diff_override()

    if module.params['state'] == 'deleted':
        dcnm_net.get_diff_delete()

    if module.params['state'] == 'query':
        dcnm_net.get_diff_query()
        dcnm_net.result['response'] = dcnm_net.query

    dcnm_net.result['warnings'].append(warn_msg) if warn_msg else []

    if module.check_mode:
        module.exit_json(**dcnm_net.result)

    if dcnm_net.diff_create or dcnm_net.diff_create_quick or dcnm_net.diff_attach \
            or dcnm_net.diff_deploy or dcnm_net.diff_delete or dcnm_net.diff_create_update \
            or dcnm_net.diff_detach or dcnm_net.diff_undeploy:
        dcnm_net.result['changed'] = True
    else:
        module.exit_json(**dcnm_net.result)

    dcnm_net.format_diff()
    dcnm_net.result['diff'] = dcnm_net.diff_input_format

    dcnm_net.push_to_remote()

    module.exit_json(**dcnm_net.result)

if __name__ == '__main__':
    main()

