.. _cisco.dcnm.dcnm_vrf_module:


*******************
cisco.dcnm.dcnm_vrf
*******************

**Send REST API requests to DCNM controller for vrf operations**


Version added: 2.10

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Send REST API requests to DCNM controller for vrf operations - Create, Attach, Deploy and Delete




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
                         / <span style="color: purple">elements=dictionary</span>                         / <span style="color: red">required</span>                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>List of details of vrfs being managed</div>
                                                        </td>
            </tr>
                                                            <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
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
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>source</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                                    </div>
                                    </td>
                                <td>
                                                                                                                                                                    <b>Default:</b><br/><div style="color: blue">"None"</div>
                                    </td>
                                                                <td>
                                            <div>??</div>
                                                        </td>
            </tr>
                                <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>suboptions</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">-</span>
                                                                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                                        </td>
            </tr>
                                <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
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
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>vrf_id</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                                                 / <span style="color: red">required</span>                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>ID of the vrf being managed</div>
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
                                                 / <span style="color: red">required</span>                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>Name of the vrf being managed</div>
                                                        </td>
            </tr>
                                <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
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
                                                                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>fabric</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                 / <span style="color: red">required</span>                    </div>
                                    </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>Name of the target fabric for vrf operations</div>
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
                                            <div>The state of the configuration after module completion. Merged - The state of the objects listed on the playbook will be created on the DCNM for the same objects. Only additions will be made if the playbook object or part of the object is missing on DCNM. If an object or part of the object mentioned on playbook is already present on DCNM, no operation will be performed for such objects or part of the objects. Replaced - The state of the objects listed in the playbook will serve as source of truth for the same objects on the DCNM under the fabric mentioned. Additions and deletions will be done to bring the DCNM objects to the state listed in the playbook. Note - Replace will only work on the objects mentioned in the playbook. Overridden - The state of the objects listed in the playbook will serve as source of truth for all the objects under the fabric mentioned. Additions and deletions will be done to bring the DCNM objects to the state listed in the playbook. Note - Override will work on the all the objects in the playbook and also all the objects on DCNM. Deleted - Deletes the list of objects specified in the playbook, if no objects are provided in the playbook, all the objects present on DCNM will be deleted. Query - Returns the current state on the DCNM for the objects listed in the playbook.
    rollback functionality - This module supports task level rollback functionality. If any task runs into failures, as part of failure handling, the module tries to bring the state of the DCNM back to the state captured in have structure at the beginning of the task execution. Following few lines provide a logical description of how this works, if (failure) want data = have data have data = get state of DCNM Run the module in override state with above set of data to produce the required set of diffs and push the diff payloads to DCNM. If rollback fails, the module does not attempt to rollback again, it just quits with appropriate error messages.</div>
                                                        </td>
            </tr>
                        </table>
    <br/>




Examples
--------

.. code-block:: yaml+jinja

    
    - name: Merge vrfs
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: merged 
        config:
        - vrf_name: ansible-vrf-r1
          vrf_id: 9008011
          vrf_template: Default_VRF_Universal
          vrf_extension_template: Default_VRF_Extension_Universal
          source: None
          service_vrf_template: None
          attach:
          - ip_address: 10.122.197.224
            vlan_id: 202
            deploy: true
          - ip_address: 10.122.197.225
            vlan_id: 203
            deploy: false
        - vrf_name: ansible-vrf-r2
          vrf_id: 9008012
          vrf_template: Default_VRF_Universal
          vrf_extension_template: Default_VRF_Extension_Universal
          source: None
          service_vrf_template: None
          attach:
          - ip_address: 10.122.197.224
            vlan_id: 402
          - ip_address: 10.122.197.225
            vlan_id: 403

    - name: Replace vrfs
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: replaced 
        config:
        - vrf_name: ansible-vrf-r1
          vrf_id: 9008011
          vrf_template: Default_VRF_Universal
          vrf_extension_template: Default_VRF_Extension_Universal
          source: None
          service_vrf_template: None
          attach:
          - ip_address: 10.122.197.224
            vlan_id: 202
            deploy: true
          # Delete this attachment
          # - ip_address: 10.122.197.225
          #   vlan_id: 203
          # deploy: true
          # Create the following attachment
          - ip_address: 10.122.197.226
            vlan_id: 204
            deploy: true
        # Dont touch this if its present on DCNM
        # - vrf_name: ansible-vrf-r2
        #   vrf_id: 9008012
        #   vrf_template: Default_VRF_Universal
        #   vrf_extension_template: Default_VRF_Extension_Universal
        #   source: None
        #   service_vrf_template: None
        #   attach:
        #   - ip_address: 10.122.197.224
        #     vlan_id: 402
        #   - ip_address: 10.122.197.225
        #     vlan_id: 403
                  
    - name: Override vrfs
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: overridden 
        config:
        - vrf_name: ansible-vrf-r1
          vrf_id: 9008011
          vrf_template: Default_VRF_Universal
          vrf_extension_template: Default_VRF_Extension_Universal
          source: None
          service_vrf_template: None
          attach:
          - ip_address: 10.122.197.224
            vlan_id: 202
            deploy: true
          # Delete this attachment
          # - ip_address: 10.122.197.225
          #   vlan_id: 203
          #   deploy: true
          # Create the following attachment
          - ip_address: 10.122.197.226
            vlan_id: 204
            deploy: true
        # Delete this vrf
        # - vrf_name: ansible-vrf-r2
        #   vrf_id: 9008012
        #   vrf_template: Default_VRF_Universal
        #   vrf_extension_template: Default_VRF_Extension_Universal
        #   source: None
        #   service_vrf_template: None
        #   attach:
        #   - ip_address: 10.122.197.224
        #     vlan_id: 402
        #   - ip_address: 10.122.197.225
        #     vlan_id: 403
                  
    - name: Delete selected vrfs
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: deleted 
        config:
        - vrf_name: ansible-vrf-r1
          vrf_id: 9008011
          vrf_template: Default_VRF_Universal
          vrf_extension_template: Default_VRF_Extension_Universal
          source: None
          service_vrf_template: None
        - vrf_name: ansible-vrf-r2
          vrf_id: 9008012
          vrf_template: Default_VRF_Universal
          vrf_extension_template: Default_VRF_Extension_Universal
          source: None
          service_vrf_template: None
              
    - name: Delete all the vrfs
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: deleted
          
    - name: Query vrfs
      cisco.dcnm.dcnm_vrf:
        fabric: vxlan-fabric
        state: query
        config:
        - vrf_name: ansible-vrf-r1
          vrf_id: 9008011
          vrf_template: Default_VRF_Universal
          vrf_extension_template: Default_VRF_Extension_Universal
          source: None
          service_vrf_template: None
        - vrf_name: ansible-vrf-r2
          vrf_id: 9008012
          vrf_template: Default_VRF_Universal
          vrf_extension_template: Default_VRF_Extension_Universal
          source: None
          service_vrf_template: None





Status
------


Authors
~~~~~~~

- Shrishail Kariyappanavar(@nkshrishail)


