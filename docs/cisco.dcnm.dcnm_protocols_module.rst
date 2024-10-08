.. _cisco.dcnm.dcnm_protocols_module:


*************************
cisco.dcnm.dcnm_protocols
*************************

**Configure Protocols for security contracts on NDFC fabrics**


Version added: 3.5.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- This module configures Protocols for security contracts on NDFC fabrics.




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
                        <div>A list of dictionaries representing the protocols configuration.</div>
                        <div>Not required for &#x27;query&#x27; and &#x27;deleted&#x27; states.</div>
                </td>
            </tr>
                                <tr>
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
                </td>
                <td>
                        <div>Description of the protocol.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>match</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A list of dictionaries representing the match criteria.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>destination_port_range</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Destination port range.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dscp</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>DSCP value.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>fragments</b>
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
                        <div>Match fragments.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>protocol_options</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Protocol options.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>source_port_range</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>Source port range.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>stateful</b>
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
                        <div>Match stateful connections.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>tcp_flags</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>est</li>
                                    <li>ack</li>
                                    <li>fin</li>
                                    <li>syn</li>
                                    <li>rst</li>
                                    <li>psh</li>
                        </ul>
                        <b>Default:</b><br/><div style="color: blue">""</div>
                </td>
                <td>
                        <div>TCP flags.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
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
                                    <li>ip</li>
                                    <li>ipv4</li>
                                    <li>ipv6</li>
                        </ul>
                </td>
                <td>
                        <div>Type of the protocol.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>match_all</b>
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
                        <div>Match all traffic.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>protocol_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the protocol.</div>
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
                        <div>Name of the target fabric for protocols operations.</div>
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
                                    <li>deleted</li>
                                    <li>replaced</li>
                                    <li>overridden</li>
                                    <li>query</li>
                        </ul>
                </td>
                <td>
                        <div>The required state of the protocols configuration after module completion.</div>
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
    #   Protocols defined in the playbook will be merged into the target fabric.
    #     - If the protocol does not exist it will be added.
    #     - If the protocol exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Protocols that are not specified in the playbook will be untouched.
    #
    # Replaced:
    #   Protocols defined in the playbook will be replaced in the target fabric.
    #     - If the protocol does not exist it will be added.
    #     - If the protocol exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Properties that can be managed by the module but are not specified
    #       in the playbook will be deleted or defaulted if possible.
    #     - Protocols that are not specified in the playbook will be untouched.
    #
    # Overridden:
    #   Protocols defined in the playbook will be overridden in the target fabric.
    #     - If the protocol does not exist it will be added.
    #     - If the protocol exists but properties managed by the playbook are different
    #       they will be updated if possible.
    #     - Properties that can be managed by the module but are not specified
    #       in the playbook will be deleted or defaulted if possible.
    #     - Protocols that are not specified in the playbook will be deleted.
    #
    # Deleted:
    #   Protocols defined in the playbook will be deleted.
    #   If no protocol are provided in the playbook, all protocols present on that DCNM fabric will be deleted.
    #
    # Query:
    #   Returns the current DCNM state for the protocols listed in the playbook.
    #   If no protocols are provided in the playbook, all protocols present on that DCNM fabric will be returned.

    # Merged state - Add a new protocol
    # The following example adds a new protocol to the fabric.
    # If the protocol already exists, the module will update the protocol with the new configuration.

    - name: Add a new protocol
      cisco.dcnm.dcnm_protocols:
        fabric: vxlan-fabric
        state: merged
        config:
          - protocol_name: protocol1
            description: "Protocol 1"
            match_all: false
            match:
              - type: ip
                protocol_options: tcp
                fragments: false
                stateful: false
                source_port_range: "20-30"
                destination_port_range: "50"
                tcp_flags: ""
                dscp: 16

    # Replaced state - Replace an existing protocol
    # The following example replaces an existing protocol protocol1 in the fabric.
    # If the protocol does not exist, the module will create the protocol.

    - name: Replace an existing protocol
      cisco.dcnm.dcnm_protocols:
        fabric: vxlan-fabric
        state: replaced
        config:
          - protocol_name: protocol1
            description: "Protocol 1"
            match_all: false
            match:
              - type: ip
                protocol_options: tcp
                fragments: false
                stateful: false
                source_port_range: "10-40"

    # Overridden state - Override an existing protocol
    # The following example overrides all existing protocol configuration in the fabric.
    # If the protocol does not exist, the module will create the protocol.
    # If the protocol exists, update the protocol with the new configuration.
    # If the protocol exists but is not specified in the playbook, the module will delete the protocol.

    - name: Override all existing protocols
      cisco.dcnm.dcnm_protocols:
        fabric: vxlan-fabric
        state: overridden
        config:
          - protocol_name: protocol1
            description: "Protocol 1"
            match_all: false
            match:
              - type: ip
                protocol_options: udp
                source_port_range: "10-40"

    # Deleted state - Delete a protocol
    # The following example deletes a protocol from the fabric.

    - name: Delete a protocol
      cisco.dcnm.dcnm_protocols:
        fabric: vxlan-fabric
        state: deleted
        config:
          - protocol_name

    # If no protocol are provided in the playbook, all protocols present on that DCNM fabric will be deleted.

    - name: Delete all protocols
      cisco.dcnm.dcnm_protocols:
        fabric: vxlan-fabric
        state: deleted

    # Query state - Query a protocol
    # The following example queries a protocol from the fabric.

    - name: Query a protocol
      cisco.dcnm.dcnm_protocols:
        fabric: vxlan-fabric
        state: query
        config:
          - protocol_name: protocol

    # If no protocol are provided in the playbook, all protocols present on that DCNM fabric will be returned.

    - name: Query all protocols
      cisco.dcnm.dcnm_protocols:
        fabric: vxlan-fabric
        state: query




Status
------


Authors
~~~~~~~

- Praveen Ramoorthy(@praveenramoorthy)
