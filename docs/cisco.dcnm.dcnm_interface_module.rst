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
                        <div>Secondary VLAN IDs as a string, for example &quot;2211&quot; or &quot;2211-2212,2214&quot;.</div>
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
                        <div>In mode &#x27;pvlan&#x27; the supported companion fields are &#x27;description&#x27;, &#x27;admin_state&#x27;, &#x27;bpdu_guard&#x27;, &#x27;port_type_fast&#x27;, &#x27;mtu&#x27;, &#x27;speed&#x27;, &#x27;enable_cdp&#x27;, &#x27;orphan_port&#x27;, &#x27;duplex&#x27;, &#x27;enable_pfc&#x27;, &#x27;enable_qos&#x27;, &#x27;qos_policy&#x27;, &#x27;queuing_policy&#x27; and &#x27;cmds&#x27;. Any other field is refused. &#x27;cmds&#x27; must not carry private-vlan or switchport lines. &#x27;native_vlan&#x27; (&#x27;&#x27; or one VLAN) and &#x27;allowed_vlans&#x27; (&#x27;&#x27;, &#x27;none&#x27; or VLAN ranges; &#x27;all&#x27; is refused) apply to the two trunk submodes only.</div>
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
                        <div>Disable statistics for the attached QoS policy. This option is applicable only when mode is trunk, access or dot1q.</div>
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
                        <div>Disable statistics for the attached output queuing policy. This option is applicable only when mode is trunk, access or dot1q.</div>
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
                        <div>Spanning-tree port type. This option is applicable only when mode is trunk, access or dot1q.</div>
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
                        <div>Source interface for DHCP relay. Valid interfaces are Ethernet, port-channel or loopback.</div>
                        <div>Independent of the DHCP server addresses; it can be set on its own.</div>
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
                        </ul>
                </td>
                <td>
                        <div>Interface mode</div>
                        <div><code>dot1q</code> selects the dot1q-tunnel vPC template (<code>int_vpc_dot1q_tunnel</code>) and requires NDFC 12. It takes the same options as <code>access</code>, plus the LACP options.</div>
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
                        <div>Vlans that are allowed on this interface of first peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;</div>
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
                        <div>Vlan used as native vlan of first peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;</div>
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
                        <div>Vlans that are allowed on this interface of second peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;</div>
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
                        <div>Vlan used as native vlan of second peer. This option is applicable only for interfaces whose &#x27;mode&#x27; is &#x27;trunk&#x27;</div>
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
                        <div>The only value this module currently accepts is the exact string <code>4.3.1.0175006011</code>. No other string is treated as equivalent: a shorter prefix such as <code>4.3.1</code>, a numerically adjacent SMU build, or a newer Nexus Dashboard release (including ND&gt;=4.4.1, accepted by a different module&#x27;s ACL-focused capability check) are all rejected the same as an omitted value. There is no partial match and no numeric &#x27;newer therefore acceptable&#x27; comparison.</div>
                        <div>This is a SECOND, independent requirement on top of each registered field&#x27;s existing minimum NDFC version. Meeting the per-field NDFC floor does not substitute for an approved patch, and an approved patch does not bypass a field&#x27;s NDFC floor or its <code>smu_unsupported</code> exclusion when one exists; both conditions must hold together before a registered field is configurable.</div>
                        <div>There is no enabling default anywhere in the module. When this is omitted, null, empty, or not the exact approved value, the module rejects the ENTIRE invocation before any configuration or deployment request is sent, as soon as any config entry sets a registered field explicitly -- including a native/legacy-only entry earlier in the same task list, per the normal invocation-wide preflight this module already applies to its other validation failures.</div>
                        <div>When a registered field is merely OMITTED (not set) while this capability is disabled, the module does not reset, clear, or otherwise change that field. For an interface RETAINED under <code>replaced</code> or <code>overridden</code> (same parent, same identity, not newly created and not explicitly removed), its existing controller value is carried forward unchanged in the full replacement payload, exactly as it would be if the field were not part of this registry at all. This preservation scope is specifically the retained-same-parent carry-forward; it does not change whole-object deletion (<code>state=deleted</code> or an explicit removal under <code>overridden</code>) or an interface&#x27;s transition to a different parent template, both of which keep their existing, independent contracts.</div>
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
        # both registered generic-binding-registry fields. Without the exact approved patch
        # context, the module rejects this whole task before any configuration/deployment call
        # -- there is no product default that enables these fields. See the patch_version
        # option documentation for the version/floor/migration contract.
        patch_version: "4.3.1.0175006011"
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
