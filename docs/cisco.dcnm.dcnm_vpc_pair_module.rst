.. _cisco.dcnm.dcnm_vpc_pair_module:


************************
cisco.dcnm.dcnm_vpc_pair
************************

**DCNM Ansible Module for managing VPC switch pairs required for VPC interfaces.**


Version added: 3.5.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- DCNM Ansible Module for managing VPC switch pairs.




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
                        <div>A list of dictionaries containing VPC switch pair information</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peerOneId</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP Address/Host Name of Peer1 of VPC switch pair.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>peerTwoId</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP Address/Host Name of Peer2 of VPC switch pair.</div>
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
                        <div>A dictionary of additional VPC switch pair related parameters that must be included while creating VPC switch pairs.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ADMIN_STATE</b>
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
                        <div>Flag to enable/disbale administrative state of the interface.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ALLOWED_VLANS</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>none</li>
                                    <li><div style="color: blue"><b>all</b>&nbsp;&larr;</div></li>
                                    <li>vlan-range(e.g., 1-2, 3-40)</li>
                        </ul>
                </td>
                <td>
                        <div>Vlans that are allowed on the VPC peer link port-channel.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>DOMAIN_ID</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>VPC domain ID.</div>
                        <div>Minimum value is 1 and Maximum value is 1000.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>FABRIC_NAME</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the target fabric for VPC switch pair operations.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>KEEP_ALIVE_HOLD_TIMEOUT</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">3</div>
                </td>
                <td>
                        <div>Hold timeout to ignore stale peer keep alive messages.</div>
                        <div>Minimum value is 3 and Maximum value is 10</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>KEEP_ALIVE_VRF</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the VRF used for keep-alive messages.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PC_MODE</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>on</li>
                                    <li><div style="color: blue"><b>active</b>&nbsp;&larr;</div></li>
                                    <li>passive</li>
                        </ul>
                </td>
                <td>
                        <div>Port channel mode.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER1_DOMAIN_CONF</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Additional CLI for PEER1 vPC Domain.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER1_KEEP_ALIVE_LOCAL_IP</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address of a L3 interface in non-default VRF on PEER1.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER1_MEMBER_INTERFACES</b>
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
                        <div>A list of member interfaces for PEER1.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER1_PCID</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">1</div>
                </td>
                <td>
                        <div>PEER1 peerlink port-channel number.</div>
                        <div>Minimum value is 1 and Maximum value is 4096.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER1_PO_CONF</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Additional CLI for PEER1 vPC peerlink port-channel.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER1_PO_DESC</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description for the PEER1 port-channel.</div>
                        <div>Minimum length is 1 and Maximum length is 254.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER2_DOMAIN_CONF</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Additional CLI for PEER2 vPC Domain.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER2_KEEP_ALIVE_LOCAL_IP</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address of a L3 interface in non-default VRF on PEER2.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER2_MEMBER_INTERFACES</b>
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
                        <div>A list of member interfaces for PEER2.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER2_PCID</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">1</div>
                </td>
                <td>
                        <div>PEER2 peerlink port-channel number.</div>
                        <div>Minimum value is 1 and Maximum value is 4096.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER2_PO_CONF</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Additional CLI for PEER2 vPC peerlink port-channel.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>PEER2_PO_DESC</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Description for the PEER2 port-channel.</div>
                        <div>Minimum length is 1 and Maximum length is 254.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>templateName</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the template which inlcudes the required parameters for creating the VPC switch pair.</div>
                        <div>This parameter is &#x27;mandatory&#x27; if the fabric is of type &#x27;LANClassic&#x27; or &#x27;External&#x27;. It is optional otherwise.</div>
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
                        <div>Flag indicating if the configuration must be pushed to the switch.</div>
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
                        <div>Name of the target fabric for VPC switch pair operations</div>
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
                                    <li>fetch</li>
                        </ul>
                </td>
                <td>
                        <div>The required state of the configuration after module completion.</div>
                </td>
            </tr>
            <tr>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>templates</b>
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
                        <div>List of templates to be fetched.</div>
                        <div>This is required only if the &#x27;state&#x27; is &#x27;fetch&#x27;. In this case the list should contain the template names whose details. are to be fetched.</div>
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
    #   VPC switch pairs defined in the playbook will be merged into the target fabric.
    #
    #   The VPC switch pairs listed in the playbook will be created if not already present on the DCNM
    #   server. If the VPC switch pair is already present and the configuration information included
    #   in the playbook is either different or not present in DCNM, then the corresponding
    #   information is added to the DCNM. If a VPC switch pair  mentioned in playbook
    #   is already present on DCNM and there is no difference in configuration, no operation
    #   will be performed for such switch pairs.
    #
    # Replaced:
    #   VPC switch pairs defined in the playbook will be replaced in the target fabric.
    #
    #   The state of the VPC switch pairs listed in the playbook will serve as source of truth for the
    #   same VPC switch pairs present on the DCNM under the fabric mentioned. Additions and updations
    #   will be done to bring the DCNM VPC switch pairs to the state listed in the playbook.
    #   Note: Replace will only work on the VPC switch pairs mentioned in the playbook.
    #
    # Overridden:
    #   VPC switch pairs defined in the playbook will be overridden in the target fabric.
    #
    #   The state of the VPC switch pairs listed in the playbook will serve as source of truth for all
    #   the VPC switch pairs under the fabric mentioned. Additions and deletions will be done to bring
    #   the DCNM VPC switch pairs to the state listed in the playbook. All VPC switch pairs other than the
    #   ones mentioned in the playbook will be deleted.
    #   Note: Override will work on the all the VPC switch pairs present in the DCNM Fabric.
    #
    # Deleted:
    #   VPC switch pairs defined in the playbook will be deleted in the target fabric.
    #
    #   Deletes the list of VPC switch pairs specified in the playbook.  If the playbook does not include
    #   any VPC switch pair information, then all VPC switch pairs from the fabric will be deleted.
    #
    # Query:
    #   Returns the current DCNM state for the VPC switch pairs listed in the playbook.

    # CREATE VPC SWITCH PAIR (LANClassic or External fabrics)

    - name: Merge VPC switch pair paremeters
      cisco.dcnm.dcnm_vpc_pair:
        src_fabric: "test-fabric"
        deploy: true
        state: merged
        config:
          - peerOneId: 192.168.1.1
            peerTwoId: 192.168.1.2
            templateName: "vpc_pair"
            profile:
              ADMIN_STATE: True
              ALLOWED_VLANS: "all"
              DOMAIN_ID: 100
              FABRIC_NAME: test-fabric
              KEEP_ALIVE_HOLD_TIMEOUT: 3
              KEEP_ALIVE_VRF: management
              PC_MODE: active
              PEER1_DOMAIN_CONF: "graceful consistency-check"
              PEER1_KEEP_ALIVE_LOCAL_IP: 192.168.1.1
              PEER1_MEMBER_INTERFACES: e1/21,e1/22-23
              PEER1_PCID: 101
              PEER1_PO_CONF: "buffer-boost"
              PEER1_PO_DESC: "This is peer1 PC"
              PEER2_DOMAIN_CONF: "graceful consistency-check"
              PEER2_KEEP_ALIVE_LOCAL_IP: 192.168.1.2
              PEER2_MEMBER_INTERFACES: e1/21,e1/22-23
              PEER2_PCID: 102
              PEER2_PO_CONF: "buffer-boost"
              PEER2_PO_DESC: "This is peer2 PC"

    # CREATE VPC SWITCH PAIR (VXLAN fabrics)

    - name: Merge VPC switch pair paremeters
      cisco.dcnm.dcnm_vpc_pair:
        src_fabric: "test-fabric"
        deploy: true
        state: merged
        config:
          - peerOneId: 192.168.1.1
            peerTwoId: 192.168.1.2

    # DELETE VPC SWITCH PAIR

    - name: Delete VPC switch pair
      cisco.dcnm.dcnm_vpc_pair:
        src_fabric: "test-fabric"
        deploy: true
        state: deleted
        config:
          - peerOneId: 192.168.1.1
            peerTwoId: 192.168.1.2

    # REPLACE VPC SWITCH PAIR (LANClassic or External fabrics)

    - name: Replace VPC switch pair paremeters
      cisco.dcnm.dcnm_vpc_pair:
        src_fabric: "test-fabric"
        deploy: true
        state: merged
        config:
          - peerOneId: 192.168.1.1
            peerTwoId: 192.168.1.2
            templateName: "vpc_pair"
            profile:
              ADMIN_STATE: True
              ALLOWED_VLANS: "all"
              DOMAIN_ID: 100
              FABRIC_NAME: test-fabric
              KEEP_ALIVE_HOLD_TIMEOUT: 3
              KEEP_ALIVE_VRF: management
              PC_MODE: active
              PEER1_DOMAIN_CONF: "graceful consistency-check"
              PEER1_KEEP_ALIVE_LOCAL_IP: 192.168.1.1
              PEER1_MEMBER_INTERFACES: e1/21,e1/22-23
              PEER1_PCID: 101
              PEER1_PO_CONF: "buffer-boost"
              PEER1_PO_DESC: "This is peer1 PC"
              PEER2_DOMAIN_CONF: "graceful consistency-check"
              PEER2_KEEP_ALIVE_LOCAL_IP: 192.168.1.2
              PEER2_MEMBER_INTERFACES: e1/21,e1/22-23
              PEER2_PCID: 102
              PEER2_PO_CONF: "buffer-boost"
              PEER2_PO_DESC: "This is peer2 PC"

    # OVERRIDDE VPC SWITCH PAIRS

    - name: Override with a new VPC switch pair
      cisco.dcnm.dcnm_vpc_pair:
        src_fabric: "test-fabric"
        deploy: true
        state: overridden
        config:
          - peerOneId: 192.168.1.1
            peerTwoId: 192.168.1.2
            templateName: "vpc_pair"
            profile:
              ADMIN_STATE: True
              ALLOWED_VLANS: "all"
              DOMAIN_ID: 100
              FABRIC_NAME: "test-fabric"
              KEEP_ALIVE_HOLD_TIMEOUT: 3
              KEEP_ALIVE_VRF: management
              PC_MODE: active
              PEER1_KEEP_ALIVE_LOCAL_IP: 192.168.1.1
              PEER1_MEMBER_INTERFACES: e1/20
              PEER1_PCID: 101
              PEER1_PO_DESC: "This is peer1 PC"
              PEER2_KEEP_ALIVE_LOCAL_IP: 192.168.1.2
              PEER2_MEMBER_INTERFACES: e1/20
              PEER2_PCID: 102
              PEER2_PO_DESC: "This is peer2 PC"

    - name: Override without any new switch pairs
      cisco.dcnm.dcnm_vpc_pair:
        src_fabric: "test-fabric"
        deploy: true
        state: overridden

    # QUERY VPC SWITCH PAIRS

    - name: Query VPC switch pairs - with no filters
      cisco.dcnm.dcnm_vpc_pair:
        src_fabric: "test-fabric"
        state: query

    - name: Query VPC switch pairs - with both peers specified
      cisco.dcnm.dcnm_vpc_pair:
        src_fabric: "test-fabric"
        state: query
        config:
          - peerOneId: "{{ ansible_switch1 }}"
            peerTwoId: "{{ ansible_switch2 }}"

    - name: Query VPC switch pairs - with one peer specified
      cisco.dcnm.dcnm_vpc_pair:
        src_fabric: "test-fabric"
        state: query
        config:
          - peerOneId: "{{ ansible_switch1 }}"




Status
------


Authors
~~~~~~~

- Mallik Mudigonda(@mmudigon)
