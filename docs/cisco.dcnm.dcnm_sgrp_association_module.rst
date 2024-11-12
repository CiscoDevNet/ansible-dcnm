.. _cisco.dcnm.dcnm_sgrp_association_module:


********************************
cisco.dcnm.dcnm_sgrp_association
********************************

**DCNM Ansible Module for managing Security Groups Associatons.**


Version added: 3.5.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- DCNM Ansible Module for managing Security Groups Associations.




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
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>A list of dictionaries containing Security Group information</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>contract_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Contract name associated with the Security Group Association.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dst_group_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A unique identifier to identify the destination group. This argument is optional and will be allocated by the module before a payload is pushed to the controller. If this argument is included in the input, then the user provided argument is used.</div>
                        <div>This argument takes a minimum value of 16 and a maximum value of 65535.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>dst_group_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the destination Security Group in the association.</div>
                        <div>This argument must have a minimum length of 1 and a maximum length of 63.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>src_group_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A unique identifier to identify the source group. This argument is optional and will be allocated by the module before a payload is pushed to the controller. If this argument is included in the input, then the user provided argument is used.</div>
                        <div>This argument takes a minimum value of 16 and a maximum value of 65535.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>src_group_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the source Security Group in the association.</div>
                        <div>This argument must have a minimum length of 1 and a maximum length of 63.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
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
                        <div>IP address or DNS name of the management interface. All switches mentioned in this list will be deployed with the included configuration.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
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
                        <div>VRF name associated with the Security Group Association.</div>
                        <div>This argument must have a minimum length of 1 and a maximum length of 32.</div>
                </td>
            </tr>

            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>deploy</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>none</li>
                                    <li><div style="color: blue"><b>switches</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>Flag indicating if the configuration must be pushed to the switch.</div>
                        <div>A value of &#x27;none&#x27; will not push the changes to the controller. A value of &#x27;switches&#x27; will perform switch level deploy for the changes made.</div>
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
                        <div>Name of the target fabric for Security Group Association operations</div>
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
    #   Security Group Associations defined in the playbook will be merged into the target fabric.
    #
    #   The Security Group Associations listed in the playbook will be created if not already present on the DCNM
    #   server. If the Security Group Association is already present and the configuration information included
    #   in the playbook is either different or not present in DCNM, then the corresponding
    #   information is added to the DCNM. If a Security Group Asssociation  mentioned in playbook
    #   is already present on DCNM and there is no difference in configuration, no operation
    #   will be performed for such groups.
    #
    # Replaced:
    #   Security Group Associations defined in the playbook will be replaced in the target fabric.
    #
    #   The state of the Security Group Associations listed in the playbook will serve as source of truth for the
    #   same Security Group Associations present on the DCNM under the fabric mentioned. Additions and updations
    #   will be done to bring the DCNM Security Group Associations to the state listed in the playbook.
    #   Note: Replace will only work on the Security Group Associations mentioned in the playbook.
    #
    # Overridden:
    #   Security Group Associations defined in the playbook will be overridden in the target fabric.
    #
    #   The state of the Security Group Associations listed in the playbook will serve as source of truth for all
    #   the Security Group Associations under the fabric mentioned. Additions and deletions will be done to bring
    #   the DCNM Security Group Associations to the state listed in the playbook. All Security Group Associations other than the
    #   ones mentioned in the playbook will be deleted.
    #   Note: Override will work on the all the Security Group Associations present in the DCNM Fabric.
    #
    # Deleted:
    #   Security Group Associations defined in the playbook will be deleted in the target fabric.
    #
    #   Deletes the list of Security Group Associations specified in the playbook.  If the playbook does not include
    #   any Security Group Association information, then all Security Group Associations from the fabric will be deleted.
    #
    # Query:
    #   Returns the current DCNM state for the Security Group Associations listed in the playbook.

    # CREATE SECURITY GROUP ASSOCIATIONS

    - name: Create Security Group Associations - with and without mentioning group IDs
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        deploy: switches                                    # choose from ["none", "switches"]
        state: merged                                       # choose from [merged, replaced, deleted, overridden, query]
        config:
          - src_group_name: "LSG_15001"
            dst_group_name: "LSG_15001"
            src_group_id: 15001                             # Group Id associated with src_group_name
            dst_group_id: 15001                             # Group Id associated with dst_group_name
            vrf_name: "MyVRF_50001"
            contract_name: CONTRACT1
            switch:
              - 192.168.1.1
              - 192.168.1.2

          - src_group_name: "LSG_15002"
            dst_group_name: "LSG_15002"
            vrf_name: "MyVRF_50002"
            contract_name: CONTRACT1
            switch:
              - 192.168.1.1
              - 192.168.1.2

    # DELETE SECURITY GROUP ASSOCIATIONS

    - name: Delete Security Group Associations - without config
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
        deploy: switches                    # choose from ["none", "switches"]

    - name: Delete Security Group Associations - with group name
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
        deploy: switches                    # choose from ["none", "switches"]
        config:
          - src_group_name: "LSG_15001"
            switch:
              - 192.168.1.1

    - name: Delete Security Group Associations - with group Id
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
        deploy: switches                    # choose from ["none", "switches"]
        config:
          - dst_group_id: 15001

    - name: Delete Security Group Associations - with vrf name
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
        deploy: switches                    # choose from ["none", "switches"]
        config:
          - vrf_name: "MyVRF_50003"
            switch:
              - 192.168.1.2

    - name: Delete Security Group Associations - with contract name
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
        deploy: switches                    # choose from ["none", "switches"]
        config:
          - contract_name: "CONTRACT1"

    - name: Delete Security Group Associations - sepcifying all
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        state: deleted                      # choose from [merged, replaced, deleted, overridden, query]
        deploy: switches                    # choose from ["none", "switches"]
        config:
          - src_group_id: 15001
            dst_group_id: 15002
            src_group_name: "LSG_15001"
            dst_group_name: "LSG_15002"
            vrf_name: "MyVRF_50003"
            contract_name: "CONTRACT1"

    # REPLACE SECURITY GROUP ASSOCIATIONS

    - name: Replace Security Group Associations
      cisco.dcnm.dcnm_sgrp_association:
        fabric: "{{ ansible_it_fabric }}"
        deploy: switches                                    # choose from ["none", "switches"]
        state: replaced                                     # choose from [merged, replaced, deleted, overridden, query]
        config:
          - src_group_name: "LSG_15001"
            dst_group_name: "LSG_15001"
            src_group_id: 15001                             # Group Id associated with src_group_name
            dst_group_id: 15001                             # Group Id associated with dst_group_name
            vrf_name: "MyVRF_50001"
            contract_name: ICMP-PERMIT
            switch:
              - 192.168.1.1
              - 192.168.1.2

    # OVERRIDE SECURITY GROUP ASSOCIATIONS

    - name: Override Security Group Association without no config
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        deploy: switches                                    # choose from ["none", "switches"]
        state: overridden                                   # choose from [merged, replaced, deleted, overridden, query]

    - name: Override Security Group Association with config
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        deploy: switches                                    # choose from ["none", "switches"]
        state: overridden                                   # choose from [merged, replaced, deleted, overridden, query]
        config:
          - src_group_name: "LSG_15003"
            dst_group_name: "LSG_15004"
            src_group_id: 15003                             # Group Id associated with src_group_name
            dst_group_id: 15004                             # Group Id associated with dst_group_name
            vrf_name: "MyVRF_50003"
            contract_name: CONTRACT1
            switch:
              - 192.168.1.1
              - 192.168.1.2

    # QUERY SECURITY GROUP ASSOCIATIONS

    - name: Query Security Groups - without filters
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        deploy: none
        state: query

    - name: Query Security Groups - with destination group name
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        deploy: none
        state: query
        config:
          - dst_group_name: "LSG_15002"

    - name: Query Security Groups - with vrf name
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        deploy: none
        state: query
        config:
          - vrf_name: "MyVRF_50003"

    - name: Query Security Groups - with group id
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        deploy: none
        state: query
        config:
          - src_group_id: 15001

    - name: Query Security Groups - with contract name
      cisco.dcnm.dcnm_sgrp_association:
        fabric: Test-Fabric
        deploy: none
        state: query
        config:
          - contract_name: CONTRACT1




Status
------


Authors
~~~~~~~

- Mallik Mudigonda(@mmudigon)
