.. _cisco.dcnm.dcnm_sgrp_module:


********************
cisco.dcnm.dcnm_sgrp
********************

**DCNM Ansible Module for managing Security Groups.**


Version added: 3.5.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- DCNM Ansible Module for managing Security Groups.




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
                        <div>A list of dictionaries containing Security Group information</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>group_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A unique identifier to identify the group. This argument is optional and will be allocated by the module before a payload is pushed to the controller. If this argument is included in the input, then the user provided argument is used.</div>
                        <div>This argument takes a minimum value of 16 and a maximum value of 65535.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>group_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Name of the Security Group.</div>
                        <div>This argument must have a minimum length of 1 and a maximum length of 63.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ip_selectors</b>
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
                        <div>A list of dictionaries containing Security Group IP Selector information.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>ip</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address and mask.</div>
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
                                    <li>Connected Endpoints</li>
                                    <li>External Subnets</li>
                        </ul>
                </td>
                <td>
                        <div>Specifies the type of IP selector.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
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
                        <div>VRF name associated with the IP prefixes.</div>
                        <div>This argument must have a minimum length of 1 and a maximum length of 32.</div>
                </td>
            </tr>

            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>network_selectors</b>
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
                        <div>A list of dictionaries containing Security Group Network Selector information.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>network</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Network name.</div>
                        <div>This argument must have a minimum length of 1 and a maximum length of 32.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
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
                        <div>VRF name.</div>
                        <div>This argument must have a minimum length of 1 and a maximum length of 32.</div>
                </td>
            </tr>


            <tr>
                <td colspan="3">
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
                        <div>Name of the target fabric for Security Group operations</div>
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
    #   Security Groups defined in the playbook will be merged into the target fabric.
    #
    #   The Security Groups listed in the playbook will be created if not already present on the DCNM
    #   server. If the Security Group is already present and the configuration information included
    #   in the playbook is either different or not present in DCNM, then the corresponding
    #   information is added to the DCNM. If a Security Group  mentioned in playbook
    #   is already present on DCNM and there is no difference in configuration, no operation
    #   will be performed for such groups.
    #
    # Replaced:
    #   Security Groups defined in the playbook will be replaced in the target fabric.
    #
    #   The state of the Security Groups listed in the playbook will serve as source of truth for the
    #   same Security Groups present on the DCNM under the fabric mentioned. Additions and updations
    #   will be done to bring the DCNM Security Groups to the state listed in the playbook.
    #   Note: Replace will only work on the Security Groups mentioned in the playbook.
    #
    # Overridden:
    #   Security Groups defined in the playbook will be overridden in the target fabric.
    #
    #   The state of the Security Groups listed in the playbook will serve as source of truth for all
    #   the Security Groups under the fabric mentioned. Additions and deletions will be done to bring
    #   the DCNM Security Groups to the state listed in the playbook. All Security Groups other than the
    #   ones mentioned in the playbook will be deleted.
    #   Note: Override will work on the all the Security Groups present in the DCNM Fabric.
    #
    # Deleted:
    #   Security Groups defined in the playbook will be deleted in the target fabric.
    #
    #   Deletes the list of Security Groups specified in the playbook.  If the playbook does not include
    #   any Security Group information, then all Security Groups from the fabric will be deleted.
    #
    # Query:
    #   Returns the current DCNM state for the Security Groups listed in the playbook.

    # CREATE SECURITY GROUPS

    - name: Create Security Groups
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        deploy: switches                                    # choose from ["none", "switches"]
        state: merged                                       # choose form [merged, replaced, deleted, overridden, query]
        config:
          - group_name: LSG_15001
            group_id: 15001                                 # choose between [min:16, max:65535]
            ip_selectors:
              - type: "Connected Endpoints"
                vrf_name: MyVRF_50001
                ip: 11.1.1.1/24
              - type: "External Subnets"
                vrf_name: MyVRF_50001
                ip: 2001::01/64
              - type: "Connected Endpoints"
                vrf_name: MyVRF_50001
                ip: 11.3.3.1/24
            network_selectors:
              - vrf_name: MyVRF_50001
                network: MyNetwork_30001
            switch:
              - 192.168.1.1
      register: result

    # DELETE SECURITY GROUPS

    - name: Delete all the security groups from the fabric
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        state: deleted                     # choose form [merged, replaced, deleted, overridden, query]
        deploy: switches                   # choose from ["none", "switches"]
      register: result

    - name: Delete security groups by ID
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        state: deleted                     # choose from [merged, replaced, deleted, overridden, query]
        deploy: switches                   # choose from ["none", "switches"]
        config:
          - group_id: 15001
      register: result

    - name: Delete security groups by Name
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        state: deleted                     # choose from [merged, replaced, deleted, overridden, query]
        deploy: switches                   # choose from ["none", "switches"]
        config:
          - group_name: LSG_15001
      register: result

    - name: Delete security groups by Name and ID
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        state: deleted                     # choose from [merged, replaced, deleted, overridden, query]
        deploy: switches                   # choose from ["none", "switches"]
        config:
          - group_name: LSG_15001
            group_id: 15001
      register: result

    # REPLACE SECURITY GROUPS

    - name: Replace Security Groups
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        deploy: switches                                    # choose from ["none", "switches"]
        state: replaced                                     # choose from [merged, replaced, deleted, overridden, query]
        config:
          - group_name: "LSG_15001"
            group_id: 15001                                 # choose between [min:16, max:65535]
            ip_selectors:
              - type: "Connected Endpoints"
                vrf_name: MyVRF_50003
                ip: 21.1.1.1/24
              - type: "Connected Endpoints"
                vrf_name: MyVRF_50003
                ip: 3001::01/64
              - type: "External Subnets"
                vrf_name: MyVRF_50003
                ip: 11.3.3.1/24
            network_selectors:
              - vrf_name: MyVRF_50003
                network: MyNetwork_30003
            switch:
              - 912.168.1.1
      register: result

    # OVERRIDE SECURITY GROUPS

    - name: Override Security Groups - delete all existing groups
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        deploy: switches                                    # choose from ["none", "switches"]
        state: overridden                                   # choose from [merged, replaced, deleted, overridden, query]
      register: result

    - name: Override Security Groups - delete all except the one included
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        deploy: switches                                    # choose from ["none", "switches"]
        state: overridden                                   # choose from [merged, replaced, deleted, overridden, query]
        config:
          - group_name: "LSG_15001"
            group_id: 15001                                 # choose between [min:16, max:65535]
            ip_selectors:
              - type: "Connected Endpoints"
                vrf_name: MyVRF_50001
                ip: 11.1.1.1/24
              - type: "Connected Endpoints"
                vrf_name: MyVRF_50001
                ip: 2001::01/64
              - type: "Connected Endpoints"
                vrf_name: MyVRF_50001
                ip: 11.3.3.1/24
            network_selectors:
              - vrf_name: MyVRF_50001
                network: MyNetwork_30001
            switch:
              - 192.168.1.1
      register: result

    # QUERY SECURITY GROUPS

    - name: Query Security Groups - no filters
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        deploy: none                                        # choose from ["none", "switches"]
        state: query
      register: result

    - name: Query Security Groups - with  IDs
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        config:
          - group_id: 15001                                 # 16 - 65535
          - group_id: 15002                                 # 16 - 65535
          - group_id: 15003
          - group_id: 15004
        deploy: none                                        # choose from ["none", "switches"]
        state: query
      register: result

    - name: Query Security Groups - with names
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        config:
          - group_name: "LSG_15001"
          - group_name: "LSG_15002"
          - group_name: "LSG_15003"
          - group_name: "LSG_15004"
        deploy: none                                        # choose from ["none", "switches"]
        state: query
      register: result

    - name: Q._verbosityuery Security Groups - with names and IDs
      cisco.dcnm.dcnm_sgrp:
        fabric: test-fabric
        config:
          - group_name: "LSG_15001"
            group_id: 15001                                 # 16 - 65535
          - group_name: "LSG_15002"
            group_id: 15002                                 # 16 - 65535
          - group_name: "LSG_15003"
            group_id: 15003                                 # 16 - 65535
          - group_name: "LSG_15004"
            group_id: 15004                                 # 16 - 65535
        deploy: none                                        # choose from ["none", "switches"]
        state: query
      register: result




Status
------


Authors
~~~~~~~

- Mallik Mudigonda(@mmudigon)
