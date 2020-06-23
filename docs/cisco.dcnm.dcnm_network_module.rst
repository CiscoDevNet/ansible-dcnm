.. _cisco.dcnm.dcnm_network_module:


***********************
cisco.dcnm.dcnm_network
***********************

**Send REST API requests to DCNM controller for network operations**


Version added: 2.10

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Send REST API requests to DCNM controller for network operations - Create, Update, Attach, Deploy and Delete




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="2">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
                        <th width="100%">Comments</th>
        </tr>
                    <tr>
                                                                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>config</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>                         / <span style="color: red">required</span>                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>List of details of networks being managed</div>
                                                        </td>
            </tr>
                                                            <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>gw_ip_subnet</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">ipv4</span>
                                                                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>Gateway with subnet for the network</div>
                                                        </td>
            </tr>
                                <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>net_extension_template</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                                    </div>
                                    </td>
                                <td>
                                                                                                                                                                    <b>Default:</b><br/><div style="color: blue">"Default_Network_Extension_Universal"</div>
                                    </td>
                                                                <td>
                                            <div>Name of the extension config template to be used</div>
                                                        </td>
            </tr>
                                <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>net_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                                                                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>ID of the network being managed</div>
                                                        </td>
            </tr>
                                <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>net_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                 / <span style="color: red">required</span>                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>Name of the network being managed</div>
                                                        </td>
            </tr>
                                <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>net_template</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                                    </div>
                                    </td>
                                <td>
                                                                                                                                                                    <b>Default:</b><br/><div style="color: blue">"Default_Network_Universal"</div>
                                    </td>
                                                                <td>
                                            <div>Name of the config template to be used</div>
                                                        </td>
            </tr>
                                <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>suboptions</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                                                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                        </td>
            </tr>
                                <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vlan_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                                                                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>VLAN ID for the network</div>
                                                        </td>
            </tr>
                                <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                 / <span style="color: red">required</span>                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>Name of the VRF to which the network belongs to</div>
                                                        </td>
            </tr>
                    
                                                <tr>
                                                                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>fabric</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                 / <span style="color: red">required</span>                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>Name of the target fabric for network operations</div>
                                                        </td>
            </tr>
                                <tr>
                                                                <td colspan="2">
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
                                            <div>The state of DCNM after module completion.</div>
                                                        </td>
            </tr>
                        </table>
    <br/>




Examples
--------

.. code-block:: yaml+jinja

    
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
        - Properties that can be managed by the module but are  not specified
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
          - ip_address: 10.122.197.224
            ports: [Ethernet1/13, Ethernet1/14]
            deploy: true
          - ip_address: 10.122.197.225
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
          - ip_address: 10.122.197.224
            ports: [Ethernet1/11, Ethernet1/12]
            deploy: true
          - ip_address: 10.122.197.225
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
            - ip_address: 10.122.197.224
              # Replace the ports with new ports
              # ports: [Ethernet1/13, Ethernet1/14]
              ports: [Ethernet1/16, Ethernet1/17]
              deploy: true
              # Delete this attachment
            # - ip_address: 10.122.197.225
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
            #     - ip_address: 10.122.197.224
            #       ports: [Ethernet1/11, Ethernet1/12]
            #       deploy: true
            #     - ip_address: 10.122.197.225
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
          - ip_address: 10.122.197.224
            # Replace the ports with new ports
            # ports: [Ethernet1/13, Ethernet1/14]
            ports: [Ethernet1/16, Ethernet1/17]
            deploy: true
            # Delete this attachment
            # - ip_address: 10.122.197.225
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
          #   - ip_address: 10.122.197.224
          #     ports: [Ethernet1/11, Ethernet1/12]
          #     deploy: true
          #   - ip_address: 10.122.197.225
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





Status
------


Authors
~~~~~~~

- Chris Van Heuveln(@chrisvanheuveln), Shrishail Kariyappanavar(@nkshrishail)


