.. _cisco.dcnm.dcnm_vrf_module:


*******************
cisco.dcnm.dcnm_vrf
*******************

**Add and remove VRFs from a DCNM managed VXLAN fabric.**


Version added: 0.9.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Add and remove VRFs and VRF Lite Extension from a DCNM managed VXLAN fabric.
- In Multisite fabrics, VRFs can be created only on Multisite fabric
- In Multisite fabrics, VRFs cannot be created on member fabric




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="5">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="5">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>_fabric_type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>multisite_child</li>
                                    <li>multisite_parent</li>
                                    <li><div style="color: blue"><b>standalone</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>INTERNAL PARAMETER - DO NOT USE</div>
                        <div>Fabric type is determined by the module&#x27;s action plugin</div>
                        <div>This parameter is used internally by the module for multisite fabric processing</div>
                        <div>Valid values are &#x27;multisite_child&#x27;, &#x27;multisite_parent&#x27; and &#x27;standalone&#x27;</div>
                </td>
            </tr>
            <tr>
                <td colspan="5">
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
                        <div>List of details of vrfs being managed. Not required for state deleted</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>adv_default_routes</b>
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
                        <div>Flag to Control Advertisement of Default Route Internally</div>
                        <div>Not applicable at Multisite Parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>adv_host_routes</b>
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
                        <div>Flag to Control Advertisement of /32 and /128 Routes to Edge Routers</div>
                        <div>Not applicable at Multisite Parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
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
                        <div>List of vrf attachment details</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
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
                        <div>Per switch knob to control whether to deploy the attachment</div>
                        <div>This knob has been deprecated from Ansible NDFC Collection Version 2.1.0 onwards. There will not be any functional impact if specified in playbook.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>export_evpn_rt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>export evpn route-target</div>
                        <div>supported on NDFC only</div>
                        <div>Use &#x27;,&#x27; to separate multiple route-targets</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>import_evpn_rt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>import evpn route-target</div>
                        <div>supported on NDFC only</div>
                        <div>Use &#x27;,&#x27; to separate multiple route-targets</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                        <div>IP address of the switch where vrf will be attached or detached</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_lite</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VRF Lite Extensions options</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dot1q</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>DOT1Q Id</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>interface</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Interface of the switch which is connected to the edge router</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
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
                </td>
                <td>
                        <div>IP address of the interface which is connected to the edge router</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
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
                </td>
                <td>
                        <div>IPv6 address of the interface which is connected to the edge router</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>neighbor_ipv4</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Neighbor IP address of the edge router</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>neighbor_ipv6</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Neighbor IPv6 address of the edge router</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VRF Name to which this extension is attached</div>
                </td>
            </tr>



            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>bgp_passwd_encrypt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>3</b>&nbsp;&larr;</div></li>
                                    <li>7</li>
                        </ul>
                </td>
                <td>
                        <div>VRF Lite BGP Key Encryption Type</div>
                        <div>Allowed values are 3 (3DES) and 7 (Cisco)</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>bgp_password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VRF Lite BGP neighbor password</div>
                        <div>Password should be in Hex string format</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
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
                        <div>Configuration for Child fabrics in multisite (MSD) deployments</div>
                        <div>Only applicable for Parent multisite fabrics</div>
                        <div>Defines VRF behavior on each Child fabric</div>
                        <div>If not specified, Child fabrics will default the required properties</div>
                        <div>Not supported with state &#x27;deleted&#x27;</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>adv_default_routes</b>
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
                        <div>Advertise default routes on Child fabric</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>adv_host_routes</b>
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
                        <div>Advertise host routes on Child fabric</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>bgp_passwd_encrypt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>3</b>&nbsp;&larr;</div></li>
                                    <li>7</li>
                        </ul>
                </td>
                <td>
                        <div>BGP password encryption type on Child fabric</div>
                        <div>3 for 3DES encryption, 7 for Cisco encryption</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>bgp_password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>BGP password for Child fabric VRF Lite</div>
                        <div>Password should be in Hex string format</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
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
                                    <li>yes</li>
                        </ul>
                </td>
                <td>
                        <div>Control whether to deploy the specified attachment on Child fabric.</div>
                        <div>If not specified, defaults to value specified at Multisite Parent fabric level.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>export_mvpn_rt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>MVPN routes to export on Child fabric</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Use &#x27;,&#x27; to separate multiple route-targets</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
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
                        <div>Name of the Child fabric</div>
                        <div>Must be a valid Child fabric associated with the Parent</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>import_mvpn_rt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>MVPN routes to import on Child fabric</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Use &#x27;,&#x27; to separate multiple route-targets</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>l3vni_wo_vlan</b>
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
                        <div>Enable L3 VNI without VLAN on Child fabric</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
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
                        <div>Enable netflow on Child fabric</div>
                        <div>Netflow is supported only if it is enabled on fabric</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>nf_monitor</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Netflow monitor on Child fabric</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>no_rp</b>
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
                        <div>No RP, only SSM is used on Child fabric</div>
                        <div>Cannot be used with TRM enabled</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>overlay_mcast_group</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Overlay IPv4 Multicast group on Child fabric</div>
                        <div>Format (224.0.0.0/4 to 239.255.255.255/4)</div>
                        <div>Can be configured only when TRM is enabled</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>rp_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IPv4 Address of RP (Rendezvous Point) on Child fabric</div>
                        <div>Can be configured only when TRM is enabled</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>rp_external</b>
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
                        <div>Specifies if RP is external to the Child fabric</div>
                        <div>Can be configured only when TRM is enabled</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>rp_loopback_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Loopback ID of RP on Child fabric</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Range 0-1023</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>static_default_route</b>
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
                        <div>Configure static default route on Child fabric</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>trm_bgw_msite</b>
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
                        <div>Enable TRM on Border Gateway Multisite for Child fabric</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Required for multicast across sites</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
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
                        <div>Enable TRM (Tenant Routed Multicast) on Child fabric</div>
                        <div>Required for multicast traffic within VRF on Child fabric</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>underlay_mcast_ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Underlay IPv4 Multicast Address on Child fabric</div>
                        <div>Can be configured only when TRM is enabled</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
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
                        <div>Global knob to control whether to deploy the attachment</div>
                        <div>Ansible NDFC Collection Behavior for Version 2.0.1 and earlier</div>
                        <div>This knob will create and deploy the attachment in DCNM only when set to &quot;True&quot; in playbook</div>
                        <div>Ansible NDFC Collection Behavior for Version 2.1.0 and later</div>
                        <div>Attachments specified in the playbook will always be created in DCNM This knob, when set to &quot;True&quot;,  will deploy the attachment in DCNM, by pushing the configs to switch. If set to &quot;False&quot;, the attachments will be created in DCNM, but will not be deployed</div>
                        <div>In case of Multisite fabrics, deploy flag on parent will be inherited by the specified child fabrics, unless overridden at child fabric config level.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>disable_rt_auto</b>
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
                        <div>Disable RT Auto-Generate</div>
                        <div>supported on NDFC only</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>export_evpn_rt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>EVPN routes to export</div>
                        <div>supported on NDFC only</div>
                        <div>Use &#x27;,&#x27; to separate multiple route-targets</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>export_mvpn_rt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>MVPN routes to export</div>
                        <div>supported on NDFC only</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Use &#x27;,&#x27; to separate multiple route-targets</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>export_vpn_rt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VPN routes to export</div>
                        <div>supported on NDFC only</div>
                        <div>Use &#x27;,&#x27; to separate multiple route-targets</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>import_evpn_rt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>EVPN routes to import</div>
                        <div>supported on NDFC only</div>
                        <div>Use &#x27;,&#x27; to separate multiple route-targets</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>import_mvpn_rt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>MVPN routes to import</div>
                        <div>supported on NDFC only</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Use &#x27;,&#x27; to separate multiple route-targets</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>import_vpn_rt</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VPN routes to import</div>
                        <div>supported on NDFC only</div>
                        <div>Use &#x27;,&#x27; to separate multiple route-targets</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv6_linklocal_enable</b>
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
                        <div>Enable IPv6 link-local Option</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>l3vni_wo_vlan</b>
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
                        <div>Enable L3 VNI without VLAN</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>loopback_route_tag</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">12345</div>
                </td>
                <td>
                        <div>Loopback Routing Tag</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>max_bgp_paths</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">1</div>
                </td>
                <td>
                        <div>Max BGP Paths</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>max_ibgp_paths</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">2</div>
                </td>
                <td>
                        <div>Max iBGP Paths</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
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
                        <div>Enable netflow on VRF-LITE Sub-interface</div>
                        <div>Netflow is supported only if it is enabled on fabric</div>
                        <div>Netflow configs are supported on NDFC only</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>nf_monitor</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Netflow Monitor</div>
                        <div>Netflow configs are supported on NDFC only</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>no_rp</b>
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
                        <div>No RP, only SSM is used</div>
                        <div>supported on NDFC only</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>overlay_mcast_group</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Underlay IPv4 Multicast group (224.0.0.0/4 to 239.255.255.255/4)</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>redist_direct_rmap</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"FABRIC-RMAP-REDIST-SUBNET"</div>
                </td>
                <td>
                        <div>Redistribute Direct Route Map</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>rp_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IPv4 Address of RP</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>rp_external</b>
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
                        <div>Specifies if RP is external to the fabric</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>rp_loopback_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>loopback ID of RP</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>service_vrf_template</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"None"</div>
                </td>
                <td>
                        <div>Service vrf template</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>static_default_route</b>
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
                        <div>Flag to Control Static Default Route Configuration</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>trm_bgw_msite</b>
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
                        <div>Enable TRM on Border Gateway Multisite</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
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
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>underlay_mcast_ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Underlay IPv4 Multicast Address</div>
                        <div>Can be configured only when TRM is enabled</div>
                        <div>Not applicable at Multisite parent fabric level</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>v6_redist_direct_rmap</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"FABRIC-RMAP-REDIST-SUBNET"</div>
                </td>
                <td>
                        <div>IPv6 Redistribute Direct Route Map</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
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
                        <div>vlan ID for the vrf attachment</div>
                        <div>If not specified in the playbook, DCNM will auto-select an available vlan_id</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_description</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VRF Description</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_extension_template</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"Default_VRF_Extension_Universal"</div>
                </td>
                <td>
                        <div>Name of the extension config template to be used</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>ID of the vrf being managed</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_int_mtu</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">9216</div>
                </td>
                <td>
                        <div>VRF interface MTU</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_intf_desc</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VRF Intf Description</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the vrf being managed</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_template</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"Default_VRF_Universal"</div>
                </td>
                <td>
                        <div>Name of the config template to be used</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_vlan_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VRF Vlan Name</div>
                        <div>if &gt; 32 chars enable - system vlan long-name</div>
                </td>
            </tr>

            <tr>
                <td colspan="5">
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
                        <div>Name of the target fabric for vrf operations</div>
                </td>
            </tr>
            <tr>
                <td colspan="5">
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

.. code-block:: yaml

    # This module supports the following states:
    #
    # Merged:
    #   VRFs defined in the playbook will be merged into the target fabric.
    #     - If the VRF does not exist it will be added.
    #     - If the VRF exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - VRFs that are not specified in the playbook will be untouched.
    #
    # Replaced:
    #   VRFs defined in the playbook will be replaced in the target fabric.
    #     - If the VRF does not exist it will be added.
    #     - If the VRF exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Properties that can be managed by the module but are  not specified
    #       in the playbook will be deleted or defaulted if possible.
    #     - VRFs that are not specified in the playbook will be untouched.
    #
    # Overridden:
    #   VRFs defined in the playbook will be overridden in the target fabric.
    #     - If the VRF does not exist it will be added.
    #     - If the VRF exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Properties that can be managed by the module but are not specified
    #       in the playbook will be deleted or defaulted if possible.
    #     - VRFs that are not specified in the playbook will be deleted.
    #
    # Deleted:
    #   VRFs defined in the playbook will be deleted.
    #   If no VRFs are provided in the playbook, all VRFs present on that DCNM fabric will be deleted.
    #
    # Query:
    #   Returns the current DCNM state for the VRFs listed in the playbook.
    #
    # rollback functionality:
    # This module supports task level rollback functionality. If any task runs into failures, as part of failure
    # handling, the module tries to bring the state of the DCNM back to the state captured in have structure at the
    # beginning of the task execution. Following few lines provide a logical description of how this works,
    # if (failure)
    #     want data = have data
    #     have data = get state of DCNM
    #     Run the module in override state with above set of data to produce the required set of diffs
    #     and push the diff payloads to DCNM.
    # If rollback fails, the module does not attempt to rollback again, it just quits with appropriate error messages.

    # ===========================================================================
    # Non-MSD/Standalone Fabric Examples
    # ===========================================================================

    - name: MERGE | Create two VRFs on a standalone fabric
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: merged
        config:
          - vrf_name: ansible-vrf-r1
            vrf_id: 9008011
            vrf_template: Default_VRF_Universal
            vrf_extension_template: Default_VRF_Extension_Universal
            vlan_id: 2000
            service_vrf_template: null
            attach:
              - ip_address: 192.168.1.224
              - ip_address: 192.168.1.225
          - vrf_name: ansible-vrf-r2
            vrf_id: 9008012
            vrf_template: Default_VRF_Universal
            vrf_extension_template: Default_VRF_Extension_Universal
            service_vrf_template: null
            attach:
              - ip_address: 192.168.1.224
              - ip_address: 192.168.1.225

    - name: MERGE | Create a VRF with VRF-Lite extensions
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: merged
        config:
          - vrf_name: ansible-vrf-r1
            vrf_id: 9008011
            vrf_template: Default_VRF_Universal
            vrf_extension_template: Default_VRF_Extension_Universal
            vlan_id: 2000
            service_vrf_template: null
            attach:
              - ip_address: 192.168.1.224
              - ip_address: 192.168.1.225
                vrf_lite:
                  - peer_vrf: test_vrf_1 # optional
                    interface: Ethernet1/16 # mandatory
                    ipv4_addr: 10.33.0.2/30 # optional
                    neighbor_ipv4: 10.33.0.1 # optional
                    ipv6_addr: 2010::10:34:0:7/64 # optional
                    neighbor_ipv6: 2010::10:34:0:3 # optional
                    dot1q: 2 # dot1q can be got from dcnm/optional
                  - peer_vrf: test_vrf_2 # optional
                    interface: Ethernet1/17 # mandatory
                    ipv4_addr: 20.33.0.2/30 # optional
                    neighbor_ipv4: 20.33.0.1 # optional
                    ipv6_addr: 3010::10:34:0:7/64 # optional
                    neighbor_ipv6: 3010::10:34:0:3 # optional
                    dot1q: 3 # dot1q can be got from dcnm/optional

    - name: REPLACE | Update attachments for a VRF
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: replaced
        config:
          - vrf_name: ansible-vrf-r1
            vrf_id: 9008011
            vrf_template: Default_VRF_Universal
            vrf_extension_template: Default_VRF_Extension_Universal
            vlan_id: 2000
            service_vrf_template: null
            attach:
              - ip_address: 192.168.1.224
              # Delete this attachment
              # - ip_address: 192.168.1.225
              # Create the following attachment
              - ip_address: 192.168.1.226
          # Dont touch this if its present on DCNM
          # - vrf_name: ansible-vrf-r2
          #   vrf_id: 9008012
          #   vrf_template: Default_VRF_Universal
          #   vrf_extension_template: Default_VRF_Extension_Universal
          #   attach:
          #   - ip_address: 192.168.1.224
          #   - ip_address: 192.168.1.225

    - name: OVERRIDE | Override all VRFs on a fabric
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: overridden
        config:
          - vrf_name: ansible-vrf-r1
            vrf_id: 9008011
            vrf_template: Default_VRF_Universal
            vrf_extension_template: Default_VRF_Extension_Universal
            vlan_id: 2000
            service_vrf_template: null
            attach:
              - ip_address: 192.168.1.224
              # Delete this attachment
              # - ip_address: 192.168.1.225
              # Create the following attachment
              - ip_address: 192.168.1.226
          # Delete this vrf
          # - vrf_name: ansible-vrf-r2
          #   vrf_id: 9008012
          #   vrf_template: Default_VRF_Universal
          #   vrf_extension_template: Default_VRF_Extension_Universal
          #   vlan_id: 2000
          #   service_vrf_template: null
          #   attach:
          #   - ip_address: 192.168.1.224
          #   - ip_address: 192.168.1.225

    - name: DELETE | Delete selected VRFs
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: deleted
        config:
          - vrf_name: ansible-vrf-r1
            vrf_id: 9008011
            vrf_template: Default_VRF_Universal
            vrf_extension_template: Default_VRF_Extension_Universal
            vlan_id: 2000
            service_vrf_template: null
          - vrf_name: ansible-vrf-r2
            vrf_id: 9008012
            vrf_template: Default_VRF_Universal
            vrf_extension_template: Default_VRF_Extension_Universal
            vlan_id: 2000
            service_vrf_template: null

    - name: DELETE | Delete all VRFs on a fabric
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: deleted

    - name: QUERY | Query specific VRFs
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: query
        config:
          - vrf_name: ansible-vrf-r1
          - vrf_name: ansible-vrf-r2

    # ===========================================================================
    # MSD (Multi-Site Domain) Fabric Examples
    # ===========================================================================

    # Note: For fabrics which are "member" (part of an MSD fabric),
    # operations are permitted only through the parent MSD fabric tasks.

    # ---------------------------------------------------------------------------
    # STATE: MERGED - Create/Update VRFs on Parent and Child Fabrics
    # ---------------------------------------------------------------------------

    - name: MSD MERGE | Create a VRF on Parent and extend to Child fabrics
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-parent-fabric # Must be the Parent MSD fabric
        state: merged
        config:
          - vrf_name: ansible-vrf-msd-1
            vrf_id: 9008011
            vlan_id: 2000
            vrf_template: Default_VRF_Universal
            vrf_extension_template: Default_VRF_Extension_Universal
            service_vrf_template: null
            # Attachments are for switches at the Parent fabric
            attach:
              - ip_address: 192.168.1.224
              - ip_address: 192.168.1.225
            # Define how this VRF behaves on each Child fabric
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                adv_default_routes: true
                adv_host_routes: false
              - fabric: vxlan-child-fabric2
                adv_default_routes: false
                adv_host_routes: true
          - vrf_name: ansible-vrf-msd-2 # A second VRF in the same task
            vrf_id: 9008012
            vlan_id: 2001
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                adv_default_routes: false
                adv_host_routes: false
            # Attachments are for switches at the Parent fabric
            attach:
              - ip_address: 192.168.1.224
              - ip_address: 192.168.1.225

    - name: MSD MERGE | Create VRF with L3VNI and advanced routing settings
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-parent-fabric
        state: merged
        config:
          - vrf_name: ansible-vrf-advanced
            vrf_id: 9008020
            vlan_id: 2020
            vrf_int_mtu: 9000
            max_bgp_paths: 4
            max_ibgp_paths: 4
            ipv6_linklocal_enable: true
            # Parent-specific settings
            redist_direct_rmap: CUSTOM-RMAP-REDIST
            v6_redist_direct_rmap: CUSTOM-RMAP-REDIST-V6
            # Child fabric configuration with multicast settings
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                l3vni_wo_vlan: true
                trm_enable: true
                trm_bgw_msite: true
                rp_address: 10.1.1.1
                underlay_mcast_ip: 239.1.1.1
                overlay_mcast_group: 239.2.1.1
              - fabric: vxlan-child-fabric2
                bgp_password: 1234ABCD
                bgp_passwd_encrypt: 7
                netflow_enable: true
                nf_monitor: NETFLOW_MONITOR_1

    # ---------------------------------------------------------------------------
    # STATE: REPLACED - Replace VRF configuration on Parent and Child Fabrics
    # ---------------------------------------------------------------------------

    - name: MSD REPLACE | Update VRF properties on Parent and Child fabrics
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-parent-fabric
        state: replaced
        config:
          - vrf_name: ansible-vrf-msd-1
            vrf_id: 9008011
            vrf_template: Default_VRF_Universal
            vrf_extension_template: Default_VRF_Extension_Universal
            vlan_id: 2000
            vrf_int_mtu: 9000 # Update MTU on Parent
            service_vrf_template: null
            # Child fabric configs are replaced: child1 is updated
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                adv_default_routes: false # Value is updated
                adv_host_routes: true     # Value is updated
            attach:
              - ip_address: 192.168.1.224
              # Delete this attachment
              # - ip_address: 192.168.1.225
              # Create the following attachment
              - ip_address: 192.168.1.226
          # Dont touch this if its present on NDFC
          # - vrf_name: ansible-vrf-r2
          #   vrf_id: 9008012
          #   vrf_template: Default_VRF_Universal
          #   vrf_extension_template: Default_VRF_Extension_Universal
          #   attach:
          #   - ip_address: 192.168.1.224
          #   - ip_address: 192.168.1.225

    - name: MSD REPLACE | Update VRF with route-target configuration
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-parent-fabric
        state: replaced
        config:
          - vrf_name: ansible-vrf-advanced
            vrf_id: 9008020
            vlan_id: 2020
            # Parent route-target settings
            disable_rt_auto: false
            import_vpn_rt: "65000:10001,65000:10002"
            export_vpn_rt: "65000:10001,65000:10002"
            import_evpn_rt: "65000:20001,65000:20002"
            export_evpn_rt: "65000:20001,65000:20002"
            # Child fabric configuration updates
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                trm_enable: true
                import_mvpn_rt: "65000:30001"
                export_mvpn_rt: "65000:30001"

    # ---------------------------------------------------------------------------
    # STATE: OVERRIDDEN - Override all VRFs on Parent and Child Fabrics
    # ---------------------------------------------------------------------------

    - name: MSD OVERRIDE | Override all VRFs ensuring only specified ones exist
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-parent-fabric
        state: overridden
        config:
          - vrf_name: ansible-vrf-production
            vrf_id: 9008050
            vlan_id: 2050
            vrf_description: "Production VRF for critical workloads"
            child_fabric_config:
              - fabric: vxlan-child-fabric1
                adv_default_routes: true
                static_default_route: true
              - fabric: vxlan-child-fabric2
                adv_default_routes: true
                static_default_route: true
            attach:
              - ip_address: 192.168.1.224
              - ip_address: 192.168.1.225
          # All other VRFs will be deleted from both parent and child fabrics

    # ---------------------------------------------------------------------------
    # STATE: DELETED - Delete VRFs from Parent and all Child Fabrics
    # ---------------------------------------------------------------------------

    - name: MSD DELETE | Delete a VRF from the Parent and all associated Child fabrics
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-parent-fabric
        state: deleted
        config:
          - vrf_name: ansible-vrf-msd-1
          # The 'child_fabric_config' parameter is not used or allowed for 'deleted' state.

    - name: MSD DELETE | Delete multiple VRFs from Parent and Child fabrics
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-parent-fabric
        state: deleted
        config:
          - vrf_name: ansible-vrf-msd-1
          - vrf_name: ansible-vrf-msd-2
          - vrf_name: ansible-vrf-advanced

    - name: MSD DELETE | Delete all VRFs from the Parent and all associated Child fabrics
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-parent-fabric
        state: deleted

    # ---------------------------------------------------------------------------
    # STATE: QUERY - Query VRFs
    # ---------------------------------------------------------------------------

    - name: MSD QUERY | Query specific VRFs on the Parent MSD fabric
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-parent-fabric
        state: query
        config:
          - vrf_name: ansible-vrf-msd-1
          - vrf_name: ansible-vrf-msd-2
          # The query will return the VRF's configuration on the parent
          # and its attachments on all associated child fabrics.

    - name: MSD QUERY | Query all VRFs on the Parent MSD fabric
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-parent-fabric
        state: query
        # No config specified - returns all VRFs

    - name: MSD QUERY | Query specific VRFs on the Child MSD fabric
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-child-fabric1
        state: query
        config:
          - vrf_name: ansible-vrf-msd-1
          - vrf_name: ansible-vrf-msd-2
          # The query will return the VRF's configuration on the child
          # and its attachments.

    - name: MSD QUERY | Query all VRFs on the Child MSD fabric
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-child-fabric1
        state: query
        # No config specified - returns all VRFs on the child.

    - name: MSD QUERY | Query specific VRFs on Parent & Child fabric
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-parent-fabric
        state: query
        config:
          - vrf_name: ansible-vrf-msd-1
            child_fabric_config:
              - fabric: vxlan-child-fabric1
          - vrf_name: ansible-vrf-msd-2
            child_fabric_config:
              - fabric: vxlan-child-fabric2
          # The query will return the VRF's configuration on the parent and the
          # configuration on the specified childs and its attachments at
          # the parent and child level respectively.




Status
------


Authors
~~~~~~~

- Shrishail Kariyappanavar(@nkshrishail), Karthik Babu Harichandra Babu (@kharicha), Praveen Ramoorthy(@praveenramoorthy)
