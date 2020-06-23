.. _cisco.dcnm.dcnm_network_module:


***********************
cisco.dcnm.dcnm_network
***********************

**Send REST API requests to DCNM controller for network operations**


Version added: 0.9.0

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
                                            <div>The state of the configuration after module completion. Merged - The state of the objects listed on the playbook will be created on the DCNM for the same objects. Only additions will be made if the playbook object or part of the object is missing on DCNM. If an object or part of the object mentioned on playbook is already present on DCNM, no operation will be performed for such objects or part of the objects. Replaced - The state of the objects listed in the playbook will serve as source of truth for the same objects on the DCNM under the fabric mentioned. Additions and deletions will be done to bring the DCNM objects to the state listed in the playbook. Note - Replace will only work on the objects mentioned in the playbook. Overridden - The state of the objects listed in the playbook will serve as source of truth for all the objects under the fabric mentioned. Additions and deletions will be done to bring the DCNM objects to the state listed in the playbook. Note - Override will work on the all the objects in the playbook and also all the objects on DCNM. Deleted - Deletes the list of objects specified in the playbook, if no objects are provided in the playbook, all the objects present on DCNM will be deleted. Query - Returns the current state on the DCNM for the objects listed in the playbook.
    rollback functionality - This module supports task level rollback functionality. If any task runs into failures, as part of failure handling, the module tries to bring the state of the DCNM back to the state captured in have structure at the beginning of the task execution. Following few lines provide a logical description of how this works, if (failure) want data = have data have data = get state of DCNM Run the module in override state with above set of data to produce the required set of diffs and push the diff payloads to DCNM. If rollback fails, the module does not attempt to rollback again, it just quits with appropriate error messages.</div>
                                                        </td>
            </tr>
                        </table>
    <br/>




Examples
--------

.. code-block:: yaml+jinja

    
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


