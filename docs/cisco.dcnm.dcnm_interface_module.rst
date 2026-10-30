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
            <th colspan="4">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="4">
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
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>config</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>A dictionary of interface operations</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
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
                        <div>Flag indicating if the configuration must be pushed to the switch. If not included it is considered true by default</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                <td colspan="3">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile_breakout</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Though the key shown here is &#x27;profile_breakout&#x27; the actual key to be used in playbook is &#x27;profile&#x27;. The key &#x27;profile_breakout&#x27; is used here to logically segregate the interface objects applicable for this profile</div>
                        <div>Interface must be parent interface. Ex: Ethernet1/49. Short name is not supported.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>map</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>10g-4x</li>
                                    <li>25g-4x</li>
                                    <li>50g-2x</li>
                                    <li>50g-4x</li>
                                    <li>100g-2x</li>
                                    <li>100g-4x</li>
                                    <li>200g-2x</li>
                        </ul>
                </td>
                <td>
                        <div>type of breakout</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                <td colspan="2">
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
                        <div>Vlan for the interface. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;access&#x27; or &#x27;dot1q&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>acl_filter</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the ACL filter applied to the interface. This option is applicable only when mode is trunk or access. Between 1 and 64 characters. Explicit-only, no default; when omitted the current controller value is left untouched.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                        <div>In mode &#x27;pvlan&#x27; a boolean is also accepted, and the strings in any letter case; the value is sent as &#x27;true&#x27;, &#x27;false&#x27; or &#x27;no&#x27; (&#x27;no&#x27; is its own value, not false).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                        <div>In <code>mode=pvlan</code> a text is also accepted, one command per line; a text with a comma is refused.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disable_lldp_receive</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Disable LLDP receive on the interface. See disable_lldp_transmit; setting one without the other emits a single CLI line. Explicit-only, no default; when omitted the current controller value is left untouched.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disable_lldp_transmit</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Disable LLDP transmit on the interface. Replaces the earlier disable_lldp, which acted on both directions at once; the two directions are now independent. Explicit-only, no default; when omitted the current controller value is left untouched.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disable_qos_stats</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Disable statistics for the attached QoS policy. This option is applicable only when mode is trunk or access.</div>
                        <div>Does NOT produce a configuration line of its own. It appends &#x27; no-stats&#x27; to the &#x27;service-policy type qos input&#x27; line that &#x27;enable_qos&#x27; and &#x27;qos_policy&#x27; produce. With no QoS policy in effect the value is stored on the controller and changes nothing on the device.</div>
                        <div>Requires &#x27;enable_qos&#x27; to be true AND a QoS policy name to resolve, either from &#x27;qos_policy&#x27; or from the fabric AI/ML QoS setting.</div>
                        <div>Explicit-only, no default. When omitted the current controller value is left untouched.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disable_queuing_stats</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Disable statistics for the attached output queuing policy. This option is applicable only when mode is trunk or access.</div>
                        <div>Does NOT produce a configuration line of its own. It appends &#x27; no-stats&#x27; to the &#x27;service-policy type queuing output&#x27; line that &#x27;queuing_policy&#x27; produces. With &#x27;queuing_policy&#x27; empty the value is stored on the controller and changes nothing on the device.</div>
                        <div>Explicit-only, no default. When omitted the current controller value is left untouched.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>duplex</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>auto</b>&nbsp;&larr;</div></li>
                                    <li>full</li>
                                    <li>half</li>
                        </ul>
                </td>
                <td>
                        <div>Duplex of the interface. Speed must be set to use duplex.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_cdp</b>
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
                        <div>State of CDP protocol on the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_monitor</b>
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
                        <div>State of Switchport Monitor for SPAN/ERSPAN</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_pfc</b>
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
                        <div>State of Priority Flow Control (PFC) on the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_qos</b>
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
                        <div>Enable QoS on the interface. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;, &#x27;access&#x27;, or &#x27;routed&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>flowcontrol_receive</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>on</li>
                                    <li>off</li>
                        </ul>
                </td>
                <td>
                        <div>State of IEEE 802.3x pause-frame reception. This option is applicable only when mode is trunk or access.</div>
                        <div>Explicit-only, no default. When omitted the current controller value is left untouched; set &#x27;off&#x27; to remove the CLI.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>flowcontrol_send</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>on</li>
                                    <li>off</li>
                        </ul>
                </td>
                <td>
                        <div>State of IEEE 802.3x pause-frame transmission. This option is applicable only when mode is trunk or access.</div>
                        <div>Explicit-only, no default. When omitted the current controller value is left untouched; set &#x27;off&#x27; to remove the CLI.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>guard_mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>root</li>
                                    <li>none</li>
                                    <li>loop</li>
                                    <li>no</li>
                        </ul>
                </td>
                <td>
                        <div>Spanning-tree guard mode. This option is applicable only when mode is trunk. Explicit-only, no default; when omitted the current controller value is left untouched.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                                    <li>dot1q</li>
                                    <li>pvlan</li>
                        </ul>
                </td>
                <td>
                        <div>Interface mode</div>
                        <div>When ethernet interface is a PortChannel or vPC member, mode is ignored. The only properties that can be managed for PortChannel or vPC member interfaces are &#x27;admin_state&#x27;, &#x27;description&#x27; and &#x27;cmds&#x27;. All other properties are ignored.</div>
                        <div>Mode &#x27;pvlan&#x27; selects the NDFC 12 policy &#x27;int_pvlan_host&#x27; on a standalone physical Ethernet interface; see &#x27;pvlan_mode&#x27;. It is refused on a PortChannel or vPC member and on an interface owned by a network attachment.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>native_vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Vlan used as native vlan. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>orphan_port</b>
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
                        <div>interface orphan port behavior when switch is in vPC</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pvlan_association</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Primary/secondary VLAN associations for &#x27;pvlan_mode&#x27; &#x27;host&#x27; (at most one) and &#x27;trunk secondary&#x27; (one secondary per primary). A new &#x27;trunk secondary&#x27; association requires the fabric network of the secondary VLAN to be isolated.</div>
                        <div>A secondary VLAN belongs to one primary VLAN - the resulting list (after a &#x27;merged&#x27; union with the current one) that puts one secondary under two primaries is refused before any write.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>primary_vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Primary VLAN ID (1-4094).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>secondary_vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Secondary VLAN ID (1-4094).</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pvlan_mapping</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Promiscuous mappings for &#x27;pvlan_mode&#x27; &#x27;promiscuous&#x27; (one primary) and &#x27;trunk promiscuous&#x27;. Ranges are expanded and sent as one row per pair.</div>
                        <div>A secondary VLAN belongs to one primary VLAN - the resulting list (after a &#x27;merged&#x27; union with the current one) that puts one secondary under two primaries is refused before any write.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>primary_vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Primary VLAN ID (1-4094).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>secondary_vlans</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Secondary VLAN IDs as a string, for example &quot;2211&quot; or &quot;2211-2212,2214&quot;. A single-value range such as &quot;2212-2212&quot; is accepted as the VLAN &quot;2212&quot; and sent and compared as &quot;2212&quot;; a descending, repeated, overlapping or out-of-range value is refused.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pvlan_mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>host</li>
                                    <li>promiscuous</li>
                                    <li>trunk promiscuous</li>
                                    <li>trunk secondary</li>
                        </ul>
                </td>
                <td>
                        <div>Private VLAN port mode. Required, and only valid, when &#x27;mode&#x27; is &#x27;pvlan&#x27;.</div>
                        <div>With &#x27;mode&#x27; &#x27;pvlan&#x27; no field has a module default. State &#x27;merged&#x27; keeps every omitted field at its current controller value; &#x27;replaced&#x27; and a retained &#x27;overridden&#x27; interface clear omitted lists and &#x27;native_vlan&#x27;/&#x27;allowed_vlans&#x27; and return omitted companion fields to the int_pvlan_host template defaults.</div>
                        <div>Changing the submode of an existing PVLAN port requires &#x27;replaced&#x27; or &#x27;overridden&#x27;; &#x27;merged&#x27; refuses it.</div>
                        <div>In mode &#x27;pvlan&#x27; the supported companion fields are &#x27;description&#x27;, &#x27;admin_state&#x27;, &#x27;bpdu_guard&#x27;, &#x27;port_type_fast&#x27;, &#x27;mtu&#x27;, &#x27;speed&#x27;, &#x27;enable_cdp&#x27;, &#x27;orphan_port&#x27;, &#x27;duplex&#x27;, &#x27;enable_pfc&#x27;, &#x27;enable_qos&#x27;, &#x27;qos_policy&#x27;, &#x27;queuing_policy&#x27; and &#x27;cmds&#x27;, plus the registered &#x27;disable_lldp_transmit&#x27; and &#x27;disable_lldp_receive&#x27; (NOT LIVE TESTED in this mode; they need an approved <code>patch_version</code>). Any other field is refused. An explicit LLDP value always wins; an omitted one is kept by &#x27;merged&#x27; and, on &#x27;replaced&#x27;, withdrawn to &#x27;false&#x27; (inferred) only with an approved <code>patch_version</code>, else kept. &#x27;cmds&#x27; must not carry private-vlan or switchport lines. &#x27;native_vlan&#x27; (&#x27;&#x27; or one VLAN) and &#x27;allowed_vlans&#x27; (&#x27;&#x27;, &#x27;none&#x27; or VLAN ranges; &#x27;all&#x27; is refused) apply to the two trunk submodes only.</div>
                        <div>Before every deployment attempt (including the check_deploy resend and the deployment-status retries) the module recomputes the switch pending configuration through the legacy config-preview API. Using that answer&#x27;s device running configuration and the controller&#x27;s expected configuration, it deploys only the remaining work when every pending command for the interface leads from the device state to the intended state; it skips the attempt for an interface whose device state is already verified as the intended state. When a check fails after the intent was written, the intent change is reported and is not rolled back.</div>
                        <div>Every deployment response is judged on its original body; a failed or unrecognised response fails the task even if a later read reports In-Sync, and no further deployment is sent.</div>
                        <div>The interface must be a standalone physical Ethernet with exactly one direct policy, both in the interface summary and in the switch policy list; a network attachment, port-channel membership or incomplete ownership data is refused.</div>
                        <div>The CLI coverage of the current and destination configurations is verified before any write, also in check mode. The bulk interface update capability is verified before any write in normal mode only; its sole probe is a POST request, so in check mode a native PVLAN invocation that would change intent is refused with &quot;could not be verified in check mode&quot;, and nothing is sent.</div>
                        <div>Removal authority comes from the requested transition, not from the device. A pending command may withdraw only a line the int_pvlan_host (or, for a reset or conversion, int_trunk_host) template renders, or a &#x27;cmds&#x27; line of the current or requested intent. A device command outside that set is never withdrawn by the deployment, and one inside a field these policies own but that cannot be interpreted blocks the deployment.</div>
                        <div>Removing a secondary VLAN from a &#x27;promiscuous&#x27; mapping that keeps other secondaries is refused before any write, because the controller generates an invalid removal command for that transition. Clear the mapping or use &#x27;trunk promiscuous&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>qos_policy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>QoS policy name to apply to the interface. This option is only valid when &#x27;enable_qos&#x27; is true. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;, &#x27;access&#x27;, or &#x27;routed&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>queuing_policy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Queuing policy name to apply to the interface. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;, &#x27;access&#x27;, or &#x27;routed&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>spanning_tree_port_type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>network</li>
                                    <li>normal</li>
                        </ul>
                </td>
                <td>
                        <div>Spanning-tree port type. This option is applicable only when mode is trunk or access.</div>
                        <div>Requires &#x27;port_type_fast&#x27; to be false. The parent template rejects &#x27;network&#x27; or &#x27;normal&#x27; while port type fast is enabled, and port type fast defaults to true, so both must be sent together.</div>
                        <div>A value of &#x27;no&#x27; does not mean &quot;no configuration&quot;. It defers to the port-type-fast behaviour, and the resulting CLI differs per mode - &#x27;spanning-tree port type edge trunk&#x27; on a trunk interface, and &#x27;spanning-tree port type edge&#x27; on an access one. Both were observed on a live switch.</div>
                        <div>Explicit-only, no default. When omitted the current controller value is left untouched.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>speed</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"Auto"</div>
                </td>
                <td>
                        <div>Speed of the interface.</div>
                        <div>In mode &#x27;pvlan&#x27; it must be one of Auto, 10Mb, 100Mb, 1Gb, 2.5Gb, 5Gb, 10Gb, 25Gb, 40Gb, 50Gb, 100Gb, 200Gb, 400Gb or 800Gb, in any letter case, and it is sent in that spelling.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                        <div>IPv4 address of the interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                        <div>IPv6 address of the interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                                    <li>fabric</li>
                                    <li>mpls</li>
                        </ul>
                </td>
                <td>
                        <div>There are several modes for loopback interfaces.</div>
                        <div>Mode &#x27;lo&#x27; is used to create, modify and delete non fabric loopback interfaces using policy &#x27;int_loopback&#x27;.</div>
                        <div>Mode &#x27;fabric&#x27; is used to modify loopbacks created when the fabric is first created using policy &#x27;int_fabric_loopback_11_1&#x27;</div>
                        <div>Mode &#x27;mpls&#x27; is used to modify loopbacks created when the fabric is first created using policy &#x27;int_mpls_loopback&#x27;</div>
                        <div>Mode &#x27;fabric&#x27; and &#x27;mpls&#x27; interfaces can be modified but not created or deleted.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>secondary_ipv4_addr</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Secondary IP address of the nve interface loopback</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                <td colspan="2">
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
                        <div>Vlan for the interface. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;access&#x27; or &#x27;dot1q&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>acl_filter</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the ACL filter applied to the port-channel. This option is applicable only when mode is trunk, access or dot1q. Between 1 and 64 characters. Explicit-only, no default; when omitted the current controller value is left untouched.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>copy_description</b>
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
                        <div>Copy the port-channel description to its member interfaces.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disable_lacp_suspend_individual</b>
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
                        <div>If disabled, lacp will put the port to individual state and not suspend the port in case the port does not get LACP BPDU from the peer ports in the port-channel</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disable_qos_stats</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Disable statistics for the attached QoS policy. This option is applicable only when mode is trunk, access, dot1q or peer_link.</div>
                        <div>Does NOT produce a configuration line of its own. It appends &#x27; no-stats&#x27; to the &#x27;service-policy type qos input&#x27; line that &#x27;enable_qos&#x27; and &#x27;qos_policy&#x27; produce. With no QoS policy in effect the value is stored on the controller and changes nothing on the device.</div>
                        <div>Explicit-only, no default. When omitted the current controller value is left untouched.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disable_queuing_stats</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Disable statistics for the attached output queuing policy. This option is applicable only when mode is trunk, access, dot1q or pvlan (in mode pvlan, true requires a resulting &#x27;queuing_policy&#x27;).</div>
                        <div>Does NOT produce a configuration line of its own. It appends &#x27; no-stats&#x27; to the &#x27;service-policy type queuing output&#x27; line that &#x27;queuing_policy&#x27; produces. With &#x27;queuing_policy&#x27; empty the value is stored on the controller and changes nothing on the device.</div>
                        <div>Explicit-only, no default. When omitted the current controller value is left untouched.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>duplex</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>auto</b>&nbsp;&larr;</div></li>
                                    <li>full</li>
                                    <li>half</li>
                        </ul>
                </td>
                <td>
                        <div>Duplex of the interface. Speed must be set to use duplex.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_cdp</b>
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
                        <div>State of CDP protocol on the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_monitor</b>
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
                        <div>State of Switchport Monitor for SPAN/ERSPAN</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_pfc</b>
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
                        <div>State of Priority Flow Control (PFC) on the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_qos</b>
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
                        <div>Enable QoS on the interface. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;, &#x27;access&#x27;, or &#x27;l3&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>guard_mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>root</li>
                                    <li>none</li>
                                    <li>loop</li>
                                    <li>no</li>
                        </ul>
                </td>
                <td>
                        <div>Spanning-tree guard mode. This option is applicable only when mode is trunk. Explicit-only, no default; when omitted the current controller value is left untouched.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>lacp_port_priority</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">32768</div>
                </td>
                <td>
                        <div>&lt;1-65535&gt; Set LACP port priority on member interfaces, default is 32768</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>lacp_rate</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>normal</b>&nbsp;&larr;</div></li>
                                    <li>fast</li>
                        </ul>
                </td>
                <td>
                        <div>Set the rate at which LACP control packets are sent to an LACP-supported interface. Normal rate (30 seconds), fast rate (1 second), rate is set on member interfaces, default is normal</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                                    <li>dot1q</li>
                                    <li>monitor</li>
                                    <li>pvlan</li>
                                    <li>peer_link</li>
                        </ul>
                </td>
                <td>
                        <div>Interface mode</div>
                        <div>Mode &#x27;pvlan&#x27; selects the NDFC 12 policy &#x27;int_port_channel_pvlan_host&#x27; for a regular port-channel with one or more explicit physical members. Supported - creation in the four PVLAN modes, update of the PVLAN lists (&#x27;merged&#x27; adds to the current list, &#x27;replaced&#x27; states the complete model) and of &#x27;pc_mode&#x27;, &#x27;description&#x27;, &#x27;admin_state&#x27;, &#x27;native_vlan&#x27; and &#x27;allowed_vlans&#x27; without changing &#x27;pvlan_mode&#x27;, a change of the member list, the identical repetition and &#x27;overridden&#x27; (a kept port-channel follows &#x27;replaced&#x27;; a PVLAN port-channel of the sweep&#x27;s scope that the request no longer wants is deleted through the same path and contract as &#x27;state=deleted&#x27;; switch scope and override_intf_types are those of the generic sweep; MEASURED for host mode on NDFC 12.6.0.267, NOT LIVE TESTED for the other modes). Refused before any change is sent - ranges, vPC, a &#x27;pvlan_mode&#x27; change, and removing secondaries from a &#x27;promiscuous&#x27; mapping that keeps others (protection kept from the measured Ethernet defect). Fields for this mode are &#x27;pvlan_mode&#x27;, &#x27;pvlan_association&#x27; (host, trunk secondary), &#x27;pvlan_mapping&#x27; (promiscuous, trunk promiscuous), &#x27;native_vlan&#x27; and &#x27;allowed_vlans&#x27; (trunk modes), &#x27;members&#x27;, &#x27;pc_mode&#x27;, &#x27;description&#x27; and &#x27;admin_state&#x27;. The members are managed by the parent and follow the regular port-channel rule - &#x27;merged&#x27; adds the listed members to the current ones (&#x27;members&#x27; may be omitted, and a subset never removes a member); &#x27;replaced&#x27; states the exact member list, which must be listed explicitly (an omitted or empty list is refused, an empty member list is not supported). An added member must qualify as for a creation. A member qualifies when it is a free port on the base its mode admits (<code>int_trunk_host</code> for host, promiscuous and trunk promiscuous; a prepared access or routed port for trunk secondary) with no freeform commands and an explicit administrative state (ADMIN_STATE true or false). An administratively up member joins and stays up and a down member stays down, each member keeping its own state whatever the port-channel&#x27;s &#x27;admin_state&#x27; (MEASURED for host, parent down and up, on NDFC 12.6.0.267 / NX-OS 10.5(5); NOT LIVE TESTED for promiscuous, trunk promiscuous and trunk secondary, which share the same template inheritance). A missing or unknown state is refused, and the module never changes a member&#x27;s state. Administratively up does not mean link up or traffic. A removed member (up or down) is released, before the deployment and as in &#x27;state=deleted&#x27;, to the fabric&#x27;s host interface default HOST_INTF_ADMIN_STATE (true - up, the NDFC default - or false - down), the value the generic reset of a host interface uses; the module corrects the release with one modify only when the controller released it otherwise. An unreadable fabric default or an unknown member state is refused; removing members needs no check mode. With <code>deploy</code> false a member removal or a deletion is SAVED - the modify or mark-delete, the released member corrected to the fabric default and the pending validated by the pre-deploy gate, with no deployment request (result <code>pvlan_saved</code>); a later request with <code>deploy</code> true, in any process, recognises the saved operation from the controller&#x27;s state only (the marked-for-deletion listing, the device&#x27;s running configuration and the released member), deploys and verifies it without a second mark-delete, and the same request with <code>deploy</code> false writes nothing and reports it still pending (MEASURED for host mode, deletion and member removal, on NDFC 12.6.0.267; NOT LIVE TESTED for the other modes). For &#x27;trunk secondary&#x27; the member must ALREADY be prepared as a neutral access (int_access_host) or routed (int_routed_host) port, administratively up or down; a member in switchport mode trunk is refused (known incident - NX-OS rejects the join) and the module never converts a member. &#x27;state=deleted&#x27; removes the port-channel and releases its member to the fabric&#x27;s host interface default before the deployment, on the policy the controller releases it to (read afresh, never converted) - <code>int_trunk_host</code>, or <code>int_routed_host</code> only in the measured neutral form (no address, VRF, routing, QoS or freeform commands, MTU 9216, speed Auto); any other release stops before the deployment.</div>
                        <div>Companion fields of mode &#x27;pvlan&#x27; on a port-channel (NOT LIVE TESTED). Native, no <code>patch_version</code> needed - &#x27;bpdu_guard&#x27;, &#x27;port_type_fast&#x27;, &#x27;mtu&#x27;, &#x27;copy_description&#x27;, &#x27;enable_cdp&#x27;, &#x27;orphan_port&#x27;, &#x27;duplex&#x27;, &#x27;queuing_policy&#x27;, &#x27;disable_lacp_suspend_individual&#x27;, &#x27;lacp_port_priority&#x27; (1-65535) and &#x27;lacp_rate&#x27; (normal, fast); &#x27;bpdu_guard&#x27; takes a boolean or &#x27;true&#x27;, &#x27;false&#x27;, &#x27;no&#x27; in any letter case and &#x27;speed&#x27; any letter case of its values, both sent in the template&#x27;s spelling. Registered, so they need an approved <code>patch_version</code> and NDFC 12.6.0.267 or later - &#x27;disable_lldp_transmit&#x27;, &#x27;disable_lldp_receive&#x27;, &#x27;spanning_tree_port_type&#x27; and &#x27;disable_queuing_stats&#x27;. &#x27;merged&#x27; keeps an omitted field; &#x27;replaced&#x27; returns an omitted native field to the template default and withdraws an omitted registered field to its reset (inferred, not measured on this policy), or keeps it when the patch context is not approved. CDP, LLDP and the LACP priority/rate reach the member through the parent template; &#x27;copy_description&#x27; copies &#x27;description&#x27; to the member. Refused before any write - &#x27;spanning_tree_port_type&#x27; network/normal while port type fast is true, &#x27;disable_queuing_stats&#x27; true without a resulting &#x27;queuing_policy&#x27;, and a &#x27;lacp_rate&#x27; change while the member is administratively up (template precondition; the module never changes a member&#x27;s admin state).</div>
                        <div>Speed and freeform of mode &#x27;pvlan&#x27; on a port-channel (NOT LIVE TESTED). &#x27;speed&#x27; takes the template values; it is rendered on the port-channel and inherited by every member, and the controller checks that the switch supports it. The controller&#x27;s pending carries the speed on the port-channel only and NX-OS applies it to the member (MEASURED for 1Gb, one member, host mode, administratively down - the addition and the return to Auto with <code>no speed 1000</code>); the module accepts that form only for <code>speed 1000</code>, the member administratively down, its own persisted channel-group, the same mode on member and port-channel, no <code>no negotiate auto</code> and every other member line unchanged. Any other speed or pending form is refused before the deployment (the intent change already written is reported, not rolled back). The same holds for <code>duplex</code> full (MEASURED for one member, host mode, administratively down, with the speed fixed at 1000 and unchanged in that transition) - the controller&#x27;s pending carries <code>duplex full</code> on the port-channel only and its withdrawal is <code>no duplex full</code>; a member that follows is accepted, anything else is refused before the deployment. Not covered - <code>duplex</code> half, a duplex change together with a speed or MTU change, any other speed. On an existing port-channel or vPC a request that changes the speed and the duplex at once (against the current intent, judged on each vPC peer) is refused before any write - set the fixed speed first, in its own request, and then the duplex; to withdraw both, set duplex auto first and then speed Auto (a creation may set both). More than one member is not refused by count - each member is judged on its own state and is covered by offline tests; the live measurement covers one member per port-channel or leg. A duplex other than auto needs a resulting fixed speed (NX-OS rejects it with speed Auto) - the request is refused before any write, judged on the resulting state (&#x27;merged&#x27; keeps an omitted speed); the return to auto is never blocked. The post-deployment readback also compares the stored duplex (NOT LIVE TESTED by the module). Not measured and not checked - more than one member, a mode other than host, another switch role or platform; they are accepted when the controller&#x27;s pending has the measured form, followed only by the usual post-deployment compliance and intent readback. Freeform &#x27;cmds&#x27; holds one top-level command per entry; a text (and a list entry holding line breaks) is also accepted and every line is checked as one entry, while a text with a comma is refused (the same applies to <code>peer1_cmds</code> and <code>peer2_cmds</code> of a vPC). &#x27;merged&#x27; keeps an omitted &#x27;speed&#x27; or &#x27;cmds&#x27; and adds the listed commands to the current ones; &#x27;replaced&#x27; returns an omitted &#x27;speed&#x27; to Auto and states the exact command list (an omitted or empty list clears it); a command repeated in one request is kept once, in the order of its first appearance. A speed returning to Auto is deployed only when the pending withdraws <code>speed &lt;n&gt;</code> and, when the controller had added it, <code>no negotiate auto</code> (expected as <code>negotiate auto</code>; INFERRED, not measured - the templates never render it); a different pending is refused before any deployment. Refused before any write - a command the controller copies to every member (starting with cts, duplex, flowcontrol, load-interval, medium, mtu, no negotiate, port-type, priority-flow-control, speed, storm-control or switchport), a command of a field a structured option owns (private-vlan, channel-group, vpc, interface, mtu, speed, negotiate, duplex, spanning-tree, description, cdp, lldp, lacp, shutdown, priority-flow-control, service-policy, ip port access-group) and an indented sub-command.</div>
                        <div>Mode &#x27;peer_link&#x27; (NOT LIVE TESTED) updates an existing vPC peer-link port-channel (policy int_vpc_peer_link_po). The vPC pairing creates the peer-link and owns every other field, so the module never creates or deletes it and refuses state &#x27;deleted&#x27; with this mode. &#x27;switch&#x27; must name both switches of the vPC pair, and both peers receive the same values. The accepted fields are &#x27;enable_qos&#x27;, &#x27;qos_policy&#x27;, &#x27;disable_qos_stats&#x27; and &#x27;spanning_tree_port_type&#x27;, each explicit-only with no default; any other field is refused. The mode requires NDFC 12 and an approved <code>patch_version</code>. Every other stored nvPair of the peer-link, including its member list, is sent back unchanged.</div>
                        <div>In mode &#x27;peer_link&#x27;, &#x27;merged&#x27; sets the listed fields and keeps the others. &#x27;replaced&#x27;, and an &#x27;overridden&#x27; item that names the peer-link, return an omitted &#x27;spanning_tree_port_type&#x27; to &#x27;no&#x27; and an omitted &#x27;disable_qos_stats&#x27; to false. &#x27;overridden&#x27; does not remove a peer-link that the request does not name.</div>
                        <div>In mode &#x27;peer_link&#x27;, QoS withdrawal is not supported. The captured template body keeps the QoS attachment when QoS is disabled, and whether a controller removes it is not verified. While QoS is enabled on the controller, &#x27;enable_qos&#x27; false, an empty &#x27;qos_policy&#x27; and, under &#x27;replaced&#x27; or &#x27;overridden&#x27;, omitting either field are refused before any change is sent.</div>
                        <div>In mode &#x27;peer_link&#x27;, &#x27;replaced&#x27; and &#x27;overridden&#x27; also refuse to omit &#x27;qos_policy&#x27; while a policy name is stored with QoS disabled, for example after QoS was disabled outside the module. Restate the stored name, or use &#x27;merged&#x27;, which keeps it. Neither withdraws QoS. An explicit empty &#x27;qos_policy&#x27; sends an empty name; its effect on a QoS attachment that the controller kept is not verified.</div>
                        <div>In mode &#x27;peer_link&#x27;, &#x27;qos_policy&#x27; and &#x27;disable_qos_stats&#x27; are accepted while QoS is disabled. The module sends them, but a value sent this way does not show an active policy on the device, and a name sent this way must then be restated under &#x27;replaced&#x27; and &#x27;overridden&#x27;. &#x27;enable_qos&#x27; true requires a non-empty &#x27;qos_policy&#x27; of at most 40 characters without whitespace.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>native_vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Vlan used as native vlan. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>orphan_port</b>
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
                        <div>interface orphan port behavior when switch is in vPC</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pvlan_association</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Primary/secondary VLAN associations for <code>pvlan_mode</code> <code>host</code> (exactly one) and <code>trunk secondary</code> (one secondary per primary; the secondary must be an isolated VLAN), as a list of dictionaries with the keys <code>primary_vlan</code> and <code>secondary_vlan</code>.</div>
                        <div>A secondary VLAN belongs to one primary VLAN - the resulting list (after a <code>merged</code> union with the current one) that puts one secondary under two primaries is refused before any write.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pvlan_mapping</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Promiscuous mappings for <code>pvlan_mode</code> <code>promiscuous</code> (a single primary VLAN) and <code>trunk promiscuous</code>, as a list of dictionaries with the keys <code>primary_vlan</code> and <code>secondary_vlans</code> (a VLAN list string; a single-value range &quot;N-N&quot; is the VLAN N, also in <code>allowed_vlans</code>).</div>
                        <div>A secondary VLAN belongs to one primary VLAN - the resulting list (after a <code>merged</code> union with the current one) that puts one secondary under two primaries is refused before any write.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pvlan_mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>host</li>
                                    <li>promiscuous</li>
                                    <li>trunk promiscuous</li>
                                    <li>trunk secondary</li>
                        </ul>
                </td>
                <td>
                        <div>Private VLAN mode. Required, and only valid, when &#x27;mode&#x27; is &#x27;pvlan&#x27;. It cannot be changed on an existing port-channel.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>qos_policy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>QoS policy name to apply to the interface. This option is only valid when &#x27;enable_qos&#x27; is true. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;, &#x27;access&#x27;, or &#x27;l3&#x27;</div>
                        <div>In mode &#x27;peer_link&#x27; it is explicit-only, with no default, and needs an approved <code>patch_version</code>. See &#x27;mode&#x27; for the QoS restrictions of that mode.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>queuing_policy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Queuing policy name to apply to the interface. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;, &#x27;access&#x27;, or &#x27;l3&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>spanning_tree_port_type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>no</li>
                                    <li>network</li>
                                    <li>normal</li>
                        </ul>
                </td>
                <td>
                        <div>Spanning-tree port type. This option is applicable only when mode is trunk, access, dot1q, pvlan or peer_link.</div>
                        <div>In mode &#x27;peer_link&#x27; the captured template body copies the value to each member (NOT LIVE TESTED), and &#x27;port_type_fast&#x27; does not apply.</div>
                        <div>Requires &#x27;port_type_fast&#x27; to be false. The parent template rejects &#x27;network&#x27; or &#x27;normal&#x27; while port type fast is enabled, and port type fast defaults to true, so both must be sent together.</div>
                        <div>A value of &#x27;no&#x27; does not mean &quot;no configuration&quot;. It defers to the port-type-fast behaviour.</div>
                        <div>Explicit-only, no default. When omitted the current controller value is left untouched.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="3">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="3">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_relay_src_intf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Source interface for DHCP relay, normally an Ethernet, port-channel or loopback interface. The <code>int_vlan</code> body of SMU <code>4.3.1.0175006011</code> accepts only these.</div>
                        <div>The <code>int_vlan</code> body served with SMU <code>4.3.1.0175006017</code> also accepts a VLAN interface, for example <code>vlan2301</code>. The module does not validate the interface name; the installed template decides whether the controller accepts it. A supported <code>patch_version</code> selects the nvPair name only, so it does not show that an untested controller body accepts a VLAN source (NOT LIVE TESTED).</div>
                        <div>Independent of the DHCP server addresses; it can be set on its own.</div>
                        <div>The nvPair name depends on the installed <code>int_vlan</code> body and is selected by <code>patch_version</code> (legacy <code>DHCP_RELAY_SRC_INTF</code>, SMU body <code>dhcpRelaySourceInterface</code>).</div>
                        <div>An explicit empty string clears a configured source interface, also under <code>merged</code>; an omitted value is preserved under <code>merged</code> and reset under <code>replaced</code> and <code>overridden</code> (NOT LIVE TESTED).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_server_addr4</b>
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
                        <div>An explicit empty string clears a configured address, also under <code>merged</code>, together with its <code>vrf_dhcp4</code>; an omitted value is preserved under <code>merged</code> and reset under <code>replaced</code> and <code>overridden</code> (NOT LIVE TESTED).</div>
                        <div>The nvPair name depends on the installed <code>int_vlan</code> body and is selected by <code>patch_version</code> (legacy <code>dhcpServerAddr4</code>, SMU body <code>dhcpServerAddress4</code>).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>hsrp_secondary_vips</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Secondary IPv4 virtual addresses of the existing HSRP group. At most 16 entries.</div>
                        <div>Same merged, replaced and overridden behavior as <em>secondary_gws</em>, identified by address. The HSRP group and its primary virtual address are not changed.</div>
                        <div>The controller requires HSRP enabled with a primary IPv4 virtual address, and each entry in the subnet of the SVI primary address.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>hsrp_secondary_vip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IPv4 address, for example 192.0.2.123.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>secondary_gws</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Secondary IPv4 addresses of the SVI, each with its prefix length. At most 16 entries.</div>
                        <div>Entries are identified by address. Order is not significant.</div>
                        <div>With <em>state=merged</em>, an omitted key or an empty list leaves the current entries unchanged, and a non-empty list is added to them; an address that already exists takes the prefix length given here.</div>
                        <div>With <em>state=replaced</em> and for an interface kept by <em>state=overridden</em>, the list is the complete set; omitting the key or giving an empty list removes every entry.</div>
                        <div>Requires a primary IPv4 address on the SVI.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>gateway_ip_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IPv4 address and prefix length, for example 192.0.2.254/24. Host bits are kept.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_dhcp4</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>VRF to reach DHCP server. This parameter is required if &quot;dhcp_server_addr4&quot; is included.</div>
                        <div>It is cleared together with <code>dhcp_server_addr4</code>.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                <td colspan="2">
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
                <td colspan="2">
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
                        <div>In mode &#x27;pvlan&#x27; a boolean is also accepted, and the strings in any letter case; the value is sent as &#x27;true&#x27;, &#x27;false&#x27; or &#x27;no&#x27; (&#x27;no&#x27; is its own value, not false).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>copy_description</b>
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
                        <div>Copy each peer port-channel description to that peer&#x27;s member interfaces.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disable_lacp_suspend_individual</b>
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
                        <div>If disabled, lacp will put the port to individual state and not suspend the port in case the port does not get LACP BPDU from the peer ports in the port-channel</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_lacp_vpc_convergence</b>
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
                        <div>Enable lacp convergence for vPC port-channels</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_qos</b>
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
                        <div>Enable QoS on the interface. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27; or &#x27;access&#x27;</div>
                        <div>In mode &#x27;uplink_access&#x27; it is explicit-only, with no default, and needs an approved <code>patch_version</code>. See &#x27;mode&#x27; for the QoS rules of that mode.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>lacp_port_priority</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">32768</div>
                </td>
                <td>
                        <div>&lt;1-65535&gt; Set LACP port priority on member interfaces, default is 32768</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>lacp_rate</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>normal</b>&nbsp;&larr;</div></li>
                                    <li>fast</li>
                        </ul>
                </td>
                <td>
                        <div>Set the rate at which LACP control packets are sent to an LACP-supported interface. Normal rate (30 seconds), fast rate (1 second), rate is set on member interfaces, default is normal</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                                    <li>dot1q</li>
                                    <li>pvlan</li>
                                    <li>uplink_access</li>
                        </ul>
                </td>
                <td>
                        <div>Interface mode</div>
                        <div><code>dot1q</code> selects the dot1q-tunnel vPC template (<code>int_vpc_dot1q_tunnel</code>) and requires NDFC 12. It takes the same options as <code>access</code>, plus the LACP options.</div>
                        <div><code>pvlan</code> selects the NDFC 12 policy <code>int_vpc_pvlan_host</code> for a vPC with one or more explicit physical members per peer, in any of its four <code>pvlan_mode</code> values. Supported - creation, identical repetition, an update that reaches BOTH peers (the list of the mode, &#x27;pc_mode&#x27;, the description of both peers, or the PVLAN native/allowed VLANs of both peers), a change of the description of ONE peer alone (<code>peer1_description</code> or <code>peer2_description</code>, only while <code>copy_description</code> is false; the other peer keeps its value and is still checked to stay unchanged; an explicit empty string clears the description of that peer, while an omitted description keeps it; NOT LIVE TESTED), a change of the members of one peer or both, and <code>state=deleted</code> of the vPC, all with <code>deploy</code> true when a deployment is wanted. Refused before any change is sent - a <code>pvlan_mode</code> change, a field the mode does not take, a PCID change of an existing vPC (<code>peer1_pcid</code> and <code>peer2_pcid</code> are optional integers 1-4096, one per peer, independent of the vPC id and of each other - as for the regular vPC; omitted means the vPC id on a creation and the stored value on an update), an empty list, removing secondaries from a <code>promiscuous</code> mapping that keeps others (protection kept from the measured Ethernet defect), any other update that reaches only one peer (including a description change of one peer together with a member change of that peer, a one-peer PVLAN native/allowed change and a one-peer freeform change), a change of <code>admin_state</code> of an existing vPC, check mode for a creation or a deletion and NDFC 11. <code>overridden</code> keeps a requested vPC as <code>replaced</code> and deletes a PVLAN vPC of the sweep&#x27;s scope that the request no longer wants through the deletion path (one decision per pair and name; MEASURED for host mode on NDFC 12.6.0.267 - retention, unchanged repetition, a vPC no longer wanted and the last PVLAN vPC; NOT LIVE TESTED for the other modes). For <code>trunk secondary</code> each member must ALREADY be prepared as a neutral access (<code>int_access_host</code>) or routed (<code>int_routed_host</code>) port on BOTH peers; a member in switchport mode trunk is refused (known incident - NX-OS rejects the join) and the module never converts a member. <code>peer1_*</code> belong to the first switch of <code>switch</code> and <code>peer2_*</code> to the second; both switches must be the two switches of the vPC pair. The members are managed by the parent; per peer, <code>peer1_members</code> and <code>peer2_members</code> follow the regular port-channel rule - <code>merged</code> adds the listed members (an omitted list keeps the current members), <code>replaced</code> states the exact member list of each peer, which must be listed explicitly (an omitted or empty list is refused). An added member must qualify as for a creation (as for a regular port-channel; each member keeps its own explicit administrative state, an up member on one peer and a down member on the other are both admitted and each peer is judged on its own serial - MEASURED for host with both members up, NOT LIVE TESTED for the other modes); a removed member (up or down) is released to the fabric&#x27;s host interface default on its own switch before the deployment (needs no check mode and a readable fabric default; with <code>deploy</code> false the removal or the deletion is saved and completed later as for a regular port-channel - a saved deletion is recognised only when BOTH peers list the vPC&#x27;s children marked for deletion, a saved member removal only when the device still joins the port to the peer&#x27;s port-channel, the vPC intent no longer lists it and it is already released). Both peers are validated before anything is deployed and the vPC is reported successful only when EVERY peer is. Before the deployment, each released member is proven on its own peer against the explicit contract (a direct <code>int_trunk_host</code>, or <code>int_routed_host</code> in the measured neutral form, as the controller releases it; at the fabric&#x27;s host interface default; no freeform commands, no residual PVLAN or channel-group field and no policy left by the vPC) without rewriting any member beyond setting a released member to that default on its own policy - also when a later run completes a saved deletion. After the deployment the module reads only the interface summary of each peer - the vPC and its port-channels must no longer be listed and every member must be listed In-Sync - and does not read the intent or the policies again.</div>
                        <div>Companion fields of <code>pvlan</code> on a vPC, shared by both peers (NOT LIVE TESTED). Native, no <code>patch_version</code> needed - <code>bpdu_guard</code>, <code>port_type_fast</code>, <code>mtu</code>, <code>copy_description</code>, <code>enable_cdp</code>, <code>duplex</code>, <code>enable_pfc</code>, <code>queuing_policy</code>, <code>disable_lacp_suspend_individual</code>, <code>enable_lacp_vpc_convergence</code>, <code>lacp_port_priority</code>, <code>lacp_rate</code>, <code>enable_qos</code> and <code>qos_policy</code>. Registered, so they need an approved <code>patch_version</code> and NDFC 12.6.0.267 or later - <code>disable_lldp_transmit</code>, <code>disable_lldp_receive</code>, <code>spanning_tree_port_type</code>, <code>disable_queuing_stats</code>, <code>acl_filter</code> and <code>disable_qos_stats</code>. The parent hands them to both child port-channels and both members; the same merged, replaced and pre-write rules as the regular port-channel apply, on both peers. <code>speed</code> (shared by both peers) follows the port-channel rules and reaches both child port-channels and every member; the inherited member speed is judged on each peer&#x27;s own serial and preview (MEASURED for 1Gb on both peers), and one peer that does not match stops the whole vPC before any deployment. The same holds for <code>duplex</code> full with a fixed speed 1000 unchanged (MEASURED on both peers, one member per leg) - each leg is judged on its own serial and its own child port-channel, and a duplex other than auto with a resulting speed Auto, or a speed and duplex change at once on either peer, is refused before any write; the stored duplex of the parent and of each child is read back. <code>peer1_cmds</code> and <code>peer2_cmds</code> set the freeform of each peer&#x27;s port-channel under the port-channel freeform rules; a change of the freeform of one peer only is refused like any other update that reaches one peer (NOT LIVE TESTED). Ingress QoS on a vPC in mode <code>pvlan</code> (NOT LIVE TESTED) - <code>enable_qos</code>, <code>qos_policy</code> and <code>disable_qos_stats</code> follow the regular vPC merged/replaced rule (<code>merged</code> keeps an omitted field, also a residual policy when it disables QoS; <code>replaced</code> returns them to false / &#x27;&#x27; / false, the last one only with an approved <code>patch_version</code>), with two deliberate differences, so this is not full parity with the regular vPC. First, a <code>merged</code> request that changes only <code>qos_policy</code> keeps the <code>enable_qos</code> state already stored and applies the new policy; the regular vPC path currently sends an empty policy unless <code>enable_qos</code> is restated. Second, the checks are stricter than the regular ones and apply to the RESULTING state of the vPC, not only to the fields of the request. Refused before any write - <code>qos_policy</code> with QoS disabled, <code>enable_qos</code> true without a <code>qos_policy</code> (the template&#x27;s fabric-dependent default, QOS_CLASSIFICATION on an AI/ML fabric, is not modeled) and <code>disable_qos_stats</code> true without an enabled policy. Because the state is checked, an existing vPC whose stored intent is QoS enabled with an empty policy (for example a fabric-dependent default set through the GUI) refuses even a <code>merged</code> update of another field; to proceed, give the correct <code>qos_policy</code>, or set <code>enable_qos</code> false when disabling QoS is the intent. The module makes neither correction by itself. Both child port-channels are expected to carry <code>service-policy type qos input &lt;policy&gt;[ no-stats]</code>. The int_vpc_pvlan_host / int_vpc_pvlan_po revision installed on the test ND does not hand these values (nor <code>queuing_policy</code> and <code>enable_pfc</code>) to the children and renders a <code>type ENABLE_QOS</code> literal; on such a revision the deployment is refused before it is sent, and the intent change already written is reported, not rolled back. A live run therefore depends on verifying the installed template revision first.</div>
                        <div>Mode &#x27;uplink_access&#x27; (NOT LIVE TESTED) updates the existing ToR-uplink vPC of a leaf pair (policy int_vpc_uplink_access). The ToR pairing creates it, with a port-channel and member on each leaf, and owns every other field. The module never creates or deletes it, refuses state &#x27;deleted&#x27; with this mode, and never writes the port-channel children, the members or the ToR. &#x27;switch&#x27; must name both leaves of the vPC pair. The accepted fields are &#x27;enable_qos&#x27;, &#x27;qos_policy&#x27;, &#x27;disable_qos_stats&#x27;, &#x27;spanning_tree_port_type&#x27;, &#x27;enable_storm_control&#x27;, &#x27;storm_control_action&#x27; and the six &#x27;storm_control_&lt;broadcast|multicast|unicast&gt;_level_&lt;percent|pps&gt;&#x27; fields, each explicit-only with no default; any other field is refused. The mode requires NDFC 12.6.0.267 or later and an approved <code>patch_version</code>. Every other stored nvPair of the parent, including the neighbour, the port-channel IDs and the member lists, is sent back unchanged.</div>
                        <div>In mode &#x27;uplink_access&#x27;, &#x27;merged&#x27; sets the listed fields and keeps the others. &#x27;replaced&#x27;, and an &#x27;overridden&#x27; item that names the uplink, return each omitted field the controller holds to its template default - false, an empty name or level, &#x27;no&#x27; for &#x27;spanning_tree_port_type&#x27; and &#x27;default&#x27; for &#x27;storm_control_action&#x27;. &#x27;overridden&#x27; does not remove an uplink vPC that the request does not name.</div>
                        <div>In mode &#x27;uplink_access&#x27;, a request that names &#x27;enable_qos&#x27; or &#x27;qos_policy&#x27; must end with QoS disabled, or enabled with a non-empty &#x27;qos_policy&#x27; (requested, or stored under &#x27;merged&#x27;) of at most 40 characters without whitespace. The module never chooses a policy, including a fabric default. &#x27;enable_qos&#x27; false sends false, and &#x27;merged&#x27; keeps the stored name; an empty &#x27;qos_policy&#x27; sends an empty name. By the template body, the parent passes these values to the port-channel of each leaf, which attaches the policy only while QoS is enabled with a name.</div>
                        <div>In mode &#x27;uplink_access&#x27;, &#x27;storm_control_action&#x27; takes &#x27;shutdown&#x27;, &#x27;trap&#x27; or &#x27;default&#x27; (sent as &#x27;no&#x27;). A percent level is 0 to 100 with at most two decimal places, and a PPS level is an integer from 0 to 200000000. A PPS level does not accept an empty string, and 0 is a level. An explicit action or level needs &#x27;enable_storm_control&#x27; true, requested or stored. A percent and a PPS level of the same traffic type cannot be given together. Under &#x27;merged&#x27;, a level in one unit sends an empty level for a stored level in the other unit of that traffic type, so a stored PPS level is cleared by setting the percent level of that type. &#x27;replaced&#x27;, and an &#x27;overridden&#x27; item that names the uplink, clear an omitted stored level. &#x27;enable_storm_control&#x27; false under &#x27;merged&#x27; keeps the stored action and levels.</div>
                        <div>In mode &#x27;uplink_access&#x27;, enabled storm control uses one unit for every configured traffic type, as in the other storm-control modes. A request that names a storm-control field or changes any other field, and would leave storm control enabled with percent and PPS levels, requested or stored, is refused before any write. To change the unit, give every configured traffic type the new unit in one request, or clear the other levels; the module neither clears another traffic type nor converts a level. A percent level of 100 is not rendered and has no unit. Disabling storm control, and a request that names no storm-control field and changes nothing, are not judged on the stored levels.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                        <div>Vlan for the interface of first peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;access&#x27; or &#x27;dot1q&#x27;. For &#x27;dot1q&#x27; it is the dot1q-tunnel VLAN of that peer.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                        <div>Vlans that are allowed on this interface of first peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;, or &#x27;pvlan&#x27; with <code>pvlan_mode</code> <code>trunk promiscuous</code> or <code>trunk secondary</code> (PVLAN trunk allowed VLANs of that peer; <code>all</code> is refused there, no default - omitted keeps the current value in <code>merged</code>).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_native_vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Vlan used as native vlan of first peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;, or &#x27;pvlan&#x27; with <code>pvlan_mode</code> <code>trunk promiscuous</code> or <code>trunk secondary</code> (&#x27;&#x27; or one VLAN; PVLAN trunk native VLAN of that peer).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                        <div>Vlan for the interface of second peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;access&#x27; or &#x27;dot1q&#x27;. For &#x27;dot1q&#x27; it is the dot1q-tunnel VLAN of that peer.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                        <div>Vlans that are allowed on this interface of second peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;, or &#x27;pvlan&#x27; with <code>pvlan_mode</code> <code>trunk promiscuous</code> or <code>trunk secondary</code> (as <code>peer1_allowed_vlans</code>).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_native_vlan</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Vlan used as native vlan of second peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;, or &#x27;pvlan&#x27; with <code>pvlan_mode</code> <code>trunk promiscuous</code> or <code>trunk secondary</code> (as <code>peer1_native_vlan</code>).</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                <td colspan="2">
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
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pvlan_association</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Primary/secondary VLAN associations for <code>pvlan_mode</code> <code>host</code> (exactly one) and <code>trunk secondary</code> (one secondary per primary; the secondary must be an isolated VLAN), as a list of dictionaries with the keys <code>primary_vlan</code> and <code>secondary_vlan</code>.</div>
                        <div>A secondary VLAN belongs to one primary VLAN - the resulting list (after a <code>merged</code> union with the current one) that puts one secondary under two primaries is refused before any write.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pvlan_mapping</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Promiscuous mappings for <code>pvlan_mode</code> <code>promiscuous</code> (a single primary VLAN) and <code>trunk promiscuous</code>, as a list of dictionaries with the keys <code>primary_vlan</code> and <code>secondary_vlans</code> (a VLAN list string; a single-value range &quot;N-N&quot; is the VLAN N, also in <code>allowed_vlans</code>).</div>
                        <div>A secondary VLAN belongs to one primary VLAN - the resulting list (after a <code>merged</code> union with the current one) that puts one secondary under two primaries is refused before any write.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>pvlan_mode</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>host</li>
                                    <li>promiscuous</li>
                                    <li>trunk promiscuous</li>
                                    <li>trunk secondary</li>
                        </ul>
                </td>
                <td>
                        <div>Private VLAN mode. Required, and only valid, when &#x27;mode&#x27; is &#x27;pvlan&#x27;. It cannot be changed on an existing vPC.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>qos_policy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>QoS policy name to apply to the interface. This option is only valid when &#x27;enable_qos&#x27; is true. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27; or &#x27;access&#x27;</div>
                        <div>In mode &#x27;uplink_access&#x27; it is explicit-only, with no default, and needs an approved <code>patch_version</code>. See &#x27;mode&#x27; for the QoS rules of that mode.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>queuing_policy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Queuing policy name to apply to the interface. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27; or &#x27;access&#x27;</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                <td colspan="3">
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
                                    <li>breakout</li>
                        </ul>
                </td>
                <td>
                        <div>Interface type. Example, pc, vpc, sub_int, lo, eth, svi</div>
                </td>
            </tr>

            <tr>
                <td colspan="4">
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
                <td colspan="4">
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
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>override_intf_types</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>
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
                                    <li>st_fex</li>
                                    <li>aa_fex</li>
                                    <li>breakout</li>
                        </ul>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>A list of interface types which will be deleted/defaulted in overridden/deleted state. If this list is empty, then during overridden/deleted state, all interface types will be defaulted/deleted. If this list includes specific interface types, then only those interface types that are included in the list will be deleted/defaulted.</div>
                </td>
            </tr>
            <tr>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>patch_version</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Declares the installed Nexus Dashboard/NDFC patch context so the module can trust the installed interface templates to carry the registered profile fields the generic binding registry manages (for example <code>acl_filter</code>, <code>flowcontrol_receive</code>, <code>ospf_cost</code>, <code>disable_lldp_transmit</code>/<code>disable_lldp_receive</code> and the other registered fields documented per interface profile).</div>
                        <div>This is a capability declaration the caller makes; it is never sent to the controller, never part of the interface payload, and never part of the computed diff.</div>
                        <div>The same declaration selects the nvPair names of two native SVI fields of <code>int_vlan</code>, because the installed parent template names them differently in its two bodies - with a supported value <code>dhcp_server_addr4</code> and <code>dhcp_relay_src_intf</code> use <code>dhcpServerAddress4</code> and <code>dhcpRelaySourceInterface</code> (the body served with the activated SMU <code>4.3.1.0175006017</code>); without it they keep <code>dhcpServerAddr4</code> and <code>DHCP_RELAY_SRC_INTF</code>. These two fields stay native (an absent value does not reject them), only one family is ever sent, and the controller is not probed. A controller that serves the SMU body must be paired with this declaration (NOT LIVE TESTED; <code>4.4.1</code> or later is an assumption of the shared selector, not an observation). When an SVI&#x27;s stored values carry the other body&#x27;s names, setting, clearing or (replaced/overridden) resetting these fields is refused before any change is sent.</div>
                        <div>Accepts the exact SMU string <code>4.3.1.0175006017</code> or a numeric Nexus Dashboard release <code>4.4.1</code> or later, matching the version policy of <code>dcnm_network</code>. ND release strings require at least three dot-separated numeric components; additional build components must also be numeric. The first three components are compared numerically. No whitespace or suffixes are accepted. For example, <code>4.4.1.10</code> and <code>4.10.0</code> are supported, while <code>4.4.0</code>, <code>4.4</code>, <code>4.4.1-rc1</code> and adjacent unapproved <code>4.3.1</code> SMU builds are rejected.</div>
                        <div>The only SMU build this module supports is <code>4.3.1.0175006017</code>. The earlier <code>4.3.1.0175006011</code> is not accepted, because its interface templates declare different OSPF nvPair names.</div>
                        <div>On loopbacks and subinterfaces, <code>ospf_bfd_mode</code> (<code>no_change</code>, <code>enable</code>, <code>disable</code>) and, on subinterfaces, <code>ospf_passive_mode</code> (<code>no_change</code>, <code>passive</code>, <code>no_passive</code>) carry the OSPF BFD and passive settings, as on routed interfaces and SVIs. The earlier boolean inputs <code>ospf_bfd</code> and <code>ospf_passive_interface</code> are still accepted as aliases - <code>true</code> means <code>enable</code> or <code>passive</code>; <code>false</code> keeps its old meaning of no local override and therefore means <code>no_change</code>, never the explicit <code>disable</code> or <code>no_passive</code>. Give the mode key to request an explicit negative setting. Giving both spellings is accepted only when they mean the same, and the alias is refused on a parent that does not register it.</div>
                        <div>Fields that only the <code>4.3.1.0175006017</code> templates declare (NOT LIVE TESTED; read from the installed template bodies). On a routed Ethernet - <code>enable_cdp</code> (bool; CDP stays on unless false, which renders <code>no cdp enable</code>), <code>enable_evpn_multisite_dci_tracking</code> (bool; renders <code>evpn multisite dci-tracking</code>; the template does not check the switch role, so whether NX-OS accepts it outside a multisite border gateway is not established) and <code>ospf_retransmit_interval</code> (1-65535; requires <code>enable_ospf</code>; <code>5</code> is the NX-OS default and renders nothing). On an access Ethernet - <code>logging_event_port_link_status</code> (bool; renders <code>logging event port link-status</code>). On a subinterface - <code>enable_pim_bfd_instance</code> (bool; renders <code>ip pim bfd-instance</code>, independent of <code>enable_pim_sparse</code>). Under <code>replaced</code> and <code>overridden</code> an omitted value is reset to the template default (<code>enable_cdp</code> true, the other booleans false, the interval cleared); under <code>merged</code> it is preserved. A leaf reset of an access Ethernet with <code>logging_event_port_link_status</code> true goes to <code>int_trunk_host</code> in the usual single request; <code>int_trunk_host</code> does not declare the field, and the controller removes the line with the policy change (measured on NDFC 12.6.0.267 with the <code>4.3.1.0175006017</code> templates). <code>enable_cdp</code> keeps its native behaviour on the access, trunk, dot1q-tunnel, PVLAN, port-channel and vPC profiles.</div>
                        <div>On a loopback, the <code>4.3.1.0175006017</code> templates also declare the EIGRP fields that the routed, subinterface and SVI profiles already accept (NOT LIVE TESTED; read from the installed template body) - <code>enable_eigrp_ipv6_routing</code> (bool; renders <code>ipv6 router eigrp &lt;tag&gt;</code>), <code>eigrp_ipv4_distribute_list_prefix_list</code> and <code>eigrp_ipv6_distribute_list_prefix_list</code> (up to 63 characters; render <code>ip distribute-list eigrp &lt;tag&gt; prefix-list &lt;name&gt; &lt;direction&gt;</code> and its IPv6 form), and <code>eigrp_ipv4_distribute_list_direction</code> and <code>eigrp_ipv6_distribute_list_direction</code> (<code>in</code> or <code>out</code>, default <code>out</code>; used only with their prefix list). All need <code>eigrp_process_tag</code>; the template refuses an option without it and the module does not check it. The module never creates or deletes the referenced prefix lists. Under <code>replaced</code> and <code>overridden</code> an omitted value is reset to the template default (<code>false</code>, an empty list, <code>out</code>); under <code>merged</code> it is preserved.</div>
                        <div>On a routed port-channel (<code>type</code> <code>pc</code>, <code>mode</code> <code>l3</code>), the <code>4.3.1.0175006017</code> template also declares <code>enable_pim_bfd_instance</code> (bool; renders <code>ip pim bfd-instance</code>; NOT LIVE TESTED, read from the installed template body). The template does not require PIM sparse mode, which this profile does not accept. Under <code>replaced</code> and <code>overridden</code> an omitted value is reset to false; under <code>merged</code> it is preserved.</div>
                        <div>The routed port-channel also accepts the OSPF keys of the routed Ethernet profile, with the same meaning and dependencies (the <code>4.3.1.0175006017</code> declarations are identical) - <code>enable_ospf</code>, <code>ospf_tag</code>, <code>ospf_area_id</code>, <code>enable_ospf_auth</code>, <code>ospf_auth_key_id</code>, <code>ospf_auth_key</code>, <code>ospf_authentication_key_type</code>, <code>ospf_authentication_key</code>, <code>ospf_passive_mode</code>, <code>ospf_cost</code>, <code>ospf_mtu_ignore</code>, <code>ospf_hello_interval</code>, <code>ospf_dead_interval</code>, <code>ospf_shutdown</code>, <code>ospf_transmit_delay</code>, <code>ospf_retransmit_interval</code>, <code>ospf_priority</code>, <code>ospf_network_type</code> and <code>ospf_bfd_mode</code>. Every option needs <code>enable_ospf</code> true with a tag and an area; disabling OSPF clears the options and the message-digest key in the same request, and keeps the tag stored but inert. Configuration of all 19 keys was measured on NDFC 12.6.0.267 with the <code>4.3.1.0175006017</code> templates under <code>merged</code> and <code>replaced</code>. <code>deleted</code> removed a port-channel that carried <code>enable_ospf</code>, <code>ospf_tag</code>, <code>ospf_area_id</code>, <code>ospf_cost</code>, <code>ospf_hello_interval</code>, <code>ospf_dead_interval</code>, <code>ospf_priority</code>, <code>ospf_network_type</code>, <code>ospf_passive_mode</code> and <code>ospf_retransmit_interval</code>; the other keys were not set at that point. Under <code>overridden</code>, with the port-channel kept and <code>override_intf_types</code> <code>[pc]</code>, <code>ospf_authentication_key</code>, <code>enable_ospf_auth</code> with <code>ospf_auth_key</code>, <code>ospf_mtu_ignore</code>, <code>ospf_shutdown</code>, <code>ospf_transmit_delay</code> and <code>ospf_bfd_mode</code> were set and withdrawn while the other keys stayed unchanged, and <code>ospf_auth_key_id</code> stayed <code>1</code>. The simple key was measured with <code>ospf_authentication_key_type</code> <code>7</code> only, and the message-digest key with a type 3 encrypted key, which the template renders after <code>md5 3</code>. <code>query</code>, the <code>4.4.1</code> bodies, OSPF adjacency and traffic are NOT LIVE TESTED.</div>
                        <div>On a trunk port-channel (<code>mode=trunk</code>) the <code>4.3.1.0175006017</code> templates declare <code>link_transmit_reset_skip</code> (bool; the nvPair <code>linkTransmitResetSkip</code> of <code>int_port_channel_trunk_host</code>). It is the default a member takes when it joins the port-channel. A member that already exists keeps its stored value when the option is raised or lowered, so a false option does not mean every member is false. The module writes only the port-channel parent. It never writes a member and never detaches or rejoins one. Under <code>merged</code>, an explicit true or false replaces the stored parent value and an omitted option keeps it, including in a description-only update. Under <code>replaced</code>, and for a port-channel that <code>overridden</code> keeps, an omitted option resets the parent to the template default (<code>false</code>); each member keeps its stored value, so this does not withdraw a member command. <code>deleted</code> and a port-channel that <code>overridden</code> leaves out use the existing aggregate removal and member release. <code>query</code> returns the parent value as the controller stores it and does not show that the members match it. The module does not check whether the device applies the rendered <code>link transmit reset-skip</code> line.</div>
                        <div>This is a SECOND, independent requirement on top of each registered field&#x27;s existing minimum NDFC version. Meeting the per-field NDFC floor does not substitute for a supported patch/ND release, and that release does not bypass a field&#x27;s NDFC floor or its <code>smu_unsupported</code> exclusion when one exists; both conditions must hold together before a registered field is configurable.</div>
                        <div>There is no enabling default anywhere in the module. When this is omitted, null, empty, malformed, or unsupported, the module rejects the ENTIRE invocation before any configuration or deployment request is sent, as soon as any config entry sets a registered field explicitly -- including a native/legacy-only entry earlier in the same task list, per the normal invocation-wide preflight this module already applies to its other validation failures.</div>
                        <div>When a registered field is merely OMITTED (not set) while this capability is disabled, the module does not reset, clear, or otherwise change that field. For an interface RETAINED under <code>replaced</code> or <code>overridden</code> (same parent, same identity, not newly created and not explicitly removed), its existing controller value is carried forward unchanged in the full replacement payload, exactly as it would be if the field were not part of this registry at all. This preservation scope is specifically the retained-same-parent carry-forward; it does not change whole-object deletion (<code>state=deleted</code> or an explicit removal under <code>overridden</code>) or an interface&#x27;s transition to a different parent template, both of which keep their existing, independent contracts.</div>
                        <div>With this capability enabled, resetting a physical Ethernet port to its role default (a port named under <code>state=deleted</code>, or a port <code>overridden</code> leaves out) also sends, for each registered field the port still holds, that field&#x27;s verified reset value on the default parent template. The module verifies the request it sends, not that the controller or the switch removes the configuration. A field without a verified reset, a controller value that cannot be classified, or a field the port&#x27;s current policy holds but the default parent cannot withdraw (the reset changes the policy) refuses the ENTIRE invocation before any request is sent, naming the interface and the field, never its value; such a field needs a separate, verified clean-up. A port that is not reset (still configured, or skipped by scope) is not affected, and a former port-channel member reset after its port-channel is deleted is not covered. With the capability disabled these fields are left unchanged, as before.</div>
                        <div>Some registered fields depend on another option of the same interface on int_routed_host, int_subif, int_vlan and int_loopback - the OSPF options, process tag and authentication fields on <code>enable_ospf</code>, the message-digest key and key ID on <code>enable_ospf_auth</code>, the simple-key encryption type on <code>ospf_authentication_key</code>. While that option is disabled they configure nothing. Disabling it sends the neutral value of each dependent option, keeps a stored process tag or encryption type as inert stored data, and clears a stored message-digest key. In <code>merged</code>, an explicit <code>enable_ospf</code> or <code>enable_ospf_auth</code> false does the same for the stored dependents; omitting it preserves them as usual. Before any request, the module refuses an explicit non-neutral OSPF option while OSPF ends disabled, an explicit empty <code>ospf_tag</code> or <code>ospf_auth_key</code> while its option is enabled, and enabling message-digest authentication over a cleared key without a new key. A port reset while such an option is still enabled is refused and names the option to disable first. On int_loopback in the default VRF (<code>int_vrf</code> default) the template keeps the loopback in the fabric underlay OSPF process whatever <code>enable_ospf</code> says, with the stored process tag first, so the tag and the OSPF options stay live there. A disable in that VRF must state <code>ospf_tag</code> and does not remove the OSPF line, and an explicit <code>merged</code> disable keeps the options. The authentication rules apply in every VRF.</div>
                        <div>Registered string fields whose letter case is part of the value (authentication keys and ACL, prefix-list or MACsec key-chain and policy names) are compared case-sensitively, so a change of case alone is sent. IPv6 text, numeric fields, booleans and enumerations keep their case-insensitive comparison, and so do process tags, whose case semantics are not established.</div>
                        <div>Existing playbooks that already set a registered field (see the list above) must add this argument -- directly on the task, or once via <code>module_defaults</code> for <code>cisco.dcnm.dcnm_interface</code> -- to keep working under this module version. A playbook that only uses native/legacy fields needs no change.</div>
                        <div>The module performs no automatic patch discovery and applies no environment-based fallback; the caller is the sole source of this value.</div>
                </td>
            </tr>
            <tr>
                <td colspan="4">
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

    ## Loopback Interfaces Created During Fabric Creation
    - name: Mange Fabric loopback interfaces
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: merged
        config:
          - name: lo1                           # This is usually lo0 or lo1 created during fabric creation
            type: lo
            switch:
              - "192.172.1.1"                   # provide the switch where to deploy the config
            deploy: true                        # choose from [true, false]
            profile:
              admin_state: false                # choose from [true, false]
              mode: fabric                      # This must be set to 'fabric' for fabric loopback interfaces
              secondary_ipv4_addr: 172.16.5.1   # secondary ipv4 address for loopback interface
              route_tag: "100"                  # Routing Tag for the interface
              cmds:                             # Freeform config
                - no shutdown
              description: "Fabric interface managed by Ansible"

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


    - name: Create a dot1q-tunnel vPC
      cisco.dcnm.dcnm_interface:
        fabric: mmudigon-fabric
        state: merged
        # Required because the profile below sets disable_lldp_transmit/disable_lldp_receive,
        # both registered generic-binding-registry fields. Without a supported patch/ND release
        # context, the module rejects this whole task before any configuration/deployment call
        # -- there is no product default that enables these fields. See the patch_version
        # option documentation for the version/floor/migration contract.
        patch_version: "4.3.1.0175006017"
        config:
          - name: vpc760                      # should be of the form vpc<port-id>
            type: vpc
            switch:                           # both switches of the vPC pair
              - "192.172.1.1"
              - "192.172.1.2"
            deploy: true
            profile:
              mode: dot1q                     # dot1q-tunnel vPC (int_vpc_dot1q_tunnel), NDFC 12
              peer1_pcid: 760
              peer2_pcid: 760
              peer1_members:
                - e1/27
              peer2_members:
                - e1/27
              peer1_access_vlan: 3790         # dot1q-tunnel VLAN on peer 1
              peer2_access_vlan: 3790         # dot1q-tunnel VLAN on peer 2
              peer1_description: "dot1q-tunnel vPC peer1"
              peer2_description: "dot1q-tunnel vPC peer2"
              disable_lldp_transmit: true     # registered generic fields of this parent --
              disable_lldp_receive: true      # require patch_version above (see note)

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
              # peer2_pcid: 1                  # choose between [Min:1, Max:4096], if not given, will be VPC port-id
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
              ipv4_addr: 192.0.2.1                      # optional, Interfae IP, default is ""
              ipv4_mask_len: 24                         # optional, IP mask length, default is ""
              mtu: 9216                                 # optional, MTU default is ""
              route_tag: 1001                           # optional, Routing TAG, default is ""
              disable_ip_redirects: true                # optional, flag to enable/disable IP redirects, default is "false"
              cmds:                                     # Freeform config
                - no shutdown
              admin_state: true                         # Flag to enable/disable Vlan interaface
              enable_hsrp: true                         # optional, flag to enable/disable HSRP on the interface, default is "false"
              hsrp_vip: 192.0.2.100                     # optional, Virtual IP address for HSRP, default is ""
              hsrp_group: 10                            # optional, HSRP group, default is ""
              hsrp_priority: 5                          # optional, HSRP priority, default is ""
              hsrp_vmac: 0000.0101.ac0a                 # optional, HSRP virtual MAC, default is ""
              dhcp_server_addr1: 192.200.1.1            # optional, DHCP relay server address, default is ""
              vrf_dhcp1: blue                           # optional, VRF to reach DHCP server. default is ""
              dhcp_server_addr2: 192.200.1.2            # optional, DHCP relay server address, default is ""
              vrf_dhcp2: blue                           # optional, VRF to reach DHCP server. default is ""
              dhcp_server_addr3: 192.200.1.3            # optional, DHCP relay server address, default is ""
              vrf_dhcp3: blue                           # optional, VRF to reach DHCP server. default is ""
              dhcp_server_addr4: 192.200.1.4            # optional, DHCP relay server address, default is ""
              vrf_dhcp4: blue                           # optional, VRF to reach DHCP server. default is ""
              dhcp_relay_src_intf: loopback0            # optional, source interface for DHCP relay, default is ""
              adv_subnet_in_underlay: true              # optional, flag to enable/disable advertisements of subnets into underlay, default is "false"
              enable_netflow: false                     # optional, flag to enable netflow, default is "false"
              netflow_monitor: svi1001                  # optional, name of netflow monitor, default is ""
              hsrp_version: 1                           # optional, HSRP protocol version, default is 1
              preempt: true                             # optional, flag to enable/disable overthrow of low priority active routers, optional is "false"
              mode: vlan                                # choose from [vlan, vlan_admin_state], default is "vlan"
              description: Switched vlan interface 1001 # optional, Interface description, default is ""
              secondary_gws:                            # optional, secondary IPv4 addresses (max 16)
                - gateway_ip_address: 198.51.100.1/24
                - gateway_ip_address: 203.0.113.1/24
              hsrp_secondary_vips:                      # optional, secondary HSRP virtual addresses (max 16)
                - hsrp_secondary_vip: 192.0.2.101
                - hsrp_secondary_vip: 192.0.2.102

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
              dhcp_server_addr4: 193.200.1.4                  # optional, DHCP relay server address, default is ""
              vrf_dhcp4: green                                # optional, VRF to reach DHCP server. default is ""
              dhcp_relay_src_intf: loopback0                  # optional, source interface for DHCP relay, default is ""
              adv_subnet_in_underlay: false                   # optional, flag to enable/disable advertisements of subnets into underlay, default is "false"
              enable_netflow: false                           # optional, flag to enable netflow, default is "false"
              netflow_monitor: svi1002                        # optional, name of netflow monitor, default is ""
              hsrp_version: 2                                 # optional, HSRP protocol version, default is 1
              preempt: false                                  # optional, flag to enable/disable overthrow of low priority active routers, optional is "false"
              mode: vlan                                      # choose from [vlan, vlan_admin_state], default is "vlan"
              description: Switched vlan interface 1001 - Rep # optional, Interface description, default is ""

    - name: Delete SVI interfaces
      cisco.dcnm.dcnm_interface:
        check_deploy: true
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
        check_deploy: true
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
        check_deploy: true
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
        check_deploy: true
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

    # Dot1q Tunnel host

    - name: Configure dot1q on interface E1/12
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: merged
        config:
          - name: eth1/12
            type: eth
            switch:
              - "{{ ansible_switch1 }}"
            deploy: true
            profile:
            admin_state: true
            mode: dot1q
            access_vlan: 41
            description: "ETH 1/12 Dot1q Tunnel"

    # Private VLAN (int_pvlan_host, NDFC 12)

    - name: Configure a trunk promiscuous PVLAN port
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: merged
        config:
          - name: eth1/7
            type: eth
            switch:
              - "{{ ansible_switch1 }}"
            deploy: true
            profile:
              mode: pvlan
              pvlan_mode: trunk promiscuous
              admin_state: false
              pvlan_mapping:
                - primary_vlan: 2210
                  secondary_vlans: "2211-2212"
              native_vlan: "2301"
              allowed_vlans: "2301"

    - name: Make a PVLAN host port exactly one association (replaced clears omitted fields)
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: replaced
        config:
          - name: eth1/8
            type: eth
            switch:
              - "{{ ansible_switch1 }}"
            deploy: true
            profile:
              mode: pvlan
              pvlan_mode: host
              pvlan_association:
                - primary_vlan: 2210
                  secondary_vlan: 2212

    # Private VLAN on a regular port-channel (int_port_channel_pvlan_host, NDFC 12; explicit physical member lists)

    - name: Create a port-channel in PVLAN host mode with one administratively down member
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: replaced
        config:
          - name: po10
            type: pc
            switch:
              - "{{ ansible_switch1 }}"
            deploy: true
            profile:
              mode: pvlan
              pvlan_mode: host
              members:
                - Ethernet1/7
              pc_mode: active
              admin_state: false
              pvlan_association:
                - primary_vlan: 2210
                  secondary_vlan: 2212

    - name: Create a port-channel in PVLAN host mode whose member is already administratively up (it joins and stays up)
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: merged
        config:
          - name: po11
            type: pc
            switch:
              - "{{ ansible_switch1 }}"
            deploy: true
            profile:
              mode: pvlan
              pvlan_mode: host
              members:
                - Ethernet1/8               # int_trunk_host with ADMIN_STATE true: no shutdown before or after the join
              admin_state: false            # the port-channel's own state; it does not change the member's
              pvlan_association:
                - primary_vlan: 2210
                  secondary_vlan: 2212
    # Deleting po11 later releases its member to the fabric's host interface default (HOST_INTF_ADMIN_STATE).

    - name: Set companion controls of that port-channel (NOT LIVE TESTED; the LLDP and spanning-tree fields are registered)
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: merged
        patch_version: "4.3.1.0175006017"   # required by disable_lldp_transmit and spanning_tree_port_type only
        config:
          - name: po10
            type: pc
            switch:
              - "{{ ansible_switch1 }}"
            deploy: true
            profile:
              mode: pvlan
              pvlan_mode: host
              enable_cdp: false                 # native: reaches the member as 'no cdp enable'
              lacp_port_priority: 100           # native: member 'lacp port-priority 100'
              queuing_policy: QUEUING_POLICY_1  # native: Po 'service-policy type queuing output ...'
              disable_lldp_transmit: true       # registered: member 'no lldp transmit'
              port_type_fast: false             # required with a spanning-tree port type other than 'no'
              spanning_tree_port_type: network  # registered: Po 'spanning-tree port type network'

    - name: Delete that port-channel (its member is released to the fabric's host interface default)
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: deleted
        config:
          - name: po10
            switch:
              - "{{ ansible_switch1 }}"
            deploy: true

    # Private VLAN on a vPC (int_vpc_pvlan_host, NDFC 12; explicit members per peer, optional peer1_pcid/peer2_pcid)

    - name: Create a vPC in PVLAN host mode (peer1_* belong to the first switch, peer2_* to the second)
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: merged
        config:
          - name: vpc10
            type: vpc
            switch:
              - "{{ ansible_switch1 }}"
              - "{{ ansible_switch2 }}"
            deploy: true
            profile:
              mode: pvlan
              pvlan_mode: host
              peer1_members:
                - Ethernet1/7
              peer2_members:
                - Ethernet1/8
              peer1_pcid: 10
              peer2_pcid: 10
              admin_state: false
              pvlan_association:
                - primary_vlan: 2210
                  secondary_vlan: 2212

    - name: Create a vPC in PVLAN promiscuous mode (a single primary VLAN)
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: merged
        config:
          - name: vpc11
            type: vpc
            switch:
              - "{{ ansible_switch1 }}"
              - "{{ ansible_switch2 }}"
            deploy: true
            profile:
              mode: pvlan
              pvlan_mode: promiscuous
              peer1_members:
                - Ethernet1/9
              peer2_members:
                - Ethernet1/9
              peer1_pcid: 11
              peer2_pcid: 11
              admin_state: false
              pvlan_mapping:
                - primary_vlan: 2210
                  secondary_vlans: "2211-2212"

    - name: Create a vPC in PVLAN trunk promiscuous mode with per-peer native/allowed VLANs
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: merged
        config:
          - name: vpc12
            type: vpc
            switch:
              - "{{ ansible_switch1 }}"
              - "{{ ansible_switch2 }}"
            deploy: true
            profile:
              mode: pvlan
              pvlan_mode: trunk promiscuous
              peer1_members:
                - Ethernet1/10
              peer2_members:
                - Ethernet1/10
              peer1_pcid: 12
              peer2_pcid: 12
              admin_state: false
              pvlan_mapping:
                - primary_vlan: 2210
                  secondary_vlans: "2211-2212"
                - primary_vlan: 2410
                  secondary_vlans: "2412"
              peer1_native_vlan: "2301"
              peer2_native_vlan: "2301"
              peer1_allowed_vlans: "2301"
              peer2_allowed_vlans: "2301"

    - name: Create a vPC in PVLAN trunk secondary mode (both members must ALREADY be prepared as access or routed ports; up or down)
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: merged
        config:
          - name: vpc13
            type: vpc
            switch:
              - "{{ ansible_switch1 }}"
              - "{{ ansible_switch2 }}"
            deploy: true
            profile:
              mode: pvlan
              pvlan_mode: trunk secondary
              peer1_members:
                - Ethernet1/11
              peer2_members:
                - Ethernet1/11
              peer1_pcid: 13
              peer2_pcid: 13
              admin_state: false
              pvlan_association:
                - primary_vlan: 2210
                  secondary_vlan: 2212
              peer1_native_vlan: "2301"
              peer2_native_vlan: "2301"
              peer1_allowed_vlans: "2301"
              peer2_allowed_vlans: "2301"

    - name: Delete that vPC (both peers verified; each member released to the fabric's host interface default, corrected only if needed)
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_fabric }}"
        state: deleted
        config:
          - name: vpc10
            type: vpc
            switch:
              - "{{ ansible_switch1 }}"
              - "{{ ansible_switch2 }}"
            deploy: true

    # Breakout interfaces

    - name: Configure breakout interface
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_svi_fabric }}"
        state: merged
        config:
          - name: ethernet1/100
            type: breakout
            switch:
              - "{{ ansible_switch1 }}"
            deploy: true
            profile:
              map: 10g-4x
          - name: ethernet1/101
            type: breakout
            switch:
              - "{{ ansible_switch1 }}"
            deploy: true
            profile:
              map: 10g-4x
          - name: ethernet1/102
            type: breakout
            switch:
              - "{{ ansible_switch1 }}"
            deploy: true
            profile:
              map: 10g-4x

    - name: Configure breakout interface
      cisco.dcnm.dcnm_interface:
        fabric: "{{ ansible_svi_fabric }}"
        state: deleted
        config:
          - name: ethernet1/100
            type: breakout
            switch:
              - "{{ ansible_switch1 }}"
          - name: ethernet1/101
            type: breakout
            switch:
              - "{{ ansible_switch1 }}"
          - name: ethernet1/102
            type: breakout
            switch:
              - "{{ ansible_switch1 }}"

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
