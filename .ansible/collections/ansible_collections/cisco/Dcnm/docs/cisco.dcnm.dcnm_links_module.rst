.. _cisco.dcnm.dcnm_links_module:


*********************
cisco.dcnm.dcnm_links
*********************

**DCNM ansible module for managing Links.**


Version added: 2.1.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- DCNM ansible module for creating, modifying, deleting and querying Links




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
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>A list of dictionaries containing Links information.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dst_device</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address or DNS name of the destination switch which is part of the link being configured.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dst_fabric</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the destination fabric. If this is same as &#x27;src_fabric&#x27; then the link is considered intra-fabric link. If this parameter is different from &#x27;src_fabric&#x27;, then the link is considered inter-fabric link.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dst_interface</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Interface on the destination device which is part of the link being configured.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>profile</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Additional link related parameters that must be included while creating links.</div>
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
                        <div>Admin state of the link.</div>
                        <div>This parameter is not required if template is &#x27;ext_evpn_multisite_overlay_setup&#x27;, &#x27;ext_multisite_underlay_setup&#x27;, and &#x27;ext_fabric_setup&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>auto_deploy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Flag that controls auto generation of neighbor VRF Lite configuration for managed neighbor devices.</div>
                        <div>This parameter is required only if template is &#x27;ext_fabric_setup&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>bgp_multihop</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">5</div>
                </td>
                <td>
                        <div>eBGP Time-To-Live Value for Remote Peer.</div>
                        <div>This parameter is required only if template is &#x27;ext_evpn_multisite_overlay_setup&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dci_routing_proto</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>is-is</b>&nbsp;&larr;</div></li>
                                    <li>ospf</li>
                        </ul>
                </td>
                <td>
                        <div>Routing protocol used on the DCI MPLS link</div>
                        <div>This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup` and `mpls_fabric` is `SR`</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dci_routing_tag</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"MPLS_UNDERLAY"</div>
                </td>
                <td>
                        <div>Routing Process Tag of DCI Underlay</div>
                        <div>This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup`</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>deploy_dci_tracking</b>
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
                        <div>Flag to enable deploy DCI tracking.</div>
                        <div>This parameter is required only if template is &#x27;ext_multisite_underlay_setup&#x27;.</div>
                        <div>This parameter MUST be included only if the fabrics are part of multisite.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dst_asn</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>BGP ASN number on the destination fabric.</div>
                        <div>Required for below templates</div>
                        <div>ext_fabric_setup</div>
                        <div>ext_multisite_underlay_setup</div>
                        <div>ext_evpn_multisite_overlay_setup</div>
                        <div>ext_vxlan_mpls_overlay_setup</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ebgp_auth_key_type</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>3</li>
                                    <li>7</li>
                        </ul>
                </td>
                <td>
                        <div>BGP Key Encryption Type.</div>
                        <div>This parameter is required only if template is &#x27;ext_multisite_underlay_setup&#x27; or &#x27;ext_evpn_multisite_overlay_setup&#x27;.</div>
                        <div>This parameter is required only if inherit_from_msd is false.</div>
                        <div>Choices are 3 (3DES) or 7 (Cisco)</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ebgp_password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Encrypted eBGP Password Hex String.</div>
                        <div>This parameter is required only if template is &#x27;ext_multisite_underlay_setup&#x27; or &#x27;ext_evpn_multisite_overlay_setup&#x27;.</div>
                        <div>This parameter is required only if inherit_from_msd is false.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ebgp_password_enable</b>
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
                        <div>Flag to enable eBGP password.</div>
                        <div>This parameter is required only if template is &#x27;ext_multisite_underlay_setup&#x27; or &#x27;ext_evpn_multisite_overlay_setup&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>enable_macsec</b>
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
                        <div>Enable MACsec on the link.</div>
                        <div>This parameter is applicable only if MACsec feature is enabled on the fabric.</div>
                        <div>This parameter is applicable only if template is &#x27;int_intra_fabric_ipv6_link_local&#x27; or &#x27;int_intra_fabric_num_link&#x27; or &#x27;int_intra_fabric_unnum_link&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>global_block_range</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"16000-23999"</div>
                </td>
                <td>
                        <div>For Segment Routing binding</div>
                        <div>This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup` and `mpls_fabric` is `SR`</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>inherit_from_msd</b>
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
                        <div>Flag indicating whether to inherit BGP password from MSD information.</div>
                        <div>Applicable only when source and destination fabric are in the same MSD fabric.</div>
                        <div>This parameter is required only if template is &#x27;ext_multisite_underlay_setup&#x27; or &#x27;ext_evpn_multisite_overlay_setup&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>intf_vrf</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Name of the non-default VRF for the link.</div>
                        <div>Make sure to configure the VRF before using it here.</div>
                        <div>This parameter is applicable only if template is &#x27;int_intra_vpc_peer_keep_alive_link&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv4_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IPV4 address of the source interface without mask.</div>
                        <div>This parameter is required only if template is &#x27;ext_evpn_multisite_overlay_setup&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ipv4_subnet</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IPV4 address of the source interface with mask.</div>
                        <div>Required for below templates</div>
                        <div>ext_fabric_setup</div>
                        <div>ext_multisite_underlay_setup</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>max_paths</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">1</div>
                </td>
                <td>
                        <div>Maximum number of iBGP/eBGP paths.</div>
                        <div>This parameter is required only if template is &#x27;ext_multisite_underlay_setup&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>mpls_fabric</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>SR</b>&nbsp;&larr;</div></li>
                                    <li>LDP</li>
                        </ul>
                </td>
                <td>
                        <div>MPLS LDP or Segment-Routing</div>
                        <div>This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup`.</div>
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
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>MTU of the link.</div>
                        <div>This parameter is optional if template is &#x27;ios_xe_int_intra_fabric_num_link&#x27;. The default value in this case will be 1500.</div>
                        <div>This parameter is not required if template is &#x27;ext_evpn_multisite_overlay_setup&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>neighbor_ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IPV4 address of the neighbor switch on the destination fabric.</div>
                        <div>Required for below templates</div>
                        <div>ext_fabric_setup</div>
                        <div>ext_multisite_underlay_setup</div>
                        <div>ext_evpn_multisite_overlay_setup</div>
                        <div>ext_vxlan_mpls_underlay_setup</div>
                        <div>ext_vxlan_mpls_overlay_setup</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ospf_area_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"0.0.0.0"</div>
                </td>
                <td>
                        <div>OSPF Area ID in IP address format</div>
                        <div>This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup` and `dci_routing_proto` is `ospf`</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_bfd_echo_disable</b>
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
                        <div>Enable BFD echo on the source interface. Only applicable if BFD is enabled on the fabric.</div>
                        <div>This parameter is applicable only if template is &#x27;int_intra_fabric_num_link&#x27;.</div>
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
                        <div>Commands to be included in the configuration under the source interface.</div>
                        <div>This parameter is not required if template is  &#x27;ext_evpn_multisite_overlay_setup&#x27;.</div>
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
                        <div>Description of the source interface.</div>
                        <div>This parameter is not required if template is &#x27;ext_evpn_multisite_overlay_setup&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_ipv4_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IPV4 address of the source interface.</div>
                        <div>This parameter is optional if the underlying fabric is ipv6 enabled.</div>
                        <div>This parameter is required only if template is &#x27;int_intra_fabric_num_link&#x27; or &#x27;ios_xe_int_intra_fabric_num_link&#x27; or &#x27;int_intra_vpc_peer_keep_alive_link&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_ipv6_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>IPV6 address of the source interface.</div>
                        <div>This parameter is required only if the underlying fabric is ipv6 enabled.</div>
                        <div>This parameter is required only if template is &#x27;int_intra_fabric_num_link&#x27; or &#x27;ios_xe_int_intra_fabric_num_link&#x27; or &#x27;int_intra_vpc_peer_keep_alive_link&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer1_sr_mpls_index</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"0"</div>
                </td>
                <td>
                        <div>Unique SR SID index for the source border</div>
                        <div>This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup` and `mpls_fabric` is `SR`</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_bfd_echo_disable</b>
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
                        <div>Enable BFD echo on the destination interface. Only applicable if BFD is enabled on the fabric.</div>
                        <div>This parameter is applicable only if template is &#x27;int_intra_fabric_num_link&#x27;.</div>
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
                        <div>Commands to be included in the configuration under the destination interface.</div>
                        <div>This parameter is not required if template is &#x27;ext_evpn_multisite_overlay_setup&#x27;.</div>
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
                        <div>Description of the destination interface.</div>
                        <div>This parameter is not required if template is &#x27;ext_evpn_multisite_overlay_setup&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_ipv4_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IPV4 address of the destination interface.</div>
                        <div>This parameter is optional if the underlying fabric is ipv6 enabled.</div>
                        <div>This parameter is required only if template is &#x27;int_intra_fabric_num_link&#x27; or &#x27;ios_xe_int_intra_fabric_num_link&#x27; or &#x27;int_intra_vpc_peer_keep_alive_link&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_ipv6_address</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>IPV6 address of the destination interface.</div>
                        <div>This parameter is required only if the underlying fabric is ipv6 enabled.</div>
                        <div>This parameter is required only if template is &#x27;int_intra_fabric_num_link&#x27; or &#x27;ios_xe_int_intra_fabric_num_link&#x27; or &#x27;int_intra_vpc_peer_keep_alive_link&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peer2_sr_mpls_index</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"0"</div>
                </td>
                <td>
                        <div>Unique SR SID index for the destination border</div>
                        <div>This parameter is applicable only if template is `ext_vxlan_mpls_underlay_setup` and `mpls_fabric` is `SR`</div>
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
                        <div>Routing tag associated with interface IP.</div>
                        <div>This parameter is required only if template is &#x27;ext_multisite_underlay_setup&#x27;</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>src_asn</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>BGP ASN number on the source fabric.</div>
                        <div>Required for below templates</div>
                        <div>ext_fabric_setup</div>
                        <div>ext_multisite_underlay_setup</div>
                        <div>ext_evpn_multisite_overlay_setup</div>
                        <div>ext_vxlan_mpls_overlay_setup</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>trm_enabled</b>
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
                        <div>Flag to enable Tenant Routed Multicast.</div>
                        <div>This parameter is required only if template is &#x27;ext_evpn_multisite_overlay_setup&#x27;.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>src_device</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address or DNS name of the source switch which is part of the link being configured.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>src_interface</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Interface on the source device which is part of the link being configured.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>template</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>int_intra_fabric_ipv6_link_local(intra-fabric)</li>
                                    <li>int_intra_fabric_num_link (intra-fabric)</li>
                                    <li>int_intra_fabric_unnum_link (intra-fabric)</li>
                                    <li>int_intra_vpc_peer_keep_alive_link (intra-fabric)</li>
                                    <li>int_pre_provision_intra_fabric_link (intra-fabric)</li>
                                    <li>ios_xe_int_intra_fabric_num_link (intra-fabric)</li>
                                    <li>ext_fabric_setup (inter-fabric)</li>
                                    <li>ext_multisite_underlay_setup (inter-fabric)</li>
                                    <li>ext_evpn_multisite_overlay_setup (inter-fabric)</li>
                        </ul>
                </td>
                <td>
                        <div>Name of the template that is applied on the link being configured.</div>
                        <div>The last 3 template choices are applicable for inter-fabric links and the others are applicable for intra-fabric links.</div>
                        <div>This parameter is required only for &#x27;merged&#x27; and &#x27;replaced&#x27; states. It is</div>
                        <div>optional for other states.</div>
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
                        <div>Flag to control deployment of links. If set to &#x27;true&#x27; then the links included will be deployed to specified switches. If set to &#x27;false&#x27;, the links will be created but not deployed.</div>
                        <div>Setting this flag to &#x27;true&#x27; will result in all pending configurations on the source and destination devices to be deployed.</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>src_fabric</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the source fabric for links operations.</div>
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
    #   Links defined in the playbook will be merged into the target fabric.
    #
    #   The links listed in the playbook will be created if not already present on the DCNM
    #   server. If the link is already present and the configuration information included
    #   in the playbook is either different or not present in DCNM, then the corresponding
    #   information is added to the link on DCNM. If a link mentioned in playbook
    #   is already present on DCNM and there is no difference in configuration, no operation
    #   will be performed for such link.
    #
    # Replaced:
    #   Links defined in the playbook will be replaced in the target fabric.
    #
    #   The state of the links listed in the playbook will serve as source of truth for the
    #   same links present on the DCNM under the fabric mentioned. Additions and updations
    #   will be done to bring the DCNM links to the state listed in the playbook.
    #   Note: Replace will only work on the links mentioned in the playbook.
    #
    # Deleted:
    #   Links defined in the playbook will be deleted in the target fabric.
    #
    #   WARNING: Deleting a Link will deploy all pending configurations on the impacted switches
    #
    # Query:
    #   Returns the current DCNM state for the links listed in the playbook. Information included
    #    in the playbook will be used as filters to get the desired output.
    #
    # CREATE LINKS
    #
    # NUMBERED FABRIC
    #
    # INTRA-FABRIC

        - name: Create Links
          cisco.dcnm.dcnm_links:
            state: merged                                            # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_num_fabric"
            config:
              - dst_fabric: "ansible_num_fabric"                     # Destination fabric
                src_interface: "Ethernet1/1"                         # Interface on the Source fabric
                dst_interface: "Ethernet1/1"                         # Interface on the Destination fabric
                src_device: 193.168.1.1                              # Device on the Source fabric
                dst_device: 193.168.1.2                              # Device on the Destination fabric
                template: int_intra_fabric_num_link                  # template to be applied, choose from
                                                                     #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                     #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                     #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

                profile:
                  peer1_ipv4_addr: 192.168.1.1                       # IP address of the Source interface
                  peer2_ipv4_addr: 192.168.1.2                       # IP address of the Destination interface
                  admin_state: true                                  # choose from [true, false]
                  mtu: 9216                                          #
                  peer1_description: "Description of source"         # optional, default is ""
                  peer2_description: "Description of dest"           # optional, default is ""
                  peer1_bfd_echo_disable: false                      # optional, choose from [true, false]
                  peer2_bfd_echo_disable: false                      # optional, choose from [true, false]
                  enable_macsec: false                               # optional, choose from [true, false]
                  peer1_cmds:                                        # Freeform config for source device
                    - no shutdown                                    # optional, default is ""
                  peer2_cmds:                                        # Freeform config for destination device
                    - no shutdown                                    # optional, default is ""

              - dst_fabric: "ansible_num_fabric"                     # Destination fabric
                src_interface: "Ethernet1/2"                         # Interface on the Source fabric
                dst_interface: "Ethernet1/2"                         # Interface on the Destination fabric
                src_device: 193.168.1.1                              # Device on the Source fabric
                dst_device: 193.168.1.2                              # Device on the Destination fabric
                template: int_pre_provision_intra_fabric_link        # template to be applied, choose from
                                                                     #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                     #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                     #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]
              - dst_fabric: "ansible_num_fabric"                     # Destination fabric
                src_interface: "Ethernet1/3"                         # Interface on the Source fabric
                dst_interface: "Ethernet1/3"                         # Interface on the Destination fabric
                src_device: 193.168.1.1                              # Device on the Source fabric
                dst_device: 193.168.1.2                              # Device on the Destination fabric
                template: ios_xe_int_intra_fabric_num_link           # template to be applied, choose from
                                                                     #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                     #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                     #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

                profile:
                  peer1_ipv4_addr: 192.169.2.1                       # IPV4 address of the Source interface
                  peer2_ipv4_addr: 192.169.2.2                       # IPV4 address of the Destination interface
                  peer1_ipv6_addr: fe80:01::01                       # optional, default is ""
                  peer2_ipv6_addr: fe80:01::02                       # optional, default is ""
                  admin_state: true                                  # choose from [true, false]
                  mtu: 1500                                          # optional, default is 1500
                  peer1_description: "Description of source"         # optional, default is ""
                  peer2_description: "Description of dest"           # optional, default is ""
                  peer1_bfd_echo_disable: false                      # optional, choose from [true, false]
                  peer2_bfd_echo_disable: false                      # optional, choose from [true, false]
                  enable_macsec: false                               # optional, choose from [true, false]
                  peer1_cmds:                                        # Freeform config for source device
                    - no shutdown                                    # optional, default is ""
                  peer2_cmds:                                        # Freeform config for destination device
                    - no shutdown                                    # optional, default is ""
    #
    # INTER-FABRIC

        - name: Create Links including optional parameters
          cisco.dcnm.dcnm_links: &links_merge_with_opt
            state: merged                                            # choose from [merged, replaced, deleted, query]
            src_fabric: "{{ ansible_num_fabric }}"
            config:
              - dst_fabric: "{{ ansible_unnum_fabric }}"             # Destination fabric
                src_interface: "{{ intf_1_3 }}"                      # Interface on the Source fabric
                dst_interface: "{{ intf_1_3 }}"                      # Interface on the Destination fabric
                src_device: "{{ ansible_num_switch1 }}"              # Device on the Source fabric
                dst_device: "{{ ansible_unnum_switch1 }}"            # Device on the Destination fabric
                template: ext_fabric_setup                           # template to be applied, choose from
                                                                     #   [ ext_fabric_setup, ext_multisite_underlay_setup,
                                                                     #     ext_evpn_multisite_overlay_setup ]
                profile:
                  ipv4_subnet: 193.168.1.1/24                        # IP address of interface in src fabric with mask
                  neighbor_ip: 193.168.1.2                           # IP address of the interface in dst fabric
                  src_asn: 1000                                      # BGP ASN in source fabric
                  dst_asn: 1001                                      # BGP ASN in destination fabric
                  mtu: 9216                                          #
                  auto_deploy: false                                 # optional, default is false
                                                                     # Flag that controls auto generation of neighbor VRF Lite configuration
                  peer1_description: "Description of source"         # optional, default is ""
                  peer2_description: "Description of dest"           # optional, default is ""
                  peer1_cmds:                                        # Freeform config for source interface
                    - no shutdown                                    # optional, default is ""
                  peer2_cmds:                                        # Freeform config for destination interface
                    - no shutdown                                    # optional, default is ""

              - dst_fabric: "{{ ansible_unnum_fabric }}"             # Destination fabric
                src_interface: "{{ intf_1_4 }}"                      # Interface on the Source fabric
                dst_interface: "{{ intf_1_4 }}"                      # Interface on the Destination fabric
                src_device: "{{ ansible_num_switch1 }}"              # Device on the Source fabric
                dst_device: "{{ ansible_unnum_switch1 }}"            # Device on the Destination fabric
                template: ext_multisite_underlay_setup               # template to be applied, choose from
                                                                     #   [ ext_fabric_setup, ext_multisite_underlay_setup,
                                                                     #     ext_evpn_multisite_overlay_setup ]
                profile:
                  ipv4_subnet: 193.168.2.1/24                        # IP address of interface in src fabric with mask
                  neighbor_ip: 193.168.2.2                           # IP address of the interface in dst fabric
                  src_asn: 1200                                      # BGP ASN in source fabric
                  dst_asn: 1201                                      # BGP ASN in destination fabric
                  mtu: 9216                                          #
                  deploy_dci_tracking: false                         # optional, default is false
                  max_paths: 1                                       # optional, default is 1
                  route_tag: 12345                                   # optional, optional is ""
                  ebgp_password_enable: true                         # optional, default is true
                  ebgp_password: 0102030405                          # optional, required only if ebgp_password_enable flag is true, and inherit_from_msd
                                                                     # is false.
                  inherit_from_msd: True                             # optional, required only if ebgp_password_enable flag is true, default is false
                  ebgp_auth_key_type: 3                              # optional, required only if ebpg_password_enable is true, and inherit_from_msd
                                                                     # is false. Default is 3
                                                                     # choose from [3 - 3DES, 7 - Cisco ]
                  peer1_description: "Description of source"         # optional, default is ""
                  peer2_description: "Description of dest"           # optional, default is ""
                  peer1_cmds:                                        # Freeform config for source interface
                    - no shutdown                                    # optional, default is ""
                  peer2_cmds:                                        # Freeform config for destination interface
                    - no shutdown                                    # optional, default is ""

              - dst_fabric: "{{ ansible_unnum_fabric }}"             # Destination fabric
                src_interface: "{{ intf_1_5 }}"                      # Interface on the Source fabric
                dst_interface: "{{ intf_1_5 }}"                      # Interface on the Destination fabric
                src_device: "{{ ansible_num_switch1 }}"              # Device on the Source fabric
                dst_device: "{{ ansible_unnum_switch1 }}"            # Device on the Destination fabric
                template: ext_evpn_multisite_overlay_setup           # template to be applied, choose from
                                                                     #   [ ext_fabric_setup, ext_multisite_underlay_setup,
                                                                     #     ext_evpn_multisite_overlay_setup ]
                profile:
                  ipv4_addr: 193.168.3.1                             # IP address of interface in src fabric
                  neighbor_ip: 193.168.3.2                           # IP address of the interface in dst fabric
                  src_asn: 1300                                      # BGP ASN in source fabric
                  dst_asn: 1301                                      # BGP ASN in destination fabric
                  trm_enabled: false                                 # optional, default is false
                  bgp_multihop: 5                                    # optional, default is 5
                  ebgp_password_enable: true                         # optional, default is true
                  ebgp_password: 0102030405                          # optional, required only if ebgp_password_enable flag is true, and inherit_from_msd
                                                                     # is false. Default is 3
                  inherit_from_msd: false                            # optional, required only if ebgp_password_enable flag is true, default is false
                  ebpg_auth_key_type: 3                              # optional, required only if ebpg_password_enable is true, and inherit_from_msd
                                                                     # is false. Default is 3
                                                                     # choose from [3 - 3DES, 7 - Cisco ]
              - dst_fabric: "{{ ansible_unnum_fabric }}"             # Destination fabric
                src_interface: "{{ intf_1_5 }}"                      # Interface on the Source fabric
                dst_interface: "{{ intf_1_5 }}"                      # Interface on the Destination fabric
                src_device: "{{ ansible_num_switch1 }}"              # Device on the Source fabric
                dst_device: "{{ ansible_unnum_switch1 }}"            # Device on the Destination fabric
                template: ext_vxlan_mpls_underlay_setup              # Template of MPLS handoff underlay link
                profile:
                  ipv4_subnet: 193.168.3.1/30                        # IP address of interface in src fabric with the mask
                  neighbor_ip: 193.168.3.2                           # IP address of the interface in dst fabric
                  mpls_fabric: LDP                                   # MPLS handoff protocol, choose from [LDP, SR]
                  dci_routing_proto: isis                            # Routing protocol used on the DCI MPLS link, choose from [is-is, ospf]

              - dst_fabric: "{{ ansible_unnum_fabric }}"             # Destination fabric
                src_interface:  Loopback101                          # Loopback interface on the Source fabric
                dst_interface:  Loopback1                            # Loopback interface on the Destination fabric
                src_device: "{{ ansible_num_switch1 }}"              # Device on the Source fabric
                dst_device: "{{ ansible_unnum_switch1 }}"            # Device on the Destination fabric
                template: ext_vxlan_mpls_overlay_setup               #Template of MPLS handoff overlay link
                profile:
                  neighbor_ip: 2.2.2.2 .                             # IP address of the loopback interface of destination device
                  src_asn: 498278384                                 # BGP ASN in source fabric
                  dst_asn: 498278384                                 # BGP ASN in destination fabric



    # FABRIC WITH VPC PAIRED SWITCHES

        - name: Create Links
          cisco.dcnm.dcnm_links:
            state: merged                                            # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_vpc_fabric"
            config:
              - dst_fabric: "ansible_vpc_fabric"                     # Destination fabric
                src_interface: "Ethernet1/4"                         # Interface on the Source fabric
                dst_interface: "Ethernet1/4"                         # Interface on the Destination fabric
                src_device: "ansible_vpc_switch1"                    # Device on the Source fabric
                dst_device: "ansible_vpc_switch2"                    # Device on the Destination fabric
                template: int_intra_vpc_peer_keep_alive_link         # template to be applied, choose from
                                                                     #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                     #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                     #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

                profile:
                  peer1_ipv4_addr: 192.170.1.1                       # IPV4 address of the Source interface
                  peer2_ipv4_addr: 192.170.1.2                       # IPV4 address of the Destination interface
                  peer1_ipv6_addr: fe80:2a::01                       # optional, default is ""
                  peer2_ipv6_addr: fe80:2a::02                       # optional, default is ""
                  admin_state: true                                  # choose from [true, false]
                  mtu: 9216                                          #
                  peer1_description: "Description of source"         # optional, default is ""
                  peer2_description: "Description of dest"           # optional, default is ""
                  enable_macsec: false                               # optional, choose from [true, false]
                  peer1_cmds:                                        # Freeform config for source device
                    - no shutdown                                    # optional, default is ""
                  peer2_cmds:                                        # Freeform config for destination device
                    - no shutdown                                    # optional, default is ""
                  intf_vrf: "test_vrf"                               # optional, default is ""

    # UNNUMBERED FABRIC

        - name: Create Links
          cisco.dcnm.dcnm_links:
            state: merged                                            # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_unnum_fabric"
            config:
              - dst_fabric: "ansible_unnum_fabric"                   # Destination fabric
                src_interface: "Ethernet1/1"                         # Interface on the Source fabric
                dst_interface: "Ethernet1/1"                         # Interface on the Destination fabric
                src_device: "ansible_unnum_switch1"                  # Device on the Source fabric
                dst_device: "ansible_unnum_switch2"                  # Device on the Destination fabric
                template: int_intra_fabric_unnum_link                # template to be applied, choose from
                                                                     #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                     #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                     #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

                profile:
                  admin_state: true                                  # choose from [true, false]
                  mtu: 9216                                          #
                  peer1_description: "Description of source"         # optional, default is ""
                  peer2_description: "Description of dest"           # optional, default is ""
                  enable_macsec: false                               # optional, choose from [true, false]
                  peer1_cmds:                                        # Freeform config for source device
                    - no shutdown                                    # optional, default is ""
                  peer2_cmds:                                        # Freeform config for destination device
                    - no shutdown                                    # optional, default is ""

              - dst_fabric: "ansible_unnum_fabric"                   # Destination fabric
                src_interface: "Ethernet1/2"                         # Interface on the Source fabric
                dst_interface: "Ethernet1/2"                         # Interface on the Destination fabric
                src_device: "ansible_unnum_switch1"                  # Device on the Source fabric
                dst_device: "ansible_unnum_switch2"                  # Device on the Destination fabric
                template: int_pre_provision_intra_fabric_link        # template to be applied, choose from
                                                                     #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                     #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                     #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

    # IPV6 UNDERLAY FABRIC

        - name: Create Links
          cisco.dcnm.dcnm_links:
            state: merged                                            # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_ipv6_fabric"
            config:
              - dst_fabric: "ansible_ipv6_fabric"                    # Destination fabric
                src_interface: "Ethernet1/1"                         # Interface on the Source fabric
                dst_interface: "Ethernet1/1"                         # Interface on the Destination fabric
                src_device: "ansible_ipv6_switch1"                   # Device on the Source fabric
                dst_device: "ansible_ipv6_switch2"                   # Device on the Destination fabric
                template: int_intra_fabric_ipv6_link_local           # template to be applied, choose from
                                                                     #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                     #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                     #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

                profile:
                  peer1_ipv4_addr: 192.169.1.1                       # optional, default is ""
                  peer2_ipv4_addr: 192.169.1.2                       # optional, default is ""
                  peer1_ipv6_addr: fe80:0201::01                     # IP address of the Source interface
                  peer2_ipv6_addr: fe80:0201::02                     # IP address of the Source interface
                  admin_state: true                                  # choose from [true, false]
                  mtu: 9216                                          #
                  peer1_description: "Description of source"         # optional, default is ""
                  peer2_description: "Description of dest"           # optional, default is ""
                  peer1_bfd_echo_disable: false                      # optional, choose from [true, false]
                  peer2_bfd_echo_disable: false                      # optional, choose from [true, false]
                  enable_macsec: false                               # optional, choose from [true, false]
                  peer1_cmds:                                        # Freeform config for source device
                    - no shutdown                                    # optional, default is ""
                  peer2_cmds:                                        # Freeform config for destination device
                    - no shutdown                                    # optional, default is ""

              - dst_fabric: "ansible_ipv6_fabric"                    # Destination fabric
                src_interface: "Ethernet1/2"                         # Interface on the Source fabric
                dst_interface: "Ethernet1/2"                         # Interface on the Destination fabric
                src_device: "ansible_ipv6_switch1"                   # Device on the Source fabric
                dst_device: "ansible_ipv6_switch2"                   # Device on the Destination fabric
                template: int_pre_provision_intra_fabric_link        # template to be applied, choose from
                                                                     #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                     #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                     #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]
              - dst_fabric: "ansible_ipv6_fabric"                    # Destination fabric
                src_interface: "Ethernet1/3"                         # Interface on the Source fabric
                dst_interface: "Ethernet1/3"                         # Interface on the Destination fabric
                src_device: "ansible_ipv6_switch1"                   # Device on the Source fabric
                dst_device: "ansible_ipv6_switch2"                   # Device on the Destination fabric
                template: int_intra_fabric_num_link                  # template to be applied, choose from
                                                                     #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                     #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                     #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]

                profile:
                  peer1_ipv4_addr: 192.169.2.1                       # IPV4 address of the Source interface
                  peer2_ipv4_addr: 192.169.2.2                       # IPV4 address of the Destination interface
                  peer1_ipv6_addr: fe80:0202::01                     # IP address of the Source interface
                  peer2_ipv6_addr: fe80:0202::02                     # IP address of the Source interface
                  admin_state: true                                  # choose from [true, false]
                  mtu: 1500                                          # optional, default is 1500
                  peer1_description: "Description of source"         # optional, default is ""
                  peer2_description: "Description of dest"           # optional, default is ""
                  peer1_bfd_echo_disable: false                      # optional, choose from [true, false]
                  peer2_bfd_echo_disable: false                      # optional, choose from [true, false]
                  enable_macsec: false                               # optional, choose from [true, false]
                  peer1_cmds:                                        # Freeform config for source device
                    - no shutdown                                    # optional, default is ""
                  peer2_cmds:                                        # Freeform config for destination device
                    - no shutdown                                    # optional, default is ""
    # DELETE LINKS

        - name: Delete Links
          cisco.dcnm.dcnm_links:
            state: deleted                                           # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_num_fabric"
            config:
              - dst_fabric: "ansible_num_fabric"                     # Destination fabric
                src_interface: "Ethernet1/1"                         # Interface on the Source fabric
                dst_interface: "Ethernet1/1"                         # Interface on the Destination fabric
                src_device: 193.168.1.1                              # Device on the Source fabric
                dst_device: 193.168.1.2                              # Device on the Destination fabric

    # QUERY LINKS

        - name: Query Links - with Src Fabric
          cisco.dcnm.dcnm_links:
            state: query                                             # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_num_fabric"

        - name: Query Links - with Src & Dst Fabric
          cisco.dcnm.dcnm_links:
            state: query                                             # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_num_fabric"
            config:
              - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric

        - name: Query Links - with Src & Dst Fabric, Src Intf
          cisco.dcnm.dcnm_links:
            state: query                                             # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_num_fabric"
            config:
              - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric
                src_interface: "Ethernet1/1"                         # optional, Interface on the Source fabric

        - name: Query Links - with Src & Dst Fabric, Src & Dst Intf
          cisco.dcnm.dcnm_links:
            state: query                                             # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_num_fabric"
            config:
              - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric
                src_interface: "Ethernet1/1"                         # optional, Interface on the Source fabric
                dst_interface: "Ethernet1/1"                         # optional, Interface on the Destination fabric

        - name: Query Links - with Src & Dst Fabric, Src & Dst Intf, Src Device
          cisco.dcnm.dcnm_links:
            state: query                                             # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_num_fabric"
            config:
              - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric
                src_interface: "Ethernet1/1"                         # optional, Interface on the Source fabric
                dst_interface: "Ethernet1/1"                         # optional, Interface on the Destination fabric
                src_device: 193.168.1.1                              # optional, Device on the Source fabric
          register: result

        - assert:
            that:
              '(result["response"] | length) >= 1'

        - name: Query Links - with Src & Dst Fabric, Src & Dst Intf, Src & Dst Device
          cisco.dcnm.dcnm_links:
            state: query                                             # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_num_fabric"
            config:
              - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric
                src_interface: "Ethernet1/1"                         # optional, Interface on the Source fabric
                dst_interface: "Ethernet1/1"                         # optional, Interface on the Destination fabric
                src_device: 193.168.1.1                              # optional, Device on the Source fabric
                dst_device: 193.168.1.2                              # optional, Device on the Destination fabric
     #
     # INTRA-FABRIC
     #
        - name: Query Links - with Src & Dst Fabric, Src & Dst Intf, Src & Dst Device, Template
          cisco.dcnm.dcnm_links:
            state: query                                             # choose from [merged, replaced, deleted, query]
            src_fabric: "ansible_num_fabric"
            config:
              - dst_fabric: "ansible_num_fabric"                     # optional, Destination fabric
                src_interface: "Ethernet1/1"                         # optional, Interface on the Source fabric
                dst_interface: "Ethernet1/1"                         # optional, Interface on the Destination fabric
                src_device: 193.168.1.1                              # optional, Device on the Source fabric
                dst_device: 193.168.1.2                              # optional, Device on the Destination fabric
                template: int_intra_fabric_num_link                  # optional, template to be applied, choose from
                                                                     #   [ int_intra_fabric_ipv6_link_local, int_intra_fabric_num_link,
                                                                     #     int_intra_fabric_unnum_link, int_intra_vpc_peer_keep_alive_link,
                                                                     #     int_pre_provision_intra_fabric_link, ios_xe_int_intra_fabric_num_link ]
    #
    # INTER-FABRIC
    #
        - name: Query Links - with Src & Dst Fabric, Src & Dst Intf, Src & Dst Device, Template
          cisco.dcnm.dcnm_links:
            state: query                                             # choose from [merged, replaced, deleted, query]
            src_fabric: "{{ ansible_num_fabric }}"
            config:
              - dst_fabric: "{{ ansible_ipv6_fabric }}"              # optional, Destination fabric
                src_interface: "{{ intf_1_6 }}"                      # optional, Interface on the Source fabric
                dst_interface: "{{ intf_1_6 }}"                      # optional, Interface on the Destination fabric
                src_device: "{{ ansible_num_switch1 }}"              # optional, Device on the Source fabric
                dst_device: "{{ ansible_ipv6_switch1 }}"             # optional, Device on the Destination fabric
                template: ext_fabric_setup                           # optional, template to be applied, choose from
                                                                     #   [ ext_fabric_setup, ext_multisite_underlay_setup,
                                                                     #     ext_evpn_multisite_overlay_setup ]




Status
------


Authors
~~~~~~~

- Mallik Mudigonda (@mmudigon)
