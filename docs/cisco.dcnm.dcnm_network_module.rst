.. _cisco.dcnm.dcnm_network_module:


***********************
cisco.dcnm.dcnm_network
***********************

**Add and remove Networks from a ND managed VXLAN fabric.**


Version added: 0.9.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Add and remove Networks from a ND managed VXLAN fabric.
- For multisite (MSD) fabrics, child fabric configurations can be specified using the child_fabric_config parameter
- The attribute _fabric_type (standalone, multisite_parent, multisite_child) is automatically detected and should not be manually specified by the user




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
                    <b>_fabric_details</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>INTERNAL PARAMETER - DO NOT USE</div>
                        <div>Fabric details dictionary automatically provided by the action plugin</div>
                        <div>Contains fabric_type, cluster_name, and nd_version information</div>
                        <div>This parameter is used internally by the action plugin for MSD/MFD fabric processing</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>cluster_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Name of the cluster if applicable</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>fabric_type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>multicluster_parent</li>
                                    <li>multicluster_child</li>
                                    <li>multisite_parent</li>
                                    <li>multisite_child</li>
                                    <li>standalone</li>
                        </ul>
                </td>
                <td>
                        <div>Type of fabric (multicluster_parent, multicluster_child, multisite_parent, multisite_child, standalone)</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>nd_version</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">float</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>ND/NDFC version number used for API path selection</div>
                        <div>Automatically provided by action plugin</div>
                        <div>Module will fail if this is not provided by action plugin</div>
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
                </td>
                <td>
                        <div>List of details of networks being managed. Not required for state deleted</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>arp_suppress</b>
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
                        <div>ARP suppression</div>
                        <div>ARP suppression is only supported if SVI is present when Layer-2-Only is not enabled</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>attach</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>List of network attachment details</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
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
                        <div>Per switch knob to control whether to deploy the attachment</div>
                        <div>This knob has been deprecated from Ansible NDFC Collection Version 2.1.0 onwards. There will not be any functional impact if specified in playbook.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ip_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address of the switch where the network will be attached or detached</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ports</b>
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
                        <div>List of switch interfaces where the network will be attached</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>tor_ports</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>List of interfaces in the paired TOR switch for this leaf where the network will be attached</div>
                        <div>Please attach the same set of TOR ports to both the VPC paired switches.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ip_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address of the TOR switch where the network will be attached</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ports</b>
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
                        <div>List of TOR switch interfaces where the network will be attached</div>
                </td>
            </tr>


            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>child_fabric_config</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>List of child fabric configurations for MSD (Multi-Site Domain) parent fabrics</div>
                        <div>Only valid when the fabric is an MSD parent fabric</div>
                        <div>Child fabric configurations cannot contain &#x27;attach&#x27; parameter - attachments are managed at parent level only</div>
                        <div>Child-specific parameters like dhcp_loopback_id, l3gw_on_border, netflow_enable, etc. can be specified per child</div>
                        <div>Deploy setting defaults to parent&#x27;s deploy value but can be overridden per child fabric</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
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
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Override deploy setting for this child fabric</div>
                        <div>If not specified, inherits the deploy value from parent fabric configuration</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_loopback_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Child-specific Loopback ID for DHCP Relay interface</div>
                        <div>Configured ID value should be in range 0-1023</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_servers</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Child-specific List of DHCP server_vrf pairs where &#x27;srvr_ip&#x27; is the IP key and &#x27;srvr_vrf&#x27; is the VRF key</div>
                        <div>The &#x27;srvr_vrf&#x27; key is optional, if not specified will use same VRF as the network VRF</div>
                        <div>For ND version 3.1 and NDFC 12.1 &#x27;srvr_vrf&#x27; must be specified for each DHCP server</div>
                        <div>This replaces dhcp_srvr1_ip, dhcp_srvr1_vrf, dhcp_srvr2_ip, dhcp_srvr2_vrf, dhcp_srvr3_ip, dhcp_srvr3_vrf</div>
                        <div>If both dhcp_servers and any of dhcp_srvr1_ip, dhcp_srvr1_vrf, dhcp_srvr2_ip, dhcp_srvr2_vrf, dhcp_srvr3_ip, dhcp_srvr3_vrf are specified an error message is generated indicating these are mutually exclusive options</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr1_ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Child-specific DHCP relay IP address of the first DHCP server</div>
                        <div>If dhcp_servers and dhcp_srvr1_ip are specified an error message is generated indicating these are mutually exclusive options</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr1_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Child-specific VRF ID of first DHCP server</div>
                        <div>If not specified, will use same VRF as the network VRF</div>
                        <div>For ND version 3.1 and NDFC 12.1 dhcp_srvr1_vrf must be specified for dhcp_srvr1_ip</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr2_ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Child-specific DHCP relay IP address of the second DHCP server</div>
                        <div>If dhcp_servers and dhcp_srvr2_ip are specified an error message is generated indicating these are mutually exclusive options</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr2_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Child-specific VRF ID of second DHCP server</div>
                        <div>If not specified, will use same VRF as the network VRF</div>
                        <div>For ND version 3.1 and NDFC 12.1 dhcp_srvr2_vrf must be specified for dhcp_srvr2_ip</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr3_ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Child-specific DHCP relay IP address of the third DHCP server</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>If dhcp_servers and dhcp_srvr3_ip are specified an error message is generated indicating these are mutually exclusive options</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr3_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Child-specific VRF ID of third DHCP server</div>
                        <div>If not specified, will use same VRF as the network VRF</div>
                        <div>For ND version 3.1 and NDFC 12.1 dhcp_srvr3_vrf must be specified for dhcp_srvr3_ip</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
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
                        <div>Name of the child fabric</div>
                        <div>Child fabric must be a member of the specified MSD parent fabric</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>l3gw_on_border</b>
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
                        <div>Child-specific Enable L3 Gateway on Border setting</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>multicast_group_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Child-specific multicast IP address for the network</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>netflow_enable</b>
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
                        <div>Child-specific Enable Netflow setting</div>
                        <div>Netflow is supported only if it is enabled on fabric</div>
                        <div>Netflow configs are supported on NDFC only</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>trm_enable</b>
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
                        <div>Child-specific Enable Tenant Routed Multicast</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vlan_nf_monitor</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Child-specific Vlan Netflow Monitor</div>
                        <div>Provide monitor name defined in fabric setting for Layer 3 Record</div>
                        <div>Netflow configs are supported on NDFC only</div>
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
                        <div>Global knob to control whether to deploy the attachment</div>
                        <div>Ansible NDFC Collection Behavior for Version 2.0.1 and earlier</div>
                        <div>This knob will create and deploy the attachment in ND only when set to &quot;True&quot; in playbook</div>
                        <div>Ansible NDFC Collection Behavior for Version 2.1.0 and later</div>
                        <div>Attachments specified in the playbook will always be created in DCNM. This knob, when set to &quot;True&quot;,  will deploy the attachment in DCNM, by pushing the configs to switch. If set to &quot;False&quot;, the attachments will be created in DCNM, but will not be deployed</div>
                        <div>Defaults to true. For MSD parent fabrics, this value is copied to child fabrics unless overridden at child level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_loopback_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Loopback ID for DHCP Relay interface</div>
                        <div>Configured ID value should be in range 0-1023</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_servers</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>List of DHCP server_vrf pairs where &#x27;srvr_ip&#x27; is the IP key and &#x27;srvr_vrf&#x27; is the VRF key</div>
                        <div>The &#x27;srvr_vrf&#x27; key is optional, if not specified will use same VRF as the network VRF</div>
                        <div>For ND version 3.1 and NDFC 12.1 &#x27;srvr_vrf&#x27; must be specified for each DHCP server</div>
                        <div>This replaces dhcp_srvr1_ip, dhcp_srvr1_vrf, dhcp_srvr2_ip, dhcp_srvr2_vrf, dhcp_srvr3_ip, dhcp_srvr3_vrf</div>
                        <div>If both dhcp_servers and any of dhcp_srvr1_ip, dhcp_srvr1_vrf, dhcp_srvr2_ip, dhcp_srvr2_vrf, dhcp_srvr3_ip, dhcp_srvr3_vrf are specified an error message is generated indicating these are mutually exclusive options</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr1_ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>DHCP relay IP address of the first DHCP server</div>
                        <div>If dhcp_servers and dhcp_srvr1_ip are specified an error message is generated indicating these are mutually exclusive options</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr1_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VRF ID of first DHCP server</div>
                        <div>If not specified, will use same VRF as the network VRF</div>
                        <div>For ND version 3.1 and NDFC 12.1 dhcp_srvr1_vrf must be specified for dhcp_srvr1_ip</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr2_ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>DHCP relay IP address of the second DHCP server</div>
                        <div>If dhcp_servers and dhcp_srvr2_ip are specified an error message is generated indicating these are mutually exclusive options</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr2_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VRF ID of second DHCP server</div>
                        <div>If not specified, will use same VRF as the network VRF</div>
                        <div>For ND version 3.1 and NDFC 12.1 dhcp_srvr2_vrf must be specified for dhcp_srvr2_ip</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr3_ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>DHCP relay IP address of the third DHCP server</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>If dhcp_servers and dhcp_srvr3_ip are specified an error message is generated indicating these are mutually exclusive options</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dhcp_srvr3_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VRF ID of third DHCP server</div>
                        <div>If not specified, will use same VRF as the network VRF</div>
                        <div>For ND version 3.1 and NDFC 12.1 dhcp_srvr3_vrf must be specified for dhcp_srvr3_ip</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                        <div>DEPRECATED</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>gw_ip_subnet</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
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
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>gw_ipv6_subnet</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IPv6 Gateway with prefix for the network</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>int_desc</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Description for the interface</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>intfvlan_nf_monitor</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Interface Vlan Netflow Monitor</div>
                        <div>Applicable only if &#x27;Layer 2 Only&#x27; is not enabled. Provide monitor name defined in fabric setting for Layer 3 Record</div>
                        <div>Netflow configs are supported on NDFC only</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>is_l2only</b>
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
                        <div>Layer 2 only network</div>
                        <div>If specified as true, VRF Name(vrf_name) should not be specified or can be specified as &quot;&quot;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>l3gw_on_border</b>
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
                        <div>Enable L3 Gateway on Border</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mtu_l3intf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>MTU for Layer 3 interfaces</div>
                        <div>Configured MTU value should be in range 68-9216</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>multicast_group_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>The multicast IP address for the network</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                <td colspan="3">
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
                        <div>If not specified in the playbook, ND will auto-select an available net_id</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>net_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the network being managed</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>netflow_enable</b>
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
                        <div>Enable Netflow</div>
                        <div>Netflow is supported only if it is enabled on fabric</div>
                        <div>Netflow configs are supported on NDFC only</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>route_target_both</b>
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
                        <div>Enable both L2 VNI Route-Target</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>routing_tag</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">12345</div>
                </td>
                <td>
                        <div>Routing Tag for the network profile</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>secondary_ip_gw1</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address with subnet for secondary gateway 1</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>secondary_ip_gw2</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address with subnet for secondary gateway 2</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>secondary_ip_gw3</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address with subnet for secondary gateway 3</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>secondary_ip_gw4</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address with subnet for secondary gateway 4</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>trm_enable</b>
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
                        <div>Enable Tenant Routed Multicast</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                        <div>VLAN ID for the network.</div>
                        <div>If not specified in the playbook, ND will auto-select an available vlan_id</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vlan_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the vlan configured</div>
                        <div>if &gt; 32 chars enable, system vlan long-name on switch</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vlan_nf_monitor</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Vlan Netflow Monitor</div>
                        <div>Provide monitor name defined in fabric setting for Layer 3 Record</div>
                        <div>Netflow configs are supported on NDFC only</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the VRF to which the network belongs to</div>
                        <div>This field is required for L3 Networks. VRF name should not be specified or may be specified as &quot;&quot; for L2 networks</div>
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
                        <div>Name of the target fabric for network operations</div>
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
                        <div>The state of ND after module completion.</div>
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
    #   Networks defined in the playbook will be merged into the target fabric.
    #     - If the network does not exist it will be added.
    #     - If the network exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Networks that are not specified in the playbook will be untouched.
    #
    # Replaced:
    #   Networks defined in the playbook will be replaced in the target fabric.
    #     - If the Networks does not exist it will be added.
    #     - If the Networks exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Properties that can be managed by the module but are not specified
    #       in the playbook will be deleted or defaulted if possible.
    #     - Networks that are not specified in the playbook will be untouched.
    #
    # Overridden:
    #   Networks defined in the playbook will be overridden in the target fabric.
    #     - If the Networks does not exist it will be added.
    #     - If the Networks exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Properties that can be managed by the module but are not specified
    #       in the playbook will be deleted or defaulted if possible.
    #     - Networks that are not specified in the playbook will be deleted.
    #
    # Deleted:
    #   Networks defined in the playbook will be deleted.
    #   If no Networks are provided in the playbook, all Networks present on that ND fabric will be deleted.
    #
    # Query:
    #   Returns the current ND state for the Networks listed in the playbook.
    #
    # MSD (Multi-Site Domain) Fabric Support:
    # - The module automatically detects fabric type (standalone, multisite_parent, multisite_child) using fabric associations API
    # - For MSD parent fabrics, use child_fabric_config to specify child-specific network parameters
    # - Child fabric configurations inherit deploy setting from parent unless explicitly overridden
    # - Attachments (attach parameter) can only be specified at parent fabric level, not in child_fabric_config
    # - When parent state is 'overridden', child fabrics use 'replaced' state (never 'overridden')
    # - Deploy defaults to true for both parent and child configurations

    # ===========================================================================
    # Standalone Fabric Examples
    # ===========================================================================
    # ---------------------------------------------------------------------------
    # STATE: MERGED - Merge Network Configuration
    # ---------------------------------------------------------------------------

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
              - ip_address: 192.168.1.224
                ports: [Ethernet1/13, Ethernet1/14]
              - ip_address: 192.168.1.225
                ports: [Ethernet1/13, Ethernet1/14]
            deploy: true
          - net_name: ansible-net12
            vrf_name: Tenant-2
            net_id: 7002
            net_template: Default_Network_Universal
            net_extension_template: Default_Network_Extension_Universal
            vlan_id: 151
            gw_ip_subnet: '192.168.40.1/24'
            attach:
              - ip_address: 192.168.1.224
                ports: [Ethernet1/11, Ethernet1/12]
                tor_ports:
                  - ip_address: 192.168.1.120
                    ports: [Ethernet1/14, Ethernet1/15]
              - ip_address: 192.168.1.225
                ports: [Ethernet1/11, Ethernet1/12]
            deploy: false

    # ---------------------------------------------------------------------------
    # STATE: REPLACED - Replace Network Configuration
    # ---------------------------------------------------------------------------

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
            dhcp_servers:
              - srvr_ip: 192.168.1.1
                srvr_vrf: vrf_01
              - srvr_ip: 192.168.2.1
                srvr_vrf: vrf_02
              - srvr_ip: 192.168.3.1
                srvr_vrf: vrf_03
              - srvr_ip: 192.168.4.1
                srvr_vrf: vrf_04
              - srvr_ip: 192.168.5.1
                srvr_vrf: vrf_05
              - srvr_ip: 192.168.6.1
                srvr_vrf: vrf_06
              - srvr_ip: 192.168.7.1
                srvr_vrf: vrf_07
              - srvr_ip: 192.168.8.1
                srvr_vrf: vrf_08
              - srvr_ip: 192.168.9.1
                srvr_vrf: vrf_09
              - srvr_ip: 192.168.10.1
                srvr_vrf: vrf_10
            attach:
              - ip_address: 192.168.1.224
                # Replace the ports with new ports
                # ports: [Ethernet1/13, Ethernet1/14]
                ports: [Ethernet1/16, Ethernet1/17]
            # Delete this attachment
            # - ip_address: 192.168.1.225
            #   ports: [Ethernet1/13, Ethernet1/14]
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
            #     - ip_address: 192.168.1.224
            #       ports: [Ethernet1/11, Ethernet1/12]
            #     - ip_address: 192.168.1.225
            #       ports: [Ethernet1/11, Ethernet1/12]
            #   deploy: false

    # ---------------------------------------------------------------------------
    # STATE: OVERRIDDEN - Override all Networks
    # ---------------------------------------------------------------------------

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
              - ip_address: 192.168.1.224
                # Replace the ports with new ports
                # ports: [Ethernet1/13, Ethernet1/14]
                ports: [Ethernet1/16, Ethernet1/17]
            # Delete this attachment
            # - ip_address: 192.168.1.225
            #   ports: [Ethernet1/13, Ethernet1/14]
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
    #   - ip_address: 192.168.1.224
    #     ports: [Ethernet1/11, Ethernet1/12]
    #   - ip_address: 192.168.1.225
    #     ports: [Ethernet1/11, Ethernet1/12]
    #   deploy: false

    # ---------------------------------------------------------------------------
    # STATE: DELETED - Delete Networks
    # ---------------------------------------------------------------------------

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

    # ---------------------------------------------------------------------------
    # STATE: QUERY - Query Networks
    # ---------------------------------------------------------------------------

    - name: Query Networks
      cisco.dcnm.dcnm_network:
        fabric: vxlan-fabric
        state: query
        config:
          - net_name: ansible-net13
          - net_name: ansible-net12

    # ===========================================================================
    # MSD (Multi-Site Domain) Fabric Examples
    # ===========================================================================

    # Note: The module automatically detects fabric type using fabric associations API.

    # ---------------------------------------------------------------------------
    # STATE: MERGED - Create/Update Networks on Parent and Child Fabrics
    # ---------------------------------------------------------------------------

    - name: MSD MERGE | Create a Network on Parent and extend to Child fabrics
      cisco.dcnm.dcnm_network:
        fabric: vxlan-parent-fabric  # Must be the Parent MSD fabric
        state: merged
        config:
          - net_name: ansible-net-msd-1
            vrf_name: Tenant-1
            net_id: 130001
            vlan_id: 2301
            net_template: Default_Network_Universal
            net_extension_template: Default_Network_Extension_Universal
            gw_ip_subnet: '192.168.12.1/24'
            routing_tag: 1234
            # Attachments are for switches at the Parent fabric
            attach:
              - ip_address: 192.168.10.203
                ports: [Ethernet1/13, Ethernet1/14]
              - ip_address: 192.168.10.204
                ports: [Ethernet1/13, Ethernet1/14]
            # Define how this Network behaves on each Child fabric
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                l3gw_on_border: true
                dhcp_loopback_id: 204
                multicast_group_address: '239.1.1.1'
              - fabric: vxlan-child-fabric2
                l3gw_on_border: false
                dhcp_loopback_id: 205
            deploy: true
          - net_name: ansible-net-msd-2  # A second Network in the same task
            vrf_name: Tenant-2
            net_id: 130002
            vlan_id: 2302
            gw_ip_subnet: '192.168.13.1/24'
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                netflow_enable: false
            # Attachments are for switches at the Parent fabric
            attach:
              - ip_address: 192.168.10.203
                ports: [Ethernet1/15, Ethernet1/16]
              - ip_address: 192.168.10.204
                ports: [Ethernet1/15, Ethernet1/16]

    - name: MSD MERGE | Create Network with advanced DHCP and multicast settings
      cisco.dcnm.dcnm_network:
        fabric: vxlan-parent-fabric
        state: merged
        config:
          - net_name: ansible-net-advanced
            vrf_name: Tenant-1
            net_id: 130010
            vlan_id: 2310
            vlan_name: advanced_network_vlan2310
            gw_ip_subnet: '192.168.20.1/24'
            int_desc: "Advanced Network Configuration"
            mtu_l3intf: 9216
            arp_suppress: true
            route_target_both: true
            # Parent-specific DHCP settings
            dhcp_servers:
              - srvr_ip: 192.168.1.1
                srvr_vrf: management
              - srvr_ip: 192.168.1.2
                srvr_vrf: management
            # Child fabric configuration with different settings per child
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                multicast_group_address: '239.2.1.1'
                dhcp_loopback_id: 210
                dhcp_srvr1_ip: '10.1.1.10'
                dhcp_srvr1_vrf: 'management'
              - fabric: vxlan-child-fabric2
                multicast_group_address: '239.2.2.1'
                l3gw_on_border: true
                deploy: false  # Override parent deploy setting
            attach:
              - ip_address: 192.168.10.203
                ports: [Ethernet1/17, Ethernet1/18]
              - ip_address: 192.168.10.204
                ports: [Ethernet1/17, Ethernet1/18]
            deploy: true  # Parent deploy setting, inherited by children unless overridden

    # ---------------------------------------------------------------------------
    # STATE: REPLACED - Replace Network configuration on Parent and Child Fabrics
    # ---------------------------------------------------------------------------

    - name: MSD REPLACE | Update Network properties on Parent and Child fabrics
      cisco.dcnm.dcnm_network:
        fabric: vxlan-parent-fabric
        state: replaced
        config:
          - net_name: ansible-net-msd-1
            vrf_name: Tenant-1
            net_id: 130001
            net_template: Default_Network_Universal
            net_extension_template: Default_Network_Extension_Universal
            vlan_id: 2301
            gw_ip_subnet: '192.168.12.1/24'
            mtu_l3intf: 9000  # Update MTU on Parent
            # Child fabric configs are replaced: child1 is updated
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                l3gw_on_border: false  # Value is updated
                dhcp_loopback_id: 205  # Value is updated
            attach:
              - ip_address: 192.168.10.203
              # Delete this attachment
              # - ip_address: 192.168.10.204
              # Create the following attachment
              - ip_address: 192.168.10.205
                ports: [Ethernet1/13, Ethernet1/14]
          # Dont touch this if its present on ND
          # - net_name: ansible-net-msd-2
          #   vrf_name: Tenant-2
          #   net_id: 130002
          #   net_template: Default_Network_Universal
          #   net_extension_template: Default_Network_Extension_Universal
          #   attach:
          #   - ip_address: 192.168.10.203
          #     ports: [Ethernet1/15, Ethernet1/16]
          #   - ip_address: 192.168.10.204
          #     ports: [Ethernet1/15, Ethernet1/16]

    - name: MSD REPLACE | Update Network with netflow configuration
      cisco.dcnm.dcnm_network:
        fabric: vxlan-parent-fabric
        state: replaced
        config:
          - net_name: ansible-net-advanced
            vrf_name: Tenant-1
            net_id: 130010
            vlan_id: 2310
            gw_ip_subnet: '192.168.20.1/24'
            # Parent settings
            arp_suppress: false  # Updated value
            # Child fabric configuration updates
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                netflow_enable: true
                vlan_nf_monitor: NETFLOW_MONITOR_2  # Updated monitor
                multicast_group_address: '239.2.1.2'  # Updated address

    # ---------------------------------------------------------------------------
    # STATE: OVERRIDDEN - Override all Networks on Parent and Child Fabrics
    # ---------------------------------------------------------------------------

    - name: MSD OVERRIDE | Override all Networks ensuring only specified ones exist
      cisco.dcnm.dcnm_network:
        fabric: vxlan-parent-fabric
        state: overridden
        config:
          - net_name: ansible-net-production
            vrf_name: Tenant-Production
            net_id: 140001
            vlan_id: 3001
            gw_ip_subnet: '172.16.1.1/24'
            int_desc: "Production Network for critical workloads"
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                l3gw_on_border: true
                netflow_enable: true
              - fabric: vxlan-child-fabric2
                l3gw_on_border: true
                netflow_enable: true
            attach:
              - ip_address: 192.168.10.203
                ports: [Ethernet1/19, Ethernet1/20]
              - ip_address: 192.168.10.204
                ports: [Ethernet1/19, Ethernet1/20]
            deploy: true
          # All other Networks will be deleted from both parent and child fabrics

    # ---------------------------------------------------------------------------
    # STATE: DELETED - Delete Networks from Parent and all Child Fabrics
    # ---------------------------------------------------------------------------

    - name: MSD DELETE | Delete a Network from the Parent and all associated Child fabrics
      cisco.dcnm.dcnm_network:
        fabric: vxlan-parent-fabric
        state: deleted
        config:
          - net_name: ansible-net-msd-1
          # The 'child_fabric_config' parameter is ignored for 'deleted' state.

    - name: MSD DELETE | Delete multiple Networks from Parent and Child fabrics
      cisco.dcnm.dcnm_network:
        fabric: vxlan-parent-fabric
        state: deleted
        config:
          - net_name: ansible-net-msd-1
          - net_name: ansible-net-msd-2
          - net_name: ansible-net-advanced

    - name: MSD DELETE | Delete all Networks from the Parent and all associated Child fabrics
      cisco.dcnm.dcnm_network:
        fabric: vxlan-parent-fabric
        state: deleted

    # ---------------------------------------------------------------------------
    # STATE: QUERY - Query Networks
    # ---------------------------------------------------------------------------

    - name: MSD QUERY | Query specific Networks on the Parent MSD fabric
      cisco.dcnm.dcnm_network:
        fabric: vxlan-parent-fabric
        state: query
        config:
          - net_name: ansible-net-msd-1
          - net_name: ansible-net-msd-2
          # The query will return the Network's configuration on the parent
          # and its attachments on all associated child fabrics.

    - name: MSD QUERY | Query all Networks on the Parent MSD fabric
      cisco.dcnm.dcnm_network:
        fabric: vxlan-parent-fabric
        state: query
        # No config specified - returns all Networks

    - name: MSD QUERY | Query specific Networks on the Child MSD fabric
      cisco.dcnm.dcnm_network:
        fabric: vxlan-child-fabric1
        state: query
        config:
          - net_name: ansible-net-msd-1
          - net_name: ansible-net-msd-2
          # The query will return the Network's configuration on the child
          # and its attachments.

    - name: MSD QUERY | Query all Networks on the Child MSD fabric
      cisco.dcnm.dcnm_network:
        fabric: vxlan-child-fabric1
        state: query
        # No config specified - returns all Networks on the child.

    - name: MSD QUERY | Query specific Networks on Parent & Child fabric
      cisco.dcnm.dcnm_network:
        fabric: vxlan-parent-fabric
        state: query
        config:
          - net_name: ansible-net-msd-1
            child_fabric_config:
              - fabric: vxlan-child-fabric1
          - net_name: ansible-net-msd-2
            child_fabric_config:
              - fabric: vxlan-child-fabric2
          # The query will return the Network's configuration on the parent and the
          # configuration on the specified childs and its attachments at
          # the parent and child level respectively.




Status
------


Authors
~~~~~~~

- Chris Van Heuveln(@chrisvanheuveln), Shrishail Kariyappanavar(@nkshrishail) Praveen Ramoorthy(@praveenramoorthy)
