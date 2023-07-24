.. _cisco.dcnm.dcnm_interface_module:


*************************
cisco.dcnm.dcnm_interface
*************************

**DCNM Ansible Module for managing interfaces.**


Version added: 0.9.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- DCNM Ansible Module for the following interface service operations
- Create, Delete, Modify PortChannel, VPC, Loopback and Sub-Interfaces
- Modify Ethernet Interfaces




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
                    <b>check_deploy</b>
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
                        <div>Deploy operations may take considerable time in certain cases based on the configuration included in the playbook. A success response from DCNM server does not guarantee the completion of deploy operation. This flag if set indicates that the module should verify if the configured state is in sync with what is requested in playbook. If not set the module will return without verifying the state.</div>
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
                        <div>A dictionary of interface operations</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                        <div>Flag indicating if the configuration must be pushed to the switch. If not included it is considered true by default</div>
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
                        <div>Name of the interface. Example, po55, eth2/1, lo100, vpc25, eth1/1.1.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile_aa_fex</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Though the key shown here is &#x27;profile_aa_fex&#x27; the actual key to be used in playbook is &#x27;profile&#x27;. The key &#x27;profile_aa_fex&#x27; is used here to logically segregate the interface objects applicable for this profile</div>
                        <div>Object profile which must be included for active-active FEX inetrface configurations.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>admin_state</b>
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
                        <div>Administrative state of the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the FEX interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_netflow</b>
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
                        <div>Flag to enable netflow.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>port_channel_aa</li>
                        </ul>
                </td>
                <td>
                        <div>Interface mode</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mtu</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>default</li>
                                    <li><div style="color: blue"><b>jumbo</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>Interface MTU</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>netflow_monitor</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Name of netflow monitor. This parameter is required if &quot;enable_netflow&quot; is True.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_cmds</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>Commands to be included in the configuration under this interface of first peer</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_members</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Member interfaces that are part of this port channel on first peer</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_po_description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the port-channel interface of first peer</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_cmds</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>Commands to be included in the configuration under this interface of second peer</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_members</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Member interfaces that are part of this port channel on second peer</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_po_description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the port-channel interface of second peer</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile_eth</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Though the key shown here is &#x27;profile_eth&#x27; the actual key to be used in playbook is &#x27;profile&#x27;. The key &#x27;profile_eth&#x27; is used here to logically segregate the interface objects applicable for this profile</div>
                        <div>Object profile which must be included for ethernet interface configurations.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>access_vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Vlan for the interface. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;access&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>admin_state</b>
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
                        <div>Administrative state of the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>allowed_vlans</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>none</b>&nbsp;&larr;</div></li>
                                    <li>all</li>
                                    <li>vlan-range(e.g., 1-2, 3-40)</li>
                        </ul>
                </td>
                <td>
                        <div>Vlans that are allowed on this interface. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>bpdu_guard</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>true</b>&nbsp;&larr;</div></li>
                                    <li>false</li>
                                    <li>no</li>
                        </ul>
                </td>
                <td>
                        <div>Spanning-tree bpduguard</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cmds</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>Commands to be included in the configuration under this interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>int_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"default"</div>
                </td>
                <td>
                        <div>Interface VRF name. This object is applicable only if the &#x27;mode&#x27; is &#x27;routed&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv4_addr</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>IPV4 address of the interface. This object is applicable only if the &#x27;mode&#x27; is &#x27;routed&#x27; or &#x27;epl_routed&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv4_mask_len</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">8</div>
                </td>
                <td>
                        <div>IPV4 address mask length. This object is applicable only if the &#x27;mode&#x27; is &#x27;routed&#x27; or &#x27;epl_routed&#x27;</div>
                        <div>Minimum Value (1), Maximum Value (31)</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv6_addr</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>IPV6 address of the interface. This object is applicable only if the &#x27;mode&#x27; is &#x27;epl_routed&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv6_mask_len</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">8</div>
                </td>
                <td>
                        <div>IPV6 address mask length. This object is applicable only if the &#x27;mode&#x27; is &#x27;epl_routed&#x27;</div>
                        <div>Minimum Value (1), Maximum Value (31)</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>trunk</li>
                                    <li>access</li>
                                    <li>routed</li>
                                    <li>monitor</li>
                                    <li>epl_routed</li>
                        </ul>
                </td>
                <td>
                        <div>Interface mode</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mtu</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Interface MTU.</div>
                        <div>Can be specified either &quot;default&quot; or &quot;jumbo&quot; for access and trunk interface types. If not specified, it defaults to &quot;jumbo&quot;</div>
                        <div>Can be specified with any value within 576 and 9216 for routed interface types. If not specified, it defaults to 9216</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>port_type_fast</b>
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
                        <div>Spanning-tree edge port behavior</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>route_tag</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Route tag associated with the interface IP. This object is applicable only if the &#x27;mode&#x27; is &#x27;routed&#x27; or &#x27;epl_routed&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>speed</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>Auto</b>&nbsp;&larr;</div></li>
                                    <li>100Mb</li>
                                    <li>1Gb</li>
                                    <li>10Gb</li>
                                    <li>25Gb</li>
                                    <li>40Gb</li>
                                    <li>100Gb</li>
                        </ul>
                </td>
                <td>
                        <div>Speed of the interface.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile_lo</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Though the key shown here is &#x27;profile_lo&#x27; the actual key to be used in playbook is &#x27;profile&#x27;. The key &#x27;profile_lo&#x27; is used here to logically segregate the interface objects applicable for this profile</div>
                        <div>Object profile which must be included for loopback interface configurations.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>admin_state</b>
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
                        <div>Administrative state of the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cmds</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>Commands to be included in the configuration under this interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>int_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"default"</div>
                </td>
                <td>
                        <div>Interface VRF name.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv4_addr</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>IPV4 address of the interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv6_addr</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>IPV6 address of the interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>lo</li>
                        </ul>
                </td>
                <td>
                        <div>Interface mode</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>route_tag</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Route tag associated with the interface IP.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile_pc</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Though the key shown here is &#x27;profile_pc&#x27; the actual key to be used in playbook is &#x27;profile&#x27;. The key &#x27;profile_pc&#x27; is used here to logically segregate the interface objects applicable for this profile</div>
                        <div>Object profile which must be included for port channel interface configurations.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>access_vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Vlan for the interface. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;access&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>admin_state</b>
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
                        <div>Administrative state of the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cmds</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>Commands to be included in the configuration under this interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>int_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"default"</div>
                </td>
                <td>
                        <div>Interface VRF name. This object is applicable only if the &#x27;mode&#x27; is &#x27;l3&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv4_addr</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>IPV4 address of the interface. This object is applicable only if the &#x27;mode&#x27; is &#x27;l3&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv4_mask_len</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">8</div>
                </td>
                <td>
                        <div>IPV4 address mask length. This object is applicable only if the &#x27;mode&#x27; is &#x27;l3&#x27;</div>
                        <div>Minimum Value (1), Maximum Value (31)</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>members</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Member interfaces that are part of this port channel</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>trunk</li>
                                    <li>access</li>
                                    <li>l3</li>
                                    <li>monitor</li>
                        </ul>
                </td>
                <td>
                        <div>Interface mode</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>route_tag</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Route tag associated with the interface IP. This object is applicable only if the &#x27;mode&#x27; is &#x27;l3&#x27;</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile_st_fex</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Though the key shown here is &#x27;profile_st_fex&#x27; the actual key to be used in playbook is &#x27;profile&#x27;. The key &#x27;profile_st_fex&#x27; is used here to logically segregate the interface objects applicable for this profile</div>
                        <div>Object profile which must be included for straigth-through FEX interface configurations.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>admin_state</b>
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
                        <div>Administrative state of the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cmds</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>Commands to be included in the configuration under this interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the FEX interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_netflow</b>
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
                        <div>Flag to enable netflow.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>members</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Member interfaces that are part of this FEX</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>port_channel_st</li>
                        </ul>
                </td>
                <td>
                        <div>Interface mode</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mtu</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>default</li>
                                    <li><div style="color: blue"><b>jumbo</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>Interface MTU.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>netflow_monitor</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Name of netflow monitor. This parameter is required if &quot;enable_netflow&quot; is True.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>po_description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the port-channel which is part of the FEX interface</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile_subint</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Though the key shown here is &#x27;profile_subint&#x27; the actual key to be used in playbook is &#x27;profile&#x27;. The key &#x27;profile_subint&#x27; is used here to logically segregate the interface objects applicable for this profile</div>
                        <div>Object profile which must be included for sub-interface configurations.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>admin_state</b>
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
                        <div>Administrative state of the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cmds</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>Commands to be included in the configuration under this interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>int_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"default"</div>
                </td>
                <td>
                        <div>Interface VRF name.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv4_addr</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>IPV4 address of the interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv4_mask_len</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">8</div>
                </td>
                <td>
                        <div>IPV4 address mask length.</div>
                        <div>Minimum Value (8), Maximum Value (31)</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv6_addr</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>IPV6 address of the interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv6_mask_len</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">8</div>
                </td>
                <td>
                        <div>IPV6 address mask length.</div>
                        <div>Minimum Value (1), Maximum Value (31)</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>subint</li>
                        </ul>
                </td>
                <td>
                        <div>Interface mode</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mtu</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">9216</div>
                </td>
                <td>
                        <div>Interface MTU</div>
                        <div>Minimum Value (567), Maximum Value (9216)</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">0</div>
                </td>
                <td>
                        <div>DOT1Q vlan id for this interface</div>
                        <div>Minimum Value (2), Maximum Value (3967)</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile_svi</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Though the key shown here is &#x27;profile_svi&#x27; the actual key to be used in playbook is &#x27;profile&#x27;. The key &#x27;profile_svi&#x27; is used here to logically segregate the interface objects applicable for this profile</div>
                        <div>Object profile which must be included for SVI interface configurations.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>admin_state</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Administrative state of the interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>adv_subnet_in_underlay</b>
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
                        <div>Flag to enable/disable advertisements of subnets into underlay.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cmds</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>Commands to be included in the configuration under this interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_server_addr1</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>DHCP relay server address.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_server_addr2</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>DHCP relay server address.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_server_addr3</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>DHCP relay server address.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disable_ip_redirects</b>
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
                        <div>Flag to enable/disable IP redirects.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_hsrp</b>
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
                        <div>Flag to enable/disable HSRP on the interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_netflow</b>
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
                        <div>Flag to enable netflow.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>hsrp_group</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>HSRP group. This parameter is required if &quot;enable_hsrp&quot; is True.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>hsrp_priority</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>HSRP priority.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>hsrp_version</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>1</b>&nbsp;&larr;</div></li>
                                    <li>2</li>
                        </ul>
                </td>
                <td>
                        <div>HSRP protocol version.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>hsrp_vip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Virtual IP address for HSRP. This parameter is required if &quot;enable_hsrp&quot; is True.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>hsrp_vmac</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>HSRP virtual MAC.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>int_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"default"</div>
                </td>
                <td>
                        <div>Interface VRF name.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv4_addr</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>IPV4 address of the interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv4_mask_len</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IPV4 address mask length. This parameter is required if &#x27;ipv4_addr&#x27; is included.</div>
                        <div>Minimum Value (1), Maximum Value (31)</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>vlan</li>
                        </ul>
                </td>
                <td>
                        <div>Interface mode.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mtu</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">9216</div>
                </td>
                <td>
                        <div>Interface MTU.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>netflow_monitor</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Name of netflow monitor. This parameter is required if &quot;enable_netflow&quot; is True.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>preempt</b>
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
                        <div>Flag to enable/disable overthrow of low priority active routers. This parameter is valid only if &quot;enable_hsrp&quot; is True.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>route_tag</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Route tag associated with the interface IP.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_dhcp1</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>VRF to reach DHCP server. This parameter is required if &quot;dhcp_server_addr1&quot; is included.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_dhcp2</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>VRF to reach DHCP server. This parameter is required if &quot;dhcp_server_addr2&quot; is included.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_dhcp3</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>VRF to reach DHCP server. This parameter is required if &quot;dhcp_server_addr3&quot; is included.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile_vpc</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Though the key shown here is &#x27;profile_vpc&#x27; the actual key to be used in playbook is &#x27;profile&#x27;. The key &#x27;profile_vpc&#x27; is used here to logically segregate the interface objects applicable for this profile</div>
                        <div>Object profile which must be included for virtual port channel inetrface configurations.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>admin_state</b>
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
                        <div>Administrative state of the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>bpdu_guard</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>true</b>&nbsp;&larr;</div></li>
                                    <li>false</li>
                                    <li>no</li>
                        </ul>
                </td>
                <td>
                        <div>Spanning-tree bpduguard</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>trunk</li>
                                    <li>access</li>
                        </ul>
                </td>
                <td>
                        <div>Interface mode</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mtu</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>default</li>
                                    <li><div style="color: blue"><b>jumbo</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>Interface MTU</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pc_mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>active</b>&nbsp;&larr;</div></li>
                                    <li>passive</li>
                                    <li>on</li>
                        </ul>
                </td>
                <td>
                        <div>Port channel mode</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_access_vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Vlan for the interface of first peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;access&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_allowed_vlans</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>none</b>&nbsp;&larr;</div></li>
                                    <li>all</li>
                                    <li>vlan-range(e.g., 1-2, 3-40)</li>
                        </ul>
                </td>
                <td>
                        <div>Vlans that are allowed on this interface of first peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_cmds</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>Commands to be included in the configuration under this interface of first peer</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the interface of first peer</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_members</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Member interfaces that are part of this port channel on first peer</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_pcid</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Port channel identifier of first peer. If this object is not included, then the value defaults to the vPC identifier. This value cannot be changed once vPC is created</div>
                        <div>Minimum Value (1), Maximum Value (4096)</div>
                        <div>Default value if not specified is the vPC port identifier</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_access_vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Vlan for the interface of second peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;access&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_allowed_vlans</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>none</b>&nbsp;&larr;</div></li>
                                    <li>all</li>
                                    <li>vlan-range(e.g., 1-2, 3-40)</li>
                        </ul>
                </td>
                <td>
                        <div>Vlans that are allowed on this interface of second peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_cmds</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>Commands to be included in the configuration under this interface of second peer</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description of the interface of second peer</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_members</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Member interfaces that are part of this port channel on second peer</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_pcid</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Port channel identifier of second peer. If this object is not included, then the value defaults to the vPC identifier. This value cannot be changed once vPC is created</div>
                        <div>Minimum Value (1), Maximum Value (4096)</div>
                        <div>Default value if not specified is the vPC port identifier</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>port_type_fast</b>
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
                        <div>Spanning-tree edge port behavior</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>switch</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address or DNS name of the management interface. All switches mentioned in this list will be deployed with the included configuration. For vPC interfaces this list object will contain elements each of which is a list of pair of switches</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>pc</li>
                                    <li>vpc</li>
                                    <li>sub_int</li>
                                    <li>lo</li>
                                    <li>eth</li>
                                    <li>svi</li>
                                    <li>st-fex</li>
                                    <li>aa-fex</li>
                        </ul>
                </td>
                <td>
                        <div>Interface type. Example, pc, vpc, sub_int, lo, eth, svi</div>
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
                        <div>Flag indicating if the configuration must be pushed to the switch. This flag is used to decide the deploy behavior in &#x27;deleted&#x27; and &#x27;overridden&#x27; states as mentioned below</div>
                        <div>In &#x27;overridden&#x27; state this flag will be used to deploy deleted interfaces.</div>
                        <div>In &#x27;deleted&#x27; state this flag will be used to deploy deleted interfaces when a specific &#x27;config&#x27; block is not included.</div>
                        <div>The &#x27;deploy&#x27; flags included with individual interface configuration elements under the &#x27;config&#x27; block will take precedence over this global flag.</div>
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
                        <div>Name of the target fabric for interface operations</div>
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
                        <div>The required state of the configuration after module completion.</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    # States:
    # This module supports the following states:
    #
    # Merged:
    #   Interfaces defined in the playbook will be merged into the target fabric.
    #
    #   The interfaces listed in the playbook will be created if not already present on the DCNM
    #   server. If the interface is already present and the configuration information included
    #   in the playbook is either different or not present in DCNM, then the corresponding
    #   information is added to the interface on DCNM. If an interface mentioned in playbook
    #   is already present on DCNM and there is no difference in configuration, no operation
    #   will be performed for such interface.
    #
    # Replaced:
    #   Interfaces defined in the playbook will be replaced in the target fabric.
    #
    #   The state of the interfaces listed in the playbook will serve as source of truth for the
    #   same interfaces present on the DCNM under the fabric mentioned. Additions and updations
    #   will be done to bring the DCNM interfaces to the state listed in the playbook.
    #   Note: Replace will only work on the interfaces mentioned in the playbook.
    #
    # Overridden:
    #   Interfaces defined in the playbook will be overridden in the target fabric.
    #
    #   The state of the interfaces listed in the playbook will serve as source of truth for all
    #   the interfaces under the fabric mentioned. Additions and deletions will be done to bring
    #   the DCNM interfaces to the state listed in the playbook. All interfaces other than the
    #   ones mentioned in the playbook will either be deleted or reset to default state.
    #   Note: Override will work on the all the interfaces present in the DCNM Fabric.
    #
    # Deleted:
    #   Interfaces defined in the playbook will be deleted in the target fabric.
    #
    #   Deletes the list of interfaces specified in the playbook.  If the playbook does not include
    #   any switches or interface information, then all interfaces from all switches in the
    #   fabric will either be deleted or put to default state. If configuuration includes information
    #   pertaining to any particular switch, then interfaces belonging to that switch will either be
    #   deleted or put to default. If configuration includes both interface and switch information,
    #   then the specified interfaces will either be deleted or reset on all the seitches specified
    #
    # Query:
    #   Returns the current DCNM state for the interfaces listed in the playbook.

    # LOOPBACK INTERFACE

    - name: Create loopback interfaces
      cisco.dcnm.dcnm_interface: &lo_merge
        fabric: mmudigon-fabric
        state: merged                         # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: lo100                       # should be of the form lo<port-id>
            type: lo                          # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:
              - "192.172.1.1"                 # provide the switch where to deploy the config
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: true               # choose from [true, false]
              mode: lo                        # choose from [lo]
              int_vrf: ""                     # VRF name
              ipv4_addr: 192.169.10.1         # ipv4 address for the loopback interface
              ipv6_addr: fd01::0201           # ipV6 address for the loopback interface
              route_tag: ""                   # Routing Tag for the interface
              cmds:                           # Freeform config
                - no shutdown
              description: "loopback interface 100 configuration"

    - name: Replace loopback interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: replaced                       # only choose from [merged, replaced, deleted, overridden. query]
        config:
          - name: lo100                       # should be of the form lo<port-id>
            type: lo                          # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:
              - "192.172.1.1"                 # provide the switch where to deploy the config
            deploy: true                      ## choose from [true, false]
            profile:
              admin_state: false              ## choose from [true, false]
              mode: lo                        # choose from [lo]
              int_vrf: ""                     # VRF name
              ipv4_addr: 192.169.12.1         ## ipv4 address for the loopback interface
              ipv6_addr: fd01:0203            # ipV6 address for the loopback interface
              route_tag: "100"                ## Routing Tag for the interface
              cmds:                           # Freeform config
                - no shutdown
              description: "loopback interface 100 configuration - replaced"

    # To delete or reset all interfaces on all switches in the fabric
    - name: Delete loopback interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]

    # To delete or reset all interfaces on a specific switch in the fabric
    - name: Delete loopback interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - switch:
              - "192.172.1.1"                 # provide the switch where to deploy the config

    # To delete or reset a particular interface on all switches in the fabric
    - name: Delete loopback interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: lo100                       # should be of the form lo<port-id>

    # To delete or reset a particular interface on a specific switch in the fabric
    - name: Delete loopback interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: lo100                       # should be of the form lo<port-id>
            switch:
              - "192.172.1.1"                 # provide the switch where to deploy the config

    # To override with a particular interface configuration
    - name: Override loopback interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: overridden                     # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: lo103                       # should be of the form lo<port-id>
            type: lo                          # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:
              - "192.172.1.1"                 # provide the switch where to deploy the config
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: true               # choose from [true, false]
              mode: lo                        # choose from [lo]
              int_vrf: ""                     # VRF name
              ipv4_addr: 192.169.14.1         # ipv4 address for the loopback interface
              ipv6_addr: fd01::0205           # ipV6 address for the loopback interface
              route_tag: ""                   # Routing Tag for the interface
              cmds:                           # Freeform config
                - no shutdown
              description: "loopback interface 103 configuration - overridden"

    # To override all interface on all switches in the fabric
    - name: Override loopback interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: overridden                     # only choose from [merged, replaced, deleted, overridden, query]

    # To override all interfaces on a particular switche in the fabric
    - name: Override loopback interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: overridden                     # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - switch:
              - "192.172.1.1"                 # provide the switch where to deploy the config

    # PORTCHANNEL INTERFACE

    - name: Create port channel interfaces
      cisco.dcnm.dcnm_interface: &pc_merge
        fabric: mmudigon-fabric
        state: merged                         # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: po300                       # should be of the form po<port-id>
            type: pc                          # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:
              - "192.172.1.1"                 # provide the switch information where the config is to be deployed
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: true               # choose from [true, false]
              mode: trunk                     # choose from [trunk, access, l3, monitor]
              members:                        # member interfaces
                - e1/10
              pc_mode: 'on'                   # choose from ['on', 'active', 'passive']
              bpdu_guard: true                # choose from [true, false, no]
              port_type_fast: true            # choose from [true, false]
              mtu: jumbo                      # choose from [default, jumbo]
              allowed_vlans: none             # choose from [none, all, vlan range]
              cmds:                           # Freeform config
                - no shutdown
              description: "port channel acting as trunk"

          - name: po301                       # should be of the form po<port-id>
            type: pc                          # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:
              - "192.172.1.1"                 # provide the switch information where the config is to be deployed
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: false              # choose from [true, false]
              mode: access                    # choose from [trunk, access, l3, monitor]
              members:                        # member interfaces
                - e1/11
              pc_mode: 'on'                   # choose from ['on', 'active', 'passive']
              bpdu_guard: true                # choose from [true, false, no]
              port_type_fast: true            # choose from [true, false]
              mtu: default                    # choose from [default, jumbo]
              access_vlan: 301                #
              cmds:                           # Freeform config
                - no shutdown
              description: "port channel acting as access"

    - name: Replace port channel interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: replaced                       # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: po300                       # should be of the form po<port-id>
            type: pc                          # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:
              - "192.172.1.1"                 # provide the switch information where the config is to be deployed
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: false              ## choose from [true, false]
              mode: trunk                     # choose from [trunk, access, l3, monitor]
              members:                        # member interfaces
                - e1/10
              pc_mode: 'active'               ## choose from ['on', 'active', 'passive']
              bpdu_guard: false               ## choose from [true, false, no]
              port_type_fast: false           ## choose from [true, false]
              mtu: default                    ## choose from [default, jumbo]
              allowed_vlans: all              ## choose from [none, all, vlan range]
              cmds:                           # Freeform config
                - no shutdown
              description: "port channel acting as trunk - replace"

    # To delete or reset a particular interface on a specific switch in the fabric
    - name: Delete port channel interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: po300                       # should be of the form po<port-id>
            switch:
              - "192.172.1.1"                 # provide the switch information where the config is to be deployed

    # To delete or reset all interfaces on all switches in the fabric
    - name: Delete port channel interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]

    # To delete or reset a particular interface on all switches in the fabric
    - name: Delete port-channel interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: po300                       # should be of the form po<port-id>

    # To delete or reset all interfaces on a specific switch in the fabric
    - name: Delete port channel interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - switch:
              - "192.172.1.1"                 # provide the switch information where the config is to be deployed

    - name: Override port channel interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: overridden                     # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: po320                       # should be of the form po<port-id>
            type: pc                          # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:
              - "192.172.1.1"                 # provide the switch information where the config is to be deployed
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: true               # choose from [true, false]
              mode: trunk                     # choose from [trunk, access, l3, monitor]
              members:                        # member interfaces
                - e1/10
              pc_mode: 'on'                   # choose from ['on', 'active', 'passive']
              bpdu_guard: true                # choose from [true, false, no]
              port_type_fast: true            # choose from [true, false]
              mtu: jumbo                      # choose from [default, jumbo]
              allowed_vlans: none             # choose from [none, all, vlan range]
              cmds:                           # Freeform config
                - no shutdown
              description: "port channel acting as trunk"

    # SUB-INTERFACE

    - name: Create sub-interfaces
      cisco.dcnm.dcnm_interface: &sub_merge
        fabric: mmudigon-fabric
        state: merged                         # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: eth1/1.1                    # should be of the form eth<port-num>.<port-id>
            type: sub_int                     # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:
              - "192.172.1.1"                 # provide the switch information where the config is to be deployed
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: true               # choose from [true, false]
              mode: subint                    # choose from [subint]
              vlan: 100                       # vlan ID [min:2, max:3967]
              int_vrf: ""                     # VRF name
              ipv4_addr: 192.168.30.1         # ipv4 address for the sub-interface
              ipv4_mask_len: 24               # choose between [min:8, max:31]
              ipv6_addr: fd01::0401           # ipV6 address for the sub-interface
              ipv6_mask_len: 64               # choose between [min:64, max:127]
              mtu: 9216                       # choose between [min:576, max:9216]
              cmds:                           # Freeform config
                - no shutdown
              description: "sub interface eth1/1.1 configuration"

    - name: Replace sub-interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: replaced                       # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: eth1/1.1                    # should be of the form eth<port-num>.<port-id>
            type: sub_int                     # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:
              - "192.172.1.1"                 # provide the switch information where the config is to be deployed
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: false              ## choose from [true, false]
              mode: subint                    # choose from [subint]
              vlan: 200                       ## vlan ID [min:2, max:3967]
              int_vrf: ""                     # VRF name
              ipv4_addr: 192.168.32.1         ## ipv4 address for the sub-interface
              ipv4_mask_len: 20               # choose between [min:8, max:31]
              ipv6_addr: fd01::0403           # ipV6 address for the sub-interface
              ipv6_mask_len: 64               # choose between [min:64, max:127]
              mtu: 1500                       ## choose between [min:576, max:9216]
              cmds:                           # Freeform config
                - no shutdown
              description: "sub interface eth1/1.1 configuration - replace"

    # To delete or reset all interfaces on all switches in the fabric
    - name: Delete sub-interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]

    # To delete or reset a particular interface on all switches in the fabric
    - name: Delete port-channel interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: deleted                        # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: eth1/1.1                    # should be of the form eth<port-num>.<port-id>

    - name: Override sub-interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: overridden                     # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: eth1/1.3                    # should be of the form eth<port-num>.<port-id>
            type: sub_int                     # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:
              - "192.172.1.1"                 # provide the switch information where the config is to be deployed
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: true               # choose from [true, false]
              mode: subint                    # choose from [subint]
              vlan: 103                       # vlan ID [min:2, max:3967]
              int_vrf: ""                     # VRF name
              ipv4_addr: 192.168.35.1         # ipv4 address for the sub-interface
              ipv4_mask_len: 24               # choose between [min:8, max:31]
              ipv6_addr: fd01::0405           # ipV6 address for the sub-interface
              ipv6_mask_len: 64               # choose between [min:64, max:127]
              mtu: 9216                       # choose between [min:576, max:9216]
              cmds:                           # Freeform config
                - no shutdown
              description: "sub interface eth1/1.3 configuration - override"

    # VPC INTERFACE

    - name: Create vPC interfaces
      cisco.dcnm.dcnm_interface: &vpc_merge
        fabric: mmudigon-fabric
        state: merged                         # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: vpc750                      # should be of the form vpc<port-id>
            type: vpc                         # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:                           # provide switches of vPC pair
              - ["192.172.1.1",
                 "192.172.1.2"]
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: true               # choose from [true, false]
              mode: trunk                     # choose from [trunk, access]
              peer1_pcid: 100                 # choose between [Min:1, Max:4096], if not given, will be VPC port-id
              peer2_pcid: 100                 # choose between [Min:1, Max:4096], if not given, will be VPC port-id
              peer1_members:                  # member interfaces on peer 1
                - e1/24
              peer2_members:                  # member interfaces on peer 2
                - e1/24
              pc_mode: 'active'               # choose from ['on', 'active', 'passive']
              bpdu_guard: true                # choose from [true, false, 'no']
              port_type_fast: true            # choose from [true, false]
              mtu: jumbo                      # choose from [default, jumbo]
              peer1_allowed_vlans: none       # choose from [none, all, vlan range]
              peer2_allowed_vlans: none       # choose from [none, all, vlan range]
              peer1_description: "VPC acting as trunk peer1"
              peer2_description: "VPC acting as trunk peer2"


    - name: Replace vPC interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: replaced                         # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: vpc750                      # should be of the form vpc<port-id>
            type: vpc                         # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:                           # provide switches of vPC pair
              - ["192.172.1.1",
                 "192.172.1.2"]
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: false              ## choose from [true, false]
              mode: trunk                     # choose from [trunk, access]
              peer1_pcid: 100                 # choose between [Min:1, Max:4096], if not given, will be VPC port-id
              peer2_pcid: 100                 # choose between [Min:1, Max:4096], if not given, will be VPC port-id
              peer1_members:                  ## member interfaces on peer 1
                - e1/26
              peer2_members:                  ## member interfaces on peer 2
                - e1/26
              pc_mode: 'active'               ## choose from ['on', 'active', 'passive']
              bpdu_guard: false               ## choose from [true, false, 'no']
              port_type_fast: false           ## choose from [true, false]
              mtu: default                    ## choose from [default, jumbo]
              peer1_allowed_vlans: all        ## choose from [none, all, vlan range]
              peer2_allowed_vlans: all        ## choose from [none, all, vlan range]
              peer1_description: "VPC acting as trunk peer1 - modified"
              peer2_description: "VPC acting as trunk peer2 - modified"
              peer1_cmds:                     # Freeform config
                  - no shutdown
              peer2_cmds:                     # Freeform config
                  - no shutdown

    # To delete or reset a particular interface on a specific switch in the fabric
    - name: Delete vPC interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: deleted                         # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: vpc750                      # should be of the form vpc<port-id>
            switch:                           # provide switches of vPC pair
              - ["192.172.1.1",
                 "192.172.1.2"]

    - name: Override vPC interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: overridden                         # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - name: vpc752                      # should be of the form vpc<port-id>
            type: vpc                         # choose from this list [pc, vpc, sub_int, lo, eth]
            switch:                           # provide switches of vPC pair
              - ["192.172.1.1",
                 "192.172.1.2"]
            deploy: true                      # choose from [true, false]
            profile:
              admin_state: true               # choose from [true, false]
              mode: trunk                     # choose from [trunk, access]
              peer1_pcid: 752                 # choose between [Min:1, Max:4096], if not given, will be VPC port-id
              #peer2_pcid: 1                  # choose between [Min:1, Max:4096], if not given, will be VPC port-id
              peer1_members:                  # member interfaces on peer 1
                - e1/26
              peer2_members:                  # member interfaces on peer 2
                - e1/27
              pc_mode: 'on'                   # choose from ['on', 'active', 'passive']
              bpdu_guard: true                # choose from [true, false, no]
              port_type_fast: true            # choose from [true, false]
              mtu: jumbo                      # choose from [default, jumbo]
              peer1_allowed_vlans: none       # choose from [none, all, vlan range]
              peer2_allowed_vlans: none       # choose from [none, all, vlan range]
              peer1_description: "VPC acting as trunk peer1"
              peer2_description: "VPC acting as trunk peer2"
              peer1_cmds:                     # Freeform config
                  - no shutdown
                  - no shutdown
              peer2_cmds:                     # Freeform config
                  - no shutdown
                  - no shutdown

    # SVI INTERFACES

    - name: Create SVI interfaces including optional parameters
      cisco.dcnm.dcnm_interface:
        check_deploy: true
        fabric: "{{ ansible_svi_fabric }}"
        state: merged                                   # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: vlan1001                              # should be of the form vlan<vlan-id>
            type: svi                                   # choose from this list [pc, vpc, sub_int, lo, eth, svi]
            switch:
              - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
            deploy: true                                # choose from [true, false]
            profile:
              int_vrf: blue                             # optional, Interface VRF name, default is "default"
              ipv4_addr: 192.168.2.1                    # optional, Interfae IP, default is ""
              ipv4_mask_len: 24                         # optional, IP mask length, default is ""
              mtu: 9216                                 # optional, MTU default is ""
              route_tag: 1001                           # optional, Routing TAG, default is ""
              disable_ip_redirects: true                # optional, flag to enable/disable IP redirects, default is "false"
              cmds:                                     # Freeform config
                - no shutdown
              admin_state: true                         # Flag to enable/disable Vlan interaface
              enable_hsrp: true                         # optional, flag to enable/disable HSRP on the interface, default is "false"
              hsrp_vip: 192.168.2.100                   # optional, Virtual IP address for HSRP, default is ""
              hsrp_group: 10                            # optional, HSRP group, default is ""
              hsrp_priority: 5                          # optional, HSRP priority, default is ""
              hsrp_vmac: 0000.0101.ac0a                 # optional, HSRP virtual MAC, default is ""
              dhcp_server_addr1: 192.200.1.1            # optional, DHCP relay server address, default is ""
              vrf_dhcp1: blue                           # optional, VRF to reach DHCP server. default is ""
              dhcp_server_addr2: 192.200.1.2            # optional, DHCP relay server address, default is ""
              vrf_dhcp2: blue                           # optional, VRF to reach DHCP server. default is ""
              dhcp_server_addr3: 192.200.1.3            # optional, DHCP relay server address, default is ""
              vrf_dhcp3: blue                           # optional, VRF to reach DHCP server. default is ""
              adv_subnet_in_underlay: true              # optional, flag to enable/disable advertisements of subnets into underlay, default is "false"
              enable_netflow: false                     # optional, flag to enable netflow, default is "false"
              netflow_monitor: svi1001                  # optional, name of netflow monitor, default is ""
              hsrp_version: 1                           # optional, HSRP protocol version, default is 1
              preempt: true                             # optional, flag to enable/disable overthrow of low priority active routers, optional is "false"
              mode: vlan                                # choose from [vlan, vlan_admin_state], default is "vlan"
              description: Switched vlan interface 1001 # optional, Interface description, default is ""

    - name: Replace SVI interface
      cisco.dcnm.dcnm_interface:
        check_deploy: true
        fabric: "{{ ansible_svi_fabric }}"
        state: replaced                                       # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: vlan1001                                    # should be of the form vlan<vlan-id>
            type: svi                                         # choose from this list [pc, vpc, sub_int, lo, eth, svi]
            switch:
              - "{{ ansible_switch1 }}"                       # provide the switch information where the config is to be deployed
            deploy: true                                      # choose from [true, false]
            profile:
              int_vrf: red                                    # optional, Interface VRF name, default is "default"
              ipv4_addr: 192.169.2.1                          # optional, Interfae IP, default is ""
              ipv4_mask_len: 20                               # optional, IP mask length, default is ""
              mtu: 9210                                       # optional, MTU default is ""
              route_tag: 1002                                 # optional, Routing TAG, default is ""
              disable_ip_redirects: false                     # optional, flag to enable/disable IP redirects, default is "false"
              cmds:                                           # Freeform config
                - no shutdown
              admin_state: false                              # Flag to enable/disable Vlan interaface
              enable_hsrp: true                               # optional, flag to enable/disable HSRP on the interface, default is "false"
              hsrp_vip: 192.169.2.100                         # optional, Virtual IP address for HSRP, default is ""
              hsrp_group: 11                                  # optional, HSRP group, default is ""
              hsrp_priority: 5                                # optional, HSRP priority, default is ""
              hsrp_vmac: 0000.0102.ac0a                       # optional, HSRP virtual MAC, default is ""
              dhcp_server_addr1: 193.200.1.1                  # optional, DHCP relay server address, default is ""
              vrf_dhcp1: green                                # optional, VRF to reach DHCP server. default is ""
              dhcp_server_addr2: 193.200.1.2                  # optional, DHCP relay server address, default is ""
              vrf_dhcp2: green                                # optional, VRF to reach DHCP server. default is ""
              dhcp_server_addr3: 193.200.1.3                  # optional, DHCP relay server address, default is ""
              vrf_dhcp3: green                                # optional, VRF to reach DHCP server. default is ""
              adv_subnet_in_underlay: false                   # optional, flag to enable/disable advertisements of subnets into underlay, default is "false"
              enable_netflow: false                           # optional, flag to enable netflow, default is "false"
              netflow_monitor: svi1002                        # optional, name of netflow monitor, default is ""
              hsrp_version: 2                                 # optional, HSRP protocol version, default is 1
              preempt: false                                  # optional, flag to enable/disable overthrow of low priority active routers, optional is "false"
              mode: vlan                                      # choose from [vlan, vlan_admin_state], default is "vlan"
              description: Switched vlan interface 1001 - Rep # optional, Interface description, default is ""

    - name: Delete SVI interfaces
      cisco.dcnm.dcnm_interface:
        check_deploy: True
        fabric: "{{ ansible_svi_fabric }}"
        state: deleted                        # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: vlan1000                    # should be of the form vlan<vlan-id>
            type: svi                         # choose from this list [pc, vpc, sub_int, lo, eth, svi]
            switch:
              - "{{ ansible_switch1 }}"       # provide the switch where to deploy the config

          - name: vlan1001                    # should be of the form vlan<vlan-id>
            type: svi                         # choose from this list [pc, vpc, sub_int, lo, eth, svi]
            switch:
              - "{{ ansible_switch1 }}"       # provide the switch where to deploy the config

    - name: Override SVI interface
      cisco.dcnm.dcnm_interface:
        check_deploy: true
        fabric: "{{ ansible_svi_fabric }}"
        state: overridden                                     # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: vlan1002                                    # should be of the form vlan<vlan-id>
            type: svi                                         # choose from this list [pc, vpc, sub_int, lo, eth, svi]
            switch:
              - "{{ ansible_switch1 }}"                       # provide the switch information where the config is to be deployed
            deploy: true                                      # choose from [true, false]
            profile:
              admin_state: true                               # Flag to enable/disable Vlan interaface
              mode: vlan                                      # choose from [vlan, vlan_admin_state], default is "vlan"

    # AA FEX INTERFACES

    - name: Create AA FEX interfaces including optional parameters
      cisco.dcnm.dcnm_interface:
        check_deploy: True
        fabric: "{{ ansible_svi_fabric }}"
        state: merged                                   # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: vpc151                                # should be of the form vpc<id>
            type: aa_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
            switch:
              - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
            deploy: true                                # choose from [true, false]
            profile:
              description: "AA FEX interface 151"       # optional, description of FEX interface, default is ""
              peer1_members:                            # optional, member interfaces, default is []
                - e1/10
              peer2_members:                            # optional, member interfaces, default is []
                - e1/10
              mtu: "jumbo"                              # optional, MTU for the interface, default is "jumbo"
              peer1_po_description: "PC 151 for AA FEX" # optional, description of PC interface, default is ""
              peer2_po_description: "PC 151 for AA FEX" # optional, description of PC interface, default is ""
              peer1_cmds:                               # optional, freeform config, default is []
                - no shutdown
              peer2_cmds:                               # optional, freeform config, default is []
                - no shutdown
              admin_state: true                         # Flag to enable/disable FEX interface.
              enable_netflow: false                     # optional, flag to enable netflow, default is false
              mode: port_channel_aa                     # choose from [port_channel_aa], default is "port_channel_aa"

    - name: Replace AA FEX interface
      cisco.dcnm.dcnm_interface:
        check_deploy: true
        fabric: "{{ ansible_svi_fabric }}"
        state: replaced                                 # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: vpc150                                # should be of the form vpc<id>
            type: aa_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
            switch:
              - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
            deploy: true                                # choose from [true, false]
            profile:
              peer1_members:                            # optional, member interfaces, default is []
                - e1/11
              peer2_members:                            # optional, member interfaces, default is []
                - e1/11
              mtu: "default"                            # optional, MTU for the interface, default is "jumbo"
              peer1_po_description: "PC 150 for AA FEX - REP" # optional, description of PC interface, default is ""
              peer2_po_description: "PC 150 for AA FEX - REP" # optional, description of PC interface, default is ""
              admin_state: false                        # Flag to enable/disable FEX interface.
              enable_netflow: false                     # optional, flag to enable netflow, default is false
              mode: port_channel_aa                     # choose from [port_channel_aa], default is "port_channel_aa"

              peer1_cmds:                               # optional, freeform config, default is []
                - ip arp inspection trust
              peer2_cmds:                               # optional, freeform config, default is []
                - ip arp inspection trust

    - name: Delete AA FEX interfaces
      cisco.dcnm.dcnm_interface:
        check_deploy: True
        fabric: "{{ ansible_svi_fabric }}"
        state: deleted                        # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: vpc151                      # should be of the form vpc<id>
            switch:
              - "{{ ansible_switch1 }}"       # provide the switch where to deploy the config


    - name: Overide AA FEX interface with a new one
      cisco.dcnm.dcnm_interface:
        check_deploy: true
        fabric: "{{ ansible_svi_fabric }}"
        state: overridden                               # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: vpc151                                # should be of the form vpc<id>
            type: aa_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
            switch:
              - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
            deploy: true                                # choose from [true, false]
            profile:
              description: "AA FEX interface 151"       # optional, description of FEX interface, default is ""
              peer1_members:                            # optional, member interfaces, default is []
                - e1/10
              peer2_members:                            # optional, member interfaces, default is []
                - e1/10
              mtu: "jumbo"                              # optional, MTU for the interface, default is "jumbo"
              peer1_po_description: "PC 151 for AA FEX" # optional, description of PC interface, default is ""
              peer2_po_description: "PC 151 for AA FEX" # optional, description of PC interface, default is ""
              peer1_cmds:                               # optional, freeform config, default is []
                - no shutdown
              peer2_cmds:                               # optional, freeform config, default is []
                - no shutdown
              admin_state: true                         # Flag to enable/disable FEX interface.
              enable_netflow: false                     # optional, flag to enable netflow, default is false
              mode: port_channel_aa                     # choose from [port_channel_aa], default is "port_channel_aa"

    # STRAIGHT-THROUGH FEX INTERFACES

    - name: Create ST FEX interfaces including optional parameters
      cisco.dcnm.dcnm_interface:
        check_deploy: true
        fabric: "{{ ansible_svi_fabric }}"
        state: merged                                   # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: po151                                 # should be of the form po<po-id>
            type: st_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
            switch:
              - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
            deploy: true                                # choose from [true, false]
            profile:
              description: "ST FEX interface 151"       # optional, description of FEX interface, default is ""
              members:                                  # optional, member interfaces, default is []
                - e1/10
              mtu: "jumbo"                              # optional, MTU for the interface, default is "jumbo"
              po_description: "PC 151 for ST FEX"       # optional, description of PC interface, default is ""
              cmds:                                     # optional, freeform config, default is []
                - no shutdown
              admin_state: true                         # Flag to enable/disable FEX interface.
              enable_netflow: false                     # optional, flag to enable netflow, default is false
              mode: port_channel_st                     # choose from [port_channel_st], default is "port_channel_st"

    - name: Replace ST FEX interface
      cisco.dcnm.dcnm_interface:
        check_deploy: true
        fabric: "{{ ansible_svi_fabric }}"
        state: replaced                                 # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: po160                                 # should be of the form po<po-id>
            type: st_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
            switch:
              - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
              - "{{ ansible_switch2 }}"                 # provide the switch information where the config is to be deployed
            deploy: true                                # choose from [true, false]
            profile:
              members:                                  # optional, member interfaces, default is []
                - e1/11
              mtu: "default"                            # optional, MTU for the interface, default is "jumbo"
              po_description: "PC 160 for ST FEX - REP" # optional, description of PC interface, default is ""
              cmds:                                     # optional, freeform config, default is []
                - ip arp inspection trust
              admin_state: false                        # Flag to enable/disable FEX interface.
              enable_netflow: false                     # optional, flag to enable netflow, default is false
              mode: port_channel_st                     # choose from [port_channel_st], default is "port_channel_st"

    - name: Delete ST FEX interfaces
      cisco.dcnm.dcnm_interface:
        check_deploy: True
        fabric: "{{ ansible_svi_fabric }}"
        state: deleted                        # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: po159                       # should be of the form po<po-id>
            switch:
              - "{{ ansible_switch1 }}"       # provide the switch where to deploy the config
              - "{{ ansible_switch2 }}"       # provide the switch where to deploy the config

    - name: Overide ST FEX interface with a new one
      cisco.dcnm.dcnm_interface:
        check_deploy: true
        fabric: "{{ ansible_svi_fabric }}"
        state: overridden                               # only choose form [merged, replaced, deleted, overridden, query]
        config:
          - name: po151                                 # should be of the form po<po-id>
            type: st_fex                                # choose from this list [pc, vpc, sub_int, lo, eth, svi, st_fex, aa_fex]
            switch:
              - "{{ ansible_switch1 }}"                 # provide the switch information where the config is to be deployed
            deploy: true                                # choose from [true, false]
            profile:
              description: "ST FEX interface 151"       # optional, description of FEX interface, default is ""
              members:                                  # optional, member interfaces, default is []
                - e1/10
              mtu: "jumbo"                              # optional, MTU for the interface, default is "jumbo"
              po_description: "PC 151 for ST FEX"       # optional, description of PC interface, default is ""
              cmds:                                     # optional, freeform config, default is []
                - no shutdown
              admin_state: true                         # Flag to enable/disable FEX interface.
              enable_netflow: false                     # optional, flag to enable netflow, default is false
              mode: port_channel_st                     # choose from [port_channel_st], default is "port_channel_st"

    # QUERY

    - name: Query interface details
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: query            # only choose from [merged, replaced, deleted, overridden, query]
        config:
          - switch:
              - "192.172.1.1"
          - name: po350
            switch:
              - "192.172.1.1"
          - name: lo450
            switch:
              - "192.172.1.1"
          - name: eth1/1
            switch:
              - "192.172.1.1"
          - name: eth1/15.2
            switch:
              - "192.172.1.1"
          - name: vpc750
            switch:
              - "192.172.1.1"




Status
------


Authors
~~~~~~~

- Mallik Mudigonda(@mmudigon)
