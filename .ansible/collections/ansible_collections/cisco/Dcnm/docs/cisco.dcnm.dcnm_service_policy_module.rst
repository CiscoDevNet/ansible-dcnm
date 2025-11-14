.. _cisco.dcnm.dcnm_service_policy_module:


******************************
cisco.dcnm.dcnm_service_policy
******************************

**DCNM ansible module for managing service policies.**


Version added: 1.2.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- DCNM ansible module for creating, deleting, querying and modifying service policies




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="3">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>attach</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li><div style="color: blue"><b>yes</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>a flag specifying if the given service policy is to be attached to the specified service node</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>config</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>a list of dictionaries containing service policy and switch information</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dest_network</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>name of the destination network for this service policy</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dest_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>name of the destination vrf for this service policy</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>a unique name which identifies the service policy</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>next_hop</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>next hop ip address to be used in source to network direction</div>
                        <div>This must exactly match the next hop IP configured for the route peering associated with this policy</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>policy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>details of the policy (ACL) to be applied</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>acl_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"will be auto-generated by DCNM"</div>
                </td>
                <td>
                        <div>Name of the ACL in the forward direction</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>action</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>permit</b>&nbsp;&larr;</div></li>
                                    <li>deny</li>
                        </ul>
                </td>
                <td>
                        <div>action to apply for traffic matching the service profile</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dest_port</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>any</li>
                                    <li>Min 1</li>
                                    <li>Max 65535</li>
                        </ul>
                </td>
                <td>
                        <div>destination port number to be matched to apply this ACL</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>next_hop_option</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>none</b>&nbsp;&larr;</div></li>
                                    <li>drop-on-fail</li>
                                    <li>drop</li>
                        </ul>
                </td>
                <td>
                        <div>option to specify how to redirect traffic</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>proto</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>ip</li>
                                    <li>icmp</li>
                                    <li>tcp</li>
                                    <li>udp</li>
                        </ul>
                </td>
                <td>
                        <div>protocol to be matched to apply this ACL</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>rev_acl_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"will be auto-generated by DCNM"</div>
                </td>
                <td>
                        <div>Name of the ACL in the reverse direction</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>rev_route_map_num</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>route map match number for reverse direction</div>
                        <div>Minimum Value (1), Maximum Value (65535)</div>
                        <div>Default value is auto-generated by DCNM</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>route_map_num</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>route map match number</div>
                        <div>Minimum Value (1), Maximum Value (65535)</div>
                        <div>Default value is auto-generated by DCNM</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>src_port</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>any</li>
                                    <li>Min 1</li>
                                    <li>Max 65535</li>
                        </ul>
                </td>
                <td>
                        <div>source port number to be matched to apply this ACL</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>reverse_next_hop</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>reverse next hop ip address to be used in network to source direction</div>
                        <div>This must exactly match the reverse next hop IP configured for the route peering associated with this policy</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>src_network</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>name of the source network for this service policy</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>src_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>name of the source vrf for this service policy</div>
                </td>
            </tr>

            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>deploy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li><div style="color: blue"><b>yes</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>a flag specifying if a service policy is to be deployed on the switches</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>fabric</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>name of the target fabric for service policy operations</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>service_fabric</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>name of the external fabric attached to the service node for service policy operations</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>state</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>merged</b>&nbsp;&larr;</div></li>
                                    <li>replaced</li>
                                    <li>overridden</li>
                                    <li>deleted</li>
                                    <li>query</li>
                        </ul>
                </td>
                <td>
                        <div>the required state of the configuration after module completion.</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    # L4-L7 Service Insertion:
    #
    # Cisco DCNM has the ability to insert Layer 4-Layer 7 (L4-L7) service devices in a data center fabric, and also enables selectively
    # redirecting traffic to these service devices. You can add a service node, create route peering between the service node and the
    # service leaf switch, and then selectively redirect traffic to these service nodes. Ansible collections support 3 modules viz.
    # Service Node, Service Route Peering and Service Policy to enable this.
    #
    # Service Node:
    #
    # You have to create an external fabric and specify that a service node resides in that external fabric during service node creation.
    # Service policies are created on the service node to determine the actions to be applied to the traffic
    #
    # Route Peerings:
    #
    # Multiple Service Route Peerings can be created under service node. Each Route Peering creates required service networks that is used to
    # carry traffic towards the service node.
    #
    # Service Policy:
    #
    # Each route peering can have multiple service policies. Service policies can only be created for networks created through route peerings.
    # The service policies define the actions to be taken for matching traffic.
    #
    # Dependency Tree:
    #
    # Service Node
    # |
    # |---- Route Peering 1
    # |     |
    # .     |---- Service Policy 1
    # .     |
    # .     .
    # .     .
    # .     .
    # .     |---- Service Policy N
    # .
    # |---- Route Peering N
    #       |
    #       |---- Service Policy 1
    #       |
    #       .
    #       .
    #       .
    #       |---- Service Policy N
    #
    #
    # This module supports the following states:

    # Merged:
    #   Service Policies defined in the playbook will be merged into the target fabric.
    #     - If the Service Policies does not exist it will be added.
    #     - If the Service Policies exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Service Policies that are not specified in the playbook will be untouched.
    #
    # Replaced:
    #   Service Policies defined in the playbook will be replaced in the target fabric.
    #     - If the Service Policies does not exist it will be added.
    #     - If the Service Policies exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Properties that can be managed by the module but are not specified
    #       in the playbook will be deleted or defaulted if possible.
    #     - Service Policies that are not specified in the playbook will be untouched.
    #
    # Overridden:
    #   Service Policies defined in the playbook will be overridden in the target fabric.
    #     - If the Service Policies does not exist it will be added.
    #     - If the Service Policies exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Properties that can be managed by the module but are not specified
    #       in the playbook will be deleted or defaulted if possible.
    #     - Service Policies that are not specified in the playbook will be deleted.
    #
    # Deleted:
    #   Service Policies defined in the playbook will be deleted.
    #
    # Query:
    #   Returns the current DCNM state for the Service Policies listed in the playbook.

    # CREATING SERVICE POLICIES
    # =========================

    - name: Create service policy including all optional objects
      cisco.dcnm.dcnm_service_policy:
        fabric: test_fabric
        service_fabric: external
        attach: true
        deploy: true
        state: merged
        config:
          - name: service_policy_1
            node_name: it-sn-1
            rp_name: it-fw-rp1
            src_vrf: vrf_11
            dest_vrf: vrf_11
            src_network: net_11
            dest_network: net_12
            next_hop: 192.161.1.100
            reverse_next_hop: 192.161.2.100
            reverse: true
            policy:
              proto: tcp
              src_port: any
              dest_port: 22
              action: permit
              next_hop_option:  none
              acl_name: fwd_acl_10
              rev_acl_name: rev_acl_10
              route_map_num: 101
              rev_route_map_num: 102

    # DELETE SERVICE POLICIES
    # =======================

    # 1. With Policy Name and Node name
    #
    # Deletes the specific service policy specified from the given node

    - name: Delete service policies with policy name and node name
      cisco.dcnm.dcnm_service_policy:
        fabric: test_fabric
        service_fabric: external
        state: deleted
        config:
          - name: service_policy_1
            node_name: it-sn-1

          - name: service_policy_2
            node_name: it-sn-2

          - name: service_policy_3
            node_name: it-sn-2

          - name: service_policy_4
            node_name: it-sn-2

          - name: service_policy_5
            node_name: it-sn-2

    # 2. With Node name alone
    #
    # Deletes all service policies from the specified nodes

    - name: Delete service policies with Node names
      cisco.dcnm.dcnm_service_policy:
        fabric: test_fabric
        service_fabric: external
        state: deleted
        config:
          - node_name: it-sn-1
          - node_name: it-sn-2

    # 3. With Node name and RP name
    #
    # Deletes all service policies under the specified route peering and node

    - name: Delete service policies with Node name and RP name
      cisco.dcnm.dcnm_service_policy:
        fabric: test_fabric
        service_fabric: external
        state: deleted
        config:
          - node_name: it-sn-1
            rp_name: it-fw-rp1

          - node_name: it-sn-2
            rp_name: it-fw-rp2

    # 4. Without config
    #
    # Deletes all service policies on the given fabric and attached fabric

    - name: Delete service policies without config
      cisco.dcnm.dcnm_service_policy:
        fabric: test_fabric
        service_fabric: external
        state: deleted

    # OVERRIDE SERVICE POLICIES
    # =========================

    # When this playbook is executed, service policy service_policy_1 will be created or replaced and all
    # other service policies in test_fabric and external will be deleted

    - name: Override all existing service policies with a new one
      cisco.dcnm.dcnm_service_policy:
        fabric: test_fabric
        service_fabric: external
        attach: true
        deploy: true
        state: overridden
        config:
          - name: service_policy_1
            node_name: it-sn-1
            rp_name: it-fw-rp1
            src_vrf: vrf_11
            dest_vrf: vrf_11
            src_network: net_11
            dest_network: net_12
            next_hop: 192.161.1.100
            reverse_next_hop: 192.161.2.100
            policy:
              proto: icmp
              src_port: 555
              dest_port: 22
              action: permit
              next_hop_option:  none
              acl_name: fwd_acl_555
              rev_acl_name: rev_acl_555
              route_map_num: 555
              rev_route_map_num: 556

    # REPLACE SERVICE POLICIES
    # ========================

    - name: Replace service policy_1 with the one specified below
      cisco.dcnm.dcnm_service_policy:
        fabric: test_fabric
        service_fabric: external
        attach: true
        deploy: true
        state: replaced
        config:
          - name: service_policy_1
            node_name: it-sn-1
            rp_name: it-fw-rp1
            src_vrf: vrf_11
            dest_vrf: vrf_11
            src_network: net_11
            dest_network: net_12
            next_hop: 192.161.1.100
            reverse_next_hop: 192.161.2.100
            policy:
              proto: udp
              src_port: 501
              dest_port: 502
              action: deny
              next_hop_option: drop_on_fail

    # QUERY SERVICE POLICIES
    # ======================

    - name: Query service policies based on service node and policy name
      cisco.dcnm.dcnm_service_policy:
        fabric: test_fabric
        service_fabric: external
        state: query
        config:
          - name: service_policy_1
            node_name: it-sn-1

    - name: Query service policies based on service node
      cisco.dcnm.dcnm_service_policy:
      fabric: test_fabric
      service_fabric: external
      state: query
      config:
        - node_name: it-sn-1




Status
------


Authors
~~~~~~~

- Mallik Mudigonda (@mmudigon)
