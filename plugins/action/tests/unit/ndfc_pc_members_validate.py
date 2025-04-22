from __future__ import absolute_import, division, print_function


__metaclass__ = type

from ansible.utils.display import Display
from ansible.plugins.action import ActionBase

display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        results = super(ActionModule, self).run(tmp, task_vars)
        results['failed'] = False

        ndfc_data = self._task.args['ndfc_data']
        test_data = self._task.args['test_data']

        # import epdb ; epdb.st()

        expected_state = {}
        expected_state['pc_trunk_description'] = test_data['pc_trunk_desc']
        expected_state['pc_trunk_member_description'] = test_data['eth_trunk_desc']
        expected_state['pc_access_description'] = test_data['pc_access_desc']
        expected_state['pc_access_member_description'] = test_data['eth_access_desc']
        expected_state['pc_l3_description'] = test_data['pc_l3_desc']
        expected_state['pc_l3_member_description'] = test_data['eth_l3_desc']
        expected_state['pc_dot1q_description'] = test_data['pc_dot1q_desc']
        expected_state['pc_dot1q_member_description'] = test_data['eth_dot1q_desc']
        # --
        expected_state['pc_trunk_host_policy'] = 'int_port_channel_trunk_host'
        expected_state['pc_trunk_member_policy'] = 'int_port_channel_trunk_member_11_1'
        # --
        expected_state['pc_access_host_policy'] = 'int_port_channel_access_host'
        expected_state['pc_access_member_policy'] = 'int_port_channel_access_member_11_1'
        # --
        expected_state['pc_l3_policy'] = 'int_l3_port_channel'
        expected_state['pc_l3_member_policy'] = 'int_l3_port_channel_member'
        # --
        expected_state['pc_dot1q_policy'] = 'int_port_channel_dot1q_tunnel_host'
        expected_state['pc_dot1q_member_policy'] = 'int_port_channel_dot1q_tunnel_member_11_1'

        interface_list = [test_data['pc1'], test_data['eth_intf8'], test_data['eth_intf9'],
                          test_data['pc2'], test_data['eth_intf10'], test_data['eth_intf11'],
                          test_data['pc3'], test_data['eth_intf12'], test_data['eth_intf13'],
                          test_data['pc4'], test_data['eth_intf14'], test_data['eth_intf15']]

        if len(ndfc_data['response']) == 0:
            results['failed'] = True
            results['msg'] = 'No response data found'
            return results

        # ReWrite List Data to Dict keyed by interface name
        ndfc_data_dict = {}
        for interface in ndfc_data['response']:
            int = interface['interfaces'][0]['ifName']
            ndfc_data_dict[int] = interface['interfaces'][0]
            ndfc_data_dict[int]['policy'] = interface['policy']

        for interface in interface_list:
            if interface not in ndfc_data_dict.keys():
                results['failed'] = True
                results['msg'] = f'Interface {interface} not found in response data'
                return results

            # Use a regex to match string 'Eth' in interface variable
            if interface == test_data['pc1']:
                if ndfc_data_dict[interface]['policy'] != expected_state['pc_trunk_host_policy']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} policy is not {expected_state["pc_trunk_host_policy"]}'
                    return results
                if ndfc_data_dict[interface]['nvPairs']['DESC'] != expected_state['pc_trunk_description']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} description is not {expected_state["pc_trunk_description"]}'
                    return results
            if interface == test_data['eth_intf8'] or interface == test_data['eth_intf9']:
                if ndfc_data_dict[interface]['policy'] != expected_state['pc_trunk_member_policy']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} policy is not {expected_state["pc_trunk_member_policy"]}'
                    return results
                if ndfc_data_dict[interface]['nvPairs']['DESC'] != expected_state['pc_trunk_member_description']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} description is not {expected_state["pc_trunk_member_description"]}'
                    return results

            if interface == test_data['pc2']:
                if ndfc_data_dict[interface]['policy'] != expected_state['pc_access_host_policy']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} policy is {expected_state["pc_access_host_policy"]}'
                    return results
                if ndfc_data_dict[interface]['nvPairs']['DESC'] != expected_state['pc_access_description']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} description is not {expected_state["pc_access_description"]}'
                    return results
            if interface == test_data['eth_intf10'] or interface == test_data['eth_intf11']:
                if ndfc_data_dict[interface]['policy'] != expected_state['pc_access_member_policy']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} policy is not {expected_state["pc_access_member_policy"]}'
                    return results
                if ndfc_data_dict[interface]['nvPairs']['DESC'] != expected_state['pc_access_member_description']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} description is not {expected_state["pc_access_member_description"]}'
                    return results

            if interface == test_data['pc3']:
                if ndfc_data_dict[interface]['policy'] != expected_state['pc_l3_policy']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} policy is not {expected_state["pc_l3_policy"]}'
                    return results
                if ndfc_data_dict[interface]['nvPairs']['DESC'] != expected_state['pc_l3_description']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} description is not {expected_state["pc_l3_description"]}'
                    return results
            if interface == test_data['eth_intf12'] or interface == test_data['eth_intf13']:
                if ndfc_data_dict[interface]['policy'] != expected_state['pc_l3_member_policy']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} policy is not {expected_state["pc_l3_member_policy"]}'
                    return results
                if ndfc_data_dict[interface]['nvPairs']['DESC'] != expected_state['pc_l3_member_description']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} description is not {expected_state["pc_l3_member_description"]}'
                    return results

            if interface == test_data['pc4']:
                if ndfc_data_dict[interface]['policy'] != expected_state['pc_dot1q_policy']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} policy is not {expected_state["pc_dot1q_policy"]}'
                    return results
                if ndfc_data_dict[interface]['nvPairs']['DESC'] != expected_state['pc_dot1q_description']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} description is not {expected_state["pc_dot1q_description"]}'
                    return results
            if interface == test_data['eth_intf14'] or interface == test_data['eth_intf15']:
                if ndfc_data_dict[interface]['policy'] != expected_state['pc_dot1q_member_policy']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} policy is not {expected_state["pc_dot1q_member_policy"]}'
                    return results
                if ndfc_data_dict[interface]['nvPairs']['DESC'] != expected_state['pc_dot1q_member_description']:
                    results['failed'] = True
                    results['msg'] = f'Interface {interface} description is not {expected_state["pc_dot1q_member_description"]}'
                    return results

        return results
