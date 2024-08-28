.. _cisco.dcnm.dcnm_policy_module:


**********************
cisco.dcnm.dcnm_policy
**********************

**DCNM Ansible Module for managing policies.**


Version added: 1.1.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- DCNM Ansible Module for Creating, Deleting, Querying and Modifying policies




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
                        <div>A list of dictionaries containing policy and switch information</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>create_additional_policy</b>
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
                        <div>A flag indicating if a policy is to be created even if an identical policy already exists</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
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
                        <div>Description of the policy. The description may include the details regarding the policy i.e. the arguments if any etc.</div>
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
                        <div>This can be one of the following a) Template Name - A unique name identifying the template. Please note that a template name can be used by multiple policies and hence a template name does not identify a policy uniquely. b) Policy ID     - A unique ID identifying a policy. Policy ID MUST be used for modifying policies since template names cannot uniquely identify a policy</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>policy_vars</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">{}</div>
                </td>
                <td>
                        <div>A set of arguments required for creating and deploying policies. The arguments are specific to each policy and depends on the tmeplate that is used by the policy.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="3">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>priority</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"500"</div>
                </td>
                <td>
                        <div>Priority associated with the policy</div>
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
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>A dictionary of switches and associated policy information. All switches in this list will be deployed with only those policies that are included under &quot;policies&quot; object i.e. &#x27;policies&#x27; object will override the list of policies for this particular switch. If &#x27;policies&#x27; object is not included, then other policies specified in the configurstion will be deployed to these switches.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
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
                        <div>IP address of the switch where the policy is to be deployed. This can be IPV4 address, IPV6 address or hostname</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>policies</b>
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
                        <div>A list of policies to be deployed on the switch. Note only policies included here will be deployed on the switch irrespective of other polcies included in the configuration.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>create_additional_policy</b>
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
                        <div>A flag indicating if a policy is to be created even if an identical policy already exists</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
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
                        <div>Description of the policy. The description may include the details regarding the policy</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
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
                        <div>This can be one of the following a) Template Name - A unique name identifying the template. Please note that a template name can be used by multiple policies and hence a template name does not identify a policy uniquely. b) Policy ID     - A unique ID identifying a policy. Policy ID MUST be used for modifying policies since template names cannot uniquely identify a policy</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>policy_vars</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">{}</div>
                </td>
                <td>
                        <div>A set of arguments required for creating and deploying policies. The arguments are specific to each policy and that depends on the tmeplate that is used by the policy.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>priority</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"500"</div>
                </td>
                <td>
                        <div>Priority associated with the policy</div>
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
                        <div>A flag specifying if a policy is to be deployed on the switches</div>
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
                        <div>Name of the target fabric for policy operations</div>
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
                                    <li>deleted</li>
                                    <li>query</li>
                        </ul>
                </td>
                <td>
                        <div>The required state of the configuration after module completion.</div>
                </td>
            </tr>
            <tr>
                <td colspan="4">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>use_desc_as_key</b>
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
                        <div>Flag to enforce using the description parameter as the unique key for policy management.</div>
                        <div>When set to True, the description parameter must be unique and non-empty for each policy in the playbook. The module will also use the description to find the policy to modify or delete. If exsiting policies have the same description, the module will raise an error. If the existing policy with the matching description is using differnet template name, the module will delete the existing policy and create a new one.</div>
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
    #   Policies defined in the playbook will be merged into the target fabric.
    #
    #   The policies listed in the playbook will be created if not already present on the DCNM
    #   server. If the policy is already present and the configuration information included
    #   in the playbook is either different or not present in DCNM, then the corresponding
    #   information is added to the policy on DCNM. If an policy mentioned in playbook
    #   is already present on DCNM and there is no difference in configuration, no operation
    #   will be performed for such policy.
    #
    # Deleted:
    #   Policies defined in the playbook will be deleted in the target fabric.
    #
    #   WARNING: Deleting a policy will deploy all pending configurations on the impacted switches.
    #
    # Query:
    #   Returns the current DCNM state for the policies listed in the playbook.

    # CREATE POLICY

    # NOTE: In the following create task, policies identified by template names template_101,
    #       template_102, and template_103 are deployed on ansible_switch2 where as policies
    #       template_104 and template_105 are the only policies installed on ansible_switch1.

    - name: Create different policies
      cisco.dcnm.dcnm_policy:
        fabric: "{{ ansible_it_fabric }}"
        state: merged
        deploy: true
        config:
          - name: template_101  # This must be a valid template name
            create_additional_policy: false  # Do not create a policy if it already exists
            priority: 101

          - name: template_102  # This must be a valid template name
            create_additional_policy: false  # Do not create a policy if it already exists
            description: 102 - No piority given

          - name: template_103  # This must be a valid template name
            create_additional_policy: false  # Do not create a policy if it already exists
            description: Both description and priority given
            priority: 500

          - switch:
              - ip: "{{ ansible_switch1 }}"
                policies:
                  - name: template_104  # This must be a valid template name
                    create_additional_policy: false  # Do not create a policy if it already exists

                  - name: template_105  # This must be a valid template name
                    create_additional_policy: false  # Do not create a policy if it already exists
              - ip: "{{ ansible_switch2 }}"

    # CREATE POLICY (including arguments)

    # NOTE: The actual arguments to be included depends on the template used to create the policy

    - name: Create policy including required variables
      cisco.dcnm.dcnm_policy:
        fabric: "{{ ansible_it_fabric }}"
        config:
          - name: my_base_ospf               # This must be a valid template name
            create_additional_policy: false  # Do not create a policy if it already exists
            priority: 101
            policy_vars:
              OSPF_TAG: 2000
              LOOPBACK_IP: 10.122.84.108

          - switch:
              - ip: "{{ ansible_switch1 }}"

    # MODIFY POLICY

    # NOTE: Since there can be multiple policies with the same template name, policy-id MUST be used
    #       to modify a particular policy.

    - name: Modify different policies
      cisco.dcnm.dcnm_policy:
        fabric: "{{ ansible_it_fabric }}"
        state: merged
        deploy: true
        config:
          - name: POLICY-101101  # This must be a valid POLICY ID
            create_additional_policy: false  # Do not create a policy if it already exists
            priority: 101

          - name: POLICY-102102  # This must be a valid POLICY ID
            create_additional_policy: false  # Do not create a policy if it already exists
            description: 102 - No piority given

          - name: POLICY-103103  # This must be a valid POLICY ID
            create_additional_policy: false  # Do not create a policy if it already exists
            description: Both description and priority given
            priority: 500

          - switch:
              - ip: "{{ ansible_switch1 }}"
                policies:
                  - name: POLICY-104104  # This must be a valid POLICY ID
                    create_additional_policy: false  # Do not create a policy if it already exists

                  - name: POLICY-105105  # This must be a valid POLICY ID
                    create_additional_policy: false  # Do not create a policy if it already exists
              - ip: "{{ ansible_switch2 }}"

    # DELETE POLICY

    # NOTE: In the case of deleting policies using template names, all policies using the template name
    #       will be deleted. To delete specific policy, policy-ids must be used

    - name: Delete policies using template name
      cisco.dcnm.dcnm_policy:
        fabric: "{{ ansible_it_fabric }}"
        state: deleted          # only choose form [merged, deleted, query]
        config:
          - name: template_101  # name is mandatory
          - name: template_102  # name is mandatory
          - name: template_103  # name is mandatory
          - name: template_104  # name is mandatory
          - name: template_105  # name is mandatory
          - switch:
              - ip: "{{ ansible_switch1 }}"
              - ip: "{{ ansible_switch2 }}"

    - name: Delete policies using policy-id
      cisco.dcnm.dcnm_policy:
        fabric: "{{ ansible_it_fabric }}"
        state: deleted          # only choose form [merged, deleted, query]
        config:
          - name: POLICY-101101  # name is mandatory
          - name: POLICY-102102  # name is mandatory
          - name: POLICY-103103  # name is mandatory
          - name: POLICY-104104  # name is mandatory
          - name: POLICY-105105  # name is mandatory
          - switch:
              - ip: "{{ ansible_switch1 }}"
              - ip: "{{ ansible_switch2 }}"

    # QUERY

    # NOTE: In the case of Query using template names, all policies that have a matching template name will be
    #       returned

    - name: Query all policies from the specified switches
      cisco.dcnm.dcnm_policy:
        fabric: "{{ ansible_it_fabric }}"
        state: query
        config:
          - switch:
              - ip: "{{ ansible_switch1 }}"
              - ip: "{{ ansible_switch2 }}"

    - name: Query policies matching template names
      cisco.dcnm.dcnm_policy:
        fabric: "{{ ansible_it_fabric }}"
        state: query
        config:
          - name: template_101
          - name: template_102
          - name: template_103
          - switch:
              - ip: "{{ ansible_switch1 }}"

    - name: Query policies using policy-ids
      cisco.dcnm.dcnm_policy:
        fabric: "{{ ansible_it_fabric }}"
        state: query
        config:
          - name: POLICY-101101
          - name: POLICY-102102
          - name: POLICY-103103
          - switch:
              - ip: "{{ ansible_switch1 }}"

    # Use the description as key

    # NOTE: As the description of the policy in NDFC/DCNM is not unique,
    #       the user must make sure no policies with the same description are created on NDFC out of the playbook.
    #       If the description is not unique, the module will raise an error.

    ## Below task will create policies with description "policy_radius" on swtich1, switch2 and switch3,
    ## and only create policy "feature bfd" and "feature bash-shell" on the switch1 only

    - name: Create policies
      cisco.dcnm.dcnm_policy:
        fabric: fabric_prod
        use_desc_as_key: true
        config:
          - name: switch_freeform
            create_additional_policy: false
            description: policy_radius
            policy_vars:
              CONF: |
                radius-server host 10.1.1.2 key 7 "ljw3976!" authentication accounting
          - switch:
              - ip: "{{ switch1 }}"
                policies:
                  - name: switch_freeform
                    create_additional_policy: false
                    priority: 101
                    description: feature bfd
                    policy_vars:
                      CONF: |
                        feature bfd
                  - name: switch_freeform
                    create_additional_policy: false
                    priority: 102
                    description: feature bash-shell
                    policy_vars:
                      CONF: |
                        feature bash-shell
              - ip: "{{ switch2 }}"
              - ip: "{{ switch3 }}"




Status
------


Authors
~~~~~~~

- Mallik Mudigonda(@mmudigon)
