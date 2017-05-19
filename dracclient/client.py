#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Wrapper for pywsman.Client
"""

import logging
import time

from dracclient import exceptions
from dracclient.resources import bios
from dracclient.resources import idrac_card
from dracclient.resources import inventory
from dracclient.resources import job
from dracclient.resources import lifecycle_controller
from dracclient.resources import raid
from dracclient.resources import uris
from dracclient import utils
from dracclient import wsman

LOG = logging.getLogger(__name__)


class DRACClient(object):
    """Client for managing DRAC nodes"""

    BIOS_DEVICE_FQDD = 'BIOS.Setup.1-1'

    def __init__(self, host, username, password, port=443, path='/wsman',
                 protocol='https'):
        """Creates client object

        :param host: hostname or IP of the DRAC interface
        :param username: username for accessing the DRAC interface
        :param password: password for accessing the DRAC interface
        :param port: port for accessing the DRAC interface
        :param path: path for accessing the DRAC interface
        :param protocol: protocol for accessing the DRAC interface
        """
        self.client = WSManClient(host, username, password, port, path,
                                  protocol)
        self._job_mgmt = job.JobManagement(self.client)
        self._power_mgmt = bios.PowerManagement(self.client)
        self._boot_mgmt = bios.BootManagement(self.client)
        self._bios_cfg = bios.BIOSConfiguration(self.client)
        self._lifecycle_cfg = lifecycle_controller.LCConfiguration(self.client)
        self._idrac_cfg = idrac_card.iDRACCardConfiguration(self.client)
        self._raid_mgmt = raid.RAIDManagement(self.client)
        self._inventory_mgmt = inventory.InventoryManagement(self.client)

    def get_power_state(self):
        """Returns the current power state of the node

        :returns: power state of the node, one of 'POWER_ON', 'POWER_OFF' or
                  'REBOOT'
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._power_mgmt.get_power_state()

    def set_power_state(self, target_state):
        """Turns the server power on/off or do a reboot

        :param target_state: target power state. Valid options are: 'POWER_ON',
                             'POWER_OFF' and 'REBOOT'.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        :raises: InvalidParameterValue on invalid target power state
        """
        self._power_mgmt.set_power_state(target_state)

    def list_boot_modes(self):
        """Returns the list of boot modes

        :returns: list of BootMode objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._boot_mgmt.list_boot_modes()

    def list_boot_devices(self):
        """Returns the list of boot devices

        :returns: a dictionary with the boot modes and the list of associated
                  BootDevice objects, ordered by the pending_assigned_sequence
                  property
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._boot_mgmt.list_boot_devices()

    def change_boot_device_order(self, boot_mode, boot_device_list):
        """Changes the boot device sequence for a boot mode

        :param boot_mode: boot mode for which the boot device list is to be
                          changed
        :param boot_device_list: a list of boot device ids in an order
                                 representing the desired boot sequence
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        return self._boot_mgmt.change_boot_device_order(boot_mode,
                                                        boot_device_list)

    def list_bios_settings(self, by_name=True):
        """List the BIOS configuration settings

        :param by_name: Controls whether returned dictionary uses BIOS
                        attribute name as key. If set to False, instance_id
                        will be used.
        :returns: a dictionary with the BIOS settings using its name as the
                  key. The attributes are either BIOSEnumerableAttribute,
                  BIOSStringAttribute or BIOSIntegerAttribute objects.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._bios_cfg.list_bios_settings(by_name)

    def set_bios_settings(self, settings):
        """Sets the BIOS configuration

        To be more precise, it sets the pending_value parameter for each of the
        attributes passed in. For the values to be applied, a config job must
        be created and the node must be rebooted.

        :param settings: a dictionary containing the proposed values, with
                         each key being the name of attribute and the value
                         being the proposed value.
        :returns: a dictionary containing the commit_needed key with a boolean
                  value indicating whether a config job must be created for the
                  values to be applied.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        :raises: InvalidParameterValue on invalid BIOS attribute
        """
        return self._bios_cfg.set_bios_settings(settings)

    def list_idrac_settings(self):
        """List the iDRAC configuration settings

        :returns: a dictionary with the iDRAC settings using InstanceID as the
                  key. The attributes are either iDRACCArdEnumerableAttribute,
                  iDRACCardStringAttribute or iDRACCardIntegerAttribute
                  objects.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._idrac_cfg.list_idrac_settings()

    def list_lifecycle_settings(self):
        """List the Lifecycle Controller configuration settings

        :returns: a dictionary with the Lifecycle Controller settings using its
                  InstanceID as the key. The attributes are either
                  LCEnumerableAttribute or LCStringAttribute objects.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._lifecycle_cfg.list_lifecycle_settings()

    def list_jobs(self, only_unfinished=False):
        """Returns a list of jobs from the job queue

        :param only_unfinished: indicates whether only unfinished jobs should
                                be returned
        :returns: a list of Job objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._job_mgmt.list_jobs(only_unfinished)

    def get_job(self, job_id):
        """Returns a job from the job queue

        :param job_id: id of the job
        :returns: a Job object on successful query, None otherwise
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._job_mgmt.get_job(job_id)

    def create_config_job(self, resource_uri, cim_creation_class_name,
                          cim_name, target,
                          cim_system_creation_class_name='DCIM_ComputerSystem',
                          cim_system_name='DCIM:ComputerSystem',
                          reboot=False):
        """Creates a config job

        In CIM (Common Information Model), weak association is used to name an
        instance of one class in the context of an instance of another class.
        SystemName and SystemCreationClassName are the attributes of the
        scoping system, while Name and CreationClassName are the attributes of
        the instance of the class, on which the CreateTargetedConfigJob method
        is invoked.

        :param resource_uri: URI of resource to invoke
        :param cim_creation_class_name: creation class name of the CIM object
        :param cim_name: name of the CIM object
        :param target: target device
        :param cim_system_creation_class_name: creation class name of the
                                               scoping system
        :param cim_system_name: name of the scoping system
        :param reboot: indicates whether a RebootJob should also be
                       created or not
        :returns: id of the created job
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        return self._job_mgmt.create_config_job(
            resource_uri, cim_creation_class_name, cim_name, target,
            cim_system_creation_class_name, cim_system_name, reboot)

    def delete_pending_config(
            self, resource_uri, cim_creation_class_name, cim_name, target,
            cim_system_creation_class_name='DCIM_ComputerSystem',
            cim_system_name='DCIM:ComputerSystem'):
        """Cancels pending configuration

        Once a config job has been submitted, it can no longer be abandoned.

        In CIM (Common Information Model), weak association is used to name an
        instance of one class in the context of an instance of another class.
        SystemName and SystemCreationClassName are the attributes of the
        scoping system, while Name and CreationClassName are the attributes of
        the instance of the class, on which the CreateTargetedConfigJob method
        is invoked.

        :param resource_uri: URI of resource to invoke
        :param cim_creation_class_name: creation class name of the CIM object
        :param cim_name: name of the CIM object
        :param target: target device
        :param cim_system_creation_class_name: creation class name of the
                                               scoping system
        :param cim_system_name: name of the scoping system
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        self._job_mgmt.delete_pending_config(
            resource_uri, cim_creation_class_name, cim_name, target,
            cim_system_creation_class_name, cim_system_name)

    def commit_pending_bios_changes(self, reboot=False):
        """Applies all pending changes on the BIOS by creating a config job

        :param reboot: indicates whether a RebootJob should also be
                       created or not
        :returns: id of the created job
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        return self._job_mgmt.create_config_job(
            resource_uri=uris.DCIM_BIOSService,
            cim_creation_class_name='DCIM_BIOSService',
            cim_name='DCIM:BIOSService', target=self.BIOS_DEVICE_FQDD,
            reboot=reboot)

    def abandon_pending_bios_changes(self):
        """Deletes all pending changes on the BIOS

        Once a config job has been submitted, it can no longer be abandoned.

        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        self._job_mgmt.delete_pending_config(
            resource_uri=uris.DCIM_BIOSService,
            cim_creation_class_name='DCIM_BIOSService',
            cim_name='DCIM:BIOSService', target=self.BIOS_DEVICE_FQDD)

    def get_lifecycle_controller_version(self):
        """Returns the Lifecycle controller version

        :returns: Lifecycle controller version as a tuple of integers
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return lifecycle_controller.LifecycleControllerManagement(
            self.client).get_version()

    def list_raid_controllers(self):
        """Returns the list of RAID controllers

        :returns: a list of RAIDController objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._raid_mgmt.list_raid_controllers()

    def list_virtual_disks(self):
        """Returns the list of RAID arrays

        :returns: a list of VirtualDisk objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._raid_mgmt.list_virtual_disks()

    def list_physical_disks(self):
        """Returns the list of physical disks

        :returns: a list of PhysicalDisk objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._raid_mgmt.list_physical_disks()

    def convert_physical_disks(self, raid_controller, physical_disks,
                               raid_enable=True):
        """Changes the operational mode of a physical disk.

        Disks can be enabled or disabled for RAID mode.

        :param raid_controller: the FQDD ID of the RAID controller
        :param physical_disks: list of FQDD ID strings of the physical disks
               to update
        :param raid_enable: boolean flag, set to True if the disk is to
               become part of the RAID.  The same flag is applied to all
               listed disks
        :returns: a dictionary containing the commit_required key with a
                  boolean value indicating whether a config job must be
                  created for the values to be applied.
        """
        return self._raid_mgmt.convert_physical_disks(
            physical_disks, raid_enable)

    def create_virtual_disk(self, raid_controller, physical_disks, raid_level,
                            size_mb, disk_name=None, span_length=None,
                            span_depth=None):
        """Creates a virtual disk

        The created virtual disk will be in pending state.

        :param raid_controller: id of the RAID controller
        :param physical_disks: ids of the physical disks
        :param raid_level: RAID level of the virtual disk
        :param size_mb: size of the virtual disk in megabytes
        :param disk_name: name of the virtual disk (optional)
        :param span_length: number of disks per span (optional)
        :param span_depth: number of spans in virtual disk (optional)
        :returns: a dictionary containing the commit_needed key with a boolean
                  value indicating whether a config job must be created for the
                  values to be applied.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        :raises: InvalidParameterValue on invalid input parameter
        """
        return self._raid_mgmt.create_virtual_disk(
            raid_controller, physical_disks, raid_level, size_mb, disk_name,
            span_length, span_depth)

    def delete_virtual_disk(self, virtual_disk):
        """Deletes a virtual disk

        The deleted virtual disk will be in pending state. For the changes to
        be applied, a config job must be created and the node must be rebooted.

        :param virtual_disk: id of the virtual disk
        :returns: a dictionary containing the commit_needed key with a boolean
                  value indicating whether a config job must be created for the
                  values to be applied.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        return self._raid_mgmt.delete_virtual_disk(virtual_disk)

    def commit_pending_raid_changes(self, raid_controller, reboot=False):
        """Applies all pending changes on a RAID controller

         ...by creating a config job.

        :param raid_controller: id of the RAID controller
        :param reboot: indicates whether a RebootJob should also be
                       created or not
        :returns: id of the created job
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        return self._job_mgmt.create_config_job(
            resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target=raid_controller, reboot=reboot)

    def abandon_pending_raid_changes(self, raid_controller):
        """Deletes all pending changes on a RAID controller

        Once a config job has been submitted, it can no longer be abandoned.

        :param raid_controller: id of the RAID controller
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        self._job_mgmt.delete_pending_config(
            resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target=raid_controller)

    def list_cpus(self):
        """Returns the list of CPUs

        :returns: a list of CPU objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return self._inventory_mgmt.list_cpus()

    def list_memory(self):
        """Returns a list of memory modules

        :returns: a list of Memory objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        return self._inventory_mgmt.list_memory()

    def list_nics(self):
        """Returns a list of NICs

        :returns: a list of NIC objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        return self._inventory_mgmt.list_nics()

    def is_idrac_ready(self):
        """Indicates if the iDRAC is ready to accept commands

           Returns a boolean indicating if the iDRAC is ready to accept
           commands.

        :returns: Boolean indicating iDRAC readiness
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """

        return self._lifecycle_cfg.is_idrac_ready()

    def wait_until_idrac_is_ready(self, retries=24, retry_delay=10):
        """Waits until the iDRAC is in a ready state

        :param retries: The number of times to check if the iDRAC is ready
        :param retry_delay: The number of seconds to wait between retries

        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface or timeout
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """

        # Try every 10 seconds over 4 minutes for the iDRAC to become ready
        while retries > 0:
            LOG.debug("Checking to see if the iDRAC is ready")

            if self.is_idrac_ready():
                LOG.debug("The iDRAC is ready")
                return

            LOG.debug("The iDRAC is not ready")
            retries -= 1
            if retries > 0:
                time.sleep(retry_delay)

        if retries == 0:
            err_msg = "Timed out waiting for the iDRAC to become ready"
            LOG.error(err_msg)
            raise exceptions.DRACOperationFailed(drac_messages=err_msg)


class WSManClient(wsman.Client):
    """Wrapper for wsman.Client with return value checking"""

    def invoke(self, resource_uri, method, selectors=None, properties=None,
               expected_return_value=None):
        """Invokes a remote WS-Man method

        :param resource_uri: URI of the resource
        :param method: name of the method to invoke
        :param selectors: dictionary of selectors
        :param properties: dictionary of properties
        :param expected_return_value: expected return value reported back by
            the DRAC card. For return value codes check the profile
            documentation of the resource used in the method call. If not set,
            return value checking is skipped.
        :returns: an lxml.etree.Element object of the response received
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """
        if selectors is None:
            selectors = {}

        if properties is None:
            properties = {}

        resp = super(WSManClient, self).invoke(resource_uri, method, selectors,
                                               properties)

        return_value = utils.find_xml(resp, 'ReturnValue', resource_uri).text
        if return_value == utils.RET_ERROR:
            message_elems = utils.find_xml(resp, 'Message', resource_uri, True)
            messages = [message_elem.text for message_elem in message_elems]
            raise exceptions.DRACOperationFailed(drac_messages=messages)

        if (expected_return_value is not None and
                return_value != expected_return_value):
            raise exceptions.DRACUnexpectedReturnValue(
                expected_return_value=expected_return_value,
                actual_return_value=return_value)

        return resp
