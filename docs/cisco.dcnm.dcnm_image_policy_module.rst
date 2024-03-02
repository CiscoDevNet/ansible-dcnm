
.. Document meta

:orphan:

.. |antsibull-internal-nbsp| unicode:: 0xA0
    :trim:

.. meta::
  :antsibull-docs: 2.7.0

.. Anchors

.. _ansible_collections.cisco.dcnm.dcnm_image_policy_module:

.. Anchors: short name for ansible.builtin

.. Title

cisco.dcnm.dcnm_image_policy module -- Image policy management for Nexus Dashboard Fabric Controller
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This module is part of the `cisco.dcnm collection <https://galaxy.ansible.com/ui/repo/published/cisco/dcnm/>`_.

    It is not included in ``ansible-core``.
    To check whether it is installed, run :code:`ansible-galaxy collection list`.

    To install it, use: :code:`ansible-galaxy collection install cisco.dcnm`.

    To use it in a playbook, specify: :code:`cisco.dcnm.dcnm_image_policy`.

.. version_added

.. rst-class:: ansible-version-added

New in cisco.dcnm 3.5.0

.. contents::
   :local:
   :depth: 1

.. Deprecated


Synopsis
--------

.. Description

- Create, delete, modify image policies.


.. Aliases


.. Requirements






.. Options

Parameters
----------

.. tabularcolumns:: \X{1}{3}\X{2}{3}

.. list-table::
  :width: 100%
  :widths: auto
  :header-rows: 1
  :class: longtable ansible-option-table

  * - Parameter
    - Comments

  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-config"></div>

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-config:

      .. rst-class:: ansible-option-title

      **config**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-config" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=dictionary` / :ansible-option-required:`required`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      List of dictionaries containing image policy parameters


      .. raw:: html

        </div>
    
  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-config/agnostic"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-config/agnostic:

      .. rst-class:: ansible-option-title

      **agnostic**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-config/agnostic" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`boolean`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      The agnostic flag.


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry-default:`false` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`true`


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-config/description"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-config/description:

      .. rst-class:: ansible-option-title

      **description**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-config/description" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      The image policy description.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`""`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-config/epld_image"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-config/epld_image:

      .. rst-class:: ansible-option-title

      **epld_image**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-config/epld_image" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      The epld image name.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`""`

      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-config/name"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-config/name:

      .. rst-class:: ansible-option-title

      **name**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-config/name" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string` / :ansible-option-required:`required`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      The image policy name.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-config/packages"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-config/packages:

      .. rst-class:: ansible-option-title

      **packages**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-config/packages" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`dictionary`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      A dictionary containing two keys, install and uninstall.


      .. raw:: html

        </div>
    
  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-config/packages/install"></div>

      .. raw:: latex

        \hspace{0.04\textwidth}\begin{minipage}[t]{0.28\textwidth}

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-config/packages/install:

      .. rst-class:: ansible-option-title

      **install**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-config/packages/install" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=string`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      A list of packages to install.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-config/packages/uninstall"></div>

      .. raw:: latex

        \hspace{0.04\textwidth}\begin{minipage}[t]{0.28\textwidth}

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-config/packages/uninstall:

      .. rst-class:: ansible-option-title

      **uninstall**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-config/packages/uninstall" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`list` / :ansible-option-elements:`elements=string`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      A list of packages to uninstall.


      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-config/platform"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-config/platform:

      .. rst-class:: ansible-option-title

      **platform**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-config/platform" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string` / :ansible-option-required:`required`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      The platform to which the image policy applies e.g. N9K.


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-config/release"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-config/release:

      .. rst-class:: ansible-option-title

      **release**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-config/release" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string` / :ansible-option-required:`required`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      The release associated with the image policy.

      Example 10.2.5\_nxos64-cs\_64bit

      See NDFC API documentation regarding this string


      .. raw:: html

        </div>

  * - .. raw:: html

        <div class="ansible-option-indent"></div><div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-config/type"></div>

      .. raw:: latex

        \hspace{0.02\textwidth}\begin{minipage}[t]{0.3\textwidth}

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-config/type:

      .. rst-class:: ansible-option-title

      **type**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-config/type" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

      .. raw:: latex

        \end{minipage}

    - .. raw:: html

        <div class="ansible-option-indent-desc"></div><div class="ansible-option-cell">

      The type of the image policy e.g. PLATFORM.


      .. rst-class:: ansible-option-line

      :ansible-option-default-bold:`Default:` :ansible-option-default:`"PLATFORM"`

      .. raw:: html

        </div>


  * - .. raw:: html

        <div class="ansible-option-cell">
        <div class="ansibleOptionAnchor" id="parameter-state"></div>

      .. _ansible_collections.cisco.dcnm.dcnm_image_policy_module__parameter-state:

      .. rst-class:: ansible-option-title

      **state**

      .. raw:: html

        <a class="ansibleOptionLink" href="#parameter-state" title="Permalink to this option"></a>

      .. ansible-option-type-line::

        :ansible-option-type:`string`

      .. raw:: html

        </div>

    - .. raw:: html

        <div class="ansible-option-cell">

      The state of the feature or object after module completion


      .. rst-class:: ansible-option-line

      :ansible-option-choices:`Choices:`

      - :ansible-option-choices-entry:`"deleted"`
      - :ansible-option-choices-entry-default:`"merged"` :ansible-option-choices-default-mark:`← (default)`
      - :ansible-option-choices-entry:`"overridden"`
      - :ansible-option-choices-entry:`"query"`
      - :ansible-option-choices-entry:`"replaced"`


      .. raw:: html

        </div>


.. Attributes


.. Notes


.. Seealso


.. Examples

Examples
--------

.. code-block:: yaml+jinja

    
    # This module supports the following states:
    #
    # deleted:
    #   Delete image policies from the controller.
    #
    #   If an image policy has references (i.e. it is attached to a device),
    #   the module will fail.  Use dcnm_image_upgrade module, state deleted,
    #    to detach the image policy from all devices before deleting it.
    #
    # merged:
    #   Create (or update) one or more image policies.
    #
    #   If an image policy does not exist on the controller, create it.
    #   If an image policy already exists on the controller, edit it.
    #
    # overridden:
    #   Create/delete one or more image policies.
    #
    #   If an image policy already exists on the controller, delete it and update
    #   it with the configuration in the playbook task.
    #
    #   Remove any image policies from the controller that are not in the
    #   playbook task.
    #
    # query:
    #
    #   Return the configuration for one or more image policies.
    #
    # replaced:
    #
    #   Replace image policies on the controller with policies in the playbook task.
    #
    #   If an image policy exists on the controller, but not in the playbook task,
    #   do not delete it or modify it.
    #
    # Delete two image policies from the controller.

        -   name: Delete Image policies
            cisco.dcnm.dcnm_image_policy:
                state: deleted
                config:
                -   name: KR5M
                -   name: NR3F
            register: result
        -   name: print result
            ansible.builtin.debug:
                var: result

    # Merge two image policies into the controller.

        -   name: Merge Image policies
            cisco.dcnm.dcnm_image_policy:
                state: merged
                config:
                -   name: KR5M
                    agnostic: false
                    description: KR5M
                    epld_image: n9000-epld.10.2.5.M.img
                    packages:
                       install:
                       - mtx-openconfig-all-2.0.0.0-10.4.1.src.rpm
                       uninstall:
                       - mtx-grpctunnel-2.1.0.0-10.4.1.lib32_64_n9000
                    platform: N9K
                    release: 10.2.5_nxos64-cs_64bit
                    type: PLATFORM
                -   name: NR3F
                    description: NR3F
                    platform: N9K
                    epld_image: n9000-epld.10.3.1.F.img
                    release: 10.3.1_nxos64-cs_64bit
            register: result
        -   name: print result
            ansible.builtin.debug:
                var: result

    # Override all policies on the controller and replace them with
    # the policies in the playbook task.  Any policies other than
    # KR5M and NR3F are deleted from the controller.

        -   name: Override Image policies
            cisco.dcnm.dcnm_image_policy:
                state: overridden
                config:
                -   name: KR5M
                    agnostic: false
                    description: KR5M
                    epld_image: n9000-epld.10.2.5.M.img
                    platform: N9K
                    release: 10.2.5_nxos64-cs_64bit
                    type: PLATFORM
                -   name: NR3F
                    description: NR3F
                    platform: N9K
                    epld_image: n9000-epld.10.2.5.M.img
                    release: 10.3.1_nxos64-cs_64bit
            register: result
        -   name: print result
            ansible.builtin.debug:
                var: result

    # Query the controller for the policies in the playbook task.

        -   name: Query Image policies
            cisco.dcnm.dcnm_image_policy:
                state: query
                config:
                -   name: NR3F
                -   name: KR5M
            register: result
        -   name: print result
            ansible.builtin.debug:
                var: result

    # Replace any policies on the controller that are in the playbook task with
    # the configuration given in the playbook task.  Policies not listed in the
    # playbook task are not modified and are not deleted.

        -   name: Replace Image policies
            cisco.dcnm.dcnm_image_policy:
                state: replaced
                config:
                -   name: KR5M
                    agnostic: false
                    description: KR5M
                    epld_image: n9000-epld.10.2.5.M.img
                    platform: N9K
                    release: 10.2.5_nxos64-cs_64bit
                    type: PLATFORM
                -   name: NR3F
                    description: Replaced NR3F
                    platform: N9K
                    epld_image: n9000-epld.10.3.1.F.img
                    release: 10.3.1_nxos64-cs_64bit
            register: result
        -   name: print result
            ansible.builtin.debug:
                var: result




.. Facts


.. Return values


..  Status (Presently only deprecated)


.. Authors

Authors
~~~~~~~

- Allen Robel (@quantumonion)



.. Extra links


.. Parsing errors

