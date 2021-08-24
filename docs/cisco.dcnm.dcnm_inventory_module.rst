.. _cisco.dcnm.dcnm_inventory_module:


*************************
cisco.dcnm.dcnm_inventory
*************************

**Add and remove Switches from a DCNM managed VXLAN fabric.**


Version added: 0.9.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Add and remove Switches from a DCNM managed VXLAN fabric.




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
                        <div>List of switches being managed. Not required for state deleted</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>auth_proto</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>MD5</li>
                                    <li>SHA</li>
                                    <li>MD5_DES</li>
                                    <li>MD5_AES</li>
                                    <li>SHA_DES</li>
                                    <li>SHA_AES</li>
                        </ul>
                </td>
                <td>
                        <div>Name of the authentication protocol to be used</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>max_hops</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Maximum Hops to reach the switch</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Login password to the switch</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>preserve_configs</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Set this to false for greenfield deployment and true for brownfield deployment</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>role</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>leaf</b>&nbsp;&larr;</div></li>
                                    <li>spine</li>
                                    <li>border</li>
                                    <li>border_spine</li>
                                    <li>border_gateway</li>
                                    <li>border_gateway_spine</li>
                                    <li>super_spine</li>
                                    <li>border_super_spine</li>
                                    <li>border_gateway_super_spine</li>
                        </ul>
                </td>
                <td>
                        <div>Role which needs to be assigned to the switch</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>seed_ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Seed Name(support both IP address and dns_name) of the switch which needs to be added to the DCNM Fabric</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>user_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Login username to the switch</div>
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
                        <div>Name of the target fabric for Inventory operations</div>
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

.. code-block:: yaml

    # This module supports the following states:
    #
    # Merged:
    #   Switches defined in the playbook will be merged into the target fabric.
    #     - If the switch does not exist it will be added.
    #     - Switches that are not specified in the playbook will be untouched.
    #
    # Overridden:
    #   The playbook will serve as source of truth for the target fabric.
    #     - If the switch does not exist it will be added.
    #     - If the switch is not defined in the playbook but exists in DCNM it will be removed.
    #     - If the switch exists, properties that need to be modified and can be modified will be modified.
    #
    # Deleted:
    #   Deletes the list of switches specified in the playbook.
    #   If no switches are provided in the playbook, all the switches present on that DCNM fabric will be deleted.
    #
    # Query:
    #   Returns the current DCNM state for the switches listed in the playbook.


    # The following two switches will be merged into the existing fabric
    - name: Merge switch into fabric
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: merged # merged / deleted / overridden / query
        config:
        - seed_ip: 192.168.0.1
          auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
          user_name: switch_username
          password: switch_password
          max_hops: 0
          role: spine
          preserve_config: False # boolean, default is  true
        - seed_ip: 192.168.0.2
          auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
          user_name: switch_username
          password: switch_password
          max_hops: 0
          role: leaf
          preserve_config: False # boolean, default is true

    # The following two switches will be added or updated in the existing fabric and all other
    # switches will be removed from the fabric
    - name: Override Switch
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: overridden # merged / deleted / overridden / query
        config:
        - seed_ip: 192.168.0.1
          auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
          user_name: switch_username
          password: switch_password
          max_hops: 0
          role: spine
          preserve_config: False # boolean, default is  true
        - seed_ip: 192.168.0.2
          auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
          user_name: switch_username
          password: switch_password
          max_hops: 0
          role: leaf
          preserve_config: False # boolean, default is true

    # The following two switches will be deleted in the existing fabric
    - name: Delete selected switches
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: deleted # merged / deleted / overridden / query
        config:
        - seed_ip: 192.168.0.1
          auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
          user_name: switch_username
          password: switch_password
          max_hops: 0
          role: spine
          preserve_config: False # boolean, default is  true
        - seed_ip: 192.168.0.2
          auth_proto: MD5 # choose from [MD5, SHA, MD5_DES, MD5_AES, SHA_DES, SHA_AES]
          user_name: switch_username
          password: switch_password
          max_hops: 0
          role: leaf
          preserve_config: False # boolean, default is  true

    # All the switches will be deleted in the existing fabric
    - name: Delete all the switches
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: deleted # merged / deleted / overridden / query

    # The following two switches information will be queried in the existing fabric
    - name: Query switch into fabric
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: query # merged / deleted / overridden / query
        config:
        - seed_ip: 192.168.0.1
          role: spine
        - seed_ip: 192.168.0.2
          role: leaf

    # All the existing switches will be queried in the existing fabric
    - name: Query all the switches in the fabric
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: query # merged / deleted / overridden / query




Status
------


Authors
~~~~~~~

- Karthik Babu Harichandra Babu(@kharicha)
