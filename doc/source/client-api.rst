Client API
==========


Power management
----------------

get_power_state
~~~~~~~~~~~~~~~
Returns the current power state of the node.

set_power_state
~~~~~~~~~~~~~~~
Turns the server power on/off or do a reboot.

Required parameters:

* ``target_state``: target power state. Valid options are: ``POWER_ON``,
  ``POWER_OFF`` and ``REBOOT``.


Boot management
---------------

list_boot_modes
~~~~~~~~~~~~~~~
Returns the list of boot modes.

list_boot_devices
~~~~~~~~~~~~~~~~~
Returns the list of boot devices.

change_boot_device_order
~~~~~~~~~~~~~~~~~~~~~~~~
Changes the boot device sequence for a boot mode.

Required parameters:

* ``boot_mode``: boot mode for which the boot device list is to be changed.

* ``boot_device_list``: a list of boot device ids in an order representing the
  desired boot sequence.


BIOS configuration
------------------

list_bios_settings
~~~~~~~~~~~~~~~~~~
Lists the BIOS configuration settings.

set_bios_settings
~~~~~~~~~~~~~~~~~
Sets the BIOS configuration. To be more precise, it sets the ``pending_value``
parameter for each of the attributes passed in. It returns a dictionary
containing the ``commit_needed`` key with a boolean value indicating whether a
config job must be created for the values to be applied.

Required parameters:

* ``settings``: a dictionary containing the proposed values, with each key
  being the name of attribute and the value being the proposed value.

commit_pending_bios_changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Applies all pending changes on the BIOS by creating a config job and returns
the id of the created job.

Optional parameters:

* ``reboot``: indicates whether a RebootJob should also be created or not.
  Defaults to ``False``.

abandon_pending_bios_changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Deletes all pending changes on the BIOS.

.. note::
    Once a config job has been submitted, it can no longer be abandoned.

RAID management
---------------

list_raid_controllers
~~~~~~~~~~~~~~~~~~~~~
Returns the list of RAID controllers.

list_virtual_disks
~~~~~~~~~~~~~~~~~~
Returns the list of RAID arrays.

list_physical_disks
~~~~~~~~~~~~~~~~~~~
Returns the list of physical disks.

create_virtual_disk
~~~~~~~~~~~~~~~~~~~
Creates a virtual disk and returns a dictionary containing the
``commit_needed`` key with a boolean value indicating whether a config job must
be created for the values to be applied.

.. note::
    The created virtual disk will be in pending state.

Required parameters:

* ``raid_controller``: id of the RAID controller.

* ``physical_disks``: ids of the physical disks.

* ``raid_level``: RAID level of the virtual disk.

* ``size_mb``: size of the virtual disk in megabytes.

Optional parameters:

* ``disk_name``: name of the virtual disk.

* ``span_length``: number of disks per span.

* ``span_depth``: number of spans in virtual disk.

delete_virtual_disk
~~~~~~~~~~~~~~~~~~~
Deletes a virtual disk and returns a dictionary containing the
``commit_needed`` key with a boolean value indicating whether a config job must
be created for the values to be applied.

.. note::
    The deleted virtual disk will be in pending state. For the changes to be
    applied, a config job must be created and the node must be rebooted.

Required parameters:

* ``virtual_disk``: id of the virtual disk.

commit_pending_raid_changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Applies all pending changes on a RAID controller by creating a config job and
returns the id of the created job.

Required parameters:

* ``raid_controller``: id of the RAID controller.

Optional parameters:

* ``reboot``: indicates whether a RebootJob should also be created or not.
  Defaults to ``False``.

abandon_pending_raid_changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Deletes all pending changes on a RAID controller.

.. note::
    Once a config job has been submitted, it can no longer be abandoned.

Required parameters:

* ``raid_controller``: id of the RAID controller.

Inventory Management
--------------------

list_cpus
~~~~~~~~~
Returns a list of installed CPUs.

list_memory
~~~~~~~~~~~
Returns a list of installed memory modules.

list_nics
~~~~~~~~~
Returns a list of NICs.

Job management
--------------

list_jobs
~~~~~~~~~
Returns a list of jobs from the job queue.

Optional parameters:

* ``only_unfinished``: indicates whether only unfinished jobs should be
  returned. Defaults to ``False``.

get_job
~~~~~~~
Returns a job from the job queue.

Required parameters:

* ``job_id``: id of the job.

create_config_job
~~~~~~~~~~~~~~~~~
Creates a config job and returns the id of the created job.

.. note::
    In CIM (Common Information Model), weak association is used to name an
    instance of one class in the context of an instance of another class.
    ``SystemName`` and ``SystemCreationClassName`` are the attributes of the
    scoping system, while ``Name`` and ``CreationClassName`` are the attributes
    of the instance of the class, on which the ``CreateTargetedConfigJob``
    method is invoked.

Required parameters:

* ``resource_uri``: URI of resource to invoke.

* ``cim_creation_class_name``: creation class name of the CIM object.

* ``cim_name``: name of the CIM object.

* ``target``: target device.

Optional parameters:

* ``cim_system_creation_class_name``: creation class name of the scoping
  system. Defaults to ``DCIM_ComputerSystem``.

* ``cim_system_name``: name of the scoping system. Defaults to
  ``DCIM:ComputerSystem``.

* ``reboot``: indicates whether a RebootJob should also be created or not.
  Defaults to ``False``.

delete_pending_config
~~~~~~~~~~~~~~~~~~~~~
Cancels pending configuration.

.. note::
    Once a config job has been submitted, it can no longer be abandoned.

.. note::
    In CIM (Common Information Model), weak association is used to name an
    instance of one class in the context of an instance of another class.
    ``SystemName`` and ``SystemCreationClassName`` are the attributes of the
    scoping system, while ``Name`` and ``CreationClassName`` are the attributes
    of the instance of the class, on which the ``CreateTargetedConfigJob``
    method is invoked.

Required parameters:

* ``resource_uri``: URI of resource to invoke.

* ``cim_creation_class_name``: creation class name of the CIM object.

* ``cim_name``: name of the CIM object.

* ``target``: target device.

Optional parameters:

* ``cim_system_creation_class_name``: creation class name of the scoping
  system. Defaults to ``DCIM_ComputerSystem``.

* ``cim_system_name``: name of the scoping system. Defaults to
  ``DCIM:ComputerSystem``.

* ``reboot``: indicates whether a RebootJob should also be created or not.
  Defaults to ``False``.


Lifecycle controller management
-------------------------------

get_lifecycle_controller_version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Returns the Lifecycle controller version as a tuple of integers.
