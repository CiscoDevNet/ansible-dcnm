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
            <th colspan="3">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
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
                        <div>List of switches being managed. Not required for state deleted</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>auth_proto</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>MD5</b>&nbsp;&larr;</div></li>
                                    <li>SHA</li>
                                    <li>MD5_DES</li>
                                    <li>MD5_AES</li>
                                    <li>SHA_DES</li>
                                    <li>SHA_AES</li>
                        </ul>
                </td>
                <td>
                        <div>Name of the authentication protocol to be used.</div>
                        <div>For POAP and RMA configurations authentication protocol should be <em>MD5</em>.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>max_hops</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">0</div>
                </td>
                <td>
                        <div>Maximum Hops to reach the switch.</div>
                        <div>This parameter is deprecated(as on 2024-03-06)</div>
                        <div>Defaults to 0 irrespective of configured value.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>poap</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Configurations of switch to Bootstrap/Pre-provision.</div>
                        <div>Please note that POAP and DHCP configurations needs to enabled in fabric configuration before adding/preprovisioning switches through POAP.</div>
                        <div>Idempotence checks against inventory is only for <b>IP Address</b> for Preprovision configs.</div>
                        <div>Idempotence checks against inventory is only for <b>IP Address</b> and <b>Serial Number</b> for Bootstrap configs.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>config_data</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Basic config data of switch to Bootstrap/Pre-provision.</div>
                        <div><code>modulesModel</code> and <code>gateway</code> are mandatory.</div>
                        <div><code>modulesModel</code> is list of model of modules in switch to Bootstrap/Pre-provision.</div>
                        <div><code>gateway</code> is the gateway IP with mask for the switch to Bootstrap/Pre-provision.</div>
                        <div>For other supported config data please refer to NDFC/DCNM configuration guide.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>discovery_password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Password for device discovery during POAP and RMA discovery</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>discovery_username</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Username for device discovery during POAP and RMA discovery</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>hostname</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Hostname of switch to Bootstrap/Pre-provision.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>image_policy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the image policy to be applied on switch during Bootstrap/Pre-provision.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>model</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Model of switch to Bootstrap/Pre-provision.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>preprovision_serial</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Serial number of switch to Pre-provision.</div>
                        <div>When <code>preprovision_serial</code> is provided along with <code>serial_number</code>, then the Preprovisioned switch(with serial number as in <code>preprovision_serial</code>) will be swapped with a actual switch(with serial number in <code>serial_number</code>) through bootstrap.</div>
                        <div>Swap feature is supported only on NDFC and is not supported on DCNM 11.x versions.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>serial_number</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Serial number of switch to Bootstrap.</div>
                        <div>When <code>preprovision_serial</code> is provided along with <code>serial_number</code>, then the Preprovisioned switch(with serial number as in <code>preprovision_serial</code>) will be swapped with a actual switch(with serial number in <code>serial_number</code>) through bootstrap.</div>
                        <div>Swap feature is supported only on NDFC and is not supported on DCNM 11.x versions.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>version</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Software version of switch to Bootstrap/Pre-provision.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>preserve_config</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Set this to false for greenfield deployment and true for brownfield deployment</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>rma</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>RMA an existing switch with a new one</div>
                        <div>Please note that the existing switch should be configured and deployed in maintenance mode</div>
                        <div>Please note that the existing switch being replaced should be shutdown state or out of network</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>config_data</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Basic config data of switch to Bootstrap for RMA.</div>
                        <div><code>modulesModel</code> and <code>gateway</code> are mandatory.</div>
                        <div><code>modulesModel</code> is list of model of modules in switch to Bootstrap for RMA.</div>
                        <div><code>gateway</code> is the gateway IP with mask for the switch to Bootstrap for RMA.</div>
                        <div>For other supported config data please refer to NDFC/DCNM configuration guide.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>discovery_password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Password for device discovery during POAP and RMA discovery</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>discovery_username</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Username for device discovery during POAP and RMA discovery</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>image_policy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the image policy to be applied on switch during Bootstrap for RMA.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>model</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Model of switch to Bootstrap for RMA.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>old_serial</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Serial number of switch to be replaced by RMA.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>serial_number</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Serial number of switch to Bootstrap for RMA.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>version</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Software version of switch to Bootstrap for RMA.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>role</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
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
                                    <li>access</li>
                                    <li>aggregation</li>
                                    <li>edge_router</li>
                                    <li>core_router</li>
                                    <li>tor</li>
                        </ul>
                </td>
                <td>
                        <div>Role which needs to be assigned to the switch</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                        <div>Login username to the switch.</div>
                        <div>For POAP and RMA configurations username should be <em>admin</em></div>
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
                        <div>Deploy the pending configuration of the fabric after inventory is updated</div>
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
                        <div>Name of the target fabric for Inventory operations</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>query_poap</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Query for Bootstrap(POAP) capable switches available.</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>save</b>
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
                        <div>Save/Recalculate the configuration of the fabric after the inventory is updated</div>
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
                                    <li>overridden</li>
                                    <li>deleted</li>
                                    <li>query</li>
                        </ul>
                </td>
                <td>
                        <div>The state of DCNM after module completion.</div>
                        <div><em>merged</em> and <em>query</em> are the only states supported for POAP.</div>
                        <div><em>merged</em> is the only state supported for RMA.</div>
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
        - seed_ip: 192.168.0.2

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

    # The following task will enable Bootstrap and DHCP on an existing fabric.
    # Please note that only bootstrap and DHCP configs are present in the below example.
    # You have to add other existing fabric configs to the task.
    - name: Bootstrap and DHCP Configuration
      cisco.dcnm.dcnm_rest:
        method: PUT
        path: /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/vxlan-fabric
        json_data: '{"fabricId": "FABRIC-7","fabricName": "vxlan-fabric","id": 7,"nvPairs":{...,"BOOTSTRAP_ENABLE": true,"DHCP_ENABLE": true,"DHCP_IPV6_ENABLE": "DHCPv4","DHCP_START": "192.168.1.10", "DHCP_END": "192.168.1.20","MGMT_GW": "192.168.123.1","MGMT_PREFIX": "24",...},"templateName": "Easy_Fabric"}' # noqa

    # The following switch will be Bootstrapped and merged into the existing fabric
    - name: Poap switch Configuration
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: merged # Only 2 options supported merged/query for poap config
        config:
        # All the values below are mandatory if poap configuration is being done - state is merged
        - seed_ip: 192.168.0.5
          user_name: switch_username
          password: switch_password
          role: border_gateway
          poap:
            - serial_number: 2A3BCDEFJKL
              model: 'N9K-C9300v'
              version: '9.3(7)'
              hostname: 'POAP_SWITCH'
              image_policy: "poap_image_policy"
              config_data:
                modulesModel: [N9K-X9364v, N9K-vSUP]
                gateway: 192.168.0.1/24

    # The following switch will be Pre-provisioned and merged into the existing fabric
    - name: Pre-provision switch Configuration
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: merged # Only 2 options supported merged/query for poap config
        config:
        # All the values below are mandatory if poap configuration is being done - state is merged
        - seed_ip: 192.168.0.4
          user_name: switch_username
          password: switch_password
          role: border
          poap:
            - preprovision_serial: 1A2BCDEFGHI
              model: 'N9K-C9300v'
              version: '9.3(7)'
              hostname: 'PREPRO_SWITCH'
              image_policy: "prepro_image_policy"
              config_data:
                modulesModel: [N9K-X9364v, N9K-vSUP]
                gateway: 192.168.0.1/24

    - name: Poap, Pre-provision and existing switch Configuration
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: merged # Only 2 options supported merged/query for poap config
        config:
        - seed_ip: 192.168.0.2
          user_name: switch_username
          password: switch_password
          role: border_gateway
          poap:
            - serial_number: 2A3BCDEFGHI
              model: 'N9K-C9300v'
              version: '9.3(7)'
              hostname: 'POAP_SWITCH'
              image_policy: "poap_image_policy"
              config_data:
                modulesModel: [N9K-X9364v, N9K-vSUP]
                gateway: 192.168.0.1/24
        - seed_ip: 192.168.0.3
          user_name: switch_username
          password: switch_password
          auth_proto: MD5
          max_hops: 0
          preserve_config: False
          role: spine
        - seed_ip: 192.168.0.4
          user_name: switch_username
          password: switch_password
          role: border
          poap:
            - preprovision_serial: 1A2BCDEFGHI
              model: 'N9K-C9300v'
              version: '9.3(7)'
              hostname: 'PREPRO_SWITCH'
              image_policy: "prepro_image_policy"
              config_data:
                modulesModel: [N9K-X9364v, N9K-vSUP]
                gateway: 192.168.0.1/24

    # The following pre-provisioned switch will be swapped with actual switch in the existing fabric
    # No Need to provide any other parameters for swap operation as bootstrap will inherit the preprovision configs
    # If other parameters are provided it will be overidden with preprovision switch configs
    # This swap feature is supported only in NDFC and not on DCNM 11.x versions
    - name: Pre-provision switch Configuration
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: merged # Only 2 options supported merged/query for poap config
        config:
        # All the values below are mandatory if poap configuration is being done - state is merged
        - seed_ip: 192.168.0.4
          user_name: switch_username
          password: switch_password
          role: border
          poap:
            - preprovision_serial: 1A2BCDEFGHI
              serial_number: 2A3BCDEFGHI

    # All the existing switches along with available Bootstrap(POAP)
    # will be queried in the existing fabric
    - name: Query all the switches in the fabric
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: query # merged / query
        query_poap: True

    # The following switch which is part of fabric will be replaced with a new switch
    # with same configurations through RMA.
    # Please note that the existing switch should be configured in maintenance mode and in shutdown state
    - name: RMA switch Configuration
      cisco.dcnm.dcnm_inventory:
        fabric: vxlan-fabric
        state: merged # Only merged is supported for rma config
        config:
        - seed_ip: 192.168.0.4
          user_name: switch_username
          password: switch_password
          rma:
            - serial_number: 2A3BCDEFJKL
              old_serial: 2A3BCDEFGHI
              model: 'N9K-C9300v'
              version: '9.3(7)'
              image_policy: "rma_image_policy"
              config_data:
                modulesModel: [N9K-X9364v, N9K-vSUP]
                gateway: 192.168.0.1/24




Status
------


Authors
~~~~~~~

- Karthik Babu Harichandra Babu(@kharicha), Praveen Ramoorthy(@praveenramoorthy)
