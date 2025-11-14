.. _cisco.dcnm.dcnm_resource_manager_module:


********************************
cisco.dcnm.dcnm_resource_manager
********************************

**DCNM ansible module for managing resources.**


Version added: 2.1.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- DCNM ansible module for creating, deleting and querying resources




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
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A list of dictionaries containing resources and switch information</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>entity_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A unique name which identifies the entity to which the resourcce is allocated to.</div>
                        <div>The format of this parameter depends on the scope_type. The details are provided in</div>
                        <div>the EXAMPLES section</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pool_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the resource pool from which the resource is allocated</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pool_type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>ID</li>
                                    <li>IP</li>
                                    <li>SUBNET</li>
                        </ul>
                </td>
                <td>
                        <div>Type of resource pool</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>resource</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Value of the resource being allocated</div>
                        <div>The value will be</div>
                        <div>an integer if pool_type is ID</div>
                        <div>an IPV4/IPV6 address if pool_type is IP</div>
                        <div>an IPV4 address/net_mask or IPV6 address/net_maskif pool_type is SUBNET</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>scope_type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>fabric</li>
                                    <li>device</li>
                                    <li>device_interface</li>
                                    <li>device_pair</li>
                                    <li>link</li>
                        </ul>
                </td>
                <td>
                        <div>Socpe of resource allocation</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>switch</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address or DNS name of the management interface of the switch to which the allocated resource is assigned to.</div>
                </td>
            </tr>

            <tr>
                <td colspan="2">
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
                        <div>Name of the target fabric for resource manager operations</div>
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
                                    <li>deleted</li>
                                    <li>query</li>
                        </ul>
                </td>
                <td>
                        <div>The required state of the configuration after module completion.</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    # Entity name format
    # ==================
    #
    # The format of the entity name depends on the scope_type of the resource being allocated.

    # Scope Type                Entity Name
    # =====================================
    # Fabric                    Eg: My_Network_30000
    # Device                    Eg: loopback0
    # Device Pair               Eg: FDO21331S8T~FDO21332E6X~vPC1
    # Device Interface          Eg: FDO21332E6X~Ethernet1/13
    # Link                      Eg: FDO21332E6X~Ethernet1/3~FDO21331S8T~Ethernet1/3

    # where FDO21331S8T and FDO21331S8T are switch serial numbers

    # This module supports the following states:

    # Merged:
    #   Resources defined in the playbook will be merged into the target fabric.
    #     - If the Resources does not exist it will be added.
    #     - If the Resources exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Resources that are not specified in the playbook will be untouched.
    #
    # Deleted:
    #   Resources defined in the playbook will be deleted.
    #
    # Query:
    #   Returns the current DCNM state for the Resources listed in the playbook.

    # CREATING RESOURCES
    # ==================
    - name: Create Resources
      cisco.dcnm.dcnm_resource_manager:
        state: merged                               # choose form [merged, deleted, query]
        fabric: test_fabric
        config:
          - entity_name: "l3_vni_fabric"            # A unique name to identify the resource
            pool_type: "ID"                         # choose from ['ID', 'IP, 'SUBNET']
            pool_name: "L3_VNI"                     # Based on the 'poolType', select appropriate name
            scope_type: "fabric"                    # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
            resource: "101"                         # The value of the resource being created

          - entity_name: "9M99N34RDED~9NXHSNTEO6C"  # A unique name to identify the resource
            pool_type: "ID"                         # choose from ['ID', 'IP, 'SUBNET']
            pool_name: "VPC_ID"                     # Based on the 'poolType', select appropriate name
            scope_type: "device_pair"               # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
            switch:                                 # provide the switch information to which the given resource is to be attached
              - 192.175.1.1
              - 192.175.1.2
            resource: "500"                         # The value of the resource being created

          - entity_name: "mmudigon-2"               # A unique name to identify the resource
            pool_type: "IP"                         # choose from ['ID', 'IP, 'SUBNET']
            pool_name: "LOOPBACK0_IP_POOL"          # Based on the 'poolType', select appropriate name
            scope_type: "fabric"                    # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
            resource: "110.1.1.1"                   # The value of the resource being created

          - entity_name: "9M99N34RDED~Ethernet1/10" # A unique name to identify the resource
            pool_type: "IP"                         # choose from ['ID', 'IP, 'SUBNET']
            pool_name: "LOOPBACK1_IP_POOL"          # Based on the 'poolType', select appropriate name
            scope_type: "device_interface"          # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
            switch:                                 # provide the switch information to which the given resource is to be attached
              - 192.175.1.1
            resource: "fe:80::04"                   # The value of the resource being created

          - entity_name: "9M99N34RDED~Ethernet1/3~9NXHSNTEO6C~Ethernet1/3"  # A unique name to identify the resource
            pool_type: "SUBNET"                     # choose from ['ID', 'IP, 'SUBNET']
            pool_name: "SUBNET"                     # Based on the 'poolType', select appropriate name
            scope_type: "link"                      # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
            switch:                                 # provide the switch information to which the given resource is to be attached
              - 192.175.1.1
            resource: "fe:80:05::05/64"

    # DELETING RESOURCES
    # ==================

    - name: Delete Resources
      cisco.dcnm.dcnm_resource_manager:
        state: deleted                              # choose form [merged, deleted, query]
        fabric: test_fabric
        config:
          - entity_name: "l3_vni_fabric"            # A unique name to identify the resource
            pool_type: "ID"                         # choose from ['ID', 'IP, 'SUBNET']
            pool_name: "L3_VNI"                     # Based on the 'poolType', select appropriate name
            scope_type: "fabric"                    # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']

          - entity_name: "9M99N34RDED~9NXHSNTEO6C"  # A unique name to identify the resource
            pool_type: "ID"                         # choose from ['ID', 'IP, 'SUBNET']
            pool_name: "VPC_ID"                     # Based on the 'poolType', select appropriate name
            scope_type: "device_pair"               # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
            switch:                                 # provide the switch information to which the given resource is attached
              - 192.175.1.1
              - 192.175.1.2

          - entity_name: "mmudigon-2"               # A unique name to identify the resource
            pool_type: "IP"                         # choose from ['ID', 'IP, 'SUBNET']
            pool_name: "LOOPBACK0_IP_POOL"          # Based on the 'poolType', select appropriate name
            scope_type: "fabric"                    # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']

          - entity_name: "9M99N34RDED~Ethernet1/10" # A unique name to identify the resource
            pool_type: "IP"                         # choose from ['ID', 'IP, 'SUBNET']
            pool_name: "LOOPBACK1_IP_POOL"          # Based on the 'poolType', select appropriate name
            scope_type: "device_interface"          # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
            switch:                                 # provide the switch information to which the given resource is attached
              - 192.175.1.1

          - entity_name: "9M99N34RDED~Ethernet1/3~9NXHSNTEO6C~Ethernet1/3" # A unique name to identify the resource
            pool_type: "SUBNET"                     # choose from ['ID', 'IP, 'SUBNET']
            pool_name: "SUBNET"                     # Based on the 'poolType', select appropriate name
            scope_type: "link"                      # choose from ['fabric', 'device', device_interface', 'device_pair', 'link']
            switch:                                 # provide the switch information to which the given resource is attached
              - 192.175.1.1

    # QUERY SERVICE POLICIES
    # ======================

    - name: Query all Resources - no filters
      cisco.dcnm.dcnm_resource_manager:
        state: query                               # choose form [merged, deleted, query]
        fabric: test_fabric

    - name: Query Resources - filter by entity name
      cisco.dcnm.dcnm_resource_manager:
        state: query                                # choose form [merged, deleted, query]
        fabric: test_fabric
        config:
          - entity_name: "l3_vni_fabric"            # A unique name to identify the resource
          - entity_name: "loopback_dev"             # A unique name to identify the resource
          - entity_name: "9M99N34RDED~9NXHSNTEO6C"  # A unique name to identify the resource
          - entity_name: "9M99N34RDED~Ethernet1/10" # A unique name to identify the resource
          - entity_name: "9M99N34RDED~Ethernet1/2~~9NXHSNTEO6CEthernet1/2" # A unique name to identify the resource

    - name: Query Resources - filter by switch
      cisco.dcnm.dcnm_resource_manager:
        state: query                                # choose form [merged, deleted, query]
        fabric: test_fabric
        config:
          - switch:                                 # provide the switch information to which the given resource is attached
              - 192.175.1.1

    - name: Query Resources - filter by fabric and pool name
      cisco.dcnm.dcnm_resource_manager:
        state: query                                # choose form [merged, deleted, query]
        fabric: test_fabric
        config:
          - pool_name: "L3_VNI"                     # Based on the 'poolType', select appropriate name
          - pool_name: "VPC_ID"                     # Based on the 'poolType', select appropriate name
          - pool_name: "SUBNET"                     # Based on the 'poolType', select appropriate name

    - name: Query Resources - filter by switch and pool name
      cisco.dcnm.dcnm_resource_manager:
        state: query                                # choose form [merged, deleted, query]
        fabric: "{{ ansible_it_fabric }}"
        config:
          - pool_name: "L3_VNI"                     # Based on the 'poolType', select appropriate name
            switch:                                 # provide the switch information to which the given resource is attached
              - 192.175.1.1
          - pool_name: "LOOPBACK_ID"                # Based on the 'poolType', select appropriate name
            switch:                                 # provide the switch information to which the given resource is attached
              - 192.175.1.1
          - pool_name: "VPC_ID"                     # Based on the 'poolType', select appropriate name
            switch:                                 # provide the switch information to which the given resource is attached
              - 192.175.1.2

    - name: Query Resources - mixed query
      cisco.dcnm.dcnm_resource_manager:
        state: query                                # choose form [merged, deleted, query]
        fabric: test_fabric
        config:
          - entity_name: "l2_vni_fabric"            # A unique name to identify the resource
          - switch:                                 # provide the switch information to which the given resource is attached
              - 192.175.1.1
          - pool_name: "LOOPBACK_ID"                # Based on the 'poolType', select appropriate name
          - pool_name: "VPC_ID"                     # Based on the 'poolType', select appropriate name
            switch:                                 # provide the switch information to which the given resource is attached
              - 192.175.1.1




Status
------


Authors
~~~~~~~

- Mallik Mudigonda (@mmudigon)
