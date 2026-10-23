#!/usr/bin/python
#
# Copyright (c) 2020-2023 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Mallik Mudigonda, Mike Wiebe"

DOCUMENTATION = """
---
module: dcnm_interface
short_description: DCNM Ansible Module for managing interfaces.
version_added: "0.9.0"
description:
    - "DCNM Ansible Module for the following interface service operations"
    - "Create, Delete, Modify PortChannel, VPC, Loopback and Sub-Interfaces"
    - "Modify Ethernet Interfaces"
author: Mallik Mudigonda(@mmudigon)
options:
  check_deploy:
    description:
    - Deploy operations may take considerable time in certain cases based on the configuration included
      in the playbook. A success response from DCNM server does not guarantee the completion of deploy
      operation. This flag if set indicates that the module should verify if the configured state is in
      sync with what is requested in playbook. If not set the module will return without verifying the
      state.
    type: bool
    required: false
    default: false
  fabric:
    description:
    - Name of the target fabric for interface operations
    type: str
    required: true
  state:
    description:
    - The required state of the configuration after module completion.
    type: str
    choices: ['merged', 'replaced', 'overridden', 'deleted', 'query']
    default: merged
  deploy:
    description:
    - Flag indicating if the configuration must be pushed to the switch. This flag is used to decide the deploy behavior in
      'deleted' and 'overridden' states as mentioned below
    - In 'overridden' state this flag will be used to deploy deleted interfaces.
    - In 'deleted' state this flag will be used to deploy deleted interfaces when a specific 'config' block is not
      included.
    - The 'deploy' flags included with individual interface configuration elements under the 'config' block will take precedence
       over this global flag.
    type: bool
    default: true
  override_intf_types:
    description:
    - A list of interface types which will be deleted/defaulted in overridden/deleted state. If this list is empty, then during
      overridden/deleted state, all interface types will be defaulted/deleted. If this list includes specific interface types,
      then only those interface types that are included in the list will be deleted/defaulted.
    type: list
    required: false
    elements: str
    choices: ["pc", "vpc", "sub_int", "lo", "eth", "svi", "st_fex", "aa_fex", "breakout"]
    default: []
  patch_version:
    description:
    - Declares the installed Nexus Dashboard/NDFC patch context so the module can trust the
      installed interface templates to carry the registered profile fields the generic
      binding registry manages (for example C(acl_filter), C(flowcontrol_receive),
      C(ospf_cost), C(disable_lldp_transmit)/C(disable_lldp_receive) and the other registered
      fields documented per interface profile).
    - This is a capability declaration the caller makes; it is never sent to the controller,
      never part of the interface payload, and never part of the computed diff.
    - The same declaration selects the nvPair names of two native SVI fields of C(int_vlan), because the
      installed parent template names them differently in its two bodies - with a supported value
      C(dhcp_server_addr4) and C(dhcp_relay_src_intf) use C(dhcpServerAddress4) and
      C(dhcpRelaySourceInterface) (the body served with the activated SMU C(4.3.1.0175006017)); without it
      they keep C(dhcpServerAddr4) and C(DHCP_RELAY_SRC_INTF). These two fields stay native (an absent
      value does not reject them), only one family is ever sent, and the controller is not probed. A
      controller that serves the SMU body must be paired with this declaration (NOT LIVE TESTED; C(4.4.1)
      or later is an assumption of the shared selector, not an observation). When an SVI's stored values
      carry the other body's names, setting, clearing or (replaced/overridden) resetting these fields is
      refused before any change is sent.
    - Accepts the exact SMU string C(4.3.1.0175006017) or a numeric Nexus Dashboard
      release C(4.4.1) or later, matching the version policy of C(dcnm_network).
      ND release strings require at least three dot-separated numeric components;
      additional build components must also be numeric. The first three components are
      compared numerically. No whitespace or suffixes are accepted. For example,
      C(4.4.1.10) and C(4.10.0) are supported, while C(4.4.0), C(4.4),
      C(4.4.1-rc1) and adjacent unapproved C(4.3.1) SMU builds are rejected.
    - The only SMU build this module supports is C(4.3.1.0175006017). The earlier C(4.3.1.0175006011) is not
      accepted, because its interface templates declare different OSPF nvPair names.
    - On loopbacks and subinterfaces, C(ospf_bfd_mode) (C(no_change), C(enable), C(disable)) and, on subinterfaces,
      C(ospf_passive_mode) (C(no_change), C(passive), C(no_passive)) carry the OSPF BFD and passive settings, as on
      routed interfaces and SVIs. The earlier boolean inputs C(ospf_bfd) and C(ospf_passive_interface) are still accepted as
      aliases - C(true) means C(enable) or C(passive); C(false) keeps its old meaning of no local override and therefore
      means C(no_change), never the explicit C(disable) or C(no_passive). Give the mode key to request an explicit
      negative setting. Giving both spellings is accepted only when they mean the same, and the alias is refused on a
      parent that does not register it.
    - Fields that only the C(4.3.1.0175006017) templates declare (NOT LIVE TESTED; read from the installed template
      bodies). On a routed Ethernet - C(enable_cdp) (bool; CDP stays on unless false, which renders C(no cdp enable)),
      C(enable_evpn_multisite_dci_tracking) (bool; renders C(evpn multisite dci-tracking); the template does not check
      the switch role, so whether NX-OS accepts it outside a multisite border gateway is not established) and
      C(ospf_retransmit_interval) (1-65535; requires C(enable_ospf); C(5) is the NX-OS default and renders nothing).
      On an access Ethernet - C(logging_event_port_link_status) (bool; renders C(logging event port link-status)).
      On a subinterface - C(enable_pim_bfd_instance) (bool; renders C(ip pim bfd-instance), independent of
      C(enable_pim_sparse)). Under C(replaced) and C(overridden) an omitted value is reset to the template default
      (C(enable_cdp) true, the other booleans false, the interval cleared); under C(merged) it is preserved. A leaf
      reset of an access Ethernet with C(logging_event_port_link_status) true goes to C(int_trunk_host) in the usual
      single request; C(int_trunk_host) does not declare the field, and the controller removes the line with the
      policy change (measured on NDFC 12.6.0.267 with the C(4.3.1.0175006017) templates). C(enable_cdp) keeps its
      native behaviour on the access, trunk, dot1q-tunnel, PVLAN, port-channel and vPC profiles.
    - This is a SECOND, independent requirement on top of each registered field's existing
      minimum NDFC version. Meeting the per-field NDFC floor does not substitute for a
      supported patch/ND release, and that release does not bypass a field's NDFC floor or its
      C(smu_unsupported) exclusion when one exists; both conditions must hold together
      before a registered field is configurable.
    - There is no enabling default anywhere in the module. When this is omitted, null,
      empty, malformed, or unsupported, the module rejects the ENTIRE invocation
      before any configuration or deployment request is sent, as soon as any config entry
      sets a registered field explicitly -- including a native/legacy-only entry earlier in
      the same task list, per the normal invocation-wide preflight this module already
      applies to its other validation failures.
    - When a registered field is merely OMITTED (not set) while this capability is
      disabled, the module does not reset, clear, or otherwise change that field. For an
      interface RETAINED under C(replaced) or C(overridden) (same parent, same identity,
      not newly created and not explicitly removed), its existing controller value is
      carried forward unchanged in the full replacement payload, exactly as it would be if
      the field were not part of this registry at all. This preservation scope is
      specifically the retained-same-parent carry-forward; it does not change whole-object
      deletion (C(state=deleted) or an explicit removal under C(overridden)) or an
      interface's transition to a different parent template, both of which keep their
      existing, independent contracts.
    - With this capability enabled, resetting a physical Ethernet port to its role default
      (a port named under C(state=deleted), or a port C(overridden) leaves out) also sends, for
      each registered field the port still holds, that field's verified reset value on the
      default parent template. The module verifies the request it sends, not that the
      controller or the switch removes the configuration. A field without a verified reset, a
      controller value that cannot be classified, or a field the port's current policy holds but
      the default parent cannot withdraw (the reset changes the policy) refuses the ENTIRE
      invocation before any request is sent, naming the interface and the field, never its
      value; such a field needs a separate, verified clean-up. A port that is not reset (still
      configured, or skipped by scope) is not affected, and a former port-channel member reset
      after its port-channel is deleted is not covered. With the capability disabled these
      fields are left unchanged, as before.
    - Some registered fields depend on another option of the same interface on
      int_routed_host, int_subif, int_vlan and int_loopback - the OSPF options, process tag and
      authentication fields on C(enable_ospf), the message-digest key and key ID on
      C(enable_ospf_auth), the simple-key encryption type on C(ospf_authentication_key). While
      that option is disabled they configure nothing. Disabling it sends the neutral value of
      each dependent option, keeps a stored process tag or encryption type as inert stored
      data, and clears a stored message-digest key. In C(merged), an explicit C(enable_ospf)
      or C(enable_ospf_auth) false does the same for the stored dependents; omitting it
      preserves them as usual. Before any request, the module refuses an explicit non-neutral
      OSPF option while OSPF ends disabled, an explicit empty C(ospf_tag) or C(ospf_auth_key)
      while its option is enabled, and enabling message-digest authentication over a cleared
      key without a new key. A port reset while such an option is still enabled is refused and
      names the option to disable first. On int_loopback in the default VRF (C(int_vrf) default)
      the template keeps the loopback in the fabric underlay OSPF process whatever C(enable_ospf)
      says, with the stored process tag first, so the tag and the OSPF options stay live there.
      A disable in that VRF must state C(ospf_tag) and does not remove the OSPF line, and an
      explicit C(merged) disable keeps the options. The authentication rules apply in every VRF.
    - Registered string fields whose letter case is part of the value (authentication keys and
      ACL, prefix-list or MACsec key-chain and policy names) are compared case-sensitively, so
      a change of case alone is sent. IPv6 text, numeric fields, booleans and enumerations keep
      their case-insensitive comparison, and so do process tags, whose case semantics are not
      established.
    - "Existing playbooks that already set a registered field (see the list above) must add
      this argument -- directly on the task, or once via C(module_defaults) for
      C(cisco.dcnm.dcnm_interface) -- to keep working under this module version. A playbook
      that only uses native/legacy fields needs no change."
    - The module performs no automatic patch discovery and applies no environment-based
      fallback; the caller is the sole source of this value.
    type: str
    required: false
  config:
    description:
    - A dictionary of interface operations
    type: list
    elements: dict
    default: []
    suboptions:
      name:
        description:
        - Name of the interface. Example, po55, eth2/1, lo100, vpc25, eth1/1.1.
        type: str
        required: true
      switch:
        description:
        - IP address or DNS name of the management interface. All switches mentioned in this list
          will be deployed with the included configuration. For vPC interfaces
          this list object will contain elements each of which is a list of
          pair of switches
        type: list
        elements: str
        required: true
      type:
        description:
        - Interface type. Example, pc, vpc, sub_int, lo, eth, svi
        type: str
        required: true
        choices: ['pc', 'vpc', 'sub_int', 'lo', 'eth', 'svi', 'st-fex', 'aa-fex', 'breakout']
      deploy:
        description:
        - Flag indicating if the configuration must be pushed to the switch. If not included
          it is considered true by default
        type: bool
        default: true
      profile_pc:
        description:
        - Though the key shown here is 'profile_pc' the actual key to be used in playbook
          is 'profile'. The key 'profile_pc' is used here to logically segregate the interface objects applicable for this profile
        - Object profile which must be included for port channel interface configurations.
        suboptions:
          mode:
            description:
            - Interface mode
            - Mode 'pvlan' selects the NDFC 12 policy 'int_port_channel_pvlan_host' for a regular
              port-channel with one or more explicit physical members. Supported - creation in
              the four PVLAN modes, update of the PVLAN lists ('merged' adds to the current list,
              'replaced' states the complete model) and of 'pc_mode', 'description', 'admin_state',
              'native_vlan' and 'allowed_vlans' without changing 'pvlan_mode', a change of the member
              list, the identical repetition and 'overridden' (a kept port-channel follows 'replaced'; a
              PVLAN port-channel of the sweep's scope that the request no longer wants is deleted through
              the same path and contract as 'state=deleted'; switch scope and override_intf_types are those
              of the generic sweep; MEASURED for host mode on NDFC 12.6.0.267, NOT LIVE TESTED for the other
              modes). Refused before any change is sent - ranges, vPC, a
              'pvlan_mode' change, and removing secondaries from a 'promiscuous' mapping
              that keeps others (protection kept from the measured Ethernet defect). Fields for this mode are 'pvlan_mode', 'pvlan_association' (host,
              trunk secondary), 'pvlan_mapping' (promiscuous, trunk promiscuous), 'native_vlan' and
              'allowed_vlans' (trunk modes), 'members', 'pc_mode', 'description' and 'admin_state'.
              The members are managed by the parent and follow the regular port-channel rule - 'merged'
              adds the listed members to the current ones ('members' may be omitted, and a subset never
              removes a member); 'replaced' states the exact member list, which must be listed
              explicitly (an omitted or empty list is refused, an empty member list is not supported).
              An added member must qualify as for a creation. A member qualifies when it is a free port
              on the base its mode admits (C(int_trunk_host) for host, promiscuous and trunk promiscuous;
              a prepared access or routed port for trunk secondary) with no freeform commands and an
              explicit administrative state (ADMIN_STATE true or false). An administratively up member
              joins and stays up and a down member stays down, each member keeping its own state whatever
              the port-channel's 'admin_state' (MEASURED for host, parent down and up, on NDFC 12.6.0.267 /
              NX-OS 10.5(5); NOT LIVE TESTED for promiscuous, trunk promiscuous and trunk secondary, which
              share the same template inheritance). A missing or unknown state is refused, and the module
              never changes a member's state. Administratively up does not mean link up or traffic. A removed member (up or
              down) is released, before the deployment and as in 'state=deleted', to the fabric's host interface default
              HOST_INTF_ADMIN_STATE (true - up, the NDFC default - or false - down), the value the generic reset of a host
              interface uses; the module corrects the release with one modify only when the controller released it otherwise.
              An unreadable fabric default or an unknown member state is refused; removing members needs no check mode.
              With C(deploy) false a member removal or a deletion is SAVED - the
              modify or mark-delete, the released member corrected to the fabric default and the pending
              validated by the pre-deploy gate, with no deployment request (result C(pvlan_saved)); a later
              request with C(deploy) true, in any process, recognises the saved operation from the
              controller's state only (the marked-for-deletion listing, the device's running configuration
              and the released member), deploys and verifies it without a second mark-delete, and the
              same request with C(deploy) false writes nothing and reports it still pending (MEASURED for
              host mode, deletion and member removal, on NDFC 12.6.0.267; NOT LIVE TESTED for the other modes).
              For 'trunk secondary' the member must ALREADY be prepared as a neutral access
              (int_access_host) or routed (int_routed_host) port, administratively up or down; a member in switchport
              mode trunk is refused (known incident - NX-OS rejects the join) and the module never
              converts a member. 'state=deleted' removes the port-channel and releases its member to the
              fabric's host interface default before the deployment, on the policy the controller releases it
              to (read afresh, never converted) - C(int_trunk_host), or C(int_routed_host) only in the
              measured neutral form (no address, VRF, routing, QoS or freeform commands, MTU 9216,
              speed Auto); any other release stops before the deployment.
            - Companion fields of mode 'pvlan' on a port-channel (NOT LIVE TESTED). Native, no
              C(patch_version) needed - 'bpdu_guard', 'port_type_fast', 'mtu', 'copy_description',
              'enable_cdp', 'orphan_port', 'duplex', 'queuing_policy', 'disable_lacp_suspend_individual',
              'lacp_port_priority' (1-65535) and 'lacp_rate' (normal, fast); 'bpdu_guard' takes a boolean or 'true', 'false',
              'no' in any letter case and 'speed' any letter case of its values, both sent in the template's spelling. Registered, so they need an
              approved C(patch_version) and NDFC 12.6.0.267 or later - 'disable_lldp_transmit',
              'disable_lldp_receive', 'spanning_tree_port_type' and 'disable_queuing_stats'. 'merged'
              keeps an omitted field; 'replaced' returns an omitted native field to the template
              default and withdraws an omitted registered field to its reset (inferred, not measured
              on this policy), or keeps it when the patch context is not approved. CDP, LLDP and the
              LACP priority/rate reach the member through the parent template; 'copy_description'
              copies 'description' to the member. Refused before any write - 'spanning_tree_port_type'
              network/normal while port type fast is true, 'disable_queuing_stats' true without a
              resulting 'queuing_policy', and a 'lacp_rate' change while the member is
              administratively up (template precondition; the module never changes a member's admin
              state).
            - Speed and freeform of mode 'pvlan' on a port-channel (NOT LIVE TESTED). 'speed' takes the
              template values; it is rendered on the port-channel and inherited by every member, and
              the controller checks that the switch supports it. The controller's pending carries the
              speed on the port-channel only and NX-OS applies it to the member (MEASURED for 1Gb, one
              member, host mode, administratively down - the addition and the return to Auto with
              C(no speed 1000)); the module accepts that form only for C(speed 1000), the member
              administratively down, its own persisted channel-group, the same mode on member and
              port-channel, no C(no negotiate auto) and every other member line unchanged. Any other
              speed or pending form is refused before the deployment (the intent change already written
              is reported, not rolled back). The same holds for C(duplex) full (MEASURED for one member, host mode, administratively down, with
              the speed fixed at 1000 and unchanged in that transition) - the controller's pending carries
              C(duplex full) on the port-channel only and its withdrawal is C(no duplex full); a member that
              follows is accepted, anything else is refused before the deployment. Not covered - C(duplex) half, a
              duplex change together with a speed or MTU change, any other speed. On an existing port-channel or
              vPC a request that changes the speed and the duplex at once (against the current intent, judged on
              each vPC peer) is refused before any write - set the fixed speed first, in its own request, and then
              the duplex; to withdraw both, set duplex auto first and then speed Auto (a creation may set both).
              More than one member is not refused by count - each member is judged on its own state and is covered
              by offline tests; the live measurement covers one member per port-channel or leg. A duplex other
              than auto needs a resulting fixed speed (NX-OS rejects it with speed Auto) - the request is refused
              before any write, judged on the resulting state ('merged' keeps an omitted speed); the return to
              auto is never blocked. The post-deployment readback also compares the stored duplex (NOT LIVE TESTED
              by the module).
              Not measured and not checked - more than one member, a
              mode other than host, another switch role or platform; they are accepted when the
              controller's pending has the measured form, followed only by the usual post-deployment
              compliance and intent readback. Freeform 'cmds' holds one top-level
              command per entry; a text (and a list entry holding line breaks) is also accepted and every
              line is checked as one entry, while a text with a comma is refused (the same applies to
              C(peer1_cmds) and C(peer2_cmds) of a vPC). 'merged' keeps an omitted 'speed' or 'cmds' and adds the listed
              commands to the current ones; 'replaced' returns an omitted 'speed' to Auto and states
              the exact command list (an omitted or empty list clears it); a command repeated in one
              request is kept once, in the order of its first appearance. A speed returning to Auto is
              deployed only when the pending withdraws C(speed <n>) and, when the controller had added
              it, C(no negotiate auto) (expected as C(negotiate auto); INFERRED, not measured - the
              templates never render it); a different pending is refused before any deployment.
              Refused before any write -
              a command the controller copies to every member (starting with cts, duplex,
              flowcontrol, load-interval, medium, mtu, no negotiate, port-type, priority-flow-control,
              speed, storm-control or switchport), a command of a field a structured option owns
              (private-vlan, channel-group, vpc, interface, mtu, speed, negotiate, duplex,
              spanning-tree, description, cdp, lldp, lacp, shutdown, priority-flow-control,
              service-policy, ip port access-group) and an indented sub-command.
            choices: ['trunk', 'access', 'l3', 'dot1q', 'monitor', 'pvlan']
            type: str
            required: true
          pvlan_mode:
            description:
            - Private VLAN mode. Required, and only valid, when 'mode' is 'pvlan'. It cannot be changed on an
              existing port-channel.
            choices: ['host', 'promiscuous', 'trunk promiscuous', 'trunk secondary']
            type: str
          pvlan_association:
            description:
            - Primary/secondary VLAN associations for C(pvlan_mode) C(host) (exactly one) and C(trunk secondary)
              (one secondary per primary; the secondary must be an isolated VLAN), as a list of dictionaries with
              the keys C(primary_vlan) and C(secondary_vlan).
            - A secondary VLAN belongs to one primary VLAN - the resulting list (after a C(merged) union with the current one)
              that puts one secondary under two primaries is refused before any write.
            type: list
            elements: dict
          pvlan_mapping:
            description:
            - Promiscuous mappings for C(pvlan_mode) C(promiscuous) (a single primary VLAN) and C(trunk promiscuous),
              as a list of dictionaries with the keys C(primary_vlan) and C(secondary_vlans) (a VLAN list string; a single-value range
              "N-N" is the VLAN N, also in C(allowed_vlans)).
            - A secondary VLAN belongs to one primary VLAN - the resulting list (after a C(merged) union with the current one)
              that puts one secondary under two primaries is refused before any write.
            type: list
            elements: dict
          members:
            description:
            - Member interfaces that are part of this port channel
            type: list
            elements: str
            required: true
          access_vlan:
            description:
            - Vlan for the interface. This option is applicable only for interfaces whose 'mode' is 'access' or 'dot1q'
            type: str
            default: ""
          native_vlan:
            description:
            - Vlan used as native vlan.
              This option is applicable only for interfaces whose 'mode' is 'trunk'.
            type: str
            default: ""
          int_vrf:
            description:
            - Interface VRF name. This object is applicable only if the 'mode' is 'l3'
            type: str
            default: default
          ipv4_addr:
            description:
            - IPV4 address of the interface. This object is applicable only if the 'mode' is 'l3'
            type: str
            default: ""
          ipv4_mask_len:
            description:
            - IPV4 address mask length. This object is applicable only if the 'mode' is 'l3'
            - Minimum Value (1), Maximum Value (31)
            type: int
            default: 8
          route_tag:
            description:
            - Route tag associated with the interface IP. This object is applicable only if the 'mode' is 'l3'
            type: str
            default: ""
          cmds:
            description:
            - Commands to be included in the configuration under this interface
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the interface
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
          orphan_port:
            description:
            - interface orphan port behavior when switch is in vPC
            type: bool
            default: false
          duplex:
            description:
            - Duplex of the interface. Speed must be set to use duplex.
            type: str
            choices: ['auto', 'full', 'half']
            default: auto
          enable_pfc:
            description:
            - State of Priority Flow Control (PFC) on the interface
            type: bool
            default: false
          enable_cdp:
            description:
            - State of CDP protocol on the interface
            type: bool
            default: true
          enable_monitor:
            description:
            - State of Switchport Monitor for SPAN/ERSPAN
            type: bool
            default: false
          disable_lacp_suspend_individual:
            description:
            - If disabled, lacp will put the port to individual state and not suspend the port
              in case the port does not get LACP BPDU from the peer ports in the port-channel
            type: bool
            default: false
          lacp_port_priority:
            description:
            - <1-65535> Set LACP port priority on member interfaces, default is 32768
            type: int
            default: 32768
          lacp_rate:
            description:
            - Set the rate at which LACP control packets are sent to an LACP-supported
              interface. Normal rate (30 seconds), fast rate (1 second), rate is set on member
              interfaces, default is normal
            type: str
            choices: ['normal', 'fast']
            default: normal
          enable_qos:
            description:
            - Enable QoS on the interface.
              This option is applicable only for interfaces whose 'mode' is 'trunk', 'access', or 'l3'
            type: bool
            default: false
          qos_policy:
            description:
            - QoS policy name to apply to the interface. This option is only valid when 'enable_qos' is true.
              This option is applicable only for interfaces whose 'mode' is 'trunk', 'access', or 'l3'
            type: str
            default: ""
          queuing_policy:
            description:
            - Queuing policy name to apply to the interface.
              This option is applicable only for interfaces whose 'mode' is 'trunk', 'access', or 'l3'
            type: str
            default: ""
          copy_description:
            description:
            - Copy the port-channel description to its member interfaces.
            type: bool
            default: false
          guard_mode:
            description:
            - Spanning-tree guard mode. This option is applicable only when
              mode is trunk. Explicit-only, no default; when omitted the
              current controller value is left untouched.
            type: str
            choices: ['root', 'none', 'loop', 'no']
          acl_filter:
            description:
            - Name of the ACL filter applied to the port-channel. This option
              is applicable only when mode is trunk, access or dot1q. Between
              1 and 64 characters. Explicit-only, no default; when omitted the
              current controller value is left untouched.
            type: str
          spanning_tree_port_type:
            description:
            - Spanning-tree port type. This option is applicable only when mode
              is trunk, access, dot1q or pvlan.
            - Requires 'port_type_fast' to be false. The parent template rejects
              'network' or 'normal' while port type fast is enabled, and port type
              fast defaults to true, so both must be sent together.
            - A value of 'no' does not mean "no configuration". It defers to the
              port-type-fast behaviour.
            - Explicit-only, no default. When omitted the current controller value
              is left untouched.
            type: str
            choices: ['no', 'network', 'normal']
          disable_qos_stats:
            description:
            - Disable statistics for the attached QoS policy. This option is
              applicable only when mode is trunk, access or dot1q.
            - Does NOT produce a configuration line of its own. It appends
              ' no-stats' to the 'service-policy type qos input' line that
              'enable_qos' and 'qos_policy' produce. With no QoS policy in effect
              the value is stored on the controller and changes nothing on the
              device.
            - Explicit-only, no default. When omitted the current controller value
              is left untouched.
            type: bool
          disable_queuing_stats:
            description:
            - Disable statistics for the attached output queuing policy. This
              option is applicable only when mode is trunk, access, dot1q or pvlan
              (in mode pvlan, true requires a resulting 'queuing_policy').
            - Does NOT produce a configuration line of its own. It appends
              ' no-stats' to the 'service-policy type queuing output' line that
              'queuing_policy' produces. With 'queuing_policy' empty the value is
              stored on the controller and changes nothing on the device.
            - Explicit-only, no default. When omitted the current controller value
              is left untouched.
            type: bool
      profile_vpc:
        description:
        - Though the key shown here is 'profile_vpc' the actual key to be used in playbook
          is 'profile'. The key 'profile_vpc' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for virtual port channel inetrface configurations.
        suboptions:
          mode:
            description:
            -  Interface mode
            - C(dot1q) selects the dot1q-tunnel vPC template (C(int_vpc_dot1q_tunnel)) and
              requires NDFC 12. It takes the same options as C(access), plus the LACP options.
            - C(pvlan) selects the NDFC 12 policy C(int_vpc_pvlan_host) for a vPC with one or more
              explicit physical members per peer, in any of its four C(pvlan_mode) values. Supported - creation,
              identical repetition, an update that reaches BOTH peers (the list of the mode, 'pc_mode',
              the description of both peers, or the PVLAN native/allowed VLANs of both peers), a change
              of the description of ONE peer alone (C(peer1_description) or C(peer2_description), only while
              C(copy_description) is false; the other peer keeps its value and is still checked to stay
              unchanged; an explicit empty string clears the description of that peer, while an omitted
              description keeps it; NOT LIVE TESTED), a change
              of the members of one peer or both, and C(state=deleted) of the vPC, all with C(deploy)
              true when a deployment is wanted. Refused before any change is sent - a C(pvlan_mode)
              change, a field the mode does not take, a PCID change of an existing vPC (C(peer1_pcid) and
              C(peer2_pcid) are optional integers 1-4096, one per peer, independent of the vPC id and of each other - as for the regular
              vPC; omitted means the vPC id on a creation and the stored value on an update), an empty list,
              removing secondaries from a C(promiscuous) mapping that keeps others (protection kept
              from the measured Ethernet defect), any other update that reaches only
              one peer (including a description change of one peer together with a member change of
              that peer, a one-peer PVLAN native/allowed change and a one-peer freeform change), a change
              of C(admin_state) of an existing vPC, check mode for a
              creation or a deletion and NDFC 11. C(overridden) keeps a requested vPC as C(replaced) and
              deletes a PVLAN vPC of the sweep's scope that the request no longer wants through the
              deletion path (one decision per pair and name; MEASURED for host mode on NDFC 12.6.0.267 - retention, unchanged
              repetition, a vPC no longer wanted and the last PVLAN vPC; NOT LIVE TESTED for the other modes). For
              C(trunk secondary) each member must ALREADY be
              prepared as a neutral access (C(int_access_host)) or routed
              (C(int_routed_host)) port on BOTH peers; a member in switchport mode trunk is refused
              (known incident - NX-OS rejects the join) and the module never converts a member.
              C(peer1_*) belong to the first switch of C(switch) and C(peer2_*) to the second; both
              switches must be the two switches of the vPC pair. The members are managed by the
              parent; per peer, C(peer1_members) and C(peer2_members) follow the regular port-channel
              rule - C(merged) adds the listed members (an omitted list keeps the current members),
              C(replaced) states the exact member list of each peer, which must be listed explicitly
              (an omitted or empty list is refused). An added member must qualify as for a creation (as
              for a regular port-channel; each member keeps its own explicit administrative state, an up
              member on one peer and a down member on the other are both admitted and each peer is judged
              on its own serial - MEASURED for host with both members up, NOT LIVE TESTED for the other
              modes); a
              removed member (up or down) is released to the fabric's host interface default on its own
              switch before the deployment (needs no check mode and a readable fabric default; with
              C(deploy) false the removal or the deletion is saved and completed later as for a regular
              port-channel - a saved deletion is recognised only when BOTH peers list the vPC's children
              marked for deletion, a saved member removal only when the device still joins the port to the
              peer's port-channel, the vPC intent no longer lists it and it is already released). Both
              peers are validated before anything is deployed and the vPC is reported
              successful only when EVERY peer is. Before the deployment, each released member is proven on
              its own peer against the explicit contract (a direct C(int_trunk_host), or C(int_routed_host)
              in the measured neutral form, as the controller releases it; at the fabric's host interface
              default; no freeform commands, no residual PVLAN or channel-group field and no policy left by
              the vPC) without rewriting any member beyond setting a released member to that default on its
              own policy - also when a later run completes a saved deletion. After the deployment the module
              reads only the interface summary of each peer - the vPC and its port-channels must no longer
              be listed and every member must be listed In-Sync - and does not read the intent or the
              policies again.
            - Companion fields of C(pvlan) on a vPC, shared by both peers (NOT LIVE TESTED). Native, no
              C(patch_version) needed - C(bpdu_guard), C(port_type_fast), C(mtu), C(copy_description),
              C(enable_cdp), C(duplex), C(enable_pfc), C(queuing_policy), C(disable_lacp_suspend_individual),
              C(enable_lacp_vpc_convergence), C(lacp_port_priority), C(lacp_rate), C(enable_qos) and
              C(qos_policy). Registered, so they need
              an approved C(patch_version) and NDFC 12.6.0.267 or later - C(disable_lldp_transmit),
              C(disable_lldp_receive), C(spanning_tree_port_type), C(disable_queuing_stats), C(acl_filter) and
              C(disable_qos_stats).
              The parent hands them to both child port-channels and both members; the same merged,
              replaced and pre-write rules as the regular port-channel apply, on both peers.
              C(speed) (shared by both peers) follows the port-channel rules and reaches both child
              port-channels and every member; the inherited member speed is judged on each peer's own
              serial and preview (MEASURED for 1Gb on both peers), and one peer that does not match
              stops the whole vPC before any deployment. The same holds for C(duplex) full with a fixed speed 1000 unchanged (MEASURED on both peers, one
              member per leg) - each leg is judged on its own serial and its own child port-channel, and a duplex
              other than auto with a resulting speed Auto, or a speed and duplex change at once on either peer, is
              refused before any write; the stored duplex of the parent and of each child is read back. C(peer1_cmds) and C(peer2_cmds) set the freeform of each
              peer's port-channel under the port-channel freeform rules; a change of the freeform of one
              peer only is refused like any other update that reaches one peer (NOT LIVE TESTED).
              Ingress QoS on a vPC in mode C(pvlan) (NOT LIVE TESTED) - C(enable_qos), C(qos_policy) and
              C(disable_qos_stats) follow the regular vPC merged/replaced rule (C(merged) keeps an omitted
              field, also a residual policy when it disables QoS; C(replaced) returns them to false / '' /
              false, the last one only with an approved C(patch_version)), with two deliberate
              differences, so this is not full parity with the regular vPC. First, a C(merged) request
              that changes only C(qos_policy) keeps the C(enable_qos) state already stored and applies
              the new policy; the regular vPC path currently sends an empty policy unless C(enable_qos)
              is restated. Second, the checks are stricter than the regular ones and apply to the
              RESULTING state of the vPC, not only to the fields of the request. Refused before any
              write - C(qos_policy) with QoS disabled, C(enable_qos) true without a C(qos_policy) (the
              template's fabric-dependent default, QOS_CLASSIFICATION on an AI/ML fabric, is not
              modeled) and C(disable_qos_stats) true without an enabled policy. Because the state is
              checked, an existing vPC whose stored intent is QoS enabled with an empty policy (for
              example a fabric-dependent default set through the GUI) refuses even a C(merged) update
              of another field; to proceed, give the correct C(qos_policy), or set C(enable_qos) false
              when disabling QoS is the intent. The module makes neither correction by itself. Both child
              port-channels are expected to carry C(service-policy type qos input <policy>[ no-stats]).
              The int_vpc_pvlan_host / int_vpc_pvlan_po revision installed on the test ND does not hand
              these values (nor C(queuing_policy) and C(enable_pfc)) to the children and renders a
              C(type ENABLE_QOS) literal; on such a revision the deployment is refused before it is sent,
              and the intent change already written is reported, not rolled back. A live run therefore
              depends on verifying the installed template revision first.
            choices: ['trunk', 'access', 'dot1q', 'pvlan']
            type: str
            required: true
          pvlan_mode:
            description:
            - Private VLAN mode. Required, and only valid, when 'mode' is 'pvlan'. It cannot be changed on an existing vPC.
            choices: ['host', 'promiscuous', 'trunk promiscuous', 'trunk secondary']
            type: str
          pvlan_association:
            description:
            - Primary/secondary VLAN associations for C(pvlan_mode) C(host) (exactly one) and C(trunk secondary)
              (one secondary per primary; the secondary must be an isolated VLAN), as a list of dictionaries with
              the keys C(primary_vlan) and C(secondary_vlan).
            - A secondary VLAN belongs to one primary VLAN - the resulting list (after a C(merged) union with the current one)
              that puts one secondary under two primaries is refused before any write.
            type: list
            elements: dict
          pvlan_mapping:
            description:
            - Promiscuous mappings for C(pvlan_mode) C(promiscuous) (a single primary VLAN) and C(trunk promiscuous),
              as a list of dictionaries with the keys C(primary_vlan) and C(secondary_vlans) (a VLAN list string; a single-value range
              "N-N" is the VLAN N, also in C(allowed_vlans)).
            - A secondary VLAN belongs to one primary VLAN - the resulting list (after a C(merged) union with the current one)
              that puts one secondary under two primaries is refused before any write.
            type: list
            elements: dict
          peer1_pcid:
            description:
            - Port channel identifier of first peer. If this object is not included, then the value defaults to the
              vPC identifier. This value cannot be changed once vPC is created
            - Minimum Value (1), Maximum Value (4096)
            - Default value if not specified is the vPC port identifier
            type: int
          peer2_pcid:
            description:
            - Port channel identifier of second peer. If this object is not included, then the value defaults to the
              vPC identifier. This value cannot be changed once vPC is created
            - Minimum Value (1), Maximum Value (4096)
            - Default value if not specified is the vPC port identifier
            type: int
          peer1_members:
            description:
            - Member interfaces that are part of this port channel on first peer
            type: list
            elements: str
            required: true
          peer2_members:
            description:
            - Member interfaces that are part of this port channel on second peer
            type: list
            elements: str
            required: true
          pc_mode:
            description:
            - Port channel mode
            type: str
            choices: ['active', 'passive', 'on']
            default: active
          bpdu_guard:
            description:
            - Spanning-tree bpduguard
            - In mode 'pvlan' a boolean is also accepted, and the strings in any letter case; the value is sent as 'true', 'false' or
              'no' ('no' is its own value, not false).
            type: str
            choices: ['true', 'false', 'no']
            default: 'true'
          port_type_fast:
            description:
            - Spanning-tree edge port behavior
            type: bool
            choices: [true, false]
            default: true
          mtu:
            description:
            - Interface MTU
            type: str
            choices: ['default', 'jumbo']
            default: jumbo
          peer1_allowed_vlans:
            description:
            - Vlans that are allowed on this interface of first peer.
              This option is applicable only for interfaces whose 'mode' is 'trunk', or 'pvlan' with
              C(pvlan_mode) C(trunk promiscuous) or C(trunk secondary) (PVLAN trunk allowed VLANs of that peer;
              C(all) is refused there, no default - omitted keeps the current value in C(merged)).
            type: str
            choices: ['none', 'all', 'vlan-range(e.g., 1-2, 3-40)']
            default: none
          peer2_allowed_vlans:
            description:
            - Vlans that are allowed on this interface of second peer.
              This option is applicable only for interfaces whose 'mode' is 'trunk', or 'pvlan' with
              C(pvlan_mode) C(trunk promiscuous) or C(trunk secondary) (as C(peer1_allowed_vlans)).
            type: str
            choices: ['none', 'all', 'vlan-range(e.g., 1-2, 3-40)']
            default: none
          peer1_native_vlan:
            description:
            - Vlan used as native vlan of first peer.
              This option is applicable only for interfaces whose 'mode' is 'trunk', or 'pvlan' with
              C(pvlan_mode) C(trunk promiscuous) or C(trunk secondary) ('' or one VLAN; PVLAN trunk native VLAN of that peer).
            type: str
            default: ""
          peer2_native_vlan:
            description:
            - Vlan used as native vlan of second peer.
              This option is applicable only for interfaces whose 'mode' is 'trunk', or 'pvlan' with
              C(pvlan_mode) C(trunk promiscuous) or C(trunk secondary) (as C(peer1_native_vlan)).
            type: str
            default: ""
          peer1_access_vlan:
            description:
            - Vlan for the interface of first peer.
              This option is applicable only for interfaces whose 'mode' is 'access' or 'dot1q'.
              For 'dot1q' it is the dot1q-tunnel VLAN of that peer.
            type: str
            default: ''
          peer2_access_vlan:
            description:
            - Vlan for the interface of second peer.
              This option is applicable only for interfaces whose 'mode' is 'access' or 'dot1q'.
              For 'dot1q' it is the dot1q-tunnel VLAN of that peer.
            type: str
            default: ''
          peer1_cmds:
            description:
            - Commands to be included in the configuration under this interface of first peer
            type: list
            elements: str
            default: []
          peer2_cmds:
            description:
            - Commands to be included in the configuration under this interface of second peer
            type: list
            elements: str
            default: []
          peer1_description:
            description:
            - Description of the interface of first peer
            type: str
            default: ""
          peer2_description:
            description:
            - Description of the interface of second peer
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
          disable_lacp_suspend_individual:
            description:
            - If disabled, lacp will put the port to individual state and not suspend the port
              in case the port does not get LACP BPDU from the peer ports in the port-channel
            type: bool
            default: false
          enable_lacp_vpc_convergence:
            description:
            - Enable lacp convergence for vPC port-channels
            type: bool
            default: false
          lacp_port_priority:
            description:
            - <1-65535> Set LACP port priority on member interfaces, default is 32768
            type: int
            default: 32768
          lacp_rate:
            description:
            - Set the rate at which LACP control packets are sent to an LACP-supported
              interface. Normal rate (30 seconds), fast rate (1 second), rate is set on member
              interfaces, default is normal
            type: str
            choices: ['normal', 'fast']
            default: normal
          enable_qos:
            description:
            - Enable QoS on the interface.
              This option is applicable only for interfaces whose 'mode' is 'trunk' or 'access'
            type: bool
            default: false
          qos_policy:
            description:
            - QoS policy name to apply to the interface. This option is only valid when 'enable_qos' is true.
              This option is applicable only for interfaces whose 'mode' is 'trunk' or 'access'
            type: str
            default: ""
          queuing_policy:
            description:
            - Queuing policy name to apply to the interface.
              This option is applicable only for interfaces whose 'mode' is 'trunk' or 'access'
            type: str
            default: ""
          copy_description:
            description:
            - Copy each peer port-channel description to that peer's member interfaces.
            type: bool
            default: false
      profile_subint:
        description:
        - Though the key shown here is 'profile_subint' the actual key to be used in playbook
          is 'profile'. The key 'profile_subint' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for sub-interface configurations.
        suboptions:
          mode:
            description:
            - Interface mode
            choices: ['subint']
            type: str
            required: true
          int_vrf:
            description:
            - Interface VRF name.
            type: str
            default: default
          ipv4_addr:
            description:
            - IPV4 address of the interface.
            type: str
            default: ""
          ipv4_mask_len:
            description:
            - IPV4 address mask length.
            - Minimum Value (8), Maximum Value (31)
            type: int
            default: 8
          ipv6_addr:
            description:
            - IPV6 address of the interface.
            type: str
            default: ""
          ipv6_mask_len:
            description:
            - IPV6 address mask length.
            - Minimum Value (1), Maximum Value (31)
            type: int
            default: 8
          mtu:
            description:
            - Interface MTU
            - Minimum Value (567), Maximum Value (9216)
            type: int
            default: 9216
          vlan:
            description:
            - DOT1Q vlan id for this interface
            - Minimum Value (2), Maximum Value (3967)
            type: int
            default: 0
          cmds:
            description:
            - Commands to be included in the configuration under this interface
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the interface
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
          route_tag:
            description:
            - Route tag associated with the interface IP.
            type: str
            default: ""
      profile_lo:
        description:
        - Though the key shown here is 'profile_lo' the actual key to be used in playbook
          is 'profile'. The key 'profile_lo' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for loopback interface configurations.
        suboptions:
          mode:
            choices: ['lo', 'fabric', 'mpls']
            description:
            - There are several modes for loopback interfaces.
            - Mode 'lo' is used to create, modify and delete non fabric loopback
              interfaces using policy 'int_loopback'.
            - Mode 'fabric' is used to modify loopbacks created when the fabric is first
              created using policy 'int_fabric_loopback_11_1'
            - Mode 'mpls' is used to modify loopbacks created when the fabric is first
              created using policy 'int_mpls_loopback'
            - Mode 'fabric' and 'mpls' interfaces can be modified but not created or deleted.
            type: str
            required: true
          int_vrf:
            description:
            - Interface VRF name.
            type: str
            default: default
          ipv4_addr:
            description:
            - IPv4 address of the interface.
            type: str
            default: ""
          secondary_ipv4_addr:
            description:
            - Secondary IP address of the nve interface loopback
            type: str
            default: ""
          ipv6_addr:
            description:
            - IPv6 address of the interface.
            type: str
            default: ""
          route_tag:
            description:
            - Route tag associated with the interface IP.
            type: str
            default: ""
          cmds:
            description:
            - Commands to be included in the configuration under this interface
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the interface
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
      profile_eth:
        description:
        - Though the key shown here is 'profile_eth' the actual key to be used in playbook
          is 'profile'. The key 'profile_eth' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for ethernet interface configurations.
        suboptions:
          mode:
            description:
            - Interface mode
            - When ethernet interface is a PortChannel or vPC member, mode is ignored.
              The only properties that can be managed for PortChannel or vPC member interfaces
              are 'admin_state', 'description' and 'cmds'. All other properties are ignored.
            - Mode 'pvlan' selects the NDFC 12 policy 'int_pvlan_host' on a standalone physical
              Ethernet interface; see 'pvlan_mode'. It is refused on a PortChannel or vPC member
              and on an interface owned by a network attachment.
            choices: ['trunk', 'access', 'routed', 'monitor', 'epl_routed', 'dot1q', 'pvlan']
            type: str
            required: true
          bpdu_guard:
            description:
            - Spanning-tree bpduguard
            - In mode 'pvlan' a boolean is also accepted, and the strings in any letter case; the value is sent as 'true', 'false' or
              'no' ('no' is its own value, not false).
            type: str
            choices: ['true', 'false', 'no']
            default: 'true'
          port_type_fast:
            description:
            - Spanning-tree edge port behavior
            type: bool
            choices: [true, false]
            default: true
          mtu:
            description:
            - Interface MTU.
            - Can be specified either "default" or "jumbo" for access and
              trunk interface types. If not specified, it defaults to "jumbo"
            - Can be specified with any value within 576 and 9216 for routed interface
              types. If not specified, it defaults to 9216
            type: str
          allowed_vlans:
            description:
            - Vlans that are allowed on this interface.
              This option is applicable only for interfaces whose 'mode' is 'trunk'
            type: str
            choices: ['none', 'all', 'vlan-range(e.g., 1-2, 3-40)']
            default: none
          access_vlan:
            description:
            - Vlan for the interface. This option is applicable only for interfaces whose 'mode' is 'access' or 'dot1q'
            type: str
            default: ""
          native_vlan:
            description:
            - Vlan used as native vlan.
              This option is applicable only for interfaces whose 'mode' is 'trunk'.
            type: str
            default: ""
          spanning_tree_port_type:
            description:
            - Spanning-tree port type. This option is applicable only when mode
              is trunk or access.
            - Requires 'port_type_fast' to be false. The parent template rejects
              'network' or 'normal' while port type fast is enabled, and port
              type fast defaults to true, so both must be sent together.
            - A value of 'no' does not mean "no configuration". It defers to the
              port-type-fast behaviour, and the resulting CLI differs per mode -
              'spanning-tree port type edge trunk' on a trunk interface, and
              'spanning-tree port type edge' on an access one. Both were observed
              on a live switch.
            - Explicit-only, no default. When omitted the current controller
              value is left untouched.
            type: str
            choices: ['no', 'network', 'normal']
          speed:
            description:
            - Speed of the interface.
            - In mode 'pvlan' it must be one of Auto, 10Mb, 100Mb, 1Gb, 2.5Gb, 5Gb, 10Gb, 25Gb, 40Gb, 50Gb, 100Gb, 200Gb, 400Gb or 800Gb,
              in any letter case, and it is sent in that spelling.
            type: str
            default: Auto
          orphan_port:
            description:
            - interface orphan port behavior when switch is in vPC
            type: bool
            default: false
          duplex:
            description:
            - Duplex of the interface. Speed must be set to use duplex.
            type: str
            choices: ['auto', 'full', 'half']
            default: auto
          int_vrf:
            description:
            - Interface VRF name. This object is applicable only if the 'mode' is 'routed'
            type: str
            default: default
          ipv4_addr:
            description:
            - IPV4 address of the interface. This object is applicable only if the 'mode' is
              'routed' or 'epl_routed'
            type: str
            default: ""
          ipv4_mask_len:
            description:
            - IPV4 address mask length. This object is applicable only if the 'mode' is 'routed' or
              'epl_routed'
            - Minimum Value (1), Maximum Value (31)
            type: int
            default: 8
          ipv6_addr:
            description:
            - IPV6 address of the interface. This object is applicable only if the 'mode' is 'epl_routed'
            type: str
            default: ""
          ipv6_mask_len:
            description:
            - IPV6 address mask length. This object is applicable only if the 'mode' is 'epl_routed'
            - Minimum Value (1), Maximum Value (31)
            type: int
            default: 8
          route_tag:
            description:
            - Route tag associated with the interface IP. This object is applicable only if the 'mode' is
              'routed' or 'epl_routed'
            type: str
            default: ""
          cmds:
            description:
            - Commands to be included in the configuration under this interface
            - In C(mode=pvlan) a text is also accepted, one command per line; a text with a comma is refused.
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the interface
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
          enable_pfc:
            description:
            - State of Priority Flow Control (PFC) on the interface
            type: bool
            default: false
          enable_cdp:
            description:
            - State of CDP protocol on the interface
            type: bool
            default: true
          enable_monitor:
            description:
            - State of Switchport Monitor for SPAN/ERSPAN
            type: bool
            default: false
          flowcontrol_receive:
            description:
            - State of IEEE 802.3x pause-frame reception. This option is
              applicable only when mode is trunk or access.
            - Explicit-only, no default. When omitted the current controller
              value is left untouched; set 'off' to remove the CLI.
            type: str
            choices: ['on', 'off']
          flowcontrol_send:
            description:
            - State of IEEE 802.3x pause-frame transmission. This option is
              applicable only when mode is trunk or access.
            - Explicit-only, no default. When omitted the current controller
              value is left untouched; set 'off' to remove the CLI.
            type: str
            choices: ['on', 'off']
          guard_mode:
            description:
            - Spanning-tree guard mode. This option is applicable only when
              mode is trunk. Explicit-only, no default; when omitted the
              current controller value is left untouched.
            type: str
            choices: ['root', 'none', 'loop', 'no']
          disable_lldp_transmit:
            description:
            - Disable LLDP transmit on the interface. Replaces the earlier
              disable_lldp, which acted on both directions at once; the two
              directions are now independent. Explicit-only, no default; when
              omitted the current controller value is left untouched.
            type: bool
          disable_lldp_receive:
            description:
            - Disable LLDP receive on the interface. See disable_lldp_transmit;
              setting one without the other emits a single CLI line.
              Explicit-only, no default; when omitted the current controller
              value is left untouched.
            type: bool
          acl_filter:
            description:
            - Name of the ACL filter applied to the interface. This option is
              applicable only when mode is trunk or access. Between 1 and 64
              characters. Explicit-only, no default; when omitted the current
              controller value is left untouched.
            type: str
          enable_qos:
            description:
            - Enable QoS on the interface.
              This option is applicable only for interfaces whose 'mode' is 'trunk', 'access', or 'routed'
            type: bool
            default: false
          qos_policy:
            description:
            - QoS policy name to apply to the interface. This option is only valid when 'enable_qos' is true.
              This option is applicable only for interfaces whose 'mode' is 'trunk', 'access', or 'routed'
            type: str
            default: ""
          queuing_policy:
            description:
            - Queuing policy name to apply to the interface.
              This option is applicable only for interfaces whose 'mode' is 'trunk', 'access', or 'routed'
            type: str
            default: ""
          disable_qos_stats:
            description:
            - Disable statistics for the attached QoS policy. This option is applicable
              only when mode is trunk or access.
            - Does NOT produce a configuration line of its own. It appends ' no-stats'
              to the 'service-policy type qos input' line that 'enable_qos' and
              'qos_policy' produce. With no QoS policy in effect the value is stored on
              the controller and changes nothing on the device.
            - Requires 'enable_qos' to be true AND a QoS policy name to resolve, either
              from 'qos_policy' or from the fabric AI/ML QoS setting.
            - Explicit-only, no default. When omitted the current controller value is
              left untouched.
            type: bool
          disable_queuing_stats:
            description:
            - Disable statistics for the attached output queuing policy. This option is
              applicable only when mode is trunk or access.
            - Does NOT produce a configuration line of its own. It appends ' no-stats'
              to the 'service-policy type queuing output' line that 'queuing_policy'
              produces. With 'queuing_policy' empty the value is stored on the controller
              and changes nothing on the device.
            - Explicit-only, no default. When omitted the current controller value is
              left untouched.
            type: bool
          pvlan_mode:
            description:
            - Private VLAN port mode. Required, and only valid, when 'mode' is 'pvlan'.
            - With 'mode' 'pvlan' no field has a module default. State 'merged' keeps every
              omitted field at its current controller value; 'replaced' and a retained
              'overridden' interface clear omitted lists and 'native_vlan'/'allowed_vlans' and
              return omitted companion fields to the int_pvlan_host template defaults.
            - Changing the submode of an existing PVLAN port requires 'replaced' or
              'overridden'; 'merged' refuses it.
            - In mode 'pvlan' the supported companion fields are 'description', 'admin_state',
              'bpdu_guard', 'port_type_fast', 'mtu', 'speed', 'enable_cdp', 'orphan_port',
              'duplex', 'enable_pfc', 'enable_qos', 'qos_policy', 'queuing_policy' and 'cmds', plus the
              registered 'disable_lldp_transmit' and 'disable_lldp_receive' (NOT LIVE TESTED in this mode;
              they need an approved C(patch_version)). Any other field is refused. An explicit LLDP value
              always wins; an omitted one is kept by 'merged' and, on 'replaced', withdrawn to 'false'
              (inferred) only with an approved C(patch_version), else kept. 'cmds' must not carry private-vlan or switchport
              lines. 'native_vlan' ('' or one VLAN) and 'allowed_vlans' ('', 'none' or VLAN
              ranges; 'all' is refused) apply to the two trunk submodes only.
            - Before every deployment attempt (including the check_deploy resend and the
              deployment-status retries) the module recomputes the switch pending configuration
              through the legacy config-preview API. Using that answer's device running
              configuration and the controller's expected configuration, it deploys only the
              remaining work when every pending command for the interface leads from the device
              state to the intended state; it skips the attempt for an interface whose device
              state is already verified as the intended state. When a check fails after the
              intent was written, the intent change is reported and is not rolled back.
            - Every deployment response is judged on its original body; a failed or
              unrecognised response fails the task even if a later read reports In-Sync, and no
              further deployment is sent.
            - The interface must be a standalone physical Ethernet with exactly one direct
              policy, both in the interface summary and in the switch policy list; a network
              attachment, port-channel membership or incomplete ownership data is refused.
            - The CLI coverage of the current and destination configurations is verified
              before any write, also in check mode. The bulk interface update capability is
              verified before any write in normal mode only; its sole probe is a POST request,
              so in check mode a native PVLAN invocation that would change intent is refused
              with "could not be verified in check mode", and nothing is sent.
            - Removal authority comes from the requested transition, not from the device. A
              pending command may withdraw only a line the int_pvlan_host (or, for a reset or
              conversion, int_trunk_host) template renders, or a 'cmds' line of the current or
              requested intent. A device command outside that set is never withdrawn by the
              deployment, and one inside a field these policies own but that cannot be
              interpreted blocks the deployment.
            - Removing a secondary VLAN from a 'promiscuous' mapping that keeps other
              secondaries is refused before any write, because the controller generates an
              invalid removal command for that transition. Clear the mapping or use
              'trunk promiscuous'.
            type: str
            choices: ['host', 'promiscuous', 'trunk promiscuous', 'trunk secondary']
          pvlan_association:
            description:
            - Primary/secondary VLAN associations for 'pvlan_mode' 'host' (at most one) and
              'trunk secondary' (one secondary per primary). A new 'trunk secondary'
              association requires the fabric network of the secondary VLAN to be isolated.
            - A secondary VLAN belongs to one primary VLAN - the resulting list (after a 'merged' union with the current one)
              that puts one secondary under two primaries is refused before any write.
            type: list
            elements: dict
            suboptions:
              primary_vlan:
                description:
                - Primary VLAN ID (1-4094).
                type: int
                required: true
              secondary_vlan:
                description:
                - Secondary VLAN ID (1-4094).
                type: int
                required: true
          pvlan_mapping:
            description:
            - Promiscuous mappings for 'pvlan_mode' 'promiscuous' (one primary) and
              'trunk promiscuous'. Ranges are expanded and sent as one row per pair.
            - A secondary VLAN belongs to one primary VLAN - the resulting list (after a 'merged' union with the current one)
              that puts one secondary under two primaries is refused before any write.
            type: list
            elements: dict
            suboptions:
              primary_vlan:
                description:
                - Primary VLAN ID (1-4094).
                type: int
                required: true
              secondary_vlans:
                description:
                - Secondary VLAN IDs as a string, for example "2211" or "2211-2212,2214". A single-value range such as "2212-2212" is
                  accepted as the VLAN "2212" and sent and compared as "2212"; a descending, repeated, overlapping or out-of-range value is
                  refused.
                type: str
                required: true
      profile_svi:
        description:
        - Though the key shown here is 'profile_svi' the actual key to be used in playbook
          is 'profile'. The key 'profile_svi' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for SVI interface configurations.
        suboptions:
          mode:
            description:
            - Interface mode.
            choices: ['vlan']
            type: str
            required: true
          int_vrf:
            description:
            - Interface VRF name.
            type: str
            default: "default"
          ipv4_addr:
            description:
            - IPV4 address of the interface.
            type: str
            default: ""
          ipv4_mask_len:
            description:
            - IPV4 address mask length. This parameter is required if 'ipv4_addr' is included.
            - Minimum Value (1), Maximum Value (31)
            type: int
          cmds:
            description:
            - Commands to be included in the configuration under this interface.
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the interface.
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface.
            type: bool
            required: true
          route_tag:
            description:
            - Route tag associated with the interface IP.
            type: str
            default: ""
          mtu:
            description:
            - Interface MTU.
            type: int
            default: 9216
          disable_ip_redirects:
            description:
            - Flag to enable/disable IP redirects.
            type: bool
            default: false
          enable_hsrp:
            description:
            - Flag to enable/disable HSRP on the interface.
            type: bool
            default: false
          hsrp_vip:
            description:
            - Virtual IP address for HSRP. This parameter is required if "enable_hsrp" is True.
            type: str
            default: ""
          hsrp_group:
            description:
            - HSRP group. This parameter is required if "enable_hsrp" is True.
            type: str
            default: ""
          hsrp_priority:
            description:
            - HSRP priority.
            type: str
            default: ""
          hsrp_vmac:
            description:
            - HSRP virtual MAC.
            type: str
            default: ""
          dhcp_server_addr1:
            description:
            - DHCP relay server address.
            type: str
            default: ""
          vrf_dhcp1:
            description:
            - VRF to reach DHCP server. This parameter is required if "dhcp_server_addr1" is included.
            type: str
            default: ""
          dhcp_server_addr2:
            description:
            - DHCP relay server address.
            type: str
            default: ""
          vrf_dhcp2:
            description:
            - VRF to reach DHCP server. This parameter is required if "dhcp_server_addr2" is included.
            type: str
            default: ""
          dhcp_server_addr3:
            description:
            - DHCP relay server address.
            type: str
            default: ""
          vrf_dhcp3:
            description:
            - VRF to reach DHCP server. This parameter is required if "dhcp_server_addr3" is included.
            type: str
            default: ""
          dhcp_server_addr4:
            description:
            - DHCP relay server address.
            - An explicit empty string clears a configured address, also under C(merged), together with its C(vrf_dhcp4);
              an omitted value is preserved under C(merged) and reset under C(replaced) and C(overridden) (NOT LIVE TESTED).
            - The nvPair name depends on the installed C(int_vlan) body and is selected by C(patch_version)
              (legacy C(dhcpServerAddr4), SMU body C(dhcpServerAddress4)).
            type: str
            default: ""
          vrf_dhcp4:
            description:
            - VRF to reach DHCP server. This parameter is required if "dhcp_server_addr4" is included.
            - It is cleared together with C(dhcp_server_addr4).
            type: str
            default: ""
          dhcp_relay_src_intf:
            description:
            - Source interface for DHCP relay. Valid interfaces are Ethernet, port-channel or loopback.
            - Independent of the DHCP server addresses; it can be set on its own.
            - The nvPair name depends on the installed C(int_vlan) body and is selected by C(patch_version)
              (legacy C(DHCP_RELAY_SRC_INTF), SMU body C(dhcpRelaySourceInterface)).
            - An explicit empty string clears a configured source interface, also under C(merged); an omitted value is preserved
              under C(merged) and reset under C(replaced) and C(overridden) (NOT LIVE TESTED).
            type: str
            default: ""
          adv_subnet_in_underlay:
            description:
            - Flag to enable/disable advertisements of subnets into underlay.
            type: bool
            default: false
          enable_netflow:
            description:
            - Flag to enable netflow.
            type: bool
            default: false
          netflow_monitor:
            description:
            - Name of netflow monitor. This parameter is required if "enable_netflow" is True.
            type: str
            default: ""
          hsrp_version:
            description:
            - HSRP protocol version.
            type: int
            default: 1
            choices: [1,2]
          preempt:
            description:
            - Flag to enable/disable overthrow of low priority active routers. This parameter is valid only if "enable_hsrp" is True.
            type: bool
            default: false
          secondary_gws:
            description:
            - Secondary IPv4 addresses of the SVI, each with its prefix length. At most 16 entries.
            - Entries are identified by address. Order is not significant.
            - With I(state=merged), an omitted key or an empty list leaves the current entries
              unchanged, and a non-empty list is added to them; an address that already exists
              takes the prefix length given here.
            - With I(state=replaced) and for an interface kept by I(state=overridden), the list
              is the complete set; omitting the key or giving an empty list removes every entry.
            - Requires a primary IPv4 address on the SVI.
            type: list
            elements: dict
            suboptions:
              gateway_ip_address:
                description:
                - IPv4 address and prefix length, for example 192.0.2.254/24. Host bits are kept.
                type: str
                required: true
          hsrp_secondary_vips:
            description:
            - Secondary IPv4 virtual addresses of the existing HSRP group. At most 16 entries.
            - Same merged, replaced and overridden behavior as I(secondary_gws), identified by
              address. The HSRP group and its primary virtual address are not changed.
            - The controller requires HSRP enabled with a primary IPv4 virtual address, and each
              entry in the subnet of the SVI primary address.
            type: list
            elements: dict
            suboptions:
              hsrp_secondary_vip:
                description:
                - IPv4 address, for example 192.0.2.123.
                type: str
                required: true
      profile_st_fex:
        description:
        - Though the key shown here is 'profile_st_fex' the actual key to be used in playbook
          is 'profile'. The key 'profile_st_fex' is used here to logically segregate the interface objects applicable for this profile
        - Object profile which must be included for straigth-through FEX interface configurations.
        suboptions:
          mode:
            description:
            - Interface mode
            choices: ['port_channel_st']
            type: str
            required: true
          mtu:
            description:
            - Interface MTU.
            type: str
            choices: ['default', 'jumbo']
            default: 'jumbo'
          members:
            description:
            - Member interfaces that are part of this FEX
            type: list
            elements: str
            required: true
          cmds:
            description:
            - Commands to be included in the configuration under this interface
            type: list
            elements: str
            default: []
          description:
            description:
            - Description of the FEX interface
            type: str
            default: ""
          po_description:
            description:
            - Description of the port-channel which is part of the FEX interface
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
          enable_netflow:
            description:
            - Flag to enable netflow.
            type: bool
            default: false
          netflow_monitor:
            description:
            - Name of netflow monitor. This parameter is required if "enable_netflow" is True.
            type: str
            default: ""
      profile_aa_fex:
        description:
        - Though the key shown here is 'profile_aa_fex' the actual key to be used in playbook
          is 'profile'. The key 'profile_aa_fex' is used here to logically segregate the interface
          objects applicable for this profile
        - Object profile which must be included for active-active FEX inetrface configurations.
        suboptions:
          description:
            description:
            - Description of the FEX interface
            type: str
            default: ""
          mode:
            description:
            -  Interface mode
            choices: ['port_channel_aa']
            type: str
            required: true
          peer1_members:
            description:
            - Member interfaces that are part of this port channel on first peer
            type: list
            elements: str
            required: true
          peer2_members:
            description:
            - Member interfaces that are part of this port channel on second peer
            type: list
            elements: str
            required: true
          mtu:
            description:
            - Interface MTU
            type: str
            choices: ['default', 'jumbo']
            default: 'jumbo'
          peer1_cmds:
            description:
            - Commands to be included in the configuration under this interface of first peer
            type: list
            elements: str
            default: []
          peer2_cmds:
            description:
            - Commands to be included in the configuration under this interface of second peer
            type: list
            elements: str
            default: []
          peer1_po_description:
            description:
            - Description of the port-channel interface of first peer
            type: str
            default: ""
          peer2_po_description:
            description:
            - Description of the port-channel interface of second peer
            type: str
            default: ""
          admin_state:
            description:
            - Administrative state of the interface
            type: bool
            default: true
          enable_netflow:
            description:
            - Flag to enable netflow.
            type: bool
            default: false
          netflow_monitor:
            description:
            - Name of netflow monitor. This parameter is required if "enable_netflow" is True.
            type: str
            default: ""
      profile_breakout:
        description:
        - Though the key shown here is 'profile_breakout' the actual key to be used in playbook
          is 'profile'. The key 'profile_breakout' is used here to logically segregate the interface
          objects applicable for this profile
        - "Interface must be parent interface. Ex: Ethernet1/49. Short name is not supported."
        suboptions:
          map:
            description:
            - type of breakout
            type: str
            required: true
            choices: ["10g-4x", "25g-4x", "50g-2x", "50g-4x", "100g-2x", "100g-4x", "200g-2x"]
"""

EXAMPLES = """

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
    # both registered generic-binding-registry fields. Without a supported patch/ND release
    # context, the module rejects this whole task before any configuration/deployment call
    # -- there is no product default that enables these fields. See the patch_version
    # option documentation for the version/floor/migration contract.
    patch_version: "4.3.1.0175006017"
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

# Private VLAN on a regular port-channel (int_port_channel_pvlan_host, NDFC 12; explicit physical member lists)

- name: Create a port-channel in PVLAN host mode with one administratively down member
  cisco.dcnm.dcnm_interface:
    fabric: "{{ ansible_fabric }}"
    state: replaced
    config:
      - name: po10
        type: pc
        switch:
          - "{{ ansible_switch1 }}"
        deploy: true
        profile:
          mode: pvlan
          pvlan_mode: host
          members:
            - Ethernet1/7
          pc_mode: active
          admin_state: false
          pvlan_association:
            - primary_vlan: 2210
              secondary_vlan: 2212

- name: Create a port-channel in PVLAN host mode whose member is already administratively up (it joins and stays up)
  cisco.dcnm.dcnm_interface:
    fabric: "{{ ansible_fabric }}"
    state: merged
    config:
      - name: po11
        type: pc
        switch:
          - "{{ ansible_switch1 }}"
        deploy: true
        profile:
          mode: pvlan
          pvlan_mode: host
          members:
            - Ethernet1/8               # int_trunk_host with ADMIN_STATE true: no shutdown before or after the join
          admin_state: false            # the port-channel's own state; it does not change the member's
          pvlan_association:
            - primary_vlan: 2210
              secondary_vlan: 2212
# Deleting po11 later releases its member to the fabric's host interface default (HOST_INTF_ADMIN_STATE).

- name: Set companion controls of that port-channel (NOT LIVE TESTED; the LLDP and spanning-tree fields are registered)
  cisco.dcnm.dcnm_interface:
    fabric: "{{ ansible_fabric }}"
    state: merged
    patch_version: "4.3.1.0175006017"   # required by disable_lldp_transmit and spanning_tree_port_type only
    config:
      - name: po10
        type: pc
        switch:
          - "{{ ansible_switch1 }}"
        deploy: true
        profile:
          mode: pvlan
          pvlan_mode: host
          enable_cdp: false                 # native: reaches the member as 'no cdp enable'
          lacp_port_priority: 100           # native: member 'lacp port-priority 100'
          queuing_policy: QUEUING_POLICY_1  # native: Po 'service-policy type queuing output ...'
          disable_lldp_transmit: true       # registered: member 'no lldp transmit'
          port_type_fast: false             # required with a spanning-tree port type other than 'no'
          spanning_tree_port_type: network  # registered: Po 'spanning-tree port type network'

- name: Delete that port-channel (its member is released to the fabric's host interface default)
  cisco.dcnm.dcnm_interface:
    fabric: "{{ ansible_fabric }}"
    state: deleted
    config:
      - name: po10
        switch:
          - "{{ ansible_switch1 }}"
        deploy: true

# Private VLAN on a vPC (int_vpc_pvlan_host, NDFC 12; explicit members per peer, optional peer1_pcid/peer2_pcid)

- name: Create a vPC in PVLAN host mode (peer1_* belong to the first switch, peer2_* to the second)
  cisco.dcnm.dcnm_interface:
    fabric: "{{ ansible_fabric }}"
    state: merged
    config:
      - name: vpc10
        type: vpc
        switch:
          - "{{ ansible_switch1 }}"
          - "{{ ansible_switch2 }}"
        deploy: true
        profile:
          mode: pvlan
          pvlan_mode: host
          peer1_members:
            - Ethernet1/7
          peer2_members:
            - Ethernet1/8
          peer1_pcid: 10
          peer2_pcid: 10
          admin_state: false
          pvlan_association:
            - primary_vlan: 2210
              secondary_vlan: 2212

- name: Create a vPC in PVLAN promiscuous mode (a single primary VLAN)
  cisco.dcnm.dcnm_interface:
    fabric: "{{ ansible_fabric }}"
    state: merged
    config:
      - name: vpc11
        type: vpc
        switch:
          - "{{ ansible_switch1 }}"
          - "{{ ansible_switch2 }}"
        deploy: true
        profile:
          mode: pvlan
          pvlan_mode: promiscuous
          peer1_members:
            - Ethernet1/9
          peer2_members:
            - Ethernet1/9
          peer1_pcid: 11
          peer2_pcid: 11
          admin_state: false
          pvlan_mapping:
            - primary_vlan: 2210
              secondary_vlans: "2211-2212"

- name: Create a vPC in PVLAN trunk promiscuous mode with per-peer native/allowed VLANs
  cisco.dcnm.dcnm_interface:
    fabric: "{{ ansible_fabric }}"
    state: merged
    config:
      - name: vpc12
        type: vpc
        switch:
          - "{{ ansible_switch1 }}"
          - "{{ ansible_switch2 }}"
        deploy: true
        profile:
          mode: pvlan
          pvlan_mode: trunk promiscuous
          peer1_members:
            - Ethernet1/10
          peer2_members:
            - Ethernet1/10
          peer1_pcid: 12
          peer2_pcid: 12
          admin_state: false
          pvlan_mapping:
            - primary_vlan: 2210
              secondary_vlans: "2211-2212"
            - primary_vlan: 2410
              secondary_vlans: "2412"
          peer1_native_vlan: "2301"
          peer2_native_vlan: "2301"
          peer1_allowed_vlans: "2301"
          peer2_allowed_vlans: "2301"

- name: Create a vPC in PVLAN trunk secondary mode (both members must ALREADY be prepared as access or routed ports; up or down)
  cisco.dcnm.dcnm_interface:
    fabric: "{{ ansible_fabric }}"
    state: merged
    config:
      - name: vpc13
        type: vpc
        switch:
          - "{{ ansible_switch1 }}"
          - "{{ ansible_switch2 }}"
        deploy: true
        profile:
          mode: pvlan
          pvlan_mode: trunk secondary
          peer1_members:
            - Ethernet1/11
          peer2_members:
            - Ethernet1/11
          peer1_pcid: 13
          peer2_pcid: 13
          admin_state: false
          pvlan_association:
            - primary_vlan: 2210
              secondary_vlan: 2212
          peer1_native_vlan: "2301"
          peer2_native_vlan: "2301"
          peer1_allowed_vlans: "2301"
          peer2_allowed_vlans: "2301"

- name: Delete that vPC (both peers verified; each member released to the fabric's host interface default, corrected only if needed)
  cisco.dcnm.dcnm_interface:
    fabric: "{{ ansible_fabric }}"
    state: deleted
    config:
      - name: vpc10
        type: vpc
        switch:
          - "{{ ansible_switch1 }}"
          - "{{ ansible_switch2 }}"
        deploy: true

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

# OSPF BFD and passive on a loopback and a subinterface (SMU 4.3.1.0175006017). The boolean spelling keeps working:
# ospf_bfd: true is enable; ospf_bfd: false is no_change (no local override), not an explicit disable.
- name: Enable OSPF BFD with the boolean alias and set passive explicitly
  cisco.dcnm.dcnm_interface:
    fabric: "{{ fabric }}"
    state: merged
    patch_version: "4.3.1.0175006017"
    config:
      - name: lo120
        type: lo
        switch: ["{{ switch_ip }}"]
        profile:
          mode: lo
          enable_ospf: true
          ospf_tag: UNDERLAY
          ospf_area_id: 0.0.0.0
          ospf_bfd: true              # same as ospf_bfd_mode: enable
      - name: eth1/20.100
        type: sub_int
        switch: ["{{ switch_ip }}"]
        profile:
          mode: subint
          vlan: 100
          ipv4_addr: 192.0.2.1
          ipv4_mask_len: 30
          enable_ospf: true
          ospf_tag: UNDERLAY
          ospf_area_id: 0.0.0.0
          ospf_bfd_mode: disable      # explicit "ip ospf bfd disable"; there is no boolean for it
          ospf_passive_mode: no_passive

# Fields added by SMU 4.3.1.0175006017 (NOT LIVE TESTED). Omitting them under merged keeps the controller value;
# under replaced or overridden an omitted value returns to the template default.
- name: Routed, access and subinterface fields of SMU 4.3.1.0175006017
  cisco.dcnm.dcnm_interface:
    fabric: "{{ fabric }}"
    state: merged
    patch_version: "4.3.1.0175006017"
    config:
      - name: eth1/21
        type: eth
        switch: ["{{ switch_ip }}"]
        profile:
          mode: routed
          ipv4_addr: 192.0.2.5
          ipv4_mask_len: 30
          enable_cdp: false                           # "no cdp enable"
          enable_evpn_multisite_dci_tracking: true    # "evpn multisite dci-tracking"
          enable_ospf: true
          ospf_tag: UNDERLAY
          ospf_area_id: 0.0.0.0
          ospf_retransmit_interval: 10                # requires enable_ospf; 5 renders nothing
      - name: eth1/22
        type: eth
        switch: ["{{ switch_ip }}"]
        profile:
          mode: access
          access_vlan: 100
          logging_event_port_link_status: true        # "logging event port link-status"
      - name: eth1/20.101
        type: sub_int
        switch: ["{{ switch_ip }}"]
        profile:
          mode: subint
          vlan: 101
          ipv4_addr: 192.0.2.9
          ipv4_mask_len: 30
          enable_pim_bfd_instance: true               # "ip pim bfd-instance"
"""

import collections
import copy
import inspect
import ipaddress
import json
import logging
import re
import sys
import time
from decimal import Decimal, InvalidOperation


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.validation import check_type_bool
from ansible.module_utils.connection import ConnectionError as AnsibleConnectionError
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_get_bulk_api_support,
    dcnm_send,
    get_fabric_inventory_details,
    get_fabric_details,
    dcnm_get_ip_addr_info,
    validate_list_of_dicts,
    get_ip_sn_dict,
    dcnm_version_supported,
    find_dict_in_list_by_key_value,
)
from ..module_utils.common.log_v2 import Log

#
# The parent whose full HAVE nvPair set was observed and classified, so the generic
# same-parent carry-forward is scoped to it. Named for the parent, not for the OSPF-MD
# feature that used to be the reason for looking at it.
LOOPBACK_CARRY_FORWARD_PARENT = "int_fabric_loopback_11_1"

# Profile keys withdrawn with the fabric-loopback OSPF-auth capability.
#
# On a fabric loopback, OSPF authentication is UNDERLAY authentication and fabricSettings owns
# it: the template gates the whole block on the fabric's link-state protocol, reads
# OSPF_AUTH_ENABLE / OSPF_AUTH_KEY_ID / OSPF_AUTH_KEY from the fabric, and a keychain fabric
# setting deletes whatever an interface value created. Configuring it per loopback is not part
# of the product.
#
# They are REJECTED rather than dropped from the spec and ignored. Silently accepting intent and
# discarding it is the worst of the three options: the playbook looks applied, the controller
# never hears about it, and nothing tells the operator. The message names the fabric setting
# that does own the feature.
RETIRED_LOOPBACK_OSPF_AUTH_KEYS = {
    "enable_ospf_auth_message_digest": "OSPF_AUTH_ENABLE",
    "ospf_auth_key_id": "OSPF_AUTH_KEY_ID",
    "ospf_auth_key": "OSPF_AUTH_KEY",
}

# Profile keys whose VALUE is key material, on ANY interface type.
#
# WHY THIS IS NOT PART OF THE REJECTION ABOVE, AND MUST NOT BE
#
# Ansible serialises the module's arguments into `invocation.module_args` on EVERY result --
# successes, failures, and argument-spec errors alike. A value only stays out of that if it was
# registered in `module.no_log_values` BEFORE the result is formatted. So key material has to be
# registered on arrival, not at the point some particular check happens to object to it.
#
# A first attempt scrubbed inside the loopback rejection loop, which failed in three measured
# ways, all with the real serialiser: the loop rejects on the FIRST withdrawn key it meets and
# `ospf_auth_key` is the third, so 'key_id + key' and 'boolean + key' both leaked; and it stops
# at the first offending interface, so a second interface carrying the key leaked too. Only the
# case where the key was the sole offender was covered.
#
# The lesson generalises past this rejection. `ospf_auth_key` is about to become a LEGITIMATE
# field on int_routed_host, int_subif and int_vlan -- the withdrawn global validators were
# removed precisely so it could be. On those parents nothing rejects it, so a rejection-time
# scrub would protect it exactly where it is refused and not at all where it is accepted, which
# is backwards. Registration therefore happens once, on arrival, for the whole config, and is
# indifferent to what any later check decides.
# DERIVED FROM THE REGISTRY, not written here. A binding marked `no_log` is protected by that
# fact alone; nobody has to remember to add its name to a second list, and there is no way to
# register a secret binding and leave it unprotected.
#
# Union, not intersection, with the withdrawn keys. gie_no_log_profile_keys() only knows about
# keys that are still registered somewhere, and `ospf_auth_key` happens to be -- but the
# withdrawn set must contribute independently of that coincidence. A key this module refuses is
# still key material, and a refusal is still a result with invocation.module_args attached.
RETIRED_LOOPBACK_OSPF_AUTH_SECRETS = frozenset({"ospf_auth_key"})


# The keychain was never a dcnm_interface field, and it is the reason the other three stopped
# being one: ``ospfAuthKeychainName`` is written by fabricSettings, which overwrites the interface
# parameter in the parent DSL. An interface value for it is therefore not merely redundant, it is
# unreachable -- the fabric wins every time.
#
# These spellings are rejected for the same reason the withdrawn keys above are, and NOT for the
# same reason they once were. The old rejection said "not supported yet"; this one says "the
# fabric owns it". Without an explicit rejection they fall through to lo_prof_spec, which does not
# declare them, and are dropped in silence -- a playbook that looks applied and a controller that
# never heard about it.
#
# The message deliberately does not name a fabricSettings field. The interface-side nvPair name is
# verified; the fabric-side one is not, and pointing an operator at a field that may not exist is
# worse than telling them which layer to look in.
OSPF_AUTH_KEYCHAIN_PROFILE_KEYS = (
    "ospf_auth_keychain_name",
    "ospf_auth_keychain",
    "ospfAuthKeychainName",
)

# Additive registry-driven binding engine. Consumes the packaged static
# binding table only; additive; explicit-only; NDFC executes template effects. The engine owns
# binding resolution + type validation + supported-version parent-nvPair transport for every
# registered binding; the OSPF-MD capability/HAVE reconciliation stays a narrow compat hook.
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
    GieBindingError,
    gie_all_registered_keys,
    gie_extend_prof_spec,
    gie_contribute_nvpairs,
    gie_invalid_parent_key,
    gie_nvpair_keymap,
    gie_normalize_ospf_aliases,
    gie_carry_forward_bindings,
    gie_withdrawal_action,
    gie_binding_inert,
    gie_inert_gate_nvpairs,
    gie_dependency_plan,
    gie_binding_is_owned_elsewhere,
    gie_patch_supported,
    GIE_READONLY_METADATA_NVPAIRS,
    GIE_WITHDRAW_NONE,
    GIE_WITHDRAW_RESET,
    GIE_WITHDRAW_UNSUPPORTED,
    GIE_WITHDRAW_UNCLASSIFIED,
    gie_describe_value_type,
    gie_fabric_owned_carry_forward,
    gie_have_carry_forward_nvpairs,
    gie_no_log_profile_keys,
    gie_validate_binding_value,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    resolve_binding,
    resolve_by_nvpair as gie_resolve_by_nvpair,
    string_compare as gie_string_compare,
)
# Native standalone Ethernet PVLAN (int_pvlan_host). Pure helpers; transport stays here.
from ansible_collections.cisco.dcnm.plugins.module_utils.interface_pvlan import (
    PROFILE_KEYS as PVLAN_PROFILE_KEYS,
    normalize_single_value_ranges as pvlan_normalize_single_value_ranges,
    PVLAN_POLICY,
    PvlanError,
    preview_entry as pvlan_preview_entry,
    reconcile as pvlan_reconcile,
    render as pvlan_render,
    split_blocks as pvlan_split_blocks,
    validate_raw_profile as pvlan_validate_raw_profile,
    pairs_from_wire as pvlan_pairs_from_wire,
    native_equal as pvlan_native_equal,
    allowed_equal as pvlan_allowed_equal,
    classify_secondary as pvlan_classify_secondary,
    template_declared_names as pvlan_template_declared_names,
    modify_outcome_problems as pvlan_modify_outcome_problems,
    deploy_outcome as pvlan_deploy_outcome,
    assess_target as pvlan_assess_target,
    transition_vocabulary as pvlan_transition_vocabulary,
    VOCABULARY_POLICIES as PVLAN_VOCABULARY_POLICIES,
    PO_VOCABULARY_POLICIES as PVLAN_PO_VOCABULARY_POLICIES,
    SUMMARY_ABSENT as PVLAN_SUMMARY_ABSENT,
    SUMMARY_KNOWN as PVLAN_SUMMARY_KNOWN,
    SUMMARY_UNKNOWN as PVLAN_SUMMARY_UNKNOWN,
    summary_mentions_policy as pvlan_summary_mentions_policy,
    summary_policy as pvlan_summary_policy,
    PO_HOST_POLICY,
    PO_MEMBER_POLICY,
    PO_PROFILE_KEYS,
    PVLAN_MODES,
    PO_NAME as PVLAN_PO_NAME,
    PO_RELEASE_METADATA as PVLAN_PO_RELEASE_METADATA,
    TRUNK_HOST_POLICY as PVLAN_TRUNK_HOST_POLICY,
    interface_stanza as pvlan_interface_stanza,
    running_po_members as pvlan_running_po_members,
    po_not_implemented as pvlan_po_not_implemented,
    reconcile_po as pvlan_reconcile_po,
    po_member_nvpairs as pvlan_po_member_nvpairs,
    po_member_baseline_problems as pvlan_po_member_baseline_problems,
    po_host_nvpairs as pvlan_po_host_nvpairs,
    normalize_member_list as pvlan_normalize_member_list,
    VPC_HOST_POLICY,
    VPC_PO_POLICY,
    VPC_NAME,
    VPC_PROFILE_KEYS,
    VPC_VOCABULARY_POLICIES as PVLAN_VPC_VOCABULARY_POLICIES,
    vpc_id,
    vpc_not_implemented as pvlan_vpc_not_implemented,
    vpc_pair_view as pvlan_vpc_pair_view,
    vpc_po_name as pvlan_vpc_po_name,
    vpc_host_nvpairs as pvlan_vpc_host_nvpairs,
    reconcile_vpc as pvlan_reconcile_vpc,
    vpc_leg_po_nv as pvlan_vpc_leg_po_nv,
    vpc_leg_models as pvlan_vpc_leg_models,
    vpc_leg_cli_changes as pvlan_vpc_leg_cli_changes,
    vpc_combine as pvlan_vpc_combine,
    vpc_response_class as pvlan_vpc_response_class,
    vpc_child_differences as pvlan_vpc_child_differences,
    vpc_same as pvlan_vpc_same,
    po_intent_same as pvlan_po_intent_same,
    speed_duplex_combined_change as pvlan_speed_duplex_combined_change,
    SPEED_DUPLEX_COMBINED_MESSAGE as pvlan_speed_duplex_combined_message_text,
    vpc_transition_problems as pvlan_vpc_transition_problems,
    vpc_member_differences as pvlan_vpc_member_differences,
    vpc_released_member_differences as pvlan_vpc_released_member_differences,
    po_force_unmeasured as pvlan_po_force_unmeasured,
    po_markdelete_outcome_problems as pvlan_po_markdelete_outcome_problems,
    PO_MARKDELETE_MESSAGE as PVLAN_PO_MARKDELETE_MESSAGE,
    po_released_member_restoration_delta as pvlan_po_released_member_restoration_delta,
    po_marked_deleted_problem as pvlan_po_marked_deleted_problem,
    po_member_force_withdrawal as pvlan_po_member_force_withdrawal,
    po_member_canonical as pvlan_po_member_canonical,
    PO_PREPARED_BASELINES as PVLAN_PO_PREPARED_BASELINES,
    PO_ROUTED_BASELINE_POLICY as PVLAN_PO_ROUTED_BASELINE_POLICY,
    po_routed_member_self_children as pvlan_po_routed_member_self_children,
    PO_ROUTED_RELEASE_CHILDREN_UP as PVLAN_PO_ROUTED_RELEASE_CHILDREN_UP,
    PO_ROUTED_RELEASE_CHILDREN_DOWN as PVLAN_PO_ROUTED_RELEASE_CHILDREN_DOWN,
    RELEASED_MEMBER_POLICIES as PVLAN_RELEASED_MEMBER_POLICIES,
    released_member_safety_problems as pvlan_released_member_safety_problems,
    released_member_payload as pvlan_released_member_payload,
    released_member_readback_problems as pvlan_released_member_readback_problems,
    released_member_role_expectation as pvlan_released_member_role_expectation,
    released_member_contract as pvlan_released_member_contract,
    released_member_model as pvlan_released_member_model,
    released_routed_children as pvlan_released_routed_children,
    # Companion controls of the PVLAN parents.
    PO_NATIVE_COMPANIONS as PVLAN_PO_NATIVE_COMPANIONS,
    VPC_NATIVE_COMPANIONS as PVLAN_VPC_NATIVE_COMPANIONS,
    native_companion_spec as pvlan_native_companion_spec,
    member_lacp_rate_problems as pvlan_member_lacp_rate_problems,
)
SECRET_PROFILE_KEYS = gie_no_log_profile_keys() | RETIRED_LOOPBACK_OSPF_AUTH_SECRETS

# The same secrets, spelled the way the CONTROLLER spells them.
#
# A key can reach the output without ever having been typed: NDFC returns it in a query, in the
# HAVE that a diff is computed from, and in an error that quotes the payload it rejected. None
# of those go through the playbook, so registering only what the operator wrote leaves every one
# of them in the clear.
#
# Derived, like its profile-key sibling: gie_nvpair_keymap() already translates nvPair -> profile
# key for every registered binding, so a secret binding lands here by being secret, not by being
# remembered.
SECRET_NVPAIRS = frozenset(
    nvpair for nvpair, profile_key in gie_nvpair_keymap().items()
    if profile_key in SECRET_PROFILE_KEYS
)


def json_pretty(msg):
    """
    Return a pretty-printed JSON string for logging messages
    """
    return json.dumps(msg, indent=4, sort_keys=True)


# ----------------------------------------------------------------------------- SVI address lists
# The two structured int_vlan fields. Both are native module arguments, NOT registry bindings:
# each is a list whose members are compared by identity, which the scalar engine cannot express.
#
#   public key           nvPair               element key           wire element key
#   secondary_gws        secondaryGws         gateway_ip_address    gatewayIpAddress   (A.B.C.D/P)
#   hsrp_secondary_vips  hsrpSecondaryVips    hsrp_secondary_vip    hsrpSecondaryVip   (A.B.C.D)
#
# Wire form, measured on the controller readback: compact JSON text with a wrapper object,
#     {"secondaryGws":[{"gatewayIpAddress":"192.0.2.254/24"}]}
# and the empty string for "no entries". The installed template parses the text with
# ast.literal_eval and accepts either the wrapper or a bare list; it caps each list at 16.
# The two int_vlan DHCP fields the builder emits only when non-empty (see dcnm_intf_get_svi_payload) and the vrf that hangs off server 4.
# (profile key, nvPair). The authoritative "no value" of all three is the empty string: it is what NDFC returns for an SVI created without
# them and what servers 1-3 already write on a reset.
SVI_DHCP4_FIELDS = (
    ("dhcp_server_addr4", "dhcpServerAddr4"),
    ("vrf_dhcp4", "vrfDhcp4"),
    ("dhcp_relay_src_intf", "DHCP_RELAY_SRC_INTF"),
)
# Template compatibility. The int_vlan parent template names the fourth server and the relay source differently in two bodies (sha256 of the
# full bodies; verbatim declaration excerpts are the oracle of tests/unit/modules/dcnm/test_dcnm_intf_svi_dhcp4_template_compat.py):
#   0efb09af7f837b30b7a5dde37e7d4e7604fdd2fc4ca92ff6338e227802fde1a3  dhcpServerAddr4      DHCP_RELAY_SRC_INTF       (the legacy tuple above)
#   f32ef5863d8757759154f5992eba9f009ecdf68425f8be9d58e5a0bb416313e4  dhcpServerAddress4   dhcpRelaySourceInterface  (the tuple below)
# vrfDhcp4 is unchanged. NDFC reports 12.6.0.267 for both bodies, so the controller version cannot choose; the body that carries the activated SMU
# 4.3.1.0175006011 (the ND upgrade history lists it with fixDetails naming dcnm-configtemplate) is f32ef586. SMU 4.3.1.0175006017, the only SMU this
# candidate supports, declares the same two names (read from its int_vlan body), and the existing patch_version
# capability (gie_patch_supported: that SMU, or a numeric ND release >= 4.4.1 -- the latter is an assumption of the existing selector, not an
# observation) is what already selects the SMU-schema names of the registered int_vlan fields. The same selector chooses these names. A missing or
# unapproved patch keeps the legacy names, as for every native field; the module never sends both and never probes the controller.
SVI_DHCP4_FIELDS_SMU = (
    ("dhcp_server_addr4", "dhcpServerAddress4"),
    ("vrf_dhcp4", "vrfDhcp4"),
    ("dhcp_relay_src_intf", "dhcpRelaySourceInterface"),
)


def svi_dhcp4_fields(patch_version=None):
    """(profile key, nvPair) of the three SVI DHCP4 fields for the int_vlan body that ``patch_version`` selects (see SVI_DHCP4_FIELDS_SMU)."""
    return SVI_DHCP4_FIELDS_SMU if gie_patch_supported(patch_version) else SVI_DHCP4_FIELDS


SVI_ADDRESS_LIST_MAX = 16
SVI_ADDRESS_LISTS = {
    "secondary_gws": {
        "nvpair": "secondaryGws",
        "element": "gateway_ip_address",
        "wire_element": "gatewayIpAddress",
        "wire_element_aliases": ("gatewayIpAddress",),
        "wire_wrappers": ("secondaryGws", "secondaryGWs"),
        "with_prefix": True,
    },
    "hsrp_secondary_vips": {
        "nvpair": "hsrpSecondaryVips",
        "element": "hsrp_secondary_vip",
        "wire_element": "hsrpSecondaryVip",
        "wire_element_aliases": ("hsrpSecondaryVip", "HSRP_SECONDARY_VIP"),
        "wire_wrappers": ("hsrpSecondaryVips", "HSRP_SECONDARY_VIPS"),
        "with_prefix": False,
    },
}


class SviAddressListError(ValueError):
    """An SVI address list that is malformed, in the playbook or in the controller readback."""


def svi_address_normalize(key, value):
    """Return (identity, canonical) for one list element value, or raise SviAddressListError.

    The identity is the IPv4 address. For secondary_gws the canonical form keeps the host bits
    and the prefix ("192.0.2.254/24"); the prefix is data, not identity, so an explicit new prefix
    for the same address is an update of that entry.
    """
    if not isinstance(value, str) or value == "":
        raise SviAddressListError(
            "{0}: element value must be a non-empty string, got {1!r}".format(key, value)
        )
    if SVI_ADDRESS_LISTS[key]["with_prefix"]:
        parts = value.split("/")
        if len(parts) != 2 or not re.match(r"^[0-9]{1,2}$", parts[1]):
            raise SviAddressListError(
                "{0}: {1!r} is not in IPv4 address/prefix format".format(key, value)
            )
        prefix = int(parts[1])
        if str(prefix) != parts[1] or not 1 <= prefix <= 32:
            raise SviAddressListError(
                "{0}: {1!r} has a prefix outside 1-32".format(key, value)
            )
        address = parts[0]
    else:
        address = value
        prefix = None
    try:
        parsed = ipaddress.IPv4Address(address)
    except ValueError:
        raise SviAddressListError(
            "{0}: {1!r} is not a valid IPv4 address".format(key, value)
        )
    identity = str(parsed)
    if identity != address:
        raise SviAddressListError(
            "{0}: {1!r} is not in canonical IPv4 notation".format(key, value)
        )
    canonical = identity if prefix is None else "{0}/{1}".format(identity, prefix)
    return identity, canonical


def svi_address_list_from_input(key, value):
    """Validate a playbook list and return [(identity, canonical), ...] in input order.

    Rejects null, non-list values, non-dict elements, unknown or missing element keys,
    invalid addresses, duplicate identities and more than SVI_ADDRESS_LIST_MAX entries.
    """
    element = SVI_ADDRESS_LISTS[key]["element"]
    if value is None:
        raise SviAddressListError(
            "{0} must be a list; null is not accepted. Omit the key to leave the list "
            "untouched under merged, or give [] for an explicit empty list".format(key)
        )
    if not isinstance(value, list):
        raise SviAddressListError(
            "{0} must be a list of dictionaries, got {1}".format(key, type(value).__name__)
        )
    if len(value) > SVI_ADDRESS_LIST_MAX:
        raise SviAddressListError(
            "{0} supports at most {1} entries, got {2}".format(
                key, SVI_ADDRESS_LIST_MAX, len(value))
        )
    entries = []
    seen = {}
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise SviAddressListError(
                "{0}[{1}] must be a dictionary with the key {2!r}".format(key, index, element)
            )
        unknown = sorted(str(k) for k in item if k != element)
        if unknown:
            raise SviAddressListError(
                "{0}[{1}] has unsupported keys {2}; the only key is {3!r}".format(
                    key, index, unknown, element)
            )
        if element not in item:
            raise SviAddressListError(
                "{0}[{1}] is missing the required key {2!r}".format(key, index, element)
            )
        identity, canonical = svi_address_normalize(key, item[element])
        if identity in seen:
            raise SviAddressListError(
                "{0} lists the address {1} more than once ({2!r} and {3!r})".format(
                    key, identity, seen[identity], canonical)
            )
        seen[identity] = canonical
        entries.append((identity, canonical))
    return entries


def svi_address_list_from_wire(key, raw):
    """Parse the nvPair text into [(identity, canonical), ...].

    "" is the measured empty representation. Anything else must be JSON with the wrapper or a
    bare list, exactly as the template accepts it. A malformed value raises: it is never read
    as an empty list, because that would turn a parse failure into a withdrawal.
    """
    meta = SVI_ADDRESS_LISTS[key]
    if raw == "":
        return []
    if not isinstance(raw, str):
        raise SviAddressListError(
            "{0}: unrecognized controller representation {1!r}".format(meta["nvpair"], raw)
        )
    try:
        obj = json.loads(raw)
    except ValueError:
        raise SviAddressListError(
            "{0}: controller value is not valid JSON".format(meta["nvpair"])
        )
    if isinstance(obj, dict):
        wrappers = [w for w in meta["wire_wrappers"] if w in obj]
        if len(obj) != 1 or len(wrappers) != 1:
            raise SviAddressListError(
                "{0}: unexpected wrapper keys {1}".format(meta["nvpair"], sorted(obj))
            )
        obj = obj[wrappers[0]]
    if not isinstance(obj, list):
        raise SviAddressListError(
            "{0}: controller value is not a list".format(meta["nvpair"])
        )
    if len(obj) > SVI_ADDRESS_LIST_MAX:
        raise SviAddressListError(
            "{0}: controller value has more than {1} entries".format(
                meta["nvpair"], SVI_ADDRESS_LIST_MAX)
        )
    entries = []
    seen = set()
    for item in obj:
        if not isinstance(item, dict):
            raise SviAddressListError(
                "{0}: controller list element is not an object".format(meta["nvpair"])
            )
        keys = [k for k in meta["wire_element_aliases"] if k in item]
        if len(item) != 1 or len(keys) != 1:
            raise SviAddressListError(
                "{0}: unexpected element keys {1}".format(meta["nvpair"], sorted(item))
            )
        if item[keys[0]] == "":
            # The template skips empty elements; they configure nothing.
            continue
        identity, canonical = svi_address_normalize(key, item[keys[0]])
        if identity in seen:
            raise SviAddressListError(
                "{0}: controller value repeats {1}".format(meta["nvpair"], identity)
            )
        seen.add(identity)
        entries.append((identity, canonical))
    return entries


def svi_address_list_to_wire(key, entries):
    """Serialize [(identity, canonical), ...] in the measured wire form; [] -> ""."""
    meta = SVI_ADDRESS_LISTS[key]
    if not entries:
        return ""
    return json.dumps(
        {meta["wire_wrappers"][0]: [{meta["wire_element"]: c} for _i, c in entries]},
        separators=(",", ":"),
    )


def svi_address_list_desired(state, requested, have):
    """The effective list for one state.

    requested is None when the key was omitted. merged: omitted or [] preserves HAVE, a
    nonempty list is a union with upsert by identity (an existing entry keeps its position).
    replaced/overridden: exact requested membership; omitted or [] removes every entry.
    """
    if state == "merged":
        if not requested:
            return list(have)
        result = list(have)
        position = dict((identity, index) for index, (identity, _c) in enumerate(result))
        for identity, canonical in requested:
            if identity in position:
                result[position[identity]] = (identity, canonical)
            else:
                position[identity] = len(result)
                result.append((identity, canonical))
        return result
    return list(requested or [])


def svi_address_list_same(left, right):
    """Membership equality; order is not a functional difference."""
    return dict(left) == dict(right)


def _read_reason_key(stage, serial):
    authority = DcnmIntf._dcnm_intf_authority_key(serial)
    return (stage, authority.casefold()) if authority else None


def _read_reasons(obj):
    # Stored in the instance dict so it also works on objects built without __init__.
    return obj.__dict__.setdefault("read_failure_reasons", {})


def read_reason_note(obj, stage, serial, reason):
    """Diagnostics only: record why this read of `stage` for this serial is not authoritative (controlled text)."""
    key = _read_reason_key(stage, serial)
    if key is not None:
        _read_reasons(obj)[key] = reason


def read_reason_note_detail(obj, serial, reason):
    """A detail read that was actually attempted and rejected: its reason, and the serial's last real failure (what spent the budget)."""
    read_reason_note(obj, "detail", serial, reason)
    read_reason_note(obj, "detail-last-failure", serial, reason)


def read_reason_clear(obj, stage, serial):
    key = _read_reason_key(stage, serial)
    if key is not None:
        _read_reasons(obj).pop(key, None)


def read_reason_get(obj, stage, serial):
    key = _read_reason_key(stage, serial)
    return _read_reasons(obj).get(key) if key is not None else None


def read_reason_suffix(obj, stage, serial):
    reason = read_reason_get(obj, stage, serial)
    return " ({0})".format(reason) if reason else ""


def response_failure_reason(resp, attempts):
    """Controlled reason for a GET answer that is not a usable RETURN_CODE 200 envelope: the observed numeric status, or the
    category of what came back. Never the body, a message or a header."""
    if resp is None:
        return "no response (transport error) after {0} attempt(s)".format(attempts)
    if isinstance(resp, dict):
        code = resp.get("RETURN_CODE")
        # The readers accept `RETURN_CODE == 200`; the same comparison here, so classifying a failure never tightens what they accept.
        if code == 200:
            return "the response DATA is not a list" if not isinstance(resp.get("DATA"), list) else None
        if isinstance(code, int) and not isinstance(code, bool):
            return "HTTP {0} after {1} attempt(s)".format(code, attempts)
        return "the response has no integer status"
    if resp == []:
        return "the response body is empty"
    return "the response is not an object"


def pvlan_lifecycle_note(obj, attr, key, value):
    """Bookkeeping written while a diff is built: the dict `attr` of `obj` gets key -> value. Module level so the planning code
    also runs on minimal instances that only carry the attributes of the generic sweep."""
    store = getattr(obj, attr, None)
    if store is None:
        store = {}
        setattr(obj, attr, store)
    store[key] = value


def pvlan_record_conventional_releases(obj, payloads, resp):
    """The physical members that THIS invocation's confirmed interface update released from a CONVENTIONAL (non-PVLAN)
    port-channel or vPC: {physical serial: {member (normalized): port-channel id}}. NaC sends conventional and PVLAN member removals in one
    `dcnm_interface` call; the controller releases a conventional member with pending (`no channel-group N ...` plus the host default) that
    the PVLAN pre-deploy gate would otherwise call foreign.

    Derived ONLY from: the authoritative pre-state of that aggregate read by this run (obj.have) -- a removed member is no longer in WANT;
    the payload actually sent (its member list for the leg); and the controller's per-item SUCCESS for that aggregate (`resp`; None for the
    individual update API, whose every answer was already required OK). A vPC member is mapped to the physical serial of ITS peer (PEERn
    -> n-th serial of the pair). PVLAN targets, aggregates without a member list in the payload, unconfirmed items and anything not read
    from the controller contribute nothing. Stored on obj.pvlan_invocation_releases for the gates of this invocation only."""
    released = {}
    targets = getattr(obj, "pvlan_targets", None) or {}
    have_all = getattr(obj, "have", None) or []
    for payload in payloads or []:
        if not isinstance(payload, dict) or payload.get("policy") in (PVLAN_POLICY, PO_HOST_POLICY, VPC_HOST_POLICY):
            continue
        intf = (payload.get("interfaces") or [{}])[0]
        name, sno, nv = str(intf.get("ifName", "")), str(intf.get("serialNumber", "")), intf.get("nvPairs") or {}
        itype = intf.get("interfaceType") or payload.get("interfaceType")
        if (sno, name.lower()) in targets:
            continue
        if itype == "INTERFACE_PORT_CHANNEL":
            number = re.match(r"^port-channel([0-9]+)$", name.lower())
            legs = [(sno, "MEMBER_INTERFACES", number.group(1) if number else None)]
        elif itype == "INTERFACE_VPC":
            parts = sno.split("~")
            if len(parts) != 2:
                continue
            legs = [(parts[i], "PEER%d_MEMBER_INTERFACES" % (i + 1), str(nv.get("PEER%d_PCID" % (i + 1), "") or "").strip() or None) for i in (0, 1)]
        else:
            continue
        if resp is not None and pvlan_modify_outcome_problems(resp, [(sno, name)]):
            continue  # this aggregate's update is not confirmed by the controller
        have = [h for h in have_all if isinstance(h, dict)
                and str(((h.get("interfaces") or [{}])[0]).get("serialNumber", "")) == sno
                and str(((h.get("interfaces") or [{}])[0]).get("ifName", "")).lower() == name.lower()]
        if len(have) != 1:
            continue
        have_nv = ((have[0].get("interfaces") or [{}])[0]).get("nvPairs") or {}
        for serial, key, pcid in legs:
            if key not in nv or not pcid:
                continue  # the leg's members are not part of what was sent, or its port-channel id is unknown
            before, unresolved_before = pvlan_normalize_member_list(have_nv.get(key))
            after, unresolved_after = pvlan_normalize_member_list(nv.get(key))
            if unresolved_before or unresolved_after:
                continue
            for member in sorted(set(before) - set(after)):
                released.setdefault(serial, {})[member] = pcid
            # A member the same confirmed update ADDED joins that channel-group (pvlan_invocation_owned: join form)
            for member in sorted(set(after) - set(before)):
                joins = getattr(obj, "pvlan_invocation_joins", None) or {}
                joins.setdefault(serial, {})[member] = pcid
                obj.pvlan_invocation_joins = joins
    store = getattr(obj, "pvlan_invocation_releases", None) or {}
    for serial, members in released.items():
        store.setdefault(serial, {}).update(members)
    obj.pvlan_invocation_releases = store
    return released


def pvlan_record_conventional_modified(obj, payloads, resp):
    """The interfaces that THIS invocation's confirmed bulk interface update MODIFIED outside the PVLAN targets:
    {physical serial: {interface name lower}}. NaC sends, in one `dcnm_interface` call, the modification of conventional interfaces (a
    port-channel's own fields, a loopback, an Ethernet, an SVI ...) together with a saved PVLAN membership removal; the confirmed update leaves
    those interfaces' own blocks in the switch pending that the PVLAN pre-deploy gate would otherwise call foreign.

    Derived ONLY from the payload actually sent and the controller's per-item SUCCESS naming that (serial, interface) in `resp` (a missing
    item, ERROR or any other outcome records nothing). A conventional vPC is recorded as each peer's child `port-channel<PEERn_PCID>` on
    the n-th serial of the pair, from the PCID that was sent (never the vPC id); a pair serial without a numeric PCID records nothing for
    that peer. PVLAN targets and policies are not recorded here (their own blocks are judged by the gate). An interface whose block this
    invocation's pre-write planning preview of the same serial (dcnm_intf_pvlan_planning_preview, when one was read) already listed as
    pending is NOT recorded: that pending predates the write. No read is made here. Stored on obj.pvlan_invocation_modified for the gates
    of this invocation only (pvlan_invocation_owned)."""
    modified = {}
    targets = getattr(obj, "pvlan_targets", None) or {}
    planning = (getattr(obj, "__dict__", None) or {}).get("pvlan_planning_previews") or {}
    before = {}
    for payload in payloads or []:
        if not isinstance(payload, dict) or payload.get("policy") in (PVLAN_POLICY, PO_HOST_POLICY, VPC_HOST_POLICY):
            continue
        for intf in payload.get("interfaces") or []:
            if not isinstance(intf, dict):
                continue
            name, sno, nv = str(intf.get("ifName", "")), str(intf.get("serialNumber", "")), intf.get("nvPairs") or {}
            if not name or not sno or (sno, name.lower()) in targets:
                continue
            if pvlan_modify_outcome_problems(resp, [(sno, name)]):
                continue  # this interface's update is not confirmed by the controller
            parts = sno.split("~")
            if len(parts) == 2:
                if (intf.get("interfaceType") or payload.get("interfaceType")) != "INTERFACE_VPC":
                    continue
                legs = [(parts[i], "port-channel%s" % str(nv.get("PEER%d_PCID" % (i + 1), "") or "").strip()) for i in (0, 1)
                        if str(nv.get("PEER%d_PCID" % (i + 1), "") or "").strip().isdigit()]
            elif len(parts) == 1:
                legs = [(sno, name.lower())]
            else:
                continue
            for serial, iname in legs:
                if serial not in before:
                    before[serial] = set()
                    if serial in planning:
                        try:
                            before[serial] = set(pvlan_split_blocks(pvlan_preview_entry(planning[serial], serial)["pendingConfig"])[0])
                        except PvlanError:
                            before[serial] = set()  # an unreadable pre-write view proves nothing either way
                if iname in before[serial]:
                    continue  # already pending before this invocation wrote: not this write's
                modified.setdefault(serial, set()).add(iname)
    store = getattr(obj, "pvlan_invocation_modified", None) or {}
    for serial, names in modified.items():
        store.setdefault(serial, set()).update(names)
    obj.pvlan_invocation_modified = store
    return modified


def pvlan_record_conventional_creation(obj, payload, resp):
    """After the confirmed creation (200/OK) of ONE CONVENTIONAL port-channel or vPC by THIS invocation, record on
    each physical serial what that creation legitimately leaves pending: each member SENT in the payload joins the new channel-group
    (obj.pvlan_invocation_joins, judged by pvlan_invocation_owned: its block must join that id) and, for a vPC, the peer's child
    `port-channel<id>` (obj.pvlan_invocation_children). A vPC leg is mapped to its peer (PEERn -> n-th serial of the pair). PVLAN targets
    and policies, other interface types, an unknown port-channel id, an unparsable member list and an unconfirmed answer record nothing.
    In memory for the gates of this invocation only."""
    if not isinstance(payload, dict) or payload.get("policy") in (PVLAN_POLICY, PO_HOST_POLICY, VPC_HOST_POLICY):
        return {}
    if not isinstance(resp, dict) or resp.get("RETURN_CODE") != 200 or resp.get("MESSAGE") != "OK":
        return {}
    intf = (payload.get("interfaces") or [{}])[0]
    name, sno, nv = str(intf.get("ifName", "")), str(intf.get("serialNumber", "")), intf.get("nvPairs") or {}
    if (sno, name.lower()) in (getattr(obj, "pvlan_targets", None) or {}):
        return {}
    itype = intf.get("interfaceType") or payload.get("interfaceType")
    if itype == "INTERFACE_PORT_CHANNEL":
        number = re.match(r"^port-channel([0-9]+)$", name.lower())
        legs = [(sno, nv.get("MEMBER_INTERFACES"), number.group(1) if number else None, False)]
    elif itype == "INTERFACE_VPC" and len(sno.split("~")) == 2:
        peers = sno.split("~")
        legs = [(peers[i], nv.get("PEER%d_MEMBER_INTERFACES" % (i + 1)), str(nv.get("PEER%d_PCID" % (i + 1), "") or "").strip() or None, True)
                for i in (0, 1)]
    else:
        return {}
    recorded = {}
    joins = getattr(obj, "pvlan_invocation_joins", None) or {}
    children = getattr(obj, "pvlan_invocation_children", None) or {}
    for serial, raw, pcid, child in legs:
        members, unresolved = pvlan_normalize_member_list(raw)
        if not pcid or not pcid.isdigit() or unresolved:
            continue
        for member in members:
            joins.setdefault(serial, {})[member] = pcid
        if child:
            children.setdefault(serial, set()).add("port-channel%s" % pcid)
        recorded[serial] = {"pcid": pcid, "members": list(members)}
    obj.pvlan_invocation_joins, obj.pvlan_invocation_children = joins, children
    return recorded


def pvlan_conventional_delete_prestate(obj, payload):
    """Immediately before ONE generic mark-delete request, the authoritative pre-state of each CONVENTIONAL port-channel /
    vPC in it: {(serial, name lower): [(physical serial, port-channel id, [members normalized])]}, from this run's controller detail of
    that aggregate (the deletion empties it, so it is read before the request). A vPC is mapped to its two PHYSICAL child port-channels
    (PEERn_PCID / PEERn_MEMBER_INTERFACES -> n-th serial of the pair). PVLAN targets, PVLAN policies, other interface types, an unknown
    port-channel id and an unparsable member list contribute nothing. Nothing is granted here: see pvlan_record_conventional_deletions."""
    out = {}
    targets = getattr(obj, "pvlan_targets", None) or {}
    for item in payload if isinstance(payload, list) else [payload]:
        if not isinstance(item, dict):
            continue
        name, sno = str(item.get("ifName", "")), str(item.get("serialNumber", ""))
        if (sno, name.lower()) in targets:
            continue
        number = re.match(r"^port-channel([0-9]+)$", name.lower())
        if number:
            itype = "INTERFACE_PORT_CHANNEL"
        elif re.match(r"^vpc[0-9]+$", name.lower()) and len(sno.split("~")) == 2:
            itype = "INTERFACE_VPC"
        else:
            continue
        detail = obj.dcnm_intf_get_intf_info(name, sno, itype)
        if not isinstance(detail, dict) or detail.get("policy") in (PVLAN_POLICY, PO_HOST_POLICY, VPC_HOST_POLICY):
            continue
        nv = ((detail.get("interfaces") or [{}])[0]).get("nvPairs") or {}
        if itype == "INTERFACE_PORT_CHANNEL":
            legs = [(sno, number.group(1), nv.get("MEMBER_INTERFACES"))]
        else:
            peers = sno.split("~")
            legs = [(peers[i], str(nv.get("PEER%d_PCID" % (i + 1), "") or "").strip(), nv.get("PEER%d_MEMBER_INTERFACES" % (i + 1)))
                    for i in (0, 1)]
        record = []
        for serial, pcid, raw in legs:
            members, unresolved = pvlan_normalize_member_list(raw)
            if pcid.isdigit() and not unresolved:
                record.append((serial, pcid, members))
        if record:
            out[(sno, name.lower())] = record
    return out


def pvlan_markdelete_batch_confirmed(resp, payload):
    """True only when the ORIGINAL answer of one generic mark-delete request (before any generic retry or "No Commands to
    execute" masking) is the measured success form -- 200/OK, DATA.message "Interface deleted successfully" -- and its `value` names
    every requested (serial, interface) exactly once and nothing else. Anything else is an unverified outcome."""
    items = payload if isinstance(payload, list) else [payload]
    if not isinstance(resp, dict) or resp.get("RETURN_CODE") != 200 or resp.get("MESSAGE") != "OK":
        return False
    data = resp.get("DATA")
    if not isinstance(data, dict) or data.get("message") != PVLAN_PO_MARKDELETE_MESSAGE or not isinstance(data.get("value"), list):
        return False
    answered = sorted((str(v.get("serialNumber", "")).casefold(), str(v.get("IfName", v.get("ifName", ""))).lower())
                      for v in data["value"] if isinstance(v, dict))
    asked = sorted((str(i.get("serialNumber", "")).casefold(), str(i.get("ifName", "")).lower()) for i in items if isinstance(i, dict))
    return len(answered) == len(data["value"]) and answered == asked


def pvlan_record_conventional_deletions(obj, payload, resp, prestate):
    """After the confirmed mark-delete of conventional aggregates in THIS invocation, record on each physical serial what that
    deletion legitimately leaves pending: the exact global withdrawal `no interface port-channel<id>` (obj.pvlan_invocation_withdrawn) and
    each pre-state member released with that id (obj.pvlan_invocation_releases, judged by pvlan_invocation_owned: its block must withdraw
    that channel-group). Unconfirmed or ambiguous answers record nothing. In memory for the gates of this invocation only."""
    if not prestate or not pvlan_markdelete_batch_confirmed(resp, payload):
        return {}
    releases = getattr(obj, "pvlan_invocation_releases", None) or {}
    withdrawn = getattr(obj, "pvlan_invocation_withdrawn", None) or {}
    for legs in prestate.values():
        for serial, pcid, members in legs:
            withdrawn.setdefault(serial, set()).add("no interface port-channel%s" % pcid)
            for member in members:
                releases.setdefault(serial, {})[member] = pcid
    obj.pvlan_invocation_releases, obj.pvlan_invocation_withdrawn = releases, withdrawn
    return prestate


def pvlan_prewrite_note(obj, kind, serial, ok, data=None):
    """PREWRITE-REUSE bookkeeping: `kind` ("detail", "policies") of ONE PHYSICAL serial was just read by the generic HAVE
    readers of THIS invocation, before its first write. ok: a complete, validated answer (data: the validated policy list); a failed or
    partial read, a combined pair serial, or any read once sending started records nothing and drops an earlier record. Module level so
    the shared readers keep working on the minimal objects of the unit tests."""
    reads = obj.__dict__.setdefault("pvlan_prewrite_reads", {})
    key = str(serial)
    record = reads.setdefault(kind, {})
    record.pop(key, None)
    if ok and not getattr(obj, "_pvlan_sending", False) and "~" not in key:
        record[key] = data


def pvlan_prewrite_reusable(obj, kind, serial):
    """True only before the first write, for a physical serial whose `kind` was read completely by this invocation and is still held as
    authoritative (not invalidated or failed since)."""
    record = (obj.__dict__.get("pvlan_prewrite_reads") or {}).get(kind) or {}
    if getattr(obj, "_pvlan_sending", False) or str(serial) not in record:
        return False
    authority = obj._dcnm_intf_authority_key(serial)
    if kind == "detail":
        return authority in obj.intf_detail_cached_snos and authority not in obj.intf_detail_fetch_failed_snos
    return isinstance(record[str(serial)], list)


def pvlan_invocation_withdrawals(obj, sno, global_lines):
    """The global pending lines of physical serial `sno` that are exactly the `no interface port-channel<id>` of a conventional
    aggregate this invocation's confirmed mark-delete deleted on that serial. Any other global line stays outside interface scope."""
    allowed = (getattr(obj, "pvlan_invocation_withdrawn", None) or {}).get(sno) or set()
    return sorted(set(str(line).strip().lower() for line in global_lines if str(line).strip().lower() in allowed))


def pvlan_invocation_owned(obj, sno, names, blocks):
    """The subset of `names` (pending interfaces of physical serial `sno` outside a PVLAN batch) that THIS
    invocation's confirmed write of a conventional aggregate produced on that serial:
      - a member it released (pvlan_record_conventional_releases / _deletions) whose block withdraws that aggregate's channel-group
        (`no channel-group <id>[ force][ mode M]`);
      - a member it joined (pvlan_record_conventional_creation, or added by a confirmed update) whose block joins that channel-group
        (`channel-group <id>[ force][ mode M]`);
      - the child `port-channel<id>` of a conventional vPC it created on that peer;
      - an interface its confirmed update modified on that serial (pvlan_record_conventional_modified: the interface itself, or the peer's
        child `port-channel<PEERn_PCID>` of a modified conventional vPC). Its whole block is accepted: the module does not parse it, so
        pending that another writer adds to that SAME interface between this write and the gate is not told apart.
    Same serial only; a name recorded on another serial, a different port-channel id, or a block without that withdrawal / join stays
    foreign."""
    released = (getattr(obj, "pvlan_invocation_releases", None) or {}).get(sno) or {}
    joined = (getattr(obj, "pvlan_invocation_joins", None) or {}).get(sno) or {}
    children = (getattr(obj, "pvlan_invocation_children", None) or {}).get(sno) or set()
    modified = (getattr(obj, "pvlan_invocation_modified", None) or {}).get(sno) or set()
    owned = []
    for name in names:
        key = str(name).lower()
        if key in children or key in modified:
            owned.append(name)
            continue
        lines = [str(line).strip() for line in blocks.get(name, [])]
        for pcid, prefix in ((released.get(key), "no "), (joined.get(key), "")):
            if not pcid:
                continue
            pattern = re.compile(r"^%schannel-group %s( force)?( mode \S+)?$" % (prefix, re.escape(str(pcid))), re.IGNORECASE)
            if any(pattern.match(line) for line in lines):
                owned.append(name)
                break
    return owned


class DcnmIntf:
    """
    Dcnm Interface methods, properties, and resources for all states.
    """

    dcnm_intf_paths = {
        11: {
            "VPC_SNO": "/rest/interface/vpcpair_serial_number?serial_number={}",
            "IF_WITH_SNO_IFNAME": "/rest/interface?serialNumber={}&ifName={}",
            "IF_WITH_SNO": "/rest/interface?serialNumber={}",
            "IF_DETAIL_WITH_SNO": "/rest/interface/detail?serialNumber={}",
            "GLOBAL_IF": "/rest/globalInterface",
            "GLOBAL_IF_DEPLOY": "/rest/globalInterface/deploy",
            "INTERFACE": "/rest/interface",
            "IF_MARK_DELETE": "/rest/interface/markdelete",
            "FABRIC_ACCESS_MODE": "/rest/control/fabrics/{}/accessmode",
            "BREAKOUT": "/rest/interface/breakout",
        },
        12: {
            "VPC_SNO": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/vpcpair_serial_number?serial_number={}",
            "IF_WITH_SNO_IFNAME": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface?serialNumber={}&ifName={}",
            "IF_WITH_SNO": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface?serialNumber={}",
            "IF_DETAIL_WITH_SNO": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/detail?serialNumber={}",
            "GLOBAL_IF": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/globalInterface",
            "GLOBAL_IF_DEPLOY": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/globalInterface/deploy",
            "INTERFACE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface",
            "UPDATE_INTERFACE_BULK": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/modify",
            "IF_MARK_DELETE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/markdelete",
            "FABRIC_ACCESS_MODE": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/accessmode",
            "BREAKOUT": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface/breakout",
            # PVLAN: documented legacy forced recompute of switch pending (configPreview).
            # recomputeMapEnable invalidates the compliance cache and recalculates; it is a GET
            # but refreshes controller state, so it never runs in check mode.
            "PVLAN_CONFIG_PREVIEW": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{}/config-preview/{}"
            "?forceShowRun=true&showBrief=false&recomputeMapEnable=true&shRunOptimization=false",
            "PVLAN_FABRIC_NETWORKS": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/top-down/fabrics/{}/networks",
            "PVLAN_TEMPLATE": "/appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates/int_pvlan_host",
            # Existing legacy policy listing (also read by the breakout path): policy ownership.
            "PVLAN_SWITCH_POLICIES": "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/switches/{}",
        },
    }

    storm_control_level_pairs = (
        (
            "storm_control_broadcast_level_percent",
            "storm_control_broadcast_level_pps",
            "STORM_CONTROL_BCAST_LEVEL_PERCENT",
            "STORM_CONTROL_BCAST_LEVEL_PPS",
        ),
        (
            "storm_control_multicast_level_percent",
            "storm_control_multicast_level_pps",
            "STORM_CONTROL_MCAST_LEVEL_PERCENT",
            "STORM_CONTROL_MCAST_LEVEL_PPS",
        ),
        (
            "storm_control_unicast_level_percent",
            "storm_control_unicast_level_pps",
            "STORM_CONTROL_UCAST_LEVEL_PERCENT",
            "STORM_CONTROL_UCAST_LEVEL_PPS",
        ),
    )

    def __init__(self, module):
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.module = module
        self.params = module.params
        self.fabric = module.params["fabric"]
        # Caller-declared ND patch context for the generic binding registry (GIE). Read once
        # here and passed to the engine unchanged; never sent to the controller, never part
        # of the interface diff. See GIE_ENABLED_PATCH_VERSIONS in gie_engine.py.
        self.patch_version = module.params.get("patch_version")
        self.config = copy.deepcopy(module.params.get("config"))
        # Before anything can fail, before dispatch by type, and regardless of whether any check
        # will accept or refuse the field. See SECRET_PROFILE_KEYS.
        self.dcnm_intf_register_secret_values(self.config)
        self.pb_input = []
        self.check_mode = False
        self.intf_info = []
        self.want = []
        self.have = []
        self.have_all = []
        self.have_all_list = []
        self.diff_create = []
        self.diff_replace = []
        self.diff_delete = [[], [], [], [], [], [], [], [], []]
        self.diff_delete_deploy = [[], [], [], [], [], [], [], [], []]
        self.want_breakout = []
        self.have_breakout = []
        self.diff_create_breakout = []
        self.diff_delete_breakout = []
        self.diff_deploy = []
        self.diff_query = []
        self.fd = None
        self.vpc_ip_sn = {}
        self.ip_sn = {}
        self.hn_sn = {}
        self.monitoring = []

        # Cached fabric-level default administrative state for host
        # (downlink) interfaces, derived from the fabric nvPair
        # HOST_INTF_ADMIN_STATE. Populated lazily on first use and reused
        # for the remainder of the module run. None means "not yet fetched".
        self.host_intf_admin_state = None

        # Cache for bulk-fetched interface policy details.
        # Keyed by (serialNumber, ifName_lower) -> interface detail dict.
        # This avoids per-interface HTTP GETs which are the primary
        # performance bottleneck when managing many interfaces.
        self.intf_detail_cache = {}
        self.intf_detail_cached_snos = set()
        self.intf_detail_fetch_failed_snos = set()
        self.intf_detail_failed_keys = set()
        self.intf_detail_authoritative_absent_keys = set()
        # Consecutive FAILED policy-detail read invocations, per queried serial.
        # Bounds the work spent on a switch that cannot be read; see
        # _dcnm_intf_read_budget_exhausted for the contract.
        self.intf_detail_failed_reads = {}
        self.have_all_cached_snos = set()
        self.have_all_failed_snos = set()
        # Diagnostics only: why the LAST read of a stage ("summary", "detail", "policies") for one serial was not authoritative.
        # Controlled text (status number, field name, entry index, failure category), never response content. Cleared when that
        # read starts again, succeeds or its authority is invalidated. No decision reads it.
        self.read_failure_reasons = {}
        self.have_breakout_cached_snos = set()
        self.have_breakout_failed_snos = set()
        self._replace_have_lookup = {}
        self._replace_pb_input_lookup = {}
        self.deferred_delete_member_defaults = []
        self._deferred_delete_member_default_keys = set()
        # The deploy each deletion was requested with, and the "marked for deletion" listings the request reaches (a saved
        # deletion awaiting its deploy), both keyed (serial, ifName lower) as decided while the diff is built.
        self.delete_requested_deploy = {}
        self.marked_delete_requests = {}

        # Bindings whose required withdrawal cannot be completed. Collected during the
        # comparison pass and raised ONCE by main(), before anything is sent.
        self.withdrawal_blocked = []
        # Dependent fields (inert_when) set against their gate, collected and raised before any request.
        self.dependency_blocked = []
        # Registered fields a reset-to-default (named deleted, overridden) must withdraw but
        # cannot, one entry per interface and field. Raised ONCE by main(), before anything is sent.
        self.default_reset_blocked = []
        # D-F3-1: SVIs whose stored nvPairs carry the other int_vlan body's DHCP4 / relay-source names than the ones
        # patch_version selects. Raised ONCE by main(), before anything is sent.
        self.svi_dhcp4_family_blocked = []
        # Native PVLAN: refusals collected during comparison/preflight and raised once by
        # main() before any write; per-target pre/post state for the pre-deploy gate.
        self.pvlan_blocked = []
        self.pvlan_targets = {}
        self.pvlan_networks = None
        self.pvlan_policies = {}
        self.pvlan_attempts = []
        self.changed_dict = [
            {
                "merged": [],
                "deleted": [],
                "replaced": [],
                "overridden": [],
                "deploy": [],
                "query": [],
                "debugs": [],
                "delete_deploy": [],
                "skipped": [],
                "deferred": [],
            }
        ]

        version_info = dcnm_version_supported(
            self.module, return_full_version=True
        )
        if isinstance(version_info, tuple):
            self.dcnm_version, self.ndfc_version = version_info
        else:
            # Preserve compatibility with tests and external mocks that still
            # return only the historical major-version integer.
            self.dcnm_version = version_info
            self.ndfc_version = None

        self._has_bulk_api = None

        self._ospf_auth_md_capability = None
        self._ospf_auth_md_capability_reason = None

        self.inventory_data = {}
        self.manageable = []
        self.unmanageable = []

        self.paths = self.dcnm_intf_paths[self.dcnm_version]

        self.dcnm_intf_facts = {
            "fabric": module.params["fabric"],
            "config": module.params["config"],
        }

        self.result = dict(changed=False, diff=[], response=[])

        # New Interfaces
        # To map keys from self.have to keys from config
        self.keymap = {
            "DISABLE_IP_REDIRECTS": "disable_ip_redirects",
            "ENABLE_HSRP": "enable_hsrp",
            "HSRP_VIP": "hsrp_vip",
            "HSRP_GROUP": "hsrp_group",
            "PREEMPT": "preempt",
            "HSRP_VERSION": "hsrp_version",
            "HSRP_PRIORITY": "hsrp_priority",
            "MAC": "hsrp_vmac",
            "dhcpServerAddr1": "dhcp_server_addr1",
            "dhcpServerAddr2": "dhcp_server_addr2",
            "dhcpServerAddr3": "dhcp_server_addr3",
            "dhcpServerAddr4": "dhcp_server_addr4",
            "dhcpServerAddress4": "dhcp_server_addr4",
            "vrfDhcp1": "vrf_dhcp1",
            "vrfDhcp2": "vrf_dhcp2",
            "vrfDhcp3": "vrf_dhcp3",
            "vrfDhcp4": "vrf_dhcp4",
            "DHCP_RELAY_SRC_INTF": "dhcp_relay_src_intf",
            "dhcpRelaySourceInterface": "dhcp_relay_src_intf",
            "advSubnetInUnderlay": "adv_subnet_in_unbderlay",
            "ENABLE_NETFLOW": "enable_netflow",
            "NETFLOW_MONITOR": "netflow_monitor",
            "secondaryGws": "secondary_gws",
            "hsrpSecondaryVips": "hsrp_secondary_vips",
            "policy": "policy",
            "ifName": "ifname",
            "serialNumber": "sno",
            "fabricName": "fabric",
            "IP": "ipv4_addr",
            "SECONDARY_IP": "secondary_ipv4_addr",
            "INTF_VRF": "int_vrf",
            "V6IP": "ipv6_addr",
            "IPv6": "ipv6_addr",
            "PREFIX": "ipv4_mask_len",
            "IPv6_PREFIX": "ipv6_mask_len",
            # int_vlan names its IPv6 prefix PREFIXv6; int_subif and int_routed_host use
            # IPv6_PREFIX. Both map to the same public key, following the existing
            # ipv6_addr pattern (mapped from both V6IP and IPv6).
            #
            # Fix the missing mapping rather than replacing keymap[k] with .get(k).
            # dcnm_intf_compare_elements indexes it inside `if t_e1 != t_e2` and
            # `elif state == "merged"`. With .get(), None would enter
            # `None not in pb_keys` -> True -> copy_and_add, an actual merge branch.
            # That would replace an explicit failure with a silent behavior change.
            "PREFIXv6": "ipv6_mask_len",
            "ROUTING_TAG": "route_tag",
            "ROUTE_MAP_TAG": "route_tag",
            "ENABLE_OSPF_AUTH_MESSAGE_DIGEST": "enable_ospf_auth_message_digest",
            "OSPF_AUTH_KEY_ID": "ospf_auth_key_id",
            "OSPF_AUTH_KEY": "ospf_auth_key",
            "CONF": "cmds",
            "DESC": "description",
            "VLAN": "vlan",
            "ADMIN_STATE": "admin_state",
            "MEMBER_INTERFACES": "members",
            "PC_MODE": "pc_mode",
            "BPDUGUARD_ENABLED": "bpdu_guard",
            "PORTTYPE_FAST_ENABLED": "port_type_fast",
            "MTU": "mtu",
            "SPEED": "speed",
            "PORT_DUPLEX_MODE": "duplex",
            "ALLOWED_VLANS": "allowed_vlans",
            "NATIVE_VLAN": "native_vlan",
            "ACCESS_VLAN": "access_vlan",
            "INTF_NAME": "ifname",
            "PO_ID": "ifname",
            "PEER1_PCID": "peer1_pcid",
            "PEER2_PCID": "peer2_pcid",
            "PEER1_MEMBER_INTERFACES": "peer1_members",
            "PEER2_MEMBER_INTERFACES": "peer2_members",
            "PEER1_ALLOWED_VLANS": "peer1_allowed_vlans",
            "PEER2_ALLOWED_VLANS": "peer2_allowed_vlans",
            "PEER1_NATIVE_VLAN": "peer1_native_vlan",
            "PEER2_NATIVE_VLAN": "peer2_native_vlan",
            "PO_DESC": "po_description",
            "PEER1_PO_DESC": "peer1_description",
            "PEER2_PO_DESC": "peer2_description",
            "PEER1_PO_CONF": "peer1_cmds",
            "PEER2_PO_CONF": "peer2_cmds",
            "PEER1_ACCESS_VLAN": "peer1_access_vlan",
            "PEER2_ACCESS_VLAN": "peer2_access_vlan",
            "DCI_ROUTING_PROTO": "dci_routing_proto",
            "DCI_ROUTING_TAG": "dci_routing_tag",
            "ENABLE_ORPHAN_PORT": "orphan_port",
            "DISABLE_LACP_SUSPEND": "disable_lacp_suspend_individual",
            "ENABLE_LACP_VPC_CONV": "enable_lacp_vpc_convergence",
            "LACP_PORT_PRIO": "lacp_port_priority",
            "LACP_RATE": "lacp_rate",
            "ENABLE_PFC": "enable_pfc",
            "ENABLE_MONITOR": "enable_monitor",
            "CDP_ENABLE": "enable_cdp",
            "ENABLE_QOS": "enable_qos",
            "QOS_POLICY": "qos_policy",
            "QUEUING_POLICY": "queuing_policy",
            "COPY_DESC": "copy_description",
            "ENABLE_STORM_CONTROL": "enable_storm_control",
            "STORM_CONTROL_ACTION": "storm_control_action",
            "STORM_CONTROL_BCAST_LEVEL_PERCENT": "storm_control_broadcast_level_percent",
            "STORM_CONTROL_BCAST_LEVEL_PPS": "storm_control_broadcast_level_pps",
            "STORM_CONTROL_MCAST_LEVEL_PERCENT": "storm_control_multicast_level_percent",
            "STORM_CONTROL_MCAST_LEVEL_PPS": "storm_control_multicast_level_pps",
            "STORM_CONTROL_UCAST_LEVEL_PERCENT": "storm_control_unicast_level_percent",
            "STORM_CONTROL_UCAST_LEVEL_PPS": "storm_control_unicast_level_pps",

        }

        # Extend the legacy comparator's nvPair -> playbook-key lookup from the packaged
        # registry. This is generic registry plumbing: no feature-specific key is added here.
        self.keymap.update(gie_nvpair_keymap())

        # NDFC 12.4.1+ (ND 4.1.1+) parameters
        if self._ndfc_version_gte("12.4.1"):
            self.keymap.update({
                "FEC": "fec",
            })

        # New Interfaces
        self.pol_types = {
            11: {
                "pc_monitor": "int_monitor_port_channel_11_1",
                "pc_trunk": "int_port_channel_trunk_host_11_1",
                "pc_access": "int_port_channel_access_host_11_1",
                "pc_l3": "int_l3_port_channel",
                "sub_int_subint": "int_subif_11_1",
                "lo_lo": "int_loopback_11_1",
                "eth_trunk": "int_trunk_host_11_1",
                "eth_access": "int_access_host_11_1",
                "eth_routed": "int_routed_host_11_1",
                "eth_monitor": "int_monitor_ethernet_11_1",
                "eth_epl_routed": "epl_routed_intf",
                "vpc_trunk": "int_vpc_trunk_host_11_1",
                "vpc_access": "int_vpc_access_host_11_1",
                "svi_vlan": "int_vlan",
                "svi_vlan_admin_state": "int_vlan_admin_state",
                "st_fex_port_channel_st": "int_port_channel_fex_11_1",
                "aa_fex_port_channel_aa": "int_port_channel_aa_fex_11_1",
            },
            12: {
                "pc_monitor": "int_monitor_port_channel",
                "pc_trunk": "int_port_channel_trunk_host",
                "pc_access": "int_port_channel_access_host",
                "pc_l3": "int_l3_port_channel",
                "pc_dot1q": "int_port_channel_dot1q_tunnel_host",
                "pc_pvlan": "int_port_channel_pvlan_host",
                "sub_int_subint": "int_subif",
                "lo_lo": "int_loopback",
                "lo_fabric": "int_fabric_loopback_11_1",
                "lo_mpls": "int_mpls_loopback",
                "eth_trunk": "int_trunk_host",
                "eth_access": "int_access_host",
                "eth_routed": "int_routed_host",
                "eth_monitor": "int_monitor_ethernet",
                "eth_epl_routed": "epl_routed_intf",
                "eth_dot1q": "int_dot1q_tunnel_host",
                "eth_pvlan": "int_pvlan_host",
                "vpc_trunk": "int_vpc_trunk_host",
                "vpc_access": "int_vpc_access_host",
                "vpc_dot1q": "int_vpc_dot1q_tunnel",
                "vpc_pvlan": "int_vpc_pvlan_host",
                "svi_vlan": "int_vlan",
                "svi_vlan_admin_state": "int_vlan_admin_state",
                "st_fex_port_channel_st": "int_port_channel_fex",
                "aa_fex_port_channel_aa": "int_port_channel_aa_fex",
                "breakout": "breakout_interface",
            },
        }

        self.pol_pc_member_types = {
            11: {
                "pc_access_member": "int_port_channel_access_member_11_1",
                "pc_trunk_member": "int_port_channel_trunk_member_11_1",
                "pc_dot1q_tunnel_member": "int_port_channel_dot1q_tunnel_member_11_1",
                "vpc_peer_link_member": "int_vpc_peer_link_po_member_11_1",
                "vpc_access_member": "int_vpc_access_po_member_11_1",
                "vpc_trunk_member": "int_vpc_trunk_po_member_11_1",
                "vpc_dot1q_tunnel_member": "int_vpc_dot1q_tunnel_po_member_11_1",
                "l3_pc_member": "int_l3_port_channel_member",
            },
            12: {
                "pc_access_member": "int_port_channel_access_member_11_1",
                "pc_trunk_member": "int_port_channel_trunk_member_11_1",
                "pc_dot1q_tunnel_member": "int_port_channel_dot1q_tunnel_member_11_1",
                "vpc_peer_link_member": "int_vpc_peer_link_po_member_11_1",
                "vpc_access_member": "int_vpc_access_po_member_11_1",
                "vpc_trunk_member": "int_vpc_trunk_po_member_11_1",
                "vpc_dot1q_tunnel_member": "int_vpc_dot1q_tunnel_po_member_11_1",
                "l3_pc_member": "int_l3_port_channel_member",
            },
        }

        # New Interfaces
        self.int_types = {
            "pc": "INTERFACE_PORT_CHANNEL",
            "vpc": "INTERFACE_VPC",
            "sub_int": "SUBINTERFACE",
            "lo": "INTERFACE_LOOPBACK",
            "eth": "INTERFACE_ETHERNET",
            "svi": "INTERFACE_VLAN",
            "st_fex": "STRAIGHT_TROUGH_FEX",
            "aa_fex": "AA_FEX",
            "breakout": "BREAKOUT",
        }

        # New Interfaces
        self.int_index = {
            "INTERFACE_PORT_CHANNEL": 0,
            "INTERFACE_VPC": 1,
            "INTERFACE_ETHERNET": 2,
            "INTERFACE_LOOPBACK": 3,
            "SUBINTERFACE": 4,
            "INTERFACE_VLAN": 5,
            "STRAIGHT_TROUGH_FEX": 6,
            "AA_FEX": 7,
            "BREAKOUT": 8,
        }

        msg = "ENTERED DcnmIntf: "
        self.log.debug(msg)

    def _ndfc_version_gte(self, target):
        """Check if NDFC version >= target. Compares as many version segments as the
        target specifies: a 3-part target like "12.4.1" stays 3-part, while a
        4-part target like "12.6.0.267" also enforces the build number. Unknown or
        malformed versions return False (fail closed)."""
        if not getattr(self, 'ndfc_version', None):
            return False
        try:
            required = tuple(int(x) for x in target.split("."))
            current = tuple(int(x) for x in self.ndfc_version.split(".")[:len(required)])
            current = current + (0,) * (len(required) - len(current))
            return current >= required
        except (ValueError, AttributeError):
            return False

    def dcnm_intf_breakout_format(self, if_name):
        # Define the pattern to match '1/x/y' where x and y are integers
        pattern = r'^ethernet1/\d+/\d+$'

        # Perform the pattern matching
        if re.match(pattern, if_name.lower()):
            # Split the interface name into parts
            intf = if_name.split("/")
            # Return True and the formatted interface string
            return True, f"{intf[0]}/{intf[1]}"

        # Return False and None if the pattern does not match
        return False, None

    def dcnm_intf_get_parent(self, name, switch):
        """
        Given an interface name and switch serial number, determine if the parent breakout interface exists in the target config.

        Args:
            cfg (list): List of interface configuration dictionaries.
            name (str): Interface name to check (e.g., "Ethernet1/100/1").
            switch (str): Switch Mgmt IP Address.

        Returns:
            tuple: (True, type) if parent breakout interface exists, else (False, None).
        """
        # Extract the parent interface ID (e.g., "1/100" from "Ethernet1/100/1")
        match = re.search(r"(\d+/\d+)/\d+", name)
        if not match:
            return False, None  # Return early if the pattern doesn't match

        parent_intf = f"Ethernet{match.group(1)}"
        # Check if the parent interface exists in the config for the given switch
        for interface in self.config:
            if (
                interface["name"].lower() == parent_intf.lower()
                and interface.get("type", "").lower() == "breakout"
                and interface["switch"][0] == switch
            ):
                return True, interface.get("type", None)
        return False, None

    def dcnm_intf_dump_have_all(self):

        lhave_all = []
        for have in self.have_all:
            lhave_all.append(
                {
                    "COMPLIANCE": have["complianceStatus"],
                    "FABRIC": have["fabricName"],
                    "IF_NAME": have["ifName"],
                    "IF_TYPE": have["ifType"],
                    "IP": have["ipAddress"],
                    "SNO": have["serialNo"],
                    "SYS NAME": have["sysName"],
                    "DELETABLE": have["deletable"],
                    "MARKED DELETE": have["markDeleted"],
                    "ALIAS": have["alias"],
                    "IS PHYSICAL": have["isPhysical"],
                    "UNDERLAY POLICIES": have["underlayPolicies"],
                }
            )
        msg = "HAVE ALL = "
        msg += f"{json_pretty(lhave_all)}"
        self.log.debug(msg)

    def dcnm_intf_xlate_speed(self, speed):

        # Controllers accept speed value in a particular format i.e. 1Gb, 100Gb etc. To make the playbook input
        # case insensitive for speed, this routine translates  the incoming speed to appropriate format.

        if speed == "":
            return ""

        if speed.lower() == "auto":
            return "auto".capitalize()
        else:
            comp = re.compile("([0-9]+)([a-zA-Z]+)")
            match = comp.match(speed)
            return str(match.group(1)) + match.group(2).capitalize()

    # New Interfaces
    def dcnm_intf_get_if_name(self, name, if_type):

        if "pc" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("Port-channel" + str(port_id[0]), port_id[0])
        if "vpc" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("vPC" + str(port_id[0]), port_id[0])
        if "sub_int" == if_type:
            if re.findall(r"\d+\/\d+.\d+", name):
                port_id = re.findall(r"\d+\/\d+.\d+", name)
                return ("Ethernet" + str(port_id[0]), port_id[0])
            if re.findall(r"\d+.\d+", name):
                port_id = re.findall(r"\d+\.\d+", name)
                return ("Port-channel" + str(port_id[0]), port_id[0])
        if "lo" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("Loopback" + str(port_id[0]), port_id[0])
        if "eth" == if_type:
            # add regex for breakout Ex: Ethernet1/49/1
            if re.findall(r"\d+\/\d+\/\d+", name):
                port_id = re.findall(r"\d+\/\d+\/\d+", name)
                return ("Ethernet" + str(port_id[0]), port_id[0])
            if re.findall(r"\d+\/\d+", name):
                port_id = re.findall(r"\d+\/\d+", name)
                return ("Ethernet" + str(port_id[0]), port_id[0])
        if "svi" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("vlan" + str(port_id[0]), port_id[0])
        if "st_fex" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("Port-channel" + str(port_id[0]), port_id[0])
        if "aa_fex" == if_type:
            port_id = re.findall(r"\d+", name)
            return ("vPC" + str(port_id[0]), port_id[0])
        if "breakout" == if_type:
            port_id = re.findall(r"\d+\/\d+", name)
            return ("Ethernet" + str(port_id[0]), port_id[0])

    def dcnm_intf_get_vpc_serial_number(self, sw):

        path = self.paths["VPC_SNO"].format(self.ip_sn[sw])
        resp = dcnm_send(self.module, "GET", path)

        if resp and resp["RETURN_CODE"] == 200:
            return resp["DATA"]["vpc_pair_sn"]
        else:
            return ""

    @staticmethod
    def dcnm_intf_storm_control_spec():
        return dict(
            enable_storm_control=dict(type="bool", default=False),
            storm_control_action=dict(
                type="str",
                default="default",
                choices=["shutdown", "trap", "default"],
            ),
            storm_control_broadcast_level_percent=dict(type="str", default=""),
            storm_control_broadcast_level_pps=dict(
                type="int", default=None, range_min=0, range_max=200000000
            ),
            storm_control_multicast_level_percent=dict(type="str", default=""),
            storm_control_multicast_level_pps=dict(
                type="int", default=None, range_min=0, range_max=200000000
            ),
            storm_control_unicast_level_percent=dict(type="str", default=""),
            storm_control_unicast_level_pps=dict(
                type="int", default=None, range_min=0, range_max=200000000
            ),
        )

    @staticmethod
    def dcnm_intf_normalize_storm_control_action(action):
        """Translate the public default action to NDFC's low-level nvPair value."""
        normalized_action = str(action).lower()
        return "no" if normalized_action == "default" else normalized_action

    def dcnm_intf_expand_storm_control_intent(self, profile):
        """Mark dependent storm-control fields as explicitly managed."""
        storm_keys = {
            "enable_storm_control",
            "storm_control_action",
        }
        for percent_key, pps_key, _percent_nvpair, _pps_nvpair in self.storm_control_level_pairs:
            storm_keys.update((percent_key, pps_key))

        if not storm_keys.intersection(profile):
            return

        enabled = profile.get("enable_storm_control")
        explicitly_disabled = False
        if "enable_storm_control" in profile:
            try:
                explicitly_disabled = not check_type_bool(enabled)
            except TypeError:
                # Leave invalid values for the normal profile validation path,
                # which reports the established user-facing error.
                pass
        if explicitly_disabled:
            profile["storm_control_action"] = "default"
            for percent_key, pps_key, _percent_nvpair, _pps_nvpair in self.storm_control_level_pairs:
                profile[percent_key] = ""
                profile[pps_key] = None
            return

        percent_mode_requested = any(
            profile.get(level_pair[0]) not in (None, "")
            for level_pair in self.storm_control_level_pairs
        )
        pps_mode_requested = any(
            profile.get(level_pair[1]) not in (None, "")
            for level_pair in self.storm_control_level_pairs
        )

        # A rate mode applies to the whole interface, not just one traffic
        # class. Mark every field in the opposite mode as explicitly cleared
        # so merged state cannot copy stale values from HAVE.
        if percent_mode_requested and not pps_mode_requested:
            for level_pair in self.storm_control_level_pairs:
                profile[level_pair[1]] = None
        elif pps_mode_requested and not percent_mode_requested:
            for level_pair in self.storm_control_level_pairs:
                profile[level_pair[0]] = ""

    def dcnm_intf_validate_storm_control_profile(self, profile, interface_name):
        enabled = profile["enable_storm_control"]
        action = profile["storm_control_action"]
        dependent_values = [action] if action != "default" else []
        percent_keys = []
        pps_keys = []

        for percent_key, pps_key, _percent_nvpair, _pps_nvpair in self.storm_control_level_pairs:
            percent_value = profile.get(percent_key, "")
            pps_value = profile.get(pps_key)

            if percent_value not in (None, ""):
                percent_keys.append(percent_key)
                dependent_values.append(percent_value)
                if not re.fullmatch(r"\d{1,3}(?:\.\d{1,2})?", percent_value):
                    self.module.fail_json(
                        msg="Invalid parameters in playbook: while processing interface "
                        + interface_name
                        + ", "
                        + percent_key
                        + " must be between 0 and 100 with at most two decimal places"
                    )
                try:
                    if Decimal(percent_value) > Decimal("100"):
                        raise InvalidOperation
                except InvalidOperation:
                    self.module.fail_json(
                        msg="Invalid parameters in playbook: while processing interface "
                        + interface_name
                        + ", "
                        + percent_key
                        + " must be between 0 and 100 with at most two decimal places"
                    )

            if pps_value is not None:
                pps_keys.append(pps_key)
                dependent_values.append(pps_value)

        if percent_keys and pps_keys:
            self.module.fail_json(
                msg="Invalid parameters in playbook: while processing interface "
                + interface_name
                + ", percentage and PPS storm-control levels are mutually exclusive; "
                + "configure only one rate mode per interface. Percentage fields: "
                + ", ".join(percent_keys)
                + "; PPS fields: "
                + ", ".join(pps_keys)
            )

        if not enabled and dependent_values:
            self.module.fail_json(
                msg="Invalid parameters in playbook: while processing interface "
                + interface_name
                + ", storm-control action and levels require enable_storm_control: true"
            )

    def dcnm_intf_set_qos_nv_pairs(self, profile, nv_pairs):
        """Write the QoS/queuing nvPairs for a port-channel profile.

        This block was duplicated verbatim in the trunk, access and l3 branches of
        dcnm_intf_get_pc_payload, and missing from the dot1q one -- so a dot1q port-channel
        could never carry a QoS or queuing policy even though its template declares
        ENABLE_QOS, QOS_POLICY and QUEUING_POLICY exactly like the other modes.

        Extracted rather than copied a fourth time. The three originals were byte-identical.
        """
        if profile.get("enable_qos"):
            nv_pairs["ENABLE_QOS"] = profile["enable_qos"]
            nv_pairs["QOS_POLICY"] = profile.get("qos_policy") or ""
        else:
            nv_pairs["ENABLE_QOS"] = False
            nv_pairs["QOS_POLICY"] = ""
        nv_pairs["QUEUING_POLICY"] = profile.get("queuing_policy") or ""

    def dcnm_intf_set_storm_control_nv_pairs(self, profile, nv_pairs):
        enabled = profile.get("enable_storm_control", False)
        nv_pairs["ENABLE_STORM_CONTROL"] = enabled
        storm_control_action = (
            profile.get("storm_control_action", "default")
            if enabled
            else "default"
        )
        nv_pairs["STORM_CONTROL_ACTION"] = (
            self.dcnm_intf_normalize_storm_control_action(
                storm_control_action
            )
        )

        for percent_key, pps_key, percent_nvpair, pps_nvpair in self.storm_control_level_pairs:
            percent_value = profile.get(percent_key, "") if enabled else ""
            pps_value = profile.get(pps_key) if enabled else None
            nv_pairs[percent_nvpair] = (
                "" if percent_value in (None, "") else str(percent_value)
            )
            nv_pairs[pps_nvpair] = "" if pps_value is None else str(pps_value)

    # Flatten the incoming config database and have the required fields updated.
    # This modified config DB will be used while creating payloads. To avoid
    # messing up the incoming config make a copy of it.
    def dcnm_intf_copy_config(self):

        for cfg in self.config:

            if cfg.get("switch", None) is None:
                continue
            for sw in cfg["switch"]:

                c = copy.deepcopy(cfg)

                # Add type of interface
                ckeys = list(cfg.keys())
                for ck in ckeys:
                    if ck.startswith("profile"):

                        if "type" not in cfg:
                            self.module.fail_json(
                                msg="<type> element, which is mandatory is missing in config"
                            )

                        c[ck]["fabric"] = self.dcnm_intf_facts["fabric"]
                        if cfg["type"] == "vpc" or cfg["type"] == "aa_fex":
                            if self.vpc_ip_sn.get(sw, None) is None:
                                self.module.fail_json(
                                    msg="Switch '{0}' is not part of VPC pair, but given I/F '{1}' is of type VPC".format(
                                        sw, c["name"]
                                    )
                                )
                            else:
                                c[ck]["sno"] = self.vpc_ip_sn[sw]
                        else:
                            c[ck]["sno"] = self.ip_sn[sw]

                        ifname, port_id = self.dcnm_intf_get_if_name(
                            c["name"], c["type"]
                        )
                        # No need to copy when we break interface, because parent interface will be removed
                        if "breakout" in cfg["type"]:
                            continue
                        if "mode" not in cfg["profile"]:
                            self.module.fail_json(
                                msg="Invalid parameters in playbook: while processing interface "
                                + ifname
                                + ", mode : Required parameter not found"
                            )
                        pol_ind_str = (
                            cfg["type"] + "_" + cfg["profile"]["mode"]
                        )
                        if (
                            cfg["type"] == "vpc"
                            and pol_ind_str not in self.pol_types[self.dcnm_version]
                        ):
                            # Without this an unsupported vPC mode -- or dot1q on a controller
                            # without int_vpc_dot1q_tunnel -- raised a bare KeyError here.
                            self.module.fail_json(
                                msg="Invalid parameters in playbook: while processing interface "
                                + ifname
                                + ", mode : {0!r} is not a supported vPC mode on this controller; "
                                "supported: {1}".format(
                                    cfg["profile"]["mode"],
                                    ", ".join(sorted(
                                        k[len("vpc_"):] for k in self.pol_types[self.dcnm_version]
                                        if k.startswith("vpc_")
                                    )),
                                )
                            )

                        if pol_ind_str == "pc_pvlan":
                            if pol_ind_str not in self.pol_types[self.dcnm_version]:
                                self.module.fail_json(
                                    msg="Interface {0}: mode 'pvlan' on a port-channel (int_port_channel_pvlan_host) "
                                    "is not implemented for this controller version. No change was sent.".format(ifname)
                                )
                        if (
                            pol_ind_str == "eth_pvlan"
                            and pol_ind_str not in self.pol_types[self.dcnm_version]
                        ):
                            self.module.fail_json(
                                msg="Interface {0}: mode 'pvlan' requires NDFC 12 (int_pvlan_host); "
                                "it is not supported on this controller. No change was sent.".format(ifname)
                            )

                        if pol_ind_str == "vpc_pvlan":
                            # One request per vPC, bound to the two serials of its pair.
                            if len(cfg["switch"]) != 2 or len(set(cfg["switch"])) != 2:
                                self.module.fail_json(
                                    msg="Interface {0}: a vPC in mode 'pvlan' needs exactly the two switches of its vPC pair in `switch`; "
                                    "peer1_* belong to the first and peer2_* to the second. No change was sent.".format(ifname)
                                )
                            c[ck]["peer_serials"] = [self.ip_sn[s_] for s_ in cfg["switch"]]
                            seen = self.__dict__.setdefault("pvlan_vpc_seen", set())
                            if (str(ifname).lower(), c[ck]["sno"]) in seen:
                                continue
                            seen.add((str(ifname).lower(), c[ck]["sno"]))

                        c[ck]["ifname"] = ifname
                        c[ck]["policy"] = self.pol_types[self.dcnm_version][
                            pol_ind_str
                        ]
                        self.dcnm_intf_expand_storm_control_intent(c[ck])
                        self.pb_input.append(c[ck])

    def dcnm_intf_validate_interface_input(
        self, config, common_spec, prof_spec
    ):

        plist = []

        # Same contract as the profile-spec call below: validate_list_of_dicts reads the
        # AnsibleModule only inside its `if no_log:` branch, to register the value in
        # module.no_log_values. No common_spec param declares no_log today, so this is a
        # no-op here -- it is passed so a future sensitive common-level field cannot raise
        # "'<param>' is a no_log parameter / Ansible module object must be passed...".
        intf_info, invalid_params = validate_list_of_dicts(
            config, common_spec, self.module
        )
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(
                "while processing interface "
                + config[0]["name"]
                + "\n"
                + "\n".join(invalid_params)
            )
            self.module.fail_json(msg=mesg)

        self.intf_info.extend(intf_info)

        if prof_spec is not None:

            if "enable_storm_control" in prof_spec:
                for config_item in config:
                    for _percent_key, pps_key, _percent_nvpair, _pps_nvpair in self.storm_control_level_pairs:
                        if config_item["profile"].get(pps_key) == "":
                            config_item["profile"][pps_key] = None

            for item in intf_info:

                plist.append(item["profile"])
                # Pass the AnsibleModule so validate_list_of_dicts can register no_log spec params
                # (e.g. the OSPF legacy-key 'ospf_auth_key') in module.no_log_values for scrubbing.
                # Without it, a no_log profile param makes validate_list_of_dicts raise
                # "'<param>' is a no_log parameter / Ansible module object must be passed...".
                intf_profile, invalid_params = validate_list_of_dicts(
                    plist, prof_spec, self.module
                )

                # Merge the info from the intf_profile into the intf_info to have a single dict to be used for building
                # payloads
                item["profile"].update(intf_profile[0])

                plist.remove(item["profile"])

                if invalid_params:
                    mesg = "Invalid parameters in playbook: {0}".format(
                        "while processing interface "
                        + config[0]["name"]
                        + ", "
                        + ", ".join(invalid_params)
                    )
                    self.module.fail_json(msg=mesg)

                if "enable_storm_control" in prof_spec:
                    self.dcnm_intf_validate_storm_control_profile(
                        item["profile"], config[0]["name"]
                    )

    def dcnm_intf_validate_port_channel_input(self, config):

        pc_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list", elements="str"),
            type=dict(required=True, type="str"),
            deploy=dict(type="bool", default=True),
            profile=dict(required=True, type="dict"),
        )

        pc_prof_spec_trunk = dict(
            mode=dict(required=True, type="str"),
            members=dict(type="list"),
            pc_mode=dict(type="str", default="active"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(type="str", default="jumbo"),
            speed=dict(type="str", default="Auto"),
            allowed_vlans=dict(type="str", default="none"),
            native_vlan=dict(type="str", default=""),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
            orphan_port=dict(type="bool", default=False),
            enable_cdp=dict(type="bool", default=True),
            enable_monitor=dict(type="bool", default=False),
            enable_pfc=dict(type="bool", default=False),
            duplex=dict(
                type="str", default="auto", choices=["auto", "full", "half"]),
            disable_lacp_suspend_individual=dict(type="bool", default=False),
            lacp_port_priority=dict(type="int", default=32768, range_min=1, range_max=65535),
            lacp_rate=dict(type="str", default="normal"),
            enable_qos=dict(type="bool", default=False),
            qos_policy=dict(type="str", default=""),
            queuing_policy=dict(type="str", default=""),
            copy_description=dict(type="bool", default=False),
        )
        pc_prof_spec_trunk.update(self.dcnm_intf_storm_control_spec())

        pc_prof_spec_access = dict(
            mode=dict(required=True, type="str"),
            members=dict(type="list"),
            pc_mode=dict(type="str", default="active"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(type="str", default="jumbo"),
            speed=dict(type="str", default="Auto"),
            access_vlan=dict(type="str", default=""),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
            orphan_port=dict(type="bool", default=False),
            enable_cdp=dict(type="bool", default=True),
            enable_monitor=dict(type="bool", default=False),
            enable_pfc=dict(type="bool", default=False),
            duplex=dict(
                type="str", default="auto", choices=["auto", "full", "half"]),
            disable_lacp_suspend_individual=dict(type="bool", default=False),
            lacp_port_priority=dict(type="int", default=32768, range_min=1, range_max=65535),
            lacp_rate=dict(type="str", default="normal"),
            enable_qos=dict(type="bool", default=False),
            qos_policy=dict(type="str", default=""),
            queuing_policy=dict(type="str", default=""),
            copy_description=dict(type="bool", default=False),
        )
        pc_prof_spec_access.update(self.dcnm_intf_storm_control_spec())

        pc_prof_spec_l3 = dict(
            mode=dict(required=True, type="str"),
            members=dict(type="list"),
            pc_mode=dict(type="str", default="active"),
            int_vrf=dict(type="str", default="default"),
            ipv4_addr=dict(type="ipv4", default=""),
            ipv4_mask_len=dict(type="int", default=8),
            route_tag=dict(type="str", default=""),
            mtu=dict(type="int", default=9216, range_min=576, range_max=9216),
            speed=dict(type="str", default="Auto"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
            enable_qos=dict(type="bool", default=False),
            qos_policy=dict(type="str", default=""),
            queuing_policy=dict(type="str", default=""),
            copy_description=dict(type="bool", default=False),
        )

        pc_prof_spec_dot1q = dict(
            mode=dict(required=True, type="str"),
            members=dict(type="list"),
            pc_mode=dict(type="str", default="active"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(type="str", default="jumbo"),
            speed=dict(type="str", default="Auto"),
            access_vlan=dict(type="str", default=""),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
            copy_description=dict(type="bool", default=False),
            # Same three keys, same defaults, as pc_prof_spec_trunk and _access. The dot1q
            # template declares ENABLE_QOS, QOS_POLICY and QUEUING_POLICY like every other
            # port-channel mode; this spec was the only one that did not accept them, so a
            # QoS policy could not be attached to a dot1q port-channel from the module at all.
            enable_qos=dict(type="bool", default=False),
            qos_policy=dict(type="str", default=""),
            queuing_policy=dict(type="str", default=""),
        )
        pc_prof_spec_dot1q.update(self.dcnm_intf_storm_control_spec())

        # Thin engine: extend the port-channel specs with registered generic keys the caller
        # set EXPLICITLY (no default), so an omitted key stays dropped exactly as before.
        gie_extend_prof_spec(
            pc_prof_spec_trunk, "int_port_channel_trunk_host", config[0]["profile"]
        )
        gie_extend_prof_spec(
            pc_prof_spec_access, "int_port_channel_access_host", config[0]["profile"]
        )
        gie_extend_prof_spec(
            pc_prof_spec_dot1q,
            "int_port_channel_dot1q_tunnel_host",
            config[0]["profile"],
        )

        if "pvlan" == config[0]["profile"]["mode"]:
            # RAW input first (before any coercion or default): everything outside the first
            # delivery is refused here, before any read or write, and never falls through to
            # another policy.
            reasons = pvlan_po_not_implemented(config[0]["profile"])
            if reasons:
                self.module.fail_json(
                    msg="Invalid parameters in playbook: while processing interface {0}, {1}. "
                    "No change was sent.".format(config[0]["name"], "; ".join(reasons))
                )
            pc_prof_spec_pvlan = dict(
                mode=dict(required=True, type="str"),
                pvlan_mode=dict(required=True, type="str"),
                pvlan_association=dict(type="list", elements="dict"),
                pvlan_mapping=dict(type="list", elements="dict"),
                native_vlan=dict(type="str"),
                allowed_vlans=dict(type="str"),
                members=dict(type="list", elements="str"),
                pc_mode=dict(type="str"),
                description=dict(type="str"),
                admin_state=dict(type="bool"),
                # RC1: freeform of the port-channel; no default (omitted = kept by merged, cleared by replaced).
                cmds=dict(type="list", elements="str"),
            )
            # Native companions (no defaults) and the registry companions the caller set explicitly.
            pc_prof_spec_pvlan.update(pvlan_native_companion_spec(PVLAN_PO_NATIVE_COMPANIONS))
            gie_extend_prof_spec(
                pc_prof_spec_pvlan, "int_port_channel_pvlan_host", config[0]["profile"]
            )
            self.dcnm_intf_validate_interface_input(
                config, pc_spec, pc_prof_spec_pvlan
            )
        if "trunk" == config[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                config, pc_spec, pc_prof_spec_trunk
            )
        if "access" == config[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                config, pc_spec, pc_prof_spec_access
            )
        if "l3" == config[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                config, pc_spec, pc_prof_spec_l3
            )
        if "dot1q" == config[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                config, pc_spec, pc_prof_spec_dot1q
            )
        if "monitor" == config[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(config, pc_spec, None)

    def dcnm_intf_validate_virtual_port_channel_input(self, cfg):

        vpc_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        vpc_prof_spec_trunk = dict(
            mode=dict(required=True, type="str"),
            peer1_pcid=dict(
                type="int", default=0, range_min=1, range_max=4096
            ),
            peer2_pcid=dict(
                type="int", default=0, range_min=1, range_max=4096
            ),
            peer1_members=dict(type="list"),
            peer2_members=dict(type="list"),
            pc_mode=dict(type="str", default="active"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(type="str", default="jumbo"),
            speed=dict(type="str", default="Auto"),
            peer1_allowed_vlans=dict(type="str", default="none"),
            peer2_allowed_vlans=dict(type="str", default="none"),
            peer1_native_vlan=dict(type="str", default=""),
            peer2_native_vlan=dict(type="str", default=""),
            peer1_cmds=dict(type="list"),
            peer2_cmds=dict(type="list"),
            peer1_description=dict(type="str", default=""),
            peer2_description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
            disable_lacp_suspend_individual=dict(type="bool", default=False),
            enable_lacp_vpc_convergence=dict(type="bool", default=False),
            lacp_port_priority=dict(type="int", default=32768, range_min=1, range_max=65535),
            lacp_rate=dict(type="str", default="normal"),
            enable_qos=dict(type="bool", default=False),
            qos_policy=dict(type="str", default=""),
            queuing_policy=dict(type="str", default=""),
            copy_description=dict(type="bool", default=False),
            enable_cdp=dict(type="bool", default=True),
        )
        vpc_prof_spec_trunk.update(self.dcnm_intf_storm_control_spec())

        vpc_prof_spec_access = dict(
            mode=dict(required=True, type="str"),
            peer1_pcid=dict(
                type="int", default=0, range_min=1, range_max=4096
            ),
            peer2_pcid=dict(
                type="int", default=0, range_min=1, range_max=4096
            ),
            peer1_members=dict(type="list"),
            peer2_members=dict(type="list"),
            pc_mode=dict(type="str", default="active"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(type="str", default="jumbo"),
            speed=dict(type="str", default="Auto"),
            peer1_access_vlan=dict(type="str", default=""),
            peer2_access_vlan=dict(type="str", default=""),
            peer1_cmds=dict(type="list"),
            peer2_cmds=dict(type="list"),
            peer1_description=dict(type="str", default=""),
            peer2_description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
            enable_qos=dict(type="bool", default=False),
            qos_policy=dict(type="str", default=""),
            queuing_policy=dict(type="str", default=""),
            copy_description=dict(type="bool", default=False),
            enable_cdp=dict(type="bool", default=True),
        )
        vpc_prof_spec_access.update(self.dcnm_intf_storm_control_spec())

        # dot1q-tunnel (int_vpc_dot1q_tunnel). The installed parent declares the access-port
        # set -- per-peer access VLAN, which is the dot1q-tunnel (outer) VLAN on each peer --
        # plus the four LACP options that the trunk spec already exposes. Same public names and
        # defaults as the sibling specs; nothing here is new public vocabulary.
        vpc_prof_spec_dot1q = dict(vpc_prof_spec_access)
        vpc_prof_spec_dot1q.update(
            disable_lacp_suspend_individual=dict(type="bool", default=False),
            enable_lacp_vpc_convergence=dict(type="bool", default=False),
            lacp_port_priority=dict(type="int", default=32768, range_min=1, range_max=65535),
            lacp_rate=dict(type="str", default="normal"),
        )

        # Registered keys must reach the vPC spec exactly as they reach the ethernet and
        # port-channel ones. Without this the keys are not in the spec, so
        # validate_list_of_dicts drops them as unknown legacy fields and the value never
        # reaches the payload -- a silent no-op, which is the failure mode this whole path
        # exists to remove. These bindings are shared across the pair, not per-peer: the vPC
        # nvPairs carry one GUARD_MODE, not PEER1_/PEER2_ variants.
        gie_extend_prof_spec(
            vpc_prof_spec_trunk, "int_vpc_trunk_host", cfg[0]["profile"]
        )
        gie_extend_prof_spec(
            vpc_prof_spec_access, "int_vpc_access_host", cfg[0]["profile"]
        )
        gie_extend_prof_spec(
            vpc_prof_spec_dot1q, "int_vpc_dot1q_tunnel", cfg[0]["profile"]
        )

        # An unsupported vPC mode, or dot1q on a controller without int_vpc_dot1q_tunnel, is
        # refused earlier, in dcnm_intf_copy_config, where pol_types is first indexed.
        mode = cfg[0]["profile"]["mode"]
        if "pvlan" == mode:
            # RAW input first (before any coercion or default): everything outside the first delivery is
            # refused here, before any read or write, and never falls through to another policy.
            reasons = pvlan_vpc_not_implemented(cfg[0]["profile"], cfg[0]["name"])
            if reasons:
                self.module.fail_json(
                    msg="Invalid parameters in playbook: while processing interface {0}, {1}. "
                    "No change was sent.".format(cfg[0]["name"], "; ".join(reasons))
                )
            vpc_prof_spec_pvlan = dict(
                mode=dict(required=True, type="str"),
                pvlan_mode=dict(required=True, type="str"),
                pvlan_association=dict(type="list", elements="dict"),
                pvlan_mapping=dict(type="list", elements="dict"),
                peer1_members=dict(type="list", elements="str"),
                peer2_members=dict(type="list", elements="str"),
                peer1_pcid=dict(type="int"),
                peer2_pcid=dict(type="int"),
                pc_mode=dict(type="str"),
                peer1_description=dict(type="str"),
                peer2_description=dict(type="str"),
                # Per-peer PVLAN native/allowed of the trunk submodes; no default (omitted = kept by merged, neutral by replaced).
                peer1_allowed_vlans=dict(type="str"),
                peer2_allowed_vlans=dict(type="str"),
                peer1_native_vlan=dict(type="str"),
                peer2_native_vlan=dict(type="str"),
                admin_state=dict(type="bool"),
                # RC1: per-peer freeform; no default (omitted = kept by merged, cleared by replaced).
                peer1_cmds=dict(type="list", elements="str"),
                peer2_cmds=dict(type="list", elements="str"),
            )
            # Shared native companions (no defaults) and the registry companions the caller set explicitly.
            vpc_prof_spec_pvlan.update(pvlan_native_companion_spec(PVLAN_VPC_NATIVE_COMPANIONS))
            gie_extend_prof_spec(
                vpc_prof_spec_pvlan, "int_vpc_pvlan_host", cfg[0]["profile"]
            )
            self.dcnm_intf_validate_interface_input(cfg, vpc_spec, vpc_prof_spec_pvlan)
        if "trunk" == mode:
            self.dcnm_intf_validate_interface_input(
                cfg, vpc_spec, vpc_prof_spec_trunk
            )
        if "access" == mode:
            self.dcnm_intf_validate_interface_input(
                cfg, vpc_spec, vpc_prof_spec_access
            )
        if "dot1q" == mode:
            self.dcnm_intf_validate_interface_input(
                cfg, vpc_spec, vpc_prof_spec_dot1q
            )

    def dcnm_intf_validate_sub_interface_input(self, cfg):

        sub_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        sub_prof_spec = dict(
            mode=dict(required=True, type="str"),
            vlan=dict(required=True, type="int", range_min=2, range_max=3967),
            ipv4_addr=dict(required=False, type="ipv4"),
            ipv4_mask_len=dict(
                required=False, type="int", range_min=8, range_max=31
            ),
            int_vrf=dict(type="str", default="default"),
            ipv6_addr=dict(type="ipv6", default=""),
            ipv6_mask_len=dict(
                type="int", range_min=64, range_max=127, default=64
            ),
            mtu=dict(type="int", range_min=576, range_max=9216, default=9216),
            route_tag=dict(type="str", default=""),
            speed=dict(type="str", default="Auto"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        # Thin engine: extend the subinterface spec with registered generic keys the caller set
        # EXPLICITLY (no default), so an omitted key stays dropped exactly as before. Same
        # plumbing as the eth and port-channel parents; no feature-specific key is added here.
        gie_extend_prof_spec(sub_prof_spec, "int_subif", cfg[0]["profile"])

        self.dcnm_intf_validate_interface_input(cfg, sub_spec, sub_prof_spec)

    @property
    def has_bulk_api(self):
        """
        Whether the controller exposes the v2 bulk-update interface API.

        The underlying probe is a POST. Evaluating it lazily keeps read-only and
        fail-before-mutation paths -- including check mode -- free of controller
        writes, and it is still resolved at most once per module execution.
        """
        if self._has_bulk_api is None:
            self._has_bulk_api = dcnm_get_bulk_api_support(self.module)
        return self._has_bulk_api

    @has_bulk_api.setter
    def has_bulk_api(self, value):
        self._has_bulk_api = value

    def dcnm_intf_ospf_md_have_unavailable(self, name, sno):
        """
        Report whether the current state of a fabric-loopback parent could NOT be
        authoritatively determined.

        An interface's HAVE is authoritative when it was found in the detail cache
        or when a bulk GET for its serial succeeded (so a miss is a genuine
        absence). It is UNAVAILABLE only when a bulk or individual GET actually
        failed (all retries, no RETURN_CODE 200). The feature path fails closed on
        unavailable state instead of treating it as absence.
        """
        return self.dcnm_intf_detail_unavailable(name, sno)

    def dcnm_intf_detail_unavailable(self, name, sno):
        """Return whether one interface detail lacks authoritative state."""
        sno = self._dcnm_intf_authority_key(sno)
        cache_key = (sno, name.lower())
        query_serial = self._dcnm_intf_query_serial(sno)
        if (
            cache_key in self.intf_detail_cache
            or sno in self.intf_detail_cached_snos
            or query_serial in self.intf_detail_cached_snos
            or cache_key in self.intf_detail_authoritative_absent_keys
        ):
            return False
        if cache_key in self.intf_detail_failed_keys:
            return True
        if "~" in sno:
            return any(
                identity in self.intf_detail_fetch_failed_snos
                for identity in (sno,) + self._dcnm_intf_serial_parts(sno)
            )
        return query_serial in self.intf_detail_fetch_failed_snos

    @classmethod
    def _dcnm_intf_read_budget_key(cls, serialNumber):
        """Return the budget key: the serial actually placed in the GET URL.

        One endpoint, one budget. A vPC/AA-FEX pair queries only its first
        component, so a request sent for ``SN1~PEER`` is charged to ``SN1`` and
        never to ``PEER`` -- the peer's own endpoint was not contacted. Folded so
        that two spellings of one serial share an allowance, matching how
        dcnm_intf_invalidate_serial_authority already compares identities.
        """
        query_serial = cls._dcnm_intf_normalize_serial(serialNumber)
        return query_serial.casefold() if query_serial else None

    def _dcnm_intf_read_budget_exhausted(self, serialNumber):
        """Whether this serial has spent its consecutive-failure allowance.

        A policy-detail read that cannot establish authority costs up to three
        HTTP attempts and three seconds of sleep. Nothing used to bound how many
        such invocations one run could make, so an unreadable switch cost one
        full invocation per requested interface. This allows two consecutive
        failed invocations. In the usual bulk-then-individual path, this leaves
        one individual probe after the bulk failure. A valid response resets
        the count so useful per-interface recovery can continue. Two failures
        do not prove that every interface on the switch is unreadable.

        Accepted tradeoff: if that single probe lands on an interface that is
        genuinely unreadable while others would have answered, the switch closes
        early for this invocation. A later module invocation starts fresh.
        """
        key = self._dcnm_intf_read_budget_key(serialNumber)
        if key is None:
            return False
        return self.intf_detail_failed_reads.get(key, 0) >= 2

    def _dcnm_intf_charge_failed_read(self, serialNumber):
        """Charge one failed read invocation against this serial."""
        key = self._dcnm_intf_read_budget_key(serialNumber)
        if key is None:
            return
        self.intf_detail_failed_reads[key] = (
            self.intf_detail_failed_reads.get(key, 0) + 1
        )

    def _dcnm_intf_clear_failed_reads(self, serialNumber):
        """Restore the allowance after a newly obtained, validated response.

        Only a response this run actually received and fully validated resets the
        count -- present, or authoritatively absent. Wanting to re-read is not
        evidence that the controller answered, so neither an explicit
        invalidation, a refresh, a repeated pass, a cache hit nor a bare
        RETURN_CODE 200 reaches this method. Nothing but this serial's own
        counter is touched: a successful read proves nothing about any other
        identity's failures.
        """
        key = self._dcnm_intf_read_budget_key(serialNumber)
        if key is None:
            return
        self.intf_detail_failed_reads.pop(key, None)
        # Diagnostics follow the same refund: a validated answer ends the "last failed read" this serial's budget was spent on.
        read_reason_clear(self, "detail-last-failure", serialNumber)

    def dcnm_intf_mark_detail_unavailable(self, serialNumber):
        """Mark the logical identity and every covered physical serial failed."""
        parts = self._dcnm_intf_serial_parts(serialNumber) or ()
        authority = self._dcnm_intf_authority_key(serialNumber)
        if authority:
            self.intf_detail_fetch_failed_snos.add(authority)
        self.intf_detail_fetch_failed_snos.update(parts)

    def dcnm_intf_require_summary_authority(self, sno, endpoint="interface"):
        """Fail closed when summary state used for mutation was unavailable."""
        authority = self._dcnm_intf_authority_key(sno)
        failed, cached = (
            (self.have_breakout_failed_snos, self.have_breakout_cached_snos)
            if endpoint == "breakout"
            else (self.have_all_failed_snos, self.have_all_cached_snos)
        )
        if authority not in failed and authority in cached:
            return
        self.module.fail_json(
            msg="Current {0} summary for {1} could not be read authoritatively. "
            "Refusing dependent create, delete, reset or deploy; no change was "
            "sent.".format(endpoint, sno)
        )

    def dcnm_intf_require_detail_authority(self, name, sno):
        """Fail before mutation when current interface policy state is unknown."""
        if not self.dcnm_intf_detail_unavailable(name, sno):
            return
        self.module.fail_json(
            msg="Current state of interface {0} on {1} could not be read "
            "authoritatively. Refusing to create, update, delete, reset or "
            "deploy over unknown controller state; no change was sent.".format(
                name, sno
            )
        )

    def dcnm_intf_gie_normalize_ospf_aliases(self):
        """Translate the legacy OSPF boolean inputs (``ospf_bfd`` on loopback and subinterface,
        ``ospf_passive_interface`` on subinterface) to the mode keys the registry binds for
        SMU 4.3.1.0175006017, before any other validation reads the profile.

        true keeps its old meaning (enable / passive); false keeps it too -- no local override --
        and becomes no_change, never the explicit disable / no_passive. Both spellings in one
        profile are accepted only when they mean the same. The value of a rejected field is never
        echoed.
        """
        pol_map = getattr(self, "pol_types", {}).get(getattr(self, "dcnm_version", None), {})
        for cfg_item in self.config:
            profile = cfg_item.get("profile")
            if not isinstance(profile, dict):
                continue
            parent = pol_map.get("{0}_{1}".format(cfg_item.get("type"), profile.get("mode")))
            _normalized, reason = gie_normalize_ospf_aliases(parent, profile)
            if reason is None:
                continue
            kind, _sep, rest = reason.partition(":")
            if kind == "not_applicable":
                msg = (
                    "Invalid parameters in playbook: while processing interface {0}, '{1}' is not "
                    "supported on this interface (type '{2}', mode '{3}'). No template metadata was "
                    "queried and no change was sent.".format(
                        cfg_item.get("name"), rest, cfg_item.get("type"), profile.get("mode")
                    )
                )
            elif kind == "not_boolean":
                key, _sep, given = rest.partition(":")
                msg = (
                    "Invalid parameters in playbook: while processing interface {0}, '{1}' must be a "
                    "native boolean, given {2}. No template metadata was queried and no change was "
                    "sent.".format(cfg_item.get("name"), key, given)
                )
            else:
                alias, _sep, mode_key = rest.partition(":")
                msg = (
                    "Invalid parameters in playbook: while processing interface {0}, '{1}' and '{2}' "
                    "give different settings for the same OSPF field; use only '{2}', which also "
                    "expresses the explicit disabled states. No template metadata was queried and no "
                    "change was sent.".format(cfg_item.get("name"), alias, mode_key)
                )
            self.module.fail_json(msg=msg)

    def dcnm_intf_gie_validate_parent_bindings(self):
        """Fail closed when a config item carries a registry-known GENERIC key that has no
        valid binding for its resolved desired parent (``pol_types[type_mode]``). This runs
        globally, before mode-specific defaulting/filtering, so a registered passthrough key
        such as ``flowcontrol_receive`` on a routed/monitor/dot1q Ethernet (or any parent that
        does not register it) is rejected instead of being silently dropped by legacy
        validation. A wholly-unknown legacy field is left untouched (legacy discard). child_pti
        keys (OSPF-MD) keep their dedicated parent/mode validate above and are not double-
        guarded here."""
        pol_map = getattr(self, "pol_types", {}).get(
            getattr(self, "dcnm_version", None), {}
        )
        # Built ONCE per invocation. It used to be rebuilt inside the profile-key loop
        # below -- once per field of every interface in the play, so a run with 1,000
        # interfaces declaring five registered fields asked for the same registry-wide set
        # 5,000 times. The set is a pure function of the packaged registry, which cannot
        # change while this method runs, so the repetition bought nothing.
        registered_keys = gie_all_registered_keys()
        for cfg_item in self.config:
            profile = cfg_item.get("profile")
            if not isinstance(profile, dict):
                continue
            parent = pol_map.get(
                "{0}_{1}".format(cfg_item.get("type"), profile.get("mode"))
            )
            bad = gie_invalid_parent_key(parent, list(profile.keys()))
            if bad is not None:
                self.module.fail_json(
                    msg="Invalid parameters in playbook: while processing interface {0}, "
                    "'{1}' is not supported on this interface (type '{2}', mode '{3}'). "
                    "No template metadata was queried and no change was sent.".format(
                        cfg_item.get("name"),
                        bad,
                        cfg_item.get("type"),
                        profile.get("mode"),
                    )
                )

            # Enforce the REGISTERED native type/choices on the RAW playbook
            # value, here, while it is still raw. The nested-profile path runs
            # validate_list_of_dicts later, and that coerces (check_type_bool("false") ->
            # False, check_type_str(True) -> "True"), so a check placed after it can only
            # ever see an already-coerced value. Scope is deliberately narrow: only keys
            # that resolve to an exact registered binding on THIS parent are inspected, so
            # unknown and non-registered legacy fields keep their existing behaviour.
            if parent is None:
                continue
            for profile_key in sorted(profile.keys()):
                if profile_key not in registered_keys:
                    continue
                if resolve_binding(parent, profile_key) is None:
                    continue
                try:
                    gie_validate_binding_value(
                        parent, profile_key, profile[profile_key]
                    )
                except GieBindingError:
                    # The engine's message deliberately omits the rejected value; this one
                    # names the field, the expected type and the type actually RECEIVED,
                    # without echoing the value either. The received type is what makes the
                    # message actionable: the common failure is a Jinja template rendering
                    # an unquoted `| default('')`, which YAML reads as null, and "expected a
                    # string" alone does not point anywhere near that.
                    #
                    # The engine raises this for ANY reason it refuses a value -- native type,
                    # enum membership, string length, numeric range -- so each of those has to
                    # be named here or the message describes the wrong problem. The numeric
                    # range was missing, and the result contradicted itself: arp_timeout=30 on
                    # a 60..28800 binding answered "'arp_timeout' must be a native integer,
                    # given an integer", which is nonsense AND silent about the 60 that would
                    # tell the operator what to fix. Measured on a live fabric; 45
                    # rows across 20 public keys declare a range, so this was never specific
                    # to one field. No earlier round caught it because their negative stages
                    # exercised TEMPLATE dependency rules, never the registry's own bounds.
                    binding = resolve_binding(parent, profile_key)
                    expected = binding["type"]
                    if binding.get("valid_values"):
                        expected = "{0} (one of: {1})".format(
                            expected, ", ".join(binding["valid_values"])
                        )
                    elif binding.get("min_length") or binding.get("max_length"):
                        expected = "{0} (length {1}..{2})".format(
                            expected,
                            binding.get("min_length", 0),
                            binding.get("max_length", "unbounded"),
                        )
                    elif (
                        binding.get("min_value") is not None
                        or binding.get("max_value") is not None
                    ):
                        # `is not None`, not truthiness, because min_value 0 is a real bound
                        # (hsrp_groupv6, hsrp_preempt_delay_minimum, ospf_priority,
                        # ospf_auth_key_id). This is DEFENSIVE, not a live fix: all four also
                        # declare a max_value, so plain `or` would reach this branch anyway
                        # today -- measured, 0 rows declare only one of the two bounds. It
                        # matters for the first row that declares a minimum of 0 and no
                        # maximum, where `or` would drop the range from the message entirely.
                        expected = "{0} (range {1}..{2})".format(
                            expected,
                            binding.get("min_value", "unbounded"),
                            binding.get("max_value", "unbounded"),
                        )
                    self.module.fail_json(
                        msg="Invalid parameters in playbook: while processing interface "
                        "{0}, '{1}' must be a native {2}, given {3}. No template "
                        "metadata was queried and no change was sent.".format(
                            cfg_item.get("name"),
                            profile_key,
                            expected,
                            gie_describe_value_type(profile[profile_key]),
                        )
                    )

    def dcnm_intf_register_secret_values(self, cfg):
        """Register every secret value in the config so Ansible scrubs it from all output.

        Walks the WHOLE config -- every interface, every secret-bearing profile key -- and does
        not stop at the first one. Stopping early is what made the previous attempt leak.

        Deliberately total and deliberately silent: it never validates, never rejects and never
        reports. Its only job is that no key material can be serialised in the clear, whatever
        happens next. A malformed config is not its problem, so anything that is not shaped like
        an interface with a profile is skipped rather than complained about -- the real
        validators run afterwards and give the operator a proper message.
        """
        if not isinstance(cfg, list):
            return
        for cfg_item in cfg:
            if not isinstance(cfg_item, dict):
                continue
            profile = cfg_item.get("profile")
            if not isinstance(profile, dict):
                continue
            for key in SECRET_PROFILE_KEYS:
                value = profile.get(key)
                # "" and None carry nothing; registering "" would scrub every empty string in
                # the output, which hides far more than it protects.
                if value not in (None, ""):
                    self.module.no_log_values.add(str(value))

    def dcnm_intf_register_controller_secrets(self, payload):
        """Register secret values the CONTROLLER produced, wherever they sit in a response.

        Walks the structure rather than a known path on purpose. Secrets surface from NDFC in
        several shapes -- the HAVE list, a query result, the body echoed back in an error -- and
        each of those has its own nesting. A walk protects all of them, including ones added
        later, where a hardcoded path would protect exactly the one it was written against.

        Like its input-side counterpart this never validates and never raises: its only job is
        that a key cannot be serialised in the clear.
        """
        def walk(node):
            if isinstance(node, dict):
                nvpairs = node.get("nvPairs")
                if isinstance(nvpairs, dict):
                    for nvpair in SECRET_NVPAIRS:
                        value = nvpairs.get(nvpair)
                        if value not in (None, ""):
                            self.module.no_log_values.add(str(value))
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(payload)

    def dcnm_intf_validate_loopback_interface_input(self, cfg):

        lo_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        lo_prof_spec = dict(
            mode=dict(required=True, type="str"),
            ipv4_addr=dict(required=True, type="ipv4"),
            secondary_ipv4_addr=dict(type="ipv4", default=""),
            int_vrf=dict(type="str", default="default"),
            ipv6_addr=dict(type="ipv6", default=""),
            route_tag=dict(type="str", default=""),
            speed=dict(type="str", default="Auto"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        # This validator serves BOTH loopback parents: mode 'lo' resolves to int_loopback and
        # mode 'fabric' to int_fabric_loopback_11_1. Everything below has to say which one it
        # means, because the two do not share an owner for authentication.
        pol_map = getattr(self, "pol_types", {}).get(
            getattr(self, "dcnm_version", None), {}
        )

        def _parent_of(cfg_item):
            profile = cfg_item.get("profile")
            if not isinstance(profile, dict):
                return None
            return pol_map.get(
                "{0}_{1}".format(cfg_item.get("type"), profile.get("mode"))
            )

        # Thin engine: extend the loopback spec with registered generic keys the caller set
        # EXPLICITLY, per item, because one call can mix the two parents and they register
        # different fields -- int_loopback declares OSPF_ADVERTISE_SUBNET and a boolean OSPF_BFD
        # that the fabric parent does not have at all. Extending from cfg[0] alone, the way the
        # single-parent paths do, would under-serve every item after the first.
        for cfg_item in cfg:
            parent = _parent_of(cfg_item)
            if parent:
                gie_extend_prof_spec(lo_prof_spec, parent, cfg_item["profile"])

        # Reject the withdrawn OSPF-auth keys by name, before the spec silently drops them.
        #
        # SCOPED TO THE FABRIC PARENT, and that scoping is the point. The retirement was a
        # decision about OWNERSHIP, not about the word "loopback": on int_fabric_loopback_11_1
        # the authentication is underlay authentication that fabricSettings owns. int_loopback is
        # a different template for a different object -- a user loopback is not part of the
        # underlay, its own template takes authentication from the interface fields, and no
        # interface in a fabric need ever use it. Unscoped, this loop refused a supported field
        # with a message naming a fabric that has no claim on it.
        for cfg_item in cfg:
            profile = cfg_item.get("profile")
            if not isinstance(profile, dict):
                continue
            parent = _parent_of(cfg_item)
            for key, fabric_setting in RETIRED_LOOPBACK_OSPF_AUTH_KEYS.items():
                # The exemption is granted by the REGISTRY, not by the parent's name: a key is
                # let through only when this parent actually has a binding that will carry it.
                #
                # Tying it to `parent != int_fabric_loopback_11_1` was tried and is unsafe on its
                # own. Until int_loopback has its bindings, exempting it means the key reaches
                # lo_prof_spec, which does not declare it, and validate_list_of_dicts DROPS an
                # undeclared profile key. The operator writes a key, the run succeeds, the
                # controller never hears it. That is the failure this rejection exists to
                # prevent, reintroduced by the fix meant to narrow it.
                #
                # Fails closed by construction: an unresolved parent has no bindings, so
                # resolve_binding returns None and the key is refused -- the old behaviour,
                # which is the safe one.
                if (
                    key in profile
                    and parent is not None
                    and parent != LOOPBACK_CARRY_FORWARD_PARENT
                    and resolve_binding(parent, key) is not None
                ):
                    continue
                if key in profile:
                    # No scrubbing here on purpose. Registration already happened for the whole
                    # config in __init__, which is the only placement that survives this loop
                    # rejecting on its first match. See SECRET_PROFILE_KEYS.
                    self.module.fail_json(
                        msg="'{0}' is no longer configurable on a fabric loopback. OSPF "
                        "authentication there is underlay authentication and the fabric owns "
                        "it: set '{1}' in the fabric settings instead. The interface value was "
                        "only ever an override of the fabric's, and a keychain fabric setting "
                        "removed it outright. No change was sent.".format(key, fabric_setting)
                    )
        # The keychain rejection stays on BOTH parents, deliberately unscoped, because each
        # refuses it for its own reason and neither can carry it:
        #
        #   int_fabric_loopback_11_1  declares ospfAuthKeychainName, but its DSL overwrites the
        #                             interface value with fabricSettings' -- the interface field
        #                             is dead, which is what retired it.
        #   int_loopback              does not declare a keychain field at all.
        #
        # Scoping this loop to the fabric parent alongside the one above was tried and reverted:
        # on a user loopback the key would reach lo_prof_spec, which does not declare it either,
        # and validate_list_of_dicts DROPS an undeclared profile key rather than refusing it. The
        # run would report success, the controller would never hear the key, and nothing would
        # tell the operator -- the exact failure this rejection was restored to prevent.
        for cfg_item in cfg:
            profile = cfg_item.get("profile")
            if not isinstance(profile, dict):
                continue
            for key in OSPF_AUTH_KEYCHAIN_PROFILE_KEYS:
                if key in profile:
                    self.module.fail_json(
                        msg="'{0}' is not a dcnm_interface field. On a fabric loopback the OSPF "
                        "authentication keychain is owned by the fabric: fabricSettings writes "
                        "'ospfAuthKeychainName' and overwrites any interface value, so setting "
                        "it here could never take effect -- configure it in the fabric settings. "
                        "On a plain loopback the template declares no keychain field at all. "
                        "Either way the value would be discarded, so it is refused instead. "
                        "No change was sent.".format(key)
                    )

        self.dcnm_intf_validate_interface_input(cfg, lo_spec, lo_prof_spec)

    def dcnm_intf_validate_ethernet_interface_input(self, cfg):

        eth_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list", elements="str"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        eth_prof_spec_trunk = dict(
            mode=dict(required=True, type="str"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(
                type="str", default="jumbo", choices=["jumbo", "default"]
            ),
            speed=dict(type="str", default="Auto"),
            allowed_vlans=dict(type="str", default="none"),
            native_vlan=dict(type="str", default=""),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
            orphan_port=dict(type="bool", default=False),
            enable_cdp=dict(type="bool", default=True),
            enable_monitor=dict(type="bool", default=False),
            enable_pfc=dict(type="bool", default=False),
            duplex=dict(
                type="str", default="auto", choices=["auto", "full", "half"]),
            enable_qos=dict(type="bool", default=False),
            qos_policy=dict(type="str", default=""),
            queuing_policy=dict(type="str", default=""),
        )
        eth_prof_spec_trunk.update(self.dcnm_intf_storm_control_spec())

        eth_prof_spec_trunk.update({
            "fec": dict(type="str", choices=["auto", "fc-fec", "off", "rs-cons16", "rs-fec", "rs-ieee"]),
        })

        eth_prof_spec_access = dict(
            mode=dict(required=True, type="str"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(
                type="str", default="jumbo", choices=["jumbo", "default"]
            ),
            speed=dict(type="str", default="Auto"),
            access_vlan=dict(type="str", default=""),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
            orphan_port=dict(type="bool", default=False),
            enable_cdp=dict(type="bool", default=True),
            enable_monitor=dict(type="bool", default=False),
            enable_pfc=dict(type="bool", default=False),
            duplex=dict(
                type="str", default="auto", choices=["auto", "full", "half"]),
            enable_qos=dict(type="bool", default=False),
            qos_policy=dict(type="str", default=""),
            queuing_policy=dict(type="str", default=""),
        )
        eth_prof_spec_access.update(self.dcnm_intf_storm_control_spec())

        eth_prof_spec_access.update({
            "fec": dict(type="str", choices=["auto", "fc-fec", "off", "rs-cons16", "rs-fec", "rs-ieee"]),
        })

        eth_prof_spec_routed_host = dict(
            int_vrf=dict(type="str", default="default"),
            ipv4_addr=dict(type="ipv4", default=""),
            ipv4_mask_len=dict(type="int", default=8),
            route_tag=dict(type="str", default=""),
            mtu=dict(type="int", default=9216, range_min=576, range_max=9216),
            speed=dict(type="str", default="Auto"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
            enable_qos=dict(type="bool", default=False),
            qos_policy=dict(type="str", default=""),
            queuing_policy=dict(type="str", default=""),
        )

        eth_prof_spec_routed_host.update({
            "fec": dict(type="str", choices=["auto", "fc-fec", "off", "rs-cons16", "rs-fec", "rs-ieee"]),
        })

        eth_prof_spec_epl_routed_host = dict(
            mode=dict(required=True, type="str"),
            ipv4_addr=dict(required=True, type="ipv4"),
            ipv4_mask_len=dict(type="int", default=8),
            ipv6_addr=dict(type="ipv6", default=""),
            ipv6_mask_len=dict(
                type="int", range_min=64, range_max=127, default=64
            ),
            route_tag=dict(type="str", default=""),
            mtu=dict(type="int", default=1500, range_max=9216),
            speed=dict(type="str", default="Auto"),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
        )

        eth_prof_spec_dot1q_tunnel_host = dict(
            mode=dict(required=True, type="str"),
            bpdu_guard=dict(type="str", default="true"),
            port_type_fast=dict(type="bool", default=True),
            mtu=dict(
                type="str", default="jumbo", choices=["jumbo", "default"]
            ),
            speed=dict(type="str", default="Auto"),
            access_vlan=dict(type="str", default=""),
            cmds=dict(type="list", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(type="bool", default=True),
            enable_cdp=dict(type="bool", default=True),
            duplex=dict(
                type="str", default="auto", choices=["auto", "full", "half"]),
        )
        eth_prof_spec_dot1q_tunnel_host.update(
            self.dcnm_intf_storm_control_spec()
        )

        eth_prof_spec_dot1q_tunnel_host.update({
            "fec": dict(type="str", choices=["auto", "fc-fec", "off", "rs-cons16", "rs-fec", "rs-ieee"]),
        })

        # Thin engine: extend the eth spec with registered generic keys the caller set
        # EXPLICITLY (no default), so an omitted key stays dropped exactly as before.
        gie_extend_prof_spec(eth_prof_spec_trunk, "int_trunk_host", cfg[0]["profile"])
        gie_extend_prof_spec(eth_prof_spec_access, "int_access_host", cfg[0]["profile"])
        gie_extend_prof_spec(
            eth_prof_spec_routed_host, "int_routed_host", cfg[0]["profile"]
        )

        if "trunk" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                cfg, eth_spec, eth_prof_spec_trunk
            )
        if "access" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                cfg, eth_spec, eth_prof_spec_access
            )
        if "routed" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                cfg, eth_spec, eth_prof_spec_routed_host
            )
        if "monitor" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(cfg, eth_spec, None)
        if "epl_routed" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                cfg, eth_spec, eth_prof_spec_epl_routed_host
            )
        if "dot1q" == cfg[0]["profile"]["mode"]:
            self.dcnm_intf_validate_interface_input(
                cfg, eth_spec, eth_prof_spec_dot1q_tunnel_host
            )
        if "pvlan" == cfg[0]["profile"]["mode"]:
            # RAW input is validated before any coercion or default: presence, types, VLAN
            # bounds, duplicates and mode compatibility. The spec below then carries NO
            # defaults, so an omitted field stays None and reconciliation sees it as omitted.
            pvlan_errors = pvlan_validate_raw_profile(cfg[0]["profile"])
            if pvlan_errors:
                self.module.fail_json(
                    msg="Invalid parameters in playbook: while processing interface {0}, {1}. "
                    "No change was sent.".format(cfg[0]["name"], "; ".join(pvlan_errors))
                )
            eth_prof_spec_pvlan = dict(
                mode=dict(required=True, type="str"),
                pvlan_mode=dict(required=True, type="str"),
                pvlan_association=dict(type="list", elements="dict"),
                pvlan_mapping=dict(type="list", elements="dict"),
                native_vlan=dict(type="str"),
                allowed_vlans=dict(type="str"),
                description=dict(type="str"),
                admin_state=dict(type="bool"),
                bpdu_guard=dict(type="str"),
                port_type_fast=dict(type="bool"),
                mtu=dict(type="str"),
                speed=dict(type="str"),
                enable_cdp=dict(type="bool"),
                orphan_port=dict(type="bool"),
                duplex=dict(type="str"),
                enable_pfc=dict(type="bool"),
                enable_qos=dict(type="bool"),
                qos_policy=dict(type="str"),
                queuing_policy=dict(type="str"),
                cmds=dict(type="list", elements="str"),
            )
            # The registry companions of int_pvlan_host (disable_lldp_transmit/receive) the caller set explicitly.
            gie_extend_prof_spec(eth_prof_spec_pvlan, "int_pvlan_host", cfg[0]["profile"])
            self.dcnm_intf_validate_interface_input(
                cfg, eth_spec, eth_prof_spec_pvlan
            )

        fec_value = cfg[0]["profile"].get("fec")
        if fec_value is not None:
            if self.ndfc_version is None:
                self.module.fail_json(
                    msg=f"Interface '{cfg[0]['name']}': fec='{fec_value}' requested but "
                    "NDFC version could not be determined. Ensure the controller is reachable."
                )
            if not self._ndfc_version_gte("12.4.1"):
                self.module.fail_json(
                    msg=f"Interface '{cfg[0]['name']}': fec requires NDFC >= 12.4.1 "
                    f"(current: {self.ndfc_version})."
                )

    def dcnm_intf_validate_vlan_interface_input(self, cfg):

        # The two SVI address lists are validated on the RAW profile, before
        # validate_list_of_dicts: that helper turns an explicit null into the default, which
        # would make `null` indistinguishable from omission. Omission and [] must stay distinct.
        raw_profile = cfg[0].get("profile")
        if isinstance(raw_profile, dict):
            for list_key in SVI_ADDRESS_LISTS:
                if list_key not in raw_profile:
                    continue
                try:
                    svi_address_list_from_input(list_key, raw_profile[list_key])
                except SviAddressListError as exc:
                    self.module.fail_json(
                        msg="Invalid parameters in playbook: while processing interface "
                        + str(cfg[0].get("name"))
                        + ", "
                        + str(exc)
                    )

        svi_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list", elements="str"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        svi_prof_spec = dict(
            mode=dict(required=True, type="str"),
            ipv4_addr=dict(type="ipv4", default=""),
            # SVI IPv6 addressing belongs in the native spec, as for int_subif and
            # int_loopback, not in the registry. Registering ipv6_addr made gie_guarded_keys(),
            # a set of profile keys without parents, claim it globally and reject it on
            # int_subif despite native support. Two subinterface tests caught this.
            ipv6_addr=dict(type="ipv6", default=""),
            ipv6_mask_len=dict(type="int", range_min=1, range_max=127, default=""),
            int_vrf=dict(type="str", default="default"),
            mtu=dict(type="int", range_min=68, range_max=9216, default=9216),
            cmds=dict(type="list", default="", elements="str"),
            description=dict(type="str", default=""),
            admin_state=dict(required=True, type="bool", default=True),
            route_tag=dict(type=str, default=""),
            disable_ip_redirects=dict(type="bool", default=True),
            dhcp_server_addr1=dict(type="ipv4", default=""),
            dhcp_server_addr2=dict(type="ipv4", default=""),
            dhcp_server_addr3=dict(type="ipv4", default=""),
            # type="ipv4" like the other three, DELIBERATELY and not by oversight. The template
            # declares all FOUR as `ipAddress` with DisplayName "IPv4 or IPv6 DHCP server N", so
            # the module restricts to IPv4 something the controller accepts in both families --
            # and the body carries a whole branch unreachable from here
            # (`if ":" not in dhcpServerAddrN` -> child vlan_interface_ipv6_dhcp_relay). The
            # limitation applies to all four equally, so lifting it is its own change: mixing it
            # into "add the fourth server" grows the diff for no reason.
            dhcp_server_addr4=dict(type="ipv4", default=""),
            # DHCP_RELAY_SRC_INTF hangs off no server: it is independent and stands alone. The
            # template declares it as type `interface` and normalizes it through
            # Helper.getInterfaceName2, so it travels as a str here and NDFC canonicalizes it.
            dhcp_relay_src_intf=dict(type="str", default=""),
            adv_subnet_in_underlay=dict(type="bool", default=False),
            enable_hsrp=dict(type="bool", default=False),
            enable_netflow=dict(type="bool", default=False),
            # No default on purpose: an omitted list stays None, which the comparison reads as
            # "not requested" (merged preserves, replaced withdraws). [] is an explicit list.
            secondary_gws=dict(type="list", elements="dict"),
            hsrp_secondary_vips=dict(type="list", elements="dict"),
        )

        if cfg[0]["profile"].get("dhcp_server_addr1", "") != "":
            svi_prof_spec["vrf_dhcp1"] = dict(required=True, type="str")
        else:
            svi_prof_spec["vrf_dhcp1"] = dict(type="str", default="")

        if cfg[0]["profile"].get("dhcp_server_addr2", "") != "":
            svi_prof_spec["vrf_dhcp2"] = dict(required=True, type="str")
        else:
            svi_prof_spec["vrf_dhcp2"] = dict(type="str", default="")

        if cfg[0]["profile"].get("dhcp_server_addr3", "") != "":
            svi_prof_spec["vrf_dhcp3"] = dict(required=True, type="str")
        else:
            svi_prof_spec["vrf_dhcp3"] = dict(type="str", default="")

        # Same pattern as the three above, mirroring the template's IsShow:
        #     @(IsMandatory=false, IsShow="dhcpServerAddr4!=null", ...) string vrfDhcp4;
        # The VRF only means anything when there is a server to reach.
        if cfg[0]["profile"].get("dhcp_server_addr4", "") != "":
            svi_prof_spec["vrf_dhcp4"] = dict(required=True, type="str")
        else:
            svi_prof_spec["vrf_dhcp4"] = dict(type="str", default="")

        if cfg[0]["profile"].get("ipv4_addr", False) is not False:
            svi_prof_spec["ipv4_mask_len"] = dict(
                required=True, type="int", range_min=1, range_max=31
            )
        else:
            svi_prof_spec["ipv4_mask_len"] = dict(
                type="int", range_min=1, range_max=31, default=""
            )

        if cfg[0]["profile"].get("enable_hsrp", False) is True:
            svi_prof_spec["hsrp_vip"] = dict(required=True, type="ipv4")
            svi_prof_spec["hsrp_group"] = dict(required=True, type="int")
            svi_prof_spec["preempt"] = dict(type="bool", default=False)
        else:
            svi_prof_spec["hsrp_vip"] = dict(type="ipv4", default="")
            svi_prof_spec["hsrp_group"] = dict(type="int", default="")
            if cfg[0]["profile"].get("preempt", False) is not False:
                self.module.fail_json(
                    msg="Invalid parameters in playbook: while processing interface "
                    + cfg[0]["name"]
                    + ", preempt : Not a valid parameter"
                )
        svi_prof_spec["hsrp_priority"] = dict(
            type="int", range_min=0, range_max=255, default=""
        )
        svi_prof_spec["hsrp_vmac"] = dict(type="str", default="")
        svi_prof_spec["hsrp_version"] = dict(
            type="int", range_min=1, range_max=2, default=""
        )

        if cfg[0]["profile"].get("enable_netflow", False) is True:
            svi_prof_spec["netflow_monitor"] = dict(required=True, type="str")

        # Thin engine: extend the SVI spec with registered generic keys the caller set
        # EXPLICITLY (no default), so an omitted key stays dropped exactly as before. Same
        # plumbing as the eth, port-channel and subinterface parents.
        gie_extend_prof_spec(svi_prof_spec, "int_vlan", cfg[0]["profile"])

        self.dcnm_intf_validate_interface_input(cfg, svi_spec, svi_prof_spec)

    def dcnm_intf_validate_aa_fex_interface_input(self, cfg):

        fex_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        fex_prof_spec = dict(
            mode=dict(required=True, type="str"),
            description=dict(type="str", default=""),
            peer1_members=dict(type="list", default=[], elements="str"),
            peer2_members=dict(type="list", default=[], elements="str"),
            mtu=dict(type="str", default="jumbo"),
            peer1_cmds=dict(type="list", default=[], elements="str"),
            peer2_cmds=dict(type="list", default=[], elements="str"),
            peer1_description=dict(type="str", default=""),
            peer2_description=dict(type="str", default=""),
            admin_state=dict(required=True, type="bool", default=True),
            enable_netflow=dict(type="bool", default=False),
        )

        if cfg[0]["profile"].get("enable_netflow", False) is True:
            fex_prof_spec["netflow_monitor"] = dict(required=True, type="str")

        self.dcnm_intf_validate_interface_input(cfg, fex_spec, fex_prof_spec)

    def dcnm_intf_validate_st_fex_interface_input(self, cfg):

        fex_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        fex_prof_spec = dict(
            mode=dict(required=True, type="str"),
            description=dict(type="str", default=""),
            members=dict(type="list", default=[], elements="str"),
            mtu=dict(type="str", default="jumbo"),
            cmds=dict(type="list", default=[], elements="str"),
            po_description=dict(type="str", default=""),
            admin_state=dict(required=True, type="bool", default=True),
            enable_netflow=dict(type="bool", default=False),
        )

        if cfg[0]["profile"].get("enable_netflow", False) is True:
            fex_prof_spec["netflow_monitor"] = dict(required=True, type="str")

        self.dcnm_intf_validate_interface_input(cfg, fex_spec, fex_prof_spec)

    def dcnm_intf_validate_breakout_interface_input(self, cfg):
        breakout_spec = dict(
            name=dict(required=True, type="str"),
            switch=dict(required=True, type="list"),
            type=dict(required=True, type="str"),
            deploy=dict(type="str", default=True),
            profile=dict(required=True, type="dict"),
        )

        breakout_prof_spec = dict(
            map=dict(required=True, type="str",
                     default="",
                     choices=["10g-4x", "25g-4x", "50g-2x", "50g-4x", "100g-2x", "100g-4x", "200g-2x"]),
        )
        self.dcnm_intf_validate_interface_input(cfg, breakout_spec, breakout_prof_spec)

    def dcnm_intf_validate_delete_state_input(self, cfg):

        del_spec = dict(
            name=dict(required=False, type="str"),
            switch=dict(required=False, type="list", elements="str"),
            deploy=dict(required=False, type="bool", default=True),
        )

        self.dcnm_intf_validate_interface_input(cfg, del_spec, None)

    def dcnm_intf_validate_query_state_input(self, cfg):

        query_spec = dict(
            name=dict(type="str", default=""),
            switch=dict(required=True, type="list", elements="str"),
        )

        self.dcnm_intf_validate_interface_input(cfg, query_spec, None)

    def dcnm_intf_validate_overridden_state_input(self, cfg):

        overridden_spec = dict(
            name=dict(required=False, type="str", default=""),
            switch=dict(required=False, type="list", elements="str"),
        )

        self.dcnm_intf_validate_interface_input(cfg, overridden_spec, None)

    # New Interfaces
    def dcnm_intf_validate_input(self):
        """Parse the playbook values, validate to param specs."""

        # Inputs will vary for each type of interface and for each state. Make specific checks
        # for each case.

        # The two global OSPF-auth validators that used to run here were withdrawn with the
        # fabric-loopback bindings they served. They rejected ospf_auth_key on any interface
        # whose type was not "lo", across the WHOLE config and before dispatch by type -- which
        # made OSPF authentication unregistrable on int_routed_host, int_subif and int_vlan,
        # where it is a self-contained interface feature the fabric has no part in.
        #
        # What remains is the generic parent guard, which is parent-qualified and applies to
        # every registered binding equally.
        if self.module.params["state"] not in ("deleted", "query"):
            self.dcnm_intf_gie_validate_parent_bindings()

        cfg = []
        for item in self.config:

            citem = copy.deepcopy(item)

            cfg.append(citem)

            if self.module.params["state"] == "deleted":
                # config for delete state is different for all interfaces. It may not have the profile
                # construct. So validate deleted state differently
                self.dcnm_intf_validate_delete_state_input(cfg)
            elif self.module.params["state"] == "query":
                # config for query state is different for all interfaces. It may not have the profile
                # construct. So validate query state differently
                self.dcnm_intf_validate_query_state_input(cfg)
            elif (self.module.params["state"] == "overridden") and not (
                any("profile" in key for key in item)
            ):
                # config for overridden state is different for all interfaces. It may not have the profile
                # construct. So validate overridden state differently
                self.dcnm_intf_validate_overridden_state_input(cfg)
            else:
                if "type" not in item:
                    mesg = "Invalid parameters in playbook: {0}".format(
                        "while processing interface " + item["name"] + "\n"
                        'mandatory object "type" missing'
                    )
                    self.module.fail_json(msg=mesg)

                if item["type"] == "pc":
                    self.dcnm_intf_validate_port_channel_input(cfg)
                if item["type"] == "vpc":
                    self.dcnm_intf_validate_virtual_port_channel_input(cfg)
                if item["type"] == "sub_int":
                    self.dcnm_intf_validate_sub_interface_input(cfg)
                if item["type"] == "lo":
                    self.dcnm_intf_validate_loopback_interface_input(cfg)
                if item["type"] == "eth":
                    self.dcnm_intf_validate_ethernet_interface_input(cfg)
                if item["type"] == "svi":
                    self.dcnm_intf_validate_vlan_interface_input(cfg)
                if item["type"] == "st_fex":
                    self.dcnm_intf_validate_st_fex_interface_input(cfg)
                if item["type"] == "aa_fex":
                    self.dcnm_intf_validate_aa_fex_interface_input(cfg)
                if item["type"] == "breakout":
                    self.dcnm_intf_validate_breakout_interface_input(cfg)
            cfg.remove(citem)

    def dcnm_intf_get_pc_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        if delem[profile]["mode"] == "pvlan":
            # Explicit creation payload (D2): the template's own declarations in their declared
            # types. The comparison pass keeps this set for a new port-channel and compares HAVE
            # against it otherwise. Scope was already enforced on the raw input.
            raw = dict(
                (k, v) for k, v in delem[profile].items()
                if k in PO_PROFILE_KEYS and v is not None
            )
            intf["interfaces"][0]["nvPairs"] = pvlan_po_host_nvpairs(raw, ifname)
            # The registry companions of int_port_channel_pvlan_host go through the engine like every other
            # registered parent. An explicit one without an approved patch_version (or below the NDFC floor) refuses
            # the WHOLE batch here, while payloads are built, before any read-modify-write.
            gie_add, gie_err = gie_contribute_nvpairs(
                intf["policy"], delem[profile], getattr(self, "ndfc_version", None),
                getattr(self, "patch_version", None)
            )
            if gie_err:
                self.module.fail_json(msg=gie_err)
            intf["interfaces"][0]["nvPairs"].update(gie_add)
            return

        if delem[profile]["mode"] == "trunk":
            if delem[profile]["members"] is None:
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "MEMBER_INTERFACES"
                ] = ",".join(delem[profile]["members"])
            intf["interfaces"][0]["nvPairs"]["PC_MODE"] = delem[profile][
                "pc_mode"
            ]
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ALLOWED_VLANS"] = delem[profile][
                "allowed_vlans"
            ]
            intf["interfaces"][0]["nvPairs"]["NATIVE_VLAN"] = delem[profile][
                "native_vlan"
            ]
            intf["interfaces"][0]["nvPairs"]["PO_ID"] = ifname
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_ORPHAN_PORT"] = delem[profile]["orphan_port"]
            intf["interfaces"][0]["nvPairs"][
                "CDP_ENABLE"] = delem[profile]["enable_cdp"]
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_PFC"] = delem[profile]["enable_pfc"]
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_MONITOR"] = delem[profile]["enable_monitor"]
            intf["interfaces"][0]["nvPairs"][
                "PORT_DUPLEX_MODE"] = delem[profile]["duplex"]
            if delem[profile].get("disable_lacp_suspend_individual"):
                intf["interfaces"][0]["nvPairs"]["DISABLE_LACP_SUSPEND"] = delem[profile]["disable_lacp_suspend_individual"]
            else:
                intf["interfaces"][0]["nvPairs"]["DISABLE_LACP_SUSPEND"] = False
            if delem[profile].get("lacp_port_priority"):
                intf["interfaces"][0]["nvPairs"]["LACP_PORT_PRIO"] = delem[profile]["lacp_port_priority"]
            else:
                intf["interfaces"][0]["nvPairs"]["LACP_PORT_PRIO"] = 32768
            if delem[profile].get("lacp_rate"):
                intf["interfaces"][0]["nvPairs"]["LACP_RATE"] = delem[profile]["lacp_rate"]
            else:
                intf["interfaces"][0]["nvPairs"]["LACP_RATE"] = "normal"
            self.dcnm_intf_set_qos_nv_pairs(

                delem[profile], intf["interfaces"][0]["nvPairs"]

            )

        if delem[profile]["mode"] == "access":
            if delem[profile]["members"] is None:
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "MEMBER_INTERFACES"
                ] = ",".join(delem[profile]["members"])
            intf["interfaces"][0]["nvPairs"]["PC_MODE"] = delem[profile][
                "pc_mode"
            ]
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ACCESS_VLAN"] = delem[profile][
                "access_vlan"
            ]
            intf["interfaces"][0]["nvPairs"]["PO_ID"] = ifname
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_ORPHAN_PORT"] = delem[profile]["orphan_port"]
            intf["interfaces"][0]["nvPairs"][
                "CDP_ENABLE"] = delem[profile]["enable_cdp"]
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_PFC"] = delem[profile]["enable_pfc"]
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_MONITOR"] = delem[profile]["enable_monitor"]
            intf["interfaces"][0]["nvPairs"][
                "PORT_DUPLEX_MODE"] = delem[profile]["duplex"]
            if delem[profile].get("disable_lacp_suspend_individual"):
                intf["interfaces"][0]["nvPairs"]["DISABLE_LACP_SUSPEND"] = delem[profile]["disable_lacp_suspend_individual"]
            else:
                intf["interfaces"][0]["nvPairs"]["DISABLE_LACP_SUSPEND"] = False
            if delem[profile].get("lacp_port_priority"):
                intf["interfaces"][0]["nvPairs"]["LACP_PORT_PRIO"] = delem[profile]["lacp_port_priority"]
            else:
                intf["interfaces"][0]["nvPairs"]["LACP_PORT_PRIO"] = 32768
            if delem[profile].get("lacp_rate"):
                intf["interfaces"][0]["nvPairs"]["LACP_RATE"] = delem[profile]["lacp_rate"]
            else:
                intf["interfaces"][0]["nvPairs"]["LACP_RATE"] = "normal"
            self.dcnm_intf_set_qos_nv_pairs(

                delem[profile], intf["interfaces"][0]["nvPairs"]

            )

        if delem[profile]["mode"] == "l3":
            if delem[profile]["members"] is None:
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "MEMBER_INTERFACES"
                ] = ",".join(delem[profile]["members"])
            intf["interfaces"][0]["nvPairs"]["PC_MODE"] = delem[profile][
                "pc_mode"
            ]
            intf["interfaces"][0]["nvPairs"]["INTF_VRF"] = delem[profile][
                "int_vrf"
            ]
            intf["interfaces"][0]["nvPairs"]["IP"] = str(
                delem[profile]["ipv4_addr"]
            )
            if delem[profile]["ipv4_addr"] != "":
                intf["interfaces"][0]["nvPairs"]["PREFIX"] = str(
                    delem[profile]["ipv4_mask_len"]
                )
            else:
                intf["interfaces"][0]["nvPairs"]["PREFIX"] = ""
            intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"] = delem[profile][
                "route_tag"
            ]
            intf["interfaces"][0]["nvPairs"]["PO_ID"] = ifname
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )

            self.dcnm_intf_set_qos_nv_pairs(


                delem[profile], intf["interfaces"][0]["nvPairs"]


            )

        if delem[profile]["mode"] == "dot1q":
            if delem[profile]["members"] is None:
                intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "MEMBER_INTERFACES"
                ] = ",".join(delem[profile]["members"])
            intf["interfaces"][0]["nvPairs"]["PC_MODE"] = delem[profile][
                "pc_mode"
            ]
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ACCESS_VLAN"] = delem[profile][
                "access_vlan"
            ]
            intf["interfaces"][0]["nvPairs"]["PO_ID"] = ifname
            self.dcnm_intf_set_qos_nv_pairs(
                delem[profile], intf["interfaces"][0]["nvPairs"]
            )

        if delem[profile]["mode"] == "monitor":
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname

        if delem[profile]["mode"] in ("trunk", "access", "dot1q"):
            self.dcnm_intf_set_storm_control_nv_pairs(
                delem[profile], intf["interfaces"][0]["nvPairs"]
            )

        if delem[profile]["mode"] != "monitor":
            intf["interfaces"][0]["nvPairs"]["COPY_DESC"] = delem[profile][
                "copy_description"
            ]
            intf["interfaces"][0]["nvPairs"]["DESC"] = delem[profile][
                "description"
            ]
            if delem[profile]["cmds"] is None:
                intf["interfaces"][0]["nvPairs"]["CONF"] = ""
            else:
                intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                    delem[profile]["cmds"]
                )
            intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
                delem[profile]["admin_state"]
            ).lower()
            intf["interfaces"][0]["nvPairs"][
                "SPEED"
            ] = self.dcnm_intf_xlate_speed(
                str(delem[profile].get("speed", ""))
            )

        # Thin engine: contribute registered generic parent nvPairs for this port-channel
        # parent (explicit-only, passthrough version fail-closed). Same generic path the eth
        # parents use; no per-feature transport code.
        gie_add, gie_err = gie_contribute_nvpairs(
            intf["policy"], delem[profile], getattr(self, "ndfc_version", None),
            getattr(self, "patch_version", None)
        )
        if gie_err:
            self.module.fail_json(msg=gie_err)
        intf["interfaces"][0]["nvPairs"].update(gie_add)

    def dcnm_intf_get_vpc_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'vpc300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        if delem[profile]["mode"] == "pvlan":
            # The template's own declarations in their declared types, every field EXPLICIT; peer1_* of the playbook
            # follow `switch[0]` and are re-bound to the serial that owns them, in the controller's pair order.
            raw = dict((k, v) for k, v in delem[profile].items() if k in VPC_PROFILE_KEYS and v is not None)
            try:
                legs = pvlan_vpc_pair_view(
                    raw, self.vpc_ip_sn.get(delem["switch"][0], ""), [self.ip_sn.get(s_, "") for s_ in delem["switch"]], ifname)
            except PvlanError as exc:
                self.module.fail_json(msg="vPC {0}: {1}. No change was sent.".format(ifname, exc))
            intf["interfaces"][0]["nvPairs"] = pvlan_vpc_host_nvpairs(raw, ifname, legs)
            # The registry companions of int_vpc_pvlan_host (shared by both peers) go through the engine; an
            # explicit one the caller's context cannot carry refuses the whole batch here, before any write.
            gie_add, gie_err = gie_contribute_nvpairs(
                intf["policy"], delem[profile], getattr(self, "ndfc_version", None),
                getattr(self, "patch_version", None)
            )
            if gie_err:
                self.module.fail_json(msg=gie_err)
            intf["interfaces"][0]["nvPairs"].update(gie_add)
            return

        # Dynamic Peer Mapping: Determine the actual ND PEER1/PEER2 assignment
        # based on the vpc_pair_sn order, regardless of playbook switch order
        peer1_members = delem[profile]["peer1_members"]
        peer2_members = delem[profile]["peer2_members"]
        peer1_allowed_vlans = delem[profile].get("peer1_allowed_vlans")
        peer2_allowed_vlans = delem[profile].get("peer2_allowed_vlans")
        peer1_native_vlan = delem[profile].get("peer1_native_vlan")
        peer2_native_vlan = delem[profile].get("peer2_native_vlan")
        peer1_access_vlan = delem[profile].get("peer1_access_vlan")
        peer2_access_vlan = delem[profile].get("peer2_access_vlan")
        peer1_pcid = delem[profile]["peer1_pcid"]
        peer2_pcid = delem[profile]["peer2_pcid"]
        peer1_description = delem[profile]["peer1_description"]
        peer2_description = delem[profile]["peer2_description"]
        peer1_cmds = delem[profile]["peer1_cmds"]
        peer2_cmds = delem[profile]["peer2_cmds"]

        # Get the vPC pair serial number from ND (format: SERIAL1~SERIAL2)
        vpc_pair_sn = self.vpc_ip_sn.get(delem["switch"][0], "")

        if "~" in vpc_pair_sn:
            vpc_sn_parts = vpc_pair_sn.split("~")
            switch_0_sn = self.ip_sn.get(delem["switch"][0], "")

            if len(delem["switch"]) < 2:
                # Single switch in playbook - swap if it maps to ND's PEER2
                if switch_0_sn == vpc_sn_parts[1]:
                    peer1_members, peer2_members = peer2_members, peer1_members
                    peer1_allowed_vlans, peer2_allowed_vlans = peer2_allowed_vlans, peer1_allowed_vlans
                    peer1_native_vlan, peer2_native_vlan = peer2_native_vlan, peer1_native_vlan
                    peer1_access_vlan, peer2_access_vlan = peer2_access_vlan, peer1_access_vlan
                    peer1_pcid, peer2_pcid = peer2_pcid, peer1_pcid
                    peer1_description, peer2_description = peer2_description, peer1_description
                    peer1_cmds, peer2_cmds = peer2_cmds, peer1_cmds
            else:
                switch_1_sn = self.ip_sn.get(delem["switch"][1], "")

                # Check if playbook switch order matches ND vPC pair order
                if switch_0_sn == vpc_sn_parts[0] and switch_1_sn == vpc_sn_parts[1]:
                    # Playbook order matches ND order - no swap needed
                    pass
                elif switch_0_sn == vpc_sn_parts[1] and switch_1_sn == vpc_sn_parts[0]:
                    # Playbook order is reversed from ND order - swap all peer parameters
                    peer1_members, peer2_members = peer2_members, peer1_members
                    peer1_allowed_vlans, peer2_allowed_vlans = peer2_allowed_vlans, peer1_allowed_vlans
                    peer1_native_vlan, peer2_native_vlan = peer2_native_vlan, peer1_native_vlan
                    peer1_access_vlan, peer2_access_vlan = peer2_access_vlan, peer1_access_vlan
                    peer1_pcid, peer2_pcid = peer2_pcid, peer1_pcid
                    peer1_description, peer2_description = peer2_description, peer1_description
                    peer1_cmds, peer2_cmds = peer2_cmds, peer1_cmds
                else:
                    # Serial numbers don't match vPC pair - this is an error condition
                    self.module.fail_json(
                        msg=f"vPC {ifname} configuration error: Switch serial numbers "
                            f"[{switch_0_sn}, {switch_1_sn}] do not match ND vPC pair "
                            f"[{vpc_sn_parts[0]}, {vpc_sn_parts[1]}]. Verify that the "
                            f"switches specified in the playbook are part of the same vPC pair."
                    )

        if delem[profile]["mode"] == "trunk":

            if peer1_members is None:
                intf["interfaces"][0]["nvPairs"][
                    "PEER1_MEMBER_INTERFACES"
                ] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "PEER1_MEMBER_INTERFACES"
                ] = ",".join(peer1_members)

            if peer2_members is None:
                intf["interfaces"][0]["nvPairs"][
                    "PEER2_MEMBER_INTERFACES"
                ] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "PEER2_MEMBER_INTERFACES"
                ] = ",".join(peer2_members)

            intf["interfaces"][0]["nvPairs"]["PC_MODE"] = delem[profile][
                "pc_mode"
            ]
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["PEER1_ALLOWED_VLANS"] = peer1_allowed_vlans
            intf["interfaces"][0]["nvPairs"]["PEER2_ALLOWED_VLANS"] = peer2_allowed_vlans
            intf["interfaces"][0]["nvPairs"]["PEER1_NATIVE_VLAN"] = peer1_native_vlan
            intf["interfaces"][0]["nvPairs"]["PEER2_NATIVE_VLAN"] = peer2_native_vlan
            if peer1_pcid == 0:
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"] = str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"] = str(peer1_pcid)

            if peer2_pcid == 0:
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"] = str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"] = str(peer2_pcid)

        # dot1q-tunnel carries the same base nvPairs as access: members, PC mode, BPDU guard,
        # port type fast, MTU, per-peer access VLAN (the tunnel VLAN) and per-peer PC IDs, all
        # declared by int_vpc_dot1q_tunnel with the same names. The peer mapping above applies.
        if delem[profile]["mode"] in ("access", "dot1q"):

            if peer1_members is None:
                intf["interfaces"][0]["nvPairs"][
                    "PEER1_MEMBER_INTERFACES"
                ] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "PEER1_MEMBER_INTERFACES"
                ] = ",".join(peer1_members)

            if peer2_members is None:
                intf["interfaces"][0]["nvPairs"][
                    "PEER2_MEMBER_INTERFACES"
                ] = ""
            else:
                intf["interfaces"][0]["nvPairs"][
                    "PEER2_MEMBER_INTERFACES"
                ] = ",".join(peer2_members)

            intf["interfaces"][0]["nvPairs"]["PC_MODE"] = delem[profile][
                "pc_mode"
            ]
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["PEER1_ACCESS_VLAN"] = peer1_access_vlan
            intf["interfaces"][0]["nvPairs"]["PEER2_ACCESS_VLAN"] = peer2_access_vlan

            if peer1_pcid == 0:
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"] = str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER1_PCID"] = str(peer1_pcid)

            if peer2_pcid == 0:
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"] = str(port_id)
            else:
                intf["interfaces"][0]["nvPairs"]["PEER2_PCID"] = str(peer2_pcid)

        intf["interfaces"][0]["nvPairs"]["PEER1_PO_DESC"] = peer1_description
        intf["interfaces"][0]["nvPairs"]["PEER2_PO_DESC"] = peer2_description
        if peer1_cmds is None:
            intf["interfaces"][0]["nvPairs"]["PEER1_PO_CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["PEER1_PO_CONF"] = "\n".join(peer1_cmds)
        if peer2_cmds is None:
            intf["interfaces"][0]["nvPairs"]["PEER2_PO_CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["PEER2_PO_CONF"] = "\n".join(peer2_cmds)
        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
            delem[profile]["admin_state"]
        ).lower()
        intf["interfaces"][0]["nvPairs"]["COPY_DESC"] = delem[profile][
            "copy_description"
        ]
        intf["interfaces"][0]["nvPairs"]["CDP_ENABLE"] = delem[profile]["enable_cdp"]
        if delem[profile].get("disable_lacp_suspend_individual"):
            intf["interfaces"][0]["nvPairs"]["DISABLE_LACP_SUSPEND"] = delem[profile]["disable_lacp_suspend_individual"]
        else:
            intf["interfaces"][0]["nvPairs"]["DISABLE_LACP_SUSPEND"] = False
        if delem[profile].get("enable_lacp_vpc_convergence"):
            intf["interfaces"][0]["nvPairs"]["ENABLE_LACP_VPC_CONV"] = delem[profile]["enable_lacp_vpc_convergence"]
        else:
            intf["interfaces"][0]["nvPairs"]["ENABLE_LACP_VPC_CONV"] = False
        if delem[profile].get("lacp_port_priority"):
            intf["interfaces"][0]["nvPairs"]["LACP_PORT_PRIO"] = delem[profile]["lacp_port_priority"]
        else:
            intf["interfaces"][0]["nvPairs"]["LACP_PORT_PRIO"] = 32768
        if delem[profile].get("lacp_rate"):
            intf["interfaces"][0]["nvPairs"]["LACP_RATE"] = delem[profile]["lacp_rate"]
        else:
            intf["interfaces"][0]["nvPairs"]["LACP_RATE"] = "normal"
        if delem[profile].get("enable_qos"):
            intf["interfaces"][0]["nvPairs"]["ENABLE_QOS"] = delem[profile]["enable_qos"]
            if delem[profile].get("qos_policy"):
                intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = delem[profile]["qos_policy"]
            else:
                intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["ENABLE_QOS"] = False
            intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = ""
        if delem[profile].get("queuing_policy"):
            intf["interfaces"][0]["nvPairs"]["QUEUING_POLICY"] = delem[profile]["queuing_policy"]
        else:
            intf["interfaces"][0]["nvPairs"]["QUEUING_POLICY"] = ""
        self.dcnm_intf_set_storm_control_nv_pairs(
            delem[profile], intf["interfaces"][0]["nvPairs"]
        )
        intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
        intf["interfaces"][0]["nvPairs"]["SPEED"] = self.dcnm_intf_xlate_speed(
            str(delem[profile].get("speed", ""))
        )

        # Thin engine: contribute registered generic parent nvPairs for this vPC parent
        # (explicit-only, passthrough version fail-closed). Same generic path the eth and
        # port-channel parents use; no per-feature transport code.
        #
        # The vPC parent emits no CLI of its own -- it hands every value to an intermediate
        # child and, for DISABLE_LLDP, on to a member. That is the template's business: the
        # value lands here, in the parent's own nvPairs, exactly as it does for a port-channel.
        # These bindings are shared across the pair, not per-peer; the nvPairs carry one
        # GUARD_MODE, not PEER1_/PEER2_ variants.
        gie_add, gie_err = gie_contribute_nvpairs(
            intf["policy"], delem[profile], getattr(self, "ndfc_version", None),
            getattr(self, "patch_version", None)
        )
        if gie_err:
            self.module.fail_json(msg=gie_err)
        intf["interfaces"][0]["nvPairs"].update(gie_add)

    def dcnm_intf_get_sub_intf_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        intf["interfaces"][0]["nvPairs"]["VLAN"] = str(delem[profile]["vlan"])
        intf["interfaces"][0]["nvPairs"]["INTF_VRF"] = delem[profile][
            "int_vrf"
        ]
        ipv4_addr = delem[profile].get("ipv4_addr")
        ipv4_mask_len = delem[profile].get("ipv4_mask_len")
        intf["interfaces"][0]["nvPairs"]["IP"] = (
            "" if ipv4_addr is None else str(ipv4_addr)
        )
        intf["interfaces"][0]["nvPairs"]["PREFIX"] = (
            "" if ipv4_mask_len is None else str(ipv4_mask_len)
        )
        intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"] = delem[profile][
            "route_tag"
        ]
        if delem[profile]["ipv6_addr"]:
            intf["interfaces"][0]["nvPairs"]["IPv6"] = str(
                delem[profile]["ipv6_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["IPv6_PREFIX"] = str(
                delem[profile]["ipv6_mask_len"]
            )
        else:
            intf["interfaces"][0]["nvPairs"]["IPv6"] = ""
            intf["interfaces"][0]["nvPairs"]["IPv6_PREFIX"] = ""
        intf["interfaces"][0]["nvPairs"]["MTU"] = str(delem[profile]["mtu"])
        intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
        intf["interfaces"][0]["nvPairs"]["DESC"] = delem[profile][
            "description"
        ]
        if delem[profile]["cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                delem[profile]["cmds"]
            )
        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
            delem[profile]["admin_state"]
        ).lower()
        intf["interfaces"][0]["nvPairs"]["SPEED"] = self.dcnm_intf_xlate_speed(
            str(delem[profile].get("speed", ""))
        )

        # Thin engine: contribute registered generic parent nvPairs for this subinterface
        # parent (explicit-only, version fail-closed), mirroring the eth path exactly.
        gie_add, gie_err = gie_contribute_nvpairs(
            intf["policy"], delem[profile], getattr(self, "ndfc_version", None),
            getattr(self, "patch_version", None)
        )
        if gie_err:
            self.module.fail_json(msg=gie_err)
        intf["interfaces"][0]["nvPairs"].update(gie_add)

    def dcnm_intf_get_loopback_payload(self, delem, intf, profile):

        # Properties common for all loopback interface modes
        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        intf["interfaces"][0]["nvPairs"]["IP"] = str(
            delem[profile]["ipv4_addr"]
        )
        intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
        intf["interfaces"][0]["nvPairs"]["DESC"] = delem[profile][
            "description"
        ]
        if delem[profile]["cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                delem[profile]["cmds"]
            )
        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
            delem[profile]["admin_state"]
        ).lower()

        intf["interfaces"][0]["nvPairs"]["SPEED"] = self.dcnm_intf_xlate_speed(
            str(delem[profile].get("speed", ""))
        )

        # Properties for mode 'lo' Loopback Interfaces
        if delem[profile]["mode"] == "lo":

            intf["interfaces"][0]["nvPairs"]["INTF_VRF"] = delem[profile][
                "int_vrf"
            ]
            intf["interfaces"][0]["nvPairs"]["V6IP"] = str(
                delem[profile]["ipv6_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["ROUTE_MAP_TAG"] = delem[profile][
                "route_tag"
            ]

        # Properties for mode 'fabric' Loopback Interfaces
        if delem[profile]["mode"] == "fabric":

            intf["interfaces"][0]["nvPairs"]["SECONDARY_IP"] = delem[profile][
                "secondary_ipv4_addr"
            ]
            intf["interfaces"][0]["nvPairs"]["V6IP"] = str(
                delem[profile]["ipv6_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["ROUTE_MAP_TAG"] = delem[profile][
                "route_tag"
            ]
            # The loopback OSPF-auth emission was withdrawn together with its bindings.
            #
            # On this parent OSPF authentication is UNDERLAY authentication and fabricSettings
            # owns it: the template gates the block on `linkStateRouting == "ospf"`, reads
            # OSPF_AUTH_ENABLE / OSPF_AUTH_KEY_ID / OSPF_AUTH_KEY from the fabric, and a
            # keychain fabric setting deletes whatever an interface value created. The module
            # therefore sends none of those nvPairs now.
            #
            # Withdrawing support is not deleting configuration: whatever the controller holds
            # is preserved by the generic HAVE carry-forward, which no longer excludes them.
            # See gie_have_carry_forward_nvpairs and test_gie_loopback_auth_is_fabric_owned.py.
        if delem[profile]["mode"] == "mpls":

            # These properties are read_only properties and are not exposed as
            # properties that can be modified.  They will be updated from the
            # self.have dictionary to reflect the actual values later in the
            # code workflow that walks the want values and compares to have values.
            intf["interfaces"][0]["nvPairs"][
                "DCI_ROUTING_PROTO"
            ] = "PLACE_HOLDER"
            intf["interfaces"][0]["nvPairs"][
                "DCI_ROUTING_TAG"
            ] = "PLACE_HOLDER"

        # Thin engine: contribute registered generic parent nvPairs for whichever loopback parent
        # this is (explicit-only, version fail-closed), mirroring the eth and subif paths exactly.
        #
        # Parent-qualified for free: intf["policy"] is already resolved to int_loopback or
        # int_fabric_loopback_11_1, and the engine keys every binding by (parent, nvpair). A field
        # registered on one is not contributed to the other -- which matters here more than
        # anywhere else, since the two templates sit behind one builder and genuinely differ.
        #
        # Placed at the very end so it runs for BOTH modes: the mode-specific blocks above return
        # nothing and simply fall through to here.
        gie_add, gie_err = gie_contribute_nvpairs(
            intf["policy"], delem[profile], getattr(self, "ndfc_version", None),
            getattr(self, "patch_version", None)
        )
        if gie_err:
            self.module.fail_json(msg=gie_err)
        intf["interfaces"][0]["nvPairs"].update(gie_add)

    def dcnm_intf_get_eth_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        # validate_list_of_dicts materializes an omitted optional FEC value as
        # None. NDFC stores that default as "auto", so serializing None causes
        # a perpetual None-versus-auto diff on subsequent runs.
        if delem[profile]["mode"] == "pvlan":
            # Builder output is the payload for an interface with no PVLAN HAVE: every value
            # comes from the explicit input or the int_pvlan_host template default. The
            # comparison pass replaces it with the reconciled full set whenever HAVE exists.
            raw = dict(
                (k, v) for k, v in delem[profile].items()
                if k in PVLAN_PROFILE_KEYS and v is not None
            )
            try:
                built = pvlan_reconcile(
                    "replaced", raw, ifname, None, None,
                    ndfc_version=getattr(self, "ndfc_version", None),
                    patch_version=getattr(self, "patch_version", None),
                )
            except PvlanError as exc:
                self.module.fail_json(
                    msg="Interface {0}: {1}. No change was sent.".format(ifname, exc)
                )
            intf["interfaces"][0]["nvPairs"] = built["nv"]
            gie_add, gie_err = gie_contribute_nvpairs(
                intf["policy"], delem[profile], getattr(self, "ndfc_version", None),
                getattr(self, "patch_version", None)
            )
            if gie_err:
                self.module.fail_json(msg=gie_err)
            intf["interfaces"][0]["nvPairs"].update(gie_add)
            return

        fec_value = delem[profile].get("fec")
        if fec_value is None:
            fec_value = "auto"

        if delem[profile]["mode"] == "trunk":
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ALLOWED_VLANS"] = delem[profile][
                "allowed_vlans"
            ]
            intf["interfaces"][0]["nvPairs"]["NATIVE_VLAN"] = delem[profile][
                "native_vlan"
            ]
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_ORPHAN_PORT"] = delem[profile]["orphan_port"]
            intf["interfaces"][0]["nvPairs"][
                "CDP_ENABLE"] = delem[profile]["enable_cdp"]
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_PFC"] = delem[profile]["enable_pfc"]
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_MONITOR"] = delem[profile]["enable_monitor"]
            intf["interfaces"][0]["nvPairs"][
                "PORT_DUPLEX_MODE"] = delem[profile]["duplex"]
            if delem[profile].get("enable_qos"):
                intf["interfaces"][0]["nvPairs"]["ENABLE_QOS"] = delem[profile]["enable_qos"]
                if delem[profile].get("qos_policy"):
                    intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = delem[profile]["qos_policy"]
                else:
                    intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = ""
            else:
                intf["interfaces"][0]["nvPairs"]["ENABLE_QOS"] = False
                intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = ""
            if delem[profile].get("queuing_policy"):
                intf["interfaces"][0]["nvPairs"]["QUEUING_POLICY"] = delem[profile]["queuing_policy"]
            else:
                intf["interfaces"][0]["nvPairs"]["QUEUING_POLICY"] = ""
            if self._ndfc_version_gte("12.4.1"):
                intf["interfaces"][0]["nvPairs"]["FEC"] = fec_value
        if delem[profile]["mode"] == "access":
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ACCESS_VLAN"] = delem[profile][
                "access_vlan"
            ]
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_ORPHAN_PORT"] = delem[profile]["orphan_port"]
            intf["interfaces"][0]["nvPairs"][
                "CDP_ENABLE"] = delem[profile]["enable_cdp"]
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_PFC"] = delem[profile]["enable_pfc"]
            intf["interfaces"][0]["nvPairs"][
                "ENABLE_MONITOR"] = delem[profile]["enable_monitor"]
            intf["interfaces"][0]["nvPairs"][
                "PORT_DUPLEX_MODE"] = delem[profile]["duplex"]
            if delem[profile].get("enable_qos"):
                intf["interfaces"][0]["nvPairs"]["ENABLE_QOS"] = delem[profile]["enable_qos"]
                if delem[profile].get("qos_policy"):
                    intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = delem[profile]["qos_policy"]
                else:
                    intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = ""
            else:
                intf["interfaces"][0]["nvPairs"]["ENABLE_QOS"] = False
                intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = ""
            if delem[profile].get("queuing_policy"):
                intf["interfaces"][0]["nvPairs"]["QUEUING_POLICY"] = delem[profile]["queuing_policy"]
            else:
                intf["interfaces"][0]["nvPairs"]["QUEUING_POLICY"] = ""
            if self._ndfc_version_gte("12.4.1"):
                intf["interfaces"][0]["nvPairs"]["FEC"] = fec_value
        if delem[profile]["mode"] == "routed":
            intf["interfaces"][0]["nvPairs"]["INTF_VRF"] = delem[profile][
                "int_vrf"
            ]
            intf["interfaces"][0]["nvPairs"]["IP"] = str(
                delem[profile]["ipv4_addr"]
            )
            if delem[profile]["ipv4_addr"] != "":
                intf["interfaces"][0]["nvPairs"]["PREFIX"] = str(
                    delem[profile]["ipv4_mask_len"]
                )
            else:
                intf["interfaces"][0]["nvPairs"]["PREFIX"] = ""
            intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"] = delem[profile][
                "route_tag"
            ]
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
            if delem[profile].get("enable_qos"):
                intf["interfaces"][0]["nvPairs"]["ENABLE_QOS"] = delem[profile]["enable_qos"]
                if delem[profile].get("qos_policy"):
                    intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = delem[profile]["qos_policy"]
                else:
                    intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = ""
            else:
                intf["interfaces"][0]["nvPairs"]["ENABLE_QOS"] = False
                intf["interfaces"][0]["nvPairs"]["QOS_POLICY"] = ""
            if delem[profile].get("queuing_policy"):
                intf["interfaces"][0]["nvPairs"]["QUEUING_POLICY"] = delem[profile]["queuing_policy"]
            else:
                intf["interfaces"][0]["nvPairs"]["QUEUING_POLICY"] = ""
            if self._ndfc_version_gte("12.4.1"):
                intf["interfaces"][0]["nvPairs"]["FEC"] = fec_value
        if delem[profile]["mode"] == "monitor":
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
        if delem[profile]["mode"] == "epl_routed":
            intf["interfaces"][0]["nvPairs"]["IP"] = str(
                delem[profile]["ipv4_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["PREFIX"] = str(
                delem[profile]["ipv4_mask_len"]
            )
            intf["interfaces"][0]["nvPairs"]["IPv6"] = str(
                delem[profile]["ipv6_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["IPv6_PREFIX"] = str(
                delem[profile]["ipv6_mask_len"]
            )
            intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"] = delem[profile][
                "route_tag"
            ]
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname

        if delem[profile]["mode"] != "monitor":
            intf["interfaces"][0]["nvPairs"]["DESC"] = delem[profile][
                "description"
            ]
            if delem[profile]["cmds"] is None:
                intf["interfaces"][0]["nvPairs"]["CONF"] = ""
            else:
                intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                    delem[profile]["cmds"]
                )
            intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
                delem[profile]["admin_state"]
            ).lower()
            intf["interfaces"][0]["nvPairs"][
                "SPEED"
            ] = self.dcnm_intf_xlate_speed(
                str(delem[profile].get("speed", ""))
            )

        # Thin engine: contribute registered generic parent nvPairs for this eth parent
        # (explicit-only, passthrough version fail-closed). OSPF-MD is not registered for an eth
        # parent; it is engine-transported on the loopback path with its capability compat hook.
        gie_add, gie_err = gie_contribute_nvpairs(
            intf["policy"], delem[profile], getattr(self, "ndfc_version", None),
            getattr(self, "patch_version", None)
        )
        if gie_err:
            self.module.fail_json(msg=gie_err)
        intf["interfaces"][0]["nvPairs"].update(gie_add)

        if delem[profile]["mode"] == "dot1q":
            intf["interfaces"][0]["nvPairs"]["BPDUGUARD_ENABLED"] = delem[
                profile
            ]["bpdu_guard"].lower()
            intf["interfaces"][0]["nvPairs"]["PORTTYPE_FAST_ENABLED"] = str(
                delem[profile]["port_type_fast"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ACCESS_VLAN"] = delem[profile][
                "access_vlan"
            ]
            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
            intf["interfaces"][0]["nvPairs"][
                "CDP_ENABLE"] = delem[profile]["enable_cdp"]
            intf["interfaces"][0]["nvPairs"][
                "PORT_DUPLEX_MODE"] = delem[profile]["duplex"]
            if self._ndfc_version_gte("12.4.1"):
                intf["interfaces"][0]["nvPairs"]["FEC"] = fec_value

        if delem[profile]["mode"] in ("trunk", "access", "dot1q"):
            self.dcnm_intf_set_storm_control_nv_pairs(
                delem[profile], intf["interfaces"][0]["nvPairs"]
            )

    def dcnm_intf_get_st_fex_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'po300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        if delem[profile]["members"] is None:
            intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["MEMBER_INTERFACES"] = ",".join(
                delem[profile]["members"]
            )

        intf["interfaces"][0]["nvPairs"]["MTU"] = str(delem[profile]["mtu"])
        intf["interfaces"][0]["nvPairs"]["PO_ID"] = ifname
        intf["interfaces"][0]["nvPairs"]["FEX_ID"] = port_id
        intf["interfaces"][0]["nvPairs"]["DESC"] = delem["profile"][
            "description"
        ]
        intf["interfaces"][0]["nvPairs"]["PO_DESC"] = delem["profile"][
            "po_description"
        ]
        if delem[profile]["cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                delem[profile]["cmds"]
            )
        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
            delem[profile]["admin_state"]
        ).lower()

        intf["interfaces"][0]["nvPairs"]["ENABLE_NETFLOW"] = str(
            delem[profile]["enable_netflow"]
        ).lower()

        if str(delem[profile]["enable_netflow"]).lower() == "true":
            intf["interfaces"][0]["nvPairs"]["NETFLOW_MONITOR"] = str(
                delem[profile]["netflow_monitor"]
            )

        intf["interfaces"][0]["nvPairs"]["SPEED"] = self.dcnm_intf_xlate_speed(
            str(delem[profile].get("speed", ""))
        )

    def dcnm_intf_get_aa_fex_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'vPC300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        if delem[profile]["peer1_members"] is None:
            intf["interfaces"][0]["nvPairs"]["PEER1_MEMBER_INTERFACES"] = ""
        else:
            intf["interfaces"][0]["nvPairs"][
                "PEER1_MEMBER_INTERFACES"
            ] = ",".join(delem[profile]["peer1_members"])

        if delem[profile]["peer2_members"] is None:
            intf["interfaces"][0]["nvPairs"]["PEER2_MEMBER_INTERFACES"] = ""
        else:
            intf["interfaces"][0]["nvPairs"][
                "PEER2_MEMBER_INTERFACES"
            ] = ",".join(delem[profile]["peer2_members"])

        intf["interfaces"][0]["nvPairs"]["MTU"] = str(delem[profile]["mtu"])
        intf["interfaces"][0]["nvPairs"]["PEER1_PCID"] = port_id
        intf["interfaces"][0]["nvPairs"]["PEER2_PCID"] = port_id
        intf["interfaces"][0]["nvPairs"]["FEX_ID"] = port_id
        intf["interfaces"][0]["nvPairs"]["DESC"] = delem["profile"][
            "description"
        ]
        intf["interfaces"][0]["nvPairs"]["PEER1_PO_DESC"] = delem["profile"][
            "peer1_description"
        ]
        intf["interfaces"][0]["nvPairs"]["PEER2_PO_DESC"] = delem["profile"][
            "peer2_description"
        ]

        if delem[profile]["peer1_cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["PEER1_PO_CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["PEER1_PO_CONF"] = "\n".join(
                delem[profile]["peer1_cmds"]
            )

        if delem[profile]["peer2_cmds"] is None:
            intf["interfaces"][0]["nvPairs"]["PEER2_PO_CONF"] = ""
        else:
            intf["interfaces"][0]["nvPairs"]["PEER2_PO_CONF"] = "\n".join(
                delem[profile]["peer2_cmds"]
            )

        intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
            delem[profile]["admin_state"]
        ).lower()

        intf["interfaces"][0]["nvPairs"]["ENABLE_NETFLOW"] = str(
            delem[profile]["enable_netflow"]
        ).lower()

        if str(delem[profile]["enable_netflow"]).lower() == "true":
            intf["interfaces"][0]["nvPairs"]["NETFLOW_MONITOR"] = str(
                delem[profile]["netflow_monitor"]
            )

        intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname

        intf["interfaces"][0]["nvPairs"]["SPEED"] = self.dcnm_intf_xlate_speed(
            str(delem[profile].get("speed", ""))
        )

    def dcnm_intf_get_svi_payload(self, delem, intf, profile):

        # Extract port id from the given name, which is of the form 'vlan300'

        ifname, port_id = self.dcnm_intf_get_if_name(
            delem["name"], delem["type"]
        )
        intf["interfaces"][0].update({"ifName": ifname})

        if delem[profile]["mode"] == "vlan":
            intf["interfaces"][0]["nvPairs"]["INTF_VRF"] = delem[profile][
                "int_vrf"
            ]
            intf["interfaces"][0]["nvPairs"]["IP"] = str(
                delem[profile]["ipv4_addr"]
            )
            intf["interfaces"][0]["nvPairs"]["PREFIX"] = str(
                delem[profile]["ipv4_mask_len"]
            )
            # int_vlan reads PREFIXv6; int_subif and int_routed_host read IPv6_PREFIX.
            # NDFC would silently discard the wrong name here. Without the prefix, the DSL
            # reaches a bare `except` that clears ipv6_vip and silently skips HSRP IPv6
            # (measured).
            # Emit conditionally: always writing these fields, even empty, adds two nvPairs
            # to every SVI payload. Existing HAVE may omit them, causing a persistent diff.
            # test_dcnm_intf_svi_merged_idempotent and ..._replaced_existing caught this
            # offline before it could produce repeated updates in the lab.
            #
            # With this guard, an SVI without IPv6 retains the previous payload exactly.
            if str(delem[profile].get("ipv6_addr", "")) != "":
                intf["interfaces"][0]["nvPairs"]["IPv6"] = str(
                    delem[profile]["ipv6_addr"]
                )
                intf["interfaces"][0]["nvPairs"]["PREFIXv6"] = str(
                    delem[profile]["ipv6_mask_len"]
                )
            intf["interfaces"][0]["nvPairs"]["MTU"] = str(
                delem[profile]["mtu"]
            )
            intf["interfaces"][0]["nvPairs"]["ROUTING_TAG"] = str(
                delem[profile]["route_tag"]
            )
            intf["interfaces"][0]["nvPairs"]["DISABLE_IP_REDIRECTS"] = str(
                delem[profile]["disable_ip_redirects"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["DESC"] = delem[profile][
                "description"
            ]

            if delem[profile]["cmds"] is None:
                intf["interfaces"][0]["nvPairs"]["CONF"] = ""
            else:
                intf["interfaces"][0]["nvPairs"]["CONF"] = "\n".join(
                    delem[profile]["cmds"]
                )
            # intf["interfaces"][0]["nvPairs"]["CONF"] = str(delem[profile]["cmds"])
            intf["interfaces"][0]["nvPairs"]["ADMIN_STATE"] = str(
                delem[profile]["admin_state"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["ENABLE_HSRP"] = str(
                delem[profile]["enable_hsrp"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["HSRP_VIP"] = str(
                delem[profile]["hsrp_vip"]
            )
            intf["interfaces"][0]["nvPairs"]["HSRP_GROUP"] = str(
                delem[profile]["hsrp_group"]
            )
            if str(delem[profile]["enable_hsrp"]).lower() == "true":
                intf["interfaces"][0]["nvPairs"]["PREEMPT"] = str(
                    delem[profile]["preempt"]
                ).lower()
            else:
                intf["interfaces"][0]["nvPairs"]["PREEMPT"] = str(
                    False
                ).lower()

            intf["interfaces"][0]["nvPairs"]["HSRP_VERSION"] = str(
                delem[profile]["hsrp_version"]
            )
            intf["interfaces"][0]["nvPairs"]["HSRP_PRIORITY"] = str(
                delem[profile]["hsrp_priority"]
            )
            intf["interfaces"][0]["nvPairs"]["MAC"] = str(
                delem[profile]["hsrp_vmac"]
            )
            intf["interfaces"][0]["nvPairs"]["dhcpServerAddr1"] = str(
                delem[profile]["dhcp_server_addr1"]
            )
            intf["interfaces"][0]["nvPairs"]["vrfDhcp1"] = str(
                delem[profile]["vrf_dhcp1"]
            )
            intf["interfaces"][0]["nvPairs"]["dhcpServerAddr2"] = str(
                delem[profile]["dhcp_server_addr2"]
            )
            intf["interfaces"][0]["nvPairs"]["vrfDhcp2"] = str(
                delem[profile]["vrf_dhcp2"]
            )
            intf["interfaces"][0]["nvPairs"]["dhcpServerAddr3"] = str(
                delem[profile]["dhcp_server_addr3"]
            )
            intf["interfaces"][0]["nvPairs"]["vrfDhcp3"] = str(
                delem[profile]["vrf_dhcp3"]
            )
            # Servers 1 to 3 above are written unconditionally; server 4 and the relay source
            # interface are NOT, and the asymmetry is deliberate and measured.
            #
            # Writing them always was implemented first and then measured, rather than assumed
            # either way. Against this lab's controller it would have converged: the HAVE of an
            # SVI created without any DHCP field DOES carry dhcpServerAddr4, vrfDhcp4 and
            # DHCP_RELAY_SRC_INTF, all three as "" (not null) -- 91 nvPairs covering 27 of the
            # 29 parameters int_vlan@0efb09af7f837b30 declares. NDFC fills them from the
            # template even though the module never sent them.
            #
            # But a controller whose GET omits the key is a real case -- an older int_vlan
            # predating the fourth server -- and there the unconditional write does not merely
            # diverge, it CRASHES: nv_keys comes from the payload, the comparison reads HAVE
            # with .get() (None), and then copy_and_add reads it directly,
            #     want[k][0][ik][nk] = d[k][0][ik][nk]        (:6439)
            # -> KeyError: 'dhcpServerAddr4'. Measured, not predicted:
            # test_dcnm_intf_svi_merged_idempotent raises exactly that, because its HAVE
            # fixture carries 26 nvPairs with servers 1-3 and no fourth.
            #
            # The guard costs nothing on a controller that does return the keys and keeps the
            # module working on one that does not. An SVI with no DHCP relay produces exactly
            # the payload it produced before this change.
            # Template compatibility: the nvPair names of server 4 and of the relay source follow the int_vlan body the patch_version
            # selects (svi_dhcp4_fields); vrfDhcp4 is the same in both.
            dhcp4 = dict(svi_dhcp4_fields(self.patch_version))
            if str(delem[profile].get("dhcp_server_addr4", "")) != "":
                intf["interfaces"][0]["nvPairs"][dhcp4["dhcp_server_addr4"]] = str(
                    delem[profile]["dhcp_server_addr4"]
                )
                # vrfDhcp4 hangs off the server, mirroring the template's
                # IsShow="<server 4>!=null". Empty means "the interface VRF".
                intf["interfaces"][0]["nvPairs"][dhcp4["vrf_dhcp4"]] = str(
                    delem[profile]["vrf_dhcp4"]
                )
            # Independent of every server: the relay source interface has no IsShow and gets
            # its own guard.
            if str(delem[profile].get("dhcp_relay_src_intf", "")) != "":
                intf["interfaces"][0]["nvPairs"][dhcp4["dhcp_relay_src_intf"]] = str(
                    delem[profile]["dhcp_relay_src_intf"]
                )
            intf["interfaces"][0]["nvPairs"]["advSubnetInUnderlay"] = str(
                delem[profile]["adv_subnet_in_underlay"]
            ).lower()
            intf["interfaces"][0]["nvPairs"]["ENABLE_NETFLOW"] = str(
                delem[profile]["enable_netflow"]
            ).lower()

            if str(delem[profile]["enable_netflow"]).lower() == "true":
                intf["interfaces"][0]["nvPairs"]["NETFLOW_MONITOR"] = str(
                    delem[profile]["netflow_monitor"]
                )
            else:
                intf["interfaces"][0]["nvPairs"]["NETFLOW_MONITOR"] = ""

            intf["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname

            # The address lists are emitted only when the playbook gives them; an omitted list
            # leaves its nvPair out, exactly as before this feature. The comparison step decides
            # what an omission means for the state (dcnm_intf_reconcile_svi_address_lists).
            for list_key, list_meta in SVI_ADDRESS_LISTS.items():
                requested = delem[profile].get(list_key)
                if requested is not None:
                    intf["interfaces"][0]["nvPairs"][list_meta["nvpair"]] = (
                        svi_address_list_to_wire(
                            list_key, svi_address_list_from_input(list_key, requested)
                        )
                    )

            intf["interfaces"][0]["nvPairs"][
                "SPEED"
            ] = self.dcnm_intf_xlate_speed(
                str(delem[profile].get("speed", ""))
            )

        # Thin engine: contribute registered generic parent nvPairs for this SVI parent
        # (explicit-only, version fail-closed). Deliberately OUTSIDE the mode branch above:
        # the registered keys apply to the parent, not to one SVI mode.
        gie_add, gie_err = gie_contribute_nvpairs(
            intf["policy"], delem[profile], getattr(self, "ndfc_version", None),
            getattr(self, "patch_version", None)
        )
        if gie_err:
            self.module.fail_json(msg=gie_err)
        intf["interfaces"][0]["nvPairs"].update(gie_add)

    # New Interfaces
    def dcnm_get_intf_payload(self, delem, sw):

        intf = {
            "deploy": False,
            "policy": "",
            "interfaceType": "",
            "interfaces": [
                {
                    "serialNumber": "",
                    "interfaceType": "",
                    "ifName": "",
                    "fabricName": "",
                    "nvPairs": {"SPEED": "Auto"},
                }
            ],
            "skipResourceCheck": str(False).lower(),
        }

        # Each interface type will have a different profile name. Set that based on the interface type and use that
        # below to extract the required parameters

        # Monitor ports are not put into diff_deploy, since they don't have any
        # commands to be executed on switch. This will affect the idempotence
        # check

        if delem["type"] == "breakout":
            ifname, port_id = self.dcnm_intf_get_if_name(delem["name"], delem["type"])

            intf = {
                "deploy": delem["deploy"],
                "policy": "breakout_interface",
                "interfaceType": "breakout_interface",
                "interfaces": [
                    {
                        "serialNumber": str(self.ip_sn[sw]),
                        "ifName": ifname,
                        "map": str(delem["profile"]["map"]),
                        "interfaceType": self.int_types[delem["type"]],
                        "fabricName": self.fabric,
                    }
                ]
            }
            return intf

        if delem["profile"]["mode"] == "monitor":
            intf.update({"deploy": False})
        else:
            intf.update({"deploy": delem["deploy"]})

        # Each type of interface and mode will have a different set of params.
        # First fill in the params common to all interface types and modes

        if "vpc" == delem["type"] or "aa_fex" == delem["type"]:
            intf["interfaces"][0].update(
                {"serialNumber": str(self.vpc_ip_sn[sw])}
            )
        else:
            intf["interfaces"][0].update({"serialNumber": str(self.ip_sn[sw])})

        intf["interfaces"][0].update(
            {"interfaceType": self.int_types[delem["type"]]}
        )
        intf["interfaces"][0].update({"fabricName": self.fabric})

        if "profile" not in delem.keys():
            # for state 'deleted', 'profile' construct is not included. So just update the ifName here
            # and return. Rest of the code is all 'profile' specific and hence not required for 'deleted'

            ifname, port_id = self.dcnm_intf_get_if_name(
                delem["name"], delem["type"]
            )
            intf["interfaces"][0].update({"ifName": ifname})
            return intf

        pol_ind_str = delem["type"] + "_" + delem["profile"]["mode"]
        intf.update({"policy": self.pol_types[self.dcnm_version][pol_ind_str]})
        intf.update({"interfaceType": self.int_types[delem["type"]]})

        # Rest of the data in the dict depends on the interface type and the template

        if "pc" == delem["type"]:
            self.dcnm_intf_get_pc_payload(delem, intf, "profile")
        if "sub_int" == delem["type"]:
            self.dcnm_intf_get_sub_intf_payload(delem, intf, "profile")
        if "lo" == delem["type"]:
            self.dcnm_intf_get_loopback_payload(delem, intf, "profile")
        if "vpc" == delem["type"]:
            self.dcnm_intf_get_vpc_payload(delem, intf, "profile")
        if "eth" == delem["type"]:
            self.dcnm_intf_get_eth_payload(delem, intf, "profile")

            # Ethernet interface payload does not have interfaceType and skipResourceCheck flags. Pop
            # them out
            intf.pop("skipResourceCheck")

        if "svi" == delem["type"]:
            self.dcnm_intf_get_svi_payload(delem, intf, "profile")

        if "st_fex" == delem["type"]:
            self.dcnm_intf_get_st_fex_payload(delem, intf, "profile")

        if "aa_fex" == delem["type"]:
            self.dcnm_intf_get_aa_fex_payload(delem, intf, "profile")

        return intf

    def dcnm_intf_merge_intf_info(self, intf_info, if_head):

        if not if_head:
            if_head.append(intf_info)
            return

        for item in if_head:

            if item["policy"] == intf_info["policy"]:
                item["interfaces"].append(intf_info["interfaces"][0])
                return
        if_head.append(intf_info)

    def dcnm_intf_get_want(self):

        if self.config == []:
            return

        if self.intf_info == []:
            return

        # self.intf_info is a list of directories each having config related to a particular interface
        for delem in self.intf_info:
            if any("profile" in key for key in delem):
                for sw in delem["switch"]:
                    intf_payload = self.dcnm_get_intf_payload(delem, sw)
                    if intf_payload["policy"] == "breakout_interface":
                        # Add to self.want_breakout if it's a breakout_interface and not already in self.want
                        if intf_payload not in self.want:
                            self.want_breakout.append(intf_payload)
                    else:
                        # Process non-breakout_interface policies
                        if intf_payload not in self.want:
                            intf = intf_payload["interfaces"][0]["ifName"]
                            is_breakout_format, formatted_interface = self.dcnm_intf_breakout_format(intf)
                            parent_breakout_found, parent_type = self.dcnm_intf_get_parent(intf, sw)
                            # Add breakout interface to self.want only if breakout is configured in state overridden
                            # When state is replaced, we don't check if parent is configured.
                            if is_breakout_format is False or parent_breakout_found is True and self.params['state'] == "overridden":
                                self.want.append(intf_payload)
                            else:
                                self.want.append(intf_payload)

    def dcnm_intf_bulk_fetch_intf_info(self, serialNumber, refresh=False):
        """Bulk-fetch all interface policy details for a switch and populate the cache.

        Instead of making one HTTP GET per interface via IF_WITH_SNO_IFNAME,
        this fetches ALL interfaces for a serial number in a single call and
        caches the results.  Subsequent calls to dcnm_intf_get_intf_info()
        will resolve from the cache in O(1) instead of making a network
        round-trip.

        Parameters:
            serialNumber (str): The serial number of the switch. For VPC/AA_FEX
                                combined serial numbers pass only one side.
        """

        expected_identity = self._dcnm_intf_authority_key(serialNumber)
        query_serial = self._dcnm_intf_query_serial(serialNumber)

        if not refresh and expected_identity in self.intf_detail_cached_snos:
            return

        self.dcnm_intf_invalidate_serial_authority(serialNumber)
        read_reason_clear(self, "detail", serialNumber)
        pvlan_prewrite_note(self, "detail", query_serial, False)

        # Invalidation above runs first on purpose: a skipped read must not leave
        # a stale cache entry behind that would let the authority guard pass.
        if self._dcnm_intf_read_budget_exhausted(serialNumber):
            last = read_reason_get(self, "detail-last-failure", serialNumber)
            skipped = "read skipped: the read budget of this serial is exhausted (no request sent)"
            if last:
                skipped += "; last failed read: {0}".format(last)
            read_reason_note(self, "detail", serialNumber, skipped)
            self.dcnm_intf_mark_detail_unavailable(serialNumber)
            return

        path = self.paths["IF_WITH_SNO"].format(query_serial)

        resp = self._dcnm_intf_get_with_retries(path)

        # Charged up front and refunded only on a proven, fully validated answer.
        # Every rejection below -- HTTP, envelope, shape, identity, duplicate --
        # therefore costs the allowance without needing its own bookkeeping, and
        # a validation branch added later is charged by construction.
        self._dcnm_intf_charge_failed_read(serialNumber)

        if resp == []:
            authorities = {expected_identity, query_serial}
            self.intf_detail_cached_snos.update(authorities)
            self.intf_detail_fetch_failed_snos.difference_update(authorities)
            self._dcnm_intf_clear_failed_reads(serialNumber)
            pvlan_prewrite_note(self, "detail", query_serial, query_serial == serialNumber)
            return

        if not (isinstance(resp, dict) and resp.get("RETURN_CODE") == 200):
            read_reason_note_detail(self, serialNumber, response_failure_reason(resp, 3))
            self.dcnm_intf_mark_detail_unavailable(serialNumber)
            return

        data = resp.get("DATA")
        if not isinstance(data, list):
            read_reason_note_detail(self, serialNumber, "the response DATA is not a list")
            self.dcnm_intf_mark_detail_unavailable(serialNumber)
            return

        entries = {}
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                read_reason_note_detail(self, serialNumber, "item {0} is not an object".format(index))
                self.dcnm_intf_mark_detail_unavailable(serialNumber)
                return
            policy = item.get("policy")
            if not isinstance(policy, str) or policy.strip() == "":
                read_reason_note_detail(self, serialNumber, "item {0} has no policy name".format(index))
                self.dcnm_intf_mark_detail_unavailable(serialNumber)
                return
            interfaces = item.get("interfaces")
            if not isinstance(interfaces, list) or not interfaces:
                read_reason_note_detail(self, serialNumber, "item {0} has no interfaces list".format(index))
                self.dcnm_intf_mark_detail_unavailable(serialNumber)
                return
            for sub, intf in enumerate(interfaces):
                if not isinstance(intf, dict):
                    read_reason_note_detail(self, serialNumber, "record {0}.{1} is not an object".format(index, sub))
                    self.dcnm_intf_mark_detail_unavailable(serialNumber)
                    return
                if_name = intf.get("ifName")
                if not isinstance(if_name, str) or if_name.strip() == "":
                    read_reason_note_detail(self, serialNumber, "record {0}.{1} has no ifName".format(index, sub))
                    self.dcnm_intf_mark_detail_unavailable(serialNumber)
                    return
                response_identity = self._dcnm_intf_bulk_response_identity(
                    intf.get("serialNumber"),
                    intf.get("interfaceType", item.get("interfaceType")),
                    query_serial,
                    serialNumber,
                )
                if response_identity is None:
                    read_reason_note_detail(self, serialNumber,
                                            "record {0}.{1} serialNumber/interfaceType does not identify the queried switch".format(index, sub))
                    self.dcnm_intf_mark_detail_unavailable(serialNumber)
                    return
                if not isinstance(intf.get("nvPairs"), dict):
                    read_reason_note_detail(self, serialNumber, "record {0}.{1} lacks the nvPairs object".format(index, sub))
                    self.dcnm_intf_mark_detail_unavailable(serialNumber)
                    return
                cache_key = (response_identity, if_name.lower())
                if cache_key in entries:
                    read_reason_note_detail(self, serialNumber, "record {0}.{1} duplicates an earlier record of the same interface".format(index, sub))
                    self.dcnm_intf_mark_detail_unavailable(serialNumber)
                    return
                single_item = {k: item[k] for k in item if k != "interfaces"}
                single_item["interfaces"] = [intf]
                entries[cache_key] = single_item

        authorities = {expected_identity, query_serial}
        self.intf_detail_cache.update(entries)
        self.intf_detail_cached_snos.update(authorities)
        self.intf_detail_fetch_failed_snos.difference_update(authorities)
        self._dcnm_intf_clear_failed_reads(serialNumber)
        pvlan_prewrite_note(self, "detail", query_serial, query_serial == serialNumber)

    def dcnm_intf_get_intf_info(self, ifName, serialNumber, ifType):

        # For VPC and AA_FEX interfaces the serialNumber will be a combined one. But GET on interface cannot
        # pass this combined serial number. We will have to pass individual ones

        sno = self._dcnm_intf_authority_key(serialNumber)
        query_serial = self._dcnm_intf_query_serial(serialNumber)

        # Check the bulk-fetched cache first to avoid a per-interface HTTP GET
        cache_key = (sno, ifName.lower())
        cached = self.intf_detail_cache.get(cache_key)
        if cached is not None:
            return cached

        if sno in self.intf_detail_cached_snos:
            return []

        if cache_key in self.intf_detail_authoritative_absent_keys:
            return []

        self.intf_detail_cache.pop(cache_key, None)
        self.intf_detail_authoritative_absent_keys.discard(cache_key)
        self.intf_detail_failed_keys.discard(cache_key)

        # Stale per-key state is cleared above before the read is skipped, for the
        # same reason the bulk reader invalidates first: an unread interface is
        # unavailable, never absent.
        if self._dcnm_intf_read_budget_exhausted(serialNumber):
            self.intf_detail_failed_keys.add(cache_key)
            return []

        path = self.paths["IF_WITH_SNO_IFNAME"].format(query_serial, ifName)
        resp = self._dcnm_intf_get_with_retries(path)

        # Charged up front, refunded only by a validated answer -- see the bulk
        # reader for why the charge precedes the branches rather than following
        # each of them.
        self._dcnm_intf_charge_failed_read(serialNumber)

        if resp == []:
            self.intf_detail_authoritative_absent_keys.add(cache_key)
            self.intf_detail_failed_keys.discard(cache_key)
            self._dcnm_intf_clear_failed_reads(serialNumber)
            return []

        if isinstance(resp, dict) and resp.get("RETURN_CODE") == 200:
            data = resp.get("DATA")
            if isinstance(data, list):
                if len(data) == 0:
                    self.intf_detail_authoritative_absent_keys.add(cache_key)
                    self.intf_detail_failed_keys.discard(cache_key)
                    self._dcnm_intf_clear_failed_reads(serialNumber)
                    return []
                if len(data) == 1 and self._dcnm_intf_valid_individual_entry(
                    data[0], ifName, query_serial, serialNumber
                ):
                    self.intf_detail_cache[cache_key] = data[0]
                    self.intf_detail_failed_keys.discard(cache_key)
                    self._dcnm_intf_clear_failed_reads(serialNumber)
                    return data[0]

        self.intf_detail_failed_keys.add(cache_key)
        return []

    def _dcnm_intf_get_with_retries(self, path):
        """Bounded GET with a controlled transport-exception path.

        Only the dcnm_send call is wrapped, so a transport/API exception becomes a
        failed attempt (not a crash), while a programmer error in the parsing
        logic that follows is NOT masked. Terminates early on a bare [] or on any
        dict carrying RETURN_CODE 200; otherwise returns the last response after
        the retry bound.

        A bare [] is AUTHORITATIVE ABSENCE to both policy-detail callers, not
        unavailability: the bulk reader records the serial as read-and-empty and
        the individual reader records a confirmed absent key. (The sentence that
        used to stand here claimed the opposite and had never matched either
        caller.) This collection's own httpapi cannot produce that shape -- it
        wraps every 2xx in the RETURN_CODE envelope and renders an empty body as
        DATA {} -- so the branch is reachable only from a transport that does not.
        """
        resp = []
        for _attempt in range(3):
            try:
                resp = dcnm_send(self.module, "GET", path)
            except AnsibleConnectionError:
                resp = None
            if resp == [] or (
                isinstance(resp, dict) and resp.get("RETURN_CODE") == 200
            ):
                return resp
            time.sleep(1)
        return resp

    def _dcnm_intf_valid_individual_entry(
        self, entry, ifName, query_serial, expected_serial
    ):
        """A usable individual entry: a dict with exactly one interface whose
        ifName matches the requested interface (wrong identity is unavailable)."""
        if not isinstance(entry, dict):
            return False
        policy = entry.get("policy")
        if not isinstance(policy, str) or policy.strip() == "":
            return False
        interfaces = entry.get("interfaces")
        if not isinstance(interfaces, list) or len(interfaces) != 1:
            return False
        intf = interfaces[0]
        if not isinstance(intf, dict):
            return False
        got = intf.get("ifName")
        return (
            isinstance(got, str)
            and got.strip() != ""
            and got.lower() == ifName.lower()
            and self._dcnm_intf_response_identity(
                intf.get("serialNumber"), query_serial, expected_serial
            ) is not None
            and isinstance(intf.get("nvPairs"), dict)
        )

    @staticmethod
    def _dcnm_intf_serial_parts(serialNumber):
        """Return one or two non-empty serial components, else ``None``."""
        if not isinstance(serialNumber, str) or serialNumber != serialNumber.strip():
            return None
        parts = serialNumber.split("~")
        if len(parts) not in (1, 2) or any(not part for part in parts):
            return None
        return tuple(parts)

    @classmethod
    def _dcnm_intf_query_serial(cls, serialNumber):
        """Return the single serial accepted by an interface GET endpoint."""
        parts = cls._dcnm_intf_serial_parts(serialNumber)
        return parts[0] if parts else None

    @classmethod
    def _dcnm_intf_authority_key(cls, serialNumber):
        """Return the complete logical identity used as the cache key."""
        parts = cls._dcnm_intf_serial_parts(serialNumber)
        return "~".join(parts) if parts else None

    @classmethod
    def _dcnm_intf_normalize_serial(cls, serialNumber):
        """Compatibility alias for callers that need the endpoint query serial."""
        return cls._dcnm_intf_query_serial(serialNumber)

    def _dcnm_intf_known_pair_identities(self):
        """Return authoritative, ordered vPC/AA-FEX identities by casefolded key."""
        known = {}
        for identity in getattr(self, "vpc_ip_sn", {}).values():
            parts = self._dcnm_intf_serial_parts(identity)
            if parts and len(parts) == 2:
                known["~".join(parts).casefold()] = "~".join(parts)
        return known

    def _dcnm_intf_summary_authorities(self, serialNumber):
        """Return identities covered by a switch-summary endpoint query."""
        parts = self._dcnm_intf_serial_parts(serialNumber)
        if parts is None:
            return set()
        query_key = parts[0].casefold()
        authorities = set(parts)
        authorities.add("~".join(parts))
        for pair in self._dcnm_intf_known_pair_identities().values():
            pair_parts = self._dcnm_intf_serial_parts(pair)
            if query_key in {part.casefold() for part in pair_parts}:
                authorities.add(pair)
                authorities.update(pair_parts)
        return authorities

    def _dcnm_intf_response_identity(
        self, response_serial, query_serial, expected_serial, allow_single=False
    ):
        """Validate a response serial and return its complete authority key."""
        response_parts = self._dcnm_intf_serial_parts(response_serial)
        expected_parts = self._dcnm_intf_serial_parts(expected_serial)
        if response_parts is None or expected_parts is None or query_serial is None:
            return None

        query_key = query_serial.casefold()
        if len(response_parts) == 1:
            if response_parts[0].casefold() != query_key:
                return None
            if len(expected_parts) == 2:
                return None
            return self._dcnm_intf_authority_key(expected_serial)

        response_key = "~".join(response_parts).casefold()
        expected_key = self._dcnm_intf_authority_key(expected_serial).casefold()
        known_pairs = self._dcnm_intf_known_pair_identities()
        if query_key not in {part.casefold() for part in response_parts}:
            return None
        if len(expected_parts) == 2:
            if response_key != expected_key:
                return None
            if known_pairs and response_key not in known_pairs:
                return None
            return self._dcnm_intf_authority_key(expected_serial)
        if response_key not in known_pairs:
            return None
        return known_pairs[response_key]

    def _dcnm_intf_bulk_response_identity(
        self, response_serial, interface_type, query_serial, expected_serial
    ):
        """Return the authority represented by one mixed bulk record.

        When the record declares a type, that type decides. When it declares NONE,
        the shape of the serial decides instead.

        That second case is not hypothetical: the bulk endpoint does not return
        ``interfaceType`` at all. Measured against NDFC 12.6.0.267, a vPC record
        carries only ``ifName``, ``nvPairs`` and a combined ``serialNumber``, and
        its enclosing item carries only ``policy`` and ``interfaces``. Requiring
        the type therefore sent every vPC record down the single-serial branch,
        which rejects a combined serial, and one rejection marks the WHOLE switch
        unreadable. Interfaces still in the playbook never noticed -- they skip the
        authority gate -- so the damage only surfaced on a delete-everything run,
        where nothing is in ``want`` and the gate runs over every interface.

        A record that DOES declare a physical type and still carries a combined
        serial remains malformed and is rejected: a physical port belongs to one
        switch, never to a pair.

        For a combined record the check that matters is that the serial we queried
        is one of the two halves: that is what keeps a foreign switch's record out.
        The pair itself needs no corroboration from ``vpc_ip_sn`` here -- the query
        named a single serial and the controller answered with the pair that serial
        belongs to. Requiring corroboration would reintroduce the same failure by
        another route, because ``vpc_ip_sn`` is only ever populated from switches
        named in the playbook and is empty on a delete-everything run.
        """
        response_parts = self._dcnm_intf_serial_parts(response_serial)
        is_pair_record = response_parts is not None and len(response_parts) == 2

        if interface_type in ("INTERFACE_VPC", "AA_FEX"):
            return self._dcnm_intf_response_identity(
                response_serial, query_serial, expected_serial
            )

        if query_serial is None:
            return None

        # Shape decides ONLY when the type is absent. A record that declares a physical
        # type and still carries a combined serial stays malformed and is rejected below:
        # a physical port belongs to one switch, never to a pair.
        if is_pair_record and not interface_type:
            if query_serial.casefold() not in {
                part.casefold() for part in response_parts
            }:
                return None
            identity = "~".join(response_parts)
            expected_parts = self._dcnm_intf_serial_parts(expected_serial)
            if expected_parts is not None and len(expected_parts) == 2:
                # An explicit pair was asked for; the answer must be that same pair.
                expected_key = self._dcnm_intf_authority_key(expected_serial)
                if identity.casefold() != expected_key.casefold():
                    return None
            return identity

        if (
            response_parts is None
            or len(response_parts) != 1
            or response_parts[0].casefold() != query_serial.casefold()
        ):
            return None
        return query_serial

    def dcnm_intf_invalidate_serial_authority(self, serialNumber):
        """Discard every cached authority/failure marker for one serial."""
        parts = self._dcnm_intf_serial_parts(serialNumber)
        if parts is None:
            return
        query_key = parts[0].casefold()
        affected_folded = {
            query_key,
            self._dcnm_intf_authority_key(serialNumber).casefold(),
        }
        if len(parts) == 2:
            affected_folded.update(part.casefold() for part in parts)
        if len(parts) == 2:
            affected_folded.update(
                pair
                for pair in self._dcnm_intf_known_pair_identities()
                if query_key in pair.split("~")
            )
        affected = {
            key
            for key in (
                set(self.intf_detail_cached_snos)
                | set(self.intf_detail_fetch_failed_snos)
                | {item[0] for item in self.intf_detail_cache}
                | {item[0] for item in self.intf_detail_failed_keys}
                | {item[0] for item in self.intf_detail_authoritative_absent_keys}
            )
            if isinstance(key, str) and key.casefold() in affected_folded
        }
        affected.add(self._dcnm_intf_authority_key(serialNumber))
        for mapping in (self.intf_detail_cache,):
            for key in [key for key in mapping if key[0] in affected]:
                mapping.pop(key, None)
        self.intf_detail_cached_snos.difference_update(affected)
        self.intf_detail_fetch_failed_snos.difference_update(affected)
        self.intf_detail_failed_keys = {
            key for key in self.intf_detail_failed_keys if key[0] not in affected
        }
        self.intf_detail_authoritative_absent_keys = {
            key
            for key in self.intf_detail_authoritative_absent_keys
            if key[0] not in affected
        }
        affected_reason_keys = {key.casefold() for key in affected if isinstance(key, str)}
        reasons = _read_reasons(self)
        for key in [key for key in reasons if key[0] == "detail" and key[1] in affected_reason_keys]:
            reasons.pop(key, None)

    def dcnm_intf_get_intf_info_from_dcnm(self, intf):

        return self.dcnm_intf_get_intf_info(
            intf["ifName"], intf["serialNumber"], intf["interfaceType"]
        )

    def dcnm_intf_get_have_all_with_sno(self, sno):
        authority = self._dcnm_intf_authority_key(sno)
        query_serial = self._dcnm_intf_query_serial(sno)
        covered = self._dcnm_intf_summary_authorities(sno)
        covered_folded = {identity.casefold() for identity in covered}
        known_serials = {
            part.casefold()
            for identity in list(getattr(self, "ip_sn", {}).values())
            + list(getattr(self, "vpc_ip_sn", {}).values())
            for part in (self._dcnm_intf_serial_parts(identity) or ())
        }
        known_serials.add(query_serial.casefold())
        self.have_all = [
            item
            for item in self.have_all
            if (
                self._dcnm_intf_authority_key(item.get("serialNo", ""))
                or ""
            ).casefold()
            not in covered_folded
        ]
        self.have_all_cached_snos.difference_update(covered)
        self.have_all_failed_snos.difference_update(covered)
        read_reason_clear(self, "summary", sno)
        path = self.paths["IF_DETAIL_WITH_SNO"].format(query_serial)
        resp = self._dcnm_intf_get_with_retries(path)
        data = resp.get("DATA") if isinstance(resp, dict) else None

        # The entry contract, written ONCE and evaluated in this order with short-circuit, so the decision and the diagnostic
        # (the first unmet requirement) cannot drift apart. Labels name the requirement, never a value.
        def nonempty_str(field):
            return lambda item: isinstance(item.get(field), str) and bool(item.get(field))

        def present(field):
            return lambda item: field in item

        def compliance_reported(item):
            # NDFC reports a logical vPC parent that has not been deployed yet (composite serial) with the key present and
            # null: measured live on 12.6.0.267. Only that shape is accepted without a value. Absent, empty or non-string
            # values, and null on any other entry, are still rejected. The null is stored untouched and is never In-Sync, so
            # every consumer that waits for or acts on convergence keeps comparing against "In-Sync" and does not proceed.
            if nonempty_str("complianceStatus")(item):
                return True
            return (
                item.get("ifType") == "INTERFACE_VPC"
                and "complianceStatus" in item
                and item["complianceStatus"] is None
                and len(self._dcnm_intf_serial_parts(item["serialNo"])) == 2
            )

        entry_checks = (
            ("field ifName missing or empty", nonempty_str("ifName")),
            ("field serialNo missing or empty", nonempty_str("serialNo")),
            ("field serialNo is not one or two serials", lambda item: bool(self._dcnm_intf_serial_parts(item["serialNo"]))),
            ("field serialNo names a switch outside the fabric inventory",
             lambda item: {part.casefold() for part in self._dcnm_intf_serial_parts(item["serialNo"])}.issubset(known_serials)),
            ("field fabricName missing or empty", nonempty_str("fabricName")),
            ("field ifType missing or empty", nonempty_str("ifType")),
            ("field isPhysical missing", present("isPhysical")),
            ("field markDeleted missing", present("markDeleted")),
            ("field alias missing", present("alias")),
            ("field complianceStatus missing or empty", compliance_reported),
            ("field underlayPolicies missing", present("underlayPolicies")),
        )

        def entry_problem(item):
            if not isinstance(item, dict):
                return "is not an object"
            for label, check in entry_checks:
                if not check(item):
                    return label
            return None

        reason = response_failure_reason(resp, 3)
        if reason is None:
            reason = next(("entry {0}: {1}".format(index, problem)
                           for index, problem in ((i, entry_problem(item)) for i, item in enumerate(data)) if problem), None)
        if reason is not None:
            read_reason_note(self, "summary", sno, reason)
            self.have_all_failed_snos.update(covered or {authority})
            return False

        for item in data:
            item_authority = self._dcnm_intf_authority_key(item["serialNo"])
            covered.add(item_authority)
            covered.update(self._dcnm_intf_serial_parts(item["serialNo"]))
        self.have_all.extend(data)
        self.have_all_cached_snos.update(covered or {authority})
        self.have_all_failed_snos.difference_update(covered or {authority})
        return True

    def dcnm_intf_get_have_all_breakout_interfaces(self, sno):
        # This function will get policies for a given serial number and
        # populate the breakout interfaces in self.have_breakout
        authority = self._dcnm_intf_authority_key(sno)
        query_serial = self._dcnm_intf_query_serial(sno)
        path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/policies/switches/{}".format(query_serial)
        resp = self._dcnm_intf_get_with_retries(path)
        data = resp.get("DATA") if isinstance(resp, dict) else None
        valid = (
            isinstance(resp, dict)
            and resp.get("RETURN_CODE") == 200
            and isinstance(data, list)
            and all(
                isinstance(elem, dict)
                and isinstance(elem.get("templateName"), str)
                and (
                    elem.get("templateName") != "breakout_interface"
                    or (
                        isinstance(elem.get("serialNumber"), str)
                        and elem.get("serialNumber")
                        and isinstance(elem.get("entityName"), str)
                        and elem.get("entityName")
                    )
                )
                for elem in data
            )
        )
        if not valid:
            self.have_breakout_failed_snos.add(authority)
            self.have_breakout_cached_snos.discard(authority)
            pvlan_prewrite_note(self, "policies", query_serial, False)
            return False
        # PREWRITE-REUSE: the same switch policy list the PVLAN reader validates (a list of objects), kept for this physical serial
        pvlan_prewrite_note(self, "policies", query_serial, query_serial == sno, copy.deepcopy(data))

        breakout = [
            elem["entityName"]
            for elem in data
            if elem["templateName"] == "breakout_interface"
            and elem["serialNumber"] in self.manageable.values()
        ]
        self.have_breakout.append({authority: breakout})
        self.have_breakout_cached_snos.add(authority)
        self.have_breakout_failed_snos.discard(authority)
        return True

    def dcnm_intf_get_have_all(self, sw):

        # Check if you have already got the details for this switch
        if sw in self.have_all_list:
            return

        # Check if the serial number is a combined one which will be the case for vPC interfaces.
        # If combined, then split it up and pass one of the serial numbers and not the combined one.

        if "~" in self.ip_sn[sw]:
            sno = self.ip_sn[sw].split("~")[0]
        else:
            sno = self.ip_sn[sw]

        summary_ok = self.dcnm_intf_get_have_all_with_sno(sno)
        breakout_ok = self.dcnm_intf_get_have_all_breakout_interfaces(sno)
        if summary_ok and breakout_ok:
            self.have_all_list.append(sw)

    def dcnm_intf_get_have(self):

        if not self.want:
            return

        # Bulk-prefetch interface details for all switches referenced in self.want.
        # This populates the cache so that individual dcnm_intf_get_intf_info calls
        # below become O(1) lookups instead of individual HTTP GETs.
        prefetch_identities = {}
        for elem in self.want:
            for intf in elem["interfaces"]:
                sno = intf.get("serialNumber", "")
                if not sno:
                    continue
                query_serial = self._dcnm_intf_query_serial(sno)
                if query_serial not in prefetch_identities or "~" in sno:
                    prefetch_identities[query_serial] = sno
        for sno in sorted(
            prefetch_identities.values(), key=lambda value: "~" not in value
        ):
            self.dcnm_intf_bulk_fetch_intf_info(sno, refresh=True)

        # We have all the requested interface config in self.want. Interfaces are grouped together based on the
        # policy string and the interface name in a single dict entry.

        for elem in self.want:
            for intf in elem["interfaces"]:
                # For each interface present here, get the information that is already available
                # in DCNM. Based on this information, we will create the required payloads to be sent
                # to the DCNM controller.

                # Fetch the information from DCNM w.r.t to the interafce that we have in self.want
                intf_payload = self.dcnm_intf_get_intf_info_from_dcnm(intf)
                if intf_payload:
                    # Before it can reach a diff, a report or an error quoting it.
                    self.dcnm_intf_register_controller_secrets(intf_payload)
                    self.have.append(intf_payload)

    def dcnm_intf_translate_elements(self, ie1, ie2):

        if sys.version_info[0] >= 3:
            # Python version 3 onwards treats unicode as strings. No special treatment is required
            e1 = ie1
            e2 = ie2
        else:
            if isinstance(
                ie1, unicode  # noqa pylint: disable=undefined-variable
            ):
                e1 = ie1.encode("utf-8")
            else:
                e1 = ie1
            if isinstance(
                ie2, unicode  # noqa pylint: disable=undefined-variable
            ):
                e2 = ie2.encode("utf-8")
            else:
                e2 = ie2

        return e1, e2

    def dcnm_intf_merge_want_and_have(self, key, wvalue, hvalue):

        comb_key = ""
        e1, e2 = self.dcnm_intf_translate_elements(wvalue, hvalue)

        if "CONF" in key:
            if e1 == "":
                comb_key = e2
            elif e2 == "":
                comb_key = e1
            else:
                comb_key = e2 + "\n" + e1
        else:
            if e1 == "":
                comb_key = e2
            elif e2 == "":
                comb_key = e1
            else:
                comb_key = e2 + "," + e1
        return comb_key

    def dcnm_intf_compare_elements(
        self, name, sno, fabric, ie1, ie2, k, state, exact_string=False
    ):

        # unicode encoded strings must be decoded to get proper strings which is required
        # for comparison purposes

        e1, e2 = self.dcnm_intf_translate_elements(ie1, ie2)

        # The keys in key_translate represent a concatenated string. We should split
        # these strings and then compare the values
        key_translate = [
            "MEMBER_INTERFACES",
            "CONF",
            "PEER1_MEMBER_INTERFACES",
            "PEER2_MEMBER_INTERFACES",
            "PEER1_PO_CONF",
            "PEER2_PO_CONF",
        ]

        merge = False

        # Some keys have values given as a list which is encoded into a
        # string. So split that up into list and then use 'set' to process
        # the same irrespective of the order of elements
        if k in key_translate:
            # CONF, PEER1_PO_CONF and PEER2_PO_CONF has '\n' joining the commands
            # MEMBER_INTERFACES, PEER1_MEMBER_INTERFACES, and PEER2_MEMBER_INTERFACES
            # have ',' joining differnet elements. So use a multi-delimiter split
            # to split with any delim
            t_e1 = sorted(re.split(r"[\n,]", e1.strip()))
            t_e2 = sorted(re.split(r"[\n,]", e2.strip()))

            # Merging of aggregate objects (refer objects in key_translate at the top) should happen only for "merged" state.
            if state == "merged":
                merge = True
        elif exact_string:
            # A registered string whose case is part of the value (a secret, an ACL or other
            # object name -- string_compare 'exact' in the registry). Lower-casing it made a
            # case-only change compare equal, so the change was never sent.
            t_e1 = e1
            t_e2 = e2
        else:
            if isinstance(e1, str):
                t_e1 = e1.lower()
            else:
                t_e1 = e1
            if isinstance(e2, str):
                t_e2 = e2.lower()
            else:
                t_e2 = e2

        if k == "STORM_CONTROL_ACTION":
            t_e1 = self.dcnm_intf_normalize_storm_control_action(t_e1)
            t_e2 = self.dcnm_intf_normalize_storm_control_action(t_e2)

        boolean_keys = [
            "ENABLE_ORPHAN_PORT",
            "DISABLE_LACP_SUSPEND",
            "ENABLE_LACP_VPC_CONV",
            "ENABLE_PFC",
            "ENABLE_MONITOR",
            "CDP_ENABLE",
            "ENABLE_QOS",
            "COPY_DESC",
            "ENABLE_STORM_CONTROL",
        ]
        if k in boolean_keys:
            # This is a special case where the value is a boolean and we need to compare it as such
            t_e1 = str(t_e1).lower()
            t_e2 = str(t_e2).lower()

        numeric_keys = [
            "LACP_PORT_PRIO",
            "STORM_CONTROL_BCAST_LEVEL_PPS",
            "STORM_CONTROL_MCAST_LEVEL_PPS",
            "STORM_CONTROL_UCAST_LEVEL_PPS",
            "OSPF_AUTH_KEY_ID",
        ]
        if k in numeric_keys:
            # Controller responses may return numeric nvPairs as strings while
            # desired state keeps them as integers. Normalize both sides so
            # default-valued port-channel/vPC settings remain idempotent.
            try:
                t_e1 = int(t_e1)
                t_e2 = int(t_e2)
            except (TypeError, ValueError):
                pass

        decimal_keys = [
            "STORM_CONTROL_BCAST_LEVEL_PERCENT",
            "STORM_CONTROL_MCAST_LEVEL_PERCENT",
            "STORM_CONTROL_UCAST_LEVEL_PERCENT",
        ]
        if k in decimal_keys:
            try:
                if t_e1 not in (None, ""):
                    t_e1 = Decimal(str(t_e1))
                if t_e2 not in (None, ""):
                    t_e2 = Decimal(str(t_e2))
            except InvalidOperation:
                pass

        if t_e1 != t_e2:

            if (state == "replaced") or (state == "overridden"):
                # Special handling is required for mode 'mpls' loopback interfaces.
                # They will contain either of the following two read_only properties.
                if k in ["DCI_ROUTING_PROTO", "DCI_ROUTING_TAG"]:
                    return "copy_and_add"

                return "add"
            elif state == "merged":
                # If the key is included in config, then use the value from want.
                # If the key is not included in config, then use the value from
                # have.

                # Match and find the corresponding PB input.

                match_pb = [
                    pb
                    for pb in self.pb_input
                    if (
                        (name.lower() == pb["ifname"].lower())
                        and (sno == pb["sno"])
                        and (fabric == pb["fabric"])
                    )
                ]

                pb_keys = list(match_pb[0].keys())
                if self.keymap[k] not in pb_keys:
                    # Copy the value from have, because for 'merged' state we
                    # should leave values that are not specified in config as is.
                    # We copy 'have' because, the validate input would have defaulted the
                    # values for non-mandatory objects.
                    return "copy_and_add"
                else:
                    if merge:
                        return "merge_and_add"
                    return "add"
        return "dont_add"

    def dcnm_intf_reconcile_svi_address_lists(
        self, state, name, want_nv, have_entries, ik, nv_keys, changed_nv
    ):
        """Resolve the two int_vlan address lists against HAVE, in place.

        Runs before the generic nvPair comparison, which then sees either the HAVE text itself
        (no change, nothing reported) or the serialized desired list (a reported change):

            requested   merged                     replaced / retained overridden
            omitted     preserve HAVE              remove every entry
            []          preserve HAVE              remove every entry
            nonempty    union, upsert by address   exact requested membership

        Equality is by membership, so a reordered list is not a change. When the result equals
        HAVE, the HAVE text is carried unchanged instead of relying on how the controller treats
        an absent nvPair. A malformed HAVE fails the run before any request is sent.
        """
        have_nv = next(
            (intf[ik] for intf in have_entries if isinstance(intf.get(ik), dict)), None
        )
        if have_nv is None:
            self.module.fail_json(
                msg="Interface {0}: the controller returned no nvPairs, so the SVI address "
                "lists cannot be compared. No change was sent.".format(name)
            )
        for list_key, list_meta in SVI_ADDRESS_LISTS.items():
            nvpair = list_meta["nvpair"]
            requested = None
            if nvpair in want_nv:
                # The builder emits this nvPair only from a validated playbook list.
                requested = svi_address_list_from_wire(list_key, want_nv[nvpair])
            # A key the controller does not return carries no list; null is not a measured
            # representation and is refused rather than read as empty.
            have_raw = have_nv.get(nvpair, "")
            try:
                have_list = svi_address_list_from_wire(list_key, have_raw)
            except SviAddressListError as exc:
                self.module.fail_json(
                    msg="Interface {0}: {1}. No change was sent.".format(name, exc)
                )
            desired = svi_address_list_desired(state, requested, have_list)
            if len(desired) > SVI_ADDRESS_LIST_MAX:
                self.module.fail_json(
                    msg="Interface {0}: {1} would hold {2} entries after the merge; the "
                    "maximum is {3}. No change was sent.".format(
                        name, list_key, len(desired), SVI_ADDRESS_LIST_MAX)
                )
            if svi_address_list_same(desired, have_list):
                if nvpair in have_nv:
                    want_nv[nvpair] = have_raw
                else:
                    want_nv.pop(nvpair, None)
                    if nvpair in nv_keys:
                        nv_keys.remove(nvpair)
                    changed_nv.pop(nvpair, None)
                continue
            wire = svi_address_list_to_wire(list_key, desired)
            want_nv[nvpair] = wire
            if nvpair not in nv_keys:
                nv_keys.append(nvpair)
            changed_nv[nvpair] = wire

    # ================================================================ native Ethernet PVLAN
    def dcnm_intf_reconcile_svi_dhcp4(self, state, name, want_nv, have_entries, ik, nv_keys, changed_nv, pb_keys):
        """Clear the int_vlan DHCP server 4, its VRF and the relay source interface, in place, before the generic comparison.

        The builder emits these three nvPairs only when non-empty, because a controller whose GET omits them would otherwise make
        the comparison read a missing HAVE key (KeyError in copy_and_add, or a perpetual update). That guard also dropped an
        authored empty, so a clear never reached the request. Here, with HAVE known, the clear is written back as "" only when
        there is something configured to clear:

            HAVE value        missing / null / empty / blank   -> nothing to clear: no key, no write, no KeyError, no perpetual update
                              non-empty string                 -> clear when the state asks for it
            state asks        merged                           -> only an AUTHORED empty (key present in the playbook profile)
                              replaced / retained overridden   -> authored empty OR omission (authoritative reset to "")
            nonempty request  (the builder already emitted it) -> untouched: set/change stays with the generic comparison

        vrfDhcp4 hangs off server 4 (template IsShow="dhcpServerAddr4!=null"): when server 4 is cleared here its VRF is cleared with it,
        also under merged. That one is written directly (not through nv_keys) because the merged comparison would otherwise copy the old
        VRF back from HAVE. Returns True when anything was written. Servers 1-3, the other VRFs and the HSRP fields are not touched.
        """
        have_nv = next((intf[ik] for intf in have_entries if isinstance(intf.get(ik), dict)), None)
        if have_nv is None:
            return False

        # D-F3-1: the stored nvPairs name the template body. When they carry the OTHER body's server-4 / relay-source keys (even
        # blank, or next to the selected ones) and this request sets, clears or (replaced/overridden) resets these fields, the
        # selected names would miss the stored values and only the shared vrfDhcp4 would move. Refused before any write; the
        # family is never switched or guessed. Absence of both families is not a mismatch.
        selected = svi_dhcp4_fields(self.patch_version)
        other = SVI_DHCP4_FIELDS if selected is SVI_DHCP4_FIELDS_SMU else SVI_DHCP4_FIELDS_SMU
        foreign = sorted(nv for key, nv in other if key != "vrf_dhcp4" and nv in have_nv)
        relevant = state in ("replaced", "overridden") or any(key in pb_keys for key, _nv in selected)
        if foreign and relevant:
            self.svi_dhcp4_family_blocked.append({
                "interface": name,
                "selected": [nv for key, nv in selected if key != "vrf_dhcp4"],
                "observed": foreign,
            })
            return False

        def configured(nvpair):
            value = have_nv.get(nvpair)
            return isinstance(value, str) and value.strip() != ""

        server_cleared = False
        written = False
        fields = svi_dhcp4_fields(self.patch_version)
        for profile_key, nvpair in fields:
            if profile_key == "vrf_dhcp4" or nvpair in want_nv:
                continue
            authored = profile_key in pb_keys
            if state == "merged" and not authored:
                continue  # merged: an omission preserves
            if not configured(nvpair):
                continue
            want_nv[nvpair] = ""
            changed_nv[nvpair] = ""
            if nvpair not in nv_keys:
                nv_keys.append(nvpair)
            written = True
            server_cleared = server_cleared or profile_key == "dhcp_server_addr4"
        vrf_key = dict(fields)["vrf_dhcp4"]
        if vrf_key not in want_nv and configured(vrf_key):
            vrf_authored = "vrf_dhcp4" in pb_keys
            if server_cleared or state in ("replaced", "overridden") or vrf_authored:
                want_nv[vrf_key] = ""
                changed_nv[vrf_key] = ""
                written = True
        return written

    def dcnm_intf_pvlan_block(self, name, sno, reason):
        """Collect a refusal; main() raises all of them once, before any write."""
        self.pvlan_blocked.append({"interface": name, "serial": sno, "reason": reason})

    def dcnm_intf_pvlan_member_policies(self):
        return set(self.pol_pc_member_types[self.dcnm_version].values())

    def dcnm_intf_pvlan_read_policies(self, sno):
        """Legacy policy list of a switch, read once per invocation; None when not authoritative."""
        if sno not in self.pvlan_policies:
            read_reason_clear(self, "policies", sno)
            resp = dcnm_send(self.module, "GET", self.paths["PVLAN_SWITCH_POLICIES"].format(self._dcnm_intf_query_serial(sno)))
            data = resp.get("DATA") if isinstance(resp, dict) and resp.get("RETURN_CODE") == 200 else None
            ok = isinstance(data, list) and all(isinstance(p, dict) for p in data)
            self.pvlan_policies[sno] = data if ok else None
            if not ok:
                reason = response_failure_reason(resp, 1) or next(
                    ("element {0} is not an object".format(i) for i, p in enumerate(data) if not isinstance(p, dict)), None)
                read_reason_note(self, "policies", sno, reason or "the policy list is not usable")
        return self.pvlan_policies[sno]

    def dcnm_intf_pvlan_check_ownership(self, name, sno, detail_policy, detail_nv=None, if_type="INTERFACE_ETHERNET",
                                        self_children=frozenset()):
        """Reason the target is not a standalone, directly owned physical Ethernet, or None.

        Two legacy authorities must agree with each other and with the detail read, and each must
        be complete:
          * interface summary (interface/detail): exactly one entry, physical Ethernet, and the
            policy it reports (pvlan_summary_policy) KNOWN: `underlayPolicies` a list holding
            exactly one object with string templateName/policyId/source/entityName/entityType/
            serialNumber for this interface. The MEASURED summary has no top-level `policy`; one,
            when present, must agree. templateName == the detail policy and source '' (direct);
            null, a missing key or source, another container, several entries, a contradiction or
            a non-empty source are refusals;
          * policy listing (control/policies/switches): exactly one non-deleted policy for the
            interface, of entityType INTERFACE, templateName == the detail policy, source '' and
            the same policyId as the summary. A second live policy -- the measured attachment
            shape is a Config_Profile entry with source OVERLAY -- means the port is owned by a
            network attachment;
          * the detail intent, when it carries POLICY_ID, names that same policyId.
        Missing or malformed evidence is never read as direct ownership.
        `self_children`: template names of live child policies whose source is THIS interface itself, set aside before the
        one-policy check (the measured children of a routed member, po_routed_member_self_children); any other policy still refuses."""
        authority = self._dcnm_intf_authority_key(sno)
        if authority not in self.have_all_cached_snos or authority in self.have_all_failed_snos:
            self.dcnm_intf_get_have_all_with_sno(sno)
        if authority not in self.have_all_cached_snos or authority in self.have_all_failed_snos:
            return "the interface summary could not be read authoritatively"
        entries = [
            h for h in self.have_all
            if str(h.get("ifName", "")).lower() == name.lower()
            and self._dcnm_intf_authority_key(h.get("serialNo", "")) == authority
        ]
        if len(entries) != 1:
            return "the interface summary holds {0} entries for this interface".format(len(entries))
        entry = entries[0]
        physical = if_type == "INTERFACE_ETHERNET"
        if entry.get("ifType") != if_type or (str(entry.get("isPhysical")).lower() == "true") != physical:
            return "it is not a standalone physical Ethernet interface" if physical else "it is not a regular port-channel"
        state, summary = pvlan_summary_policy(entry, name)
        if state == PVLAN_SUMMARY_ABSENT:
            return "the interface summary lists no underlay policy, so ownership is unknown"
        if state != PVLAN_SUMMARY_KNOWN:
            return summary
        template = summary["templateName"]
        if template in self.dcnm_intf_pvlan_member_policies():
            return "it is a port-channel or vPC member ({0})".format(template)
        if template != detail_policy:
            return "the summary policy {0!r} disagrees with the detail policy {1!r}".format(template, detail_policy)
        if summary["source"]:
            return "its policy is owned by another resource (source {0})".format(summary["source"])
        if isinstance(detail_nv, dict) and "POLICY_ID" in detail_nv and detail_nv["POLICY_ID"] != summary["policyId"]:
            return "the detail POLICY_ID {0!r} disagrees with the summary policy id {1!r}".format(detail_nv["POLICY_ID"], summary["policyId"])
        policies = self.dcnm_intf_pvlan_read_policies(sno)
        if policies is None:
            return "the switch policy list could not be read authoritatively"
        live = [p for p in policies if str(p.get("entityName", "")).lower() == name.lower() and p.get("deleted") is not True
                and str(p.get("deleted", "")).lower() != "true"]
        live = [p for p in live if not (p.get("templateName") in self_children and str(p.get("source", "")).lower() == name.lower())]
        if len(live) != 1:
            kinds = sorted("{0}/{1}".format(p.get("templateName"), p.get("source")) for p in live)
            return "the switch policy list holds {0} live policies for this interface ({1})".format(len(live), ", ".join(kinds))
        policy = live[0]
        if not (isinstance(policy.get("templateName"), str) and isinstance(policy.get("source"), str) and "deleted" in policy):
            return "the switch policy entry for this interface is malformed"
        if str(policy.get("entityType", "")).upper() != "INTERFACE" or policy["source"] != "" or policy["templateName"] != detail_policy:
            return "the switch policy for this interface is {0}/{1} from source {2!r}, not a direct {3}".format(
                policy.get("entityType"), policy["templateName"], policy["source"], detail_policy)
        if policy.get("policyId") != summary["policyId"]:
            return "the switch policy id {0!r} disagrees with the summary policy id {1!r}".format(policy.get("policyId"), summary["policyId"])
        return None

    def dcnm_intf_pvlan_compare(self, state, want, match_have, name, sno, fabric, deploy):
        """Reconcile one int_pvlan_host WANT against authoritative HAVE (all states).

        Replaces the generic per-nvPair comparison for this parent: the reconciled FULL set is
        what is sent, and the reported diff is computed from that same set."""
        if not match_have:
            self.dcnm_intf_require_detail_authority(name, sno)
            self.dcnm_intf_pvlan_block(
                name, sno,
                "the controller holds no policy for this physical interface; a physical port "
                "is never created through globalInterface",
            )
            return
        if len(match_have) != 1:
            self.dcnm_intf_pvlan_block(name, sno, "current state is ambiguous ({0} entries)".format(len(match_have)))
            return
        have = match_have[0]
        intfs = have.get("interfaces") or []
        have_nv = intfs[0].get("nvPairs") if intfs and isinstance(intfs[0], dict) else None
        if not isinstance(have_nv, dict):
            self.dcnm_intf_pvlan_block(name, sno, "the controller returned no nvPairs for the interface")
            return
        owner = self.dcnm_intf_pvlan_check_ownership(name, sno, have.get("policy"), have_nv)
        if owner:
            self.dcnm_intf_pvlan_block(name, sno, owner)
            return
        match_pb = [
            pb for pb in self.pb_input
            if name.lower() == pb["ifname"].lower() and sno == pb["sno"] and fabric == pb["fabric"]
        ]
        if len(match_pb) != 1:
            self.dcnm_intf_pvlan_block(name, sno, "the playbook names this interface {0} times".format(len(match_pb)))
            return
        raw = dict((k, v) for k, v in match_pb[0].items() if k in PVLAN_PROFILE_KEYS)
        try:
            result = pvlan_reconcile(
                state, raw, name, have.get("policy"), have_nv,
                ndfc_version=getattr(self, "ndfc_version", None), patch_version=getattr(self, "patch_version", None))
        except PvlanError as exc:
            self.dcnm_intf_pvlan_block(name, sno, str(exc))
            return
        if result["blocked"]:
            for reason in result["blocked"]:
                self.dcnm_intf_pvlan_block(name, sno, reason)
            return
        self.pvlan_targets[(sno, name.lower())] = {
            "name": name,
            "sno": sno,
            "pre": (have.get("policy"), copy.deepcopy(have_nv)),
            "post": (PVLAN_POLICY, copy.deepcopy(result["nv"])),
            "new_secondaries": result["new_secondaries"],
            "update": result["update"],
        }
        want["interfaces"][0]["nvPairs"] = result["nv"]
        intf_changed = False
        if result["update"]:
            changed_dict = copy.deepcopy(want)
            changed_dict.pop("skipResourceCheck", None)
            changed_dict["interfaces"][0].pop("interfaceType", None)
            changed_dict["interfaces"][0].pop("fabricName", None)
            changed_dict["interfaces"][0]["nvPairs"] = copy.deepcopy(result["changed"])
            want.pop("interfaceType", None)
            self.dcnm_intf_merge_intf_info(want, self.diff_replace)
            self.changed_dict[0][state].append(changed_dict)
            intf_changed = True
        if str(deploy).lower() == "true":
            if intf_changed:
                match_intf, rc = [], True
            else:
                match_intf, rc = self.dcnm_intf_can_be_added(want)
            if rc:
                delem = {"serialNumber": sno, "ifName": name, "fabricName": self.fabric}
                self.diff_deploy.append(delem)
                self.changed_dict[0]["deploy"].append(copy.deepcopy(delem))
                if match_intf != []:
                    self.changed_dict[0]["debugs"].append(
                        {"Name": name, "SNO": sno, "DeployStatus": match_intf["complianceStatus"]}
                    )

    def dcnm_intf_pvlan_po_member_context(self, member, sno):
        """(problems, policy, nvPairs) of one candidate member's CURRENT intent: bulk detail read,
        once per switch, and an unreadable or unknown interface is a refusal, never absence."""
        self.dcnm_intf_bulk_fetch_intf_info(sno)
        if self.dcnm_intf_detail_unavailable(member, sno):
            return ["its current state could not be read authoritatively"], None, None
        found = self.dcnm_intf_get_intf_info(member, sno, "INTERFACE_ETHERNET")
        if not isinstance(found, dict):
            return ["it is not an existing physical interface known to the controller (preprovisioning is not implemented)"], None, None
        nv = (found.get("interfaces") or [{}])[0].get("nvPairs")
        return [], found.get("policy"), (copy.deepcopy(nv) if isinstance(nv, dict) else None)

    @staticmethod
    def dcnm_intf_pvlan_detail_ifname(detail, name):
        """The detail entry's own ifName when it names `name` (case-insensitively), else `name`."""
        intfs = detail.get("interfaces") if isinstance(detail, dict) else None
        found = intfs[0].get("ifName") if isinstance(intfs, list) and intfs and isinstance(intfs[0], dict) else None
        return found if isinstance(found, str) and found.lower() == str(name).lower() else name

    def dcnm_intf_pvlan_po_member_ifname(self, token, sno):
        """The controller's own interface name for one member token of MEMBER_INTERFACES. MEASURED: a port-channel
        created through Manage lists its member as `e1/8`, which names no interface in the controller's detail (`Ethernet1/8`).
        An explicit port token resolves, through the bulk detail read, to the ONE interface whose name is the same port; the
        detail's spelling is then used everywhere (reads, payloads, claims). Anything else is returned unchanged and is refused
        by the member context as before (never guessed)."""
        canonical = pvlan_po_member_canonical(token)
        if canonical is None:
            return token
        self.dcnm_intf_bulk_fetch_intf_info(sno)
        found = self.intf_detail_cache.get((self._dcnm_intf_authority_key(sno), canonical))
        intfs = found.get("interfaces") if isinstance(found, dict) else None
        name = intfs[0].get("ifName") if isinstance(intfs, list) and len(intfs) == 1 and isinstance(intfs[0], dict) else None
        return name if isinstance(name, str) and pvlan_po_member_canonical(name) == canonical else token

    def dcnm_intf_pvlan_po_compare(self, state, want, match_have, name, sno, fabric, deploy):
        """Reconcile one int_port_channel_pvlan_host WANT.

        Returns "create" when the generic creation path must continue, "done" when this method
        handled the entry (identical repetition) or refused it. Identity is decided here, not by the
        Ethernet filter: a NEW port-channel has no stanza and no policy -- valid absence -- but only
        when BOTH controller authorities are readable and agree; a failed or ambiguous read is a refusal."""
        match_pb = [
            pb for pb in self.pb_input
            if name.lower() == pb["ifname"].lower() and sno == pb["sno"] and fabric == pb["fabric"]
        ]
        if len(match_pb) != 1:
            self.dcnm_intf_pvlan_block(name, sno, "the playbook names this interface {0} times".format(len(match_pb)))
            return "done"
        raw = dict((k, v) for k, v in match_pb[0].items() if k in PO_PROFILE_KEYS and v is not None)
        authority = self._dcnm_intf_authority_key(sno)
        if authority not in self.have_all_cached_snos or authority in self.have_all_failed_snos:
            self.dcnm_intf_get_have_all_with_sno(sno)
        if authority not in self.have_all_cached_snos or authority in self.have_all_failed_snos:
            self.dcnm_intf_pvlan_block(name, sno, "the interface summary could not be read authoritatively")
            return "done"
        entries = [
            h for h in self.have_all
            if str(h.get("ifName", "")).lower() == name.lower()
            and self._dcnm_intf_authority_key(h.get("serialNo", "")) == authority
        ]
        if len(entries) > 1 or len(match_have) > 1:
            self.dcnm_intf_pvlan_block(name, sno, "current state is ambiguous ({0} summary, {1} detail entries)".format(
                len(entries), len(match_have)))
            return "done"
        if not match_have:
            self.dcnm_intf_require_detail_authority(name, sno)
            if entries:
                self.dcnm_intf_pvlan_block(
                    name, sno, "the interface summary lists this port-channel but the interface detail holds no policy")
                return "done"
            policies = self.dcnm_intf_pvlan_read_policies(sno)
            if policies is None:
                self.dcnm_intf_pvlan_block(name, sno, "the switch policy list could not be read authoritatively")
                return "done"
            stray = [p for p in policies if str(p.get("entityName", "")).lower() == name.lower()
                     and p.get("deleted") is not True and str(p.get("deleted", "")).lower() != "true"]
            if stray:
                self.dcnm_intf_pvlan_block(
                    name, sno, "the switch policy list holds {0} live policy(ies) for this absent port-channel".format(len(stray)))
                return "done"
            have_policy, have_nv = None, None
        else:
            have = match_have[0]
            have_policy = have.get("policy")
            intfs = have.get("interfaces") or []
            have_nv = intfs[0].get("nvPairs") if intfs and isinstance(intfs[0], dict) else None
            if not entries:
                self.dcnm_intf_pvlan_block(name, sno, "the interface detail holds a policy but the interface summary lists no entry")
                return "done"
            owner = self.dcnm_intf_pvlan_check_ownership(name, sno, have_policy, have_nv, "INTERFACE_PORT_CHANNEL")
            if owner:
                self.dcnm_intf_pvlan_block(name, sno, owner)
                return "done"
        try:
            result = pvlan_reconcile_po(
                state, raw, name, have_policy, have_nv,
                ndfc_version=getattr(self, "ndfc_version", None), patch_version=getattr(self, "patch_version", None))
        except PvlanError as exc:
            self.dcnm_intf_pvlan_block(name, sno, str(exc))
            return "done"
        if result["blocked"]:
            for reason in result["blocked"]:
                self.dcnm_intf_pvlan_block(name, sno, reason)
            return "done"
        creates = result["creates"]
        if creates:
            unmeasured = pvlan_po_force_unmeasured(result["nv"].get("PVLAN_MODE"))
            if unmeasured:
                self.dcnm_intf_pvlan_block(name, sno, unmeasured)
                return "done"
        members = []
        member_refused = False
        claimed = self.__dict__.setdefault("pvlan_po_claimed", {})
        # The member set comes from the reconciled result (raw for a creation, HAVE for an update in which
        # `members` may be omitted). MM-B: an update may now ADD members (they join exactly as in a creation) and REMOVE members (they are
        # released after the parent's modify and BEFORE the deploy, through the same release contract as a deletion).
        added = set(result.get("added") or [])
        member_names = [self.dcnm_intf_pvlan_po_member_ifname(m, sno)
                        for m in sorted(pvlan_normalize_member_list(result.get("members"))[0])]
        for member in member_names:
            problems, m_policy, m_nv = self.dcnm_intf_pvlan_po_member_context(member, sno)
            joins = creates or pvlan_po_member_canonical(member) in added
            # A conflict known BEFORE any write: two port-channels of this playbook cannot share a member.
            claim_key = (sno, member.lower())
            if claimed.setdefault(claim_key, name.lower()) != name.lower():
                problems.append("the playbook also assigns it to port-channel {0}".format(claimed[claim_key]))
            if not problems and joins:
                if m_policy == PO_MEMBER_POLICY or m_policy in self.dcnm_intf_pvlan_member_policies():
                    problems.append("it is already a port-channel member ({0})".format(m_policy))
                else:
                    problems += pvlan_po_member_baseline_problems(m_policy, m_nv, result["nv"].get("PVLAN_MODE"))
                if not problems:
                    owner = self.dcnm_intf_pvlan_check_ownership(
                        member, sno, m_policy, m_nv,
                        self_children=pvlan_po_routed_member_self_children(m_nv) if m_policy == PVLAN_PO_ROUTED_BASELINE_POLICY else frozenset())
                    if owner:
                        problems.append(owner)
            elif not problems:
                if m_policy != PO_MEMBER_POLICY or str((m_nv or {}).get("PO_ID", "")).lower() != name.lower():
                    problems.append("it is not the member of this port-channel in the controller's intent ({0})".format(m_policy))
            # The host template rewrites every member on each write (HOST:411,529-560): the intended member is
            # always derived from the intended parent; an existing member keeps its own DESC/ADMIN_STATE/CONF.
            post_member_nv = pvlan_po_member_nvpairs(result["nv"], m_nv, current_is_member=not joins)
            if not problems:
                # The member template's own precondition for a LACP rate change (admin down); never forced.
                problems += pvlan_member_lacp_rate_problems(member, m_nv, post_member_nv, not joins)
            if problems:
                for reason in problems:
                    self.dcnm_intf_pvlan_block(member, sno, reason)
                member_refused = True
                continue
            members.append({
                "name": member,
                "pre": (m_policy, copy.deepcopy(m_nv)),
                "post": (PO_MEMBER_POLICY, post_member_nv),
                "joining": joins and not creates,
            })
        removed = []
        if result.get("removed"):
            removed, reasons = self.dcnm_intf_pvlan_po_register_removed(name, sno, result["removed"], deploy)
            for member, reason in reasons:
                self.dcnm_intf_pvlan_block(member, sno, reason)
            member_refused = member_refused or bool(reasons)
        if member_refused:
            return "done"
        self.pvlan_targets[(sno, name.lower())] = {
            "name": name, "sno": sno, "kind": "po", "creates": creates, "update": result["update"],
            "pre": (have_policy, copy.deepcopy(have_nv)) if have_policy else (None, None),
            "post": (PO_HOST_POLICY, copy.deepcopy(result["nv"])),
            "new_secondaries": result["new_secondaries"], "members": members, "removed": removed,
            "deferred_update": bool(removed) and str(deploy).lower() != "true",
        }
        want["interfaces"][0]["nvPairs"] = result["nv"]
        if creates:
            return "create"
        intf_changed = False
        if result["update"]:
            # Update of an existing PVLAN port-channel: the reconciled FULL set is sent through the same replace path
            # as the Ethernet PVLAN update; the reported diff is the delta (merged) or the changed keys (replaced).
            changed_dict = copy.deepcopy(want)
            changed_dict.pop("skipResourceCheck", None)
            changed_dict["interfaces"][0].pop("interfaceType", None)
            changed_dict["interfaces"][0].pop("fabricName", None)
            changed_dict["interfaces"][0]["nvPairs"] = copy.deepcopy(result["changed"])
            want.pop("interfaceType", None)
            self.dcnm_intf_merge_intf_info(want, self.diff_replace)
            self.changed_dict[0][state].append(changed_dict)
            intf_changed = True
        saved = []
        if not intf_changed:
            # Measured (NDFC 12.6.0.267): after a member removal SAVED with deploy false the pending is ONLY the released
            # member's; the port-channel itself stays In-Sync, so an unchanged repetition found nothing to deploy and reported success over
            # that pending. The saved removal is looked for in the controller's own state (dcnm_intf_pvlan_po_saved_removals); an unreadable
            # state refuses instead of being read as "nothing saved".
            saved = self.dcnm_intf_pvlan_po_saved_removals(sno, name, result["nv"])
            if saved is None:
                self.dcnm_intf_pvlan_block(name, sno, "the controller's preview could not be read to rule out a saved member removal")
                return "done"
            if saved and str(deploy).lower() != "true":
                self.result.setdefault("pvlan_saved", []).append({
                    "kind": "po", "name": name, "serial": sno, "operation": "remove member", "members": saved,
                    "state": "saved, awaiting deployment (nothing written by this run)"})
        if str(deploy).lower() == "true":
            if intf_changed or saved:
                match_intf, rc = [], True
            else:
                match_intf, rc = self.dcnm_intf_can_be_added(want)
            if rc:
                delem = {"serialNumber": sno, "ifName": name, "fabricName": self.fabric}
                self.diff_deploy.append(delem)
                self.changed_dict[0]["deploy"].append(copy.deepcopy(delem))
                if match_intf != []:
                    self.changed_dict[0]["debugs"].append(
                        {"Name": name, "SNO": sno, "DeployStatus": match_intf["complianceStatus"]})
        return "done"

    def dcnm_intf_pvlan_po_register_removed(self, name, sno, removed, deploy):
        """MM-B: preconditions of the members an UPDATE removes from an existing PVLAN port-channel, checked before any write (the same as a
        deletion's members, dcnm_intf_pvlan_po_register_deletes): each is this port-channel's int_port_channel_pvlan_member, administratively
        down, whose live policies are exactly the port-channel's; the fabric's host default is down; the bulk update API exists; the update
        is deployed and not in check mode (the release is validated by the pre-deploy gate). Returns ([entries], [(member, reason)]); an entry
        carries the predicted release (int_trunk_host, the template model) until the fresh release replaces it after the parent's modify."""
        entries, reasons = [], []
        names = [self.dcnm_intf_pvlan_po_member_ifname(m, sno) for m in sorted(removed)]
        common = []
        if self.module.check_mode:
            common.append("removing a member from a PVLAN port-channel is refused in check mode: the pre-deploy gate needs the update to exist")
        # Deploy false SAVES the removal (the parent's modify, the member's release corrected, the pending validated by the
        # pre-deploy gate) without deploying it; the deploy-true repetition or the fabric deploy completes it.
        if self.dcnm_intf_pvlan_release_admin_problem():
            common.append(self.dcnm_intf_pvlan_release_admin_problem())
        if not self.module.check_mode and not self.has_bulk_api:
            common.append("the controller's bulk interface update API is not available: the released member's administrative state could not be "
                          "corrected before the deploy")
        for member in names:
            problems = list(common)
            m_problems, m_policy, m_nv = self.dcnm_intf_pvlan_po_member_context(member, sno)
            problems += m_problems
            if not m_problems:
                if m_policy != PO_MEMBER_POLICY or str((m_nv or {}).get("PO_ID", "")).lower() != str(name).lower():
                    problems.append("member {0} is not the member of this port-channel in the controller's intent ({1})".format(member, m_policy))
                elif str((m_nv or {}).get("ADMIN_STATE", "")).strip().lower() not in ("true", "false"):
                    problems.append("member {0} has an unknown administrative state ({1!r})".format(member, (m_nv or {}).get("ADMIN_STATE")))
                else:
                    claims = self.dcnm_intf_pvlan_po_member_claims(member, sno, name)
                    if claims:
                        problems.append(claims)
            if problems:
                reasons += [(member, "removing it from {0}: {1}".format(name, x)) for x in problems]
                continue
            entries.append({"name": member, "pre": (PO_MEMBER_POLICY, copy.deepcopy(m_nv)),
                            "post": (PVLAN_TRUNK_HOST_POLICY, self.dcnm_intf_pvlan_released_model())})
        if entries and not reasons:
            # Never the generic deferred default for a removed member: the release corrects the member itself before the deploy.
            gone = set((sno, e["name"].lower()) for e in entries)
            self.deferred_delete_member_defaults = [
                d for d in (self.deferred_delete_member_defaults or []) if (d.get("serialNumber"), str(d.get("ifName", "")).lower()) not in gone]
        return entries, reasons

    def dcnm_intf_pvlan_po_summary_policy(self, name, sno):
        """Policy template an interface holds according to the interface SUMMARY, or None. Uses ONLY a
        summary this invocation already loaded (no new read): states such as deleted and overridden do
        not populate self.have, and this is the authority they do have. None means "not known here"."""
        authority = self._dcnm_intf_authority_key(sno)
        cached = self.intf_detail_cache.get((authority, str(name).lower()))
        if isinstance(cached, dict) and isinstance(cached.get("policy"), str):
            return cached["policy"]  # the detail the delete/replace flow already read for this interface
        if authority not in self.have_all_cached_snos or authority in self.have_all_failed_snos:
            return None
        entries = [
            h for h in self.have_all
            if str(h.get("ifName", "")).lower() == str(name).lower()
            and self._dcnm_intf_authority_key(h.get("serialNo", "")) == authority
        ]
        if len(entries) != 1:
            return None
        state, summary = pvlan_summary_policy(entries[0], name)
        return summary["templateName"] if state == PVLAN_SUMMARY_KNOWN else None

    def dcnm_intf_pvlan_requested_conflicts(self):
        """Membership conflicts inside the REQUESTED set, decided from the parsed WANT list before any
        comparison or write, independent of the order of `config`. The HAVE-based controls only see policies the
        controller holds today; a member that is about to be created here still holds its old policy there.

        With at least one new PVLAN port-channel in the invocation, for each of its members on its switch:
          * the same port requested directly (any profile) is refused: the two writes are not ordered or reconciled
            in this delivery;
          * the same port claimed by ANOTHER port-channel (PVLAN or not; vPC peers on their own serial) is refused;
          * a competing member entry that does not resolve to explicit ports (for example a range) is refused with an
            explanation, because a conflict with the PVLAN parent cannot be excluded.
        Without a PVLAN port-channel in the invocation nothing here runs, so ordinary Po/vPC flows are unchanged. Two PVLAN
        port-channels sharing a member keep their own check (pvlan_po_claimed). No read, no transport."""
        claims = {}
        parents = set()
        for want in self.want:
            if want.get("policy") not in (PO_HOST_POLICY, VPC_HOST_POLICY):
                continue
            intf = want["interfaces"][0]
            parents.add(id(want))
            if want.get("policy") == VPC_HOST_POLICY:
                # Each peer claims ITS member on ITS serial (PEERn follows the pair order).
                pair = str(intf["serialNumber"]).split("~")
                for key, index in (("PEER1_MEMBER_INTERFACES", 0), ("PEER2_MEMBER_INTERFACES", 1)):
                    names, _bad = pvlan_normalize_member_list((intf.get("nvPairs") or {}).get(key))
                    for port in names:
                        if index < len(pair):
                            claims.setdefault((pair[index], port), intf["ifName"])
                continue
            names, _bad = pvlan_normalize_member_list((intf.get("nvPairs") or {}).get("MEMBER_INTERFACES"))
            for port in names:
                claims.setdefault((intf["serialNumber"], port), intf["ifName"])
        if not claims:
            return
        claimed_serials = set(serial for serial, _port in claims)
        for want in self.want:
            if id(want) in parents:
                continue
            intf = want["interfaces"][0]
            name, sno = intf.get("ifName", ""), intf.get("serialNumber", "")
            direct, _bad = pvlan_normalize_member_list(name)
            for port in direct:
                owner = claims.get((sno, port))
                if owner:
                    self.dcnm_intf_pvlan_block(
                        name, sno,
                        "it is claimed as a member of PVLAN port-channel {0} and is also requested directly in this "
                        "invocation; the two changes are not ordered or reconciled in this delivery, so request only one".format(owner))
            nv = intf.get("nvPairs") or {}
            serials = str(sno).split("~")
            for key, index in (("MEMBER_INTERFACES", 0), ("PEER1_MEMBER_INTERFACES", 0), ("PEER2_MEMBER_INTERFACES", 1)):
                if not nv.get(key) or index >= len(serials) or serials[index] not in claimed_serials:
                    continue
                serial = serials[index]
                names, unresolved = pvlan_normalize_member_list(nv.get(key))
                for port in sorted(names):
                    owner = claims.get((serial, port))
                    if owner:
                        self.dcnm_intf_pvlan_block(
                            name, serial,
                            "member {0} is also claimed by port-channel {1} in this invocation".format(port, owner))
                for token in unresolved:
                    self.dcnm_intf_pvlan_block(
                        name, serial,
                        "member entry {0!r} cannot be resolved to an explicit port name, so a conflict with a PVLAN "
                        "port-channel of this invocation cannot be excluded; list the ports explicitly".format(token))

    def dcnm_intf_pvlan_po_assess(self, blocks, entry, target):
        """One decision for a port-channel target from ONE fresh preview entry: the parent (a NEW
        parent has no running stanza: valid absence) and every member, each against its own model."""
        parts = [(target["name"], target["pre"], target["post"], target["pre"][0] is None, None)]
        # A physical interface JOINING the port-channel (it was a standalone trunk host) gets its PVLAN mode and list
        # through the controller's `channel-group N force mode M` (MEASURED for host; INFERRED for the other
        # modes); see po_member_force_transition().
        po_number = re.match(r"^port-channel([0-9]+)$", str(target["name"]).lower())
        po_nv = target["post"][1] or {}
        joining = {"po_number": po_number.group(1), "pc_mode": str(po_nv.get("PC_MODE", "")),
                   "mode": po_nv.get("PVLAN_MODE")} if po_number else None
        # A member PREPARED as access/routed joins through the same force (measured for trunk secondary); `baseline` lets
        # the transition apply the prepared member's measured specifics. MM-B: a member ADDED by an update joins exactly the same way
        # (the force form is MEASURED for a creation; for an added member of an existing port-channel it is INFERRED).
        parts += [(m["name"], m["pre"], m["post"], False,
                   dict(joining, baseline=m["pre"][0])
                   if joining and (target.get("creates") or m.get("joining"))
                   and m["pre"][0] in (PVLAN_TRUNK_HOST_POLICY,) + tuple(PVLAN_PO_PREPARED_BASELINES)
                   else None)
                  for m in target["members"]]
        # Measured: an EXISTING member inherits the parent's PVLAN changes on the device,
        # with no member pending; that is accepted only when the port-channel's own pending carries changes this same gate
        # validates (po_member_inherited_state()).
        parent_changes = bool(blocks.get(str(target["name"]).lower())) and not target.get("creates")
        # Measured: an EXISTING member of an updated port-channel may be re-emitted with
        # `channel-group N force mode M` for this same port-channel; po_member_force_reassertion() decides, without assuming any
        # device effect of the command.
        reassert = {"po_number": po_number.group(1), "pc_mode": str(po_nv.get("PC_MODE", ""))} if po_number and not target.get("creates") else None
        # Measured: the member's `mtu 9216` withdrawal may be carried by the parent's own `no mtu 9216`
        # (po_member_mtu_inherited_state); the parent's decision is known before its members are assessed (parts[0] is the parent).
        mtu_ctx = None
        decisions, problems = [], []
        for pname, pre, post, absent_ok, member_force in parts:
            existing_member = pre[0] == PO_MEMBER_POLICY and pname != target["name"]
            decision, found = pvlan_assess_target(
                blocks.get(pname.lower(), []), entry, pname, pvlan_render(*post),
                pvlan_transition_vocabulary(pre, post), absent_ok=absent_ok, member_force=member_force,
                member_inherit=target["name"] if parent_changes and pre[0] == PO_MEMBER_POLICY else None,
                member_reassert=reassert if existing_member else None,
                member_mtu_inherit=mtu_ctx if existing_member else None,
                # SP1 (DIAG-measured): the member's `speed 1000` addition / withdrawal carried by THIS port-channel's own pending
                member_speed_inherit=mtu_ctx if existing_member else None)
            if pname == target["name"] and reassert:
                mtu_ctx = dict(reassert, parent=target["name"], parent_desired=pvlan_render(*post),
                               parent_vocabulary=pvlan_transition_vocabulary(pre, post),
                               parent_body=blocks.get(pname.lower(), []), parent_ok=decision == "deploy" and not found)
            decisions.append(decision)
            problems.extend("{0}: {1}".format(pname, f) for f in found)
        # MM-B: a member REMOVED by the update is assessed like a deleted port-channel's member: the FRESH release modeled after the
        # parent's modify (never the prediction), its membership withdrawn with the force command form when deployed (MEASURED for a
        # deletion, INFERRED for a removal) and the rest of its pending taken to the released state.
        for m in target.get("removed") or []:
            if not m.get("released"):
                decisions.append("refuse")
                problems.append("{0}: the removed member was not released before the deploy".format(m["name"]))
                continue
            body = blocks.get(m["name"].lower(), [])
            if po_number:
                body, found = pvlan_po_member_force_withdrawal(body, po_number.group(1), str(po_nv.get("PC_MODE", "")))
                if found:
                    decisions.append("refuse")
                    problems.extend("{0}: {1}".format(m["name"], f) for f in found)
                    continue
            decision, found = pvlan_assess_target(body, entry, m["name"], pvlan_render(*m["post"]), pvlan_transition_vocabulary(m["pre"], m["post"]),
                                                  release=True)
            decisions.append(decision)
            problems.extend("{0}: {1}".format(m["name"], f) for f in found)
        if "refuse" in decisions:
            return "refuse", problems
        if all(d == "converged" for d in decisions):
            return "converged", []
        return "deploy", []

    def dcnm_intf_pvlan_po_register_deletes(self):
        """Deletion of an EXISTING PVLAN port-channel named in a `deleted` invocation, through the generic
        port-channel path (interface/markdelete + globalInterface/deploy, MEASURED for a regular trunk Po in
        an earlier state-withdrawal measurement). Registered here, before the guard that refuses any other route to a PVLAN
        port-channel, only when every precondition holds; otherwise the deletion is refused before any write:
          * one live direct int_port_channel_pvlan_host owner (two authorities), one or more explicit physical members;
          * the member holds int_port_channel_pvlan_member of THIS port-channel and is administratively down, and its only
            other live policy can be the parent's 'Inherited Commands' int_eth child (both with the port-channel as
            source, as measured); anything else on the member is refused;
          * the fabric's host default is administratively down (HOST_INTF_ADMIN_STATE false): the supported contract is
            a standalone SHUTDOWN member. This is NOT how the controller releases the member -- MEASURED: the
            mark-delete leaves it int_trunk_host with ADMIN_STATE "true" -- so the release step corrects it (below);
          * the controller's bulk interface update API is available (the member correction uses it);
          * deploy is requested and the run is not in check mode (the gate needs the fresh preview).
        After the mark-delete and BEFORE any deploy, dcnm_intf_pvlan_po_release_members()
        proves the released member's ownership afresh and, when needed, sets ONLY its ADMIN_STATE to "false" with its
        complete writable nvPairs (legacy interface/modify, per-item outcome, readback). The released member's expected
        state stays PO_RELEASED_MEMBER_NV; the pre-deploy gate and the post-deploy readback verify it.
        An `overridden` sweep puts every PVLAN port-channel of its scope that the request no longer wants in the SAME
        diff_delete list, so it is registered here exactly like a named deletion (same preconditions, same release path)."""
        if self.module.params.get("state") not in ("deleted", "overridden"):
            return
        deploys = set(
            (d.get("serialNumber"), str(d.get("ifName", "")).lower()) for g in self.diff_delete_deploy for d in (g or []))
        for group in self.diff_delete:
            for delem in group or []:
                name, sno = delem.get("ifName", ""), delem.get("serialNumber", "")
                key = (sno, str(name).lower())
                if not PVLAN_PO_NAME.match(str(name)) or key in self.pvlan_targets:
                    continue
                self.dcnm_intf_bulk_fetch_intf_info(sno)
                if self.dcnm_intf_detail_unavailable(name, sno):
                    if self.dcnm_intf_pvlan_po_summary_policy(name, sno) in (PO_HOST_POLICY, None):
                        self.dcnm_intf_pvlan_block(name, sno, "its current state could not be read authoritatively")
                    continue
                detail = self.dcnm_intf_get_intf_info(name, sno, "INTERFACE_PORT_CHANNEL")
                if not isinstance(detail, dict) or detail.get("policy") != PO_HOST_POLICY:
                    continue  # not a PVLAN port-channel: the generic deletion is unchanged
                po_nv = copy.deepcopy((detail.get("interfaces") or [{}])[0].get("nvPairs") or {})
                problems = []
                owner = self.dcnm_intf_pvlan_check_ownership(name, sno, PO_HOST_POLICY, po_nv, "INTERFACE_PORT_CHANNEL")
                if owner:
                    problems.append(owner)
                if self.module.check_mode:
                    problems.append("deleting a PVLAN port-channel is refused in check mode: the pre-deploy gate needs the "
                                    "deletion to exist, so its validation could not be shown without writing")
                # A deletion requested with deploy false is SAVED (mark-delete, member release corrected and the pending
                # validated by the pre-deploy gate, no deployment); its continuation is recognised later from the controller's own
                # "marked for deletion" listing (dcnm_intf_pvlan_po_register_resumes). Requested to deploy but not queued for it keeps
                # the refusal: the generic path would leave the release unvalidated.
                deferred = self.delete_requested_deploy.get(key) is False
                if key not in deploys and not deferred:
                    problems.append("deleting a PVLAN port-channel without deploy is not implemented: the release of its "
                                    "member could not be validated")
                if self.dcnm_intf_pvlan_release_admin_problem():
                    problems.append(self.dcnm_intf_pvlan_release_admin_problem())
                if not self.module.check_mode and not self.has_bulk_api:
                    problems.append("the controller's bulk interface update API is not available: the released member's "
                                    "administrative state could not be corrected before the deploy")
                names, unresolved = pvlan_normalize_member_list(po_nv.get("MEMBER_INTERFACES"))
                members = []
                if unresolved or not names:
                    problems.append("the port-channel needs a readable, non-empty list of explicit physical members")
                for token in sorted(names) if not unresolved else []:
                    tokens = [self.dcnm_intf_pvlan_po_member_ifname(token, sno)]
                    m_problems, m_policy, m_nv = self.dcnm_intf_pvlan_po_member_context(tokens[0], sno)
                    problems += m_problems
                    if not m_problems:
                        if m_policy != PO_MEMBER_POLICY or str((m_nv or {}).get("PO_ID", "")).lower() != str(name).lower():
                            problems.append("member {0} is not the member of this port-channel in the controller's "
                                            "intent ({1})".format(tokens[0], m_policy))
                        elif str((m_nv or {}).get("ADMIN_STATE", "")).strip().lower() not in ("true", "false"):
                            problems.append("member {0} has an unknown administrative state ({1!r})".format(
                                tokens[0], (m_nv or {}).get("ADMIN_STATE")))
                        else:
                            claims = self.dcnm_intf_pvlan_po_member_claims(tokens[0], sno, name)
                            if claims:
                                problems.append(claims)
                            else:
                                members.append({"name": tokens[0], "pre": (PO_MEMBER_POLICY, copy.deepcopy(m_nv)),
                                                "post": (PVLAN_TRUNK_HOST_POLICY, self.dcnm_intf_pvlan_released_model())})
                if problems:
                    for reason in problems:
                        self.dcnm_intf_pvlan_block(name, sno, reason)
                    continue
                self.pvlan_targets[key] = {
                    "name": name, "sno": sno, "kind": "po", "deletes": True, "creates": False, "update": False, "deferred": deferred,
                    "pre": (PO_HOST_POLICY, po_nv), "post": (None, None), "new_secondaries": [], "members": members,
                    # The controller's own spelling of the port-channel (detail ifName), used on the mark-delete wire.
                    "wire_name": self.dcnm_intf_pvlan_detail_ifname(detail, name),
                    # The identities frozen before the first write; the release step proves the same member/serial.
                    "frozen": {"parent": name, "serial": sno, "member": members[0]["name"],
                               "member_policy_id": members[0]["pre"][1].get("POLICY_ID")},
                }
                # Never the generic deferred default (a sparse seven-key payload, deployed separately): the release step corrects the
                # released member itself, with its complete nvPairs, before the parent's deletion is deployed.
                self.dcnm_intf_pvlan_drop_generic_member_resets(set((sno, m["name"].lower()) for m in members))

    def dcnm_intf_pvlan_planning_preview(self, query_serial):
        """PLANNING-REUSE: ONE fresh forced preview per queried serial for the PLANNING reads of THIS invocation (the saved-state
        recognition and the saved-removal detection, all before the first write). Several candidates on the same switch then judge the
        same answer instead of recomputing that switch each time. Keyed by the serial in the request path, so peers never share an
        answer. Only an answer that parses as a preview entry of that serial is kept: an unreadable answer is returned to its caller (which
        judges and reports it as before) and not cached, so a failed read is never reused as an empty state. Once the invocation starts
        sending (dcnm_intf_send_message_to_dcnm) nothing is reused: the gates keep their own fresh reads after any write."""
        cache = None if getattr(self, "_pvlan_sending", False) else self.__dict__.setdefault("pvlan_planning_previews", {})
        if cache is not None and query_serial in cache:
            return cache[query_serial]
        resp = dcnm_send(self.module, "GET", self.paths["PVLAN_CONFIG_PREVIEW"].format(self.fabric, query_serial))
        if cache is not None:
            try:
                pvlan_preview_entry(resp, query_serial)
            except PvlanError:
                return resp
            cache[query_serial] = resp
        return resp

    def dcnm_intf_pvlan_po_register_resumes(self):
        """The continuation of a SAVED PVLAN port-channel deletion (deploy false earlier, in another process). Recognised ONLY
        from the controller's state: the request reaches a summary entry in the measured "marked for deletion" form of a regular Po
        (po_marked_deleted_problem: markDeleted, one interface_delete policy of the Po itself) and the device's running configuration, read
        through a fresh forced preview, still holds that Po in a PVLAN mode with its members joined (`channel-group N`). Each member must
        hold its released policy (the saved release); the release step proves and, if needed, corrects it again and the pre-deploy gate
        judges the pending exactly as for an immediate deletion. deploy false again: nothing is written and the deletion is reported as
        still pending (never as done). No local plan is kept between processes."""
        for key, req in sorted(self.marked_delete_requests.items(), key=str):
            sno, lname = key
            entry = req.get("entry") or {}
            name = entry.get("ifName", "")
            if key in self.pvlan_targets or not PVLAN_PO_NAME.match(str(name)) or pvlan_po_marked_deleted_problem(entry, name):
                continue  # not a regular Po saved deletion (a vPC child carries its parent as source): not this path
            resp = self.dcnm_intf_pvlan_planning_preview(self._dcnm_intf_query_serial(sno))
            try:
                pv = pvlan_preview_entry(resp, sno)
            except PvlanError as exc:
                self.dcnm_intf_pvlan_block(name, sno, "the saved deletion cannot be classified: {0}".format(exc))
                continue
            running = pv.get("runningConfig") if isinstance(pv.get("runningConfig"), list) else None
            if running is None:
                self.dcnm_intf_pvlan_block(name, sno, "the saved deletion cannot be classified: the fresh preview carries no runningConfig")
                continue
            count, body = pvlan_interface_stanza(running, name)
            if count == 0:
                continue  # nothing of it on the device: not a saved PVLAN deletion this path can complete
            if count != 1 or not any(str(line).strip().startswith("switchport mode private-vlan ") for line in body):
                continue  # not a PVLAN port-channel on the device: the generic path is unchanged
            number = re.match(r"^port-channel([0-9]+)$", str(name).lower()).group(1)
            joined, pc_mode = pvlan_running_po_members(running, number)
            problems = []
            if self.module.check_mode:
                problems.append("completing a saved PVLAN port-channel deletion is refused in check mode: the pre-deploy gate needs a fresh "
                                "decision that could not be shown without deploying")
            if not joined:
                problems.append("the device holds the port-channel but no member joined to it; the saved deletion cannot be verified")
            if self.dcnm_intf_pvlan_release_admin_problem():
                problems.append(self.dcnm_intf_pvlan_release_admin_problem())
            if not self.module.check_mode and not self.has_bulk_api:
                problems.append("the controller's bulk interface update API is not available: the released member's administrative state "
                                "could not be corrected before the deploy")
            members = []
            for member in joined:
                member = self.dcnm_intf_pvlan_po_member_ifname(member, sno)
                m_problems, m_policy, m_nv = self.dcnm_intf_pvlan_po_member_context(member, sno)
                problems += m_problems
                if not m_problems and m_policy not in PVLAN_RELEASED_MEMBER_POLICIES:
                    problems.append("member {0} holds {1}, not a released member policy: the saved deletion is not "
                                    "coherent".format(member, m_policy))
                elif not m_problems:
                    members.append({"name": member, "pre": (PO_MEMBER_POLICY, {"CONF": ""}),
                                    "post": (m_policy, self.dcnm_intf_pvlan_released_model())})
            if problems:
                for reason in problems:
                    self.dcnm_intf_pvlan_block(name, sno, reason)
                continue
            record = {"port_channel": name, "serial": sno, "members": [m["name"] for m in members]}
            if not req.get("deploy"):
                self.result.setdefault("pvlan_saved", []).append(dict(
                    record, operation="delete", state="saved, awaiting deployment (nothing written by this run)"))
                continue
            self.pvlan_targets[key] = {
                "name": name, "sno": sno, "kind": "po", "deletes": True, "resumes_delete": True, "creates": False, "update": False,
                "pre": (PO_HOST_POLICY, {"PC_MODE": pc_mode}), "post": (None, None), "new_secondaries": [], "members": members,
                "wire_name": name, "frozen": {"parent": name, "serial": sno, "member": members[0]["name"], "member_policy_id": None},
            }
            delem = {"serialNumber": sno, "ifName": name, "fabricName": self.fabric}
            self.diff_delete_deploy[self.int_index["INTERFACE_PORT_CHANNEL"]].append(delem)
            self.changed_dict[0]["delete_deploy"].append(copy.deepcopy(delem))
            self.dcnm_intf_pvlan_drop_generic_member_resets(set((sno, m["name"].lower()) for m in members))
            self.result.setdefault("pvlan_saved", []).append(dict(record, operation="delete", state="completing the saved deletion"))

    def dcnm_intf_pvlan_validate_saved_deletions(self):
        """The deletions requested with deploy false, after their mark-delete and member release: the fresh pending is judged by
        the pre-deploy gate (a refusal fails the run and reports the intent already changed); nothing is deployed and the result names each
        saved deletion and how it continues. Running configuration is NOT claimed to have converged."""
        saved = [t for t in self.dcnm_intf_pvlan_target_map().values() if t.get("deletes") and t.get("deferred")]
        if not saved:
            return
        items = [{"serialNumber": t["sno"], "ifName": t["name"], "fabricName": self.fabric} for t in saved]
        self.dcnm_intf_pvlan_deploy_gate(items, "delete_saved", True)
        for t in saved:
            self.result.setdefault("pvlan_saved", []).append({
                "kind": t.get("kind"), "name": t["name"], "serial": t["sno"], "operation": "delete",
                "state": "saved: marked for deletion, members released to the fabric's host default, pending validated; NOT deployed",
                "continuation": "deploy the switches (fabric deploy), or repeat this deletion with deploy true naming the same aggregates: "
                                "the module completes and verifies a saved PVLAN deletion, and a saved conventional port-channel or vPC "
                                "deleted with it on the same switch, from the controller's state. Not completed by the module (use the "
                                "fabric deploy): a saved deletion left out of that request, a conventional one whose PVLAN sibling is "
                                "already deployed, or a conventional vPC whose child port-channel id differs from its vPC id (its children are now "
                                "found through the marked-for-deletion relation, which has only been exercised offline: use the fabric deploy)"})

    def dcnm_intf_pvlan_validate_saved_updates(self):
        """Membership removals requested with deploy false, after the parent's confirmed modify and the removed members' release:
        the fresh pending is judged by the pre-deploy gate (removed members included) and nothing is deployed."""
        saved = [t for t in self.dcnm_intf_pvlan_target_map().values() if t.get("deferred_update")]
        if not saved:
            return
        items = [{"serialNumber": t["sno"], "ifName": t["name"], "fabricName": self.fabric} for t in saved]
        self.dcnm_intf_pvlan_deploy_gate(items, "update_saved", True)
        for t in saved:
            removed = [m["name"] for m in t.get("removed") or []]
            removed = removed or ["{0} on peer {1}".format(r["member"], r["index"] + 1) for r in t.get("removed_legs") or []]
            self.result.setdefault("pvlan_saved", []).append({
                "kind": t.get("kind"), "name": t["name"], "serial": t["sno"], "operation": "remove member", "members": removed,
                "state": "saved: membership updated, removed members released to the fabric's host default, pending validated; NOT deployed",
                "continuation": "deploy the switches (fabric deploy), or repeat the request with deploy true"})

    def dcnm_intf_pvlan_po_saved_removals(self, sno, name, po_nv):
        """The members of a SAVED removal of this existing PVLAN port-channel, from ONE fresh forced preview of its switch (cached per
        serial for this run): ports the DEVICE still joins to it (`channel-group N`), with pending, that its intent no longer lists, holding a
        released member policy at the fabric's host default and no live policy of the port-channel. [] = none; None = the preview or the
        policy list could not be read (never "none"). The same rule dcnm_intf_pvlan_po_resume_removed applies in the gate."""
        number = re.match(r"^port-channel([0-9]+)$", str(name).lower())
        if not number:
            return []
        admin = self.dcnm_intf_pvlan_release_admin()
        if admin is None:
            return None
        # A switch the inventory read at the start of this run reports explicitly In-Sync holds no pending at all, so no saved removal: the
        # preview is read only otherwise (an absent or other ccStatus is never taken as In-Sync).
        if self.dcnm_intf_pvlan_switch_in_sync(sno):
            return []
        try:
            entry = pvlan_preview_entry(self.dcnm_intf_pvlan_planning_preview(sno), sno)
            blocks, _global = pvlan_split_blocks(entry["pendingConfig"])
        except PvlanError:
            return None
        running = entry.get("runningConfig") if isinstance(entry.get("runningConfig"), list) else None
        if running is None:
            return None
        listed = set(pvlan_normalize_member_list((po_nv or {}).get("MEMBER_INTERFACES"))[0])
        joined, _mode = pvlan_running_po_members(running, number.group(1))
        out = []
        for member in joined:
            if member.lower() not in blocks or pvlan_po_member_canonical(member) in listed:
                continue
            mname = self.dcnm_intf_pvlan_po_member_ifname(member, sno)
            m_problems, m_policy, m_nv = self.dcnm_intf_pvlan_po_member_context(mname, sno)
            if m_problems or m_policy not in PVLAN_RELEASED_MEMBER_POLICIES or not isinstance(m_nv, dict):
                continue
            if str(m_nv.get("ADMIN_STATE", "")).strip().lower() != admin:
                continue
            policies = self.dcnm_intf_pvlan_read_policies(sno)
            if policies is None:
                return None
            if any(name.lower() in (str(p.get("source", "")).lower(), str(p.get("entityName", "")).lower())
                   and str(p.get("entityName", "")).lower() == mname.lower()
                   and p.get("deleted") is not True and str(p.get("deleted", "")).lower() != "true" for p in policies):
                continue
            out.append(mname)
        return out

    def dcnm_intf_pvlan_po_resume_removed(self, sno, entry, blocks, allowed, items):
        """The continuation of a SAVED member removal (deploy false earlier) of a regular PVLAN port-channel this batch deploys.
        Recognised ONLY from the controller's state in THIS fresh preview: an interface with pending that the DEVICE still holds in the
        port-channel (`channel-group N`), that the port-channel's intent no longer lists, and whose own intent is a released member policy,
        administratively down, with no live policy of the port-channel. It is then judged exactly as a member the update removed (force
        withdrawal, released model) instead of being refused as outside the batch; anything else stays outside and refuses."""
        running = entry.get("runningConfig") if isinstance(entry.get("runningConfig"), list) else None
        if running is None:
            return
        for it in items:
            target = self.pvlan_targets.get((it["serialNumber"], str(it["ifName"]).lower()))
            if it["serialNumber"] != sno or not target or target.get("kind") != "po" or target.get("deletes"):
                continue
            number = re.match(r"^port-channel([0-9]+)$", str(target["name"]).lower())
            if not number:
                continue
            listed = set(pvlan_normalize_member_list(((target.get("post") or (None, {}))[1] or {}).get("MEMBER_INTERFACES"))[0])
            joined, _mode = pvlan_running_po_members(running, number.group(1))
            for member in joined:
                lname = member.lower()
                if lname in allowed or lname not in blocks or pvlan_po_member_canonical(member) in listed:
                    continue
                name = self.dcnm_intf_pvlan_po_member_ifname(member, sno)
                m_problems, m_policy, m_nv = self.dcnm_intf_pvlan_po_member_context(name, sno)
                if m_problems or m_policy not in PVLAN_RELEASED_MEMBER_POLICIES or not isinstance(m_nv, dict):
                    continue
                if str(m_nv.get("ADMIN_STATE", "")).strip().lower() != self.dcnm_intf_pvlan_release_admin():
                    continue
                policies = self.dcnm_intf_pvlan_read_policies(sno)
                if policies is None or any(
                        target["name"].lower() in (str(p.get("source", "")).lower(), str(p.get("entityName", "")).lower())
                        and str(p.get("entityName", "")).lower() == lname
                        and p.get("deleted") is not True and str(p.get("deleted", "")).lower() != "true" for p in policies):
                    continue  # unreadable, or still claimed by the port-channel: not a release
                target.setdefault("removed", []).append({
                    "name": name, "pre": (PO_MEMBER_POLICY, {"CONF": ""}), "post": (m_policy, copy.deepcopy(m_nv)),
                    "released": True, "resumed": True})
                allowed.add(lname)
                self.result.setdefault("pvlan_saved", []).append({
                    "kind": "po", "name": target["name"], "serial": sno, "operation": "remove member", "members": [name],
                    "state": "completing the saved removal"})

    def _dcnm_intf_vpc_marked_children(self, vpc_lname, serial=None):
        """Entries of the interface summary read so far (optionally one serial) that are a port-channel marked for deletion with the
        controller's `interface_delete` policy whose source is the vPC `vpc_lname`: the authoritative relation parent -> child, whatever
        port-channel number each peer uses."""
        return [h for h in self.have_all
                if (serial is None or h.get("serialNo") == serial)
                and re.match(r"^port-channel[0-9]+$", str(h.get("ifName", "")).lower())
                and not pvlan_po_marked_deleted_problem(h, h.get("ifName", ""), parent=vpc_lname)]

    def dcnm_intf_pvlan_vpc_register_resumes(self):
        """The continuation of a SAVED PVLAN vPC deletion. MEASURED: after the vPC's mark-delete the parent is no
        longer listed and each peer's child port-channel stays listed, marked for deletion, with ONE interface_delete policy whose source is
        the vPC (lower case) until the deploy. The continuation is recognised only from that state on BOTH peers of the controller's pair,
        plus each peer's running configuration (fresh forced preview) still holding the child in a PVLAN mode with its members joined, each
        member holding its released policy. One peer marked and the other not (a vPC applied on one peer only) is refused with that
        diagnosis; nothing is written. deploy false again: reported as still pending."""
        groups = {}
        for (sno, _lname), req in sorted(self.marked_delete_requests.items(), key=str):
            entry = req.get("entry") or {}
            state, value = pvlan_summary_policy(entry, entry.get("ifName", ""))
            source = str(value.get("source", "")).lower() if state == PVLAN_SUMMARY_KNOWN else ""
            if not VPC_NAME.match(source) or pvlan_po_marked_deleted_problem(entry, entry.get("ifName", ""), parent=source):
                continue
            group = groups.setdefault(source, {"deploy": req.get("deploy"), "name": None, "peers": {}})
            group["peers"][sno] = entry
        for (pair, lname), req in sorted((getattr(self, "vpc_named_resume_requests", None) or {}).items(), key=str):
            # The child of each peer is found by its RELATION to the vPC (the marked-for-deletion `interface_delete` policy whose source is the
            # vPC), never by a name derived from the vPC id: the port-channel number may differ from the vPC id (and between the peers).
            # Only a vPC with the marking already visible in what this run read (the pair's first serial) can be a saved PVLAN deletion;
            # any other absent vPC keeps the generic no-op, without further reads.
            if not self._dcnm_intf_vpc_marked_children(lname):
                continue
            group = groups.setdefault(lname, {"deploy": req.get("deploy"), "name": req.get("name"), "peers": {}})
            group["name"] = req.get("name")
            for part in self._dcnm_intf_serial_parts(pair) or ():
                # Each peer's OWN summary is read: the named deletion read only the pair's first serial, and a child listed only on the
                # other peer must never look absent.
                if not self.dcnm_intf_get_have_all_with_sno(part):
                    group["unreadable"] = part
                    continue
                found = self._dcnm_intf_vpc_marked_children(lname, part)
                if len(found) > 1:
                    group["ambiguous"] = (part, sorted(str(h.get("ifName", "")) for h in found))
                elif found:
                    group["peers"][part] = found[0]
        for source, group in sorted(groups.items()):
            vid = vpc_id(source)
            if not group["peers"] or not vid:
                continue
            if group.get("unreadable"):
                self.dcnm_intf_pvlan_block(group["name"] or source, group["unreadable"], "the saved vPC deletion cannot be classified: the "
                                           "interface summary of {0} could not be read authoritatively".format(group["unreadable"]))
                continue
            if group.get("ambiguous"):
                self.dcnm_intf_pvlan_block(group["name"] or source, group["ambiguous"][0], "the saved vPC deletion cannot be classified: peer {0} lists "
                                           "{1} marked for deletion with the vPC as source".format(group["ambiguous"][0], ", ".join(group["ambiguous"][1])))
                continue
            some = sorted(group["peers"])[0]
            ips = [ip for ip, sn in self.ip_sn.items() if str(sn).casefold() == some.casefold()]
            pair = self.vpc_ip_sn.get(ips[0]) if len(ips) == 1 else None
            if pair is None and len(ips) == 1:
                pair = self.dcnm_intf_get_vpc_serial_number(ips[0]) or None
            name = group["name"] or "vPC" + vid
            parts = self._dcnm_intf_serial_parts(pair or "") or ()
            key = (pair, name.lower())
            if key in self.pvlan_targets:
                continue
            if len(parts) != 2:
                self.dcnm_intf_pvlan_block(name, some, "the saved vPC deletion cannot be completed: the controller returns no vPC pair for {0}".format(some))
                continue
            missing = [p for p in parts if p not in group["peers"]]
            if missing:
                self.dcnm_intf_pvlan_block(name, pair, "the saved deletion is marked on peer(s) {0} only; peer(s) {1} list no marked child of {2}: "
                                           "a vPC applied on one peer only is not completed automatically".format(
                                               ", ".join(sorted(group["peers"])), ", ".join(missing), name))
                continue
            for part in parts:
                ips = [ip for ip, sn in self.ip_sn.items() if str(sn).casefold() == part.casefold()]
                if len(ips) == 1:
                    self.vpc_ip_sn[ips[0]] = pair
            problems, legs = [], []
            if self.module.check_mode:
                problems.append("completing a saved PVLAN vPC deletion is refused in check mode")
            if self.dcnm_intf_pvlan_release_admin_problem():
                problems.append(self.dcnm_intf_pvlan_release_admin_problem())
            if not self.module.check_mode and not self.has_bulk_api:
                problems.append("the controller's bulk interface update API is not available")
            conventional = {}
            pcids = {}
            for index, part in enumerate(parts):
                # This peer's own child (the relation found above), so the two peers may use different port-channel numbers.
                pcid = re.match(r"^port-channel([0-9]+)$", str(group["peers"][part].get("ifName", "")).lower()).group(1)
                pcids[part] = pcid
                po_name = pvlan_vpc_po_name(pcid)
                resp = self.dcnm_intf_pvlan_planning_preview(part)
                try:
                    pv = pvlan_preview_entry(resp, part)
                except PvlanError as exc:
                    problems.append("peer {0} ({1}): {2}".format(index + 1, part, exc))
                    continue
                running = pv.get("runningConfig") if isinstance(pv.get("runningConfig"), list) else None
                count, body = pvlan_interface_stanza(running or [], po_name)
                if running is not None and count == 1 and not any(str(x).strip().startswith("switchport mode private-vlan ") for x in body):
                    conventional[part] = pv  # The device holds a CONVENTIONAL child here (classified after both peers)
                    continue
                if running is None or count != 1 or not any(str(x).startswith("switchport mode private-vlan ") for x in body):
                    problems.append("peer {0} ({1}): the device does not hold {2} in a PVLAN mode, so the saved deletion cannot be "
                                    "verified".format(index + 1, part, po_name))
                    continue
                joined, pc_mode = pvlan_running_po_members(running, pcid)
                if not joined:
                    problems.append("peer {0} ({1}): no member joined to {2} on the device".format(index + 1, part, po_name))
                for member in joined:
                    member = self.dcnm_intf_pvlan_po_member_ifname(member, part)
                    m_problems, m_policy, m_nv = self.dcnm_intf_pvlan_po_member_context(member, part)
                    problems += ["peer {0} ({1}): {2}".format(index + 1, part, x) for x in m_problems]
                    if not m_problems and m_policy not in PVLAN_RELEASED_MEMBER_POLICIES:
                        problems.append("peer {0} ({1}): member {2} holds {3}, not a released member policy".format(index + 1, part, member, m_policy))
                    elif not m_problems:
                        legs.append({"serial": part, "index": index, "member": member, "po_name": po_name, "pcid": pcid,
                                     "pc_mode": pc_mode or "active", "pre_member": (PO_MEMBER_POLICY, {"CONF": ""}),
                                     "post_member": (m_policy, self.dcnm_intf_pvlan_released_model())})
            if len(conventional) == 2:
                # Not a PVLAN saved deletion -- BOTH peers hold a conventional child, so the PVLAN-only checks above do
                # not apply. Kept (with the fresh previews) for dcnm_intf_pvlan_register_conventional_resumes; otherwise the generic path.
                pvlan_lifecycle_note(self, "pvlan_conventional_vpc_saved", key, {
                    "name": name, "parts": list(parts), "pcids": dict(pcids), "deploy": group["deploy"], "previews": conventional})
                continue
            if conventional:
                problems.append("the device holds {0} as a conventional port-channel on peer(s) {1} only: the peers are not the same saved "
                                "deletion".format(po_name, ", ".join(sorted(conventional))))
            if problems or set(leg["index"] for leg in legs) != {0, 1}:
                for reason in problems or ["the saved deletion cannot be verified on both peers"]:
                    self.dcnm_intf_pvlan_block(name, pair, reason)
                continue
            record = {"vpc": name, "serial": pair, "members": ["{0} on {1}".format(l["member"], l["serial"]) for l in legs]}
            if not group["deploy"]:
                self.result.setdefault("pvlan_saved", []).append(dict(
                    record, operation="delete", state="saved, awaiting deployment (nothing written by this run)"))
                continue
            self.pvlan_targets[key] = {
                "name": name, "sno": pair, "kind": "vpc", "deletes": True, "resumes_delete": True, "creates": False, "update": False,
                "pre": (VPC_HOST_POLICY, {}), "post": (None, None), "new_secondaries": [], "members": [], "legs": legs,
                "wire_name": name, "frozen": {"parent": name, "serial": pair, "legs": [(l["serial"], l["member"]) for l in legs]},
            }
            delem = {"serialNumber": pair, "ifName": name, "fabricName": self.fabric}
            self.diff_delete_deploy[self.int_index["INTERFACE_VPC"]].append(delem)
            self.changed_dict[0]["delete_deploy"].append(copy.deepcopy(delem))
            self.dcnm_intf_pvlan_drop_generic_member_resets(set((l["serial"], l["member"].lower()) for l in legs))
            self.result.setdefault("pvlan_saved", []).append(dict(record, operation="delete", state="completing the saved deletion"))

    def dcnm_intf_pvlan_register_conventional_resumes(self):
        """A saved CONVENTIONAL port-channel / vPC deletion that THIS request names again with deployment, on a physical
        serial where this request also completes a saved PVLAN deletion (registered by the PVLAN resume paths). Without it, that PVLAN
        deploy is refused: the conventional sibling's `no interface port-channel<id>` and released members are pending on the same switch.

        Recognised only from the controller's current state, never from an earlier process: the summary lists the aggregate in the
        measured "marked for deletion" form (a regular Po: markDeleted, one `interface_delete` policy whose source is the Po; a vPC: that
        form for the child on BOTH peers with the vPC as source), and each physical serial's fresh forced preview still holds the
        port-channel exactly once, NOT in a PVLAN mode, with every member joined to it holding its released policy. Then this invocation
        owns exactly that `no interface port-channel<id>` and those members (judged by the gates as for a confirmed mark-delete), and the
        aggregate joins the deployment; anything unproven is refused before any write. Deploy false, no PVLAN continuation on the serial,
        or a name this request does not repeat: unchanged (generic path; the gate keeps refusing unowned pending)."""
        resumed = set()
        for t in self.dcnm_intf_pvlan_target_map().values():
            if t.get("resumes_delete"):
                resumed.update([t["sno"]] if t.get("kind") == "po" else [leg["serial"] for leg in t.get("legs") or []])
        if not resumed:
            return
        candidates = []
        for (sno, lname), req in sorted(self.marked_delete_requests.items(), key=str):
            entry = req.get("entry") or {}
            name = str(entry.get("ifName", ""))
            if (sno, lname) in self.pvlan_targets or not PVLAN_PO_NAME.match(name) or pvlan_po_marked_deleted_problem(entry, name):
                continue
            candidates.append({"name": name, "sno": sno, "deploy": req.get("deploy"), "itype": "INTERFACE_PORT_CHANNEL", "previews": {},
                               "legs": [(sno, re.match(r"^port-channel([0-9]+)$", name.lower()).group(1))]})
        for (pair, lname), saved in sorted((getattr(self, "pvlan_conventional_vpc_saved", None) or {}).items(), key=str):
            candidates.append({"name": saved["name"], "sno": pair, "deploy": saved["deploy"], "itype": "INTERFACE_VPC",
                               "previews": saved["previews"], "legs": [(part, saved["pcids"][part]) for part in saved["parts"]]})
        for cand in candidates:
            if not cand["deploy"] or not set(serial for serial, _pcid in cand["legs"]) & resumed:
                continue
            problems, owned = [], []
            for serial, pcid in cand["legs"]:
                po_name = "port-channel" + pcid
                pv = cand["previews"].get(serial)
                if pv is None:
                    resp = self.dcnm_intf_pvlan_planning_preview(self._dcnm_intf_query_serial(serial))
                    try:
                        pv = pvlan_preview_entry(resp, serial)
                    except PvlanError as exc:
                        problems.append("{0}: {1}".format(serial, exc))
                        continue
                running = pv.get("runningConfig") if isinstance(pv.get("runningConfig"), list) else None
                count, body = pvlan_interface_stanza(running or [], po_name)
                if running is None or count != 1:
                    problems.append("{0}: the device does not hold {1} exactly once, so the saved deletion cannot be verified".format(serial, po_name))
                    continue
                if any(str(x).strip().startswith("switchport mode private-vlan ") for x in body):
                    problems.append("{0}: the device holds {1} in a PVLAN mode, not as a conventional port-channel".format(serial, po_name))
                    continue
                members = []
                for member in pvlan_running_po_members(running, pcid)[0]:
                    member = self.dcnm_intf_pvlan_po_member_ifname(member, serial)
                    m_problems, m_policy, _m_nv = self.dcnm_intf_pvlan_po_member_context(member, serial)
                    problems += ["{0}: member {1}: {2}".format(serial, member, x) for x in m_problems]
                    if not m_problems and m_policy not in PVLAN_RELEASED_MEMBER_POLICIES:
                        problems.append("{0}: member {1} holds {2}, not a released member policy".format(serial, member, m_policy))
                    elif not m_problems:
                        members.append(member)
                owned.append((serial, pcid, members))
            if problems:
                for reason in problems:
                    self.dcnm_intf_pvlan_block(cand["name"], cand["sno"], "the saved conventional deletion cannot be completed with the PVLAN "
                                               "one: {0}".format(reason))
                continue
            withdrawn = getattr(self, "pvlan_invocation_withdrawn", None) or {}
            releases = getattr(self, "pvlan_invocation_releases", None) or {}
            for serial, pcid, members in owned:
                withdrawn.setdefault(serial, set()).add("no interface port-channel%s" % pcid)
                for member in members:
                    releases.setdefault(serial, {})[member.lower()] = pcid
            self.pvlan_invocation_withdrawn, self.pvlan_invocation_releases = withdrawn, releases
            delem = {"serialNumber": cand["sno"], "ifName": cand["name"], "fabricName": self.fabric}
            self.diff_delete_deploy[self.int_index[cand["itype"]]].append(delem)
            self.changed_dict[0]["delete_deploy"].append(copy.deepcopy(delem))
            pvlan_lifecycle_note(self, "pvlan_conventional_resumes", (cand["sno"], cand["name"].lower()), dict(cand, owned=owned))
            self.result.setdefault("pvlan_saved", []).append({
                "kind": "conventional", "name": cand["name"], "serial": cand["sno"], "operation": "delete",
                "members": ["{0} on {1}".format(m, serial) for serial, _pcid, ms in owned for m in ms],
                "state": "completing the saved deletion"})

    def dcnm_intf_pvlan_conventional_verify_deleted(self):
        """Bounded, non-mutating readback after the deploy of saved conventional deletions completed with a PVLAN one: on
        every physical serial the port-channel (and a vPC parent) is no longer listed and each released member is listed In-Sync. A read
        that fails is an observation, never a success; nothing is rewritten. A difference fails the run with the observed state."""
        attempts = 6
        for (sno, _lname), cand in sorted((getattr(self, "pvlan_conventional_resumes", None) or {}).items(), key=str):
            verified, observed = False, "no readback was attempted"
            for attempt in range(attempts):
                pending = []
                for serial, pcid, members in cand["owned"]:
                    self.dcnm_intf_invalidate_serial_authority(serial)
                    if not self.dcnm_intf_get_have_all_with_sno(serial):
                        pending.append("{0}: the interface summary could not be read authoritatively".format(serial))
                        continue
                    entries = [h for h in self.have_all if h.get("serialNo") in (serial, sno)]
                    gone = ("port-channel" + pcid, cand["name"].lower())
                    listed = sorted(set(h.get("ifName") for h in entries if str(h.get("ifName", "")).lower() in gone))
                    if listed:
                        pending.append("{0}: still listed {1}".format(serial, listed))
                    for member in members:
                        summ = [h for h in entries if h.get("serialNo") == serial and str(h.get("ifName", "")).lower() == member.lower()]
                        status = summ[0].get("complianceStatus") if len(summ) == 1 else None
                        if status != "In-Sync":
                            pending.append("{0}: member {1} is {2}".format(serial, member, status))
                if not pending:
                    verified = True
                    break
                observed = "; ".join(pending)
                if attempt < attempts - 1:
                    time.sleep(5)
            if not verified:
                self.module.fail_json(
                    msg="Saved conventional deletion of {0} on {1} was deployed but could not be verified after {2} readback attempts: "
                    "{3}. Nothing else was sent.".format(cand["name"], sno, attempts, observed), **self.result)

    def dcnm_intf_pvlan_learn_pair(self, pair):
        """The pair identity of a vPC deletion found by an `overridden` sweep. A named vPC teaches the module its pair while the
        playbook is translated (vpcpair_serial_number); a vPC that only the sweep found does not, and then every later summary re-read of a
        peer kept the pair's OLD entries (the post-deploy verification saw a deleted vPC as still listed). The pair is confirmed by the same
        controller lookup for each peer, never assumed from the summary alone. Returns the problems (empty when the pair is known)."""
        parts = self._dcnm_intf_serial_parts(pair) or ()
        if len(parts) != 2:
            return ["the vPC identity {0!r} is not a pair of serials".format(pair)]
        problems = []
        for part in parts:
            ips = [ip for ip, sn in self.ip_sn.items() if str(sn).casefold() == part.casefold()]
            if len(ips) != 1:
                problems.append("peer {0} of the vPC is not exactly one switch of the fabric inventory".format(part))
                continue
            known = self.vpc_ip_sn.get(ips[0])
            if known is None:
                known = self.dcnm_intf_get_vpc_serial_number(ips[0])
            if self._dcnm_intf_authority_key(known or "") is None or \
                    self._dcnm_intf_authority_key(known).casefold() != self._dcnm_intf_authority_key(pair).casefold():
                problems.append("the controller's vPC pair of {0} ({1!r}) is not {2}".format(part, known, pair))
                continue
            self.vpc_ip_sn[ips[0]] = known
        return problems

    def dcnm_intf_pvlan_release_admin(self):
        """The administrative state a released PVLAN member must reach -- the fabric's host-interface default
        HOST_INTF_ADMIN_STATE ("true" or "false"), exactly what the generic reset of a host interface applies
        (dcnm_intf_get_default_eth_payload). Unlike that generic reader, an unreadable or non-boolean setting is NOT defaulted: it returns
        None and every PVLAN release refuses before any write (dcnm_intf_pvlan_release_admin_problem). Read once per run."""
        cached = getattr(self, "pvlan_release_admin_cache", None)
        if cached is not None:
            return cached or None
        value = None
        try:
            details = get_fabric_details(self.module, self.fabric)
            raw = ((details or {}).get("nvPairs") or {}).get("HOST_INTF_ADMIN_STATE") if isinstance(details, dict) else None
            word = None if raw is None else str(raw).strip().lower()
            value = word if word in ("true", "false") else None
        except Exception:
            value = None
        self.pvlan_release_admin_cache = value or ""
        return value

    def dcnm_intf_pvlan_release_admin_problem(self):
        """None when the released administrative state is known; else the refusal every PVLAN release records before any write."""
        if self.dcnm_intf_pvlan_release_admin() is None:
            return ("the fabric's host interface default (HOST_INTF_ADMIN_STATE) could not be read as true or false: the administrative state "
                    "of the released member cannot be decided")
        return None

    @staticmethod
    def dcnm_intf_pvlan_admin_words(admin):
        """Wording of a released member already at the targeted state (unchanged text for the original admin-down contract)."""
        return "administratively down" if admin == "false" else "administratively up, the fabric's host default"

    def dcnm_intf_pvlan_released_model(self):
        """The predicted release (template model) with the fabric's host default; only valid once the release admin state is known."""
        return pvlan_released_member_model(self.dcnm_intf_pvlan_release_admin() or "false")

    def dcnm_intf_pvlan_drop_generic_member_resets(self, released):
        """The members a REGISTERED PVLAN deletion releases (and corrects) itself never also get the generic default reset: neither the
        `deleted` deferred list nor the reset/deploy the `overridden` sweep queues inline for a member whose source is
        a deleted port-channel/vPC. `released` = {(serial, ifName lower)}. Any other entry is left untouched."""
        def kept(item):
            return (item.get("serialNumber"), str(item.get("ifName", "")).lower()) not in released

        self.deferred_delete_member_defaults = [d for d in (self.deferred_delete_member_defaults or []) if kept(d)]
        replace = []
        for payload in self.diff_replace or []:
            intfs = [i for i in payload.get("interfaces", []) if kept(i)]
            if intfs:
                payload["interfaces"] = intfs
                replace.append(payload)
        self.diff_replace = replace
        self.diff_deploy = [d for d in (self.diff_deploy or []) if kept(d)]
        changed = self.changed_dict[0]
        changed["replaced"] = [p for p in changed.get("replaced", []) if all(kept(i) for i in p.get("interfaces", [p]))]
        changed["deploy"] = [d for d in changed.get("deploy", []) if kept(d)]

    def dcnm_intf_pvlan_po_member_claims(self, member, sno, po_name):
        """Reason the member's live policies are not exactly the PVLAN port-channel's (measured shape: one
        int_port_channel_pvlan_member and, optionally, the 'Inherited Commands' int_eth, both with the port-channel as
        source), or None. Read before the first write."""
        policies = self.dcnm_intf_pvlan_read_policies(sno)
        if policies is None:
            return "the switch policy list could not be read authoritatively"
        live = [p for p in policies if str(p.get("entityName", "")).lower() == member.lower()
                and p.get("deleted") is not True and str(p.get("deleted", "")).lower() != "true"]
        kinds = sorted("{0}/{1}".format(p.get("templateName"), p.get("source")) for p in live)
        owned = [p for p in live if p.get("templateName") == PO_MEMBER_POLICY and str(p.get("source", "")).lower() == po_name.lower()]
        others = [p for p in live if p not in owned and not (
            p.get("templateName") == "int_eth" and str(p.get("source", "")).lower() == po_name.lower())]
        if len(owned) != 1 or others:
            return "member {0} live policies are not exactly those of {1}: {2}".format(member, po_name, kinds)
        return None

    def dcnm_intf_pvlan_po_release_fail(self, target, phase, problems, confirmed, uncertain=None, admin_state=None):
        """Stop the run after a release problem: no deploy was sent. Names the writes CONFIRMED by their measured
        outcome and those whose outcome is UNVERIFIED (they may or may not have been applied), and what remains."""
        uncertain = uncertain or []
        self.result.setdefault("pvlan_po_release", []).append(
            {"port_channel": target["name"], "serial": target["sno"], "phase": phase, "problems": problems,
             "confirmed_writes": confirmed, "uncertain_writes": uncertain})
        self.module.fail_json(
            msg="PVLAN port-channel {0} on {1}: member release failed {2}: {3}. Confirmed writes: {4}. Writes with an "
            "UNVERIFIED outcome: {5}. No deployment request was sent: the controller keeps the port-channel's pending "
            "{6}{7}. Nothing is retried or rolled back; recovery is the scoped manual procedure.".format(
                target["name"], target["sno"], phase, "; ".join(problems), ", ".join(confirmed) or "none",
                ", ".join(uncertain) or "none",
                "membership update (the member removed from the port-channel is not deployed)" if target.get("release_context") == "update"
                else "deletion",
                "" if admin_state is None else " and the released member with ADMIN_STATE {0!r}".format(admin_state)),
            **self.result)

    def dcnm_intf_pvlan_po_markdeletes(self):
        """The mark-delete of every REGISTERED PVLAN port-channel deletion, taken out of the generic delete batch.

        One request per port-channel, so one target's outcome can never hide behind another's, and ONE attempt: the
        generic delete path retries an unsuccessful answer up to 20 times and its parser can turn an HTTP 500 into a
        synthetic 200/OK (changed=False), which skipped the member release while the deploy still ran (review
        PO_G4_R1). Here only the MEASURED success answer (po_markdelete_outcome_problems) confirms the deletion; any
        other answer, or a transport exception, is an UNVERIFIED outcome and stops the run at once: no retry, no member
        modify, no deploy. Returns True when at least one deletion was confirmed (the release step must follow)."""
        # Po targets ONLY. A vPC deletion has its own mark-delete and release steps (dcnm_intf_pvlan_vpc_markdeletes/_release_members).
        targets = dict(((t["sno"], t["name"].lower()), t) for t in self.dcnm_intf_pvlan_target_map().values()
                       if t.get("deletes") and t.get("kind") == "po" and not t.get("resumes_delete"))
        if not targets:
            # A resumed (saved) deletion was marked by an earlier process; its release is proven again below.
            return any(t.get("resumes_delete") and t.get("kind") == "po" for t in self.dcnm_intf_pvlan_target_map().values())
        found = {}
        for index, group in enumerate(self.diff_delete):
            keep = []
            for delem in group or []:
                key = (delem.get("serialNumber"), str(delem.get("ifName", "")).lower())
                if key in targets:
                    found.setdefault(key, delem)
                else:
                    keep.append(delem)
            self.diff_delete[index] = keep
        missing = sorted("{0} on {1}".format(n, s) for (s, n) in targets if (s, n) not in found)
        if missing:
            self.module.fail_json(msg="Native PVLAN deletion is inconsistent: registered port-channel(s) {0} are not in "
                                  "the delete batch. No request was sent.".format(", ".join(missing)), **self.result)
        for key, target in targets.items():
            # Measured: the mark-delete names the port-channel in the CONTROLLER's own spelling (a Manage-created Po
            # is `port-channel504`, accepted and echoed as such); the generic element carries the playbook's normalized name.
            body = dict(found[key], ifName=target.get("wire_name") or found[key].get("ifName"))
            try:
                resp = dcnm_send(self.module, "DELETE", self.paths["IF_MARK_DELETE"], json.dumps([body]))
                problems = pvlan_po_markdelete_outcome_problems(resp, target["sno"], target["name"])
            except AnsibleConnectionError as exc:
                resp = {"transport_error": str(exc)}
                problems = ["the mark-delete request raised a transport error: {0}".format(exc)]
            self.result["response"].append(resp)
            if problems:
                self.dcnm_intf_pvlan_po_release_fail(
                    target, "at the mark-delete (outcome UNVERIFIED; not retried)", problems, [],
                    uncertain=["mark-delete of {0} (it may or may not have been applied; the member may already be "
                               "released by the controller)".format(target["name"])])
            target["markdelete"] = "confirmed"
        return True

    def dcnm_intf_pvlan_po_released_member(self, target, normalized=False):
        """(problems, policy, nvPairs) of the released member from FRESH reads (cached authority dropped first): the
        port-channel is absent -- or, MEASURED for a DEPLOYED port-channel, listed
        ONLY in the controller's "marked for deletion" form awaiting the deploy (po_marked_deleted_problem) -- no live policy
        names it (entity or source), and the frozen member is a standalone physical Ethernet with exactly one live direct
        released-member policy -- int_trunk_host or int_routed_host (summary, detail and policy list agree)."""
        sno, name, member = target["sno"], target["name"], target["frozen"]["member"]
        self.dcnm_intf_invalidate_serial_authority(sno)
        self.pvlan_policies.pop(sno, None)
        if not self.dcnm_intf_get_have_all_with_sno(sno):
            return ["the interface summary could not be read authoritatively"], None, None
        authority = self._dcnm_intf_authority_key(sno)
        listed = [h for h in self.have_all if str(h.get("ifName", "")).lower() == name.lower()
                  and self._dcnm_intf_authority_key(h.get("serialNo", "")) == authority]
        if len(listed) > 1:
            return ["the port-channel is still listed {0} times".format(len(listed))], None, None
        if listed:
            marked = pvlan_po_marked_deleted_problem(listed[0], name)
            if marked:
                return ["the port-channel is still listed: {0}".format(marked)], None, None
        policies = self.dcnm_intf_pvlan_read_policies(sno)
        if policies is None:
            return ["the switch policy list could not be read authoritatively"], None, None
        claims = sorted("{0}/{1}/{2}".format(p.get("entityName"), p.get("templateName"), p.get("source")) for p in policies
                        if p.get("deleted") is not True and str(p.get("deleted", "")).lower() != "true"
                        and name.lower() in (str(p.get("entityName", "")).lower(), str(p.get("source", "")).lower()))
        if claims:
            return ["live policies still reference the port-channel: {0}".format(claims)], None, None
        return self.dcnm_intf_pvlan_released_member_detail(member, sno, normalized)

    def dcnm_intf_pvlan_released_member_detail(self, member, sno, normalized=False):
        """Shared by the Po and vPC release: (problems, policy, nvPairs) of a released member from a FRESH detail read. The template must
        be a released-member policy (int_trunk_host or int_routed_host, MEASURED), read from the controller -- never inferred from the
        switch role and never converted. Ownership: the member is a sole direct owner of that template; for int_routed_host the member's OWN
        children (source == the member) are set aside by phase: before ADMIN_STATE is normalized and while it reads "true", the measured
        up set (routed_interface, interface_mtu, no_shut_interface); otherwise -- an already-down release, or the readback after the modify
        (`normalized`) -- only the down set, so a surviving no_shut_interface refuses. int_trunk_host keeps its contract (no child set aside)."""
        self.dcnm_intf_bulk_fetch_intf_info(sno, refresh=True)
        if self.dcnm_intf_detail_unavailable(member, sno):
            return ["the member's detail could not be read authoritatively"], None, None
        detail = self.dcnm_intf_get_intf_info(member, sno, "INTERFACE_ETHERNET")
        if not isinstance(detail, dict):
            return ["the member is no longer a known physical interface"], None, None
        nv = (detail.get("interfaces") or [{}])[0].get("nvPairs")
        policy = detail.get("policy")
        if policy not in PVLAN_RELEASED_MEMBER_POLICIES or not isinstance(nv, dict):
            return ["the released member holds {0!r}, not a readable {1}".format(
                policy, " or ".join(PVLAN_RELEASED_MEMBER_POLICIES))], None, None
        children = frozenset()
        if policy == PVLAN_PO_ROUTED_BASELINE_POLICY:
            up = str(nv.get("ADMIN_STATE", "")).strip().lower() == "true" and (
                not normalized or self.dcnm_intf_pvlan_release_admin() == "true")
            children = PVLAN_PO_ROUTED_RELEASE_CHILDREN_UP if up else PVLAN_PO_ROUTED_RELEASE_CHILDREN_DOWN
        owner = self.dcnm_intf_pvlan_check_ownership(member, sno, policy, nv, self_children=children)
        if owner:
            return ["the released member is not a sole direct {0}: {1}".format(policy, owner)], None, None
        return [], policy, copy.deepcopy(nv)

    def dcnm_intf_pvlan_released_role_expectation(self, sno, policy):
        """Diagnostic only: the release the module's default-by-role rule predicts for this switch and whether the fresh read matches it."""
        role = (getattr(self, "sno_to_switch_role", None) or {}).get(sno)
        expected = pvlan_released_member_role_expectation(role)
        return {"switch_role": role, "role_expectation": expected, "matches_role_expectation": None if expected is None else expected == policy}

    def dcnm_intf_pvlan_po_release_members(self):
        """Run after the accepted mark-delete and BEFORE any deploy. MEASURED (NDFC
        12.6.0.267): the controller releases the member as a new int_trunk_host with ADMIN_STATE "true". For each deleted
        PVLAN port-channel: prove the release afresh (dcnm_intf_pvlan_po_released_member); when ADMIN_STATE is not
        already "false", send ONE legacy interface/modify carrying the member's complete writable nvPairs with only
        ADMIN_STATE "false" (po_released_member_payload); require a SUCCESS item naming the member and no ERROR; read
        back afresh (same ownership proof) and require every writable value unchanged and ADMIN_STATE "false". Any
        problem stops the run before the deploy. The legacy modify of a released int_trunk_host is NOT live-measured
        (the measured fix was a GUI save).
        The released template is the one READ (int_trunk_host or int_routed_host); policy and nvPairs travel together into the
        payload (same policy, ADMIN_STATE only), the safety check, the readback (same template, own down children only) and the release
        model. Every member of every target is proven and validated before the first member write."""
        targets = []
        for parent in self.dcnm_intf_pvlan_target_map().values():
            if not parent.get("deletes") or parent.get("kind") != "po":
                continue
            for member in parent["members"]:
                frozen = dict(parent["frozen"], member=member["name"], member_policy_id=member["pre"][1].get("POLICY_ID"))
                targets.append(dict(parent, frozen=frozen, members=[member]))
        self.dcnm_intf_pvlan_po_normalize_releases(
            targets, self.dcnm_intf_pvlan_po_released_member, "mark-delete of {0} (confirmed by its measured outcome)")

    def dcnm_intf_pvlan_po_release_removed(self):
        """MM-B: after the CONFIRMED modify of an existing PVLAN port-channel that removed members, and BEFORE any deploy, each removed
        member is released through the same contract as a deleted port-channel's member (dcnm_intf_pvlan_po_normalize_releases): proven
        afresh (the port-channel no longer lists or claims it, and it holds a sole direct int_trunk_host or int_routed_host), set
        administratively down on its own policy when needed, read back, modeled. INFERRED: that the controller releases a member removed
        by a modify the way it releases a deleted port-channel's member (MEASURED only for the deletion)."""
        targets = []
        for parent in self.dcnm_intf_pvlan_target_map().values():
            if parent.get("kind") != "po" or not parent.get("removed"):
                continue
            for member in parent["removed"]:
                frozen = {"parent": parent["name"], "serial": parent["sno"], "member": member["name"],
                          "member_policy_id": member["pre"][1].get("POLICY_ID")}
                targets.append(dict(parent, frozen=frozen, members=[member], release_context="update"))
        if targets:
            self.dcnm_intf_pvlan_po_normalize_releases(
                targets, self.dcnm_intf_pvlan_po_removed_member, "membership update of {0} (per-item SUCCESS)")

    def dcnm_intf_pvlan_po_removed_member(self, target, normalized=False):
        """MM-B: (problems, policy, nvPairs) of a member REMOVED from an existing port-channel, from FRESH reads: the port-channel's fresh
        intent no longer lists it, no live policy of the member is the port-channel's (its int_port_channel_pvlan_member or a child whose
        source is the port-channel), and it is a released member (dcnm_intf_pvlan_released_member_detail)."""
        sno, name, member = target["sno"], target["name"], target["frozen"]["member"]
        self.dcnm_intf_invalidate_serial_authority(sno)
        self.pvlan_policies.pop(sno, None)
        if not self.dcnm_intf_get_have_all_with_sno(sno):
            return ["the interface summary could not be read authoritatively"], None, None
        policies = self.dcnm_intf_pvlan_read_policies(sno)
        if policies is None:
            return ["the switch policy list could not be read authoritatively"], None, None
        claims = sorted("{0}/{1}".format(p.get("templateName"), p.get("source")) for p in policies
                        if p.get("deleted") is not True and str(p.get("deleted", "")).lower() != "true"
                        and str(p.get("entityName", "")).lower() == member.lower()
                        and (p.get("templateName") == PO_MEMBER_POLICY or str(p.get("source", "")).lower() == name.lower()))
        if claims:
            return ["the removed member is still claimed by the port-channel: {0}".format(claims)], None, None
        self.dcnm_intf_bulk_fetch_intf_info(sno, refresh=True)
        if self.dcnm_intf_detail_unavailable(name, sno):
            return ["the port-channel's detail could not be read authoritatively"], None, None
        po = self.dcnm_intf_get_intf_info(name, sno, "INTERFACE_PORT_CHANNEL")
        po_nv = (po.get("interfaces") or [{}])[0].get("nvPairs") if isinstance(po, dict) else None
        if not isinstance(po_nv, dict):
            return ["the port-channel's fresh intent is unreadable"], None, None
        if pvlan_po_member_canonical(member) in pvlan_normalize_member_list(po_nv.get("MEMBER_INTERFACES"))[0]:
            return ["the port-channel still lists the removed member"], None, None
        return self.dcnm_intf_pvlan_released_member_detail(member, sno, normalized)

    def dcnm_intf_pvlan_po_normalize_releases(self, targets, prove, first_write, fail=None, record_key="pvlan_po_release"):
        """The member-release sequence shared by a deletion (prove = released_member) and an update's removed members (prove = removed_member):
        every member is proven and validated before the FIRST member write, then each member still up gets ONE legacy modify on its own
        policy (ADMIN_STATE only), per-item outcome, readback and release model. `first_write` names the confirmed parent write. `fail` and
        `record_key` let the vPC removal reuse it with its own per-peer diagnostics (default: the port-channel ones)."""
        fail = fail or self.dcnm_intf_pvlan_po_release_fail
        # The released member reaches the fabric's host default (HOST_INTF_ADMIN_STATE), as the generic host reset does.
        admin = self.dcnm_intf_pvlan_release_admin()
        plan = []
        for target in targets:
            problems, policy, nv = prove(target)
            if not problems and admin is None:
                problems = [self.dcnm_intf_pvlan_release_admin_problem()]
            if not problems:
                if str(nv.get("ADMIN_STATE", "")).strip().lower() == admin:
                    fresh = dict((k, v) for k, v in nv.items() if k not in PVLAN_PO_RELEASE_METADATA)
                    problems = ["the released member (already {0}) is not a safe standalone port: {1}".format(
                        self.dcnm_intf_pvlan_admin_words(admin), x) for x in pvlan_released_member_safety_problems(policy, fresh, admin)]
                else:
                    proposed = pvlan_released_member_payload(policy, nv, target["frozen"]["member"], target["sno"], self.fabric, admin)
                    # Same diagnostic context and wording as the vPC path.
                    problems = ["the member payload would not be a safe standalone port: {0}".format(x)
                                for x in pvlan_released_member_safety_problems(policy, proposed["interfaces"][0]["nvPairs"], admin)]
            if problems:
                fail(target, "while proving the released member before any member write",
                     problems, [first_write.format(target["name"])])
            plan.append((target, policy, nv))
        completed_by_parent = {}
        for target, policy, nv in plan:
            sno, member = target["sno"], target["frozen"]["member"]
            completed = completed_by_parent.setdefault((sno, target["name"]), [first_write.format(target["name"])])
            record = {"port_channel": target["name"], "serial": sno, "member": member, "released_policy": policy,
                      "released_admin_state": nv.get("ADMIN_STATE"), "released_policy_id": nv.get("POLICY_ID")}
            record.update(self.dcnm_intf_pvlan_released_role_expectation(sno, policy))
            if str(nv.get("ADMIN_STATE", "")).strip().lower() == admin:
                record["member_modify"] = "not needed (already {0})".format(self.dcnm_intf_pvlan_admin_words(admin))
                self.dcnm_intf_pvlan_po_release_model(target, policy, nv, record, completed, fail)
                self.result.setdefault(record_key, []).append(record)
                continue
            payload = pvlan_released_member_payload(policy, nv, member, sno, self.fabric, admin)
            modify = "legacy interface/modify of {0} ADMIN_STATE {1}".format(member, admin)
            try:
                resp = dcnm_send(self.module, "POST", self.paths["UPDATE_INTERFACE_BULK"], json.dumps([payload]))
            except AnsibleConnectionError as exc:
                resp = {"transport_error": str(exc)}
            self.result["response"].append(resp)
            outcome = []
            if not isinstance(resp, dict) or resp.get("RETURN_CODE") not in (200, 207):
                outcome.append("the modify answered {0}".format(resp.get("RETURN_CODE", resp) if isinstance(resp, dict) else resp))
            else:
                outcome += ["ERROR item: {0}".format(i.get("message")) for i in self.dcnm_intf_collect_batch_errors(resp)]
                outcome += pvlan_modify_outcome_problems(resp, [(sno, member)])
            if outcome:
                fail(target, "at the member modify (outcome not verified)", outcome, completed,
                     uncertain=[modify], admin_state="unknown")
            completed.append(modify + " (per-item SUCCESS)")
            problems, after_policy, after = prove(target, normalized=True)
            if not problems:
                problems = pvlan_released_member_readback_problems(policy, nv, after_policy, after, admin)
            if problems:
                fail(target, "at the member readback", problems, completed,
                     admin_state=(after or {}).get("ADMIN_STATE", "unknown"))
            record.update(member_modify="ADMIN_STATE {0} -> {1}, {2} writable nvPairs preserved".format(
                nv.get("ADMIN_STATE"), admin, len(payload["interfaces"][0]["nvPairs"])), readback_policy_id=after.get("POLICY_ID"))
            self.dcnm_intf_pvlan_po_release_model(target, after_policy, after, record, completed, fail)
            self.result.setdefault(record_key, []).append(record)

    def dcnm_intf_pvlan_po_release_model(self, target, policy, fresh_nv, record, completed, fail=None):
        """MEASURED: the controller can release the member with MTU "default" taken from a port-channel intent,
        not the template's jumbo. The released member's FRESH writable nvPairs (the readback after the admin-down modify, or the release
        itself when no modify was needed) must be a safe standalone port (po_released_member_safety_problems: admin down, no VLAN, no
        freeform), otherwise the run stops before the deploy. When safe, they become the member's intended state for the pre-deploy
        gate (controller expected == their render; pending must take the device there) and for nothing else: no field is rewritten.
        Differences from the template release model are reported as `restoration_delta` (restoring the user's baseline is a separate
        operation)."""
        fail = fail or self.dcnm_intf_pvlan_po_release_fail
        released = dict((k, v) for k, v in (fresh_nv or {}).items() if k not in PVLAN_PO_RELEASE_METADATA)
        problems = pvlan_released_member_safety_problems(policy, released, self.dcnm_intf_pvlan_release_admin() or "false")
        if problems:
            fail(
                target, "the released member is not a safe standalone port", problems, completed,
                admin_state=released.get("ADMIN_STATE", "unknown"))
        members = [m for m in target["members"] if m["name"].lower() == str(target["frozen"]["member"]).lower()]
        if len(members) != 1:
            fail(target, "while modeling the released member", [
                "the deletion target holds {0} entries for member {1}".format(len(members), target["frozen"]["member"])], completed)
        members[0]["post"] = (policy, released)
        members[0]["released"] = True
        if target.get("release_context"):
            record["release_context"] = target["release_context"]
        record["release_model"] = "fresh controller release, {0} ({1} writable nvPairs)".format(policy, len(released))
        # the template release model is the int_trunk_host one; a routed release has no template model to restore to here
        record["restoration_delta"] = pvlan_po_released_member_restoration_delta(released) if policy == PVLAN_TRUNK_HOST_POLICY else {}

    def dcnm_intf_pvlan_po_delete_assess(self, blocks, entry, target):
        """Decision for a deleted PVLAN port-channel from ONE fresh preview entry: the controller's expected
        configuration holds no stanza for the port-channel, its pending block (if any) only withdraws, and every
        member is assessed as the transition to the released state: the FRESH safe release modeled by
        dcnm_intf_pvlan_po_release_model() (the registration's PO_RELEASED_MEMBER_NV is only the prediction used before the
        mark-delete)."""
        problems = []
        if not isinstance(entry.get("expectedConfig"), list):
            return "refuse", ["the fresh preview carries no expectedConfig, so the deletion cannot be validated"]
        count, _body = pvlan_interface_stanza(entry["expectedConfig"], target["name"])
        if count:
            problems.append("the controller's expected configuration still holds {0}".format(target["name"]))
        po_block = blocks.get(target["name"].lower(), [])
        kept = [line for line in po_block if not line.startswith("no ")]
        if kept:
            problems.append("the pending for the deleted port-channel carries non-withdrawal command(s): {0}".format(kept))
        decisions = []
        po_number = re.match(r"^port-channel([0-9]+)$", str(target["name"]).lower())
        pc_mode = str((target["pre"][1] or {}).get("PC_MODE", ""))
        for m in target["members"]:
            body = blocks.get(m["name"].lower(), [])
            if po_number:
                # Measured: a deployed member is withdrawn with the force command form.
                body, found = pvlan_po_member_force_withdrawal(body, po_number.group(1), pc_mode)
                if found:
                    decisions.append("refuse")
                    problems.extend("{0}: {1}".format(m["name"], f) for f in found)
                    continue
            decision, found = pvlan_assess_target(
                body, entry, m["name"], pvlan_render(*m["post"]),
                pvlan_transition_vocabulary(m["pre"], m["post"]), release=True)
            decisions.append(decision)
            problems.extend("{0}: {1}".format(m["name"], f) for f in found)
        if problems or "refuse" in decisions:
            return "refuse", problems
        # Never "converged": the mark-delete is completed by the deploy (state-withdrawal measurement), also for a
        # port-channel that was never deployed (recovery after a refused creation); without it the intent could stay.
        return "deploy", []

    def dcnm_intf_pvlan_po_verify_deleted(self):
        """Bounded, non-mutating readback after the deletion of PVLAN port-channels: the port-channel is gone from the
        interface summary, each member holds its modeled released policy (int_trunk_host, or int_routed_host as a sole direct owner with
        only its own down children), administratively down and In-Sync, and no live policy names the
        port-channel as its entity or source (no child claim). Nothing is rewritten
        to make it so; a difference fails the run with the observed state.

        The release starts UNVERIFIED and only a complete authoritative proof (summary, member detail and policy
        list, all in one attempt) marks it verified. A read that fails is an observation, never a success: when the
        attempts run out without that proof, the run fails with the last observed cause."""
        attempts = 6
        for target in [t for t in self.dcnm_intf_pvlan_target_map().values()
                       if t.get("deletes") and t.get("kind") == "po" and not t.get("deferred")]:
            sno, name = target["sno"], target["name"]
            verified = False
            observed = "no readback was attempted"
            for attempt in range(attempts):
                self.dcnm_intf_invalidate_serial_authority(sno)
                if not self.dcnm_intf_get_have_all_with_sno(sno):
                    observed = "the interface summary could not be read authoritatively"
                else:
                    entries = [h for h in self.have_all if h.get("serialNo") == sno]
                    if [h for h in entries if str(h.get("ifName", "")).lower() == name.lower()]:
                        observed = "the port-channel is still listed"
                    else:
                        self.dcnm_intf_bulk_fetch_intf_info(sno, refresh=True)
                        states = []
                        for m in target["members"]:
                            detail = self.dcnm_intf_get_intf_info(m["name"], sno, "INTERFACE_ETHERNET")
                            nv = ((detail.get("interfaces") or [{}])[0].get("nvPairs") or {}) if isinstance(detail, dict) else {}
                            summ = [h for h in entries if str(h.get("ifName", "")).lower() == m["name"].lower()]
                            states.append((m["name"], detail.get("policy") if isinstance(detail, dict) else None,
                                           str(nv.get("ADMIN_STATE", "")).strip().lower(),
                                           summ[0].get("complianceStatus") if len(summ) == 1 else None))
                        observed = "member state {0}".format(states) if states else "the deletion target names no member"
                        wanted = dict((m["name"].lower(), m["post"][0]) for m in target["members"])
                        routed_owner = []
                        if any(m["post"][0] == PVLAN_PO_ROUTED_BASELINE_POLICY for m in target["members"]):
                            self.pvlan_policies.pop(sno, None)  # fresh policy list for the routed ownership proof
                        for m in target["members"]:
                            if m["post"][0] == PVLAN_PO_ROUTED_BASELINE_POLICY:
                                d_ = self.dcnm_intf_get_intf_info(m["name"], sno, "INTERFACE_ETHERNET")
                                why = self.dcnm_intf_pvlan_check_ownership(
                                    m["name"], sno, PVLAN_PO_ROUTED_BASELINE_POLICY,
                                    ((d_.get("interfaces") or [{}])[0].get("nvPairs") if isinstance(d_, dict) else None),
                                    self_children=pvlan_released_routed_children(self.dcnm_intf_pvlan_release_admin() or "false"))
                                if why:
                                    routed_owner.append("{0}: {1}".format(m["name"], why))
                        if routed_owner:
                            observed = "released routed member ownership: {0}".format(routed_owner)
                        elif states and all(p == wanted.get(n.lower()) and a == self.dcnm_intf_pvlan_release_admin() and c == "In-Sync"
                                            for n, p, a, c in states):
                            # No child claim may survive: the host template creates the member's child policies
                            # (int_port_channel_pvlan_member and the int_eth "Inherited Commands") with the
                            # port-channel as their source (HOST:536-560). Fresh read, not the cached list.
                            self.pvlan_policies.pop(sno, None)
                            policies = self.dcnm_intf_pvlan_read_policies(sno)
                            if policies is None:
                                observed = "the switch policy list could not be read authoritatively"
                            else:
                                residue = sorted(
                                    "{0}/{1}/{2}".format(p.get("entityName"), p.get("templateName"), p.get("source"))
                                    for p in policies
                                    if p.get("deleted") is not True and str(p.get("deleted", "")).lower() != "true"
                                    and name.lower() in (str(p.get("entityName", "")).lower(), str(p.get("source", "")).lower()))
                                if residue:
                                    observed = "live policies still reference the port-channel: {0}".format(residue)
                                else:
                                    verified = True
                                    break
                if attempt < attempts - 1:
                    time.sleep(5)
            if not verified:
                self.module.fail_json(
                    msg="PVLAN port-channel {0} on {1} was deleted but its release could not be verified after {2} readback "
                    "attempts: {3}. Nothing else was sent; the member was not rewritten.".format(name, sno, attempts, observed),
                    **self.result)

    def dcnm_intf_pvlan_po_create_207(self, payload, resp):
        """A 207 answer to the port-channel CREATE is accepted only when every reportItemType is
        SUCCESS and a SUCCESS item names the port-channel; anything else stays a failure."""
        intf = (payload.get("interfaces") or [{}])[0]
        target = self.dcnm_intf_pvlan_target_map().get((intf.get("serialNumber"), str(intf.get("ifName", "")).lower()))
        if not target or target.get("kind") != "po" or not isinstance(resp, dict):
            return False
        if resp.get("RETURN_CODE") != 207 or resp.get("MESSAGE") != "Multi-Status":
            return False
        if self.dcnm_intf_collect_batch_errors(resp):
            return False
        return not pvlan_modify_outcome_problems(resp, [(target["sno"], target["name"])])

    # ================================================================ vPC PVLAN host
    # One vPC = ONE parent (int_vpc_pvlan_host, pair identity S1~S2) that the controller expands into one child port-channel and its
    # physical members per peer. Every decision below uses THAT peer's serial (a read of the second peer
    # invalidates part of the shared per-switch cache, so a leg is judged from its own copy), and the vPC is accepted only when
    # every expected leg is. Contract labels: [SRC] installed templates captured; [INF] inferred; [UNK] first live case.
    def dcnm_intf_pvlan_vpc_live(self, policies, entity=None, source=None):
        out = []
        for p in policies or []:
            if p.get("deleted") is True or str(p.get("deleted", "")).lower() == "true":
                continue
            if entity is not None and str(p.get("entityName", "")).lower() != str(entity).lower():
                continue
            if source is not None and str(p.get("source", "")).lower() != str(source).lower():
                continue
            out.append(p)
        return out

    def dcnm_intf_pvlan_vpc_read_leg(self, serial, vpc_name, po_name, member):
        """Fresh SNAPSHOT of one peer: interface summary entries, the child Po and member details, and the live policy list.
        A read that cannot be made authoritative is recorded as a problem and as "unreadable"/None, never as absence.
        `causes`: the same failures once per read stage of this peer (no interface names), with the reader's controlled reason, so a
        refusal can name the read that failed without repeating one cause per interface or per member."""
        return self.dcnm_intf_pvlan_vpc_read_serial(serial, [(vpc_name, po_name, member)])[(vpc_name.lower(), po_name.lower(), member.lower())]

    def dcnm_intf_pvlan_vpc_read_serial(self, serial, legs, summary_only=False):
        """VPC-READS: the fresh SNAPSHOTS of several legs of ONE peer serial from ONE summary, ONE forced bulk refresh and ONE policy-list
        read of that serial (all three are switch-wide). `legs`: [(vpc_name, po_name, member)]; returns {(vpc, po, member) lower: snap},
        each snap exactly as dcnm_intf_pvlan_vpc_read_leg builds it (problems / causes per leg, "unreadable"/None, never absence).
        `summary_only` reads the summary alone (the post-deploy verification of a deletion); "po", "member" and "policies" then stay
        "unreadable"/None and must not be judged."""
        snaps = {}
        for vpc_name, po_name, member in legs:
            snaps[(vpc_name.lower(), po_name.lower(), member.lower())] = {
                "serial": serial, "problems": [], "causes": [], "summary": {"po": [], "member": [], "vpc": []}, "summary_ok": False,
                "po": "unreadable", "member": "unreadable", "policies": None}
        # The summary is always read again: the generic summary of the OTHER peer rewrites this serial's have_all entries (pair union).
        if self.dcnm_intf_get_have_all_with_sno(serial):
            for vpc_name, po_name, member in legs:
                snap = snaps[(vpc_name.lower(), po_name.lower(), member.lower())]
                snap["summary_ok"] = True
                for label, name in (("po", po_name), ("member", member), ("vpc", vpc_name)):
                    for h in self.have_all:
                        if str(h.get("ifName", "")).lower() != name.lower():
                            continue
                        parts = [x.casefold() for x in (self._dcnm_intf_serial_parts(h.get("serialNo", "")) or ())]
                        if serial.casefold() in parts and (label == "vpc") == (len(parts) == 2):
                            snap["summary"][label].append(copy.deepcopy(h))
        else:
            cause = "the interface summary of {0} could not be read authoritatively{1}".format(
                serial, read_reason_suffix(self, "summary", serial))
            for snap in snaps.values():
                snap["problems"].append(cause)
                snap["causes"].append(cause)
        if summary_only:
            return snaps
        if not pvlan_prewrite_reusable(self, "detail", serial):
            self.dcnm_intf_bulk_fetch_intf_info(serial, refresh=True)
        for vpc_name, po_name, member in legs:
            snap = snaps[(vpc_name.lower(), po_name.lower(), member.lower())]
            for key, name, kind in (("po", po_name, "INTERFACE_PORT_CHANNEL"), ("member", member, "INTERFACE_ETHERNET")):
                if self.dcnm_intf_detail_unavailable(name, serial):
                    reason = read_reason_suffix(self, "detail", serial)
                    snap["problems"].append("the detail of {0} on {1} could not be read authoritatively{2}".format(name, serial, reason))
                    cause = "the interface detail of {0} could not be read authoritatively{1}".format(serial, reason)
                    if cause not in snap["causes"]:
                        snap["causes"].append(cause)
                    continue
                found = self.dcnm_intf_get_intf_info(name, serial, kind)
                snap[key] = copy.deepcopy(found) if isinstance(found, dict) else None  # None: authoritatively absent
        if pvlan_prewrite_reusable(self, "policies", serial):
            self.pvlan_policies[serial] = copy.deepcopy(self.__dict__["pvlan_prewrite_reads"]["policies"][str(serial)])
        else:
            self.pvlan_policies.pop(serial, None)
        policies = self.dcnm_intf_pvlan_read_policies(serial)
        for snap in snaps.values():
            if policies is None:
                cause = "the switch policy list of {0} could not be read authoritatively{1}".format(
                    serial, read_reason_suffix(self, "policies", serial))
                snap["problems"].append(cause)
                snap["causes"].append(cause)
            else:
                snap["policies"] = copy.deepcopy(policies)
        return snaps

    @staticmethod
    def dcnm_intf_pvlan_vpc_nv(detail):
        nv = ((detail.get("interfaces") or [{}])[0].get("nvPairs")) if isinstance(detail, dict) else None
        return nv if isinstance(nv, dict) else None

    def dcnm_intf_pvlan_vpc_member_baseline(self, snap, member, mode=None):
        """Reasons the member of one peer cannot be the baseline of a NEW vPC member (create): snapshot-based equivalent of the
        Ethernet ownership check plus the Po member baseline. `mode` is the vPC submode; for trunk secondary the member must be
        PREPARED as access or routed and a switchport-trunk member is refused (the regular-Po known incident, transferred conservatively;
        po_member_baseline_problems). Each peer is judged on its own snapshot, so BOTH must qualify. Nothing is converted."""
        detail = snap["member"]
        if snap["problems"] or detail == "unreadable" or snap["policies"] is None or not snap["summary_ok"]:
            return ["its current state could not be read authoritatively"]
        if not isinstance(detail, dict):
            return ["it is not an existing physical interface known to the controller (preprovisioning is not implemented)"]
        policy, nv = detail.get("policy"), self.dcnm_intf_pvlan_vpc_nv(detail)
        if policy == PO_MEMBER_POLICY or policy in self.dcnm_intf_pvlan_member_policies():
            return ["it is already a port-channel member ({0})".format(policy)]
        problems = pvlan_po_member_baseline_problems(policy, nv, mode)
        if problems:
            return problems
        entries = snap["summary"]["member"]
        if len(entries) != 1:
            return ["the interface summary holds {0} entries for it".format(len(entries))]
        entry = entries[0]
        if entry.get("ifType") != "INTERFACE_ETHERNET" or str(entry.get("isPhysical")).lower() != "true":
            return ["it is not a standalone physical Ethernet interface"]
        state, summary = pvlan_summary_policy(entry, member)
        if state != PVLAN_SUMMARY_KNOWN:
            return [summary if isinstance(summary, str) else "the interface summary lists no readable underlay policy, so ownership is unknown"]
        if summary["templateName"] != policy or summary["source"]:
            return ["its policy is {0}/{1!r} in the summary, not a direct {2}".format(summary["templateName"], summary["source"], policy)]
        live = self.dcnm_intf_pvlan_vpc_live(snap["policies"], entity=member)
        if policy == PVLAN_PO_ROUTED_BASELINE_POLICY:
            # Measured: a member prepared as routed keeps three child policies whose source is the member itself; which
            # admin child (shut/no_shut) follows the member's own ADMIN_STATE (ADMIN-UP-ALL-MODES).
            own = pvlan_po_routed_member_self_children(nv)
            live = [p for p in live if not (p.get("templateName") in own and str(p.get("source", "")).lower() == member.lower())]
        if len(live) != 1:
            return ["the switch policy list holds {0} live policies for it ({1})".format(
                len(live), ", ".join(sorted("{0}/{1}".format(p.get("templateName"), p.get("source")) for p in live)))]
        pol = live[0]
        if (str(pol.get("entityType", "")).upper() != "INTERFACE" or pol.get("source") != "" or pol.get("templateName") != policy
                or pol.get("policyId") != summary["policyId"]):
            return ["its switch policy is {0}/{1!r}, not the direct {2} the summary reports".format(pol.get("templateName"), pol.get("source"), policy)]
        return []

    def dcnm_intf_pvlan_vpc_absent_problems(self, snap, vpc_name, po_name):
        """A new vPC leg: neither the child Po nor any policy of the vPC may exist on this peer."""
        if snap["problems"] or snap["po"] == "unreadable" or snap["policies"] is None or not snap["summary_ok"]:
            return ["the absence of the port-channel and of the vPC children could not be established authoritatively"]
        problems = []
        if snap["po"] is not None:
            problems.append("the controller already holds an intent for {0}".format(po_name))
        if snap["summary"]["po"]:
            problems.append("the interface summary lists {0}".format(po_name))
        if snap["summary"]["vpc"]:
            problems.append("the interface summary lists {0}".format(vpc_name))
        stray = (self.dcnm_intf_pvlan_vpc_live(snap["policies"], entity=po_name) + self.dcnm_intf_pvlan_vpc_live(snap["policies"], entity=vpc_name)
                 + self.dcnm_intf_pvlan_vpc_live(snap["policies"], source=vpc_name))
        if stray:
            problems.append("the switch policy list holds {0} live policy(ies) for this absent vPC or port-channel".format(len(stray)))
        return problems

    def dcnm_intf_pvlan_vpc_present_problems(self, snap, vpc_name, po_name, member, expected_po_nv, expected_member_nv=None, member_check=True):
        """An existing vPC leg: the child Po and the member are the ones the parent's intent implies, owned by the vPC. MM-B: for a member ADDED
        by an update (`member_check` False) only the existing child Po is judged here; the joining port has its own baseline check."""
        if snap["problems"] or snap["po"] in ("unreadable", None) or snap["member"] in ("unreadable", None) or snap["policies"] is None:
            return ["its child port-channel or member could not be read authoritatively, or is absent (a parent without its child on one peer "
                    "is a partial state)"]
        problems = []
        po = snap["po"]
        if po.get("policy") != VPC_PO_POLICY:
            problems.append("{0} holds {1}, not {2}".format(po_name, po.get("policy"), VPC_PO_POLICY))
        else:
            diffs = pvlan_vpc_child_differences(self.dcnm_intf_pvlan_vpc_nv(po), expected_po_nv)
            if diffs:
                problems.append("the child {0} does not follow the parent's intent (differs in {1}): partial state".format(po_name, ", ".join(diffs)))
        live = self.dcnm_intf_pvlan_vpc_live(snap["policies"], entity=po_name)
        if (len(live) != 1 or live[0].get("templateName") != VPC_PO_POLICY or str(live[0].get("source", "")).lower() != vpc_name.lower()
                or str(live[0].get("entityType", "")).upper() != "INTERFACE"):
            problems.append("the switch policy list does not hold exactly one {0} policy of {1} for {2} ({3})".format(
                VPC_PO_POLICY, vpc_name, po_name,
                ", ".join(sorted("{0}/{1}".format(p.get("templateName"), p.get("source")) for p in live)) or "none"))
        if not member_check:
            return problems
        mdetail = snap["member"]
        mnv = self.dcnm_intf_pvlan_vpc_nv(mdetail)
        if mdetail.get("policy") != PO_MEMBER_POLICY or str((mnv or {}).get("PO_ID", "")).lower() != po_name.lower():
            problems.append("member {0} is not the member of {1} in the controller's intent ({2})".format(member, po_name, mdetail.get("policy")))
        elif expected_member_nv is not None:
            # The fields that decide the member's CLI are compared with the model EXPECTED for this peer (inherited
            # values come from the frozen pre-state), so a generic In-Sync or a correct Po/other peer never hides a wrong member.
            diffs = pvlan_vpc_member_differences(mnv, expected_member_nv)
            if diffs:
                problems.append("member {0} differs from the expected member model: {1}".format(member, "; ".join(diffs)))
        mlive = self.dcnm_intf_pvlan_vpc_live(snap["policies"], entity=member)
        owned = [p for p in mlive if p.get("templateName") == PO_MEMBER_POLICY and str(p.get("source", "")).lower() == vpc_name.lower()]
        extra = [p for p in mlive if p not in owned and not (p.get("templateName") == "int_eth" and str(p.get("source", "")).lower() == vpc_name.lower())]
        if len(owned) != 1 or extra:
            problems.append("the switch policy list does not hold exactly one {0} policy of {1} for {2} (and only its inherited commands): {3}".format(
                PO_MEMBER_POLICY, vpc_name, member, ", ".join(sorted("{0}/{1}".format(p.get("templateName"), p.get("source")) for p in mlive)) or "none"))
        return problems

    def dcnm_intf_pvlan_vpc_parent_problems(self, name, snaps, detail_policy, detail_nv):
        """Ownership of the vPC parent. The detail intent must be int_vpc_pvlan_host. A parent policy listed on a peer must be ONE
        direct int_vpc_pvlan_host; a parent listed nowhere is tolerated (its listing is [UNK] until the first live case). A vPC entry
        in the interface summary must be an INTERFACE_VPC and, when it reports its policy, that one."""
        problems = []
        if detail_policy != VPC_HOST_POLICY:
            return ["it holds {0}, not {1}".format(detail_policy, VPC_HOST_POLICY)]
        listed = {}
        for snap in snaps:
            for p in self.dcnm_intf_pvlan_vpc_live(snap["policies"], entity=name):
                listed[p.get("policyId")] = p
        if len(listed) > 1:
            problems.append("the policy lists hold {0} live policies for {1}".format(len(listed), name))
        for p in listed.values():
            if p.get("templateName") != VPC_HOST_POLICY or p.get("source") != "" or str(p.get("entityType", "")).upper() != "INTERFACE":
                problems.append("the policy list holds {0}/{1} (source {2!r}) for {3}, not a direct {4}".format(
                    p.get("entityType"), p.get("templateName"), p.get("source"), name, VPC_HOST_POLICY))
            if isinstance(detail_nv, dict) and "POLICY_ID" in detail_nv and detail_nv["POLICY_ID"] != p.get("policyId"):
                problems.append("the detail POLICY_ID {0!r} disagrees with the listed policy id {1!r}".format(detail_nv["POLICY_ID"], p.get("policyId")))
        entries = {}
        for snap in snaps:
            for h in snap["summary"]["vpc"]:
                entries[(h.get("serialNo"), str(h.get("ifName", "")).lower())] = h
        if len(entries) > 1:
            problems.append("the interface summary holds {0} entries for {1}".format(len(entries), name))
        for h in entries.values():
            if h.get("ifType") != "INTERFACE_VPC":
                problems.append("the interface summary describes {0} as {1}, not a vPC".format(name, h.get("ifType")))
                continue
            state, summary = pvlan_summary_policy(h, name)
            if state == PVLAN_SUMMARY_KNOWN and (summary["templateName"] != VPC_HOST_POLICY or summary["source"]):
                problems.append("the interface summary reports {0}/{1!r} for {2}".format(summary["templateName"], summary["source"], name))
        return problems

    @staticmethod
    def dcnm_intf_pvlan_vpc_legs(target):
        return target.get("legs") or []

    def dcnm_intf_pvlan_vpc_register_removed(self, name, sno, legs, result, have_nv, deploy):
        """MM-B: the members an UPDATE removes from one peer (or both) of an existing vPC, checked before any write: each is that peer's
        int_port_channel_pvlan_member of the child port-channel, administratively down, whose live policies are exactly the vPC's (its
        member policy and inherited commands, source = the vPC); plus the deletion's global preconditions (fabric host default down, bulk
        API, deployed, not check mode). Returns ([removed legs], [(label, serial, reason)]). A removed leg carries its pre models (it is an
        existing, converged leg for the prior gate) and the predicted release until the fresh release replaces it after the modify."""
        entries, problems = [], []
        removed = result.get("removed") or {}
        if not removed:
            return entries, problems
        common = []
        if self.module.check_mode:
            common.append("removing a vPC member is refused in check mode: the pre-deploy gate needs the update to exist")
        # Deploy false SAVES the removal on its peer(s) without deploying it (see the regular port-channel).
        if self.dcnm_intf_pvlan_release_admin_problem():
            common.append(self.dcnm_intf_pvlan_release_admin_problem())
        if not self.module.check_mode and not self.has_bulk_api:
            common.append("the controller's bulk interface update API is not available: the released member's administrative state could not be "
                          "corrected before the deploy")
        for index, members in sorted(removed.items()):
            peer_legs = [leg for leg in legs if leg["index"] == index]
            if not peer_legs:
                problems.append((name, sno, "peer {0} keeps no member after the update; an empty member list is not implemented".format(index + 1)))
                continue
            serial = peer_legs[0]["serial"]
            pcid = str(have_nv.get("PEER%d_PCID" % (index + 1), "")).strip()
            po_name = pvlan_vpc_po_name(pcid)
            for token in members:
                member = self.dcnm_intf_pvlan_po_member_ifname(token, serial)
                snap = self.dcnm_intf_pvlan_vpc_read_leg(serial, name, po_name, member)
                reasons = list(common)
                mdetail, mnv = snap["member"], self.dcnm_intf_pvlan_vpc_nv(snap["member"])
                if snap["problems"] or mdetail in ("unreadable", None) or snap["policies"] is None:
                    reasons.append("its current state could not be read authoritatively")
                elif mdetail.get("policy") != PO_MEMBER_POLICY or str((mnv or {}).get("PO_ID", "")).lower() != po_name.lower():
                    reasons.append("it is not the member of {0} in the controller's intent ({1})".format(po_name, mdetail.get("policy")))
                elif str((mnv or {}).get("ADMIN_STATE", "")).strip().lower() not in ("true", "false"):
                    reasons.append("its administrative state is unknown ({0!r})".format((mnv or {}).get("ADMIN_STATE")))
                else:
                    mlive = self.dcnm_intf_pvlan_vpc_live(snap["policies"], entity=member)
                    owned = [x for x in mlive if x.get("templateName") == PO_MEMBER_POLICY and str(x.get("source", "")).lower() == name.lower()]
                    extra = [x for x in mlive if x not in owned
                             and not (x.get("templateName") == "int_eth" and str(x.get("source", "")).lower() == name.lower())]
                    if len(owned) != 1 or extra:
                        reasons.append("its live policies are not exactly those of {0}: {1}".format(
                            name, ", ".join(sorted("{0}/{1}".format(x.get("templateName"), x.get("source")) for x in mlive)) or "none"))
                if reasons:
                    problems += [(member, serial, "removing it from {0}: {1}".format(name, r)) for r in reasons]
                    continue
                po_pre, mem_pre = pvlan_vpc_leg_models(have_nv, index, name, mnv, True)
                entries.append({"index": index, "serial": serial, "member": member, "name": member, "po_name": po_name, "pcid": pcid,
                                "pc_mode": str(have_nv.get("PC_MODE", "active")), "pre_po": po_pre, "pre_member": mem_pre,
                                "pre": mem_pre, "post": (PVLAN_TRUNK_HOST_POLICY, self.dcnm_intf_pvlan_released_model()),
                                "policy_id": (mnv or {}).get("POLICY_ID")})
        return entries, problems

    def dcnm_intf_pvlan_switch_in_sync(self, sno):
        """True only when the inventory read at the start of this run reports `sno` explicitly In-Sync (an absent or other ccStatus is not)."""
        inventory = [v for v in (getattr(self, "inventory_data", None) or {}).values()
                     if isinstance(v, dict) and str(v.get("serialNumber", "")).casefold() == str(sno).casefold()]
        return len(inventory) == 1 and str(inventory[0].get("ccStatus", "")).strip() == "In-Sync"

    def dcnm_intf_pvlan_vpc_resume_removed(self, target, legs, previews, state="completing the saved removal"):
        """The continuation of a SAVED member removal of a PVLAN vPC (deploy false earlier, in another process), repeated
        with deploy true. Recognised ONLY from the controller's state, per peer, in THAT peer's fresh forced preview: a port the DEVICE still
        joins to the peer's child port-channel (`channel-group N`), with pending, that the vPC intent no longer lists for that peer, whose own
        intent is a released member policy at the fabric's host default, with no live policy of the vPC or of its child port-channel. Each is
        returned as a removed leg ("resumed": already released -- never released again) and is then judged exactly like a member the update
        removed (force withdrawal, released model, post-deploy verification). Anything else is not a resumption and stays outside."""
        out = []
        admin = self.dcnm_intf_pvlan_release_admin()
        if admin is None:
            return out
        known = set((r["serial"], r["member"].lower()) for r in target.get("removed_legs") or [])
        for index in (0, 1):
            peer_legs = [leg for leg in legs if leg["index"] == index]
            if not peer_legs:
                continue
            sno, po_name, pcid = peer_legs[0]["serial"], peer_legs[0]["po_name"], str(peer_legs[0].get("pcid") or "")
            if sno not in previews:
                previews[sno] = dcnm_send(self.module, "GET", self.paths["PVLAN_CONFIG_PREVIEW"].format(self.fabric, sno))
            try:
                entry = pvlan_preview_entry(previews[sno], sno)
                blocks, _global = pvlan_split_blocks(entry["pendingConfig"])
            except PvlanError:
                continue  # the gate itself reports the unreadable preview
            running = entry.get("runningConfig") if isinstance(entry.get("runningConfig"), list) else None
            number = re.match(r"^port-channel([0-9]+)$", str(po_name).lower())
            if running is None or not number:
                continue
            joined, pc_mode = pvlan_running_po_members(running, number.group(1))
            listed = set(leg["member"].lower() for leg in peer_legs)
            for member in joined:
                name = self.dcnm_intf_pvlan_po_member_ifname(member, sno)
                lname = name.lower()
                if lname in listed or lname not in blocks or (sno, lname) in known:
                    continue
                m_problems, m_policy, m_nv = self.dcnm_intf_pvlan_po_member_context(name, sno)
                if m_problems or m_policy not in PVLAN_RELEASED_MEMBER_POLICIES or not isinstance(m_nv, dict):
                    continue
                if str(m_nv.get("ADMIN_STATE", "")).strip().lower() != admin:
                    continue
                policies = self.dcnm_intf_pvlan_read_policies(sno)
                if policies is None or any(
                        p.get("templateName") == PO_MEMBER_POLICY
                        or str(p.get("source", "")).lower() in (target["name"].lower(), str(po_name).lower())
                        for p in self.dcnm_intf_pvlan_vpc_live(policies, entity=name)):
                    continue  # unreadable, or still claimed by the vPC: not a release
                released = dict((k, v) for k, v in m_nv.items() if k not in PVLAN_PO_RELEASE_METADATA)
                out.append({"index": index, "serial": sno, "member": name, "name": name, "po_name": po_name, "pcid": pcid or number.group(1),
                            "pc_mode": pc_mode or "active", "pre": (PO_MEMBER_POLICY, {"CONF": ""}), "pre_member": (PO_MEMBER_POLICY, {"CONF": ""}),
                            "post": (m_policy, released), "released": True, "resumed": True, "policy_id": m_nv.get("POLICY_ID")})
                known.add((sno, lname))
        if out:
            target.setdefault("removed_legs", []).extend(out)
            self.result.setdefault("pvlan_saved", []).append({
                "kind": "vpc", "name": target["name"], "serial": target["sno"], "operation": "remove member",
                "members": ["{0} on peer {1}".format(r["member"], r["index"] + 1) for r in out], "state": state})
        return out

    def dcnm_intf_pvlan_vpc_removed_decision(self, rleg, entry, blocks):
        """MM-B: (decision, problems) of a member REMOVED from one peer, from that peer's fresh preview: the FRESH release (never the
        prediction), its membership withdrawn with the force command form (MEASURED for a regular Po deletion; INFERRED here) and the rest of
        its pending taken to the released state. The child port-channel stays (it is judged with the peer's remaining members)."""
        if not rleg.get("released"):
            return "refuse", ["{0}: the removed member was not released before the deploy".format(rleg["member"])]
        body = blocks.get(rleg["member"].lower(), [])
        body, withdrawn = pvlan_po_member_force_withdrawal(body, rleg["pcid"], rleg["pc_mode"])
        if withdrawn:
            return "refuse", ["{0}: {1}".format(rleg["member"], f) for f in withdrawn]
        decision, found = pvlan_assess_target(body, entry, rleg["member"], pvlan_render(*rleg["post"]),
                                              pvlan_transition_vocabulary(rleg["pre"], rleg["post"]), release=True)
        problems = ["{0}: {1}".format(rleg["member"], f) for f in found]
        return ("refuse", problems) if problems or decision == "refuse" else ("deploy", [])

    def dcnm_intf_pvlan_vpc_compare(self, state, want, match_have, name, sno, fabric, deploy):
        """Reconcile one int_vpc_pvlan_host WANT. Returns "create" when the generic creation
        path must continue and "done" when this method handled the entry or refused it. Both peers are read and judged before
        anything is registered; any problem on any peer refuses the whole vPC before a write."""
        match_pb = [
            pb for pb in self.pb_input
            if name.lower() == pb["ifname"].lower() and sno == pb["sno"] and fabric == pb["fabric"]
        ]
        if len(match_pb) != 1:
            self.dcnm_intf_pvlan_block(name, sno, "the playbook names this vPC {0} times".format(len(match_pb)))
            return "done"
        raw = dict((k, v) for k, v in match_pb[0].items() if k in VPC_PROFILE_KEYS and v is not None)
        try:
            legs = pvlan_vpc_pair_view(raw, sno, match_pb[0].get("peer_serials"), name)
        except PvlanError as exc:
            self.dcnm_intf_pvlan_block(name, sno, str(exc))
            return "done"
        if len(match_have) > 1:
            self.dcnm_intf_pvlan_block(name, sno, "current state is ambiguous ({0} detail entries)".format(len(match_have)))
            return "done"
        have_policy, have_nv = None, None
        if match_have:
            have_policy = match_have[0].get("policy")
            have_nv = self.dcnm_intf_pvlan_vpc_nv(match_have[0])
        else:
            self.dcnm_intf_require_detail_authority(name, sno)
        try:
            result = pvlan_reconcile_vpc(
                state, raw, name, legs, have_policy, have_nv,
                ndfc_version=getattr(self, "ndfc_version", None), patch_version=getattr(self, "patch_version", None))
        except PvlanError as exc:
            self.dcnm_intf_pvlan_block(name, sno, str(exc))
            return "done"
        if result["blocked"]:
            for reason in result["blocked"]:
                self.dcnm_intf_pvlan_block(name, sno, reason)
            return "done"
        creates, new_nv = result["creates"], result["nv"]
        # The controller's own spelling of each member (a Manage-created member is listed as `e1/8`); an explicit port
        # resolves through the peer's bulk detail, anything else is returned unchanged and refused as before.
        # Keep one existing member model per physical port. The peer index and serial
        # stay attached to every record; payload generation still uses the two parent lists.
        legs = [dict(leg, member=self.dcnm_intf_pvlan_po_member_ifname(m, leg["serial"]),
                     added=pvlan_po_member_canonical(m) in (result.get("added") or {}).get(leg["index"], []))
                for leg, text in zip(legs, result["members"])
                for m in sorted(pvlan_normalize_member_list(text)[0])]
        members = [leg["member"] for leg in legs]
        claimed = self.__dict__.setdefault("pvlan_po_claimed", {})
        snaps, problems = [], []
        for leg, member in zip(legs, members):
            leg["po_name"] = pvlan_vpc_po_name(str(new_nv.get("PEER%d_PCID" % (leg["index"] + 1), "")).strip())
            leg["pcid"] = str(new_nv.get("PEER%d_PCID" % (leg["index"] + 1), "")).strip()
            leg["pc_mode"] = str(new_nv.get("PC_MODE", "active"))
            leg["joining"] = bool(creates) or bool(leg.get("added"))
            leg["member"] = member
            snaps.append(self.dcnm_intf_pvlan_vpc_read_leg(leg["serial"], name, leg["po_name"], member))
            claim_key = (leg["serial"], member.lower())
            if claimed.setdefault(claim_key, name.lower()) != name.lower():
                problems.append((member, leg["serial"], "the playbook also assigns it to {0}".format(claimed[claim_key])))
            # The port-channel number is independent of the vPC id, so two vPCs of one request can name the same child on a peer.
            po_key = (leg["serial"], "po:" + leg["po_name"].lower())
            if claimed.setdefault(po_key, name.lower()) != name.lower():
                problems.append((leg["po_name"], leg["serial"], "the playbook also uses this port-channel number for {0}".format(claimed[po_key])))
        removed_legs = []
        snap_reported = set()

        def report_snapshot(snap):
            # As dcnm_intf_pvlan_vpc_verify does: name the read that could not be made authoritative (stage, serial, controlled reason),
            # once per peer and cause, next to the general refusal it explains. Nothing here changes what is refused.
            for cause in snap["causes"]:
                if (snap["serial"], cause) not in snap_reported:
                    snap_reported.add((snap["serial"], cause))
                    problems.append((name, snap["serial"], cause))

        if creates:
            parent_known = [h for snap in snaps for h in snap["summary"]["vpc"]]
            if parent_known:
                problems.append((name, sno, "the interface summary lists {0} but the interface detail holds no policy".format(name)))
            for leg, snap in zip(legs, snaps):
                problems += [(name, snap["serial"], m) for m in self.dcnm_intf_pvlan_vpc_absent_problems(snap, name, leg["po_name"])]
                problems += [(leg["member"], snap["serial"], m) for m in
                             self.dcnm_intf_pvlan_vpc_member_baseline(snap, leg["member"], new_nv.get("PVLAN_MODE"))]
                report_snapshot(snap)
        else:
            problems += [(name, sno, m) for m in self.dcnm_intf_pvlan_vpc_parent_problems(name, snaps, have_policy, have_nv)]
            for leg, snap in zip(legs, snaps):
                # The combined speed + duplex transition is judged on EACH peer's own child (a child that diverged from the parent
                # may need it although the parent does not); any peer that needs it refuses the whole invocation before a write.
                child_nv = self.dcnm_intf_pvlan_vpc_nv(snap["po"]) if isinstance(snap["po"], dict) else None
                if child_nv is not None and pvlan_speed_duplex_combined_change(child_nv, new_nv):
                    problems.append((name, snap["serial"], pvlan_speed_duplex_combined_message_text))
                expected = pvlan_vpc_leg_po_nv(have_nv, leg["index"], name)
                if leg["joining"]:
                    # MM-B: an ADDED member joins the existing child Po exactly as in a creation (baseline, ownership, submode rules)
                    problems += [(name, snap["serial"], m) for m in
                                 self.dcnm_intf_pvlan_vpc_present_problems(snap, name, leg["po_name"], leg["member"], expected, member_check=False)]
                    problems += [(leg["member"], snap["serial"], m) for m in
                                 self.dcnm_intf_pvlan_vpc_member_baseline(snap, leg["member"], new_nv.get("PVLAN_MODE"))]
                    continue
                expected_member = pvlan_vpc_leg_models(have_nv, leg["index"], name, self.dcnm_intf_pvlan_vpc_nv(snap["member"]), True)[1][1]
                problems += [(name, snap["serial"], m) for m in
                             self.dcnm_intf_pvlan_vpc_present_problems(snap, name, leg["po_name"], leg["member"], expected, expected_member)]
            if any(leg["joining"] for leg in legs):
                # A member joins: every peer's read (joining or kept) gates the invocation, so every unreadable one is named.
                for snap in snaps:
                    report_snapshot(snap)
            removed_legs, removed_problems = self.dcnm_intf_pvlan_vpc_register_removed(name, sno, legs, result, have_nv, deploy)
            problems += removed_problems
        if problems:
            for label, serial, reason in problems:
                self.dcnm_intf_pvlan_block(label, serial, reason)
            return "done"
        for leg, snap in zip(legs, snaps):
            member_nv = self.dcnm_intf_pvlan_vpc_nv(snap["member"])
            idx = leg["index"]
            if creates:
                leg["pre_po"] = (None, None)
                leg["pre_member"] = (snap["member"].get("policy"), copy.deepcopy(member_nv))
            elif leg["joining"]:
                # MM-B: the child Po exists (its model from HAVE); the port joins from its own baseline policy
                leg["pre_po"] = pvlan_vpc_leg_models(have_nv, idx, name, member_nv, False)[0]
                leg["pre_member"] = (snap["member"].get("policy"), copy.deepcopy(member_nv))
            else:
                po_pre, mem_pre = pvlan_vpc_leg_models(have_nv, idx, name, member_nv, True)
                leg["pre_po"], leg["pre_member"] = po_pre, mem_pre
            po_post, mem_post = pvlan_vpc_leg_models(new_nv, idx, name, member_nv, not leg["joining"])
            leg["post_po"], leg["post_member"] = po_post, mem_post
            leg["expect"] = "deploy" if leg["joining"] or pvlan_vpc_leg_cli_changes(
                (leg["pre_po"], leg["pre_member"]), (po_post, mem_post)) else "converged"
        # STAGED (live S3b/S3d): a vPC created with deploy false and repeated unchanged with deploy true is a SAVED CREATION, not a
        # deployed baseline. It is recognised only from the controller's own state (dcnm_intf_pvlan_vpc_saved_creation); each leg is then
        # judged exactly as a creation (the child Po absent from the device, the member joining from a standalone trunk host) and the vPC
        # gets the creation rule: BOTH peers must still need the deploy. Nothing is rewritten; only the deploy is sent.
        resumes = (not creates and not result["update"] and str(deploy).lower() == "true"
                   and self.dcnm_intf_pvlan_vpc_saved_creation(snaps))
        if resumes:
            for leg in legs:
                leg["pre_po"], leg["pre_member"], leg["joining"] = (None, None), (PVLAN_TRUNK_HOST_POLICY, {}), True
        # The member template's own precondition for a LACP rate change (member admin down), on BOTH peers; never forced.
        lacp_problems = [(leg["member"], leg["serial"], m) for leg in legs for m in pvlan_member_lacp_rate_problems(
            leg["member"], leg["pre_member"][1], leg["post_member"][1], not leg["joining"])]
        if lacp_problems:
            for label, serial, reason in lacp_problems:
                self.dcnm_intf_pvlan_block(label, serial, reason)
            return "done"
        if result["update"]:
            # An update whose IDEAL pending the pre-deploy gate could not validate would be refused AFTER the intent changed: refuse it now.
            blocked_before = len(self.pvlan_blocked)
            for leg in legs:
                pairs = [(leg["po_name"], leg["pre_po"], leg["post_po"])]
                if not leg["joining"]:  # MM-B: a joining member is validated by the force transition, as in a creation
                    pairs.append((leg["member"], leg["pre_member"], leg["post_member"]))
                for label, pre_pair, post_pair in pairs:
                    pre_model, post_model = pvlan_render(*pre_pair), pvlan_render(*post_pair)
                    if pre_model.modeled and post_model.modeled and (pre_model.scalars, pre_model.pairs) != (post_model.scalars, post_model.pairs):
                        for reason in pvlan_vpc_transition_problems(pre_model, post_model):
                            self.dcnm_intf_pvlan_block(
                                label, leg["serial"], "the update cannot be validated by the pre-deploy gate, so it is refused before the intent "
                                "changes: {0}".format(reason))
            if len(self.pvlan_blocked) > blocked_before:
                return "done"
        target = {
            "name": name, "sno": sno, "kind": "vpc", "creates": creates, "update": result["update"], "deletes": False,
            "pre": (have_policy, copy.deepcopy(have_nv)) if have_policy else (None, None),
            "post": (VPC_HOST_POLICY, copy.deepcopy(new_nv)), "new_secondaries": result.get("new_secondaries") or [], "members": [],
            "legs": legs, "prior": None, "removed_legs": [] if creates else removed_legs, "resumes": resumes,
            "deferred_update": bool(removed_legs) and not creates and str(deploy).lower() != "true",
        }
        self.pvlan_targets[(sno, name.lower())] = target
        want["interfaces"][0]["nvPairs"] = new_nv
        deploying = str(deploy).lower() == "true"
        if creates:
            return "create"
        if not deploying and not result["update"] and not all(self.dcnm_intf_pvlan_switch_in_sync(leg["serial"]) for leg in legs):
            # A saved member removal repeated with deploy false writes nothing and is reported still pending
            self.dcnm_intf_pvlan_vpc_resume_removed(target, legs, {}, state="saved, awaiting deployment (nothing written by this run)")
        if deploying and resumes:
            # STAGED: the saved creation is judged and its deploy queued in the preflight (dcnm_intf_pvlan_vpc_resume_gates), once every
            # saved vPC this request completes is registered: their pending is then this request's own, not foreign.
            return "done"
        if deploying:
            # Pre-write gate: the CURRENT state of BOTH peers must be coherent before an update or a repetition acts on it. This is where a
            # pre-existing partial state (one peer applied, the other not) is rejected -- before any modify.
            decision, found = self.dcnm_intf_pvlan_vpc_gate(target, [], "prior", "pre")
            if decision == "refuse":
                for reason in found:
                    self.dcnm_intf_pvlan_block(name, sno, reason)
                return "done"
            resuming = decision == "deploy" and any(r.get("resumed") for r in target.get("removed_legs") or [])
            if resuming:
                # Every kept leg is converged and the only pending work is the saved removal: deploy it (judged again by the gate)
                decision = "converged"
                if not result["update"]:
                    delem = {"serialNumber": sno, "ifName": name, "fabricName": self.fabric}
                    self.diff_deploy.append(delem)
                    self.changed_dict[0]["deploy"].append(copy.deepcopy(delem))
            if decision != "converged":
                # Both peers still have pending work: the intent is saved but not applied. Continuing an unapplied vPC is NOT implemented
                # in this delivery (its recovery is the deletion, or a deployment made outside this request): stop and preserve.
                self.dcnm_intf_pvlan_block(
                    name, sno, "the intent of the vPC is saved but not applied on either peer; a repetition or an update is accepted only from a "
                    "coherent, deployed baseline on both peers, and completing an unapplied vPC is not implemented")
                return "done"
            target["prior"] = decision
        if result["update"]:
            changed_dict = copy.deepcopy(want)
            changed_dict.pop("skipResourceCheck", None)
            changed_dict["interfaces"][0].pop("interfaceType", None)
            changed_dict["interfaces"][0].pop("fabricName", None)
            changed_dict["interfaces"][0]["nvPairs"] = copy.deepcopy(result["changed"])
            want.pop("interfaceType", None)
            self.dcnm_intf_merge_intf_info(want, self.diff_replace)
            self.changed_dict[0][state].append(changed_dict)
        if deploying and result["update"]:
            delem = {"serialNumber": sno, "ifName": name, "fabricName": self.fabric}
            self.diff_deploy.append(delem)
            self.changed_dict[0]["deploy"].append(copy.deepcopy(delem))
        return "done"

    def dcnm_intf_pvlan_vpc_resume_gates(self):
        """STAGED + VPC-BATCH-GATE: the pre-write check of every saved vPC this request completes (deploy true on a saved creation).
        Each must still be pending on BOTH peers, coherent with this request, with nothing foreign. The pending of the OTHER saved vPCs
        completed by this same request is theirs (dcnm_intf_pvlan_vpc_batch_scope); a saved vPC that is not in the request stays
        foreign. Only then is the deploy queued; nothing is rewritten."""
        resumed = [t for t in self.dcnm_intf_pvlan_target_map().values() if t.get("kind") == "vpc" and t.get("resumes")]
        items = [{"serialNumber": t["sno"], "ifName": t["name"], "fabricName": self.fabric} for t in resumed]
        for target, delem in zip(resumed, items):
            decision, found = self.dcnm_intf_pvlan_vpc_gate(target, items, "prior", "post")
            if decision != "deploy":
                for reason in found or ["the saved creation is not pending on both peers"]:
                    self.dcnm_intf_pvlan_block(target["name"], target["sno"], reason)
                continue
            target["prior"] = decision
            self.diff_deploy.append(delem)
            self.changed_dict[0]["deploy"].append(copy.deepcopy(delem))

    @staticmethod
    def dcnm_intf_pvlan_vpc_saved_creation(snaps):
        """True when the controller lists this vPC's parent, on EVERY peer's authoritative summary, exactly once and with complianceStatus
        present and null: the MEASURED shape of a vPC whose intent was saved and never deployed (NDFC 12.6.0.267). A peer that
        reports any compliance value, a missing or duplicated parent, or an unreadable summary is not a saved creation."""
        if not snaps:
            return False
        for snap in snaps:
            parents = snap["summary"]["vpc"]
            if snap["problems"] or not snap["summary_ok"] or len(parents) != 1:
                return False
            if "complianceStatus" not in parents[0] or parents[0]["complianceStatus"] is not None:
                return False
        return True

    def dcnm_intf_pvlan_vpc_leg_decision(self, leg, entry, blocks, which):
        """(decision, problems) of ONE peer from ONE fresh preview entry: the child Po and the member, each against its own model."""
        if which == "delete":
            problems = []
            if not isinstance(entry.get("expectedConfig"), list):
                return "refuse", ["the fresh preview carries no expectedConfig, so the deletion cannot be validated"]
            count, _body = pvlan_interface_stanza(entry["expectedConfig"], leg["po_name"])
            if count:
                problems.append("the controller's expected configuration still holds {0}".format(leg["po_name"]))
            kept = [line for line in blocks.get(leg["po_name"].lower(), []) if not line.startswith("no ")]
            if kept:
                problems.append("the pending for the deleted port-channel carries non-withdrawal command(s): {0}".format(kept))
            body = blocks.get(leg["member"].lower(), [])
            # Measured for a regular host Po, inferred for a vPC member: a DEPLOYED member leaves its port-channel with the
            # COMMAND form `no channel-group N force mode M`, while the device and the model hold the persisted `channel-group N mode M`.
            body, withdrawn = pvlan_po_member_force_withdrawal(body, leg["pcid"], leg["pc_mode"])
            if withdrawn:
                return "refuse", problems + ["{0}: {1}".format(leg["member"], f) for f in withdrawn]
            decision, found = pvlan_assess_target(
                body, entry, leg["member"], pvlan_render(*leg["post_member"]),
                pvlan_transition_vocabulary(leg["pre_member"], leg["post_member"]), release=True)
            problems.extend("{0}: {1}".format(leg["member"], f) for f in found)
            return ("refuse", problems) if problems or decision == "refuse" else ("deploy", [])
        if which == "pre":
            parts = [(leg["po_name"], leg["pre_po"], leg["pre_po"], False), (leg["member"], leg["pre_member"], leg["pre_member"], False)]
        else:
            parts = [(leg["po_name"], leg["pre_po"], leg["post_po"], leg["pre_po"][0] is None),
                     (leg["member"], leg["pre_member"], leg["post_member"], False)]
        decisions, problems = [], []
        # The member joins through `channel-group N force mode M` (MEASURED for a regular host Po; INFERRED for a vPC
        # member) and an EXISTING member inherits its child Po's PVLAN changes on the device without a member pending (MEASURED
        # for a regular Po; INFERRED for a vPC member). Both apply only to the member part of the SAME peer's preview.
        member_force = None
        member_inherit = None
        member_reassert = None
        mtu_ctx = None
        if which == "post":
            # The submode of the member is its child Po's (the parent's) mode; a member PREPARED as access/routed (trunk secondary
            # only, admitted by the baseline check) joins through the same force with its measured baseline specifics.
            if leg.get("joining") and leg["pre_member"][0] in (PVLAN_TRUNK_HOST_POLICY,) + tuple(sorted(PVLAN_PO_PREPARED_BASELINES)):
                member_force = {"po_number": leg["pcid"], "pc_mode": leg["pc_mode"], "mode": leg["post_po"][1].get("PVLAN_MODE", "host"),
                                "baseline": leg["pre_member"][0]}
            elif not leg.get("joining") and leg["pre_member"][0] == PO_MEMBER_POLICY:
                # Measured on a vPC: an EXISTING member of THIS leg may be
                # re-emitted with `channel-group <pcid> force mode <pc_mode>`; po_member_force_reassertion() decides with THIS leg's pcid/mode.
                member_reassert = {"po_number": leg["pcid"], "pc_mode": leg["pc_mode"]}
                if blocks.get(leg["po_name"].lower()):
                    member_inherit = leg["po_name"]
        for pname, pre, post, absent_ok in parts:
            is_member = pname == leg["member"]
            decision, found = pvlan_assess_target(
                blocks.get(pname.lower(), []), entry, pname, pvlan_render(*post), pvlan_transition_vocabulary(pre, post), absent_ok=absent_ok,
                member_force=member_force if is_member else None, member_inherit=member_inherit if is_member else None,
                member_reassert=member_reassert if is_member else None, member_mtu_inherit=mtu_ctx if is_member else None,
                # SP1 (DIAG-measured on both peers): the member's `speed 1000` carried by THIS leg's child Po (same serial, same preview)
                member_speed_inherit=mtu_ctx if is_member else None)
            if not is_member and member_reassert is not None:
                # Measured on a vPC: the member's MTU line
                # may be carried by THIS leg's child Po
                # (same peer, same preview entry), judged first (parts[0]); the other peer never supplies the proof.
                mtu_ctx = dict(member_reassert, parent=leg["po_name"], parent_desired=pvlan_render(*post),
                               parent_vocabulary=pvlan_transition_vocabulary(pre, post), parent_body=blocks.get(pname.lower(), []),
                               parent_ok=decision == "deploy" and not found)
            decisions.append(decision)
            problems.extend("{0}: {1}".format(pname, f) for f in found)
        if "refuse" in decisions:
            return "refuse", problems
        return ("converged", []) if all(d == "converged" for d in decisions) else ("deploy", [])

    def dcnm_intf_pvlan_vpc_batch_scope(self, target, items, which):
        """VPC-BATCH-GATE: ({serial: interface names}, {serial: withdrawn lines}) owned on each PHYSICAL serial by the OTHER PVLAN vPCs
        that are items of this same deploy batch (`items`, matched by pair serial + vPC name against this run's targets). A target that is
        registered but not in the batch contributes nothing; names are scoped per serial, never merged across switches. The legs a vPC
        removes count only in the pre / post gates (they are part of that update); a deleted vPC contributes its children, members and
        `no interface <child>` only in the delete gate. Membership only stops the pending from being called foreign: each of those
        vPCs is still judged by its own gate call."""
        names, withdrawn = {}, {}
        targets = self.dcnm_intf_pvlan_target_map()
        own = (target["sno"], target["name"].lower())
        seen = set()
        for it in items or []:
            key = (it.get("serialNumber"), str(it.get("ifName", "")).lower())
            other = targets.get(key)
            if key == own or key in seen or not other or other.get("kind") != "vpc":
                continue
            seen.add(key)
            if bool(other.get("deletes")) != (which == "delete"):
                continue
            legs = list(self.dcnm_intf_pvlan_vpc_legs(other))
            if which in ("pre", "post"):
                legs += list(other.get("removed_legs") or [])
            for leg in legs:
                names.setdefault(leg["serial"], set()).update((leg["po_name"].lower(), leg["member"].lower()))
                if which == "delete":
                    withdrawn.setdefault(leg["serial"], set()).add("no interface " + leg["po_name"].lower())
        return names, withdrawn

    def dcnm_intf_pvlan_vpc_gate(self, target, items, site, which, after_deploy=False):
        """(decision, problems) for ONE vPC: one fresh forced preview PER PEER (each judged against ITS serial's models, both always
        evaluated), then ONE combined decision (vpc_combine). `which`: "pre" (the current state, no write yet), "post" (the intent just
        written/updated) or "delete". A leg that is fine never makes the vPC fine. `after_deploy`: this vPC's deploy was already sent and
        accepted in this invocation (check_deploy_resend): a peer it applied may be converged (vpc_combine)."""
        legs = self.dcnm_intf_pvlan_vpc_legs(target)
        previews = {}
        if which in ("pre", "post") and not target.get("deletes") and not target.get("creates") and not target.get("resumes"):
            # A saved member removal this request repeats with deploy true (recognised from the controller's state only)
            self.dcnm_intf_pvlan_vpc_resume_removed(target, legs, previews)
        # MM-B: the members an update removes are judged too: as existing legs in the prior gate, as releases in the post gate.
        removed = list(target.get("removed_legs") or []) if which in ("pre", "post") else []
        resumed = [r for r in removed if r.get("resumed")]
        legs = legs + removed
        batch = {}
        for it in items or []:
            batch.setdefault(it.get("serialNumber"), set()).add(str(it.get("ifName", "")).lower())
        # VPC-BATCH-GATE: the other vPCs that are really in THIS batch own their children / members / withdrawn port-channels on each
        # physical serial; their pending is theirs, not foreign. Each of them is still judged by its own gate call.
        peer_names, peer_withdrawn = self.dcnm_intf_pvlan_vpc_batch_scope(target, items, which)
        problems, decisions = [], []
        for leg in legs:
            sno = leg["serial"]
            if sno not in previews:
                previews[sno] = dcnm_send(self.module, "GET", self.paths["PVLAN_CONFIG_PREVIEW"].format(self.fabric, sno))
            resp = previews[sno]
            record = {"site": site, "serial": sno, "peer": leg["index"] + 1, "vpc": target["name"], "targets": {}}
            try:
                entry = pvlan_preview_entry(resp, sno)
                blocks, global_lines = pvlan_split_blocks(entry["pendingConfig"])
                record["status"] = entry["status"]
                withdrawn = set(["no interface " + leg["po_name"].lower()]) if which == "delete" else set()
                withdrawn |= peer_withdrawn.get(sno, set())
                # The exact withdrawal of a conventional aggregate this invocation's confirmed mark-delete deleted on this serial
                invocation_withdrawn = pvlan_invocation_withdrawals(self, sno, global_lines)
                if [line for line in global_lines if line.lower() not in withdrawn and line.strip().lower() not in invocation_withdrawn]:
                    problems.append("peer {0} ({1}): pending carries commands outside interface scope".format(leg["index"] + 1, sno))
                allowed = set(batch.get(sno, set())) | set(
                    name.lower() for peer_leg in legs if peer_leg["serial"] == sno
                    for name in (peer_leg["po_name"], peer_leg["member"])) | peer_names.get(sno, set())
                outside = sorted(set(blocks) - allowed)
                # A conventional member this invocation's confirmed update released on this physical serial is not foreign
                owned = pvlan_invocation_owned(self, sno, outside, blocks)
                if owned or invocation_withdrawn:
                    record_owned = {"site": site, "serial": sno, "vpc": target["name"], "interfaces": owned}
                    if invocation_withdrawn:
                        record_owned["withdrawn"] = invocation_withdrawn
                    self.result.setdefault("pvlan_gate_invocation_releases", []).append(record_owned)
                    outside = [n for n in outside if n not in owned]
                if outside:
                    problems.append("peer {0} ({1}): pending exists for interfaces outside this deploy batch: {2}".format(
                        leg["index"] + 1, sno, ", ".join(outside)))
                if (which == "post" and any(leg is r for r in removed)) or any(leg is r for r in resumed):
                    decision, found = self.dcnm_intf_pvlan_vpc_removed_decision(leg, entry, blocks)
                else:
                    decision, found = self.dcnm_intf_pvlan_vpc_leg_decision(leg, entry, blocks, which)
            except PvlanError as exc:
                decision, found = "refuse", [str(exc)]
            record["targets"][target["name"]] = decision
            self.result.setdefault("pvlan_gate", []).append(record)
            decisions.append(decision)
            problems.extend("peer {0} ({1}): {2}".format(leg["index"] + 1, sno, f) for f in found)
        if which == "pre" and not resumed:
            mode = "repeat"
        elif target.get("deletes"):
            mode = "delete"
        elif target["creates"] or target.get("resumes"):
            mode = "create"
        else:
            mode = "update"
        expected = [("deploy" if any(leg is r for r in removed) else leg.get("expect") or "converged") for leg in legs] if mode == "update" else None
        # Judge each member before combining the two peer outcomes. Never let a
        # good last member overwrite a bad first one on the same switch.
        per_peer, per_peer_expected = [], []
        for index in (0, 1):
            positions = [i for i, leg in enumerate(legs) if leg["index"] == index]
            values = [decisions[i] for i in positions]
            if not values or "refuse" in values:
                per_peer.append("refuse")
            elif mode == "repeat" and len(set(values)) != 1:
                per_peer.append("refuse")
                problems.append("peer {0}: members have inconsistent pre-existing deployment states".format(index + 1))
            elif mode in ("create", "delete") and len(set(values)) != 1 and not (after_deploy and mode == "create"):
                per_peer.append("refuse")
            else:
                per_peer.append("deploy" if "deploy" in values else "converged")
            if expected is not None:
                if any(decisions[i] != expected[i] and not (after_deploy and expected[i] == "deploy" and decisions[i] == "converged")
                       for i in positions):
                    problems.append("peer {0}: a member does not match its expected deployment state".format(index + 1))
                per_peer_expected.append("deploy" if any(expected[i] == "deploy" for i in positions) else "converged")
        decision, found = pvlan_vpc_combine(mode, per_peer, per_peer_expected if expected is not None else None, after_deploy=after_deploy)
        problems.extend(found)
        if problems and decision != "refuse":
            decision = "refuse"
        return decision, problems

    def dcnm_intf_pvlan_vpc_create_outcome(self, payload, resp):
        """A non-200 answer to the vPC parent CREATE passes only as an "accepted" 207 (vpc_response_class); an ERROR, an alien or an
        unknown shape stays a failure and nothing is deployed. Acceptance is NOT success: both peers are still gated and read back."""
        intf = (payload.get("interfaces") or [{}])[0]
        target = self.dcnm_intf_pvlan_target_map().get((intf.get("serialNumber"), str(intf.get("ifName", "")).lower()))
        if not target or target.get("kind") != "vpc" or not isinstance(resp, dict):
            return False
        if self.dcnm_intf_collect_batch_errors(resp):
            return False
        return pvlan_vpc_response_class(resp, target["sno"], target["name"]) == "accepted"

    def dcnm_intf_pvlan_vpc_verify_rounds(self, targets):
        """VPC-READS: the reads of the post-deploy vPC verification, planned per vPC PAIR and poll round for every vPC target of the call.

        Each round, every pair that is not finished has BOTH of its peer serials read ONCE (summary, forced bulk refresh, policy list:
        dcnm_intf_pvlan_vpc_read_serial) and the legs of all its vPCs are judged on those same answers. A pair is finished only when every
        leg of every one of its vPCs is In-Sync and readable IN THE SAME ROUND; until then both serials are re-read, so a converged peer is
        re-confirmed with its peer and no snapshot of an earlier round replaces a failed or newer read. At most 6 rounds and one 5 s wait
        between rounds. After the rounds, ONE forced bulk refresh of each pair with a fully readable, In-Sync vPC supplies its parents.
        Returns {(pair serial, vpc name lower): {"observed": {(serial, member lower): (snap, states)}, "parent": detail or None}} for this
        call only, keyed by dcnm_intf_pvlan_vpc_plan_key (the same identity as pvlan_targets, so one vPC name on two pairs never shares an
        entry): nothing is kept for another phase or invocation, and nothing read before the deploy is used."""
        groups = collections.OrderedDict()
        for target in targets:
            groups.setdefault(target["sno"], [])
            if all(t["name"].lower() != target["name"].lower() for t in groups[target["sno"]]):
                groups[target["sno"]].append(target)
        plan = dict((self.dcnm_intf_pvlan_vpc_plan_key(t), {"observed": {}, "parent": None}) for tgts in groups.values() for t in tgts)
        pending = list(groups)
        for attempt in range(6):
            for pair in list(pending):
                by_serial = collections.OrderedDict()
                for target in groups[pair]:
                    for leg in self.dcnm_intf_pvlan_vpc_legs(target):
                        by_serial.setdefault(leg["serial"], []).append((target["name"], leg["po_name"], leg["member"]))
                snaps = {}
                for serial, legs in by_serial.items():
                    for key, snap in self.dcnm_intf_pvlan_vpc_read_serial(serial, legs).items():
                        snaps[(serial,) + key] = snap
                finished = True
                for target in groups[pair]:
                    observed = {}
                    for leg in self.dcnm_intf_pvlan_vpc_legs(target):
                        snap = snaps[(leg["serial"], target["name"].lower(), leg["po_name"].lower(), leg["member"].lower())]
                        states = []
                        for label, key in (("child", "po"), ("member", "member")):
                            entries = snap["summary"][key]
                            states.append((label, entries[0].get("complianceStatus") if len(entries) == 1 else None))
                        observed[(leg["serial"], leg["member"].lower())] = (snap, states)
                    plan[self.dcnm_intf_pvlan_vpc_plan_key(target)]["observed"] = observed
                    finished = finished and self.dcnm_intf_pvlan_vpc_observed_ok(observed)
                if finished:
                    pending.remove(pair)
            if not pending:
                break
            if attempt < 5:
                time.sleep(5)
        for pair, tgts in groups.items():
            ready = [t for t in tgts if self.dcnm_intf_pvlan_vpc_observed_ok(plan[self.dcnm_intf_pvlan_vpc_plan_key(t)]["observed"])]
            if not ready:
                continue
            self.dcnm_intf_bulk_fetch_intf_info(pair, refresh=True)
            for target in ready:
                plan[self.dcnm_intf_pvlan_vpc_plan_key(target)]["parent"] = self.dcnm_intf_get_intf_info(target["name"], pair, "INTERFACE_VPC")
        return plan

    def dcnm_intf_pvlan_vpc_result_keys(self, targets):
        """RESULT-IDENTITY: the key of each vPC in the `pvlan_verification` result, decided from the targets of the invocation (no read).
        A name that is unique among the targets keeps the plain key `<name>` and the existing entry format. The same name (case-insensitive)
        on two pairs would overwrite one entry with the other, so EVERY entry of that name gets the composite key `<name>@<pair>`, with
        `vpc` and `pair` inside the entry; `<pair>` is the two peer serials in alphabetical order, so it is the same whatever the order the
        peers were written in or the controller lists them. No plain `<name>` entry is kept for a repeated name.
        Returns {plan key: (result key, extra entry fields)}."""
        by_name = collections.Counter(t["name"].lower() for t in targets)
        out = {}
        for target in targets:
            if by_name[target["name"].lower()] == 1:
                out[self.dcnm_intf_pvlan_vpc_plan_key(target)] = (target["name"], {})
                continue
            parts = self._dcnm_intf_serial_parts(target["sno"]) or (target["sno"],)
            pair = "~".join(sorted(parts, key=lambda x: str(x).casefold()))
            out[self.dcnm_intf_pvlan_vpc_plan_key(target)] = ("{0}@{1}".format(target["name"], pair), {"vpc": target["name"], "pair": pair})
        return out

    @staticmethod
    def dcnm_intf_pvlan_vpc_plan_key(target):
        """Identity of a vPC in the post-deploy plan: its pair serial as registered (the controller's vpc_pair_sn order, never re-sorted)
        and its name, lower-cased, exactly as the key of pvlan_targets."""
        return (target["sno"], target["name"].lower())

    @staticmethod
    def dcnm_intf_pvlan_vpc_observed_ok(observed):
        return bool(observed) and all(status == "In-Sync" for _s, states in observed.values() for _l, status in states) and not any(
            s["problems"] for s, _x in observed.values())

    def dcnm_intf_pvlan_vpc_verify(self, target):
        """Bounded, non-mutating readback of a deployed vPC, PER PEER: compliance In-Sync of the child Po and the member, then the
        intent of the parent, of each child Po and of each member. Any difference on any peer fails the run with a per-peer table.
        VPC-READS: the snapshots come from ONE plan (dcnm_intf_pvlan_vpc_verify_rounds) over every vPC of the current
        dcnm_intf_pvlan_verify_after_deploy call, made when its first vPC is verified and kept only for that call; a vPC verified outside
        such a call is planned alone. The judgement and its messages are unchanged."""
        name, sno, legs = target["name"], target["sno"], self.dcnm_intf_pvlan_vpc_legs(target)
        call = getattr(self, "_pvlan_vpc_call", None)
        if call is not None and any(t is target for t in call["targets"]):
            if call["plan"] is None:
                call["plan"] = self.dcnm_intf_pvlan_vpc_verify_rounds(call["targets"])
            plan = call["plan"]
        else:
            plan = self.dcnm_intf_pvlan_vpc_verify_rounds([target])
        observed = plan[self.dcnm_intf_pvlan_vpc_plan_key(target)]["observed"]
        table = []
        for leg in legs:
            snap, states = observed[(leg["serial"], leg["member"].lower())]
            table.extend("peer {0} ({1}): {2}".format(leg["index"] + 1, leg["serial"], p) for p in snap["problems"])
            table.extend("peer {0} ({1}): {2} is {3}, not In-Sync".format(leg["index"] + 1, leg["serial"], label, status)
                         for label, status in states if status != "In-Sync")
        if table:
            self.module.fail_json(
                msg="vPC {0} was deployed but not every peer reached In-Sync or could be read back: {1}. No further deployment was sent.".format(
                    name, "; ".join(table)), **self.result)
        detail = plan[self.dcnm_intf_pvlan_vpc_plan_key(target)]["parent"]
        post_nv = target["post"][1]
        mismatch = []
        if not isinstance(detail, dict) or detail.get("policy") != VPC_HOST_POLICY:
            # the parent has no peer: its differences name the PAIR (one vPC name may exist on two pairs)
            mismatch.append("the parent on {0} no longer holds {1}".format(sno, VPC_HOST_POLICY))
        else:
            have_nv = self.dcnm_intf_pvlan_vpc_nv(detail) or {}
            try:
                for key in ("PVLAN_MODE", "PC_MODE", "ADMIN_STATE", "PEER1_PO_DESC", "PEER2_PO_DESC", "PEER1_PCID", "PEER2_PCID",
                            "PEER1_MEMBER_INTERFACES", "PEER2_MEMBER_INTERFACES", "ASSOCIATION_LIST", "MAPPING_LIST",
                            "PEER1_PVLAN_NATIVE_VLAN", "PEER2_PVLAN_NATIVE_VLAN", "PEER1_PVLAN_ALLOWED_VLANS", "PEER2_PVLAN_ALLOWED_VLANS"):
                    if not pvlan_vpc_same(key, have_nv.get(key, ""), post_nv.get(key, "")):
                        mismatch.append("parent {0} on {1}".format(key, sno))
                # DUPLEX: the shared duplex of the parent is read back too (an absent key is the template's `auto`; a null is a mismatch).
                if not pvlan_vpc_same("PORT_DUPLEX_MODE", have_nv.get("PORT_DUPLEX_MODE", "auto"), post_nv.get("PORT_DUPLEX_MODE", "auto")):
                    mismatch.append("parent PORT_DUPLEX_MODE on {0}".format(sno))
            except PvlanError as exc:
                mismatch.append(str(exc))
        for leg in legs:
            snap, _states = observed[(leg["serial"], leg["member"].lower())]
            expected = pvlan_vpc_leg_po_nv(post_nv, leg["index"], name)
            mismatch.extend("peer {0} ({1}): {2}".format(leg["index"] + 1, leg["serial"], p) for p in
                            self.dcnm_intf_pvlan_vpc_present_problems(snap, name, leg["po_name"], leg["member"], expected, leg["post_member"][1]))
        if mismatch:
            self.module.fail_json(
                msg="vPC {0} was deployed and In-Sync but the post-deploy intent readback differs: {1}.".format(name, "; ".join(mismatch)),
                **self.result)
        if target.get("removed_legs"):
            self.dcnm_intf_pvlan_vpc_verify_removed(target)

    def dcnm_intf_pvlan_vpc_register_deletes(self):
        """Deletion of an EXISTING PVLAN vPC named in a `deleted` invocation, through the generic vPC path
        (interface/markdelete + globalInterface/deploy). Registered only when EVERY precondition holds, decided from the CURRENT state
        of BOTH peers (no history from the run that created it, no hidden file): otherwise the deletion is refused before any write:
          * the parent is a direct int_vpc_pvlan_host, mode host, PCID = vPC id on both peers, no stored PEERn_PO_CONF;
          * each peer holds its child Po and one or more members, each of which holds int_port_channel_pvlan_member of THAT Po and is shut;
          * deploy is requested, not check mode, and the fabric releases host interfaces administratively down.
        The release is verified against the explicit contract (a direct int_trunk_host, shut, no CONF, the documented model), never
        against a configuration this run did not read. The mark-delete releases each member ADMIN_STATE "true" (measured), so the
        module writes ONE legacy modify per member with only ADMIN_STATE "false" BEFORE the deploy (dcnm_intf_pvlan_vpc_release_members).
        Also the vPCs an `overridden` sweep queued for deletion (identity = pair serial + name, as in a named deletion)."""
        if self.module.params.get("state") not in ("deleted", "overridden"):
            return
        deploys = set((d.get("serialNumber"), str(d.get("ifName", "")).lower()) for g in self.diff_delete_deploy for d in (g or []))
        for group in self.diff_delete:
            for delem in group or []:
                name, sno = delem.get("ifName", ""), delem.get("serialNumber", "")
                key = (sno, str(name).lower())
                if not VPC_NAME.match(str(name)) or "~" not in str(sno) or key in self.pvlan_targets:
                    continue
                detail = self.dcnm_intf_get_intf_info(name, sno, "INTERFACE_VPC")
                if not isinstance(detail, dict) or detail.get("policy") != VPC_HOST_POLICY:
                    continue  # not a PVLAN vPC: the generic deletion is unchanged
                nv = self.dcnm_intf_pvlan_vpc_nv(detail)
                problems = list(self.dcnm_intf_pvlan_learn_pair(sno))
                if nv is None:
                    problems.append("the controller returned no nvPairs for the vPC")
                    nv = {}
                if self.module.check_mode:
                    problems.append("deleting a PVLAN vPC is refused in check mode: the pre-deploy gate needs the deletion to exist")
                # Deploy false SAVES the deletion (mark-delete, both peers' members released and corrected, pending validated).
                deferred = self.delete_requested_deploy.get(key) is False
                if key not in deploys and not deferred:
                    problems.append("deleting a PVLAN vPC without deploy is not implemented: the release of its members could not be validated")
                if self.dcnm_intf_pvlan_release_admin_problem():
                    problems.append(self.dcnm_intf_pvlan_release_admin_problem())
                if not self.module.check_mode and not self.has_bulk_api:
                    problems.append("the controller's bulk interface update API is not available: a released member's administrative state "
                                    "could not be corrected before the deploy")
                if nv.get("PVLAN_MODE") not in PVLAN_MODES:
                    problems.append("the vPC is not in a known pvlan_mode (found {0!r})".format(nv.get("PVLAN_MODE")))
                serials = str(sno).split("~")
                legs = []
                for n in (1, 2):
                    names, unresolved = pvlan_normalize_member_list(nv.get("PEER%d_MEMBER_INTERFACES" % n))
                    if unresolved or not names:
                        problems.append("peer {0} needs a readable, non-empty list of explicit physical members".format(n))
                        continue
                    pcid = str(nv.get("PEER%d_PCID" % n, "")).strip()
                    if not re.match(r"^[1-9][0-9]{0,3}$", pcid) or int(pcid) > 4096:
                        problems.append("PEER{0}_PCID {1!r} of the vPC is not a readable port-channel number".format(n, nv.get("PEER%d_PCID" % n)))
                        continue
                    if str(nv.get("PEER%d_PO_CONF" % n, "") or "").strip():
                        problems.append("the vPC stores freeform commands on peer {0} (PEER{0}_PO_CONF); the template would run its freeform "
                                        "delete check, which is not implemented".format(n))
                        continue
                    for member in sorted(names):
                        legs.append({"serial": serials[n - 1], "index": n - 1,
                                     "member": self.dcnm_intf_pvlan_po_member_ifname(member, serials[n - 1]),
                                     "po_name": pvlan_vpc_po_name(pcid), "pcid": pcid, "pc_mode": str(nv.get("PC_MODE", "active"))})
                if problems or set(leg["index"] for leg in legs) != {0, 1}:
                    for reason in problems:
                        self.dcnm_intf_pvlan_block(name, sno, reason)
                    continue
                snaps = [self.dcnm_intf_pvlan_vpc_read_leg(leg["serial"], name, leg["po_name"], leg["member"]) for leg in legs]
                problems += self.dcnm_intf_pvlan_vpc_parent_problems(name, snaps, detail.get("policy"), nv)
                for leg, snap in zip(legs, snaps):
                    expected = pvlan_vpc_leg_po_nv(nv, leg["index"], name)
                    expected_member = pvlan_vpc_leg_models(nv, leg["index"], name, self.dcnm_intf_pvlan_vpc_nv(snap["member"]), True)[1][1]
                    reasons = self.dcnm_intf_pvlan_vpc_present_problems(snap, name, leg["po_name"], leg["member"], expected, expected_member)
                    problems += ["peer {0} ({1}): {2}".format(leg["index"] + 1, leg["serial"], r) for r in reasons]
                    if not reasons:
                        mnv = self.dcnm_intf_pvlan_vpc_nv(snap["member"])
                        if str((mnv or {}).get("ADMIN_STATE", "")).strip().lower() not in ("true", "false"):
                            problems.append("peer {0} ({1}): member {2} has an unknown administrative state ({3!r})".format(
                                leg["index"] + 1, leg["serial"], leg["member"], (mnv or {}).get("ADMIN_STATE")))
                        else:
                            leg["pre_member"] = (PO_MEMBER_POLICY, copy.deepcopy(mnv))
                            leg["post_member"] = (PVLAN_TRUNK_HOST_POLICY, self.dcnm_intf_pvlan_released_model())
                if problems:
                    for reason in problems:
                        self.dcnm_intf_pvlan_block(name, sno, reason)
                    continue
                self.pvlan_targets[key] = {
                    "name": name, "sno": sno, "kind": "vpc", "deletes": True, "creates": False, "update": False, "deferred": deferred,
                    "pre": (VPC_HOST_POLICY, copy.deepcopy(nv)), "post": (None, None), "new_secondaries": [], "members": [], "legs": legs,
                    # The controller's own spelling of the vPC on the mark-delete wire and the identities frozen before the first write.
                    "wire_name": self.dcnm_intf_pvlan_detail_ifname(detail, name),
                    "frozen": {"parent": name, "serial": sno, "legs": [(leg["serial"], leg["member"]) for leg in legs]},
                }
                self.dcnm_intf_pvlan_drop_generic_member_resets(set((leg["serial"], leg["member"].lower()) for leg in legs))

    # ================================================================ deletion = confirmed mark-delete + released members
    # The regular-Po steps (ONE confirmed mark-delete, then the released member kept administratively DOWN before any deploy) are
    # mirrored for a vPC, per peer. Each extrapolation is an INFERENCE pending a live case: the vPC mark-delete answer, the "marked for deletion"
    # listing of the children, and that the controller releases a vPC member the way it releases a regular-Po member (int_trunk_host with
    # ADMIN_STATE "true"). An unknown outcome stops the run BEFORE any deploy with the writes confirmed and the writes unverified, per peer.
    def dcnm_intf_pvlan_vpc_release_fail(self, target, phase, problems, confirmed, uncertain=None, peer=None, per_serial=None, context=None):
        """`per_serial` = {serial: member write state} -- "confirmed" (per-item SUCCESS), "uncertain" (outcome not verified),
        "pending" (not sent), "not needed" (already down). The two member writes are NOT atomic, and the mark-delete may already have changed
        the controller's intent, so a failure never claims "zero writes"."""
        uncertain = uncertain or []
        self.result.setdefault("pvlan_vpc_release", []).append(
            {"vpc": target["name"], "serial": target["sno"], "phase": phase, "peer": peer, "problems": problems,
             "confirmed_writes": confirmed, "uncertain_writes": uncertain, "member_writes": dict(per_serial or {})})
        self.module.fail_json(
            msg="PVLAN vPC {0} on {1}: member release failed {2}{3}: {4}. Confirmed writes: {5}. Writes with an UNVERIFIED outcome: {6}. "
            "Member writes per serial: {7}. "
            "No deployment request was sent: the controller keeps the pending {8}. "
            "Nothing is retried or rolled back on any peer; recovery is a human decision after reading BOTH peers.".format(
                target["name"], target["sno"], phase, "" if peer is None else " (peer {0})".format(peer), "; ".join(problems),
                ", ".join(confirmed) or "none", ", ".join(uncertain) or "none",
                ", ".join("{0}={1}".format(k, v) for k, v in (per_serial or {}).items()) or "none",
                "membership update of the vPC (the removed member is not deployed)" if context == "update"
                else "deletion of the vPC and of the members already released"),
            **self.result)

    def dcnm_intf_pvlan_vpc_markdeletes(self):
        """ONE mark-delete per registered vPC, taken out of the generic batch, ONE attempt, confirmed only by an answer of the MEASURED shape of a
        regular port-channel (200/OK, 'Interface deleted successfully', exactly one `value` item naming serial and interface) with the PAIR
        identity -- INFERRED for a vPC. Any other answer or a transport error is an UNVERIFIED outcome: no retry, no member write, no deploy.
        Returns True when at least one deletion was confirmed (the member release must follow)."""
        targets = dict(((t["sno"], t["name"].lower()), t) for t in self.dcnm_intf_pvlan_target_map().values()
                       if t.get("deletes") and t.get("kind") == "vpc" and not t.get("resumes_delete"))
        if not targets:
            # A resumed (saved) vPC deletion was marked by an earlier process; its release is proven again.
            return any(t.get("resumes_delete") and t.get("kind") == "vpc" for t in self.dcnm_intf_pvlan_target_map().values())
        found = {}
        for index, group in enumerate(self.diff_delete):
            keep = []
            for delem in group or []:
                key = (delem.get("serialNumber"), str(delem.get("ifName", "")).lower())
                if key in targets:
                    found.setdefault(key, delem)
                else:
                    keep.append(delem)
            self.diff_delete[index] = keep
        missing = sorted("{0} on {1}".format(n, s_) for (s_, n) in targets if (s_, n) not in found)
        if missing:
            self.module.fail_json(msg="Native PVLAN vPC deletion is inconsistent: registered vPC(s) {0} are not in the delete batch. No request "
                                  "was sent.".format(", ".join(missing)), **self.result)
        for key, target in targets.items():
            body = dict(found[key], ifName=target.get("wire_name") or found[key].get("ifName"))
            try:
                resp = dcnm_send(self.module, "DELETE", self.paths["IF_MARK_DELETE"], json.dumps([body]))
                problems = pvlan_po_markdelete_outcome_problems(resp, target["sno"], target["name"])
            except AnsibleConnectionError as exc:
                resp = {"transport_error": str(exc)}
                problems = ["the mark-delete request raised a transport error: {0}".format(exc)]
            self.result["response"].append(resp)
            if problems:
                self.dcnm_intf_pvlan_vpc_release_fail(
                    target, "at the mark-delete (outcome UNVERIFIED; not retried)", problems, [],
                    uncertain=["mark-delete of {0} (it may or may not have been applied on one or both peers; the members may already be "
                               "released by the controller)".format(target["name"])])
            target["markdelete"] = "confirmed"
        return True

    def dcnm_intf_pvlan_vpc_released_member(self, target, leg, normalized=False):
        """(problems, policy, nvPairs) of ONE peer's released member from FRESH reads: the child port-channel is absent -- or listed ONLY in the
        controller's "marked for deletion" form awaiting the deploy (po_marked_deleted_problem; MEASURED for a deployed regular Po and
        for the child of a vPC, whose `interface_delete` policy is owned by the vPC itself) --,
        no live policy names the child port-channel or the vPC (entity or source), and the member is a
        standalone physical Ethernet with exactly one live direct released-member policy -- int_trunk_host or (inferred for the
        vPC child) int_routed_host (dcnm_intf_pvlan_released_member_detail; summary, detail and policy list agree)."""
        sno, po, member, vpc = leg["serial"], leg["po_name"], leg["member"], target["name"]
        self.dcnm_intf_invalidate_serial_authority(sno)
        self.pvlan_policies.pop(sno, None)
        if not self.dcnm_intf_get_have_all_with_sno(sno):
            return ["the interface summary could not be read authoritatively"], None, None
        authority = self._dcnm_intf_authority_key(sno)
        listed = [h for h in self.have_all if str(h.get("ifName", "")).lower() == po.lower()
                  and self._dcnm_intf_authority_key(h.get("serialNo", "")) == authority]
        if len(listed) > 1:
            return ["the child port-channel is still listed {0} times".format(len(listed))], None, None
        if listed:
            # The policy of a vPC child is owned by the vPC itself
            marked = pvlan_po_marked_deleted_problem(listed[0], po, parent=vpc)
            if marked:
                return ["the child port-channel is still listed: {0}".format(marked)], None, None
        policies = self.dcnm_intf_pvlan_read_policies(sno)
        if policies is None:
            return ["the switch policy list could not be read authoritatively"], None, None
        claims = sorted("{0}/{1}/{2}".format(p.get("entityName"), p.get("templateName"), p.get("source")) for p in policies
                        if p.get("deleted") is not True and str(p.get("deleted", "")).lower() != "true"
                        and (str(p.get("entityName", "")).lower() in (po.lower(), vpc.lower())
                             or str(p.get("source", "")).lower() in (po.lower(), vpc.lower())))
        if claims:
            return ["live policies still reference the vPC or its child port-channel: {0}".format(claims)], None, None
        return self.dcnm_intf_pvlan_released_member_detail(member, sno, normalized)

    def dcnm_intf_pvlan_vpc_release_removed(self):
        """MM-B: after the CONFIRMED modify of an existing vPC that removed members (one peer or both), and BEFORE any deploy, each removed
        member is released through the shared release sequence (dcnm_intf_pvlan_po_normalize_releases) on ITS serial: proven afresh (no live
        policy of the vPC claims it and it holds a sole direct int_trunk_host or int_routed_host), set down on its own policy when needed, read
        back, modeled. INFERRED: that a member removed by a vPC modify is released like a deleted vPC's member."""
        for target in [t for t in self.dcnm_intf_pvlan_target_map().values() if t.get("kind") == "vpc" and t.get("removed_legs")]:
            targets = [{"name": target["name"], "sno": r["serial"], "frozen": {"member": r["member"], "member_policy_id": r.get("policy_id")},
                        "members": [r], "release_context": "update", "vpc_target": target, "peer": r["index"] + 1}
                       for r in target["removed_legs"] if not r.get("resumed")]  # A resumed leg was released by the saving run
            if not targets:
                continue

            def fail(t, phase, problems, confirmed, uncertain=None, admin_state=None):
                self.dcnm_intf_pvlan_vpc_release_fail(t["vpc_target"], "{0} (removed member {1})".format(phase, t["frozen"]["member"]), problems,
                                                      confirmed, uncertain, peer=t["peer"], context="update")
            self.dcnm_intf_pvlan_po_normalize_releases(targets, self.dcnm_intf_pvlan_vpc_removed_member,
                                                       "membership update of {0} (per-item SUCCESS)", fail=fail, record_key="pvlan_vpc_release")

    def dcnm_intf_pvlan_vpc_removed_member(self, target, normalized=False):
        """MM-B: (problems, policy, nvPairs) of a member REMOVED from one peer of a vPC, from FRESH reads of that peer: no live policy of the
        member is the vPC's (its member policy or a child whose source is the vPC), and it is a released member."""
        sno, vpc, member = target["sno"], target["name"], target["frozen"]["member"]
        self.dcnm_intf_invalidate_serial_authority(sno)
        self.pvlan_policies.pop(sno, None)
        if not self.dcnm_intf_get_have_all_with_sno(sno):
            return ["the interface summary could not be read authoritatively"], None, None
        policies = self.dcnm_intf_pvlan_read_policies(sno)
        if policies is None:
            return ["the switch policy list could not be read authoritatively"], None, None
        claims = sorted("{0}/{1}".format(p.get("templateName"), p.get("source")) for p in self.dcnm_intf_pvlan_vpc_live(policies, entity=member)
                        if p.get("templateName") == PO_MEMBER_POLICY or str(p.get("source", "")).lower() == vpc.lower())
        if claims:
            return ["the removed member is still claimed by the vPC: {0}".format(claims)], None, None
        return self.dcnm_intf_pvlan_released_member_detail(member, sno, normalized)

    def dcnm_intf_pvlan_vpc_release_members(self):
        """After the confirmed mark-delete and BEFORE any deploy, in three phases, per peer in the controller's pair order:
          A. prove BOTH released members afresh (ownership, state) and validate BOTH: the proposed ADMIN_STATE "false" payload of a member
             still up, the fresh writable nvPairs of a member already down -- no member write yet; a problem on any peer stops the
             run with every member write still pending;
          B. for each member whose ADMIN_STATE is not already "false" (MEASURED for a regular Po and for a vPC member), ONE legacy
             interface/modify with its complete writable nvPairs and only ADMIN_STATE "false", sequentially: per-item SUCCESS naming the
             member and no ERROR, then its readback (every other writable value unchanged). The two writes are NOT atomic: a failure after a
             confirmed first write stops with the state of each serial (confirmed / uncertain / pending);
          C. the FRESH release of EACH member (its readback, or its proof read when no write was needed) must be a safe standalone port; it
             becomes that leg's post_member for the pre-deploy gate (verify_deleted uses only its policy, against the summary after the
             deploy; this phase is the last judgement of the released member's intent and contract), and its distance to the template model is recorded as
             `restoration_delta` (jumbo is never imposed; restoring the baseline is a separate operation).
        Any problem stops the run before the deploy. This is NOT a repair of a partial state."""
        for target in [t for t in self.dcnm_intf_pvlan_target_map().values() if t.get("deletes") and t.get("kind") == "vpc"]:
            completed = ["mark-delete of {0} ({1})".format(
                target["name"], "saved by an earlier run, read from the controller" if target.get("resumes_delete") else "confirmed by its answer")]
            legs = target["legs"]
            write_keys = {(leg["serial"], leg["member"]):
                          (leg["serial"] if sum(l["serial"] == leg["serial"] for l in legs) == 1
                           else leg["serial"] + ":" + leg["member"]) for leg in legs}
            writes = dict((key, "pending") for key in write_keys.values())
            # Each released member reaches the fabric's host default (HOST_INTF_ADMIN_STATE), as the generic host reset does.
            admin = self.dcnm_intf_pvlan_release_admin()
            plan = []
            for leg in legs:  # phase A
                peer, sno, member = leg["index"] + 1, leg["serial"], leg["member"]
                problems, policy, nv = self.dcnm_intf_pvlan_vpc_released_member(target, leg)
                payload = None
                if not problems and admin is None:
                    problems = [self.dcnm_intf_pvlan_release_admin_problem()]
                if not problems and str(nv.get("ADMIN_STATE", "")).strip().lower() != admin:
                    payload = pvlan_released_member_payload(policy, nv, member, sno, self.fabric, admin)
                    problems = ["the member payload would not be a safe standalone port: {0}".format(p)
                                for p in pvlan_released_member_safety_problems(policy, payload["interfaces"][0]["nvPairs"], admin)]
                elif not problems:
                    # A member released already at the targeted state is judged here too (its fresh writable nvPairs), so an
                    # unsafe peer stops the run BEFORE any member write on either peer; nothing of its intent is rewritten.
                    fresh = dict((k, v) for k, v in nv.items() if k not in PVLAN_PO_RELEASE_METADATA)
                    problems = ["the released member (already {0}) is not a safe standalone port: {1}".format(
                        self.dcnm_intf_pvlan_admin_words(admin), p) for p in pvlan_released_member_safety_problems(policy, fresh, admin)]
                if problems:
                    self.dcnm_intf_pvlan_vpc_release_fail(target, "while proving the released member before any member write", problems,
                                                          completed, peer=peer, per_serial=writes)
                if payload is None:
                    writes[write_keys[(sno, leg["member"])]] = "not needed"
                plan.append((leg, policy, nv, payload))
            fresh = []
            for leg, policy, nv, payload in plan:  # phase B
                peer, sno, member = leg["index"] + 1, leg["serial"], leg["member"]
                if payload is None:
                    fresh.append((leg, policy, nv, "not needed (already {0})".format(self.dcnm_intf_pvlan_admin_words(admin))))
                    continue
                modify = "legacy interface/modify of {0} on peer {1} ADMIN_STATE {2}".format(member, peer, admin)
                try:
                    resp = dcnm_send(self.module, "POST", self.paths["UPDATE_INTERFACE_BULK"], json.dumps([payload]))
                except AnsibleConnectionError as exc:
                    resp = {"transport_error": str(exc)}
                self.result["response"].append(resp)
                outcome = []
                if not isinstance(resp, dict) or resp.get("RETURN_CODE") not in (200, 207):
                    outcome.append("the modify answered {0}".format(resp.get("RETURN_CODE", resp) if isinstance(resp, dict) else resp))
                else:
                    outcome += ["ERROR item: {0}".format(i.get("message")) for i in self.dcnm_intf_collect_batch_errors(resp)]
                    outcome += pvlan_modify_outcome_problems(resp, [(sno, member)])
                if outcome:
                    writes[write_keys[(sno, leg["member"])]] = "uncertain"
                    self.dcnm_intf_pvlan_vpc_release_fail(target, "at the member modify (outcome not verified)", outcome, completed,
                                                          uncertain=[modify], peer=peer, per_serial=writes)
                writes[write_keys[(sno, leg["member"])]] = "confirmed"
                completed.append(modify + " (per-item SUCCESS)")
                problems, after_policy, after = self.dcnm_intf_pvlan_vpc_released_member(target, leg, normalized=True)
                if not problems:
                    problems = pvlan_released_member_readback_problems(policy, nv, after_policy, after, admin)
                if problems:
                    self.dcnm_intf_pvlan_vpc_release_fail(target, "at the member readback", problems, completed, peer=peer, per_serial=writes)
                fresh.append((leg, after_policy, after, "ADMIN_STATE {0} -> {1}, {2} writable nvPairs preserved".format(
                    nv.get("ADMIN_STATE"), admin, len(payload["interfaces"][0]["nvPairs"]))))
            records, contract = [], []
            for (leg, policy, nv, _payload), (_leg, after_policy, after, modified) in zip(plan, fresh):  # phase C
                peer, sno = leg["index"] + 1, leg["serial"]
                released = dict((k, v) for k, v in (after or {}).items() if k not in PVLAN_PO_RELEASE_METADATA)
                problems = pvlan_released_member_safety_problems(after_policy, released, admin)
                if problems:
                    self.dcnm_intf_pvlan_vpc_release_fail(target, "the released member is not a safe standalone port", problems, completed,
                                                          peer=peer, per_serial=writes)
                # The explicit release contract of the released member (no residual PVLAN/channel-group field, a modelable member)
                # Is judged HERE on this fresh release, before the deploy, for every
                # leg (a divergence on each peer is reported together). The policy residue (a policy of the
                # vPC or its child, a second own policy) is refused by the release proof above (dcnm_intf_pvlan_vpc_released_member: claims
                # and sole direct ownership on the fresh policy list) before any member write.
                contract += ["peer {0} ({1}): member {2}: {3}".format(peer, sno, leg["member"], d) for d in pvlan_vpc_released_member_differences(
                    released, pvlan_released_member_contract(after_policy, released), after_policy)]
                leg["post_member"] = (after_policy, released)
                record = {"vpc": target["name"], "peer": peer, "serial": sno, "member": leg["member"], "released_policy": after_policy,
                          "released_admin_state": nv.get("ADMIN_STATE"), "released_policy_id": nv.get("POLICY_ID"),
                          "member_modify": modified, "member_write": writes[write_keys[(sno, leg["member"])]],
                          "readback_policy_id": (after or {}).get("POLICY_ID"),
                          "release_model": "fresh controller release, {0} ({1} writable nvPairs)".format(after_policy, len(released)),
                          "restoration_delta": pvlan_po_released_member_restoration_delta(released) if after_policy == PVLAN_TRUNK_HOST_POLICY else {}}
                record.update(self.dcnm_intf_pvlan_released_role_expectation(sno, after_policy))
                records.append(record)
            if contract:
                self.dcnm_intf_pvlan_vpc_release_fail(target, "at the release contract check, before the deploy", contract, completed,
                                                      per_serial=writes)
            self.result.setdefault("pvlan_vpc_release", []).extend(records)

    def dcnm_intf_pvlan_vpc_deleted_judge(self, target, snaps):
        """Judgement of ONE deleted vPC on the SUMMARY snapshots of one round (`snaps`: the read_serial(summary_only=True) answers of its
        pair, keyed (serial, vpc, po, member) lower). Returns (peers {key: "verified" | problems text}, problems [text], parent listing).
        What a peer's summary can assert after the deploy, and nothing else: the child port-channel and the vPC parent are no longer listed,
        each member is listed exactly once and In-Sync and, ONLY when its entry reports a readable policy (pvlan_summary_policy known), that
        policy is the released one -- an absent or unreadable optional policy field is not judged here and is never recovered with another
        read. An unreadable summary is a failure, never absence; a member missing from the summary is not In-Sync, never released.
        Pure: no read here."""
        name, legs = target["name"], self.dcnm_intf_pvlan_vpc_legs(target)
        member_keys = self.dcnm_intf_pvlan_vpc_member_keys(legs)
        peers, problems, listing = {}, [], set()
        for leg in legs:
            snap = snaps[(leg["serial"], name.lower(), leg["po_name"].lower(), leg["member"].lower())]
            leg_problems = list(snap["problems"])
            if leg_problems or not snap["summary_ok"]:
                listing.add("unreadable")
                leg_problems = leg_problems or ["the interface summary of {0} was not read".format(leg["serial"])]
            else:
                if snap["summary"]["po"]:
                    leg_problems.append("the interface summary still lists {0}".format(leg["po_name"]))
                if snap["summary"]["vpc"]:
                    listing.add("still listed")
                    leg_problems.append("the interface summary still lists {0}".format(name))
                entries = snap["summary"]["member"]
                if len(entries) != 1 or entries[0].get("complianceStatus") != "In-Sync":
                    leg_problems.append("the member {0} is not In-Sync in the interface summary".format(leg["member"]))
                if len(entries) == 1:
                    released_policy = leg["post_member"][0]
                    known, summary = pvlan_summary_policy(entries[0], leg["member"])
                    if known == PVLAN_SUMMARY_KNOWN and summary["templateName"] != released_policy:
                        leg_problems.append("the interface summary lists the member {0} with {1}, not the released {2}".format(
                            leg["member"], summary["templateName"], released_policy))
            peers[member_keys[(leg["serial"], leg["member"])]] = "verified" if not leg_problems else "; ".join(leg_problems)
            problems.extend("peer {0} ({1}): {2}".format(leg["index"] + 1, leg["serial"], p) for p in leg_problems)
        parent = "unreadable" if "unreadable" in listing else "still listed" if "still listed" in listing else "not listed"
        return peers, problems, parent

    def dcnm_intf_pvlan_vpc_member_keys(self, legs):
        return {(leg["serial"], leg["member"]):
                (leg["serial"] if sum(l["serial"] == leg["serial"] for l in legs) == 1 else leg["serial"] + ":" + leg["member"])
                for leg in legs}

    def dcnm_intf_pvlan_vpc_verify_deleted(self):
        """Bounded, non-mutating readback after the DEPLOY of the deletion of PVLAN vPCs, PER PEER, with an EXPLICIT verification state per vPC
        that starts "unverified" and becomes "verified" only when both peers' summaries, read in the same round, show the deploy applied:
        neither lists the vPC parent or its child port-channel, and every member is listed once and In-Sync on its own peer. A failed or
        intermittent read, a missing peer or an expired verification is a failure; absence is never inferred from an exception, an empty list
        or a sentinel. A clean peer does not make the vPC clean. Nothing is rewritten to make it so.

        Division of the proof: the INTENT and the policies are proven FRESH BEFORE the deploy, in the same invocation -- also when a
        new process completes a saved deletion: the confirmed mark-delete (or the controller's marked-for-deletion listing) and, per released
        member, dcnm_intf_pvlan_vpc_released_member (no live policy names the vPC or its child; the member holds a sole direct released-member
        policy) and the phase C safety contract of dcnm_intf_pvlan_vpc_release_members. AFTER the deploy only its outcome is read: ONE summary
        per peer serial and round -- 2 GETs per pair and round, whatever the number of vPCs or members -- and every vPC of the pair is judged
        on those answers (dcnm_intf_pvlan_vpc_deleted_judge). The intent and the policy list are NOT read again after the deploy, so this does
        not re-confirm them against another writer acting meanwhile. `parent` reports the parent's LISTING in both summaries ("not listed",
        "still listed", "unreadable"), not its intent.
        A pair is finished only when every one of its vPCs is clean in the SAME round; until then both summaries are read again (a vPC
        verified in an earlier round is judged again with the others). At most 6 rounds and one 5 s wait between rounds, per pair. Each vPC
        keeps its own state; every vPC that did not verify is named in the failure."""
        groups = collections.OrderedDict()
        for target in [t for t in self.dcnm_intf_pvlan_target_map().values()
                       if t.get("kind") == "vpc" and t.get("deletes") and not t.get("deferred")]:
            groups.setdefault(target["sno"], []).append(target)
        state = {}
        result_keys = self.dcnm_intf_pvlan_vpc_result_keys([t for tgts in groups.values() for t in tgts])
        for tgts in groups.values():
            for target in tgts:
                member_keys = self.dcnm_intf_pvlan_vpc_member_keys(self.dcnm_intf_pvlan_vpc_legs(target))
                verification = {"state": "unverified", "parent": "not read", "peers": dict((k, "not read") for k in member_keys.values())}
                verification.update(result_keys[self.dcnm_intf_pvlan_vpc_plan_key(target)][1])
                self.result.setdefault("pvlan_verification", {})[result_keys[self.dcnm_intf_pvlan_vpc_plan_key(target)][0]] = verification
                state[self.dcnm_intf_pvlan_vpc_plan_key(target)] = {"verification": verification, "problems": ["no verification was attempted"]}
        pending = list(groups)
        for attempt in range(6):
            for pair in list(pending):
                tgts = groups[pair]
                by_serial = collections.OrderedDict()
                for target in tgts:
                    for leg in self.dcnm_intf_pvlan_vpc_legs(target):
                        by_serial.setdefault(leg["serial"], []).append((target["name"], leg["po_name"], leg["member"]))
                snaps = {}
                for serial, legs in by_serial.items():
                    for key, snap in self.dcnm_intf_pvlan_vpc_read_serial(serial, legs, summary_only=True).items():
                        snaps[(serial,) + key] = snap
                finished = True
                for target in tgts:
                    entry = state[self.dcnm_intf_pvlan_vpc_plan_key(target)]
                    verification = entry["verification"]
                    peers, problems, verification["parent"] = self.dcnm_intf_pvlan_vpc_deleted_judge(target, snaps)
                    verification["peers"].update(peers)
                    entry["problems"] = problems
                    if not problems and verification["parent"] == "not listed" and all(v == "verified" for v in verification["peers"].values()):
                        verification["state"] = "verified"
                    else:
                        verification["state"] = "unverified"
                        finished = False
                if finished:
                    pending.remove(pair)
            if not pending:
                break
            if attempt < 5:
                time.sleep(5)
        failed = []
        for tgts in groups.values():
            for target in tgts:
                entry = state[self.dcnm_intf_pvlan_vpc_plan_key(target)]
                if entry["verification"]["state"] != "verified":
                    entry["verification"]["state"] = "failed"
                    failed.append("vPC {0} was deleted but its release could not be verified on every peer: {1}".format(
                        target["name"], "; ".join(entry["problems"]) or "verification incomplete"))
        if failed:
            self.module.fail_json(msg="{0}. Nothing else was sent; no member was rewritten.".format(". ".join(failed)), **self.result)

    PVLAN_PHYSICAL_ETHERNET_NAME = re.compile(r"^ethernet[0-9]+(/[0-9]+){1,2}$", re.IGNORECASE)

    def dcnm_intf_pvlan_pre_state(self, name, sno):
        """Current controller state of one interface: ("known", policy, nvPairs or None),
        ("absent", None, None) or ("unknown", reason, None).

        ONE resolution rule, whatever the origin of the detail (self.have, the detail cache of
        this invocation, or a new bulk read). The two legacy authorities are always combined for
        a physical Ethernet target: the detail policy and the interface summary, classified by
        pvlan_summary_policy and read at most once per switch (cached). int_pvlan_host named by
        either one makes the interface a PVLAN target or, when the other authority disagrees,
        "unknown"; the caller refuses "unknown" before any write and never reads it as "not
        PVLAN". Disagreements between two non-PVLAN policies stay outside this check.
        Not targets, without reads: a vPC/AA-FEX pair identity or a name that is not a physical
        Ethernet port. Not targets after the detail is resolved: a summary entry whose ifType/
        isPhysical is not a physical Ethernet when NO authority names int_pvlan_host (a PVLAN
        detail against such a summary is "unknown", never excluded). A consistent non-PVLAN summary stays authoritative
        when the detail is unavailable; an unreadable summary leaves a present non-PVLAN or an
        authoritatively absent detail as the only evidence. nvPairs only for int_pvlan_host."""
        if "~" in str(sno) or not self.PVLAN_PHYSICAL_ETHERNET_NAME.match(str(name)):
            # int_pvlan_host exists only on a standalone physical Ethernet port: a vPC/AA-FEX pair
            # identity, a port-channel, loopback, SVI or sub-interface is never a PVLAN target.
            return PVLAN_SUMMARY_KNOWN, None, None
        authority = self._dcnm_intf_authority_key(sno)
        cache_key = (authority, name.lower())

        def detail_now():
            """("present", entry) | ("absent", None) | ("unread", None) | ("failed", None)."""
            for h in self.have:
                intf = (h.get("interfaces") or [{}])[0]
                if str(intf.get("ifName", "")).lower() == name.lower() and intf.get("serialNumber") == sno:
                    return "present", h
            cached = self.intf_detail_cache.get(cache_key)
            if isinstance(cached, dict):
                return "present", cached
            if cache_key in self.intf_detail_authoritative_absent_keys or (
                authority in self.intf_detail_cached_snos and not self.dcnm_intf_detail_unavailable(name, sno)
            ):
                return "absent", None
            if self.dcnm_intf_detail_unavailable(name, sno):
                return "failed", None
            return "unread", None

        def known(entry):
            policy = entry.get("policy")
            nv = (entry.get("interfaces") or [{}])[0].get("nvPairs") if policy == PVLAN_POLICY else None
            return PVLAN_SUMMARY_KNOWN, policy, nv

        # ---- the detail authority already held by this invocation (no read here)
        origin, detail = detail_now()
        present_other = origin == "present" and detail.get("policy") != PVLAN_POLICY

        # ---- the summary authority, at most one read per switch and never retried after a
        # failure. A present non-PVLAN detail is always contrasted with it; an authoritatively
        # absent detail (a creation) is contrasted with it when this invocation already holds it.
        loaded = authority in self.have_all_cached_snos and authority not in self.have_all_failed_snos
        failed = authority in self.have_all_failed_snos
        if not loaded and not failed and origin in ("unread", "failed") or (present_other and not loaded and not failed):
            self.dcnm_intf_get_have_all_with_sno(sno)
            loaded = authority in self.have_all_cached_snos and authority not in self.have_all_failed_snos
            failed = not loaded
        entries = [
            h for h in self.have_all
            if str(h.get("ifName", "")).lower() == name.lower() and self._dcnm_intf_authority_key(h.get("serialNo", "")) == authority
        ] if loaded else []
        if len(entries) > 1:
            return PVLAN_SUMMARY_UNKNOWN, "the interface summary holds {0} entries for this interface".format(len(entries)), None
        state, summary, mentions_pvlan, not_physical, type_text = None, None, False, False, None
        if entries:
            entry = entries[0]
            state, summary = pvlan_summary_policy(entry, name)
            mentions_pvlan = pvlan_summary_mentions_policy(entry, PVLAN_POLICY)
            not_physical = not (entry.get("ifType") == "INTERFACE_ETHERNET" and str(entry.get("isPhysical")).lower() == "true")
            type_text = "ifType {0!r}, isPhysical {1!r}".format(entry.get("ifType"), entry.get("isPhysical"))
            # The summary's type fields no longer exclude the port HERE. They are judged
            # below, after the detail is resolved, so that they can never hide a known PVLAN detail.

        # ---- the detail, read once per switch when this invocation does not hold it yet
        if origin == "unread":
            self.dcnm_intf_bulk_fetch_intf_info(sno)
            if self.dcnm_intf_detail_unavailable(name, sno):
                origin = "failed"
            else:
                found = self.dcnm_intf_get_intf_info(name, sno, "INTERFACE_ETHERNET")
                origin, detail = ("present", found) if isinstance(found, dict) else ("absent", None)
        detail_policy = detail.get("policy") if origin == "present" else None

        # ---- one decision, the same whatever the origin of the detail
        if detail_policy == PVLAN_POLICY:
            if not_physical:
                reason = "the detail holds int_pvlan_host but the interface summary describes {0}, not a physical Ethernet".format(type_text)
                return PVLAN_SUMMARY_UNKNOWN, reason, None
            return known(detail)  # a PVLAN target: the ownership check judges the summary
        if not_physical and not mentions_pvlan:
            # int_pvlan_host exists only on a standalone physical Ethernet and no authority names it:
            # the entry's own type fields exclude the port, whatever its (possibly unreadable) policy fields.
            if state == PVLAN_SUMMARY_KNOWN:
                return PVLAN_SUMMARY_KNOWN, summary["templateName"], None
            return (PVLAN_SUMMARY_ABSENT, None, None) if state == PVLAN_SUMMARY_ABSENT else (PVLAN_SUMMARY_KNOWN, None, None)
        if mentions_pvlan:
            if origin == "failed":
                return PVLAN_SUMMARY_UNKNOWN, "the interface summary reports int_pvlan_host and the interface detail could not be read", None
            return PVLAN_SUMMARY_UNKNOWN, "the interface summary names int_pvlan_host but the detail holds {0!r}".format(detail_policy), None
        if origin == "present":
            return known(detail)
        if origin == "absent":
            if state == PVLAN_SUMMARY_UNKNOWN:
                return PVLAN_SUMMARY_UNKNOWN, "{0} and the interface detail holds no policy".format(summary), None
            if state == PVLAN_SUMMARY_KNOWN:  # two non-PVLAN readings: outside this check
                return PVLAN_SUMMARY_KNOWN, summary["templateName"], None
            # Absence demonstrated by the detail; no authority names int_pvlan_host (an unread or
            # unreadable summary names nothing).
            return PVLAN_SUMMARY_ABSENT, None, None
        if state == PVLAN_SUMMARY_KNOWN:  # detail unavailable: the consistent non-PVLAN summary stands
            return PVLAN_SUMMARY_KNOWN, summary["templateName"], None
        if not loaded:
            return PVLAN_SUMMARY_UNKNOWN, "the interface summary could not be read authoritatively and the interface detail could not be read", None
        if state is None:
            return PVLAN_SUMMARY_UNKNOWN, "the interface is not in the interface summary and the interface detail could not be read", None
        reason = summary if state == PVLAN_SUMMARY_UNKNOWN else "the interface summary reports no underlay policy"
        return PVLAN_SUMMARY_UNKNOWN, "{0} and the interface detail could not be read".format(reason), None

    def dcnm_intf_pvlan_register_other_targets(self):
        """Resets/conversions/redeploys of an interface whose CURRENT policy is int_pvlan_host,
        requested through a non-PVLAN payload (deleted, overridden, mode change, redeploy)."""
        planned = []
        for payload in self.diff_replace:
            for intf in payload.get("interfaces", []):
                planned.append((intf, payload.get("policy")))
        deploys = list(self.diff_deploy)
        for group in self.diff_delete_deploy:
            deploys.extend(group or [])
        # A reset, conversion, deletion or redeploy of an EXISTING PVLAN port-channel
        # or PVLAN member that is not this invocation's own port-channel request is not implemented.
        held = {}
        for h in self.have:
            hi = (h.get("interfaces") or [{}])[0]
            held[(hi.get("serialNumber"), str(hi.get("ifName", "")).lower())] = h.get("policy")
        touched = set()
        for entry in list(self.diff_replace) + deploys + [d for g in self.diff_delete for d in (g or [])]:
            for hi in (entry.get("interfaces") or [entry]):
                touched.add((hi.get("serialNumber"), str(hi.get("ifName", "")).lower()))
        for key in sorted(touched, key=str):
            if key in self.pvlan_targets:
                continue
            policy = held.get(key) or self.dcnm_intf_pvlan_po_summary_policy(key[1], key[0])
            if policy in (PO_HOST_POLICY, PO_MEMBER_POLICY):
                self.dcnm_intf_pvlan_block(
                    key[1], key[0],
                    "it holds {0}; a reset, conversion, deletion or redeploy of a PVLAN port-channel or its member "
                    "outside the port-channel request is not implemented".format(policy))
            elif policy in (VPC_HOST_POLICY, VPC_PO_POLICY):
                self.dcnm_intf_pvlan_block(
                    key[1], key[0],
                    "it holds {0}; a reset, conversion, deletion or redeploy of a PVLAN vPC or its child port-channel "
                    "outside the vPC request is not implemented".format(policy))
        for intf, policy in planned + [(d, None) for d in deploys]:
            name, sno = intf.get("ifName", ""), intf.get("serialNumber", "")
            key = (sno, name.lower())
            if key in self.pvlan_targets:
                continue
            state, current, current_nv = self.dcnm_intf_pvlan_pre_state(name, sno)
            if state == PVLAN_SUMMARY_UNKNOWN:
                self.dcnm_intf_pvlan_block(
                    name, sno, "its current policy is unknown ({0}), so a reset, conversion or redeploy of an "
                    "int_pvlan_host port cannot be excluded".format(current))
                continue
            if state == PVLAN_SUMMARY_ABSENT or current != PVLAN_POLICY:
                continue
            pre = (current, current_nv)
            if not isinstance(pre[1], dict):
                self.dcnm_intf_pvlan_block(name, sno, "the current int_pvlan_host state could not be read")
                continue
            owner = self.dcnm_intf_pvlan_check_ownership(name, sno, pre[0], pre[1])
            if owner:
                self.dcnm_intf_pvlan_block(name, sno, owner)
                continue
            if policy is None:
                post = (pre[0], copy.deepcopy(pre[1]))
            else:
                post = (policy, copy.deepcopy(intf.get("nvPairs") or {}))
            self.pvlan_targets[key] = {
                "name": name, "sno": sno, "pre": (pre[0], copy.deepcopy(pre[1])), "post": post,
                "new_secondaries": [], "update": policy is not None,
            }

    def dcnm_intf_pvlan_read_networks(self):
        """Legacy fabric network list, read once; None when not authoritative."""
        if self.pvlan_networks is None:
            resp = dcnm_send(self.module, "GET", self.paths["PVLAN_FABRIC_NETWORKS"].format(self.fabric))
            ok = isinstance(resp, dict) and resp.get("RETURN_CODE") == 200 and isinstance(resp.get("DATA"), list)
            self.pvlan_networks = resp["DATA"] if ok else False
        return self.pvlan_networks or None

    def dcnm_intf_pvlan_check_template(self, keys):
        """Missing template declarations for the nvPairs to be written; None if unreadable."""
        resp = dcnm_send(self.module, "GET", self.paths["PVLAN_TEMPLATE"])
        data = resp.get("DATA") if isinstance(resp, dict) and resp.get("RETURN_CODE") == 200 else None
        content = data.get("content") if isinstance(data, dict) else None
        if not isinstance(content, str) or not content:
            return None
        declared = pvlan_template_declared_names(content)
        return sorted(k for k in keys if k not in declared)

    def dcnm_intf_pvlan_preflight(self):
        """Whole-invocation PVLAN gate: runs after every diff is built and before the first
        request that could write intent or deploy, in normal and check mode alike."""
        self.dcnm_intf_pvlan_po_register_deletes()
        self.dcnm_intf_pvlan_vpc_register_deletes()
        if self.module.params.get("state") in ("deleted", "overridden"):
            self.dcnm_intf_pvlan_po_register_resumes()
            self.dcnm_intf_pvlan_vpc_register_resumes()
            # The conventional siblings this request names again with deployment, beside those PVLAN continuations
            self.dcnm_intf_pvlan_register_conventional_resumes()
        self.dcnm_intf_pvlan_register_other_targets()
        self.dcnm_intf_pvlan_vpc_resume_gates()
        if self.pvlan_targets and self.dcnm_version != 12:
            self.dcnm_intf_pvlan_block("*", "*", "native PVLAN requires NDFC 12")
        for target in self.pvlan_targets.values():
            if target.get("kind") != "po" or not (target["creates"] or target["update"]):
                continue
            if self.module.check_mode and target["creates"]:
                self.dcnm_intf_pvlan_block(
                    target["name"], target["sno"],
                    "creating a PVLAN port-channel is refused in check mode: the pre-deploy gate needs the "
                    "intent to exist, so its validation could not be shown without writing")
            for label, (policy, nv) in [(target["name"], target["post"])] + [(m["name"], m["post"]) for m in target["members"]]:
                try:
                    modeled = pvlan_render(policy, nv).modeled
                except PvlanError:
                    modeled = False
                if not modeled:
                    self.dcnm_intf_pvlan_block(
                        label, target["sno"],
                        "the intended {0} configuration is not covered by the CLI model, so its deployment "
                        "could not be validated".format(policy))
            for m in target["members"]:
                # A member PREPARED as access/routed has its own measured baseline grammar (trunk secondary only, enforced
                # by po_member_baseline_problems before this point).
                if m["pre"][0] not in PVLAN_VOCABULARY_POLICIES + PVLAN_PO_VOCABULARY_POLICIES + tuple(sorted(PVLAN_PO_PREPARED_BASELINES)):
                    self.dcnm_intf_pvlan_block(
                        m["name"], target["sno"],
                        "the member's current policy {0} is not covered by the CLI model".format(m["pre"][0]))
        for target in self.pvlan_targets.values():
            if target.get("kind") != "vpc" or target.get("deletes") or not (target["creates"] or target["update"]):
                continue
            if self.module.check_mode and target["creates"]:
                self.dcnm_intf_pvlan_block(
                    target["name"], target["sno"],
                    "creating a PVLAN vPC is refused in check mode: the pre-deploy gate needs the intent to exist, so its validation "
                    "could not be shown without writing")
            for leg in target["legs"]:
                for label, (policy, nv) in ((leg["po_name"], leg["post_po"]), (leg["member"], leg["post_member"])):
                    try:
                        modeled = pvlan_render(policy, nv).modeled
                    except PvlanError:
                        modeled = False
                    if not modeled:
                        self.dcnm_intf_pvlan_block(
                            label, leg["serial"],
                            "the intended {0} configuration is not covered by the CLI model, so its deployment could not be "
                            "validated".format(policy))
                if leg["pre_member"][0] not in PVLAN_VOCABULARY_POLICIES + PVLAN_PO_VOCABULARY_POLICIES + tuple(sorted(PVLAN_PO_PREPARED_BASELINES)):
                    self.dcnm_intf_pvlan_block(
                        leg["member"], leg["serial"],
                        "the member's current policy {0} is not covered by the CLI model".format(leg["pre_member"][0]))
                if leg["pre_po"][0] is not None and leg["pre_po"][0] not in PVLAN_VPC_VOCABULARY_POLICIES:
                    self.dcnm_intf_pvlan_block(
                        leg["po_name"], leg["serial"],
                        "the child port-channel's current policy {0} is not covered by the CLI model".format(leg["pre_po"][0]))
        for target in self.pvlan_targets.values():
            if not target["new_secondaries"]:
                continue
            networks = self.dcnm_intf_pvlan_read_networks()
            if networks is None:
                self.dcnm_intf_pvlan_block(
                    target["name"], target["sno"],
                    "fabric networks could not be read, so the secondary VLAN type of a new "
                    "trunk secondary association cannot be established",
                )
                continue
            for _primary, secondary in target["new_secondaries"]:
                kind, reason = pvlan_classify_secondary(networks, secondary)
                if kind == "community":
                    self.dcnm_intf_pvlan_block(
                        target["name"], target["sno"],
                        "secondary VLAN {0} is a community VLAN; trunk secondary takes an "
                        "isolated secondary".format(secondary),
                    )
                elif kind != "isolated":
                    self.dcnm_intf_pvlan_block(target["name"], target["sno"], reason)
        for target in self.pvlan_targets.values():
            if not target["update"] or target.get("kind") == "vpc":
                continue
            try:
                modeled = pvlan_render(*target["post"]).modeled
            except PvlanError:
                modeled = False
            if not modeled:
                # Known before any write: the destination's CLI cannot be validated, so its
                # deploy would be refused AFTER the intent changed. Refuse now instead.
                self.dcnm_intf_pvlan_block(
                    target["name"], target["sno"],
                    "the destination {0} configuration is not covered by the CLI model (for example a "
                    "non-default speed, storm-control levels, NetFlow or an AI/ML QoS fallback), so its "
                    "deployment could not be validated".format(target["post"][0]),
                )
        for target in self.pvlan_targets.values():
            if (target["update"] and target.get("kind") != "vpc"
                    and target["pre"][0] not in PVLAN_VOCABULARY_POLICIES + PVLAN_PO_VOCABULARY_POLICIES):
                # Known before any write: the commands of the current policy are outside the CLI
                # vocabulary, so the gate could never authorize their withdrawal.
                self.dcnm_intf_pvlan_block(
                    target["name"], target["sno"],
                    "the current policy {0} is not covered by the CLI model, so the commands a conversion "
                    "from it withdraws could not be validated".format(target["pre"][0]),
                )
        writes = [t for t in self.pvlan_targets.values() if t["update"] and t["post"][0] == PVLAN_POLICY]
        if writes and not self.pvlan_blocked:
            keys = set()
            for t in writes:
                keys.update(t["post"][1].keys())
            missing = self.dcnm_intf_pvlan_check_template(keys)
            if missing is None:
                self.dcnm_intf_pvlan_block("*", "*", "the int_pvlan_host template could not be read")
            elif missing:
                self.dcnm_intf_pvlan_block(
                    "*", "*", "the installed int_pvlan_host template does not declare: {0}".format(", ".join(missing))
                )
        if any(t["update"] for t in self.pvlan_targets.values()) and not self.pvlan_blocked:
            if self.module.check_mode:
                # The only capability probe (dcnm_get_bulk_api_support) is a POST; check mode sends
                # none, and no read-only source of this capability is established. Decided last, so
                # check mode still reports every read-only refusal above.
                self.dcnm_intf_pvlan_block(
                    "*", "*", "native PVLAN writes need the controller's bulk interface update API, and that "
                    "capability could not be verified in check mode: its only probe is a POST request, which "
                    "check mode does not send. Run without check mode to have it verified before any write")
            elif not self.has_bulk_api:
                # Same prerequisite the sender asserts, refused before any write.
                self.dcnm_intf_pvlan_block(
                    "*", "*", "native PVLAN writes need the controller's bulk interface update API, which is not available")
        if self.pvlan_blocked:
            lines = ["  {0} on {1}: {2}".format(b["interface"], b["serial"], b["reason"]) for b in self.pvlan_blocked]
            self.module.fail_json(
                msg="Native PVLAN preflight refused the invocation:\n" + "\n".join(lines)
                + "\nNo configuration or deployment request was sent.",
                **self.result
            )

    def dcnm_intf_pvlan_target_map(self):
        """PVLAN targets of this run; empty for objects built without __init__ (unit tests
        that drive a single sender method), so every non-PVLAN path behaves as before."""
        return getattr(self, "pvlan_targets", None) or {}

    def dcnm_intf_pvlan_items(self, items):
        targets = self.dcnm_intf_pvlan_target_map()
        return [
            it for it in items or []
            if (it.get("serialNumber"), str(it.get("ifName", "")).lower()) in targets
        ]

    def dcnm_intf_pvlan_deploy_gate(self, items, site, intent_changed, sent=None):
        """Immediately before a deploy attempt: one legacy forced recompute per serial, then one
        decision per PVLAN target from THAT fresh entry (pvlan_assess_target): the device's
        runningConfig, the controller's expectedConfig and the pending block.

        Returns the items still to deploy: PVLAN targets whose verified convergence makes the
        attempt redundant are dropped; every other item (including non-PVLAN members of the batch)
        is kept in order. Any refusal, outside-target or global pending stops the whole batch with
        nothing sent. Every call -- primary, resend, status retry -- recomputes again. `sent`: the (serial, name) items the primary
        deploy of this invocation already sent and the controller accepted; only a vPC among them is judged as "after its deploy"."""
        pv_all = self.dcnm_intf_pvlan_items(items)
        if not pv_all:
            return list(items or [])
        pv = [it for it in pv_all if self.pvlan_targets[(it["serialNumber"], str(it["ifName"]).lower())].get("kind") != "vpc"]
        pv_vpc = [it for it in pv_all if it not in pv]
        batch = {}
        for it in items:
            batch.setdefault(it.get("serialNumber"), set()).add(str(it.get("ifName", "")).lower())
        problems, converged = [], set()
        for sno in sorted({it["serialNumber"] for it in pv}):
            resp = dcnm_send(self.module, "GET", self.paths["PVLAN_CONFIG_PREVIEW"].format(self.fabric, sno))
            record = {"site": site, "serial": sno, "targets": {}}
            try:
                entry = pvlan_preview_entry(resp, sno)
                blocks, global_lines = pvlan_split_blocks(entry["pendingConfig"])
                record["status"] = entry["status"]
                deleted_po = set(
                    "no interface " + t["name"].lower() for t in self.pvlan_targets.values()
                    if t.get("deletes") and t["sno"] == sno
                    and (sno, t["name"].lower()) in set((i["serialNumber"], str(i["ifName"]).lower()) for i in pv))
                # The exact withdrawal of a conventional aggregate this invocation's confirmed mark-delete deleted on this serial
                invocation_withdrawn = pvlan_invocation_withdrawals(self, sno, global_lines)
                if [line for line in global_lines if line.lower() not in deleted_po and line.strip().lower() not in invocation_withdrawn]:
                    problems.append("{0}: pending carries commands outside interface scope".format(sno))
                allowed = set(batch.get(sno, set()))
                for vit in pv_vpc:
                    for leg in self.pvlan_targets[(vit["serialNumber"], str(vit["ifName"]).lower())]["legs"]:
                        if leg["serial"] == sno:
                            allowed.update((leg["po_name"].lower(), leg["member"].lower()))
                for it in pv:
                    tgt = self.pvlan_targets.get((it["serialNumber"], str(it["ifName"]).lower()))
                    if it["serialNumber"] == sno and tgt and tgt.get("kind") == "po":
                        allowed.update(m["name"].lower() for m in tgt["members"])
                        # MM-B: a member REMOVED by the update is part of this batch (its withdrawal and release are assessed below)
                        allowed.update(m["name"].lower() for m in tgt.get("removed") or [])
                self.dcnm_intf_pvlan_po_resume_removed(sno, entry, blocks, allowed, pv)
                outside = sorted(set(blocks) - allowed)
                # A conventional member this invocation's confirmed update released on this serial is not foreign
                owned = pvlan_invocation_owned(self, sno, outside, blocks)
                if owned or invocation_withdrawn:
                    record_owned = {"site": site, "serial": sno, "interfaces": owned}
                    if invocation_withdrawn:
                        record_owned["withdrawn"] = invocation_withdrawn
                    self.result.setdefault("pvlan_gate_invocation_releases", []).append(record_owned)
                    outside = [n for n in outside if n not in owned]
                if outside:
                    problems.append("{0}: pending exists for interfaces outside this deploy batch: {1}".format(
                        sno, ", ".join(outside)))
                for it in pv:
                    if it["serialNumber"] != sno:
                        continue
                    target = self.pvlan_targets[(sno, str(it["ifName"]).lower())]
                    try:
                        if target.get("deletes"):
                            decision, found = self.dcnm_intf_pvlan_po_delete_assess(blocks, entry, target)
                        elif target.get("kind") == "po":
                            decision, found = self.dcnm_intf_pvlan_po_assess(blocks, entry, target)
                        else:
                            decision, found = pvlan_assess_target(
                                blocks.get(target["name"].lower(), []), entry, target["name"], pvlan_render(*target["post"]),
                                pvlan_transition_vocabulary(target["pre"], target["post"]))
                    except PvlanError as exc:
                        decision, found = "refuse", [str(exc)]
                    record["targets"][target["name"]] = decision
                    if decision == "converged":
                        converged.add((sno, target["name"].lower()))
                    problems.extend("{0} on {1}: {2}".format(target["name"], sno, f) for f in found)
            except PvlanError as exc:
                problems.append(str(exc))
            self.result.setdefault("pvlan_gate", []).append(record)
        for it in pv_vpc:
            # BOTH peers are previewed and judged before ANY decision, and the vPC gets ONE decision.
            target = self.pvlan_targets[(it["serialNumber"], str(it["ifName"]).lower())]
            after = sent is not None and (it["serialNumber"], str(it["ifName"]).lower()) in sent
            decision, found = self.dcnm_intf_pvlan_vpc_gate(target, items, site, "delete" if target.get("deletes") else "post", after_deploy=after)
            if decision == "converged":
                converged.add((it["serialNumber"], target["name"].lower()))
            problems.extend("{0} on {1}: {2}".format(target["name"], target["sno"], f) for f in found)
        if problems:
            self.dcnm_intf_pvlan_fail(
                "Native PVLAN pre-deploy gate ({0}) refused the deployment:\n  {1}\n".format(site, "\n  ".join(problems))
                + "No deployment request was sent for this batch.", intent_changed)
        return [it for it in items if (it.get("serialNumber"), str(it.get("ifName", "")).lower()) not in converged]

    def dcnm_intf_pvlan_fail(self, message, intent_changed):
        """Fail with the intent and attempt history of this invocation; nothing is rolled back."""
        parts = [message]
        if intent_changed:
            parts.append("Intent for these targets was ALREADY changed on the controller and is not rolled back: {0}.".format(
                ", ".join(sorted("{0} on {1}".format(t["name"], t["sno"]) for t in self.pvlan_targets.values()
                                 if t["update"] or t.get("creates") or t.get("deletes")))))
            if any(t.get("kind") == "vpc" for t in self.pvlan_targets.values()):
                parts.append("For a vPC the intent MAY have changed on one or both peers (the child policies of each peer are not assumed "
                             "to exist or to be absent): read BOTH peers before any recovery; nothing is repaired automatically.")
        if self.pvlan_attempts:
            parts.append("Deployment attempts in this invocation: {0}.".format("; ".join(
                "{0} {1}: {2}".format(a["site"], ",".join(a["targets"]) or "-", a["outcome"]) for a in self.pvlan_attempts)))
        self.result["pvlan_attempts"] = list(self.pvlan_attempts)
        self.module.fail_json(msg=" ".join(parts), **self.result)

    def dcnm_intf_pvlan_deploy_attempt(self, items, site, resp, retain):
        """Judge the ORIGINAL response of one deploy attempt that carried PVLAN targets.

        The response is retained in result["response"] before judging. An explicit failure or an
        unrecognised body ends the invocation here: no later read and no further automatic
        deploy can turn it into success. Returns True for a documented benign notice, which the
        caller must corroborate with a fresh readback."""
        pv = self.dcnm_intf_pvlan_items(items)
        if not pv:
            return False
        problems, benign = pvlan_deploy_outcome(resp, pv)
        if retain or problems:
            # retain=False: the site appends this same response itself on its success path.
            self.result["response"].append(copy.deepcopy(resp))
        self.pvlan_attempts.append({
            "site": site,
            "targets": sorted("{0}@{1}".format(it["ifName"], it["serialNumber"]) for it in pv),
            "return_code": resp.get("RETURN_CODE") if isinstance(resp, dict) else None,
            "outcome": "; ".join(problems) if problems else ("benign notice" if benign else "accepted"),
        })
        if problems:
            self.dcnm_intf_pvlan_fail(
                "Native PVLAN deployment attempt ({0}) failed or is indeterminate:\n  {1}\n".format(site, "\n  ".join(problems))
                + "No further deployment was sent.", True)
        return benign

    def dcnm_intf_pvlan_verify_rounds(self, targets):
        """The reads of the non-vPC post-deploy verification, planned per switch and poll round.

        Each round reads the summary of every switch that still has an unconverged target ONCE and judges all of its targets on that same
        answer (identity by serial and interface; a missing, duplicated or rejected answer proves nothing). At most 6 rounds and one 5 s
        wait between rounds, so every target keeps the 6 polls it had and the total wait stays bounded. After the rounds, every switch with
        a converged target gets ONE forced bulk refresh, and the detail of each of its converged targets is taken from that read (or, when
        the bulk read fails, by the existing per-interface fallback of dcnm_intf_get_intf_info).
        Returns ({key: last status}, {key: detail}) for this call only: nothing is kept for another phase or invocation, and nothing read
        before the deploy is used (the summary is always read and the bulk always refreshed here)."""
        by_serial, seen = {}, set()
        for target in targets:
            key = (target["sno"], target["name"].lower())
            if key not in seen:
                seen.add(key)
                by_serial.setdefault(target["sno"], []).append(target)
        status = dict((key, None) for key in seen)
        pending = dict((sno, list(tgts)) for sno, tgts in by_serial.items())
        for attempt in range(6):
            for sno in list(pending):
                if not self.dcnm_intf_get_have_all_with_sno(sno):
                    continue
                for target in pending[sno]:
                    name = target["name"]
                    entry = [h for h in self.have_all if str(h.get("ifName", "")).lower() == name.lower()
                             and h.get("serialNo") == sno]
                    status[(sno, name.lower())] = entry[0].get("complianceStatus") if len(entry) == 1 else None
                pending[sno] = [t for t in pending[sno] if status[(sno, t["name"].lower())] != "In-Sync"]
                if not pending[sno]:
                    del pending[sno]
            if not pending:
                break
            if attempt < 5:
                time.sleep(5)
        detail = {}
        for sno, tgts in by_serial.items():
            converged = [t for t in tgts if status[(sno, t["name"].lower())] == "In-Sync"]
            if not converged:
                continue
            self.dcnm_intf_bulk_fetch_intf_info(sno, refresh=True)
            for target in converged:
                detail[(sno, target["name"].lower())] = self.dcnm_intf_get_intf_info(
                    target["name"], sno, "INTERFACE_PORT_CHANNEL" if target.get("kind") == "po" else "INTERFACE_ETHERNET")
        return status, detail

    def dcnm_intf_pvlan_verify_after_deploy(self, items):
        """Bounded, non-mutating convergence and intent readback for deployed PVLAN targets.

        The non-vPC targets are read per switch and poll round (dcnm_intf_pvlan_verify_rounds), planned when the first of them is
        reached and kept only for this call; every target is still judged here, in item order, with the same checks and messages. vPC
        targets keep their own verifier at their own position."""
        pv = self.dcnm_intf_pvlan_items(items)
        # VPC-READS: the vPC targets of THIS call; their verifier plans their shared reads once, after the deploy, for this call only.
        self._pvlan_vpc_call = {"targets": [t for t in (self.pvlan_targets[(i["serialNumber"], str(i["ifName"]).lower())] for i in pv)
                                            if t.get("kind") == "vpc"], "plan": None}
        try:
            self.dcnm_intf_pvlan_verify_after_deploy_items(pv)
        finally:
            self._pvlan_vpc_call = None

    def dcnm_intf_pvlan_verify_after_deploy_items(self, pv):
        """The per-target judgement of dcnm_intf_pvlan_verify_after_deploy, in item order."""
        rounds = None
        for it in pv:
            target = self.pvlan_targets[(it["serialNumber"], str(it["ifName"]).lower())]
            if target.get("kind") == "vpc":
                self.dcnm_intf_pvlan_vpc_verify(target)
                continue
            if rounds is None:
                non_vpc = [self.pvlan_targets[(i["serialNumber"], str(i["ifName"]).lower())] for i in pv]
                rounds = self.dcnm_intf_pvlan_verify_rounds([t for t in non_vpc if t.get("kind") != "vpc"])
            sno, name = target["sno"], target["name"]
            status = rounds[0][(sno, name.lower())]
            if status != "In-Sync":
                self.module.fail_json(
                    msg="Interface {0} on {1} was deployed but did not reach In-Sync (last status {2}). "
                    "No further deployment was sent.".format(name, sno, status), **self.result
                )
            detail = rounds[1].get((sno, name.lower()))
            post_policy, post_nv = target["post"]
            if not isinstance(detail, dict) or detail.get("policy") != post_policy:
                self.module.fail_json(
                    msg="Interface {0} on {1}: the post-deploy readback does not hold policy {2}.".format(
                        name, sno, post_policy), **self.result)
            if target.get("kind") == "po":
                po_nv = (detail.get("interfaces") or [{}])[0].get("nvPairs") or {}
                mismatch = []
                try:
                    if po_nv.get("PVLAN_MODE") != post_nv.get("PVLAN_MODE"):
                        mismatch.append("PVLAN_MODE")
                    for list_key in ("ASSOCIATION_LIST", "MAPPING_LIST"):
                        if pvlan_pairs_from_wire(po_nv.get(list_key, "") or "", list_key) != pvlan_pairs_from_wire(
                                post_nv.get(list_key, "") or "", list_key):
                            mismatch.append(list_key)
                    if not pvlan_native_equal(po_nv.get("PVLAN_NATIVE_VLAN", "") or "", post_nv.get("PVLAN_NATIVE_VLAN", "") or ""):
                        mismatch.append("PVLAN_NATIVE_VLAN")
                    if not pvlan_allowed_equal(po_nv.get("PVLAN_ALLOWED_VLANS", "") or "", post_nv.get("PVLAN_ALLOWED_VLANS", "") or ""):
                        mismatch.append("PVLAN_ALLOWED_VLANS")
                    if str(po_nv.get("ADMIN_STATE", "")).strip().lower() != str(post_nv.get("ADMIN_STATE", "")).strip().lower():
                        mismatch.append("ADMIN_STATE")
                    # RC2 (L2): the speed and the freeform of the port-channel, as the vPC readback compares them on each child.
                    # DUPLEX: the stored duplex is compared too, so a controller that answers `auto` to a `full` request is no PASS even
                    # when the compliance says In-Sync. An absent key reads as the template's own `auto`; a null never equals a requested value.
                    for key in ("SPEED", "PORT_DUPLEX_MODE", "CONF"):
                        if not pvlan_po_intent_same(key, po_nv, post_nv):
                            mismatch.append(key)
                except PvlanError as exc:
                    mismatch.append(str(exc))
                # MM-B: identity by canonical port (a controller spelling such as `e1/8` names the same member)
                if pvlan_normalize_member_list(po_nv.get("MEMBER_INTERFACES")) != pvlan_normalize_member_list(post_nv.get("MEMBER_INTERFACES")):
                    mismatch.append("MEMBER_INTERFACES")
                if mismatch:
                    self.module.fail_json(
                        msg="Interface {0} on {1}: post-deploy intent readback differs in {2}.".format(
                            name, sno, ", ".join(mismatch)), **self.result)
                if target.get("removed"):
                    self.dcnm_intf_pvlan_po_verify_removed(target)
                continue
            if post_policy != PVLAN_POLICY:
                continue
            have_nv = (detail.get("interfaces") or [{}])[0].get("nvPairs") or {}
            mismatch = []
            try:
                if have_nv.get("PVLAN_MODE") != post_nv.get("PVLAN_MODE"):
                    mismatch.append("PVLAN_MODE")
                for key in ("ASSOCIATION_LIST", "MAPPING_LIST"):
                    if pvlan_pairs_from_wire(have_nv.get(key, ""), key) != pvlan_pairs_from_wire(post_nv.get(key, ""), key):
                        mismatch.append(key)
            except PvlanError as exc:
                mismatch.append(str(exc))
            if not pvlan_native_equal(have_nv.get("PVLAN_NATIVE_VLAN", ""), post_nv.get("PVLAN_NATIVE_VLAN", "")):
                mismatch.append("PVLAN_NATIVE_VLAN")
            if not pvlan_allowed_equal(have_nv.get("PVLAN_ALLOWED_VLANS", ""), post_nv.get("PVLAN_ALLOWED_VLANS", "")):
                mismatch.append("PVLAN_ALLOWED_VLANS")
            if mismatch:
                self.module.fail_json(
                    msg="Interface {0} on {1}: post-deploy intent readback differs in {2}.".format(
                        name, sno, ", ".join(mismatch)), **self.result)

    def dcnm_intf_pvlan_vpc_verify_removed(self, target):
        """MM-B: the members removed from a vPC, after the deploy, verified on THEIR serials like a port-channel's removed members."""
        by_serial = {}
        for r in target.get("removed_legs") or []:
            by_serial.setdefault(r["serial"], []).append({"name": r["member"], "post": r["post"]})
        for serial, removed in sorted(by_serial.items()):
            self.dcnm_intf_pvlan_po_verify_removed({"sno": serial, "name": target["name"], "removed": removed}, owner_label="vPC")

    def dcnm_intf_pvlan_po_verify_removed(self, target, owner_label="port-channel"):
        """MM-B: bounded, non-mutating readback of the members an update removed, after the deploy: each holds its modeled released policy,
        administratively down and In-Sync, no live policy of the member is the port-channel's, and a routed release is a sole direct owner with
        only its own down children. A read that fails is an observation, never a success; nothing is rewritten."""
        sno, name = target["sno"], target["name"]
        observed = "no readback was attempted"
        for attempt in range(6):
            self.dcnm_intf_invalidate_serial_authority(sno)
            self.pvlan_policies.pop(sno, None)
            problems = []
            if not self.dcnm_intf_get_have_all_with_sno(sno):
                problems.append("the interface summary could not be read authoritatively")
            else:
                self.dcnm_intf_bulk_fetch_intf_info(sno, refresh=True)
                policies = self.dcnm_intf_pvlan_read_policies(sno)
                if policies is None:
                    problems.append("the switch policy list could not be read authoritatively")
                for m in target["removed"]:
                    want = m["post"][0]
                    detail = self.dcnm_intf_get_intf_info(m["name"], sno, "INTERFACE_ETHERNET")
                    nv = ((detail.get("interfaces") or [{}])[0].get("nvPairs") or {}) if isinstance(detail, dict) else {}
                    summ = [h for h in self.have_all if h.get("serialNo") == sno and str(h.get("ifName", "")).lower() == m["name"].lower()]
                    if not isinstance(detail, dict) or detail.get("policy") != want:
                        problems.append("{0} holds {1!r}, not {2}".format(m["name"], detail.get("policy") if isinstance(detail, dict) else None, want))
                    elif str(nv.get("ADMIN_STATE", "")).strip().lower() != self.dcnm_intf_pvlan_release_admin():
                        problems.append("{0} is not at the fabric's host default ADMIN_STATE {1}".format(
                            m["name"], self.dcnm_intf_pvlan_release_admin()))
                    if len(summ) != 1 or summ[0].get("complianceStatus") != "In-Sync":
                        problems.append("{0} is not In-Sync in the interface summary".format(m["name"]))
                    if policies is not None:
                        claims = sorted("{0}/{1}".format(p.get("templateName"), p.get("source")) for p in policies
                                        if p.get("deleted") is not True and str(p.get("deleted", "")).lower() != "true"
                                        and str(p.get("entityName", "")).lower() == m["name"].lower()
                                        and (p.get("templateName") == PO_MEMBER_POLICY or str(p.get("source", "")).lower() == name.lower()))
                        if claims:
                            problems.append("{0} is still claimed by the {1}: {2}".format(m["name"], owner_label, claims))
                    if want == PVLAN_PO_ROUTED_BASELINE_POLICY and isinstance(detail, dict) and detail.get("policy") == want:
                        why = self.dcnm_intf_pvlan_check_ownership(
                            m["name"], sno, want, nv, self_children=pvlan_released_routed_children(self.dcnm_intf_pvlan_release_admin() or "false"))
                        if why:
                            problems.append("{0}: {1}".format(m["name"], why))
            if not problems:
                return
            observed = "; ".join(problems)
            if attempt < 5:
                time.sleep(5)
        self.module.fail_json(
            msg="PVLAN {0} {1} on {2}: the member(s) removed by the update could not be verified as released after 6 readback attempts: "
            "{3}. Nothing else was sent; no member was rewritten.".format(owner_label, name, sno, observed), **self.result)

    def dcnm_intf_can_be_added(self, want):

        name = want["interfaces"][0]["ifName"]
        sno = want["interfaces"][0]["serialNumber"]
        fabric = want["interfaces"][0]["fabricName"]
        self.dcnm_intf_require_summary_authority(sno)

        match_have = [
            have
            for have in self.have_all
            if (
                (name.lower() == have["ifName"].lower())
                and (sno == have["serialNo"])
                and (fabric == have["fabricName"])
            )
        ]
        if match_have:
            if (match_have[0]["complianceStatus"] != "In-Sync") and (
                match_have[0]["complianceStatus"] != "Pending"
            ):
                return match_have[0], True
            else:
                return match_have[0], False
        return [], True

    def dcnm_intf_replace_pc_members(self, want, have):
        """
        Search ``self.want`` for any port-channel member interfaces that are also
        found in ``self.have`` and if found will replace the member interfaces in
        self.want with the correct policy and properties that can be managed.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        # Get supported port-channel member policies
        member_policy_names = []
        for key in self.pol_pc_member_types[self.dcnm_version].keys():
            member_policy_names.append(self.pol_pc_member_types[self.dcnm_version][key])

        for have_int in have:
            if have_int["policy"] in member_policy_names:
                # We have a port-channel member interface. Find the corresponding port-channel
                # interface on the same device in want and replace the member interfaces
                have_pc_name = have_int["interfaces"][0]["ifName"]
                have_pc_serial = have_int["interfaces"][0]["serialNumber"]

                for want_int in want:
                    # List of keys in nvPairs to protect
                    protected_keys = ["PO_ID", "PC_MODE", "INTF_NAME", "ALLOWED_VLANS", "DESC", "ADMIN_STATE", "CONF", "PRIMARY_INTF", "FEC"]
                    match_int = find_dict_in_list_by_key_value(search=want_int['interfaces'], key='ifName', value=have_pc_name)
                    if match_int and match_int['serialNumber'] == have_pc_serial:
                        msg = "\nHave Interface Info: "
                        msg += f"{json_pretty(have_int)}"
                        msg += "Want Interface Info Before Update: "
                        msg += f"{json_pretty(want_int)}"
                        self.log.debug(msg)
                        # Rewrite want nvPairs and policy with the correct information
                        want_int['interfaces'][0]['nvPairs']['PO_ID'] = have_int['interfaces'][0]['nvPairs']['PO_ID']
                        want_int['interfaces'][0]['nvPairs']['INTF_NAME'] = have_int['interfaces'][0]['nvPairs']['INTF_NAME']

                        # The following keys may or may not be present for PC member interfaces
                        for key in ['PC_MODE', 'ALLOWED_VLANS', 'PRIMARY_INTF']:
                            want_int['interfaces'][0]['nvPairs'][key] = have_int['interfaces'][0]['nvPairs'].get(key)
                            if want_int['interfaces'][0]['nvPairs'][key] is None and key in protected_keys:
                                protected_keys.remove(key)

                        # Delete unprotected keys from want_int nvPairs
                        for key in list(want_int['interfaces'][0]['nvPairs'].keys()):
                            if key not in protected_keys:
                                want_int['interfaces'][0]['nvPairs'].pop(key)

                        # Update want_int policy to be the same as have_int policy
                        want_int['policy'] = have_int['policy']

                        msg += "Want Interface Info After Update: "
                        msg += f"{json_pretty(want_int)}"
                        self.log.debug(msg)

        self.want = want
        self.have = have

    def dcnm_intf_gie_dependencies(self, state, want, have_nvpairs, pb_keys, name):
        """Dependent-field rules (inert_when, gie_dependency_plan) for one interface WANT.

        Conflicts are recorded in self.dependency_blocked and raised by main() before any request.
        In merged, an explicit disable of a gate also brings its stored dependents to neutral: the
        returned writes are applied to WANT by the caller. `have_nvpairs` is {} unless HAVE has the
        same parent (a new interface or a policy change has no stored dependents)."""
        if state not in ("merged", "replaced", "overridden"):
            return {}
        policy = want.get("policy")
        explicit = set(
            b["parent_nvpair"] for b in gie_carry_forward_bindings(policy) if b["profile_key"] in pb_keys
        )
        writes, conflicts = gie_dependency_plan(
            policy,
            want["interfaces"][0]["nvPairs"],
            have_nvpairs,
            explicit,
            state == "merged",
            getattr(self, "ndfc_version", None),
            getattr(self, "patch_version", None),
        )
        for conflict in conflicts:
            self.dependency_blocked.append(dict(conflict, interface=name, parent=policy))
        return writes

    def dcnm_intf_compare_want_and_have(self, state):
        """
        Compare want and have states for each interface
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: entered"
        self.log.debug(msg)

        # Special Case Handling for PortChannnel (PC) and Virtual PortChannel (vPC) Member Interfaces.
        # Member interfaces are added to a PC or vPC when the PC or vPC is created and the
        # policy is applied to the member interface based on the type of PC or vPC.
        #
        # Once this policy is applied to the member interface, only the following properties
        # can be modified on the member interface:
        #   - Interface Description
        #   - Interface Admin State
        #   - Interface Freeform Configuration
        #
        # The following logic will search self.have for any member interfaces that are also
        # found in self.want and if found will replace the member interfaces in self.want
        # with the correct policy and properties that can be managed. After that we process
        # the new self.want as usual.
        if any(w.get("policy") in (PO_HOST_POLICY, VPC_HOST_POLICY) for w in self.want):
            # Only an invocation that carries a PVLAN port-channel runs the requested-set check; every other flow, and
            # every unit-test object built without __init__, never reaches it.
            self.dcnm_intf_pvlan_requested_conflicts()
        # A PVLAN WANT on a port-channel/vPC member must be refused BEFORE the member rewrite
        # below, which would otherwise silently turn it into the member policy.
        pvlan_skip = set()
        for want in self.want:
            if want.get("policy") != PVLAN_POLICY:
                continue
            member_policies = self.dcnm_intf_pvlan_member_policies()
            w_name = want["interfaces"][0]["ifName"]
            w_sno = want["interfaces"][0]["serialNumber"]
            for h in self.have:
                h_intf = (h.get("interfaces") or [{}])[0]
                if (
                    str(h_intf.get("ifName", "")).lower() == w_name.lower()
                    and h_intf.get("serialNumber") == w_sno
                    and h.get("policy") in member_policies
                ):
                    self.dcnm_intf_pvlan_block(
                        w_name, w_sno, "it is a port-channel or vPC member ({0})".format(h.get("policy")))
                    pvlan_skip.add(id(want))

        # D4: the member of a PVLAN port-channel is managed by its PARENT. Any WANT that targets an
        # interface currently holding the PVLAN member policy is a direct child mutation and is
        # refused before any write; the generic member rewrite never sees this policy.
        for want in self.want:
            if id(want) in pvlan_skip:
                continue
            w_name = want["interfaces"][0]["ifName"]
            w_sno = want["interfaces"][0]["serialNumber"]
            for h in self.have:
                h_intf = (h.get("interfaces") or [{}])[0]
                if (
                    str(h_intf.get("ifName", "")).lower() == w_name.lower()
                    and h_intf.get("serialNumber") == w_sno
                    and h.get("policy") == PO_MEMBER_POLICY
                ):
                    self.dcnm_intf_pvlan_block(
                        w_name, w_sno,
                        "it is a member of a PVLAN port-channel; its membership and policy are managed by "
                        "the parent ({0}), so changing it directly is not implemented".format(PO_MEMBER_POLICY))
                    pvlan_skip.add(id(want))

        have_member = {}
        msg = "Member Policy Types: "
        msg += f"{self.pol_pc_member_types[self.dcnm_version]}"
        self.log.debug(msg)
        for key in self.pol_pc_member_types[self.dcnm_version].keys():
            # Potential Keys:
            # [
            #   'pc_access_member',
            #   'pc_trunk_member',
            #   'vpc_peer_link_member',
            #   'vpc_access_member',
            #   'vpc_trunk_member',
            #   'l3_pc_member',
            #   'pc_dot1q_tunnel_member',
            # ]
            # NOTE: pvlan interface types are currently not supported by this module.
            policy_name = self.pol_pc_member_types[self.dcnm_version][key]
            have_member = find_dict_in_list_by_key_value(search=self.have, key='policy', value=policy_name)

            # If we find any member in self.have that matches a policy in self.pol_pc_member_types[self.dcnm_version].keys()
            # then call the self.dcnm_intf_replace_pc_members function to process all PC and vPC members.
            if have_member:
                self.dcnm_intf_replace_pc_members(self.want, self.have)
                break

        # --------------------------------------------------------------------------------------------------------------------

        # workflow to manage breakout interfaces
        # Append to self.diff_create_breakout to create breakout
        # Append to self.diff_delete_breakout to delete breakout
        if state != "deleted":
            for want_breakout in self.want_breakout:
                want_intf = want_breakout["interfaces"][0]["ifName"]
                want_serialnumber = want_breakout["interfaces"][0]["serialNumber"]
                # We cannot create breakout interfaces on pre-provisioned / unmanageable
                # devices. Posting a breakout to such a switch returns NDFC 500
                # "Invalid Interface". Skip them (mirrors the have-side guard above).
                if want_serialnumber not in self.manageable.values():
                    self.changed_dict[0]["skipped"].append(
                        {
                            "Name": want_intf,
                            "serialNumber": want_serialnumber,
                            "Reason": "Switch is in preprovision state or not manageable",
                        }
                    )
                    continue
                # A skipped switch sends nothing, so it needs no authoritative breakout summary;
                # a manageable one still does before create / no-op is decided.
                self.dcnm_intf_require_summary_authority(
                    want_serialnumber, endpoint="breakout"
                )
                match_create = False
                # Search if interface is in have_breakout
                for elem in self.have_breakout:
                    if want_serialnumber == list(elem.keys())[0]:
                        for interface in elem[want_serialnumber]:
                            if interface.lower() == want_intf.lower():
                                # If the breakout interface is already present in have,
                                # skip adding it to diff_create_breakout
                                match_create = True
                                break
                if not match_create:
                    self.diff_create_breakout.append(want_breakout["interfaces"])

        if state == "deleted" or state == "overridden":
            for have_breakout in self.have_breakout:
                self.dcnm_intf_require_summary_authority(
                    list(have_breakout.keys())[0], endpoint="breakout"
                )
                for interface in list(have_breakout.values())[0]:
                    match_delete_interface = True
                    for want_breakout in self.want_breakout:
                        if list(have_breakout.keys())[0] == want_breakout["interfaces"][0]["serialNumber"]:
                            if want_breakout["interfaces"][0]["ifName"] == interface:
                                match_delete_interface = False
                                break
                    if match_delete_interface:
                        payload = {
                            "serialNumber": list(have_breakout.keys())[0],
                            "ifName": interface + "/1"
                        }
                        self.diff_delete_breakout.append(payload)

        for want in self.want:

            delem = {}
            action = ""
            name = want["interfaces"][0]["ifName"]
            sno = want["interfaces"][0]["serialNumber"]
            fabric = want["interfaces"][0]["fabricName"]
            deploy = want["deploy"]

            intf_changed = False

            want.pop("deploy")
            if state == "replaced" and self._replace_have_lookup:
                match_have = self._replace_have_lookup.get(
                    (name.lower(), str(sno)), []
                )
            else:
                match_have = [
                    d
                    for d in self.have
                    if (
                        (name.lower() == d["interfaces"][0]["ifName"].lower())
                        and (sno == d["interfaces"][0]["serialNumber"])
                    )
                ]
            if id(want) in pvlan_skip:
                continue
            if want.get("policy") == PVLAN_POLICY:
                self.dcnm_intf_pvlan_compare(state, want, match_have, name, sno, fabric, deploy)
                continue
            if want.get("policy") == PO_HOST_POLICY:
                if self.dcnm_intf_pvlan_po_compare(state, want, match_have, name, sno, fabric, deploy) != "create":
                    continue
                # A new port-channel continues in the generic creation path below.
            if want.get("policy") == VPC_HOST_POLICY:
                if self.dcnm_intf_pvlan_vpc_compare(state, want, match_have, name, sno, fabric, deploy) != "create":
                    continue
                # A new vPC continues in the generic creation path below.
            if not match_have:
                self.dcnm_intf_require_detail_authority(name, sno)
                # A new interface has no stored dependents: only its explicit input is judged.
                self.dcnm_intf_gie_dependencies(state, want, {}, [
                    key for pb in self.pb_input
                    if name.lower() == pb["ifname"].lower() and sno == pb["sno"] and fabric == pb["fabric"]
                    for key in pb
                ], name)
                changed_dict = copy.deepcopy(want)

                if (
                    (state == "merged")
                    or (state == "replaced")
                    or (state == "overridden")
                ):
                    action = "add"
            else:

                wkeys = list(want.keys())
                if "skipResourceCheck" in wkeys:
                    wkeys.remove("skipResourceCheck")
                if "interfaceType" in wkeys:
                    wkeys.remove("interfaceType")

                for d in match_have:

                    changed_dict = copy.deepcopy(want)
                    if "skipResourceCheck" in changed_dict.keys():
                        changed_dict.pop("skipResourceCheck")

                    if state == "replaced" and self._replace_pb_input_lookup:
                        match_pb = self._replace_pb_input_lookup.get(
                            (name.lower(), str(sno), fabric), []
                        )
                    else:
                        match_pb = [
                            pb
                            for pb in self.pb_input
                            if (
                                (name.lower() == pb["ifname"].lower())
                                and (sno == pb["sno"])
                                and (fabric == pb["fabric"])
                            )
                        ]
                    pb_keys = list(match_pb[0].keys()) if match_pb else []

                    # First check if the policies are same for want and have. If they are different, we cannot compare
                    # the profiles because each profile will have different elements. As per PRD, if policies are different
                    # we should not merge the information. For now we will assume we will overwrite the same. Don't compare
                    # rest of the structure. Overwrite with whatever is in want

                    if want["policy"] != d["policy"]:
                        # The OSPF-MD policy-mismatch guard that ran here went with the bindings
                        # it protected: it only inspected the message-digest nvPair across a
                        # parent change, and nothing loopback-specific is left to guard.
                        # The stored values belong to the other parent: only explicit input is judged.
                        self.dcnm_intf_gie_dependencies(state, want, {}, pb_keys, name)
                        action = "update"
                        continue

                    for k in wkeys:
                        if k == "interfaces":
                            if_keys = list(want[k][0].keys())
                            if_keys.remove("interfaceType")
                            changed_dict[k][0].pop("interfaceType")

                            # 'have' will not contain the fabric name object. So do not try to compare that. This
                            # is especially true for Ethernet interfaces. Since a switch can belong to only one fabric
                            # the serial number should be unique across all fabrics
                            if_keys.remove("fabricName")
                            changed_dict[k][0].pop("fabricName")
                            for ik in if_keys:
                                if ik == "nvPairs":
                                    nv_keys = list(want[k][0][ik].keys())

                                    # ---------------------------------------- withdrawal
                                    # Omission-only reconciliation for `replaced` and for an
                                    # interface RETAINED under `overridden`. `merged` keeps
                                    # its preservation contract and never enters here.
                                    #
                                    # This runs BEFORE the generic carry-forward below, and
                                    # that ordering is the whole integration: the
                                    # carry-forward already skips any nvPair present in
                                    # `want`, so a reset written here makes it stand down
                                    # for that binding without a second flag.
                                    #
                                    # The reset is written into THREE places, not one:
                                    #   want[...]      -> it reaches the outgoing request
                                    #   nv_keys        -> the comparator treats it as a
                                    #                     normal difference, so omission
                                    #                     ALONE produces the write
                                    #   changed_dict   -> it is REPORTED. changed_dict is
                                    #                     deep-copied from want further up,
                                    #                     before this point, so a value put
                                    #                     only in `want` would be sent and
                                    #                     never shown -- the exact defect
                                    #                     measured on the carry-forward.
                                    if state in ("replaced", "overridden"):
                                        _w_gated = []
                                        for _w_b in gie_carry_forward_bindings(
                                            want.get("policy")
                                        ):
                                            _w_nvp = _w_b["parent_nvpair"]
                                            _w_key = _w_b["profile_key"]
                                            if _w_key in pb_keys:
                                                continue        # explicit input: not ours
                                            if _w_nvp in want[k][0][ik]:
                                                continue        # already emitted by the builder
                                            if gie_binding_is_owned_elsewhere(
                                                want.get("policy"), _w_nvp
                                            ):
                                                continue        # another path owns this pair
                                            _w_absent = object()
                                            _w_have = next(
                                                (
                                                    intf[ik][_w_nvp]
                                                    for intf in d[k]
                                                    if isinstance(intf.get(ik), dict)
                                                    and _w_nvp in intf[ik]
                                                ),
                                                _w_absent,
                                            )
                                            if _w_have is _w_absent:
                                                # Authoritatively absent. Nothing to
                                                # withdraw, and no default is invented.
                                                continue
                                            # The authoritative value must be READABLE
                                            # before it is classified. Without this the
                                            # step would short-circuit the HAVE validation
                                            # the carry-forward below performs: it writes
                                            # into `want`, the carry-forward then skips the
                                            # binding, and a malformed controller value
                                            # would be answered with a confident reset
                                            # instead of failing closed. Same call, same
                                            # value_source, same failure text.
                                            try:
                                                gie_validate_binding_value(
                                                    want.get("policy"),
                                                    _w_key,
                                                    _w_have,
                                                    value_source="have",
                                                )
                                            except GieBindingError as exc:
                                                self.module.fail_json(msg=str(exc))
                                            if _w_have == "":
                                                # NDFC's own encoding of "no value": the
                                                # engine documents and has measured it for
                                                # strings (ACL_FILTER), booleans whose
                                                # template declares no default, and
                                                # integers (OSPF_COST). It is absence, not
                                                # a configured value, so there is nothing
                                                # to withdraw -- and it never PRODUCES a
                                                # reset. Where "" is itself the verified
                                                # reset the branch above has already
                                                # matched it.
                                                continue
                                            _w_action, _w_wire = gie_withdrawal_action(
                                                want.get("policy"),
                                                _w_key,
                                                _w_have,
                                                getattr(self, "ndfc_version", None),
                                                getattr(self, "patch_version", None),
                                            )
                                            # GIE_WITHDRAW_INAPPLICABLE falls through to
                                            # nothing, deliberately. The controller cannot
                                            # carry this nvPair: emitting a reset would
                                            # transport what an explicit key is REFUSED at
                                            # gie_contribute_nvpairs, and refusing the run
                                            # would reject it over a field this controller
                                            # never had. The classifier owns that boundary
                                            # and it is the ONLY copy -- an earlier draft
                                            # repeated the check here as well, which made
                                            # each copy individually unkillable by mutation
                                            # while protecting nothing the generic
                                            # carry-forward below does not already do.
                                            if _w_action == GIE_WITHDRAW_RESET:
                                                want[k][0][ik][_w_nvp] = _w_wire
                                                if _w_nvp not in nv_keys:
                                                    nv_keys.append(_w_nvp)
                                                changed_dict[k][0][ik][_w_nvp] = _w_wire
                                            elif _w_action in (
                                                GIE_WITHDRAW_UNSUPPORTED,
                                                GIE_WITHDRAW_UNCLASSIFIED,
                                            ):
                                                # Collected, never raised here: the failure
                                                # is invocation-wide and must precede EVERY
                                                # interface's write, including ones already
                                                # diffed. main() raises it after the whole
                                                # comparison pass. The value is never
                                                # recorded -- a binding may carry a secret.
                                                _w_entry = {
                                                    "parent": want.get("policy"),
                                                    "field": _w_key,
                                                    "nvpair": _w_nvp,
                                                    "interface": name,
                                                    "reason": _w_action,
                                                }
                                                _w_row = gie_resolve_by_nvpair(want.get("policy"), _w_nvp)
                                                if _w_row is not None and _w_row.get("inert_when"):
                                                    # Judged after this loop, against the gate's
                                                    # final value (explicit, or reset above).
                                                    _w_gated.append((_w_row, _w_entry))
                                                else:
                                                    self.withdrawal_blocked.append(_w_entry)
                                        # A field inert under its gate (inert_when) is not withdrawn
                                        # when the gate ends at its inert value: the template neither
                                        # validates nor renders it, so the stored value is kept by
                                        # the carry-forward below and nothing new is transported. The
                                        # gate is taken from WANT when this pass sets it, else from
                                        # the authoritative HAVE the carry-forward will preserve.
                                        for _w_b, _w_entry in _w_gated:
                                            _w_gate_nv = {}
                                            # The gate, and its `unless` nvPair when declared (int_loopback: INTF_VRF).
                                            for _w_gate in gie_inert_gate_nvpairs(_w_b):
                                                if _w_gate in want[k][0][ik]:
                                                    _w_gate_nv[_w_gate] = want[k][0][ik][_w_gate]
                                                else:
                                                    for intf in d[k]:
                                                        if isinstance(intf.get(ik), dict) and _w_gate in intf[ik]:
                                                            _w_gate_nv[_w_gate] = intf[ik][_w_gate]
                                                            break
                                            if not gie_binding_inert(_w_b, _w_gate_nv):
                                                self.withdrawal_blocked.append(_w_entry)
                                            elif "clear" in _w_b["inert_when"]:
                                                # Key material is cleared, not kept, once its gate ends off.
                                                _w_clear = _w_b["inert_when"]["clear"]
                                                want[k][0][ik][_w_b["parent_nvpair"]] = _w_clear
                                                if _w_b["parent_nvpair"] not in nv_keys:
                                                    nv_keys.append(_w_b["parent_nvpair"])
                                                changed_dict[k][0][ik][_w_b["parent_nvpair"]] = _w_clear

                                    # Dependent fields (inert_when): explicit contradictions and empty required
                                    # fields are refused before any request; an explicit merged disable of a
                                    # gate brings its stored dependents to neutral, before the carry-forward
                                    # below would preserve them.
                                    _d_have = next(
                                        (intf[ik] for intf in d[k] if isinstance(intf.get(ik), dict)), {}
                                    )
                                    _d_written = set()
                                    for _d_nvp, _d_wire in self.dcnm_intf_gie_dependencies(
                                        state, want, _d_have, pb_keys, name
                                    ).items():
                                        _d_written.add(_d_nvp)
                                        want[k][0][ik][_d_nvp] = _d_wire
                                        if _d_nvp not in nv_keys:
                                            nv_keys.append(_d_nvp)
                                        changed_dict[k][0][ik][_d_nvp] = _d_wire

                                    # Preserve an authoritative current value for every omitted
                                    # registry passthrough binding on this SAME parent.  This is
                                    # transport preservation for replaced/overridden/full-payload
                                    # updates, not inferred intent: the carried value was not in
                                    # the original nv_keys and therefore is not reported as a
                                    # requested diff. Never invent a default when HAVE omits it.
                                    for binding in gie_carry_forward_bindings(
                                        want.get("policy")
                                    ):
                                        nvpair = binding["parent_nvpair"]
                                        profile_key = binding["profile_key"]
                                        if (
                                            profile_key in pb_keys
                                            or nvpair in want[k][0][ik]
                                        ):
                                            continue
                                        _gie_absent = object()
                                        have_value = next(
                                            (
                                                intf[ik][nvpair]
                                                for intf in d[k]
                                                if isinstance(intf.get(ik), dict)
                                                and nvpair in intf[ik]
                                            ),
                                            _gie_absent,
                                        )
                                        if have_value is not _gie_absent:
                                            try:
                                                gie_validate_binding_value(
                                                    want.get("policy"),
                                                    profile_key,
                                                    have_value,
                                                    value_source="have",
                                                )
                                            except GieBindingError as exc:
                                                self.module.fail_json(msg=str(exc))
                                            want[k][0][ik][nvpair] = have_value

                                    # Same-parent HAVE carry-forward (drift fix).
                                    # SCOPED to the exact proven parent
                                    # LOOPBACK_CARRY_FORWARD_PARENT (int_fabric_loopback_11_1): only
                                    # this parent's full HAVE nvPair set was observed and every key
                                    # classified as writable / read-only-metadata / OSPF-domain, so
                                    # the exclusion set is demonstrated complete only here. Other
                                    # parents are NOT carried until registry/template metadata proves
                                    # their writable/identity/sensitive nvPairs. Within this parent it
                                    # preserves ALL builder-omitted, non-excluded HAVE nvPairs (not a
                                    # hardcoded four). MERGED only (matches the existing 'leave
                                    # undeclared as-is' semantics; replaced/overridden intentionally
                                    # reset). The block runs on a SAME parent (a policy mismatch
                                    # already 'continue'd above). Carried value == exact HAVE, entered
                                    # after nv_keys, so no public diff, never overrides an
                                    # explicit/builder value already in want, idempotent.
                                    #
                                    # ONE AUTHORITATIVE PATH: the registered-binding carry-forward
                                    # immediately above returns [] for this parent (it has no
                                    # 'passthrough' binding), so the two never write the same nvPair.
                                    # The helper additionally skips any key already in want.
                                    # The fabric-owned loopback nvPairs are preserved in EVERY
                                    # state, not just merged. The module withdrew from managing
                                    # them, so their absence from a payload is not an operator
                                    # asking for a reset -- it is the module having nothing to
                                    # say. Narrow on purpose: widening the generic carry-forward
                                    # below to replaced/overridden would redefine what those
                                    # states mean for every other nvPair on this parent.
                                    if want.get("policy") == LOOPBACK_CARRY_FORWARD_PARENT:
                                        _fo_have = next(
                                            (
                                                intf[ik]
                                                for intf in d[k]
                                                if isinstance(intf.get(ik), dict)
                                            ),
                                            {},
                                        )
                                        for _fo_nvp, _fo_val in gie_fabric_owned_carry_forward(
                                            want[k][0][ik], _fo_have
                                        ).items():
                                            want[k][0][ik][_fo_nvp] = _fo_val

                                    if (
                                        state == "merged"
                                        and want.get("policy") == LOOPBACK_CARRY_FORWARD_PARENT
                                    ):
                                        _gie_have_nv = next(
                                            (
                                                intf[ik]
                                                for intf in d[k]
                                                if isinstance(intf.get(ik), dict)
                                            ),
                                            {},
                                        )
                                        for _gie_nvp, _gie_val in gie_have_carry_forward_nvpairs(
                                            want[k][0][ik], _gie_have_nv
                                        ).items():
                                            want[k][0][ik][_gie_nvp] = _gie_val

                                    # The OSPF-MD "safeguard an explicit false" block that ran
                                    # here was withdrawn with its binding. It existed so that a
                                    # controller unable to manage the nvPair could not silently
                                    # ignore an operator turning the feature off. With the
                                    # capability gate and the binding gone there is no explicit
                                    # request to safeguard: the module never sends the nvPair,
                                    # and the carry-forward above keeps whatever the fabric set.

                                    if want.get("policy") == "int_vlan":
                                        self.dcnm_intf_reconcile_svi_address_lists(
                                            state,
                                            name,
                                            want[k][0][ik],
                                            d[k],
                                            ik,
                                            nv_keys,
                                            changed_dict[k][0][ik],
                                        )
                                        if self.dcnm_intf_reconcile_svi_dhcp4(
                                            state,
                                            name,
                                            want[k][0][ik],
                                            d[k],
                                            ik,
                                            nv_keys,
                                            changed_dict[k][0][ik],
                                            pb_keys,
                                        ):
                                            action = "update"

                                    # List of keys to check and potentially remove from nv_keys
                                    # Some keys are not present in the first GET and must be removed
                                    keys_to_check = [
                                        "CDP_ENABLE",
                                        "DISABLE_LACP_SUSPEND",
                                        "ENABLE_LACP_VPC_CONV",
                                        "LACP_PORT_PRIO",
                                        "LACP_RATE",
                                        "ENABLE_MONITOR",
                                        "ENABLE_ORPHAN_PORT",
                                        "ENABLE_PFC",
                                        "NATIVE_VLAN",
                                        "PORT_DUPLEX_MODE",
                                        "SPEED",
                                        "ENABLE_QOS",
                                        "QOS_POLICY",
                                        "QUEUING_POLICY",
                                        "COPY_DESC",
                                        "ENABLE_STORM_CONTROL",
                                        "STORM_CONTROL_ACTION",
                                        "STORM_CONTROL_BCAST_LEVEL_PERCENT",
                                        "STORM_CONTROL_BCAST_LEVEL_PPS",
                                        "STORM_CONTROL_MCAST_LEVEL_PERCENT",
                                        "STORM_CONTROL_MCAST_LEVEL_PPS",
                                        "STORM_CONTROL_UCAST_LEVEL_PERCENT",
                                        "STORM_CONTROL_UCAST_LEVEL_PPS",
                                    ]

                                    if self._ndfc_version_gte("12.4.1"):
                                        keys_to_check.append("FEC")

                                    for key in keys_to_check:
                                        # Some GET payloads omit optional keys altogether. Keep comparing keys that were
                                        # explicitly requested in the playbook so merged state can correct drift when
                                        # the current payload is incomplete.
                                        key_missing_in_have = all(
                                            intf.get(ik, {}).get(key, None) is None
                                            for intf in d[k]
                                        )
                                        if (
                                            key in nv_keys
                                            and key_missing_in_have
                                            and self.keymap.get(key) not in pb_keys
                                        ):
                                            nv_keys.remove(key)

                                    for nk in nv_keys:
                                        # The registry says, per parent template, whether this
                                        # nvPair's case is part of its value. Only 'exact' changes
                                        # the comparison; every other key keeps the legacy one.
                                        exact_nv = gie_string_compare(want.get("policy"), nk) == "exact"
                                        # HAVE may have an entry with a list # of interfaces. Check all the
                                        # interface entries for a match.  Even if one entry matches do not
                                        # add the interface
                                        for index in range(len(d[k])):
                                            res = self.dcnm_intf_compare_elements(
                                                name,
                                                sno,
                                                fabric,
                                                want[k][0][ik][nk],
                                                d[k][index][ik].get(nk),
                                                nk,
                                                # A dependent neutralized by an explicit merged disable is
                                                # requested, not copied back from HAVE.
                                                "replaced" if nk in _d_written else state,
                                                exact_string=exact_nv,
                                            )
                                            if res == "dont_add":
                                                break
                                        if res == "copy_and_add":
                                            want[k][0][ik][nk] = d[k][0][ik][
                                                nk
                                            ]
                                            continue
                                        if res == "merge_and_add":
                                            merged_value = self.dcnm_intf_merge_want_and_have(
                                                nk,
                                                want[k][0][ik][nk],
                                                d[k][0][ik][nk],
                                            )
                                            # A merged aggregate key can resolve back to the
                                            # exact current controller value, for example
                                            # CONF="" merged with CONF="no shutdown". Skip
                                            # the update when the merged result is already in
                                            # sync.
                                            if (
                                                self.dcnm_intf_compare_elements(
                                                    name,
                                                    sno,
                                                    fabric,
                                                    merged_value,
                                                    d[k][0][ik].get(nk),
                                                    nk,
                                                    "replaced",
                                                )
                                                == "dont_add"
                                            ):
                                                changed_dict[k][0][ik].pop(nk)
                                                continue
                                            want[k][0][ik][nk] = merged_value
                                            changed_dict[k][0][ik][nk] = merged_value
                                        if res != "dont_add":
                                            action = "update"
                                        else:
                                            # Keys and values match. Remove from changed_dict
                                            changed_dict[k][0][ik].pop(nk)
                                else:
                                    # HAVE may have an entry with a list # of interfaces. Check all the
                                    # interface entries for a match.  Even if one entry matches do not
                                    # add the interface
                                    for index in range(len(d[k])):
                                        res = self.dcnm_intf_compare_elements(
                                            name,
                                            sno,
                                            fabric,
                                            want[k][0][ik],
                                            d[k][0][ik],
                                            ik,
                                            state,
                                        )
                                        if res == "dont_add":
                                            break
                                    if res == "copy_and_add":
                                        want[k][0][ik] = d[k][0][ik]
                                        continue
                                    if res == "merge_and_add":
                                        merged_value = self.dcnm_intf_merge_want_and_have(
                                            ik, want[k][0][ik], d[k][0][ik]
                                        )
                                        if (
                                            self.dcnm_intf_compare_elements(
                                                name,
                                                sno,
                                                fabric,
                                                merged_value,
                                                d[k][0][ik],
                                                ik,
                                                "replaced",
                                            )
                                            == "dont_add"
                                        ):
                                            changed_dict[k][0].pop(ik)
                                            continue
                                        want[k][0][ik] = merged_value
                                        changed_dict[k][0][ik] = merged_value
                                    if res != "dont_add":
                                        action = "update"
                                    else:
                                        # Keys and values match. Remove from changed_dict
                                        if ik != "ifName":
                                            changed_dict[k][0].pop(ik)
                        else:
                            res = self.dcnm_intf_compare_elements(
                                name, sno, fabric, want[k], d[k], k, state
                            )

                            if res == "copy_and_add":
                                want[k] = d[k]
                                continue
                            if res == "merge_and_add":
                                want[k] = self.dcnm_intf_merge_want_and_have(
                                    k, want[k], d[k]
                                )
                                changed_dict[k] = want[k]
                            if res != "dont_add":
                                action = "update"
                            else:
                                # Keys and values match. Remove from changed_dict.
                                changed_dict.pop(k)

            if action == "add":
                # If E1/x/y do not create. Interface is created with breakout
                if re.search(r"\d+\/\d+\/\d+", name):
                    if want.get("interfaceType", None) is not None:
                        want.pop("interfaceType")
                    self.dcnm_intf_merge_intf_info(want, self.diff_replace)
                    self.changed_dict[0][state].append(changed_dict)
                    intf_changed = True
                    continue
                self.dcnm_intf_merge_intf_info(want, self.diff_create)
                # Add the changed_dict to self.changed_dict
                self.changed_dict[0][state].append(changed_dict)
                intf_changed = True
            elif action == "update":
                # Remove the 'interfaceType' key from 'want'. It is not required for 'replace'
                if want.get("interfaceType", None) is not None:
                    want.pop("interfaceType")
                self.dcnm_intf_merge_intf_info(want, self.diff_replace)
                # Add the changed_dict to self.changed_dict
                self.changed_dict[0][state].append(changed_dict)
                intf_changed = True

            # if deploy flag is set to True, add the information so that this interface will be deployed
            if str(deploy).lower() == "true":
                # Add to diff_deploy,
                #   1. if intf_changed is True
                #   2. if intf_changed is False, then if 'complianceStatus is
                #      False then add to diff_deploy.
                #   3. Do not add otherwise

                if False is intf_changed:
                    match_intf, rc = self.dcnm_intf_can_be_added(want)
                else:
                    match_intf = []
                    rc = True

                if True is rc:
                    delem["serialNumber"] = sno
                    delem["ifName"] = name
                    delem["fabricName"] = self.fabric
                    self.diff_deploy.append(delem)
                    self.changed_dict[0]["deploy"].append(copy.deepcopy(delem))
                    if match_intf != []:
                        self.changed_dict[0]["debugs"].append(
                            {
                                "Name": name,
                                "SNO": sno,
                                "DeployStatus": match_intf["complianceStatus"],
                            }
                        )

    def dcnm_intf_get_diff_replaced(self):

        self.diff_create = []
        self.diff_delete = [[], [], [], [], [], [], [], []]
        self.diff_delete_deploy = [[], [], [], [], [], [], [], []]
        self.diff_deploy = []
        self.diff_replace = []

        for cfg in self.config:
            self.dcnm_intf_process_config(cfg)

        self.dcnm_intf_build_replace_lookups()

        # Compare want[] and have[] and build a list of dicts containing interface information that
        # should be sent to DCNM for updation. The list can include information on interfaces which
        # are already presnt in self.have and which differ in the values for atleast one of the keys

        self.dcnm_intf_compare_want_and_have("replaced")

    def dcnm_intf_get_diff_merge(self):

        self.diff_create = []
        self.diff_delete_deploy = [[], [], [], [], [], [], [], []]
        self.diff_deploy = []
        self.diff_replace = []

        for cfg in self.config:
            self.dcnm_intf_process_config(cfg)

        # Compare want[] and have[] and build a list of dicts containing interface information that
        # should be sent to DCNM for updation. The list can include information on new interfaces or
        # information regarding interfaces which require an update i.e. if any new information is added
        # to existing information.
        # NOTE: merge_diff will be updated only if there is some new information that is not already
        #       existing. If existing information needs to be updated then use 'replace'.

        self.dcnm_intf_compare_want_and_have("merged")

    def dcnm_intf_default_registered_resets(self, uelem, have):
        """The registered fields a reset of a physical port to its role default must withdraw.

        `uelem` is the role default payload (dcnm_intf_get_default_eth_payload), `have` the
        authoritative policy payload of the same interface. The legacy default comparison checks
        legacy nvPairs only and the default payload carries no registered nvPair, so a port whose
        only drift was a registered field (an ACL, flow control...) read as already default, and
        a reset that was sent left the field in place.

        For every nvPair of HAVE that is a registered binding of HAVE's own parent (not owned by
        another path, not read-only metadata) and holds a value, the established classifier
        decides, with the SAME capability and version boundary as the retained-interface
        withdrawal:
          * already withdrawn, or capability disabled (inapplicable): nothing -- the published
            contract while the capability is off is unchanged;
          * same parent, verified reset: that parent's own `reset_wire` is added to the payload;
          * same parent, unsupported or unclassified: blocked, named -- unless the row is gated
            (inert_when) and the gate, as this same reset leaves it (HAVE + role default payload +
            the verified resets queued here), makes it inert: then it stays stored, or is cleared
            when it declares `clear` (D-3: a border reset with OSPF on already sends ospf "false");
          * policy change (HAVE parent != default parent): the source value is NOT assumed to
            disappear with the policy change (not measured), except for the bindings of a parent
            declared in the generator as dropping all its interface-scoped child policies on a
            policy change (dropped_on_policy_change; int_routed_host), and for the bindings of an
            inline-rendered parent whose lines the controller negates for that destination
            (cleared_on_change_to; int_trunk_host and int_access_host -> int_routed_host, and for one measured field
            int_access_host loggingEventPortLinkStatus -> int_trunk_host). Only when the destination parent
            registers the same nvPair and either has a verified reset for the value (its own wire
            is used) or classifies it as already withdrawn (GIE_WITHDRAW_NONE -- the only proof of
            neutrality; INAPPLICABLE is not one) does the reset proceed; otherwise blocked as a
            transition, recording whether the SOURCE parent has a verified reset (the only case in
            which clearing the field on the current policy first is a module remedy). A source-only
            nvPair is never written into a destination template.

        Pure: returns (resets, blocked) and changes nothing. The caller applies them only where
        the reset is actually queued, so an interface that stays configured or is skipped by
        scope never produces a refusal. Values are never recorded (a binding may be a secret).
        """
        resets, blocked, gated = {}, [], []
        if not have or not uelem:
            return resets, blocked
        src = have.get("policy")
        dst = uelem.get("policy")
        have_intf = (have.get("interfaces") or [{}])[0]
        have_nv = have_intf.get("nvPairs") or {}
        ifname = have_intf.get("ifName") or uelem["interfaces"][0].get("ifName")
        sno = have_intf.get("serialNumber") or uelem["interfaces"][0].get("serialNumber")
        ndfc_version = getattr(self, "ndfc_version", None)
        patch_version = getattr(self, "patch_version", None)
        for nvpair in sorted(have_nv):
            binding = gie_resolve_by_nvpair(src, nvpair)
            if (
                binding is None
                or gie_binding_is_owned_elsewhere(src, nvpair)
                or nvpair in GIE_READONLY_METADATA_NVPAIRS
            ):
                continue
            value = have_nv[nvpair]
            if value is None or value == "":
                continue    # NDFC's encoding of "no value": nothing to withdraw, no reset invented
            entry = {"interface": ifname, "serial": sno, "parent": src, "destination": dst,
                     "field": binding["profile_key"], "nvpair": nvpair}
            action, wire = gie_withdrawal_action(src, binding["profile_key"], value, ndfc_version, patch_version)
            if action not in (GIE_WITHDRAW_RESET, GIE_WITHDRAW_UNSUPPORTED, GIE_WITHDRAW_UNCLASSIFIED):
                continue
            try:
                # Readable as its type before a reset is decided -- failing closed, as the retained
                # path does, but recorded instead of raised: this interface may not be reset at all.
                gie_validate_binding_value(src, binding["profile_key"], value, value_source="have")
            except GieBindingError:
                blocked.append(dict(entry, reason="unreadable"))
                continue
            if gie_binding_inert(binding, have_nv) and (action != GIE_WITHDRAW_RESET or src != dst):
                # Inert under its gate on the source (inert_when): it configures nothing, so there is nothing
                # to withdraw before a policy change (measured: the int_trunk_host intent carries no OSPF key
                # after routed -> trunk). On the same policy a verified reset is still sent, and key material
                # (clear) is cleared rather than kept.
                if src == dst and "clear" in binding["inert_when"]:
                    resets[nvpair] = binding["inert_when"]["clear"]
                continue
            gate = binding.get("inert_when")
            gate_binding = gie_resolve_by_nvpair(src, gate["nvpair"]) if gate else None
            if gate_binding is not None:
                # Disabling the gate on the current policy makes this field inert; the message names that remedy.
                entry["gate"] = gate_binding["profile_key"]
            if src == dst:
                if action == GIE_WITHDRAW_RESET:
                    resets[nvpair] = wire
                elif gate_binding is not None:
                    # D-3: no reset of its own, but the same reset may turn its gate off. Decided below, against the
                    # gate this reset leaves in place, once every verified reset of this interface is known.
                    gated.append((nvpair, binding, entry, action))
                else:
                    blocked.append(dict(entry, reason=action))
                continue
            dst_binding = gie_resolve_by_nvpair(dst, nvpair)
            dst_registers = dst_binding is not None and not gie_binding_is_owned_elsewhere(dst, nvpair)
            if dst_registers:
                d_action, d_wire = gie_withdrawal_action(dst, dst_binding["profile_key"], value, ndfc_version, patch_version)
                if d_action == GIE_WITHDRAW_RESET:
                    resets[nvpair] = d_wire
                    continue
                if d_action == GIE_WITHDRAW_NONE:
                    continue    # proven: already the destination's neutral value
                # UNSUPPORTED, UNCLASSIFIED and INAPPLICABLE prove nothing about the destination:
                # an inapplicable destination binding cannot even carry the field.
            if binding.get("dropped_on_policy_change"):
                # The source parent realizes this field only in an interface-scoped child policy that its delete()
                # removes when the policy is replaced (declared per parent, see POLICY_CHANGE_DROPS_CHILDREN in the
                # generator). The stored value leaves with the source parent; nothing is withdrawn on, or written
                # into, the destination.
                continue
            if not dst_registers and dst in (binding.get("cleared_on_change_to") or ()):
                # A different mechanism: the source parent renders this field inline, and the controller negates every
                # running line the destination's stanza does not expect when the policy is replaced with this destination
                # (declared per parent and destination, see POLICY_CHANGE_CLEARS_INLINE in the generator). Only for a
                # field the destination does not declare: one it declares is the destination's to classify (above).
                # Nothing is withdrawn on, or written into, the destination.
                continue
            blocked.append(dict(entry, reason="transition", source_reset=action == GIE_WITHDRAW_RESET))
        if gated:
            # D-3: the gate as this same-parent reset leaves it -- HAVE, then the role default payload, then the verified
            # resets queued above (e.g. ospf "false"). Only verified resets move a gate; an unreadable gate was blocked
            # above and never reaches `resets`. Every gate of a dependent row is itself a row with a verified reset, so
            # one pass decides them all. A dependent that is inert under the final gate configures nothing: it stays
            # stored (the controller keeps an inert ospfTag, measured) unless it declares `clear`, in which case key
            # material is cleared rather than kept. Otherwise it is refused exactly as before.
            final_nv = dict(have_nv)
            final_nv.update((uelem.get("interfaces") or [{}])[0].get("nvPairs") or {})
            final_nv.update(resets)
            for nvpair, binding, entry, action in gated:
                if gie_binding_inert(binding, final_nv):
                    if "clear" in binding["inert_when"]:
                        resets[nvpair] = binding["inert_when"]["clear"]
                    continue
                blocked.append(dict(entry, reason=action))
        return resets, blocked

    def dcnm_intf_queue_default_registered_resets(self, uelem, resets, blocked):
        """Apply what dcnm_intf_default_registered_resets found, at the point the reset is queued."""
        uelem["interfaces"][0]["nvPairs"].update(resets)
        self.default_reset_blocked.extend(blocked)

    def dcnm_compare_default_payload(self, intf, have):

        if intf.get("policy") != have.get("policy"):
            return "DCNM_INTF_NOT_MATCH"

        intf_nv = intf.get("interfaces")[0].get("nvPairs")
        have_nv = have.get("interfaces")[0].get("nvPairs")

        def normalize_default_compare_value(key, value):
            if value is None:
                value = ""

            sval = str(value).strip().lower()

            if key == "CONF":
                # NDFC may omit explicit default CLI from stored interface
                # intent while the module's generated default payload includes
                # "no shutdown". Treat them as equivalent for deleted-state
                # idempotence checks. The admin state is compared separately
                # via the dedicated ADMIN_STATE nvPair below.
                if sval in ("", "no shutdown"):
                    return ""
                return sval

            if key in (
                "ADMIN_STATE",
                "BPDUGUARD_ENABLED",
                "PORTTYPE_FAST_ENABLED",
            ):
                if sval in ("true", "yes"):
                    return "true"
                if sval in ("false", "no"):
                    return "false"
                return sval

            if key == "ENABLE_STORM_CONTROL":
                if sval in ("true", "yes", "on", "1", "y", "t"):
                    return "true"
                if sval in ("", "false", "no", "off", "0", "n", "f"):
                    return "false"
                return sval

            if key == "STORM_CONTROL_ACTION":
                if sval in ("", "default", "no"):
                    return "no"
                return sval

            return sval

        if (
            normalize_default_compare_value("SPEED", intf_nv.get("SPEED"))
            != normalize_default_compare_value("SPEED", have_nv.get("SPEED"))
        ):
            return "DCNM_INTF_NOT_MATCH"
        if (
            normalize_default_compare_value("DESC", intf_nv.get("DESC"))
            != normalize_default_compare_value("DESC", have_nv.get("DESC"))
        ):
            return "DCNM_INTF_NOT_MATCH"
        if (
            normalize_default_compare_value("CONF", intf_nv.get("CONF"))
            != normalize_default_compare_value("CONF", have_nv.get("CONF"))
        ):
            return "DCNM_INTF_NOT_MATCH"
        if (
            normalize_default_compare_value(
                "ADMIN_STATE", intf_nv.get("ADMIN_STATE")
            )
            != normalize_default_compare_value(
                "ADMIN_STATE", have_nv.get("ADMIN_STATE")
            )
        ):
            return "DCNM_INTF_NOT_MATCH"
        if (
            normalize_default_compare_value("MTU", intf_nv.get("MTU"))
            != normalize_default_compare_value("MTU", have_nv.get("MTU"))
        ):
            return "DCNM_INTF_NOT_MATCH"

        if intf.get("policy") == "int_routed_host":
            if (
                normalize_default_compare_value(
                    "INTF_VRF", intf_nv.get("INTF_VRF")
                )
                != normalize_default_compare_value(
                    "INTF_VRF", have_nv.get("INTF_VRF")
                )
            ):
                return "DCNM_INTF_NOT_MATCH"
            if (
                normalize_default_compare_value("IP", intf_nv.get("IP"))
                != normalize_default_compare_value("IP", have_nv.get("IP"))
            ):
                return "DCNM_INTF_NOT_MATCH"
            if (
                normalize_default_compare_value(
                    "PREFIX", intf_nv.get("PREFIX")
                )
                != normalize_default_compare_value(
                    "PREFIX", have_nv.get("PREFIX")
                )
            ):
                return "DCNM_INTF_NOT_MATCH"
            if (
                normalize_default_compare_value(
                    "ROUTING_TAG", intf_nv.get("ROUTING_TAG")
                )
                != normalize_default_compare_value(
                    "ROUTING_TAG", have_nv.get("ROUTING_TAG")
                )
            ):
                return "DCNM_INTF_NOT_MATCH"
        elif intf.get("policy") == "int_trunk_host":
            if (
                normalize_default_compare_value(
                    "BPDUGUARD_ENABLED", intf_nv.get("BPDUGUARD_ENABLED")
                )
                != normalize_default_compare_value(
                    "BPDUGUARD_ENABLED", have_nv.get("BPDUGUARD_ENABLED")
                )
            ):
                return "DCNM_INTF_NOT_MATCH"
            if (
                normalize_default_compare_value(
                    "PORTTYPE_FAST_ENABLED",
                    intf_nv.get("PORTTYPE_FAST_ENABLED"),
                )
                != normalize_default_compare_value(
                    "PORTTYPE_FAST_ENABLED",
                    have_nv.get("PORTTYPE_FAST_ENABLED"),
                )
            ):
                return "DCNM_INTF_NOT_MATCH"
            if (
                normalize_default_compare_value(
                    "ALLOWED_VLANS", intf_nv.get("ALLOWED_VLANS")
                )
                != normalize_default_compare_value(
                    "ALLOWED_VLANS", have_nv.get("ALLOWED_VLANS")
                )
            ):
                return "DCNM_INTF_NOT_MATCH"
            if (
                normalize_default_compare_value(
                    "NATIVE_VLAN", intf_nv.get("NATIVE_VLAN")
                )
                != normalize_default_compare_value(
                    "NATIVE_VLAN", have_nv.get("NATIVE_VLAN")
                )
            ):
                return "DCNM_INTF_NOT_MATCH"

            # Storm control is supported by the leaf role-default trunk
            # template. Treat omitted controller defaults as disabled, while
            # detecting any enabled action or retained threshold as drift.
            storm_control_keys = (
                "ENABLE_STORM_CONTROL",
                "STORM_CONTROL_ACTION",
                "STORM_CONTROL_BCAST_LEVEL_PERCENT",
                "STORM_CONTROL_BCAST_LEVEL_PPS",
                "STORM_CONTROL_MCAST_LEVEL_PERCENT",
                "STORM_CONTROL_MCAST_LEVEL_PPS",
                "STORM_CONTROL_UCAST_LEVEL_PERCENT",
                "STORM_CONTROL_UCAST_LEVEL_PPS",
            )
            for key in storm_control_keys:
                if normalize_default_compare_value(
                    key, intf_nv.get(key)
                ) != normalize_default_compare_value(key, have_nv.get(key)):
                    return "DCNM_INTF_NOT_MATCH"

        if self._ndfc_version_gte("12.4.1"):
            if (
                str(intf_nv.get("FEC", "auto")).lower()
                != str(have_nv.get("FEC", "auto")).lower()
            ):
                return "DCNM_INTF_NOT_MATCH"

        return "DCNM_INTF_MATCH"

    def dcnm_intf_get_host_intf_admin_state(self):
        """
        Return the fabric-level default administrative state for host
        (downlink) interfaces.

        When a physical Ethernet host interface is reset to its default
        configuration during 'deleted' or 'overridden' (and 'replaced')
        state, its administrative state must follow the fabric setting
        HOST_INTF_ADMIN_STATE instead of always being enabled.

        NDFC defaults HOST_INTF_ADMIN_STATE to 'true' (admin up / no
        shutdown). When a fabric administrator sets it to 'false', a reset
        host interface must come back administratively down (shutdown).

        The value is fetched once from the fabric details and cached for the
        remainder of the module run. If the fabric setting cannot be read,
        the historical behaviour (admin up) is preserved.

        Returns:
            bool: True if reset host interfaces should be admin up,
                  False if they should be admin down.
        """
        if getattr(self, "host_intf_admin_state", None) is not None:
            return self.host_intf_admin_state

        # Preserve historical behaviour (admin up) if the fabric setting
        # cannot be determined (for example when the module context or
        # fabric details are unavailable).
        admin_state = True
        module = getattr(self, "module", None)
        fabric = getattr(self, "fabric", None)
        if module is not None and fabric:
            try:
                fabric_details = get_fabric_details(module, fabric)
                if fabric_details:
                    nv_pairs = fabric_details.get("nvPairs") or {}
                    raw_value = nv_pairs.get("HOST_INTF_ADMIN_STATE")
                    if raw_value is not None:
                        admin_state = (
                            str(raw_value).strip().lower() in ("true", "yes")
                        )
            except Exception:
                # Any failure reading fabric details falls back to the safe
                # default of admin up, matching the module's prior behaviour.
                admin_state = True

        self.host_intf_admin_state = admin_state
        return admin_state

    def dcnm_intf_get_default_eth_payload(self, ifname, sno, fabric):

        # The administrative state of a host (downlink) interface reset to
        # default is governed by the fabric nvPair HOST_INTF_ADMIN_STATE and
        # is applied solely through the ADMIN_STATE nvPair below. Historically
        # this payload hard-coded ADMIN_STATE to True, which is wrong for
        # fabrics that set HOST_INTF_ADMIN_STATE to false. Derive the value
        # from the fabric so reset interfaces match the fabric-wide default.
        # The freeform CONF is intentionally left empty: the admin state is
        # already managed by the ADMIN_STATE flag, so injecting an explicit
        # "no shutdown" (or "shutdown") CLI here would contradict that flag
        # (e.g. ADMIN_STATE False + "no shutdown" freeform would bring the
        # interface back up).
        host_admin_up = self.dcnm_intf_get_host_intf_admin_state()

        eth_payload = {
            "policy": "",
            "interfaces": [
                {
                    "interfaceType": "INTERFACE_ETHERNET",
                    "serialNumber": "",
                    "ifName": "",
                    "fabricName": "",
                    "nvPairs": {
                        "interfaceType": "INTERFACE_ETHERNET",
                        "MTU": "",
                        "SPEED": "",
                        "DESC": "",
                        "CONF": "",
                        "ADMIN_STATE": host_admin_up,
                        "INTF_NAME": "",
                    },
                }
            ],
        }

        # Default payload depends on switch role. For switches with 'leaf' role the default policy must be
        # 'trunk'. For other roles it must be 'routed'.

        if self.sno_to_switch_role[sno] == "leaf":
            # default ehternet 'trunk' payload to be sent to DCNM for override case
            eth_payload["policy"] = self.pol_types[self.dcnm_version][
                "eth_trunk"
            ]
            eth_payload["interfaces"][0]["nvPairs"]["MTU"] = "jumbo"
            eth_payload["interfaces"][0]["nvPairs"]["SPEED"] = "Auto"
            eth_payload["interfaces"][0]["nvPairs"]["CONF"] = ""
            eth_payload["interfaces"][0]["nvPairs"][
                "BPDUGUARD_ENABLED"
            ] = False
            eth_payload["interfaces"][0]["nvPairs"][
                "PORTTYPE_FAST_ENABLED"
            ] = True
            eth_payload["interfaces"][0]["nvPairs"]["ALLOWED_VLANS"] = "none"
            eth_payload["interfaces"][0]["nvPairs"]["NATIVE_VLAN"] = ""
            eth_payload["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
            self.dcnm_intf_set_storm_control_nv_pairs(
                {}, eth_payload["interfaces"][0]["nvPairs"]
            )

            if self._ndfc_version_gte("12.4.1"):
                eth_payload["interfaces"][0]["nvPairs"]["FEC"] = "auto"

            eth_payload["interfaces"][0]["ifName"] = ifname
            eth_payload["interfaces"][0]["serialNumber"] = sno
            eth_payload["interfaces"][0]["fabricName"] = fabric

        else:
            # default ehternet 'routed' payload to be sent to DCNM for override case
            eth_payload["policy"] = self.pol_types[self.dcnm_version][
                "eth_routed"
            ]
            eth_payload["interfaces"][0]["nvPairs"]["MTU"] = 9216
            eth_payload["interfaces"][0]["nvPairs"]["SPEED"] = "Auto"
            eth_payload["interfaces"][0]["nvPairs"]["CONF"] = ""
            eth_payload["interfaces"][0]["nvPairs"]["INTF_NAME"] = ifname
            eth_payload["interfaces"][0]["nvPairs"]["INTF_VRF"] = ""
            eth_payload["interfaces"][0]["nvPairs"]["IP"] = ""
            eth_payload["interfaces"][0]["nvPairs"]["PREFIX"] = ""
            eth_payload["interfaces"][0]["nvPairs"]["ROUTING_TAG"] = ""

            if self._ndfc_version_gte("12.4.1"):
                eth_payload["interfaces"][0]["nvPairs"]["FEC"] = "auto"

            eth_payload["interfaces"][0]["ifName"] = ifname
            eth_payload["interfaces"][0]["serialNumber"] = sno
            eth_payload["interfaces"][0]["fabricName"] = fabric

        return eth_payload

    def dcnm_intf_build_can_be_replaced_lookups(self):
        """Pre-build lookup structures for O(1) dcnm_intf_can_be_replaced() checks.

        Replaces the O(n) linear scan of self.pb_input that was performed
        for every interface in have_all, turning the overall O(n*m) cost
        into O(n+m).

        Populates three instance-level lookup structures:
          _pb_override_lookup  – set of (ifname, sno) for overridden-state match
          _pb_member_lookup    – dict mapping expanded member ifName
                                 to list of (parent_ifname, parent_sno)
          _pb_peer_member_lookup – dict mapping expanded peer member ifName
                                   to parent_ifname
        """

        self._pb_override_lookup = set()
        self._pb_member_lookup = {}
        self._pb_peer_member_lookup = {}
        self._pb_deleted_parent_lookup = set()
        self._pb_deleted_peer_parent_lookup = set()

        for item in self.pb_input:
            ifname = item.get("ifname")
            sno = item.get("sno")

            # Override entries: (ifname, sno) pairs for direct match
            if ifname and sno:
                self._pb_override_lookup.add((ifname, sno))

            # Members (port-channel style)
            if item.get("members"):
                self._pb_deleted_parent_lookup.add((ifname, sno))
                for mem in item["members"]:
                    expanded_name = self.dcnm_intf_get_if_name(mem, "eth")[0]
                    if expanded_name not in self._pb_member_lookup:
                        self._pb_member_lookup[expanded_name] = []
                    self._pb_member_lookup[expanded_name].append((ifname, sno))

            # Peer members (VPC style)
            elif item.get("peer1_members") or item.get("peer2_members"):
                self._pb_deleted_parent_lookup.add((ifname, sno))
                self._pb_deleted_peer_parent_lookup.add(ifname)
                for mem in (item.get("peer1_members") or []):
                    expanded_name = self.dcnm_intf_get_if_name(mem, "eth")[0]
                    self._pb_peer_member_lookup[expanded_name] = ifname
                for mem in (item.get("peer2_members") or []):
                    expanded_name = self.dcnm_intf_get_if_name(mem, "eth")[0]
                    self._pb_peer_member_lookup[expanded_name] = ifname

    def dcnm_intf_can_be_replaced(self, have):

        # Build lookup structures on first call if not already built
        if not hasattr(self, '_pb_member_lookup'):
            self.dcnm_intf_build_can_be_replaced_lookups()

        have_ifname = have["ifName"]
        have_sno = have.get("serialNo")

        # Check 1: For overridden state, skip interfaces present in incoming
        # config — they will be modified in the current run anyway.
        if self.module.params["state"] == "overridden":
            if (have_ifname, have_sno) in self._pb_override_lookup:
                return False, have_ifname

        # Check 2: Check if this interface is a member of a port-channel.
        if have_ifname in self._pb_member_lookup:
            for parent_ifname, parent_sno in self._pb_member_lookup[have_ifname]:
                # Deleted state needs one extra reconciliation pass for member
                # Ethernet defaults after parent PC/vPC delete. Execution order
                # already sends parent deletes before member replacements, so it
                # is safe to queue the member default in the same module run.
                if self.module.params["state"] == "deleted":
                    if (parent_ifname, parent_sno) in self._pb_deleted_parent_lookup:
                        return True, parent_ifname
                # Compare have serial_number to item serial_number return if they don't match
                if have_sno != parent_sno:
                    return True, None
                else:
                    return False, parent_ifname

        # Check 3: Check if this interface is a peer member of a VPC.
        if have_ifname in self._pb_peer_member_lookup:
            if self.module.params["state"] == "deleted":
                parent_ifname = self._pb_peer_member_lookup[have_ifname]
                if parent_ifname in self._pb_deleted_peer_parent_lookup:
                    return True, parent_ifname
            return False, self._pb_peer_member_lookup[have_ifname]

        return True, None

    def dcnm_intf_parent_present_in_have_all(self, parent_ifname, parent_sno=None):

        parent_ifname = parent_ifname.lower()

        for have in self.have_all:
            if have.get("ifName", "").lower() != parent_ifname:
                continue
            if parent_sno is None or have.get("serialNo") == parent_sno:
                return True

        return False

    def dcnm_intf_should_defer_deleted_member_default(self, have, parent_ifname):

        if self.module.params["state"] != "deleted" or not parent_ifname:
            return False

        if not hasattr(self, "_pb_member_lookup"):
            self.dcnm_intf_build_can_be_replaced_lookups()

        have_ifname = have["ifName"]

        if have_ifname in self._pb_member_lookup:
            for candidate_parent_ifname, candidate_parent_sno in self._pb_member_lookup[have_ifname]:
                if candidate_parent_ifname != parent_ifname:
                    continue
                if (
                    (candidate_parent_ifname, candidate_parent_sno)
                    in self._pb_deleted_parent_lookup
                ):
                    return self.dcnm_intf_parent_present_in_have_all(
                        candidate_parent_ifname, candidate_parent_sno
                    )

        if have_ifname in self._pb_peer_member_lookup:
            if (
                self._pb_peer_member_lookup[have_ifname] == parent_ifname
                and parent_ifname in self._pb_deleted_peer_parent_lookup
            ):
                return self.dcnm_intf_parent_present_in_have_all(parent_ifname)

        return False

    def dcnm_intf_defer_deleted_member_default(
        self, ifname, sno, fabric, deploy, parent_ifname
    ):

        key = (str(sno), ifname.lower(), parent_ifname.lower())

        if key in self._deferred_delete_member_default_keys:
            return

        self._deferred_delete_member_default_keys.add(key)
        self.deferred_delete_member_defaults.append(
            {
                "ifName": ifname,
                "serialNumber": str(sno),
                "fabricName": fabric,
                "deploy": deploy,
                "parentIfName": parent_ifname,
            }
        )

    def dcnm_intf_refresh_deferred_deleted_member_defaults(self):

        if not self.deferred_delete_member_defaults:
            return

        affected_snos = sorted(
            {
                item["serialNumber"].split("~")[0]
                for item in self.deferred_delete_member_defaults
            }
        )

        max_retries = 10
        retry_sleep = 2

        for retry in range(max_retries):
            # Refresh only the impacted switches so same-run parent deletes are
            # reflected before we calculate default replacements for former members.
            self.have_all = [
                have
                for have in self.have_all
                if have.get("serialNo") not in affected_snos
            ]

            for sno in affected_snos:
                self.dcnm_intf_invalidate_serial_authority(sno)
                self.dcnm_intf_get_have_all_with_sno(sno)
                self.dcnm_intf_bulk_fetch_intf_info(sno)
                for item in self.deferred_delete_member_defaults:
                    if self._dcnm_intf_query_serial(
                        item["serialNumber"]
                    ) == sno:
                        self.dcnm_intf_require_detail_authority(
                            item["ifName"], item["serialNumber"]
                        )

            parent_still_present = False
            for item in self.deferred_delete_member_defaults:
                if self.dcnm_intf_parent_present_in_have_all(item["parentIfName"]):
                    parent_still_present = True
                    break

            if not parent_still_present:
                break

            if retry < (max_retries - 1):
                time.sleep(retry_sleep)

        for item in self.deferred_delete_member_defaults:
            intf = {
                "ifName": item["ifName"],
                "serialNumber": item["serialNumber"],
                "interfaceType": "INTERFACE_ETHERNET",
            }

            match_have = [
                have
                for have in self.have_all
                if (
                    (intf["ifName"].lower() == have["ifName"].lower())
                    and (intf["serialNumber"] == have["serialNo"])
                )
            ]

            if not match_have:
                continue

            if str(match_have[0].get("isPhysical")).lower() != "true":
                continue

            uelem = self.dcnm_intf_get_default_eth_payload(
                intf["ifName"], intf["serialNumber"], item["fabricName"]
            )
            intf_payload = self.dcnm_intf_get_intf_info_from_dcnm(intf)

            self.dcnm_intf_require_detail_authority(
                intf["ifName"], intf["serialNumber"]
            )

            if intf_payload != []:
                if (
                    self.dcnm_compare_default_payload(uelem, intf_payload)
                    == "DCNM_INTF_MATCH"
                ):
                    continue

            self.dcnm_intf_merge_intf_info(uelem, self.diff_replace)
            self.changed_dict[0]["replaced"].append(copy.deepcopy(uelem))

            if str(item.get("deploy", "true")).lower() == "true":
                delem = {
                    "serialNumber": intf["serialNumber"],
                    "ifName": intf["ifName"],
                    "fabricName": item["fabricName"],
                }
                self.diff_deploy.append(delem)
                self.changed_dict[0]["deploy"].append(copy.deepcopy(delem))

        self.deferred_delete_member_defaults = []
        self._deferred_delete_member_default_keys = set()

    def dcnm_intf_build_replace_lookups(self):
        """Pre-build lookup structures for replaced-state comparisons.

        Replaces repeated linear scans of self.have and self.pb_input during
        dcnm_intf_compare_want_and_have("replaced") with dictionary lookups.
        """

        self._replace_have_lookup = {}
        self._replace_pb_input_lookup = {}

        for item in self.have:
            interfaces = item.get("interfaces") or []
            if not interfaces:
                continue

            intf = interfaces[0]
            ifname = intf.get("ifName")
            sno = intf.get("serialNumber")

            if ifname and sno:
                key = (ifname.lower(), str(sno))
                self._replace_have_lookup.setdefault(key, []).append(item)

        for item in self.pb_input:
            ifname = item.get("ifname")
            sno = item.get("sno")
            fabric = item.get("fabric")

            if ifname and sno and fabric:
                key = (ifname.lower(), str(sno), fabric)
                self._replace_pb_input_lookup.setdefault(key, []).append(item)

    def dcnm_intf_get_underlay_policy_source(self, intf):

        underlay_policies = intf.get("underlayPolicies") or []

        for policy in underlay_policies:
            source = policy.get("source")
            if source:
                return source

        return None

    def dcnm_intf_capability_enabled(self, intf, capability):

        return str(intf.get(capability)).strip().lower() == "true"

    def dcnm_intf_skip_non_resolvable_deferred(self, intf):

        self.changed_dict[0]["skipped"].append(
            {
                "Name": intf["ifName"],
                "Alias": intf.get("alias"),
                "Deletable": intf.get("deletable"),
                "Underlay Policies": intf.get("underlayPolicies"),
                "Reason": "Non-deletable interface without resolvable underlay policy source",
            }
        )

    def dcnm_intf_skip_physical_default_not_allowed(self, intf):

        self.changed_dict[0]["skipped"].append(
            {
                "Name": intf["ifName"],
                "Alias": intf.get("alias"),
                "Deletable": intf.get("deletable"),
                "Edit Allowed": intf.get("editAllowed"),
                "Reason": (
                    "Physical interface reset is not allowed because neither "
                    "deletable nor editAllowed is true"
                ),
            }
        )

    def dcnm_intf_skip_edit_allowed_underlay_dependency(self, intf):

        self.changed_dict[0]["skipped"].append(
            {
                "Name": intf["ifName"],
                "Alias": intf.get("alias"),
                "Deletable": intf.get("deletable"),
                "Edit Allowed": intf.get("editAllowed"),
                "Underlay Policies": intf.get("underlayPolicies"),
                "Reason": (
                    "Physical interface reset through editAllowed was skipped "
                    "because its underlay policy source is not being deleted"
                ),
            }
        )

    def dcnm_intf_is_vpc_peer_link_port_channel(self, intf):

        if intf.get("ifType") != "INTERFACE_PORT_CHANNEL":
            return False

        alias = intf.get("alias")
        if alias is not None and "vpc-peer-link" in alias:
            return True

        underlay_policies = intf.get("underlayPolicies") or []
        for policy in underlay_policies:
            if (policy or {}).get("templateName") == "int_vpc_peer_link_po":
                return True

        return False

    def dcnm_intf_process_config(self, cfg):

        processed = []

        if cfg.get("switch", None) is None:
            return
        for sw in cfg["switch"]:

            sno = self.ip_sn[sw]

            if sno not in processed:
                processed.append(sno)

                # If the switch is part of VPC pair, then a GET on any serial number will fetch details of
                # both the switches. So check before adding to have_all

                if not any(
                    d.get("serialNo", None) == self.ip_sn[sw]
                    for d in self.have_all
                ):
                    self.dcnm_intf_get_have_all(sw)

    def dcnm_intf_get_diff_overridden(self, cfg):

        deploy = False
        self.diff_create = []
        self.diff_delete = [[], [], [], [], [], [], [], [], []]
        self.diff_delete_deploy = [[], [], [], [], [], [], [], [], []]
        self.diff_deploy = []
        self.diff_replace = []

        # If no config is included, delete/default all interfaces
        if cfg == []:
            # Since there is no 'config' block, then the 'deploy' flag at top level will be
            # used to determine the deploy behaviour
            deploy = self.module.params["deploy"]
            for address in self.ip_sn.keys():
                # the given switch may be part of a VPC pair. In that case we
                # need to get interface information using one switch which returns interfaces
                # from both the switches

                if not any(
                    d.get("serialNo", None) == self.ip_sn[address]
                    for d in self.have_all
                ):
                    self.dcnm_intf_get_have_all(address)
            # Without a config block the summary IS the scope of the sweep: a switch whose summary could not
            # be read authoritatively contributes no interface, and the run would end as a successful no-op
            # over state it never saw (or sweep only the readable switches). Refuse during planning, before
            # any configuration or deployment request; a valid empty summary still passes.
            for address in self.ip_sn.keys():
                self.dcnm_intf_require_summary_authority(self.ip_sn[address])
        else:
            # compute have_all for every switch included in 'cfg'.
            # 'deploy' flag will be picked from 'cfg' in case of state 'deleted' and from
            # top level in case of state 'overridden'

            if self.module.params["state"] == "overridden":
                deploy = self.module.params["deploy"]
            if self.module.params["state"] == "deleted":
                # NOTE: in case of state 'deleted' 'cfg' will have a single entry only.
                deploy = cfg[0].get("deploy")
            for config in cfg:
                self.dcnm_intf_process_config(config)
            if self.module.params["state"] == "overridden":
                # The switches of the request ARE the scope of this sweep, exactly as every switch is for an empty
                # config: an unreadable summary would make every interface of that switch look absent, so nothing outside the request
                # would be reset or deleted there and the run would report success over state it never saw. Refuse during planning.
                for config in cfg:
                    for sw in config.get("switch") or []:
                        if sw in self.ip_sn:
                            self.dcnm_intf_require_summary_authority(self.ip_sn[sw])

        del_list = []
        defer_list = []

        # Bulk pre-populate the interface detail cache for every switch
        # present in have_all.  This replaces N per-interface HTTP GETs
        # (inside dcnm_intf_get_intf_info) with at most S bulk GETs
        # (one per unique serial number), dramatically speeding up the
        # overridden diff computation for large interface counts.
        prefetch_identities = {}
        for h in self.have_all:
            sno = h["serialNo"]
            query_serial = self._dcnm_intf_query_serial(sno)
            if query_serial not in prefetch_identities or "~" in sno:
                prefetch_identities[query_serial] = sno
        for sno in sorted(
            prefetch_identities.values(), key=lambda value: "~" not in value
        ):
            self.dcnm_intf_bulk_fetch_intf_info(sno)

        # Pre-build O(1) lookup structures to replace linear scans.
        # want_set:  replaces match_want list comprehension over self.want
        # can_be_replaced lookups: replaces linear scan of self.pb_input
        want_set = set()
        for d in self.want:
            intf0 = d["interfaces"][0]
            want_set.add((
                intf0["ifName"].lower(),
                str(intf0["serialNumber"]),
                intf0["fabricName"],
            ))

        self.dcnm_intf_build_can_be_replaced_lookups()

        # Each peer's summary of a vPC pair lists the pair's own entries (the vPC parent, serial "S1~S2"), so a sweep over
        # both peers met the same vPC twice and queued it twice for deletion and deploy. One identity (serial or pair + name) is
        # decided once; nothing else changes.
        swept = set()
        for have in self.have_all:

            delem = {}
            name = have["ifName"]
            sno = have["serialNo"]
            fabric = have["fabricName"]
            identity = (str(self._dcnm_intf_authority_key(sno) or sno).casefold(), str(name).lower(), fabric)
            if identity in swept:
                continue
            swept.add(identity)

            # Check if this interface type is to be overridden.
            if self.module.params["override_intf_types"] != []:
                # Check if it is SUBINTERFACE. For sub-interfaces ifType will be retuened as INTERFACE_ETHERNET. So
                # for such interfaces, check if SUBINTERFACE is included in override list instead of have['ifType']
                if (have["ifType"] == "INTERFACE_ETHERNET") and (
                    (str(have["isPhysical"]).lower() == "none")
                    or (str(have["isPhysical"]).lower() == "false")
                ):
                    # This is a SUBINTERFACE.
                    if (
                        "SUBINTERFACE"
                        not in self.module.params["override_intf_types"]
                    ):
                        continue
                else:
                    if (
                        have["ifType"]
                        not in self.module.params["override_intf_types"]
                    ):
                        continue

            # The authority gate deliberately does NOT run here. ``have_all`` enumerates every
            # interface on every switch, and the two blocks below act on a subset of it:
            # INTERFACE_MGMT matches neither, so mgmt0 is never created, deleted, reset or
            # deployed by an override sweep. Gating the enumeration made an unreadable switch
            # fail on the first interface walked -- typically mgmt0 -- naming an interface the
            # sweep was never going to touch, and hiding which one actually lacked state. The
            # gate now runs at each point that decides a mutation, so it guards exactly what it
            # is meant to guard and reports the interface really at stake.

            if (have["ifType"] == "INTERFACE_ETHERNET") and (
                (str(have["isPhysical"]).lower() != "none")
                and (str(have["isPhysical"]).lower() == "true")
            ):

                # deleteReason is consumed only here, and only when an alias makes the decision depend on it.
                # An absent key (not null) is insufficient information: refuse during planning, before anything is sent.
                if have["alias"] != "" and "deleteReason" not in have:
                    self.module.fail_json(
                        msg="Interface {0} on {1} has an alias but the controller did not provide deleteReason, "
                        "so it cannot be decided whether the interface may be reset or deleted. Refusing to "
                        "reset or delete it; no change was sent.".format(name, sno)
                    )
                if have["alias"] != "" and have["deleteReason"] is not None:
                    self.changed_dict[0]["skipped"].append(
                        {
                            "Name": name,
                            "Alias": have["alias"],
                            "Delete Reason": have["deleteReason"],
                        }
                    )
                    continue

                # Skip TOR uplink member interfaces
                if have.get("underlayPolicies") is not None:
                    is_tor_member = False
                    for policy in have.get("underlayPolicies"):
                        if policy.get("templateName") in ["int_vpc_uplink_access_po_member"]:
                            is_tor_member = True
                            break

                    if is_tor_member:
                        self.changed_dict[0]["skipped"].append(
                            {
                                "Name": name,
                                "Alias": have["alias"],
                                "Reason": "TOR uplink member interface",
                            }
                        )
                        continue

                is_deleted = self.module.params["state"] == "deleted"
                deletable = self.dcnm_intf_capability_enabled(
                    have, "deletable"
                )
                edit_allowed = self.dcnm_intf_capability_enabled(
                    have, "editAllowed"
                )

                # A bulk deleted request must make the same fail-closed
                # capability decision as a named deleted request. Missing or
                # unrecognized controller metadata is not authorization to
                # reset a physical interface.
                if is_deleted and not deletable and not edit_allowed:
                    self.dcnm_intf_skip_physical_default_not_allowed(have)
                    continue

                raw_deletable_is_false = (
                    str(have.get("deletable")).strip().lower() == "false"
                )
                needs_dependency_handling = (
                    not deletable
                    if is_deleted
                    else raw_deletable_is_false
                )

                if needs_dependency_handling:
                    source = self.dcnm_intf_get_underlay_policy_source(have)

                    if source is not None:
                        # Add this 'have to a deferred list. We will process this list once we have processed all the 'haves'
                        defer_list.append(have)
                        self.changed_dict[0]["deferred"].append(
                            {
                                "Name": name,
                                "Deletable": have.get("deletable"),
                                "Underlay Policies": have["underlayPolicies"],
                                "Source": source,
                            }
                        )
                        continue

                    # Physical Ethernet interfaces are never deleted; in
                    # 'overridden' state they are reset to the role-based host
                    # default policy (int_trunk_host for leaf, int_routed_host
                    # otherwise). 'deletable' is inherently false for such
                    # ports, so it must not by itself block an overridden reset.
                    # Fabric-managed interfaces (uplinks / VPC members) are
                    # already deferred above via a non-empty underlay policy
                    # source; reaching this point means the source is empty.
                    # Skip only when edits are not allowed; otherwise fall
                    # through and reset to default just like state 'deleted'.
                    if not is_deleted and not edit_allowed:
                        self.dcnm_intf_skip_non_resolvable_deferred(have)
                        continue

                uelem = self.dcnm_intf_get_default_eth_payload(
                    name, sno, fabric
                )
                # Before we add the interface to replace list, check if the default payload is same as
                # what is already present. If both are same, skip the interface.
                # So during idempotence, we may add the same interface again if we don't compare

                intf = self.dcnm_intf_get_intf_info(
                    have["ifName"], have["serialNo"], have["ifType"]
                )
                self.dcnm_intf_require_detail_authority(
                    have["ifName"], have["serialNo"]
                )
                if intf == []:
                    # In case of LANClassic fabrics, a GET on policy details for Ethernet interfaces will return [] since
                    # these interfaces dont have any policies configured by default. In that case there is nothing to be done
                    continue

                # Registered drift counts as drift; applied below only if the reset is queued.
                reg_resets, reg_blocked = self.dcnm_intf_default_registered_resets(uelem, intf)
                if (
                    not (reg_resets or reg_blocked)
                    and self.dcnm_compare_default_payload(uelem, intf)
                    == "DCNM_INTF_MATCH"
                ):
                    # In case of breakout, check if parent interface is in cfg
                    # If a match for Ethernet1/x/y is found, verify if the parent interface Ethernet1/x exists in cfg.
                    # If the parent doesn't exist or isn't of type "breakout", remove the breakout interface.
                    if re.search(r"\d+\/\d+\/\d+", name):
                        found, parent_type = self.dcnm_intf_get_parent(name, have['mgmtIpAddress'])
                        if not (found and parent_type == "breakout"):
                            payload = {
                                "serialNumber": have["serialNo"],
                                "ifName": have["ifName"]
                            }
                            breakout_index = self.int_index[self.int_types["breakout"]]
                            self.diff_delete[breakout_index].append(payload)
                            self.changed_dict[0]["deleted"].append(copy.deepcopy(payload))
                    continue

                if uelem is not None:
                    # Before defaulting ethernet interfaces, check if this interface is present in want.
                    # If yes, ignore the interface, because configuration from want will be applied anyway.
                    # This ensures that Ethernet interfaces removed from the playbook config are reset to default,
                    # while those still in the config are left alone to be configured later.
                    in_want = (name.lower(), str(sno), fabric) in want_set

                    # Only default/reset this interface if it's NOT in the playbook config
                    if not in_want:
                        # Before defaulting ethernet interfaces, check if they are
                        # member of any port-channel. If so, do not default that
                        rc, intf = self.dcnm_intf_can_be_replaced(have)
                        if rc is True:
                            self.dcnm_intf_queue_default_registered_resets(
                                uelem, reg_resets, reg_blocked
                            )
                            self.dcnm_intf_merge_intf_info(
                                uelem, self.diff_replace
                            )
                            self.changed_dict[0]["replaced"].append(
                                copy.deepcopy(uelem)
                            )
                            delem["serialNumber"] = sno
                            delem["ifName"] = name
                            delem["fabricName"] = self.fabric
                            if str(deploy).lower() == "true":
                                # Do not create interface E1/x/y, interface is created with breakout
                                pattern = r'^Ethernet1/\d+/\d+$'
                                if_name = delem.get('ifName')

                                if not re.match(pattern, if_name):
                                    self.diff_deploy.append(delem)
                                    self.changed_dict[0]["deploy"].append(
                                        copy.deepcopy(delem)
                                    )
            # Sub-interafces are returned as INTERFACE_ETHERNET in have_all. So do an
            # additional check to see if it is physical. If not assume it to be sub-interface
            # for now. We will have to re-visit this check if there are additional non-physical
            # interfaces which have the same ETHERNET interafce type. For e.g., FEX ports

            if (
                (have["ifType"] == "INTERFACE_PORT_CHANNEL")
                or (have["ifType"] == "INTERFACE_LOOPBACK")
                or (have["ifType"] == "SUBINTERFACE")
                or (have["ifType"] == "INTERFACE_VPC")
                or (have["ifType"] == "INTERFACE_VLAN")
                or (have["ifType"] == "STRAIGHT_TROUGH_FEX")
                or (have["ifType"] == "AA_FEX")
                or (
                    (have["ifType"] == "INTERFACE_ETHERNET")
                    and (
                        (str(have["isPhysical"]).lower() == "none")
                        or (str(have["isPhysical"]).lower() == "false")
                    )
                )
            ):
                # Certain interfaces cannot be deleted, so check before deleting. But if the interface has been marked for delete,
                # we still go in and check if need to deploy.
                if (
                    str(have.get("deletable")).lower() == "true"
                    or str(have["markDeleted"]).lower() == "true"
                ):
                    # Port-channel which are created as part of VPC peer link should not be deleted
                    if have["ifType"] == "INTERFACE_PORT_CHANNEL":
                        if self.dcnm_intf_is_vpc_peer_link_port_channel(have):
                            self.changed_dict[0]["skipped"].append(
                                {
                                    "Name": name,
                                    "Alias": have["alias"],
                                    "Underlay Policies": have[
                                        "underlayPolicies"
                                    ],
                                }
                            )
                            continue
                        # Port-channel which are created as part of TOR uplink should not be deleted
                        # This includes both TOR-side and leaf-side port-channels:
                        # - TOR side: "tor-connected-to-vPC-leaf:" or "tor-connected-to-leaf:"
                        # - Leaf side: "leaf-connected-to-vPC-tor:" or "leaf-connected-to-tor:"
                        if have.get("alias") is not None and (
                            "tor-connected-to" in have.get("alias")
                            or "leaf-connected-to-vPC-tor" in have.get("alias")
                            or "leaf-connected-to-tor" in have.get("alias")
                        ):
                            self.changed_dict[0]["skipped"].append(
                                {
                                    "Name": name,
                                    "Alias": have["alias"],
                                    "Underlay Policies": have[
                                        "underlayPolicies"
                                    ],
                                }
                            )
                            continue
                        # Also check if port-channel uses TOR uplink templates
                        skip_pc = False
                        if have.get("underlayPolicies") is not None:
                            tor_uplink_templates = [
                                "int_vpc_uplink_access_po",
                                "int_port_channel_uplink_access",
                            ]
                            for policy in have.get("underlayPolicies"):
                                if policy.get("templateName") in tor_uplink_templates:
                                    self.changed_dict[0]["skipped"].append(
                                        {
                                            "Name": name,
                                            "Alias": have["alias"],
                                            "Underlay Policies": have[
                                                "underlayPolicies"
                                            ],
                                            "Skip Reason": "TOR uplink port-channel (template match)",
                                        }
                                    )
                                    skip_pc = True
                                    break
                        if skip_pc:
                            continue
                        else:
                            self.changed_dict[0]["debugs"].append(
                                {
                                    "Name": name,
                                    "Alias": have["alias"],
                                    "Underlay Policies": have[
                                        "underlayPolicies"
                                    ],
                                }
                            )

                    # TOR uplink vPC interfaces should NEVER be deleted through interface override.
                    # TOR uplink vPCs are auto-generated by NDFC when TOR switches are paired
                    # with leaf switches. These vPC interfaces (vPC1, vPC2, etc.) represent
                    # the uplink bundle between TOR and leaf switches.
                    #
                    # TOR uplink vPCs can be identified by:
                    # - ifType: INTERFACE_VPC
                    # - underlayPolicies templateName starting with "int_vpc_uplink_"
                    # - alias patterns: "tor-connected-to", "leaf-connected-to-vPC-tor"
                    if have.get("ifType") == "INTERFACE_VPC":
                        is_tor_uplink = False

                        # Check alias patterns for TOR uplinks
                        if have.get("alias") is not None and (
                            "tor-connected-to" in have.get("alias")
                            or "leaf-connected-to-vPC-tor" in have.get("alias")
                            or "leaf-connected-to-tor" in have.get("alias")
                        ):
                            is_tor_uplink = True

                        # Check underlayPolicies templateName for TOR uplink patterns
                        if not is_tor_uplink and have.get("underlayPolicies"):
                            for policy in have["underlayPolicies"]:
                                template_name = policy.get("templateName", "")
                                if template_name and template_name.startswith("int_vpc_uplink_"):
                                    is_tor_uplink = True
                                    break

                        if is_tor_uplink:
                            self.changed_dict[0]["skipped"].append(
                                {
                                    "Name": name,
                                    "Alias": have["alias"],
                                    "Underlay Policies": have["underlayPolicies"],
                                    "Reason": "TOR uplink vPC interface",
                                }
                            )
                            continue

                    # Interfaces sometimes take time to get deleted from DCNM. Such interfaces will have
                    # underlayPolicies set to "None". Such interfaces need not be deleted again

                    if have.get("underlayPolicies") is None:
                        self.changed_dict[0]["skipped"].append(
                            {
                                "Name": name,
                                "Alias": have["alias"],
                                "Underlay Policies": have["underlayPolicies"],
                            }
                        )
                        continue

                    # For interfaces that are matching, leave them alone. We will overwrite the config anyway
                    # For all other interfaces, if they are PC, vPC, SUBINT, LOOPBACK, delete them.

                    # Check if this interface is present in want. If yes, ignore the interface, because all
                    # configuration from want will be added to create anyway

                    in_want = (name.lower(), str(sno), fabric) in want_set
                    if not in_want:

                        # This interface is about to be deleted and possibly deployed. That is
                        # the mutation this gate exists for, so it runs here rather than over
                        # the enclosing enumeration.
                        self.dcnm_intf_require_detail_authority(name, sno)

                        delem = {}

                        delem["interfaceDbId"] = 0
                        delem["interfaceType"] = have["ifType"]
                        delem["ifName"] = name
                        delem["serialNumber"] = sno
                        delem["fabricName"] = fabric
                        pvlan_lifecycle_note(self, "delete_requested_deploy", (sno, str(name).lower()), str(deploy).lower() == "true")
                        if str(have["markDeleted"]).lower() == "true":
                            pvlan_lifecycle_note(self, "marked_delete_requests", (sno, str(name).lower()), {
                                "deploy": str(deploy).lower() == "true", "entry": copy.deepcopy(have)})

                        # have_all will include interfaces which are marked for DELETE too. Do not delete them again.
                        if str(have["markDeleted"]).lower() == "false":
                            self.diff_delete[
                                self.int_index[have["ifType"]]
                            ].append(delem)
                            self.changed_dict[0]["deleted"].append(
                                copy.deepcopy(delem)
                            )
                            del_list.append(have)

                        if str(deploy).lower() == "true":
                            if (have["complianceStatus"] == "In-Sync") or (
                                have["complianceStatus"] == "Pending"
                            ):
                                self.diff_delete_deploy[
                                    self.int_index[have["ifType"]]
                                ].append(delem)
                                self.changed_dict[0]["delete_deploy"].append(
                                    copy.deepcopy(delem)
                                )

        for intf in defer_list:
            # Check if the 'source' for the ethernet interface is one of the interfaces that is already deleted.
            # If so you can default/reset this ethernet interface also

            delem = {}
            sno = intf["serialNo"]
            fabric = intf["fabricName"]
            name = self.dcnm_intf_get_underlay_policy_source(intf)

            if name is None:
                self.dcnm_intf_skip_non_resolvable_deferred(intf)
                continue

            match = [
                d
                for d in del_list
                if (
                    (name.lower() == d["ifName"].lower())
                    and (sno in d["serialNo"])
                    and (fabric == d["fabricName"])
                )
            ]
            if match:

                # Deferred interfaces leave the main loop before its own gate, so this is the
                # first point at which their state is used for a mutation. Without this the
                # deferred reset path would run over state the controller never confirmed.
                self.dcnm_intf_require_detail_authority(intf["ifName"], sno)

                uelem = self.dcnm_intf_get_default_eth_payload(
                    intf["ifName"], sno, fabric
                )
                # The deferred reset also withdraws the registered fields HAVE still holds.
                self.dcnm_intf_queue_default_registered_resets(
                    uelem,
                    *self.dcnm_intf_default_registered_resets(
                        uelem, self.dcnm_intf_get_intf_info(intf["ifName"], sno, intf["ifType"])
                    )
                )

                self.dcnm_intf_merge_intf_info(uelem, self.diff_replace)
                self.changed_dict[0]["replaced"].append(copy.deepcopy(uelem))
                delem["serialNumber"] = sno
                delem["ifName"] = intf["ifName"]
                delem["fabricName"] = self.fabric

                # Deploy only if requested for
                if str(deploy).lower() == "true":
                    self.diff_deploy.append(delem)
                    self.changed_dict[0]["deploy"].append(copy.deepcopy(delem))

        self.dcnm_intf_compare_want_and_have("overridden")

    def dcnm_intf_get_diff_deleted(self):

        self.diff_create = []
        self.diff_delete = [[], [], [], [], [], [], [], [], []]
        self.diff_delete_deploy = [[], [], [], [], [], [], [], [], []]
        self.diff_deploy = []
        self.diff_replace = []
        self.deferred_delete_member_defaults = []
        self._deferred_delete_member_default_keys = set()

        if self.config == []:
            # Now that we have all the interface information we can run override
            # and delete or reset interfaces.
            self.dcnm_intf_get_diff_overridden(self.config)
        elif self.config:
            # Bulk pre-populate the interface detail cache for every switch
            # referenced in the config.  This replaces N per-interface HTTP
            # GETs (inside dcnm_intf_get_intf_info) with at most S bulk GETs
            # (one per unique serial number), dramatically speeding up the
            # deleted diff computation for large interface counts.
            prefetch_identities = {}
            for cfg in self.config:
                if cfg.get("name") is None:
                    continue
                switches = cfg.get("switch", None)
                if switches is None:
                    switches = list(self.ip_sn.keys())
                for sw in switches:
                    # VPC/AA_FEX interfaces use vpc_ip_sn for lookups.
                    # Pre-split the combined serial (e.g. "FOX~SAL") and
                    # prefetch the first part so those lookups hit cache.
                    name_lower = cfg.get("name", "")[0:3].lower()
                    if name_lower == "vpc" and sw in self.vpc_ip_sn:
                        sno = self.vpc_ip_sn[sw]
                    elif sw in self.ip_sn:
                        sno = self.ip_sn[sw]
                    else:
                        continue
                    query_serial = self._dcnm_intf_query_serial(sno)
                    if query_serial not in prefetch_identities or "~" in sno:
                        prefetch_identities[query_serial] = sno

            for sno in sorted(
                prefetch_identities.values(), key=lambda value: "~" not in value
            ):
                self.dcnm_intf_bulk_fetch_intf_info(sno, refresh=True)

            for cfg in self.config:
                if cfg.get("name", None) is not None and cfg.get("type") == "breakout":
                    self.dcnm_intf_get_have_all(cfg["switch"][0])

                    for have in self.have_all:
                        have_intf = have['ifName']
                        deletable = have['deletable']
                        if re.search(r"\d+\/\d+\/\d+", have_intf):
                            found, parent_type = self.dcnm_intf_get_parent(have_intf, have['mgmtIpAddress'])
                            # If have in want breakout and if match to E1/x/1 add to dict
                            # Else if match E1/x/2, etc. silently ignore, because we delete the breakout
                            # with the first sub if.
                            if re.search(r"\d+\/\d+\/1$", have_intf) and found:
                                if deletable is False:
                                    self.changed_dict[0]["skipped"].append(
                                        {
                                            "Name": have_intf,
                                            "Alias": have.get("alias"),
                                            "Delete Reason": have["deleteReason"] if "deleteReason" in have else "not provided by controller",
                                        }
                                    )
                                    continue
                                payload = {'serialNumber': have['serialNo'],
                                           'ifName': have['ifName']}
                                self.diff_delete_breakout.append(payload)
                elif cfg.get("name", None) is not None:
                    processed = []
                    have_all = []

                    # If interface name alone is given, then delete or reset the
                    # interface on all switches in the fabric
                    switches = cfg.get("switch", None)

                    if switches is None:
                        switches = self.ip_sn.keys()
                    else:
                        switches = cfg["switch"]

                    for sw in switches:

                        intf = {}
                        delem = {}

                        if_name, if_type = self.dcnm_extract_if_name(cfg)

                        # Check if the interface is present in DCNM
                        intf["interfaceType"] = if_type
                        if if_type == "INTERFACE_VPC":
                            intf["serialNumber"] = self.vpc_ip_sn[sw]
                        else:
                            intf["serialNumber"] = self.ip_sn[sw]
                        intf["ifName"] = if_name

                        if intf["serialNumber"] not in processed:
                            processed.append(intf["serialNumber"])
                        else:
                            continue

                        # Ethernet interfaces cannot be deleted
                        if if_type == "INTERFACE_ETHERNET":

                            if sw not in have_all:
                                have_all.append(sw)
                                self.dcnm_intf_get_have_all(sw)

                            # Get the matching interface from have_all
                            match_have = [
                                have
                                for have in self.have_all
                                if (
                                    (
                                        intf["ifName"].lower()
                                        == have["ifName"].lower()
                                    )
                                    and (
                                        intf["serialNumber"]
                                        == have["serialNo"]
                                    )
                                )
                            ][0]
                            if (
                                match_have
                                and (
                                    str(match_have["isPhysical"]).lower()
                                    != "none"
                                )
                                and (
                                    str(match_have["isPhysical"]).lower()
                                    == "true"
                                )
                            ):

                                deletable = self.dcnm_intf_capability_enabled(
                                    match_have, "deletable"
                                )
                                edit_allowed = self.dcnm_intf_capability_enabled(
                                    match_have, "editAllowed"
                                )
                                if not deletable and not edit_allowed:
                                    self.dcnm_intf_skip_physical_default_not_allowed(
                                        match_have
                                    )
                                    continue

                                using_edit_allowed = (
                                    not deletable and edit_allowed
                                )
                                uelem = self.dcnm_intf_get_default_eth_payload(
                                    intf["ifName"],
                                    intf["serialNumber"],
                                    self.fabric,
                                )
                                intf_payload = self.dcnm_intf_get_intf_info_from_dcnm(
                                    intf
                                )
                                self.dcnm_intf_require_detail_authority(
                                    intf["ifName"], intf["serialNumber"]
                                )

                                # Before we add the interface to replace list, check if the default payload is same as
                                # what is already present. If both are same, skip the interface. This is required specifically
                                # for ethernet interfaces because they don't actually get deleted. they will only be defaulted.
                                # So during idempotence, we may add the same interface again if we don't compare
                                # Registered drift counts as drift; applied below only if the
                                # reset is queued here (not for a deferred former member).
                                reg_resets, reg_blocked = self.dcnm_intf_default_registered_resets(
                                    uelem, intf_payload if intf_payload != [] else None
                                )
                                if intf_payload != []:
                                    if (
                                        not (reg_resets or reg_blocked)
                                        and self.dcnm_compare_default_payload(
                                            uelem, intf_payload
                                        )
                                        == "DCNM_INTF_MATCH"
                                    ):
                                        continue

                                if uelem is not None:
                                    # Before defaulting ethernet interfaces, check if they are
                                    # member of any port-channel. If so, do not default that
                                    rc, iface = self.dcnm_intf_can_be_replaced(
                                        match_have
                                    )
                                    if rc is True:
                                        defer_member_default = (
                                            self.dcnm_intf_should_defer_deleted_member_default(
                                                match_have, iface
                                            )
                                        )
                                        source = (
                                            self.dcnm_intf_get_underlay_policy_source(
                                                match_have
                                            )
                                        )
                                        if (
                                            using_edit_allowed
                                            and source is not None
                                            and not defer_member_default
                                        ):
                                            self.dcnm_intf_skip_edit_allowed_underlay_dependency(
                                                match_have
                                            )
                                            continue
                                        if defer_member_default:
                                            self.dcnm_intf_defer_deleted_member_default(
                                                intf["ifName"],
                                                intf["serialNumber"],
                                                self.fabric,
                                                cfg.get("deploy", "true"),
                                                iface,
                                            )
                                            continue
                                        self.dcnm_intf_queue_default_registered_resets(
                                            uelem, reg_resets, reg_blocked
                                        )
                                        self.dcnm_intf_merge_intf_info(
                                            uelem, self.diff_replace
                                        )
                                        self.changed_dict[0][
                                            "replaced"
                                        ].append(copy.deepcopy(uelem))
                                        if (
                                            str(
                                                cfg.get("deploy", "true")
                                            ).lower()
                                            == "true"
                                        ):
                                            delem["serialNumber"] = intf[
                                                "serialNumber"
                                            ]
                                            delem["ifName"] = if_name
                                            delem["fabricName"] = self.fabric
                                            self.diff_deploy.append(delem)
                        else:
                            intf_payload = self.dcnm_intf_get_intf_info_from_dcnm(
                                intf
                            )
                            self.dcnm_intf_require_detail_authority(
                                intf["ifName"], intf["serialNumber"]
                            )

                            if intf_payload != []:
                                delem["ifName"] = if_name
                                delem["serialNumber"] = intf["serialNumber"]

                                self.diff_delete[
                                    self.int_index[if_type]
                                ].append(delem)
                                self.changed_dict[0]["deleted"].append(
                                    copy.deepcopy(delem)
                                )
                                pvlan_lifecycle_note(self, "delete_requested_deploy", (intf["serialNumber"], str(if_name).lower()),
                                                     str(cfg.get("deploy", "true")).lower() == "true")

                                if "monitor" not in intf_payload["policy"]:
                                    if (
                                        str(cfg.get("deploy", "true")).lower()
                                        == "true"
                                    ):
                                        self.diff_delete_deploy[
                                            self.int_index[if_type]
                                        ].append(delem)
                                        self.changed_dict[0][
                                            "delete_deploy"
                                        ].append(copy.deepcopy(delem))
                            else:
                                # Get Interface details which will include even interfaces that are marked for delete.
                                if sw not in have_all:
                                    have_all.append(sw)
                                    self.dcnm_intf_get_have_all(sw)

                                # Get the matching interface from have_all
                                match_have = [
                                    have
                                    for have in self.have_all
                                    if (
                                        (
                                            intf["ifName"].lower()
                                            == have["ifName"].lower()
                                        )
                                        and (
                                            intf["serialNumber"]
                                            == have["serialNo"]
                                        )
                                    )
                                ]

                                if if_type == "INTERFACE_VPC" and (not match_have or str(match_have[0].get("markDeleted")).lower() == "true"):
                                    # A vPC whose deletion was saved is either no longer listed or (measured) still listed
                                    # as marked for deletion without any policy; its children carry the marking.
                                    pvlan_lifecycle_note(self, "vpc_named_resume_requests", (intf["serialNumber"], str(if_name).lower()), {
                                        "deploy": str(cfg.get("deploy", "true")).lower() == "true", "name": if_name})
                                if match_have and str(match_have[0].get("markDeleted")).lower() == "true":
                                    pvlan_lifecycle_note(self, "marked_delete_requests", (intf["serialNumber"], str(if_name).lower()), {
                                        "deploy": str(cfg.get("deploy", "true")).lower() == "true",
                                        "entry": copy.deepcopy(match_have[0])})
                                if match_have:
                                    # Matching interface found. Check 'complianceStatus' and deploy if necessary
                                    if (
                                        match_have[0]["complianceStatus"]
                                        == "In-Sync"
                                    ) or (
                                        match_have[0]["complianceStatus"]
                                        == "Pending"
                                    ):
                                        if (
                                            str(
                                                cfg.get("deploy", "true")
                                            ).lower()
                                            == "true"
                                        ):
                                            delem["ifName"] = if_name
                                            delem["serialNumber"] = intf[
                                                "serialNumber"
                                            ]
                                            self.diff_delete_deploy[
                                                self.int_index[if_type]
                                            ].append(delem)
                                            self.changed_dict[0][
                                                "delete_deploy"
                                            ].append(copy.deepcopy(delem))
                else:
                    self.dcnm_intf_get_diff_overridden([cfg])

    def dcnm_extract_if_name(self, cfg):

        if cfg["name"][0:2].lower() == "po":
            if_name, port_id = self.dcnm_intf_get_if_name(cfg["name"], "pc")
            if_type = "INTERFACE_PORT_CHANNEL"
        elif cfg["name"][0:2].lower() == "lo":
            if_name, port_id = self.dcnm_intf_get_if_name(cfg["name"], "lo")
            if_type = "INTERFACE_LOOPBACK"
        elif cfg["name"][0:3].lower() == "eth":
            if "." not in cfg["name"]:
                if_name, port_id = self.dcnm_intf_get_if_name(
                    cfg["name"], "eth"
                )
                if_type = "INTERFACE_ETHERNET"
            else:
                if_name, port_id = self.dcnm_intf_get_if_name(
                    cfg["name"], "sub_int"
                )
                if_type = "SUBINTERFACE"
        elif cfg["name"][0:3].lower() == "vpc":
            if_name, port_id = self.dcnm_intf_get_if_name(cfg["name"], "vpc")
            if_type = "INTERFACE_VPC"
        elif cfg["name"][0:4].lower() == "vlan":
            if_name, port_id = self.dcnm_intf_get_if_name(cfg["name"], "svi")
            if_type = "INTERFACE_VLAN"
        else:
            if_name = ""
            if_type = ""
        return if_name, if_type

    def dcnm_intf_get_diff_query(self):

        for info in self.intf_info:
            sno = self.ip_sn[info["switch"][0]]
            if info["name"] == "":
                # GET all interfaces
                path = self.paths["IF_DETAIL_WITH_SNO"].format(sno)
            else:
                ifname, if_type = self.dcnm_extract_if_name(info)
                # GET a specific interface
                path = self.paths["IF_WITH_SNO_IFNAME"].format(sno, ifname)

            resp = dcnm_send(self.module, "GET", path)

            if "DATA" in resp and resp["DATA"]:
                self.diff_query.extend(resp["DATA"])
        self.changed_dict[0]["query"].extend(self.diff_query)
        # query never builds a HAVE, so this is its only chance: the controller's nvPairs
        # go straight into the task result.
        self.dcnm_intf_register_controller_secrets(self.diff_query)
        self.result["response"].extend(self.diff_query)

    def dcnm_parse_response(self, resp):

        failed = False

        succ_resp = {
            "DATA": {},
            "MESSAGE": "OK",
            "METHOD": "POST",
            "REQUEST_PATH": "",
            "RETURN_CODE": 200,
        }

        # Get a list of entities from the deploy. We will have to check
        # all the responses before we declare changed as True or False

        entities = self.dcnm_intf_get_entities_list(self.diff_deploy)

        ent_resp = {}
        for ent in entities:

            ent_resp[ent] = "No Error"
            if isinstance(resp["DATA"], list):
                for data in resp["DATA"]:
                    host = data.get("entity")

                    if host:
                        host = host.split(":")[0]
                        if self.hn_sn.get(host) == ent:
                            ent_resp[ent] = data.get("message")
                    else:
                        ent_resp[ent] = "No Error"
            elif isinstance(resp["DATA"], str):
                ent_resp[ent] = resp["DATA"]

        succ_resp["ORIG_MSG"] = []
        for ent in entities:
            if ent_resp[ent] == "No Error":
                continue
            elif (
                ("No Commands to execute" in ent_resp[ent])
                or (ent_resp[ent] == "Failed to fetch policies")
                or (ent_resp[ent] == "Failed to fetch switch configuration")
                or (ent_resp[ent] == "In-Sync")
            ):
                # Consider this case as success.
                succ_resp["REQUEST_PATH"] = resp["REQUEST_PATH"]
                succ_resp["MESSAGE"] = "OK"
                succ_resp["METHOD"] = resp["METHOD"]
                succ_resp["ORIG_MSG"].append(ent_resp[ent])
                succ_resp["RETURN_CODE"] = 200
            else:
                failed = True
                break

        if failed:
            return resp, False
        else:
            return succ_resp, False

    def dcnm_intf_send_message_handle_retry(self, action, path, payload, cmd):

        count = 1
        while count < 20:

            resp = dcnm_send(self.module, action, path, payload)

            # No commands to execute is normal when you try to deploy/delete an
            # interface to switch and there is no change.
            # Consider that as success and mark the change flag as 'False; to indicate
            # nothinbg actually changed

            if (resp.get("MESSAGE") == "OK") and (
                resp.get("RETURN_CODE") == 200
            ):
                return resp, True

            presp, changed = self.dcnm_parse_response(resp)
            resp = presp

            count = count + 1
            time.sleep(0.1)

        return resp, False

    def dcnm_intf_get_entities_list(self, deploy):

        sn_list = []
        usno = []

        [
            [sn_list.append(v) for k, v in d.items() if k == "serialNumber"]
            for d in deploy
        ]

        # For vPC cases, serial numbers will be a combined one. But deploy responses from the DCNM
        # controller will be based on individual switches. So we will have to split up the serial
        # numbers into individual serial numbers and add to the list

        ulist = set(sn_list)

        vpc = False
        for num in ulist:
            if "~" in num:
                vpc = True
                slist = num.split("~")
                usno.append(slist[0])
                usno.append(slist[1])

        if vpc is True:
            ulist = usno
        return ulist

    def dcnm_intf_check_deployment_status(self, deploy_list):

        # Check for deployment status of all the configured objects only if the check_deploy flag is set.
        if self.module.params["check_deploy"] is False:
            return

        path = self.paths["GLOBAL_IF_DEPLOY"]

        resp = {}

        for item in deploy_list:
            retries = 0
            while retries < 60:
                retries += 1
                name = item["ifName"]
                sno = item["serialNumber"]
                self.dcnm_intf_require_summary_authority(sno)

                match_have = [
                    have
                    for have in self.have_all
                    if (
                        (name.lower() == have["ifName"].lower())
                        and (sno == have["serialNo"])
                        and (self.fabric == have["fabricName"])
                    )
                ]
                if match_have:

                    if match_have[0]["complianceStatus"] == "In-Sync":
                        break

                    if retries == 10 or retries == 20:
                        # PVLAN: fresh authority before EVERY retry; a verified convergence
                        # drops the target and no retry is sent. Non-PVLAN items pass through.
                        retry_items = self.dcnm_intf_pvlan_deploy_gate(
                            [{"ifName": name, "serialNumber": sno, "fabricName": self.fabric}],
                            "deployment_status_retry", True,
                        )
                        if retry_items:
                            json_payload = json.dumps(
                                {
                                    "ifName": name,
                                    "serialNumber": sno,
                                    "fabricName": self.fabric,
                                }
                            )
                            resp = dcnm_send(
                                self.module, "POST", path, json_payload
                            )
                            self.dcnm_intf_pvlan_deploy_attempt(
                                retry_items, "deployment_status_retry", resp, True
                            )

                    time.sleep(5)
                    self.have_all = []
                    if not self.dcnm_intf_get_have_all_with_sno(sno):
                        self.dcnm_intf_require_summary_authority(sno)
                else:
                    # For merge state, the interfaces would have been created just now. Fetch them again before checking
                    self.have_all = []
                    if not self.dcnm_intf_get_have_all_with_sno(sno):
                        self.dcnm_intf_require_summary_authority(sno)
            if (
                match_have == []
                or match_have[0]["complianceStatus"] != "In-Sync"
            ):
                self.module.fail_json(
                    msg={
                        "FAILURE REASON": "Interafce "
                        + name
                        + " did not reach 'In-Sync' State",
                        "Compliance Status": match_have[0]["complianceStatus"],
                        # "CHANGED": self.changed_dict,
                        # "RESP": resp
                        "RESULT": self.result,
                    }
                )

    @staticmethod
    def dcnm_intf_collect_batch_errors(resp):
        """Return the per-item ERROR entries of a Multi-Status response, or [].

        A 207 reports the outcome of EACH item in ``DATA``; the HTTP status only says the
        batch was processed. Only ``reportItemType == "ERROR"`` is treated as a failure:
        ``WARNING`` carries benign notices (the deploy call answers "No Commands to execute.
        In-Sync" that way) and an unrecognised type is deliberately ignored, so this can
        never turn a currently-working run into a failure on an item shape we have not seen.

        Fail-safe on anything unexpected: a ``DATA`` that is not a list of dicts yields [],
        because a malformed body is not evidence of a rejected item.
        """
        data = resp.get("DATA") if isinstance(resp, dict) else None
        if not isinstance(data, list):
            return []
        return [
            item
            for item in data
            if isinstance(item, dict)
            and str(item.get("reportItemType", "")).upper() == "ERROR"
        ]

    @staticmethod
    def dcnm_intf_format_batch_error(resp, failed_items):
        """Build the failure message for a partially or wholly rejected batch.

        Naming what SUCCEEDED matters as much as naming what failed. The controller applies
        a batch item by item, so a mixed response leaves real state behind; failing without
        saying which items landed would leave the operator worse off than the silent success
        this replaces -- they would know something broke but not what to reconcile.
        """
        def label(item):
            entity = item.get("entity") or "<unknown entity>"
            return "  %s: %s" % (entity, item.get("message") or "<no message>")

        data = resp.get("DATA") if isinstance(resp, dict) else []
        applied = [
            item.get("entity")
            for item in (data if isinstance(data, list) else [])
            if isinstance(item, dict)
            and str(item.get("reportItemType", "")).upper() == "SUCCESS"
            and item.get("entity")
        ]

        lines = [
            "The controller rejected %d item(s) in the interface batch update. "
            "The batch answered HTTP %s, but that status only reports that the request "
            "was processed -- the outcome is per item."
            % (len(failed_items), resp.get("RETURN_CODE")),
            "",
            "Rejected:",
        ]
        lines += [label(item) for item in failed_items]
        if applied:
            lines += [
                "",
                "Applied before the rejection (already changed on the controller):",
            ]
            lines += ["  %s" % entity for entity in applied]
        else:
            lines += ["", "Nothing in this batch was applied."]
        return "\n".join(lines)

    def dcnm_intf_send_message_to_dcnm(self):

        # PLANNING-REUSE / PREWRITE-REUSE: from here on every read is fresh; nothing planned before a write is reused after it.
        self._pvlan_sending = True
        self.__dict__.pop("pvlan_planning_previews", None)
        self.__dict__.pop("pvlan_prewrite_reads", None)

        resp = None
        changed = False

        delete = False
        delete_deploy = False
        create = False
        deploy = False
        replace = False

        path = self.paths["IF_MARK_DELETE"]

        # Native PVLAN writes need the bulk modify path and its per-item outcomes. Checked
        # before the FIRST request of this method so nothing is half-sent.
        if any(t["update"] for t in self.dcnm_intf_pvlan_target_map().values()) and not self.has_bulk_api:
            self.module.fail_json(
                msg="Native PVLAN requires the controller's bulk interface update API. "
                "No configuration or deployment request was sent.",
                **self.result
            )

        # First send deletes and then try create and update. This is because during override, the overriding
        # config may conflict with existing configuration.

        # Registered PVLAN port-channel deletions leave the generic batch: one request each, one attempt, measured
        # outcome only (dcnm_intf_pvlan_po_markdeletes). The generic path below is unchanged for everything else.
        pvlan_deleted = self.dcnm_intf_pvlan_po_markdeletes()
        # A registered vPC deletion leaves the generic batch too (one confirmed mark-delete, then the per-peer member release).
        vpc_deleted = self.dcnm_intf_pvlan_vpc_markdeletes()

        delete_index = 0
        for delem in self.diff_delete:

            if delem == []:
                delete_index = delete_index + 1
                continue

            # index 8 is used for breakout interface
            if delete_index == 8:
                path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/interface"
                break
            json_payload = json.dumps(delem)

            # A conventional aggregate deleted here leaves pending that the PVLAN gates of this invocation must recognise. Its
            # pre-state is read before the request; ownership is recorded only from the request's ORIGINAL confirmed answer.
            conventional = pvlan_conventional_delete_prestate(self, delem)
            resp = dcnm_send(self.module, "DELETE", path, json_payload)
            pvlan_record_conventional_deletions(self, delem, resp, conventional)

            if resp.get("RETURN_CODE") != 200:
                if resp["DATA"]:
                    delete_failed = False
                else:
                    delete_failed = True
                for item in resp["DATA"]:
                    if "No Commands to execute" not in item["message"]:
                        delete_failed = True
                if delete_failed is False:
                    resp["RETURN_CODE"] = 200
                    resp["MESSAGE"] = "OK"

            if (resp.get("MESSAGE") != "OK") or (
                resp.get("RETURN_CODE") != 200
            ):

                # there may be cases which are not actual failures. retry the
                # action
                resp, rc = self.dcnm_intf_send_message_handle_retry(
                    "DELETE", path, json_payload, "DELETE"
                )

                # Even if one of the elements succeed, changed must be set to
                # True. Once changed becomes True, then it remains True
                if False is changed:
                    changed = rc

                if (
                    (resp.get("MESSAGE") != "OK")
                    and ("No Commands to execute" not in resp.get("MESSAGE"))
                ) or (resp.get("RETURN_CODE") != 200):
                    resp["CHANGED"] = self.changed_dict
                    self.module.fail_json(msg=resp)
            else:
                changed = True

            delete = changed
            self.result["response"].append(resp)
            delete_index = delete_index + 1
        resp = None

        path = self.paths["GLOBAL_IF_DEPLOY"]
        # Flatten all diff_delete_deploy sublists into a single list and
        # send one POST instead of up to 9 separate calls (one per
        # interface type).  The deploy endpoint only needs serialNumber,
        # ifName, and fabricName — interface type grouping is irrelevant.
        flat_delete_deploy = []
        for delem in self.diff_delete_deploy:
            if delem:
                flat_delete_deploy.extend(delem)

        # The released member of a deleted PVLAN port-channel is corrected (admin down) BEFORE any deploy. This
        # follows every CONFIRMED PVLAN mark-delete, independently of the generic `changed` flag.
        if pvlan_deleted:
            delete = True
            self.dcnm_intf_pvlan_po_release_members()
        if vpc_deleted:
            delete = True
            self.dcnm_intf_pvlan_vpc_release_members()
        # A deletion requested with deploy false stops here, SAVED: the controller's pending (the aggregate's withdrawal and
        # its members' release) is judged by the same pre-deploy gate as an immediate deletion, and nothing is deployed.
        self.dcnm_intf_pvlan_validate_saved_deletions()
        if flat_delete_deploy:
            flat_delete_deploy = self.dcnm_intf_pvlan_deploy_gate(flat_delete_deploy, "delete_deploy", bool(delete))
        if flat_delete_deploy:
            json_payload = json.dumps(flat_delete_deploy)

            resp = dcnm_send(self.module, "POST", path, json_payload)
            self.dcnm_intf_pvlan_deploy_attempt(flat_delete_deploy, "delete_deploy", resp, False)

            if resp.get("RETURN_CODE") != 200:
                if resp["DATA"]:
                    deploy_failed = False
                else:
                    deploy_failed = True
                for item in resp["DATA"]:
                    if (
                        "No Commands to execute" not in item["message"]
                        and "In-Sync" not in item["message"]
                    ):
                        deploy_failed = True
                if deploy_failed is False:
                    resp["RETURN_CODE"] = 200
                    resp["MESSAGE"] = "OK"
                    delete_deploy = True
            else:
                delete_deploy = True
            self.result["response"].append(resp)

        resp = None

        if delete_deploy:
            self.dcnm_intf_pvlan_po_verify_deleted()
            self.dcnm_intf_pvlan_vpc_verify_deleted()
            self.dcnm_intf_pvlan_conventional_verify_deleted()

        if self.deferred_delete_member_defaults:
            self.dcnm_intf_refresh_deferred_deleted_member_defaults()

        # Add Breakout creation from self.want_breakout
        path = self.paths["BREAKOUT"]
        for payload in self.diff_create_breakout:
            json_payload = json.dumps(payload)
            resp = dcnm_send(self.module, "POST", path, json_payload)
            self.result["response"].append(resp)
            if (resp.get("MESSAGE") != "OK") or (
                resp.get("RETURN_CODE") != 200
            ):
                resp["CHANGED"] = self.changed_dict
                self.module.fail_json(msg=resp)
            else:
                create = True

        # Update interfaces
        # For bulk API support, use bulk update API. For other versions, use individual update API.
        if self.diff_replace:
            if self.has_bulk_api:
                # Bulk update API for bulk-capable controllers
                path = self.paths["UPDATE_INTERFACE_BULK"]

                json_payload = json.dumps(self.diff_replace)
                resp = dcnm_send(self.module, "POST", path, json_payload)
                self.result["response"].append(resp)

                # Accept both 200 (OK) and 207 (Multi-Status) for bulk operations
                if (resp.get("MESSAGE") not in ["OK", "Multi-Status"]) or (
                    resp.get("RETURN_CODE") not in [200, 207]
                ):
                    resp["CHANGED"] = self.changed_dict
                    self.module.fail_json(msg=resp)
                else:
                    # 207 is a BATCH code: the HTTP status only says the request was
                    # processed, and the per-item outcome lives in DATA. A 207 whose items
                    # are all ERROR looks identical, at the HTTP layer, to one whose items
                    # are all SUCCESS -- so judging by RETURN_CODE alone reports
                    # changed=true for a batch the controller rejected outright.
                    #
                    # Observed on a live controller: a parent template that refuses a value
                    # answers 207 with, per interface,
                    #   {"reportItemType": "ERROR",
                    #    "message": "Switch [...]: '<field>' cannot be set to ... ",
                    #    "entity": "<serial>:<ifName>"}
                    # and nothing is written. Silently succeeding there is the worst failure
                    # mode available: the operator believes the change landed.
                    #
                    # Only ERROR is fatal. WARNING is used for benign notices (the deploy
                    # call answers "No Commands to execute. In-Sync" that way) and any other
                    # value is left alone, so this cannot turn a working run into a failure
                    # on an item type we have not observed.
                    failed_items = self.dcnm_intf_collect_batch_errors(resp)
                    if failed_items:
                        self.module.fail_json(
                            msg=self.dcnm_intf_format_batch_error(resp, failed_items)
                        )
                    # PVLAN targets additionally need a SUCCESS item each; a missing or
                    # unknown outcome is indeterminate and must not reach a deploy.
                    pvlan_updates = sorted(
                        (t["sno"], t["name"]) for t in self.dcnm_intf_pvlan_target_map().values() if t["update"]
                    )
                    if pvlan_updates:
                        outcome = pvlan_modify_outcome_problems(resp, pvlan_updates)
                        if outcome:
                            self.module.fail_json(
                                msg="Native PVLAN update outcome is indeterminate:\n  {0}\n"
                                "Intent may have changed on the controller; it is not rolled back. "
                                "No deployment request was sent.".format("\n  ".join(outcome)),
                                **self.result
                            )
                    # Conventional members this confirmed update released (per-item SUCCESS), for this invocation's gates
                    pvlan_record_conventional_releases(self, self.diff_replace, resp)
                    # Conventional interfaces this confirmed update modified (per-item SUCCESS), for this invocation's gates
                    pvlan_record_conventional_modified(self, self.diff_replace, resp)
                    replace = True
            else:
                # Individual update API for versions 11 and 12
                path = self.paths["INTERFACE"]
                for payload in self.diff_replace:
                    json_payload = json.dumps(payload)

                    resp = dcnm_send(self.module, "PUT", path, json_payload)

                    self.result["response"].append(resp)

                    if (resp.get("MESSAGE") != "OK") or (
                        resp.get("RETURN_CODE") != 200
                    ):
                        resp["CHANGED"] = self.changed_dict
                        self.module.fail_json(msg=resp)
                    else:
                        replace = True

        resp = None

        # MM-B: members REMOVED from an existing PVLAN port-channel/vPC by the confirmed modify are released (admin down on their own policy)
        # BEFORE any deploy, through the deletion's release contract; any problem stops the run here with no deploy.
        if replace:
            self.dcnm_intf_pvlan_po_release_removed()
            self.dcnm_intf_pvlan_vpc_release_removed()
            self.dcnm_intf_pvlan_validate_saved_updates()

        # Delete Breakout interface
        if len(self.diff_delete_breakout) > 0:
            json_payload = json.dumps(self.diff_delete_breakout)
            resp = dcnm_send(self.module, "DELETE", path, json_payload)
            self.result["response"].append(resp)

            if (resp.get("MESSAGE") != "OK") or (
                resp.get("RETURN_CODE") != 200
            ):
                resp["CHANGED"] = self.changed_dict
                self.module.fail_json(msg=resp)
            else:
                delete = changed

        resp = None
        path = self.paths["GLOBAL_IF"]
        for payload in self.diff_create:
            # Do not create interface E1/x/y directly.
            if re.search(r"\d+\/\d+\/\d+", payload['interfaces'][0]['ifName']):
                continue
            json_payload = json.dumps(payload)
            resp = dcnm_send(self.module, "POST", path, json_payload)

            self.result["response"].append(resp)

            if ((resp.get("MESSAGE") != "OK") or (
                resp.get("RETURN_CODE") != 200
            )) and not self.dcnm_intf_pvlan_po_create_207(payload, resp) and not self.dcnm_intf_pvlan_vpc_create_outcome(payload, resp):
                resp["CHANGED"] = self.changed_dict
                self.module.fail_json(msg=resp)
            else:
                create = True
                # What this confirmed conventional creation leaves pending, for this invocation's PVLAN gates
                pvlan_record_conventional_creation(self, payload, resp)

        resp = None

        path = self.paths["GLOBAL_IF_DEPLOY"]
        deploy_items = []
        if self.diff_deploy:
            deploy_items = self.dcnm_intf_pvlan_deploy_gate(
                self.diff_deploy, "deploy", bool(replace or create or delete)
            )
        if deploy_items:
            json_payload = json.dumps(deploy_items)

            resp = dcnm_send(self.module, "POST", path, json_payload)
            self.dcnm_intf_pvlan_deploy_attempt(deploy_items, "deploy", resp, False)

            if (resp.get("MESSAGE") != "OK") and (
                resp.get("RETURN_CODE") != 200
            ):
                resp, rc = self.dcnm_parse_response(resp)
                changed = rc
            else:
                changed = True

            deploy = changed

            self.result["response"].append(resp)

            # Continue further only if original deploy is success. Fail otherwise
            if (resp.get("MESSAGE") != "OK") and (
                resp.get("RETURN_CODE") != 200
            ):
                resp["CHANGED"] = self.changed_dict
                self.module.fail_json(msg=resp)

        resp = None

        if self.diff_deploy and self.module.params["check_deploy"]:
            # Safety re-deploy: only when check_deploy is True.
            # Sometimes NDFC does not deploy all interfaces on the first
            # attempt.  A second deploy covers those stragglers before
            # the deployment-status polling loop below verifies In-Sync.
            # When check_deploy is False (default), the extra round-trip
            # is skipped because the caller does not require deployment
            # verification anyway.

            sent = set((it.get("serialNumber"), str(it.get("ifName", "")).lower()) for it in deploy_items)
            resend_items = self.dcnm_intf_pvlan_deploy_gate(self.diff_deploy, "check_deploy_resend", True, sent=sent)
            if resend_items:
                resp = dcnm_send(self.module, "POST", path, json.dumps(resend_items))
                self.dcnm_intf_pvlan_deploy_attempt(resend_items, "check_deploy_resend", resp, True)

            resp = None

        if self.diff_deploy:
            self.dcnm_intf_check_deployment_status(self.diff_deploy)
            self.dcnm_intf_pvlan_verify_after_deploy(self.diff_deploy)

        # In overridden and deleted states, if no delete or create is happening and we have
        # only replace, then check the return message for deploy. If it says
        # "No Commands to execute", then the interfaces we are replacing are
        # already in the required state and so consider that a no change
        if (self.module.params["state"] == "overridden") or (
            self.module.params["state"] == "deleted"
        ):
            self.result["changed"] = (
                delete or create or replace or deploy or delete_deploy
            )
        else:
            if delete or create or replace or deploy or delete_deploy:
                self.result["changed"] = True
            else:
                self.result["changed"] = False

    def dcnm_intf_get_xlated_object(self, cfg, key):

        """
        Routine to translate individual vlans like 45, 55 to 44-44 and 55-55 format

        Parameters:
            cfg (dict): Config element that includes the object idebtified by key to be translated
            key (str): key identifying the object to be translated

        Returns:
            translated object
        """

        citems = cfg["profile"][key].split(",")

        for index in range(len(citems)):
            if (
                (citems[index].lower() == "none")
                or (citems[index].lower() == "all")
                or ("-" in citems[index])
            ):
                continue

            # Playbook config includes individual vlans in allowed_vlans object. Convert the elem to
            # appropriate format i.e. vlaues in the form of 4, 7 to 4-4 and 7-7
            citems[index] = citems[index].strip() + "-" + citems[index].strip()
        return citems

    def dcnm_intf_translate_allowed_vlans(self, cfg):

        """
        Routine to translate xxx_allowed_vlans object in the config. 'xxx_allowed_vlans' object will
        allow only 'none', 'all', or 'vlan-ranges like 1-5' values. It does not allow individual
        vlans to be included. To enable user to include individual vlans in the playbook config, this
        routine tranlates the individual vlans like 3, 5 etc to 3-3 and 5-5 format.

        Parameters:
            cfg (dict): Config element that needs to be translated

        Returns:
            None
        """

        if cfg.get("profile", None) is None:
            return

        if cfg["profile"].get("allowed_vlans", None) is not None:
            xlated_obj = self.dcnm_intf_get_xlated_object(cfg, "allowed_vlans")
            cfg["profile"]["allowed_vlans"] = ",".join(xlated_obj)
        if cfg["profile"].get("peer1_allowed_vlans", None) is not None:
            xlated_obj = self.dcnm_intf_get_xlated_object(
                cfg, "peer1_allowed_vlans"
            )
            cfg["profile"]["peer1_allowed_vlans"] = ",".join(xlated_obj)
        if cfg["profile"].get("peer2_allowed_vlans", None) is not None:
            xlated_obj = self.dcnm_intf_get_xlated_object(
                cfg, "peer2_allowed_vlans"
            )
            cfg["profile"]["peer2_allowed_vlans"] = ",".join(xlated_obj)

    def dcnm_intf_update_inventory_data(self):

        """
        Routine to update inventory data for all fabrics included in the playbook. This routine
        also updates ip_sn, sn_hn and hn_sn objetcs from the updated inventory data.

        Parameters:
            None

        Returns:
            None
        """

        inv_data = get_fabric_inventory_details(self.module, self.fabric)

        self.inventory_data.update(inv_data)

        if self.module.params["state"] != "query":

            # Get all switches which are manageable and unmanageable
            manageable_ip = []
            manageable_hosts = []
            unmanageable_ip = []
            unmanageable_hosts = []

            for key in self.inventory_data:
                serial_number = self.inventory_data[key]["serialNumber"]
                logical_name = self.inventory_data[key]["logicalName"]
                is_manageable = str(self.inventory_data[key]["managable"]).lower() == "true"

                if is_manageable:
                    manageable_ip.append((key, serial_number))
                    manageable_hosts.append((logical_name, serial_number))
                else:
                    unmanageable_ip.append((key, serial_number))
                    unmanageable_hosts.append((logical_name, serial_number))

            self.manageable = dict(manageable_ip + manageable_hosts)
            self.unmanageable = dict(unmanageable_ip + unmanageable_hosts)

            # Build a mapping of serial numbers to switch roles. This will be required to build default ethernet
            # payload during overridden state. for switch role leaf the default policy for ethernet interface must
            # be 'trunk' and for other roles it must be 'routed'.
            self.sno_to_switch_role = {}
            for key in self.inventory_data:
                self.sno_to_switch_role.update(
                    {
                        self.inventory_data[key][
                            "serialNumber"
                        ]: self.inventory_data[key]["switchRole"]
                    }
                )

            # Get all switches which are manageable. Deploy must be avoided to all switches which are not part of this list
            ronly_sw_list = []
            for cfg in self.config:
                # Check if there are any switches which are not manageable in the config.
                if cfg.get("switch", None) is not None:
                    for sw in cfg["switch"]:
                        if sw not in self.manageable:
                            if sw not in ronly_sw_list:
                                ronly_sw_list.append(sw)

            # Deploy must be avoided to fabrics which are in monitoring mode
            path = self.paths["FABRIC_ACCESS_MODE"].format(self.fabric)
            resp = dcnm_send(self.module, "GET", path)

            if resp and resp["RETURN_CODE"] == 200:
                if str(resp["DATA"]["readonly"]).lower() == "true":
                    self.monitoring.append(self.fabric)

            # Check if source fabric is in monitoring mode. If so return an error, since fabrics in monitoring mode do not allow
            # create/modify/delete and deploy operations.
            if self.fabric in self.monitoring:
                self.module.fail_json(
                    msg="Error: Source Fabric '{0}' is in Monitoring mode, No changes are allowed on the fabric\n".format(
                        self.fabric
                    )
                )

        # Based on the updated inventory_data, update ip_sn, hn_sn and sn_hn objects
        self.ip_sn, self.hn_sn = get_ip_sn_dict(self.inventory_data)

    def dcnm_translate_playbook_info(self, config, ip_sn, hn_sn):

        # Transalte override_intf_types to proper types that can be directly used in overridden state.

        for if_type in self.module.params["override_intf_types"][:]:
            self.module.params["override_intf_types"].append(
                self.int_types[if_type]
            )
            self.module.params["override_intf_types"].remove(if_type)
        for cfg in config:
            index = 0
            if cfg.get("switch", None) is None:
                continue

            cfg_name = cfg.get("name", "")
            need_vpc_pair_lookup = cfg.get("type") in ("vpc", "aa_fex")
            if not need_vpc_pair_lookup and isinstance(cfg_name, str):
                # Deleted/query-style entries may omit type. Keep supporting
                # vPC names without paying the VPC lookup cost for every
                # non-vPC interface in the playbook.
                need_vpc_pair_lookup = cfg_name.lower().startswith("vpc")

            for sw_elem in cfg["switch"][:]:
                if sw_elem in self.ip_sn or sw_elem in self.hn_sn:
                    addr_info = dcnm_get_ip_addr_info(
                        self.module, sw_elem, ip_sn, hn_sn
                    )
                    cfg["switch"][index] = addr_info

                    # Fetch VPC pair serials only for interface types that
                    # actually need them.
                    if (
                        need_vpc_pair_lookup
                        and self.vpc_ip_sn.get(addr_info, None) is None
                    ):
                        sno = self.dcnm_intf_get_vpc_serial_number(addr_info)
                        if "~" in sno:
                            # This switch is part of VPC pair. Populate the VPC serial number DB
                            self.vpc_ip_sn[addr_info] = sno
                else:
                    cfg["switch"].remove(sw_elem)
                index = index + 1

            # 'allowed-vlans' in the case of trunk interfaces accepts 'all', 'none' and 'vlan-ranges' which
            # will be of the form 20-30 etc. There is not way to include individual vlans which are not contiguous.
            # To include individual vlans like 3,6,20 etc. user must input them in the form 3-3, 6-6, 20-20 which is
            # not very intuitive. To handle this scenario, we allow playbooks to include individual vlans and translate
            # them here appropriately.

            # Native PVLAN (Ethernet and port-channel) keeps the RAW allowed_vlans: it is validated
            # before any rewrite and sent in the measured int_pvlan_host form ("2301", not "2301-2301").
            # The same for the per-peer PVLAN allowed VLANs of a vPC in mode 'pvlan'.
            # SINGLETON-RANGE: a single-value range "N-N" (NaC convert_ranges for from N / to N) in those lists and in the
            # pvlan_mapping secondary_vlans is collapsed to "N" here, before validation, so it is sent and compared exactly as "N".
            if (
                cfg.get("type") in ("eth", "pc", "vpc")
                and isinstance(cfg.get("profile"), dict)
                and cfg["profile"].get("mode") == "pvlan"
            ):
                pvlan_normalize_single_value_ranges(cfg["profile"])
            if cfg.get("profile", None) is not None and not (
                cfg.get("type") in ("eth", "pc", "vpc")
                and isinstance(cfg["profile"], dict)
                and cfg["profile"].get("mode") == "pvlan"
            ):
                if (
                    (
                        cfg["profile"].get("peer1_allowed_vlans", None)
                        is not None
                    )
                    or (
                        cfg["profile"].get("peer2_allowed_vlans", None)
                        is not None
                    )
                    or (cfg["profile"].get("allowed_vlans", None) is not None)
                ):
                    self.dcnm_intf_translate_allowed_vlans(cfg)


def main():

    """main entry point for module execution"""
    element_spec = dict(
        fabric=dict(required=True, type="str"),
        config=dict(required=False, type="list", elements="dict", default=[]),
        deploy=dict(required=False, type="bool", default=True),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "replaced", "overridden", "deleted", "query"],
        ),
        override_intf_types=dict(
            required=False,
            type="list",
            elements="str",
            choices=[
                "pc",
                "vpc",
                "sub_int",
                "lo",
                "eth",
                "svi",
                "st_fex",
                "aa_fex",
                "breakout",
            ],
            default=[],
        ),
        check_deploy=dict(type="bool", default=False),
        # No default: see GIE_ENABLED_PATCH_VERSIONS in gie_engine.py for the one-location
        # capability policy this declares against. Omitted/None is the fail-closed input a
        # caller who does not supply it gets; there is no enabling fallback here or anywhere
        # else in the module/engine.
        patch_version=dict(required=False, type="str", default=None),
    )

    module = AnsibleModule(
        argument_spec=element_spec, supports_check_mode=True
    )

    # Logging setup
    try:
        log = Log()
        log.commit()
    except (TypeError, ValueError):
        pass

    dcnm_intf = DcnmIntf(module)

    state = module.params["state"]
    if not dcnm_intf.config:
        if state == "merged" or state == "replaced" or state == "query":
            module.fail_json(
                msg="'config' element is mandatory for state '{0}', given = '{1}'".format(
                    state, dcnm_intf.config
                )
            )

    dcnm_intf.dcnm_intf_update_inventory_data()

    if not dcnm_intf.ip_sn:
        dcnm_intf.result[
            "msg"
        ] = "Fabric {0} missing on DCNM or does not have any switches".format(
            dcnm_intf.fabric
        )
        module.fail_json(
            msg="Fabric {0} missing on DCNM or does not have any switches".format(
                dcnm_intf.fabric
            )
        )

    dcnm_intf.dcnm_translate_playbook_info(
        dcnm_intf.config, dcnm_intf.ip_sn, dcnm_intf.hn_sn
    )

    # The legacy OSPF booleans become their mode keys BEFORE the config is flattened into pb_input: the merged
    # comparison reads pb_input to tell an authored key from an omitted one, so an alias left there would
    # compare as "not authored".
    if module.params["state"] not in ("deleted", "query"):
        dcnm_intf.dcnm_intf_gie_normalize_ospf_aliases()

    dcnm_intf.dcnm_intf_copy_config()

    dcnm_intf.dcnm_intf_validate_input()

    # state 'deleted' may not include all the information
    if (module.params["state"] != "query") and (
        module.params["state"] != "deleted"
    ):
        dcnm_intf.dcnm_intf_get_want()
        dcnm_intf.dcnm_intf_get_have()

    if module.params["state"] == "merged":
        dcnm_intf.dcnm_intf_get_diff_merge()

    if module.params["state"] == "replaced":
        dcnm_intf.dcnm_intf_get_diff_replaced()

    if module.params["state"] == "overridden":
        dcnm_intf.dcnm_intf_get_diff_overridden(dcnm_intf.config)

    if module.params["state"] == "deleted":
        dcnm_intf.dcnm_intf_get_diff_deleted()

    if module.params["state"] == "query":
        dcnm_intf.dcnm_intf_get_diff_query()

    # ------------------------------------------------ withdrawal preflight
    # Placed here deliberately: every state has finished building its diffs, and NOTHING
    # has been sent. A valid first interface followed by an unsupported second one
    # therefore writes nothing at all -- the failure is invocation-wide.
    #
    # This is preflight, not a transaction: the module offers no rollback and none is
    # implied. It simply refuses to start.
    #
    # It fires in check mode too. Check mode is a report, and reporting a replacement
    # that could not be completed would be the same false claim as performing one.
    #
    # The message names the public field and the parent and NEVER the value: a binding
    # may carry key material, and a refusal is still a result with invocation.module_args
    # attached to it.
    # Native PVLAN preflight: ownership, defect, secondary-type and template authority for every
    # PVLAN target, raised once and before anything is sent (check mode included).
    if module.params["state"] != "query":
        dcnm_intf.dcnm_intf_pvlan_preflight()

    if dcnm_intf.svi_dhcp4_family_blocked:
        # D-F3-1: names only, never values; the declared patch_version is not corrected or guessed.
        parts = [
            "Interface {0}: patch_version {1} selects the int_vlan DHCP field names {2}, but the interface's current "
            "nvPairs carry {3} from the other int_vlan template body; the DHCP server 4 / relay source change would "
            "miss the stored values.".format(
                b["interface"],
                "'{0}'".format(dcnm_intf.patch_version) if dcnm_intf.patch_version else "(not declared)",
                "/".join(b["selected"]),
                "/".join(b["observed"]),
            )
            for b in dcnm_intf.svi_dhcp4_family_blocked
        ]
        parts.append(
            "No configuration or deployment request was sent. Verify patch_version and the int_vlan template "
            "installed on the controller."
        )
        module.fail_json(msg=" ".join(parts), **dcnm_intf.result)

    if dcnm_intf.dependency_blocked:
        # Dependent fields (inert_when) set against their gate. Names only, never values.
        set_off = sorted(
            {
                (b["interface"], b["parent"], b["field"], b["gate"])
                for b in dcnm_intf.dependency_blocked
                if b["reason"] == "set_while_off"
            }
        )
        empty_on = sorted(
            {
                (b["interface"], b["parent"], b["field"], b["gate"])
                for b in dcnm_intf.dependency_blocked
                if b["reason"] == "empty_while_on"
            }
        )
        parts = []
        if set_off:
            parts.append(
                "These fields depend on an option that this request leaves disabled, so they would "
                "configure nothing, and the controller refuses them or would keep their key material: {0}. "
                "Omit the field or give its neutral value when the option is disabled.".format(
                    ", ".join("{2} (needs {3}) on {0}, parent {1}".format(*b) for b in set_off)
                )
            )
        if empty_on:
            parts.append(
                "These fields are required while the option they depend on is enabled, and this request "
                "leaves them empty: {0}. Set the field, or disable the option.".format(
                    ", ".join("{2} (with {3} enabled) on {0}, parent {1}".format(*b) for b in empty_on)
                )
            )
        parts.append("No configuration or deployment request was sent.")
        module.fail_json(msg=" ".join(parts), **dcnm_intf.result)

    if dcnm_intf.withdrawal_blocked:
        unsupported = sorted(
            {
                (b["parent"], b["field"])
                for b in dcnm_intf.withdrawal_blocked
                if b["reason"] == GIE_WITHDRAW_UNSUPPORTED
            }
        )
        unclassified = sorted(
            {
                (b["parent"], b["field"])
                for b in dcnm_intf.withdrawal_blocked
                if b["reason"] == GIE_WITHDRAW_UNCLASSIFIED
            }
        )
        parts = []
        if unsupported:
            parts.append(
                "These fields were omitted while the controller holds a different "
                "configured value, so state '{0}' must withdraw them, and no verified "
                "reset is established for them on this parent: {1}.".format(
                    module.params["state"],
                    ", ".join("{0} on {1}".format(f, p) for p, f in unsupported),
                )
            )
        if unclassified:
            parts.append(
                "These fields were omitted while the controller holds a value that "
                "cannot be classified as already withdrawn, so state '{0}' cannot "
                "confirm the replacement is complete: {1}.".format(
                    module.params["state"],
                    ", ".join("{0} on {1}".format(f, p) for p, f in unclassified),
                )
            )
        parts.append(
            "No configuration or deployment request was sent. Set the field explicitly "
            "to the value you want, or use state 'merged' to preserve it."
        )
        module.fail_json(msg=" ".join(parts), **dcnm_intf.result)

    if dcnm_intf.default_reset_blocked:
        # A reset to the role default that cannot withdraw every registered field it must.
        # Named per interface and field, never with the value; nothing has been sent.
        same = sorted(
            {
                (b["interface"], b["serial"], b["parent"], b["field"], b["nvpair"])
                for b in dcnm_intf.default_reset_blocked
                if b["reason"] in (GIE_WITHDRAW_UNSUPPORTED, GIE_WITHDRAW_UNCLASSIFIED) and not b.get("gate")
            }
        )
        same_gated = sorted(
            {
                (b["interface"], b["serial"], b["parent"], b["field"], b["nvpair"], b["gate"])
                for b in dcnm_intf.default_reset_blocked
                if b["reason"] in (GIE_WITHDRAW_UNSUPPORTED, GIE_WITHDRAW_UNCLASSIFIED) and b.get("gate")
            }
        )
        unreadable = sorted(
            {
                (b["interface"], b["serial"], b["parent"], b["field"], b["nvpair"])
                for b in dcnm_intf.default_reset_blocked
                if b["reason"] == "unreadable"
            }
        )
        moved_clearable = sorted(
            {
                (b["interface"], b["serial"], b["parent"], b["destination"], b["field"], b["nvpair"])
                for b in dcnm_intf.default_reset_blocked
                if b["reason"] == "transition" and b.get("source_reset")
            }
        )
        moved_unverified = sorted(
            {
                (b["interface"], b["serial"], b["parent"], b["destination"], b["field"], b["nvpair"])
                for b in dcnm_intf.default_reset_blocked
                if b["reason"] == "transition" and not b.get("source_reset") and not b.get("gate")
            }
        )
        moved_gated = sorted(
            {
                (b["interface"], b["serial"], b["parent"], b["destination"], b["field"], b["nvpair"], b["gate"])
                for b in dcnm_intf.default_reset_blocked
                if b["reason"] == "transition" and not b.get("source_reset") and b.get("gate")
            }
        )
        # A remedy is offered only where the module has one. An explicit empty value is
        # not a verified withdrawal (booleans and enums even reject it), so it is never promised.
        no_withdrawal = (
            " This module has no verified withdrawal for it; it must be cleaned up by a separate, "
            "verified procedure before the reset is repeated."
        )
        parts = []
        if same:
            parts.append(
                "Resetting these interfaces to their default policy in state '{0}' must withdraw a "
                "registered field that holds a configured value, and no verified reset is established "
                "for it on that parent: {1}.{2}".format(
                    module.params["state"],
                    ", ".join("{3} ({4}) on {0} [{1}], parent {2}".format(*b) for b in same),
                    no_withdrawal,
                )
            )
        if same_gated:
            parts.append(
                "Resetting these interfaces to their default policy in state '{0}' must withdraw a "
                "registered field that holds a configured value, and no verified reset is established "
                "for it on that parent: {1}. The field configures nothing while its gate is off: disable {2} "
                "on the current policy first, then repeat the reset.".format(
                    module.params["state"],
                    ", ".join("{3} ({4}) on {0} [{1}], parent {2}".format(*b) for b in same_gated),
                    ", ".join(sorted(set(b[5] for b in same_gated))),
                )
            )
        if unreadable:
            parts.append(
                "Resetting these interfaces in state '{0}' must classify a registered field whose "
                "controller value is not readable as its type, so the reset cannot be confirmed: "
                "{1}.{2}".format(
                    module.params["state"],
                    ", ".join("{3} ({4}) on {0} [{1}], parent {2}".format(*b) for b in unreadable),
                    no_withdrawal,
                )
            )
        moved_head = (
            "Resetting these interfaces in state '{0}' changes their policy, and the registered "
            "field holds a configured value that the destination parent cannot withdraw; whether "
            "the controller drops it with the policy change is not established: {1}."
        )
        if moved_clearable:
            parts.append(
                (moved_head + " Its current policy has a verified reset: clear the field on that policy "
                 "first, then repeat the reset.").format(
                    module.params["state"],
                    ", ".join("{4} ({5}) on {0} [{1}], {2} -> {3}".format(*b) for b in moved_clearable),
                )
            )
        if moved_unverified:
            parts.append(
                (moved_head + "{2}").format(
                    module.params["state"],
                    ", ".join("{4} ({5}) on {0} [{1}], {2} -> {3}".format(*b) for b in moved_unverified),
                    no_withdrawal,
                )
            )
        if moved_gated:
            parts.append(
                (moved_head + " The field configures nothing while its gate is off: disable {2} on the current "
                 "policy first, then repeat the reset.").format(
                    module.params["state"],
                    ", ".join("{4} ({5}) on {0} [{1}], {2} -> {3}".format(*b) for b in moved_gated),
                    ", ".join(sorted(set(b[6] for b in moved_gated))),
                )
            )
        parts.append("No configuration or deployment request was sent.")
        module.fail_json(msg=" ".join(parts), **dcnm_intf.result)

    dcnm_intf.result["diff"] = dcnm_intf.changed_dict

    if (
        dcnm_intf.diff_create
        or dcnm_intf.diff_replace
        or dcnm_intf.diff_deploy
        or dcnm_intf.diff_delete[dcnm_intf.int_index["INTERFACE_PORT_CHANNEL"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["INTERFACE_VPC"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["INTERFACE_ETHERNET"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["SUBINTERFACE"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["INTERFACE_LOOPBACK"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["INTERFACE_VLAN"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["STRAIGHT_TROUGH_FEX"]]
        or dcnm_intf.diff_delete[dcnm_intf.int_index["AA_FEX"]]
        or any(dcnm_intf.diff_delete_deploy)
        or dcnm_intf.diff_create_breakout
        or dcnm_intf.diff_delete_breakout
    ):
        dcnm_intf.result["changed"] = True
    else:
        module.exit_json(**dcnm_intf.result)

    if module.check_mode:
        module.exit_json(**dcnm_intf.result)

    dcnm_intf.dcnm_intf_send_message_to_dcnm()
    module.exit_json(**dcnm_intf.result)


if __name__ == "__main__":
    main()
